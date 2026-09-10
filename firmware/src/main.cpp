// Akuisisi EKG stand-alone: tombol REC merekam ke PSRAM lalu simpan ke LittleFS,
// tombol DUMP mengirimnya ke serial. Tanpa laptop saat merekam.
//
// Sampling 360 Hz TEPAT lewat timer hardware — bukan delay() di loop(). Model
// dilatih pada fs=360; laju yang melayang mencemari RR_prev & dRR, fitur yang
// paling menentukan kelas S.
#ifndef PIO_UNIT_TESTING
#include <Arduino.h>
#include <LittleFS.h>
#include <string.h>

#include "ecg_preproc.h"          // GENERATED: ECG_FS dll
#include "ecg_pipeline.h"         // ecg_bandpass — dipakai utk menilai kualitas sinyal

constexpr int PIN_EKG   = 4;      // AD8232 OUTPUT — WAJIB ADC1 (GPIO1-10).
                                  // ADC2 (GPIO11-20) mati total saat WiFi aktif.
constexpr int PIN_PROBE = 18;     // pin nganggur, dipakai sbg "voltmeter" saat debug
constexpr int PIN_LOP   = 17;     // LO+ (digital, pin mana pun boleh)
constexpr int PIN_LON   = 7;      // LO-
constexpr int PIN_REC   = 6;
constexpr int PIN_DUMP  = 5;
constexpr int PIN_LED   = 48;

constexpr uint32_t DETIK_MAKS = 300;                      // 5 menit
constexpr size_t   N_MAKS = (size_t)ECG_FS * DETIK_MAKS;  // 108.000 sampel
constexpr const char *BERKAS = "/rekaman.csv";
constexpr uint32_t DEBOUNCE_MS = 50;

static uint16_t *buf = nullptr;
static volatile size_t n_sampel = 0;
static volatile bool rekam = false;
static volatile uint32_t n_lewat = 0;
static volatile bool waktunya = false;
static int ayun_terakhir = 0;      // ayunan sinyal 1 detik terakhir, buat LED
static bool clipping_terakhir = false;
static hw_timer_t *timer = nullptr;
static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

// ISR sengaja cuma menaikkan penanda; analogRead() tidak aman dipanggil di sini.
void IRAM_ATTR on_timer()
{
    portENTER_CRITICAL_ISR(&mux);
    if (waktunya) n_lewat++;               // loop() belum sempat mengambil
    waktunya = true;
    portEXIT_CRITICAL_ISR(&mux);
}

static void led(uint8_t r, uint8_t g, uint8_t b) { neopixelWrite(PIN_LED, r, g, b); }
static bool elektroda_lepas() { return digitalRead(PIN_LOP) || digitalRead(PIN_LON); }

static bool ditekan(int pin, uint32_t &terakhir, bool &sebelumnya)
{
    const bool kini = (digitalRead(pin) == LOW);
    const uint32_t t = millis();
    bool tepi = false;
    if (kini != sebelumnya && t - terakhir > DEBOUNCE_MS) {
        tepi = kini;
        sebelumnya = kini;
        terakhir = t;
    }
    return tepi;
}

static void mulai_rekam()
{
    // Lead-off cuma PERINGATAN, bukan penolakan: deteksi DC AD8232 bisa tetap
    // HIGH walau elektroda menempel (gel kering, impedansi tinggi) sementara
    // sinyalnya sendiri sudah bagus. Yang menentukan layak-tidaknya rekaman
    // adalah analisis sinyal di model/scripts/, bukan pin ini.
    if (elektroda_lepas()) {
        Serial.println("PERINGATAN: LO menandakan elektroda lepas — rekam tetap jalan.");
    }
    n_sampel = 0;
    n_lewat = 0;
    rekam = true;
    timerAlarmEnable(timer);
    Serial.printf("REKAM mulai — %u Hz, maks %u detik\n", ECG_FS, DETIK_MAKS);
}

static void simpan()
{
    timerAlarmDisable(timer);
    rekam = false;
    const size_t n = n_sampel;

    File f = LittleFS.open(BERKAS, "w");
    if (!f) { Serial.println("GAGAL membuka LittleFS"); return; }
    f.printf("# fs=%u n=%u lewat=%u\n", ECG_FS, (unsigned)n, (unsigned)n_lewat);
    for (size_t i = 0; i < n; i++) f.printf("%u\n", buf[i]);
    f.close();
    Serial.printf("SIMPAN %u sampel (%.1f detik), %u terlewat -> %s\n",
                  (unsigned)n, (float)n / ECG_FS, (unsigned)n_lewat, BERKAS);
}

static void dump()
{
    File f = LittleFS.open(BERKAS, "r");
    if (!f) { Serial.println("Belum ada rekaman."); return; }
    Serial.println("---MULAI---");
    while (f.available()) Serial.write(f.read());
    Serial.println("---SELESAI---");
    f.close();
}

void setup()
{
    Serial.begin(115200);
    delay(1500);
    pinMode(PIN_LOP, INPUT);
    pinMode(PIN_LON, INPUT);
    pinMode(PIN_REC, INPUT_PULLUP);
    pinMode(PIN_DUMP, INPUT_PULLUP);
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);

    // Buffer di PSRAM: 108.000 x 2 byte = 216 KB.
    buf = (uint16_t *)ps_malloc(N_MAKS * sizeof(uint16_t));
    if (!buf) buf = (uint16_t *)malloc(N_MAKS * sizeof(uint16_t));
    if (!buf) {
        Serial.println("FATAL: alokasi buffer gagal");
        while (true) { led(64, 0, 0); delay(300); led(0, 0, 0); delay(300); }
    }
    if (!LittleFS.begin(true)) Serial.println("PERINGATAN: LittleFS gagal mount");

    timer = timerBegin(0, 80, true);                 // 80 MHz / 80 = 1 MHz
    timerAttachInterrupt(timer, &on_timer, true);
    timerAlarmWrite(timer, 1000000 / ECG_FS, true);  // 2778 us = 360 Hz

    Serial.printf("\n=== AKUISISI EKG SIAP ===\nREC=GPIO%d  DUMP=GPIO%d  fs=%u Hz  buffer %u detik\n",
                  PIN_REC, PIN_DUMP, ECG_FS, DETIK_MAKS);
}

void loop()
{
    static uint32_t t_rec = 0, t_dump = 0;
    static bool s_rec = false, s_dump = false;

    if (rekam) {
        bool ambil = false;
        portENTER_CRITICAL(&mux);
        if (waktunya) { waktunya = false; ambil = true; }
        portEXIT_CRITICAL(&mux);
        if (ambil) {
            buf[n_sampel++] = (uint16_t)analogRead(PIN_EKG);
            if (n_sampel >= N_MAKS) { Serial.println("Buffer penuh."); simpan(); }
        }
    }

    // Perintah serial: setara tombol, tapi bisa dipicu dari laptop sehingga
    // tidak bergantung pada timing tekan-tombol saat sedang menyimak.
    //   r = rekam mulai/berhenti   d = dump   s = status sekali
    if (Serial.available()) {
        const char c = Serial.read();
        if (c == 'r')      rekam ? simpan() : mulai_rekam();
        else if (c == 'd') { if (!rekam) dump(); else Serial.println("Sedang merekam."); }
        else if (c == 's') Serial.printf("status: rekam=%d n=%u LO %d %d\n",
                                         (int)rekam, (unsigned)n_sampel,
                                         digitalRead(PIN_LOP), digitalRead(PIN_LON));
    }

    if (ditekan(PIN_REC, t_rec, s_rec))  rekam ? simpan() : mulai_rekam();
    if (ditekan(PIN_DUMP, t_dump, s_dump)) {
        if (rekam) Serial.println("DUMP diabaikan saat merekam (mengganggu timing).");
        else dump();
    }

    // Status berkala saat idle — sekaligus alat diagnosis di meja kerja.
    // gpio7 dipakai sebagai "voltmeter": pindahkan jumpernya ke pin modul yang
    // ingin diukur (3.3V, OUTPUT, ...). 4095 ~ 3,1 V.
    static uint32_t t_status = 0;
    if (!rekam && millis() - t_status > 1000) {
        t_status = millis();
        // Ambil 1 detik pada 360 Hz lalu lewatkan bandpass yang SAMA dengan
        // pipeline. 50 Hz ada di luar pita 0,5-40 Hz, jadi ayunan setelah
        // filter mencerminkan sinyal jantung, bukan dengung.
        static float mentah[ECG_FS], tersaring[ECG_FS];
        int mn = 4095, mx = 0; long jml = 0;
        for (int i = 0; i < ECG_FS; i++) {
            const int v = analogRead(PIN_EKG);
            mentah[i] = (float)v;
            if (v < mn) mn = v;
            if (v > mx) mx = v;
            jml += v;
            delayMicroseconds(2778);
        }
        // Buang DC SEBELUM difilter. Highpass 0,5 Hz punya tetapan waktu ~0,3 s;
        // menyuapkan step DC ~3300 counts menghasilkan transien raksasa yang
        // menutupi sinyal selama ratusan sampel.
        const float rerata = (float)jml / ECG_FS;
        for (int i = 0; i < ECG_FS; i++) mentah[i] -= rerata;
        float st[ECG_N_SOS * 2];
        memset(st, 0, sizeof(st));
        ecg_bandpass(mentah, tersaring, ECG_FS, st);

        // Tetap lewati 180 sampel (0,5 detik) sebagai sisa transien.
        float fmn = 1e9f, fmx = -1e9f;
        for (int i = 180; i < ECG_FS; i++) {
            if (tersaring[i] < fmn) fmn = tersaring[i];
            if (tersaring[i] > fmx) fmx = tersaring[i];
        }
        ayun_terakhir = (int)(fmx - fmn);
        clipping_terakhir = (mx >= 4090 || mn <= 5);
        Serial.printf("idle | mentah %4d..%4d avg %4d | TERSARING ayun %4d | LO %d %d\n",
                      mn, mx, (int)(jml / ECG_FS), ayun_terakhir,
                      digitalRead(PIN_LOP), digitalRead(PIN_LON));
    }

    // LED menunjukkan KUALITAS SINYAL, bukan pin LO — deteksi lead-off AD8232
    // ternyata tetap HIGH walau detak tertangkap, jadi tak berguna sbg indikator.
    // Ini satu-satunya umpan balik saat jalan dengan powerbank.
    //   hijau       : ayunan sehat, siap rekam
    //   oranye      : ayunan terlalu kecil — elektroda kurang kontak
    //   merah kedip : clipping, sinyal terpotong
    //   merah tetap : sedang merekam
    static uint32_t t_led = 0;
    static bool nyala = false;
    if (millis() - t_led > 250) {
        t_led = millis();
        nyala = !nyala;
        if (rekam)                       led(64, 0, 0);
        else if (clipping_terakhir)      led(nyala ? 80 : 0, 0, 0);
        else if (ayun_terakhir < 60)     led(64, 24, 0);   // ayunan TERSARING
        else                             led(0, 48, 0);
    }
}
#endif
