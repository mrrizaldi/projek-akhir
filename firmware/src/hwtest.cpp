// Uji hardware PCB rev1 di breadboard: AD8232 + TFT ST7789 + modul buzzer + 3 tombol.
// Terpisah dari firmware utama:  pio run -e hwtest -t upload && pio device monitor
//
// Simulasi tanpa elektroda: HWTEST_SIM (build flag di platformio.ini) memilih
// sumber sinyal awal. 0 = ADC AD8232, 1 = TERATUR (satu beat Normal golden_raw
// diulang pada BPM tetap, untuk menilai bip dengan telinga), 2 = REKAMAN 208
// (golden_raw apa adanya: 6 dari 9 beat abnormal, ritme memang acak).
// Serial: 'y' = ganti sumber, '+'/'-' = BPM dummy teratur +-10,
//         '['/']' = nada buzzer -+250 Hz (bunyi 300 ms untuk dibandingkan).
//         'r' rekam, 'd' dump, 's' status, 'a' alir mentah, 'g' diagnosa buzzer.
//
// Layar (landscape 320x172):
//   atas   HR dari detektor yang SAMA dengan firmware (ecg_live) + arus/tegangan
//          INA219 + status rekam (REC detik) / sumber (EKG, TERATUR, REKAMAN)
//   tengah gelombang EKG tersaring 0,5-40 Hz, skala otomatis per sapuan
//   bawah  tiga kotak tombol, kuning selama ditekan
// Tombol: B1 bisu/bunyi beep per beat (tahan 2 detik = ganti sumber seperti
// 'y', bunyi 300 ms), B2 bekukan gelombang + bip beat (state sendiri, bukan
// BISU: lepas beku = bip jalan lagi sesuai B1), B3 REKAM (mulai/
// simpan). Rekaman = ADC mentah, format & protokol serial SAMA dengan main.cpp
// ('r' rekam, 'd' dump, 's' status), jadi `make pull` di model/ langsung jalan.
#ifndef HWTEST_SIM
#define HWTEST_SIM 0
#endif
enum Sumber
{
    ADC,
    TERATUR,
    REKAMAN
};
#include <Arduino.h>
#include <SPI.h>
#include <LittleFS.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include "driver/adc.h"
#include "driver/ledc.h"

#include "ecg_live.h"
#include "ina219.h"
#include "golden_ref.h"

// Pin map PCB rev1 (schematic_rev_1.pdf). TFT CS diikat ke GND.
constexpr adc1_channel_t KANAL_EKG = ADC1_CHANNEL_0; // GPIO 1
constexpr int PIN_LON = 2, PIN_LOP = 42;
constexpr int TFT_SCK = 9, TFT_MOSI = 8, TFT_RST = 10, TFT_DC = 11;
// Modul buzzer 3 pin (VCC, GND, I/O) berisi transistor: I/O LOW = BUNYI,
// HIGH = diam (deskripsi produk A07009/A18009). Jadi diam = HIGH, bukan LOW.
// BUZZER_PASIF=1 (A18009): gelombang kotak LEDC, keluarannya dibalik.
// BUZZER_PASIF=0 (A07009): osilator di dalam, cukup LOW = bunyi.
#ifndef BUZZER_PASIF
#define BUZZER_PASIF 1
#endif
constexpr int PIN_BUZZ = 13, KANAL_BUZZ = 0;
// Knob: buzzer pasif paling keras di frekuensi resonansinya, beda per part.
// Cari dengan '[' / ']' di serial, lalu kunci angkanya di sini.
static uint32_t nada_hz = 2000;
constexpr uint32_t BIP_MS = 50;
constexpr int PIN_BTN[3] = {4, 5, 6};     // ke GND, pull-up internal.
constexpr int I2C_SDA = 17, I2C_SCL = 18; // INA219, VCC modul WAJIB 3V3
// Knob kalibrasi: koreksi kalau multimeter tidak setuju,
// R_baru = R_lama x (I_ina219 / I_multimeter).
constexpr float R_SHUNT = 0.1f;

constexpr int W = 320, H = 172;
constexpr int GY = 30, GH = 112; // area gelombang
constexpr int DESIMASI = 3;      // 120 px/detik -> 320 px = 2,7 detik
constexpr uint16_t ABU = 0x4208;

static Adafruit_ST7789 tft(-1, TFT_DC, TFT_RST);

// ISR 360 Hz -> antrean -> loop, pola yang sama dengan main.cpp: menggambar ke
// TFT memblok loop, jadi ADC tidak boleh dibaca dari loop.
constexpr size_t ANTRE_N = 256;
static volatile uint16_t antre[ANTRE_N];
static volatile size_t tulis, baca;
static volatile uint32_t n_lewat;
static hw_timer_t *timer;
// Sampel yang SUDAH masuk antrean = jam sampel waktu nyata. Indeksnya sama
// dengan r_abs ecg_live (keduanya menghitung sampel yang lolos antrean).
static volatile uint32_t n_masuk;

// Replay: salinan teknik main.cpp. Konversi float di setup(), ISR cuma menyalin
// integer (float di ISR = panic Coprocessor exception setelah ~18 detik).
static volatile Sumber sumber = (Sumber)HWTEST_SIM;
static volatile size_t replay_i;
static uint16_t sim_counts[GOLDEN_N];
// Dummy teratur: beat N golden (R di sampel 1181) dari R-100 sampai R+150.
// Di sela beat, sampel terakhir ditahan. Diuji di PC 30-180 bpm: HR terbaca
// persis target, RR meleset 0 sampel.
constexpr int R_TMPL = 1181, PRE_TMPL = 100, L_TMPL = 250;
static uint16_t tmpl_counts[L_TMPL];
static volatile uint32_t periode = 60 * ECG_FS / 75;
static int bpm_dummy = 75;

void IRAM_ATTR on_timer()
{
    const size_t berikut = (tulis + 1) % ANTRE_N;
    if (berikut == baca)
    {
        n_lewat++;
        return;
    }
    if (sumber == REKAMAN)
    {
        antre[tulis] = sim_counts[replay_i];
        replay_i = (replay_i + 1) % GOLDEN_N;
    }
    else if (sumber == TERATUR)
    {
        const size_t i = replay_i;
        antre[tulis] = tmpl_counts[i < L_TMPL ? i : L_TMPL - 1];
        replay_i = (i + 1) % periode;
    }
    else
        antre[tulis] = (uint16_t)adc1_get_raw(KANAL_EKG);
    tulis = berikut;
    n_masuk++;
}

static void siapkan_replay()
{
    for (size_t i = 0; i < GOLDEN_N; i++)
        sim_counts[i] = (uint16_t)constrain(golden_raw[i] * 1000.0f + 2048.0f, 0.0f, 4095.0f);
    for (int i = 0; i < L_TMPL; i++)
        tmpl_counts[i] = sim_counts[R_TMPL - PRE_TMPL + i];
}

static const char *nama_sumber()
{
    return sumber == TERATUR ? "TERATUR" : sumber == REKAMAN ? "REKAMAN"
                                                             : "ADC";
}

// ADC -> TERATUR -> REKAMAN -> ADC. Dipakai serial 'y' dan B1 tahan 2 detik.
static void ganti_sumber()
{
    replay_i = 0;
    sumber = (Sumber)((sumber + 1) % 3);
    Serial.printf("sumber: %s\n", nama_sumber());
}

static bool bisu, beku;
static int bpm, n_beat, r_lalu = -1;
static uint32_t buzz_sampai;
static uint16_t mentah_min = 4095, mentah_maks;
static uint32_t push_maks_us; // burst deteksi; antrean 256 = 711 ms anggaran
// Jeda terlama antar-putaran loop(). Bip dimatikan dari loop, jadi loop yang
// macet X ms = bip memanjang X ms (gejala "tittttt" panjang).
static uint32_t loop_maks_ms;
static bool alir_mentah; // serial 'a': tiap sampel ADC dicetak "m,<counts>" untuk analisis di PC

// Rekaman mentah di PSRAM, disimpan ke LittleFS saat berhenti. Batas 5 menit
// (216 KB), sama dengan main.cpp.
constexpr size_t REKAM_N = (size_t)ECG_FS * 300;
constexpr const char *BERKAS = "/rekaman.csv";
static uint16_t *rekam_buf;
static size_t rekam_n, rekam_lepas;
static bool rekam;
static bool ina_ada;

// Diam DULU: modul aktif-LOW, pin yang belum di-set bisa berarti bunyi.
static void pasang_buzzer()
{
    pinMode(PIN_BUZZ, OUTPUT);
    digitalWrite(PIN_BUZZ, HIGH);
#if BUZZER_PASIF
    ledcSetup(KANAL_BUZZ, nada_hz, 8);
    ledc_channel_config_t ch = {};
    ch.gpio_num = PIN_BUZZ;
    ch.speed_mode = LEDC_LOW_SPEED_MODE;
    ch.channel = (ledc_channel_t)KANAL_BUZZ;
    ch.timer_sel = LEDC_TIMER_0; // kanal 0 -> timer 0, sama dengan ledcSetup
    ch.duty = 0;
    ch.flags.output_invert = 1;
    ledc_channel_config(&ch);
#endif
}

// Diagnosa rangkaian (serial 'g'): GPIO 13 dipaksa ke 4 keadaan, 3 dtk tiap
// fase, nama fase di layar. Modul pasif aktif-LOW yang benar: hanya fase 3
// yang berbunyi panjang (fase 2 boleh "klik" sekali). Bunyi di fase 1 atau 4
// = rangkaian, bukan firmware. Selama diagnosa, bip beat dibungkam.
static int diag = -1;
static uint32_t diag_t;

static void diag_fase()
{
    static const char *const NAMA[4] = {"1 HIGH=diam", "2 LOW (DC) ", "3 PWM 2kHz ", "4 LEPAS    "};
    ledcDetachPin(PIN_BUZZ);
    if (diag == 0)
    {
        pinMode(PIN_BUZZ, OUTPUT);
        digitalWrite(PIN_BUZZ, HIGH);
    }
    if (diag == 1)
    {
        pinMode(PIN_BUZZ, OUTPUT);
        digitalWrite(PIN_BUZZ, LOW);
    }
    if (diag == 2)
    {
        ledcSetup(KANAL_BUZZ, 2000, 8);
        ledcAttachPin(PIN_BUZZ, KANAL_BUZZ);
        ledcWrite(KANAL_BUZZ, 128);
    }
    if (diag == 3)
        pinMode(PIN_BUZZ, INPUT);
    tft.fillRect(0, GY, W, GH, ST77XX_BLACK);
    tft.setTextSize(3);
    tft.setTextColor(ST77XX_YELLOW, ST77XX_BLACK);
    tft.setCursor(10, GY + 40);
    tft.print(NAMA[diag]);
    Serial.printf("diagnosa buzzer: fase %s\n", NAMA[diag]);
}

static void diag_jalan()
{
    if (diag < 0 || millis() - diag_t < 3000)
        return;
    diag_t = millis();
    if (++diag < 4)
        return diag_fase();
    diag = -1;
    tft.fillRect(0, GY, W, GH, ST77XX_BLACK);
    pasang_buzzer();
    Serial.println("diagnosa buzzer: selesai");
}

static void buzzer(bool nyala)
{
    if (diag >= 0)
        return;
#if BUZZER_PASIF
    ledcWriteTone(KANAL_BUZZ, nyala ? nada_hz : 0); // duty 0 + invert = HIGH = diam
#else
    digitalWrite(PIN_BUZZ, nyala ? LOW : HIGH);
#endif
}

static uint32_t n_bip; // bip per detik di baris status: 0 = firmware tidak membunyikan apa pun

static void bunyi(uint32_t ms)
{
    n_bip++;
    buzzer(true);
    buzz_sampai = millis() + ms;
}

// Bip per beat, SINKRON dengan ritme. ecg_live mengeluarkan beat berkelompok
// tiap 1 detik, 0,36-1,36 detik sesudah R terjadi; bunyi saat beat keluar =
// dua beat lebur jadi satu bip, laju tertahan ~60/menit. Jadi bip dijadwalkan
// di r_abs + TUNDA: semua bip telat sama rata, jarak antar-bip = RR persis.
// TUNDA = kadens deteksi + post-window (batas telat terburuk) + 0,1 dtk margin
// untuk antrean & burst deteksi.
constexpr uint32_t TUNDA_BIP = ECG_LIVE_TIAP + ECG_WIN_POST + ECG_FS / 10;
constexpr int JADWAL_N = 8; // 250 bpm x 1,46 dtk = 6 bip menunggu
static uint32_t jadwal[JADWAL_N];
static int j_kepala, j_isi;
static uint32_t bip_telat_maks; // sampel; > ~5 berarti TUNDA_BIP kurang

// Gelombang di layar ikut ditunda TUNDA_BIP: R digambar tepat saat bipnya
// berbunyi. Tanpa ini mata melihat R ~0,7 dtk sebelum telinga mendengarnya.
static float tunda_plot[TUNDA_BIP];
static size_t i_plot;

static float tertunda(float f)
{
    const float lama = tunda_plot[i_plot];
    tunda_plot[i_plot] = f;
    i_plot = (i_plot + 1) % TUNDA_BIP;
    return lama;
}

static void bunyi_beat(const ecg_beat_t &b)
{
    if (bisu || j_isi == JADWAL_N)
        return;
    jadwal[(j_kepala + j_isi++) % JADWAL_N] = (uint32_t)b.r_abs + TUNDA_BIP;
}

static void jalankan_jadwal()
{
    const uint32_t kini = n_masuk;
    while (j_isi && (int32_t)(kini - jadwal[j_kepala]) >= 0)
    {
        bip_telat_maks = max(bip_telat_maks, kini - jadwal[j_kepala]);
        j_kepala = (j_kepala + 1) % JADWAL_N;
        j_isi--;
        // Beku dicek di sini, bukan saat dijadwalkan: layar juga ditunda
        // TUNDA_BIP, jadi bip berhenti tepat di R yang terakhir tergambar.
        if (!beku)
            bunyi(BIP_MS);
    }
}

static void saat_beat(const ecg_beat_t &b)
{
    n_beat++;
    if (b.sinyal_hilang)
    {
        bpm = 0;
        r_lalu = -1;
        return;
    } // timeout 3 detik
    if (r_lalu >= 0)
        bpm = (int)lroundf(60.0f * ECG_FS / (float)(b.r_abs - r_lalu));
    r_lalu = b.r_abs;
    bunyi_beat(b);
}

static void mulai_rekam()
{
    if (!rekam_buf)
    {
        Serial.println("PSRAM gagal, rekam nonaktif");
        return;
    }
    rekam_n = rekam_lepas = 0;
    n_lewat = 0;
    rekam = true;
    Serial.println("REKAM mulai");
}

static void simpan()
{
    rekam = false;
    buzzer(false); // menulis file memblok loop ~detik; bip jangan ikut tertahan
    buzz_sampai = 0;
    File f = LittleFS.open(BERKAS, "w");
    if (!f)
    {
        Serial.println("GAGAL membuka LittleFS");
        return;
    }
    // 'lepas' dari pin LO: dicatat apa adanya demi format yang sama dengan
    // main.cpp, TIDAK dipakai menilai (LO terbaca 1 terus walau sinyal ada).
    f.printf("# fs=%u n=%u lewat=%u lepas=%u (%.0f%%)\n", ECG_FS, (unsigned)rekam_n,
             (unsigned)n_lewat, (unsigned)rekam_lepas,
             rekam_n ? 100.0f * rekam_lepas / rekam_n : 0.0f);
    for (size_t i = 0; i < rekam_n; i++)
        f.printf("%u\n", rekam_buf[i]);
    f.close();
    Serial.printf("SIMPAN %u sampel (%.1f detik), %u terlewat -> %s\n",
                  (unsigned)rekam_n, (float)rekam_n / ECG_FS, (unsigned)n_lewat, BERKAS);
}

static void dump()
{
    File f = LittleFS.open(BERKAS, "r");
    if (!f)
    {
        Serial.println("Belum ada rekaman.");
        return;
    }
    Serial.println("---MULAI---");
    while (f.available())
        Serial.write(f.read());
    Serial.println("---SELESAI---");
    f.close();
}

static void gambar_tombol(int i, bool tekan)
{
    static const char *const label[3][2] = {
        {"B1 BUNYI", "B1 BISU"}, {"B2 JALAN", "B2 BEKU"}, {"B3 REC", "B3 STOP"}};
    const bool aktif = (i == 0) ? bisu : (i == 1) ? beku
                                                  : rekam;
    const int x = i * 107;
    const uint16_t bg = tekan ? ST77XX_YELLOW : ABU;
    tft.fillRect(x, 148, 105, 24, bg);
    tft.setTextSize(2);
    tft.setTextColor(tekan ? ST77XX_BLACK : ST77XX_WHITE, bg);
    tft.setCursor(x + 6, 153);
    tft.print(label[i][aktif]);
}

// B1 tahan >= 2 detik = ganti sumber, + bunyi 300 ms (sekalian uji buzzer,
// tidak ikut BISU). Karena itu B1 pendek (bisu) baru bertindak saat DILEPAS.
constexpr uint32_t TAHAN_MS = 2000;

static void tombol()
{
    static bool stabil[3];
    static uint32_t t_ubah[3];
    static bool b1_lama; // tahan sudah dieksekusi: lepasnya bukan toggle bisu
    if (stabil[0] && !b1_lama && millis() - t_ubah[0] >= TAHAN_MS)
    {
        b1_lama = true;
        ganti_sumber();
        bunyi(300);
    }
    for (int i = 0; i < 3; i++)
    {
        const bool kini = digitalRead(PIN_BTN[i]) == LOW;
        if (kini == stabil[i] || millis() - t_ubah[i] < 50)
            continue; // debounce
        stabil[i] = kini;
        t_ubah[i] = millis();
        if (i == 0 && !kini && !b1_lama)
            bisu = !bisu;
        if (kini)
        {
            bunyi(20); // klik
            if (i == 0)
                b1_lama = false;
            if (i == 1)
                beku = !beku;
            if (i == 2)
                rekam ? simpan() : mulai_rekam();
            Serial.printf("tombol B%d (GPIO%d)\n", i + 1, PIN_BTN[i]);
        }
        gambar_tombol(i, kini);
    }
}

static void plot(float f)
{
    static int n, x, y_lalu = GY + GH / 2;
    static float lo = -300, hi = 300, mn = 1e9f, mx = -1e9f;

    mn = fminf(mn, f);
    mx = fmaxf(mx, f);
    if (++n < DESIMASI || beku)
        return;
    n = 0;

    int y = GY + GH - 1 - (int)((f - lo) * (GH - 1) / (hi - lo));
    y = constrain(y, GY, GY + GH - 1);
    tft.fillRect(x, GY, min(4, W - x), GH, ST77XX_BLACK); // hapus di depan kursor
    tft.drawFastVLine(x, min(y, y_lalu), abs(y - y_lalu) + 1, ST77XX_GREEN);
    y_lalu = y;

    if (++x < W)
        return;
    x = 0; // akhir sapuan: skala ulang dari sapuan ini
    const float span = fmaxf(mx - mn, 50.0f);
    lo = mn - 0.1f * span;
    hi = lo + 1.2f * span;
    mn = 1e9f;
    mx = -1e9f;
}

static void status_1hz()
{
    static uint32_t t = 0;
    if (millis() - t < 1000)
        return;
    t = millis();

    // Pin LO TIDAK dipakai menilai: di breadboard ini LO+/LO- terbaca 1 terus
    // walau puncak R jelas terlihat. Cuma dicetak di serial untuk diagnosa.

    tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
    tft.setTextSize(2);
    tft.setCursor(4, 8);
    tft.print("HR");
    tft.setTextSize(3);
    tft.setCursor(32, 3);
    if (bpm > 0)
        tft.printf("%3d", bpm);
    else
        tft.print(" --");
    tft.setTextSize(1);
    tft.setCursor(90, 17);
    tft.print("bpm");

    tft.setTextSize(2);
    tft.setCursor(220, 8);
    if (rekam)
    {
        tft.setTextColor(ST77XX_RED, ST77XX_BLACK);
        tft.printf("REC%4u", (unsigned)(rekam_n / ECG_FS));
    }
    else
    {
        tft.setTextColor(sumber != ADC ? ST77XX_YELLOW : ST77XX_GREEN, ST77XX_BLACK);
        tft.print(sumber == TERATUR ? "TERATUR " : sumber == REKAMAN ? "REKAMAN "
                                                                     : "EKG     ");
    }

    // INA219 di celah x 116..215. Chip sudah merata-rata 128 sampel (~68 ms),
    // jadi satu baca per detik tidak melompat-lompat ikut burst 33 ms.
    float mA = 0, V = 0;
    const bool ina_ok = ina_ada && ina219_baca(R_SHUNT, &mA, &V);
    tft.setTextSize(2);
    tft.setCursor(116, 2);
    tft.setTextColor(ina_ok ? ST77XX_CYAN : ST77XX_RED, ST77XX_BLACK);
    if (ina_ok)
        tft.printf("%4.0fmA", mA);
    else
        tft.print("INA -- ");
    tft.setTextSize(1);
    tft.setCursor(116, 20);
    if (ina_ok)
        tft.printf("%4.2fV %5.0fmW", V, mA * V);
    else
        tft.print("cek SDA17 SCL18");

    Serial.printf("rekam=%d n=%u | %s%s | mentah %4u..%4u | HR %3d | beat %d | bip %u%s, meleset maks %u ms | push maks %u us | loop maks %u ms | LO+ %d LO- %d | lewat %u | ",
                  (int)rekam, (unsigned)rekam_n, nama_sumber(), sumber == TERATUR ? (String(" ") + bpm_dummy).c_str() : "", mentah_min, mentah_maks, bpm, n_beat,
                  (unsigned)n_bip, bisu ? " BISU" : "", (unsigned)(bip_telat_maks * 1000 / ECG_FS), (unsigned)push_maks_us, (unsigned)loop_maks_ms,
                  digitalRead(PIN_LOP), digitalRead(PIN_LON), (unsigned)n_lewat);
    if (ina_ok)
        Serial.printf("I=%.1f mA V=%.3f V P=%.1f mW\n", mA, V, mA * V);
    else
        Serial.println("INA219 tidak menjawab");
    mentah_min = 4095;
    mentah_maks = 0;
    push_maks_us = 0;
    loop_maks_ms = 0;
    n_bip = 0;
    bip_telat_maks = 0; // per detik: yang dilihat kejadian detik ini, bukan sejak boot
}

void setup()
{
    // SPI DULU: miso -1 di S3 BUKAN "tanpa MISO", spiAttachMISO menggantinya
    // dengan default FSPI = GPIO 13 (esp32-hal-spi.c) dan merebut pin buzzer
    // dari LEDC. Gejala: bip terhitung di serial tapi diam sampai 'g' dijalankan.
    SPI.begin(TFT_SCK, -1, TFT_MOSI);
    pasang_buzzer();

    Serial.begin(115200);
    pinMode(PIN_LOP, INPUT_PULLUP); // kabel LO putus = HIGH = "lepas"
    pinMode(PIN_LON, INPUT_PULLUP);
    for (int p : PIN_BTN)
        pinMode(p, INPUT_PULLUP);

    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(KANAL_EKG, ADC_ATTEN_DB_11);

    tft.init(172, 320, SPI_MODE3); // CS ke GND -> wajib mode 3
    tft.setRotation(1);
    tft.fillScreen(ST77XX_BLACK);
    tft.drawFastHLine(0, GY - 2, W, ABU);
    for (int i = 0; i < 3; i++)
        gambar_tombol(i, false);

    ina_ada = ina219_mulai(I2C_SDA, I2C_SCL);
    rekam_buf = (uint16_t *)ps_malloc(REKAM_N * sizeof(uint16_t));
    if (!LittleFS.begin(true))
        Serial.println("PERINGATAN: LittleFS gagal mount");

    siapkan_replay(); // WAJIB sebelum timer jalan
    ecg_live_reset();
    timer = timerBegin(0, 80, true);
    timerAttachInterrupt(timer, &on_timer, true);
    timerAlarmWrite(timer, 1000000 / ECG_FS, true);
    timerAlarmEnable(timer);

    bunyi(100);
    Serial.printf("\n=== HWTEST PCB rev1 === fs=%u Hz | EKG GPIO1, LO+ 42, LO- 2, buzzer %s %d @%u Hz, tombol 4/5/6\n",
                  ECG_FS, BUZZER_PASIF ? "pasif" : "aktif", PIN_BUZZ, (unsigned)nada_hz);
    Serial.printf("sumber: %s | 'y' ganti sumber, '+'/'-' BPM dummy, '['/']' nada, 'r' rekam, 'd' dump, 's' status, 'a' alir mentah, 'g' diagnosa buzzer | layar+bip tertunda %u ms dari R | deteksi tiap %u ms\n",
                  nama_sumber(),
                  (unsigned)(TUNDA_BIP * 1000 / ECG_FS), (unsigned)(ECG_LIVE_TIAP * 1000 / ECG_FS));
    Serial.printf("INA219 (SDA %d, SCL %d, 0x%02X): %s\n", I2C_SDA, I2C_SCL, INA219_ALAMAT,
                  ina_ada ? "siap" : "TIDAK TERDETEKSI");
}

void loop()
{
    static ecg_beat_t beat;
    static uint32_t t_loop = millis();
    loop_maks_ms = max(loop_maks_ms, (uint32_t)(millis() - t_loop));
    t_loop = millis();

    while (baca != tulis)
    {
        const uint16_t s = antre[baca];
        baca = (baca + 1) % ANTRE_N;
        if (alir_mentah)
            Serial.printf("m,%u\n", s);
        if (rekam)
        {
            rekam_buf[rekam_n++] = s;
            if (digitalRead(PIN_LOP) || digitalRead(PIN_LON))
                rekam_lepas++;
            if (rekam_n == REKAM_N)
                simpan(); // penuh 5 menit
        }
        mentah_min = min(mentah_min, s);
        mentah_maks = max(mentah_maks, s);
        const uint32_t t0 = micros();
        const int ada = ecg_live_push((float)s, &beat);
        push_maks_us = max(push_maks_us, (uint32_t)(micros() - t0));
        if (ada)
            saat_beat(beat);
        const float f = tertunda(ecg_live_tersaring_terakhir());
        if (diag < 0) // diagnosa memakai area gelombang untuk nama fase
            plot(f);
    }

    jalankan_jadwal();
    const int c = Serial.read();
    if (c == 'y')
        ganti_sumber();
    else if (c == '+' || c == '-')
    {
        bpm_dummy = constrain(bpm_dummy + (c == '+' ? 10 : -10), 30, 180);
        periode = 60 * ECG_FS / bpm_dummy;
        replay_i = 0;
        Serial.printf("BPM dummy %d\n", bpm_dummy);
    }
    else if (c == 'r')
        rekam ? simpan() : mulai_rekam();
    else if (c == 'd')
        rekam ? (void)Serial.println("Sedang merekam.") : dump();
    else if (c == 's')
        Serial.printf("status: rekam=%d n=%u | sumber %s\n", (int)rekam, (unsigned)rekam_n, nama_sumber());
    else if (c == 'a')
        alir_mentah = !alir_mentah;
    else if (c == 'g' && diag < 0) // diagnosa rangkaian buzzer
    {
        diag = 0;
        diag_t = millis();
        diag_fase();
    }
    else if (c == '[' || c == ']')
    {
        nada_hz = constrain((int)nada_hz + (c == ']' ? 250 : -250), 500, 6000);
        bunyi(300);
        Serial.printf("nada %u Hz\n", (unsigned)nada_hz);
    }
    tombol();
    diag_jalan();
    status_1hz();
    if (buzz_sampai && (int32_t)(millis() - buzz_sampai) >= 0)
    {
        buzzer(false);
        buzz_sampai = 0;
    }
}
