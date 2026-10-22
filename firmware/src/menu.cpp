#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "menu.h"

#include <Arduino.h>
#include <WiFi.h>

#include "akuisisi.h"
#include "ecg_mqtt.h"
#include "gerbang.h"
#include "ina219.h"
#include "klasifikasi.h"
#include "konfig.h"
#include "perangkat.h"
#include "rekam.h"
#include "diagnosa.h"
#include "daya.h"
#include "tampilan.h"
#include "tombol.h"

#ifndef VERSI_GIT
#define VERSI_GIT "?"
#endif

typedef char baris_t[TAMPILAN_KOLOM + 1];

struct halaman_t;
struct item_t {
    const char *teks;
    const halaman_t *anak;
    void (*aksi)(void);
    const char *(*nilai)(void);
};
struct halaman_t {
    const char *judul;
    const item_t *item;
    int n;
    int (*n_dyn)(void);
    void (*teks_dyn)(int i, char *out, size_t n);
    void (*pilih_dyn)(int i);
    void (*isi)(baris_t *b);
};
#define DAFTAR(j, a) {j, a, (int)(sizeof a / sizeof a[0]), nullptr, nullptr, nullptr, nullptr}
#define DINAMIS(j, n, t, p) {j, nullptr, 0, n, t, p, nullptr}
#define TEKS(j, f) {j, nullptr, 0, nullptr, nullptr, nullptr, f}

static const char *tanda(bool aktif) { return aktif ? "*" : ""; }
static void ke_adc() { akuisisi_set_sumber(SUMBER_ADC, 0, true); }
static void ke_acuan() { akuisisi_set_sumber(SUMBER_ACUAN, 0, true); }
static const char *n_adc() { return tanda(akuisisi_sumber() == SUMBER_ADC); }
static const char *n_acuan() { return tanda(akuisisi_sumber() == SUMBER_ACUAN); }

static int rk_no[64], rk_n;
static int rekaman_n() { return rk_n = rekam_daftar(rk_no, 64); }
static void rekaman_teks(int i, char *out, size_t n)
{
    const bool aktif = akuisisi_sumber() == SUMBER_REKAM && akuisisi_sumber_rekam() == rk_no[i];
    snprintf(out, n, "%03d  %6.1f s  %s", rk_no[i], (float)rekam_sampel_n(rk_no[i]) / ECG_FS,
             aktif ? "*" : "");
}
static void rekaman_pilih(int i) { akuisisi_set_sumber(SUMBER_REKAM, rk_no[i], true); }
static const halaman_t H_REKAMAN = DINAMIS("Replay rekaman", rekaman_n, rekaman_teks, rekaman_pilih);
static const char *n_rekaman()
{
    static char t[8];
    if (akuisisi_sumber() != SUMBER_REKAM) return ">";
    snprintf(t, sizeof t, "%03d * >", akuisisi_sumber_rekam());
    return t;
}

static const item_t I_SUMBER[] = {
    {"Sensor (ADC)", nullptr, ke_adc, n_adc},
    {"REPLAY 208", nullptr, ke_acuan, n_acuan},
    {"Replay rekaman", &H_REKAMAN, nullptr, n_rekaman},
};
static const halaman_t H_SUMBER = DAFTAR("Sumber sinyal", I_SUMBER);

static const char *on_off(bool on) { return on ? "ON" : "OFF"; }
static void kalib_ulang()
{
    gerbang_mulai_sesi();
    klasifikasi_reset();
    Serial.println("kalibrasi: sesi baru");
}
static void kalib_lewati()
{
    gerbang_set_lewati(!gerbang_lewati());
    Serial.printf("lewati gerbang kalibrasi %s\n", on_off(gerbang_lewati()));
}
static const char *n_lewati() { return on_off(gerbang_lewati()); }
static void kalib_status(baris_t *b)
{
    const gerbang_kualitas_t &q = gerbang_kualitas();
    const int f = gerbang_fase();
    snprintf(b[0], sizeof *b, "Fase %s", f == FASE_KALIBRASI ? "KALIBRASI" : f == FASE_BAIK ? "BAIK" : "BURUK");
    snprintf(b[1], sizeof *b, "Kontak %lu/%lu s",
             (unsigned long)min<uint32_t>(gerbang_kontak_ms() / 1000, 99999),
             (unsigned long)(PEMANASAN_MS / 1000));
    snprintf(b[2], sizeof *b, "RR tenang %lu/%lu s",
             (unsigned long)min<uint32_t>(gerbang_tenang_ms() / 1000, 99999),
             (unsigned long)(RR_TENANG_MS / 1000));
    snprintf(b[3], sizeof *b, "Ayun %d/%d 50Hz %d/%d", q.ayun_bersih, AMBANG_AYUN, q.hum50, AMBANG_DENGUNG);
    snprintf(b[4], sizeof *b, "Lewati %s  Replay %s", on_off(gerbang_lewati()), on_off(akuisisi_replay()));
    snprintf(b[5], sizeof *b, "Sampel hilang %u", (unsigned)akuisisi_lewat());
}
static const halaman_t H_KALIB_STATUS = TEKS("Status kalibrasi", kalib_status);
static const item_t I_KALIB[] = {
    {"Mulai ulang", nullptr, kalib_ulang, nullptr},
    {"Lewati (bench)", nullptr, kalib_lewati, n_lewati},
    {"Status", &H_KALIB_STATUS, nullptr, nullptr},
};
static const halaman_t H_KALIB = DAFTAR("Kalibrasi", I_KALIB);

static const char *tes_nama;
static diag_hasil_t tes_hasil;
static void tes_jalan(const char *nama, diag_hasil_t (*f)(void))
{
    tes_nama = nama;
    akuisisi_timer(false);
    tes_hasil = f();
    akuisisi_timer(daya_mode() != 0);
    int i;
    while (tombol_event(&i) != TOMBOL_TIDAK) {}
    Serial.printf("tes %s: %s | %s\n", nama, tes_hasil.lulus ? "LULUS" : "GAGAL", tes_hasil.ringkas);
}
static diag_hasil_t tombol_10s()
{
    tampilan_menu_bingkai("Tes tombol", "B2 yang masih ditahan: lepas dulu", "");
    tampilan_menu_baris(1, "Tekan B1, B2, B3", false);
    tampilan_menu_baris(2, "batas 10 detik", false);
    return diag_tombol(10000);
}
static void tes_buzzer() { tes_jalan("Buzzer", diag_buzzer); }
static void tes_layar() { tes_jalan("Layar", diag_layar); }
static void tes_adc() { tes_jalan("ADC & lead-off", diag_adc); }
static void tes_ina() { tes_jalan("INA219", diag_ina219); }
static void tes_tombol() { tes_jalan("Tombol", tombol_10s); }
static void tes_isi(baris_t *b)
{
    snprintf(b[0], sizeof *b, "%s", tes_nama ? tes_nama : "-");
    snprintf(b[1], sizeof *b, "%s", tes_hasil.lulus ? "LULUS" : "GAGAL");
    const char *r = tes_hasil.ringkas;
    for (int k = 2; k < TAMPILAN_BARIS && *r; k++, r += min<size_t>(strlen(r), TAMPILAN_KOLOM))
        snprintf(b[k], sizeof *b, "%.*s", TAMPILAN_KOLOM, r);
}
static const halaman_t H_TES_HASIL = TEKS("Hasil tes", tes_isi);
static const item_t I_TES[] = {
    {"Buzzer", &H_TES_HASIL, tes_buzzer, nullptr},
    {"Layar (pola warna)", &H_TES_HASIL, tes_layar, nullptr},
    {"ADC & lead-off", &H_TES_HASIL, tes_adc, nullptr},
    {"INA219", &H_TES_HASIL, tes_ina, nullptr},
    {"Tombol (10 s)", &H_TES_HASIL, tes_tombol, nullptr},
};
static const halaman_t H_TES = DAFTAR("Tes perangkat", I_TES);

static void daya_isi(baris_t *b)
{
    if (daya_tangga_aktif()) {
        snprintf(b[0], sizeof *b, "Mengukur, jangan disentuh");
        snprintf(b[1], sizeof *b, "Langkah p%d (%d/6)", daya_tangga_langkah(), daya_tangga_langkah() + 1);
        return;
    }
    daya_baris_t h[TAMPILAN_BARIS];
    const int n = daya_tangga_hasil(h, TAMPILAN_BARIS);
    if (!n) { snprintf(b[0], sizeof *b, "Belum ada hasil"); return; }
    for (int k = 0; k < n; k++)
        snprintf(b[k], sizeof *b, "%-3s%6.1fmA %5.0fmW", h[k].mode, h[k].i_ma, h[k].p_mw);
    char *e = b[0] + strlen(b[0]);
    snprintf(e, sizeof *b - (e - b[0]), " #%03d", daya_tangga_berkas());
}
static const halaman_t H_DAYA = TEKS("Ukur daya", daya_isi);
static void tutup();
static void mulai_tangga()
{
    daya_tangga_mulai();
    if (daya_tangga_aktif()) tutup();
}
static const item_t I_DAYA[] = {
    {"Mulai tangga p0-p5", nullptr, mulai_tangga, nullptr},
    {"Hasil terakhir", &H_DAYA, nullptr, nullptr},
};
static const halaman_t H_DAYA_MENU = DAFTAR("Ukur daya", I_DAYA);

static int wifi_n() { return konfig_wifi_n(); }
static void wifi_teks(int i, char *out, size_t n)
{
    snprintf(out, n, "%c %s", i == konfig_wifi() ? '*' : ' ', konfig_wifi_nama(i));
}
static void wifi_pilih(int i) { konfig_pilih_wifi(i); }
static int broker_n() { return konfig_broker_n(); }
static void broker_teks(int i, char *out, size_t n)
{
    snprintf(out, n, "%c %s %s", i == konfig_broker() ? '*' : ' ', konfig_broker_nama(i),
             konfig_broker_host(i));
}
static void broker_pilih(int i) { konfig_pilih_broker(i); }
static const halaman_t H_WIFI = DINAMIS("WiFi", wifi_n, wifi_teks, wifi_pilih);
static const halaman_t H_BROKER = DINAMIS("Broker", broker_n, broker_teks, broker_pilih);

static void wifi_ganti() { konfig_set_wifi_aktif(!konfig_wifi_aktif()); }
static const char *n_wifi_aktif() { return on_off(konfig_wifi_aktif()); }
static const char *n_wifi() { return konfig_wifi_nama(konfig_wifi()); }
static const char *n_broker() { return konfig_broker_nama(konfig_broker()); }
static const char *ip_teks()
{
    static char t[16];
    if (WiFi.status() != WL_CONNECTED) return "-";
    snprintf(t, sizeof t, "%s", WiFi.localIP().toString().c_str());
    return t;
}
static void net_status(baris_t *b)
{
    const int k = konfig_broker();
    snprintf(b[0], sizeof *b, "MQTT %s (%s)", on_off(ecg_mqtt_aktif()), ecg_mqtt_status());
    snprintf(b[1], sizeof *b, "WiFi %s", konfig_wifi_nama(konfig_wifi()));
    snprintf(b[2], sizeof *b, "IP %s", ip_teks());
    snprintf(b[3], sizeof *b, "RSSI %d dBm", ecg_mqtt_rssi());
    snprintf(b[4], sizeof *b, "%s:%d", konfig_broker_host(k), konfig_broker_port(k));
    snprintf(b[5], sizeof *b, "Kirim %u backlog %u", (unsigned)ecg_mqtt_terkirim(),
             (unsigned)ecg_mqtt_antre_n());
}
static const halaman_t H_NET_STATUS = TEKS("Status jaringan", net_status);
static const item_t I_JARINGAN[] = {
    {"WiFi aktif", nullptr, wifi_ganti, n_wifi_aktif},
    {"WiFi", &H_WIFI, nullptr, n_wifi},
    {"Broker", &H_BROKER, nullptr, n_broker},
    {"Status", &H_NET_STATUS, nullptr, nullptr},
};
static const halaman_t H_JARINGAN = DAFTAR("Jaringan", I_JARINGAN);

static void info_isi(baris_t *b)
{
    const int k = konfig_broker();
    snprintf(b[0], sizeof *b, "IP %s  %d dBm", ip_teks(), ecg_mqtt_rssi());
    snprintf(b[1], sizeof *b, "Broker %s %s", konfig_broker_nama(k), konfig_broker_host(k));
    float mA, V;
    if (daya_ina_ada() && ina219_baca(R_SHUNT, &mA, &V))
        snprintf(b[2], sizeof *b, "INA %.2f V %.1f mA", V, mA);
    else
        snprintf(b[2], sizeof *b, "INA219 tidak menjawab");
    const uint32_t d = millis() / 1000;
    snprintf(b[3], sizeof *b, "Uptime %lu:%02lu:%02lu", (unsigned long)(d / 3600),
             (unsigned long)(d / 60 % 60), (unsigned long)(d % 60));
    snprintf(b[4], sizeof *b, "Versi %s", VERSI_GIT);
    snprintf(b[5], sizeof *b, "Build %s %.5s", __DATE__, __TIME__);
}
static const halaman_t H_INFO = TEKS("Info", info_isi);

static const item_t I_AKAR[] = {
    {"Sumber sinyal", &H_SUMBER, nullptr, nullptr},
    {"Kalibrasi", &H_KALIB, nullptr, nullptr},
    {"Tes perangkat", &H_TES, nullptr, nullptr},
    {"Ukur daya", &H_DAYA_MENU, nullptr, nullptr},
    {"Jaringan", &H_JARINGAN, nullptr, nullptr},
    {"Info", &H_INFO, nullptr, nullptr},
};
static const halaman_t H_AKAR = DAFTAR("MENU", I_AKAR);

constexpr int DALAM_MAKS = 4;
static struct { const halaman_t *h; int sel, atas; } tumpuk[DALAM_MAKS];
static int dalam = -1;
static uint32_t t_isi;

bool menu_terbuka(void) { return dalam >= 0; }

static int jumlah(const halaman_t *h) { return h->item ? h->n : h->n_dyn ? h->n_dyn() : 0; }

static void label(const halaman_t *h, int i, char *out, size_t n)
{
    if (!h->item) { h->teks_dyn(i, out, n); return; }
    const item_t &it = h->item[i];
    const char *v = it.nilai ? it.nilai() : it.anak ? ">" : "";
    const int pad = TAMPILAN_KOLOM - (int)strlen(it.teks);
    snprintf(out, n, "%s%*s", it.teks, pad > 0 ? pad : 1, v);
}

static void gambar(bool bingkai)
{
    auto &t = tumpuk[dalam];
    if (bingkai)
        tampilan_menu_bingkai(t.h->judul,
                              t.h->isi ? "B2 kembali" : "B3 naik   B1 turun   tahan B2 pilih",
                              t.h->isi ? "tahan B1/B3 keluar ke monitor"
                                       : "B2 kembali   tahan B1/B3 keluar ke monitor");
    if (t.h->isi) {
        baris_t b[TAMPILAN_BARIS] = {};
        t.h->isi(b);
        for (int r = 0; r < TAMPILAN_BARIS; r++) tampilan_menu_baris(r, b[r], false);
        return;
    }
    const int n = jumlah(t.h);
    if (t.sel >= n) t.sel = n ? n - 1 : 0;
    if (t.sel < t.atas) t.atas = t.sel;
    if (t.sel >= t.atas + TAMPILAN_BARIS) t.atas = t.sel - TAMPILAN_BARIS + 1;
    for (int r = 0; r < TAMPILAN_BARIS; r++) {
        const int i = t.atas + r;
        baris_t s = "";
        if (i < n) label(t.h, i, s, sizeof s);
        else if (n == 0 && r == 0) strcpy(s, "(kosong)");
        tampilan_menu_baris(r, s, i < n && i == t.sel);
    }
}

static void lapor()
{
    auto &t = tumpuk[dalam];
    if (t.h->isi) {
        baris_t b[TAMPILAN_BARIS] = {};
        t.h->isi(b);
        Serial.printf("menu: %s\n", t.h->judul);
        for (auto &s : b) if (s[0]) Serial.printf("menu:   %s\n", s);
        return;
    }
    const int n = jumlah(t.h);
    baris_t s = "(kosong)";
    if (n) label(t.h, t.sel, s, sizeof s);
    Serial.printf("menu: %s [%d/%d] %s\n", t.h->judul, n ? t.sel + 1 : 0, n, s);
}

static void masuk(const halaman_t *h)
{
    if (dalam + 1 >= DALAM_MAKS) return;
    tumpuk[++dalam] = {h, 0, 0};
    t_isi = millis();
    gambar(true);
    lapor();
}

void menu_buka(void)
{
    if (dalam >= 0) return;
    if (rekam_tolak("menu")) { tampilan_pesan("TERKUNCI", "tahan B3=simpan"); return; }
    tampilan_set_monitor(false);
    masuk(&H_AKAR);
}

static void tutup()
{
    dalam = -1;
    tampilan_set_monitor(true);
    Serial.println("menu: tutup");
}

static void kembali()
{
    if (dalam == 0) { tutup(); return; }
    dalam--;
    gambar(true);
    lapor();
}

static void pilih()
{
    auto &t = tumpuk[dalam];
    if (t.h->isi || !jumlah(t.h)) return;
    if (!t.h->item) {
        t.h->pilih_dyn(t.sel);
        kembali();
        return;
    }
    const item_t &it = t.h->item[t.sel];
    if (it.aksi) it.aksi();
    if (dalam < 0) return;
    if (it.anak) { masuk(it.anak); return; }
    gambar(false);
    lapor();
}

void menu_tombol(int i, int e)
{
    if (dalam < 0) return;
    if (e == TOMBOL_LAMA) {
        if (i == 1) pilih();
        else tutup();
    } else if (e == TOMBOL_PENDEK) {
        auto &t = tumpuk[dalam];
        const int n = t.h->isi ? 0 : jumlah(t.h);
        if (i == 1) kembali();
        else if (n) {
            t.sel = (t.sel + (i == 2 ? n - 1 : 1)) % n;
            gambar(false);
            lapor();
        }
    }
}

void menu_layani(void)
{
    static bool daya_lalu;
    const bool d = daya_tangga_aktif();
    if (daya_lalu && !d && (dalam < 0 || tumpuk[dalam].h != &H_DAYA)) {
        if (dalam < 0) tampilan_set_monitor(false);
        masuk(&H_DAYA);
    }
    daya_lalu = d;
    if (dalam < 0 || !tumpuk[dalam].h->isi || millis() - t_isi < 1000) return;
    t_isi = millis();
    gambar(false);
}
#endif
