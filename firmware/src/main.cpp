// Firmware utama: akuisisi + klasifikasi aritmia langsung di alat.
//
// ADC dibaca di timer ISR 360 Hz dan ditaruh ke antrean; loop utama yang
// menguras dan memproses. Pemisahan ini WAJIB: beban pemrosesan menggumpal —
// rata-rata 82 us/sampel tapi puncaknya 33 ms saat deteksi dan inferensi
// bersamaan. Kalau ADC dibaca di loop, ~12 sampel hilang tiap detik dan
// interval RR rusak (docs/firmware-walkthrough.md §5b).
#ifndef PIO_UNIT_TESTING
#include <Arduino.h>
#include <LittleFS.h>
#include <string.h>
#include "driver/adc.h"

#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"
#if __has_include("tensorflow/lite/micro/micro_error_reporter.h")
#include "tensorflow/lite/micro/micro_error_reporter.h"
#define TFLM_PUNYA_ERROR_REPORTER 1
#endif

#include "ecg_live.h"
#include "model_int8.h"

constexpr adc1_channel_t KANAL_EKG = ADC1_CHANNEL_7;   // GPIO 8 (ADC1_CH7)
constexpr int PIN_LOP = 17, PIN_LON = 7;
constexpr int PIN_REC = 6, PIN_DUMP = 5, PIN_LED = 48;

constexpr size_t ANTRE_N = 256;            // >= 13 (puncak burst), dibulatkan pangkat 2
constexpr uint32_t DETIK_MAKS = 300;
constexpr size_t REKAM_N = (size_t)ECG_FS * DETIK_MAKS;
constexpr const char *BERKAS = "/rekaman.csv";
constexpr int ARENA_N = 24 * 1024;

// Ambang kualitas sinyal, dari akuisisi-walkthrough.md §2 (angka empiris, bukan
// tebakan: kontak segar 691 counts, elektroda dipakai ulang 195).
constexpr int AMBANG_AYUN = 60;            // ayunan TERSARING 1 detik, counts ADC
constexpr int ADC_ATAS = 4090, ADC_BAWAH = 5;

// Bandpass 0,5-40 Hz TIDAK membunuh 50 Hz, cuma meredamnya -9,3 dB (diukur dari
// ecg_sos dengan sosfreqz). Jadi dengung jala-jala tetap masuk hitungan ayunan
// dan bisa memalsukan LED hijau. Kontribusinya diukur dengan Goertzel lalu
// dikurangkan. 50 Hz x 1 detik = 50 siklus bulat, jadi binnya tepat.
constexpr float GAIN_50HZ = 0.342f;

static volatile uint16_t antre[ANTRE_N];
static volatile size_t tulis, baca;
static volatile uint32_t n_lewat;          // antrean penuh = sampel hilang
static hw_timer_t *timer;

static uint16_t *rekam_buf;
static volatile size_t rekam_n;
static volatile bool rekam;
static size_t rekam_lepas;                 // sampel dgn LO aktif selama merekam

alignas(16) static uint8_t arena[ARENA_N];
static tflite::MicroInterpreter *interp;
static TfLiteTensor *in_morph, *in_rr, *keluar;

static int beat_total, beat_aritmia;

// Kualitas sinyal 1 detik terakhir (dipakai LED + laporan serial).
static int ayun_1s, ayun_bersih_1s, hum50_1s, mentah_min_1s, mentah_maks_1s;
static bool clipping_1s;
static bool lapor_kualitas;                // toggle 'q': cetak tiap detik

void IRAM_ATTR on_timer()
{
    const size_t berikut = (tulis + 1) % ANTRE_N;
    if (berikut == baca) { n_lewat++; return; }        // loop ketinggalan
    antre[tulis] = (uint16_t)adc1_get_raw(KANAL_EKG);  // cepat, aman di ISR
    tulis = berikut;
}

static void led(uint8_t r, uint8_t g, uint8_t b) { neopixelWrite(PIN_LED, r, g, b); }

static void siapkan_model()
{
    const tflite::Model *m = tflite::GetModel(model_int8_tflite);
    static tflite::MicroMutableOpResolver<8> res;
    res.AddConv2D(); res.AddDepthwiseConv2D(); res.AddMaxPool2D();
    res.AddConcatenation(); res.AddLogistic(); res.AddAdd();
    res.AddReshape(); res.AddExpandDims();
#ifdef TFLM_PUNYA_ERROR_REPORTER
    static tflite::MicroErrorReporter lapor;
    static tflite::MicroInterpreter it(m, res, arena, ARENA_N, &lapor);
#else
    static tflite::MicroInterpreter it(m, res, arena, ARENA_N);
#endif
    interp = &it;
    if (interp->AllocateTensors() != kTfLiteOk) {
        Serial.println("FATAL: AllocateTensors gagal");
        while (true) { led(64, 0, 0); delay(200); led(0, 0, 0); delay(200); }
    }
    TfLiteTensor *a = interp->input(0), *b = interp->input(1);
    const bool a_kecil = a->bytes < b->bytes;
    in_rr = a_kecil ? a : b;
    in_morph = a_kecil ? b : a;
    keluar = interp->output(0);
}

static int8_t ke_int8(float x, float skala, int nol)
{
    long q = lroundf(x / skala) + nol;
    if (q < -128) q = -128;
    if (q > 127) q = 127;
    return (int8_t)q;
}

static float klasifikasi(const ecg_beat_t &beat)
{
    for (int i = 0; i < ECG_WIN_LEN_; i++)
        in_morph->data.int8[i] = ke_int8(beat.window[i], ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO);
    for (int i = 0; i < ECG_N_RR; i++)
        in_rr->data.int8[i] = ke_int8(beat.rr[i], ECG_IN_RR_SCALE, ECG_IN_RR_ZERO);
    interp->Invoke();
    return (keluar->data.int8[0] - ECG_OUT_ZERO) * ECG_OUT_SCALE;
}

static void simpan()
{
    rekam = false;
    File f = LittleFS.open(BERKAS, "w");
    if (!f) { Serial.println("GAGAL membuka LittleFS"); return; }
    // 'lepas' menjawab yang tidak bisa dijawab data mentah: apakah elektroda
    // benar-benar menempel saat rekaman dibuat? AD8232 memarkir output di
    // mid-rail saat leads-off, dan garis datar itu menyamar sebagai "sinyal
    // tenang" di CSV.
    f.printf("# fs=%u n=%u lewat=%u lepas=%u (%.0f%%)\n", ECG_FS, (unsigned)rekam_n,
             (unsigned)n_lewat, (unsigned)rekam_lepas,
             rekam_n ? 100.0f * rekam_lepas / rekam_n : 0.0f);
    for (size_t i = 0; i < rekam_n; i++) f.printf("%u\n", rekam_buf[i]);
    f.close();
    Serial.printf("SIMPAN %u sampel (%.1f detik), %u terlewat, elektroda lepas %.0f%% -> %s\n",
                  (unsigned)rekam_n, (float)rekam_n / ECG_FS, (unsigned)n_lewat,
                  rekam_n ? 100.0f * rekam_lepas / rekam_n : 0.0f, BERKAS);
    if (rekam_lepas > rekam_n / 10)
        Serial.println("PERINGATAN: elektroda lepas >10% — rekaman ini kemungkinan besar kosong.");
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

// Menilai kualitas sinyal tiap 1 detik, lalu menyetir LED.
//
// Ayunan diukur pada sinyal SETELAH bandpass 0,5-40 Hz, bukan ADC mentah:
// dengung 50 Hz ada di luar pita, jadi kabel yang dipenuhi jala-jala tidak
// lagi terbaca "kuat". Clipping tetap dinilai dari ADC mentah — begitu
// terpotong di rail, informasinya sudah hilang sebelum filter.
static void nilai_kualitas(float mentah)
{
    static size_t n;
    static float f_min, f_maks;
    static int m_min, m_maks;

    static float g1, g2;
    static const float koef = 2.0f * cosf(2.0f * (float)M_PI * 50.0f / ECG_FS);

    const float f = ecg_live_tersaring_terakhir();
    const int m = (int)mentah;
    if (n == 0) { f_min = f_maks = f; m_min = m_maks = m; g1 = g2 = 0.0f; }

    const float g0 = koef * g1 - g2 + mentah;   // Goertzel bin 50 Hz
    g2 = g1; g1 = g0;

    if (f < f_min) f_min = f;
    if (f > f_maks) f_maks = f;
    if (m < m_min) m_min = m;
    if (m > m_maks) m_maks = m;

    if (++n < ECG_FS) return;              // satu jendela = 1 detik
    n = 0;
    ayun_1s = (int)(f_maks - f_min);
    // Amplitudo puncak 50 Hz -> puncak-ke-puncak -> porsinya yang lolos filter.
    const float amp50 = 2.0f * sqrtf(fmaxf(g1 * g1 + g2 * g2 - koef * g1 * g2, 0.0f)) / ECG_FS;
    hum50_1s = (int)(2.0f * amp50);
    ayun_bersih_1s = (int)fmaxf(ayun_1s - GAIN_50HZ * 2.0f * amp50, 0.0f);
    mentah_min_1s = m_min;
    mentah_maks_1s = m_maks;
    clipping_1s = (m_maks >= ADC_ATAS || m_min <= ADC_BAWAH);
    if (lapor_kualitas)
        Serial.printf("kualitas | mentah %4d..%4d | ayun %4d - dengung50 %4d = "
                      "BERSIH %4d (ambang %d) | clipping %d | LO %d %d\n",
                      mentah_min_1s, mentah_maks_1s, ayun_1s, hum50_1s,
                      ayun_bersih_1s, AMBANG_AYUN,
                      (int)clipping_1s, digitalRead(PIN_LOP), digitalRead(PIN_LON));
}

// Arti LED (akuisisi-walkthrough.md §2):
//   merah  : sedang merekam — HANYA itu, tidak ada arti lain
//   oranye : ayunan BERSIH < ambang — kontak kurang / dengung dominan
//   hijau  : ayunan sehat, siap rekam
// Tiga keadaan, tanpa kedip. Clipping DULU punya pola merah kedip sendiri;
// dicabut karena menumpuk arti di satu warna dan bikin merah ambigu. Clipping
// tetap dihitung dan dilaporkan lewat serial ('q' tiap detik, 's' sesaat) —
// yang hilang cuma penanda visualnya, jadi sinyal terpotong kini tampil HIJAU.
// LO+/LO- SENGAJA tidak dipakai menyetir LED: ia hanya melaporkan elektroda
// lepas total, dan pada 3-lead tanpa RL yang rapat ia menyala terus walau
// sinyalnya sebenarnya bagus. Ayunan mengukur yang benar-benar kita butuhkan.
static void perbarui_led()
{
    static uint32_t t_led = 0;

    if (millis() - t_led < 250) return;    // neopixelWrite matikan interrupt ~30 us
    t_led = millis();

    if (rekam)                             led(64, 0, 0);
    else if (ayun_bersih_1s < AMBANG_AYUN) led(64, 24, 0);
    else                                   led(0, 48, 0);
}

static bool ditekan(int pin, uint32_t &terakhir, bool &sebelumnya)
{
    const bool kini = (digitalRead(pin) == LOW);
    const uint32_t t = millis();
    bool tepi = false;
    if (kini != sebelumnya && t - terakhir > 50) {
        tepi = kini; sebelumnya = kini; terakhir = t;
    }
    return tepi;
}

void setup()
{
    Serial.begin(115200);
    delay(1500);
    // INPUT_PULLUP, bukan INPUT: kalau kabel LO putus/lepas, pin terbaca HIGH
    // = "elektroda lepas". Pin mengambang yang kebetulan terbaca LOW pernah
    // menipu kami — ia melaporkan "elektroda menempel" untuk kabel yang tidak
    // tersambung ke apa pun. Output LO AD8232 push-pull, jadi pull-up internal
    // 45k tidak melawannya.
    pinMode(PIN_LOP, INPUT_PULLUP); pinMode(PIN_LON, INPUT_PULLUP);
    pinMode(PIN_REC, INPUT_PULLUP); pinMode(PIN_DUMP, INPUT_PULLUP);

    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(KANAL_EKG, ADC_ATTEN_DB_11);

    rekam_buf = (uint16_t *)ps_malloc(REKAM_N * sizeof(uint16_t));
    if (!rekam_buf) Serial.println("PERINGATAN: PSRAM gagal, perekaman mentah nonaktif");
    if (!LittleFS.begin(true)) Serial.println("PERINGATAN: LittleFS gagal mount");

    siapkan_model();
    ecg_live_reset();

    timer = timerBegin(0, 80, true);
    timerAttachInterrupt(timer, &on_timer, true);
    timerAlarmWrite(timer, 1000000 / ECG_FS, true);
    timerAlarmEnable(timer);

    Serial.printf("\n=== MONITOR ARITMIA SIAP ===\n"
                  "fs=%u Hz  antrean=%u  arena=%u B  threshold=%.2f\n"
                  "REC=GPIO%d  DUMP=GPIO%d  |  serial: r/d/s/q\n",
                  ECG_FS, (unsigned)ANTRE_N, (unsigned)interp->arena_used_bytes(),
                  ECG_THRESHOLD, PIN_REC, PIN_DUMP);
}

void loop()
{
    static ecg_beat_t beat;
    static uint32_t t_rec = 0, t_dump = 0;
    static bool s_rec = false, s_dump = false;

    // Kuras antrean ISR. Satu sampel per iterasi supaya tombol & serial tetap
    // responsif; beban 3% membuat antrean selalu terkejar.
    if (baca != tulis) {
        const float sampel = (float)antre[baca];
        baca = (baca + 1) % ANTRE_N;

        if (rekam && rekam_buf && rekam_n < REKAM_N) {
            rekam_buf[rekam_n++] = (uint16_t)sampel;
            if (digitalRead(PIN_LOP) || digitalRead(PIN_LON)) rekam_lepas++;
        }

        const int ada_beat = ecg_live_push(sampel, &beat);
        nilai_kualitas(sampel);            // SETELAH push: baca sampel tersaring terbaru

        if (ada_beat) {
            const float p = klasifikasi(beat);
            const bool aritmia = p >= ECG_THRESHOLD;
            beat_total++;
            if (aritmia) beat_aritmia++;
            // BPM dari RR_prev, BUKAN dari selisih millis(): beat keluar
            // bergerombol setelah deteksi berkala, jadi jarak waktu antar-cetak
            // tidak sama dengan jarak antar-detak.
            const float bpm = (beat.rr[0] > 0.05f) ? 60.0f / beat.rr[0] : 0.0f;
            Serial.printf("beat %4d  p=%.4f  %-7s  RR=%.3fs  %3.0f bpm\n",
                          beat_total, p, aritmia ? "ARITMIA" : "normal", beat.rr[0], bpm);
        }
    }

    perbarui_led();

    if (Serial.available()) {
        const char c = Serial.read();
        if (c == 'r') { if (rekam) simpan(); else { rekam_n = rekam_lepas = n_lewat = 0; rekam = true; Serial.println("REKAM mulai"); } }
        else if (c == 'd') { if (!rekam) dump(); else Serial.println("Sedang merekam."); }
        else if (c == 'q') {
            lapor_kualitas = !lapor_kualitas;
            Serial.printf("laporan kualitas %s\n", lapor_kualitas ? "ON" : "OFF");
        }
        else if (c == 's')
            Serial.printf("status: rekam=%d n=%u | beat %d (%d aritmia) | "
                          "antrean %u | sampel hilang %u | LO %d %d | "
                          "mentah %d..%d ayun %d clipping %d\n",
                          (int)rekam, (unsigned)rekam_n, beat_total, beat_aritmia,
                          (unsigned)((tulis - baca + ANTRE_N) % ANTRE_N), (unsigned)n_lewat,
                          digitalRead(PIN_LOP), digitalRead(PIN_LON),
                          mentah_min_1s, mentah_maks_1s, ayun_bersih_1s, (int)clipping_1s);
    }

    if (ditekan(PIN_REC, t_rec, s_rec)) {
        if (rekam) simpan(); else { rekam_n = rekam_lepas = n_lewat = 0; rekam = true; Serial.println("REKAM mulai"); }
    }
    if (ditekan(PIN_DUMP, t_dump, s_dump)) {
        if (rekam) Serial.println("DUMP diabaikan saat merekam."); else dump();
    }
}
#endif
