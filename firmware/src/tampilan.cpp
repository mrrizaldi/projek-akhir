#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "tampilan.h"

#include <Arduino.h>
#include <time.h>

#include "akuisisi.h"
#include "daya.h"
#include "gerbang.h"
#include "ina219.h"
#include "perangkat.h"
#include "rekam.h"
#include "tombol.h"

constexpr int GY = 30, GH = 112;
constexpr int DESIMASI = 3;
constexpr uint16_t ABU = 0x4208;
constexpr uint32_t BIP_MS = 50, BIP_ARITMIA_MS = 250;
constexpr uint32_t HR_BASI_MS = 3000;
constexpr uint32_t PERIODE_LED_MS = 250;
constexpr int X_TENGAH = 116, X_KANAN = 220;

static bool bisu, beku;
static bool monitor = true;
static int hr_tampil;
static bool hr_aritmia;
static uint32_t t_hr;
static uint32_t buzz_sampai;

bool tampilan_bisu(void) { return bisu; }
void tampilan_set_bisu(bool on) { bisu = on; }
bool tampilan_beku(void) { return beku; }
void tampilan_set_beku(bool on) { beku = on; }

void tampilan_led(uint8_t r, uint8_t g, uint8_t b) { neopixelWrite(PIN_LED, r, g, b); }

void tampilan_bunyi(uint32_t ms)
{
    buzzer(true);
    buzz_sampai = millis() + ms;
}

constexpr uint32_t TUNDA_BIP = ECG_LIVE_TIAP + ECG_WIN_POST + ECG_FS / 10;
constexpr int JADWAL_N = 8;
static struct { uint32_t sampel; uint16_t ms; } jadwal[JADWAL_N];
static int j_kepala, j_isi;

void tampilan_hapus_jadwal(void) { j_isi = 0; }

static void jadwalkan_bip(const ecg_beat_t &b, bool aritmia)
{
    if (bisu || j_isi == JADWAL_N) return;
    auto &j = jadwal[(j_kepala + j_isi++) % JADWAL_N];
    j.sampel = (uint32_t)b.r_abs + TUNDA_BIP;
    j.ms = aritmia ? BIP_ARITMIA_MS : BIP_MS;
}

static void jalankan_jadwal()
{
    const uint32_t kini = (uint32_t)ecg_live_total_sampel();
    while (j_isi && (int32_t)(kini - jadwal[j_kepala].sampel) >= 0) {
        const uint16_t ms = jadwal[j_kepala].ms;
        j_kepala = (j_kepala + 1) % JADWAL_N;
        j_isi--;
        if (!beku) tampilan_bunyi(ms);
    }
}

static float tunda_plot[TUNDA_BIP];
static size_t i_plot;

static float tertunda(float f)
{
    const float lama = tunda_plot[i_plot];
    tunda_plot[i_plot] = f;
    i_plot = (i_plot + 1) % TUNDA_BIP;
    return lama;
}

static void plot(float f)
{
    static int n, x, y_lalu = GY + GH / 2;
    static float lo = -300, hi = 300, mn = 1e9f, mx = -1e9f;

    mn = fminf(mn, f);
    mx = fmaxf(mx, f);
    if (++n < DESIMASI || beku) return;
    n = 0;

    int y = GY + GH - 1 - (int)((f - lo) * (GH - 1) / (hi - lo));
    y = constrain(y, GY, GY + GH - 1);
    if (monitor) {
        tft.fillRect(x, GY, min(4, TFT_W - x), GH, ST77XX_BLACK);
        tft.drawFastVLine(x, min(y, y_lalu), abs(y - y_lalu) + 1, ST77XX_GREEN);
    }
    y_lalu = y;

    if (++x < TFT_W) return;
    x = 0;
    const float span = fmaxf(mx - mn, 50.0f);
    lo = mn - 0.1f * span;
    hi = lo + 1.2f * span;
    mn = 1e9f;
    mx = -1e9f;
}

void tampilan_sampel(void)
{
    jalankan_jadwal();
    plot(tertunda(ecg_live_tersaring_terakhir()));
}

void tampilan_beat(const ecg_beat_t &beat, bool aritmia)
{
    if (gerbang_kualitas().ayun_bersih < AMBANG_AYUN) return;
    hr_tampil = (beat.rr[0] > 0.05f) ? (int)lroundf(60.0f / beat.rr[0]) : 0;
    hr_aritmia = aritmia;
    t_hr = millis();
    if (gerbang_fase() != FASE_KALIBRASI) jadwalkan_bip(beat, aritmia);
}

void tampilan_gambar_tombol(int i)
{
    if (!monitor) return;
    static const char *const label[2][2] = {{"B1 BUNYI", "B1 BISU"}, {"B2 JALAN", "B2 BEKU"}};
    const bool ditekan = tombol_ditekan(i);
    const int x = i * 107;
    const uint16_t bg = ditekan ? ST77XX_YELLOW : ABU;
    tft.fillRect(x, 148, 105, 24, bg);
    tft.setTextColor(ditekan ? ST77XX_BLACK : ST77XX_WHITE, bg);
    tft.setTextSize(2);
    if (i < 2) {
        tft.setCursor(x + 6, 153);
        tft.print(label[i][i == 0 ? bisu : beku]);
    } else if (!rekam_aktif()) {
        tft.setCursor(x + 6, 153);
        tft.print("B3 REC");
    } else {
        tft.setCursor(x, 149);
        tft.print(rekam_dijeda() ? "B3 LANJUT" : "B3 JEDA");
        tft.setTextSize(1);
        tft.setCursor(x + 6, 165);
        tft.print("tahan=SIMPAN");
    }
}

void tampilan_mulai(void)
{
    tft.drawFastHLine(0, GY - 2, TFT_W, ABU);
    for (int i = 0; i < 3; i++) tampilan_gambar_tombol(i);
}

static void perbarui_led()
{
    static uint32_t t_led = 0;

    if (millis() - t_led < PERIODE_LED_MS) return;
    t_led = millis();

    if (!daya_tahap(4))                    tampilan_led(0, 0, 0);
    else if (gerbang_fase() == FASE_KALIBRASI) tampilan_led(0, 16, 64);
    else if (gerbang_fase() == FASE_BURUK) tampilan_led(64, 24, 0);
    else                                   tampilan_led(0, 48, 0);
}

static uint32_t t_1hz;
static char kanan_lalu[32];
constexpr uint32_t PESAN_MS = 2000, BIP_TOLAK_MS = 150;
static char pesan_besar[9], pesan_kecil[17];
static uint32_t t_pesan;

void tampilan_pesan(const char *besar, const char *kecil)
{
    snprintf(pesan_besar, sizeof pesan_besar, "%s", besar);
    snprintf(pesan_kecil, sizeof pesan_kecil, "%s", kecil);
    t_pesan = millis() | 1;
    t_1hz = millis() - 1000;
    tampilan_bunyi(BIP_TOLAK_MS);
}

static void gambar_tengah()
{
    static const char *const BULAN[12] = {"Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                                          "Jul", "Agu", "Sep", "Okt", "Nov", "Des"};
    static bool jam_dilog;
    char besar[16], kecil[24];
    uint16_t w = ST77XX_WHITE;

    const time_t kini = time(nullptr);
    struct tm t;
    localtime_r(&kini, &t);
    const bool sinkron = t.tm_year + 1900 > 2020;
    if (sinkron && !jam_dilog) {
        jam_dilog = true;
        Serial.printf("jam: %02d:%02d:%02d WIB %d %s %d\n", t.tm_hour, t.tm_min, t.tm_sec,
                      t.tm_mday, BULAN[t.tm_mon], t.tm_year + 1900);
    }

    if ((millis() / 3000) % 2 == 0) {
        float mA = 0, V = 0;
        const bool ok = daya_ina_ada() && ina219_baca(R_SHUNT, &mA, &V);
        w = ok ? ST77XX_CYAN : ST77XX_RED;
        if (ok) {
            snprintf(besar, sizeof besar, "%4.0fmA", mA);
            snprintf(kecil, sizeof kecil, "%4.2fV %5.0fmW", V, mA * V);
        } else {
            snprintf(besar, sizeof besar, "INA --");
            snprintf(kecil, sizeof kecil, "cek SDA%d SCL%d", I2C_SDA, I2C_SCL);
        }
    } else if (sinkron) {
        snprintf(besar, sizeof besar, "%02d:%02d:%02d", t.tm_hour, t.tm_min, t.tm_sec);
        snprintf(kecil, sizeof kecil, "%d %s %d", t.tm_mday, BULAN[t.tm_mon], t.tm_year + 1900);
    } else {
        const uint32_t d = millis() / 1000;
        snprintf(besar, sizeof besar, "%02u:%02u:%02u", (unsigned)(d / 3600 % 100),
                 (unsigned)(d / 60 % 60), (unsigned)(d % 60));
        snprintf(kecil, sizeof kecil, "up (belum NTP)");
    }
    tft.setTextColor(w, ST77XX_BLACK);
    tft.setTextSize(2);
    tft.setCursor(X_TENGAH, 2);
    tft.printf("%-8.8s", besar);
    tft.setTextSize(1);
    tft.setCursor(X_TENGAH, 20);
    tft.printf("%-16.16s", kecil);
}

static void gambar_kanan()
{
    char t[16] = "", kecil[24] = "";
    uint16_t w = ST77XX_YELLOW;
    const unsigned d = (unsigned)(rekam_n_sesi() / ECG_FS);
    const int simpan = rekam_baru_disimpan();
    if (t_pesan && millis() - t_pesan < PESAN_MS) {
        w = ST77XX_ORANGE;
        snprintf(t, sizeof t, "%s", pesan_besar);
        snprintf(kecil, sizeof kecil, "%s", pesan_kecil);
    } else if (rekam_aktif() && !rekam_dijeda() && akuisisi_lewat()) {
        w = ST77XX_RED;
        snprintf(t, sizeof t, "HILANG");
        snprintf(kecil, sizeof kecil, "%u sampel", (unsigned)akuisisi_lewat());
    } else if (rekam_aktif() && !rekam_dijeda()) {
        w = ST77XX_RED;
        snprintf(t, sizeof t, "REC%02u:%02u", d / 60 % 100, d % 60);
        if (rekam_bagian() > 1) snprintf(kecil, sizeof kecil, "bagian %d", rekam_bagian());
    } else if (rekam_aktif()) {
        snprintf(t, sizeof t, "JEDA%u:%02u", d / 60 % 10, d % 60);
    } else if (rekam_menulis()) {
        snprintf(t, sizeof t, "SIMPAN..");
    } else if (simpan) {
        w = ST77XX_GREEN;
        snprintf(t, sizeof t, "SIMPAN");
        snprintf(kecil, sizeof kecil, REKAM_POLA, simpan);
    } else if (akuisisi_sumber() == SUMBER_REKAM) {
        snprintf(t, sizeof t, "RP#%03d", akuisisi_sumber_rekam());
    } else if (akuisisi_sumber() == SUMBER_ACUAN) {
        snprintf(t, sizeof t, "RP 208");
    }

    char kunci[sizeof kanan_lalu];
    snprintf(kunci, sizeof kunci, "%s|%s|%u", t, kecil, (unsigned)w);
    if (strcmp(kunci, kanan_lalu) == 0) return;
    strcpy(kanan_lalu, kunci);
    tft.fillRect(X_KANAN, 0, TFT_W - X_KANAN, GY - 3, ST77XX_BLACK);
    tft.setTextColor(w, ST77XX_BLACK);
    tft.setTextSize(2);
    tft.setCursor(X_KANAN, kecil[0] ? 2 : 8);
    tft.print(t);
    if (kecil[0]) {
        tft.setTextSize(1);
        tft.setCursor(X_KANAN, 20);
        tft.print(kecil);
    }
}

static void layar_1hz()
{
    uint32_t &t = t_1hz;
    if (!monitor || millis() - t < 1000) return;
    t = millis();

    const bool hr_ada = hr_tampil > 0 && millis() - t_hr < HR_BASI_MS;
    tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
    tft.setTextSize(2);
    tft.setCursor(4, 8);
    tft.print("HR");
    tft.setTextSize(3);
    tft.setCursor(32, 3);
    tft.setTextColor(hr_ada && hr_aritmia ? ST77XX_RED : ST77XX_WHITE, ST77XX_BLACK);
    if (hr_ada) tft.printf("%3d", hr_tampil);
    else        tft.print(" --");
    tft.setTextSize(1);
    tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
    tft.setCursor(90, 17);
    tft.print("bpm");

    gambar_tengah();
    gambar_kanan();

    for (int i = 0; i < 3; i++) tampilan_gambar_tombol(i);
}

void tampilan_set_monitor(bool on)
{
    monitor = on;
    if (!on) return;
    tft.fillScreen(ST77XX_BLACK);
    tampilan_mulai();
    t_1hz = millis() - 1000;
    kanan_lalu[0] = 0;
}

bool tampilan_monitor(void) { return monitor; }

constexpr int MY = 26, MH = 20;
constexpr uint16_t BIRU_TUA = 0x0010;
static char isi_baris[TAMPILAN_BARIS][TAMPILAN_KOLOM + 1];
static int8_t sorot_baris[TAMPILAN_BARIS];

void tampilan_menu_bingkai(const char *judul, const char *petunjuk1, const char *petunjuk2)
{
    tft.fillScreen(ST77XX_BLACK);
    tft.fillRect(0, 0, TFT_W, 22, BIRU_TUA);
    tft.setTextSize(2);
    tft.setTextColor(ST77XX_WHITE, BIRU_TUA);
    tft.setCursor(4, 3);
    tft.print(judul);
    tft.drawFastHLine(0, 148, TFT_W, ABU);
    tft.setTextSize(1);
    tft.setTextColor(ST77XX_CYAN, ST77XX_BLACK);
    tft.setCursor(4, 152);
    tft.print(petunjuk1);
    tft.setCursor(4, 162);
    tft.print(petunjuk2);
    for (int r = 0; r < TAMPILAN_BARIS; r++) { isi_baris[r][0] = 0; sorot_baris[r] = 0; }
}

void tampilan_menu_baris(int r, const char *teks, bool sorot, uint16_t warna)
{
    if (r < 0 || r >= TAMPILAN_BARIS) return;
    char t[TAMPILAN_KOLOM + 1];
    snprintf(t, sizeof t, "%-*.*s", TAMPILAN_KOLOM, TAMPILAN_KOLOM, teks);
    if (sorot_baris[r] == sorot && strcmp(isi_baris[r], t) == 0) return;
    strcpy(isi_baris[r], t);
    sorot_baris[r] = sorot;
    const uint16_t bg = sorot ? ST77XX_YELLOW : ST77XX_BLACK;
    const int y = MY + r * MH;
    tft.fillRect(0, y, 4, 16, bg);
    tft.fillRect(4 + TAMPILAN_KOLOM * 12, y, TFT_W - 4 - TAMPILAN_KOLOM * 12, 16, bg);
    tft.setTextSize(2);
    tft.setTextColor(sorot ? ST77XX_BLACK : warna, bg);
    tft.setCursor(4, y + 1);
    tft.print(t);
}

void tampilan_layani(void)
{
    perbarui_led();
    layar_1hz();
    if (buzz_sampai && (int32_t)(millis() - buzz_sampai) >= 0) {
        buzzer(false);
        buzz_sampai = 0;
    }
}
#endif
