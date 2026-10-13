// Menu. Kontrak: include/menu.h
#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "menu.h"

#include <Arduino.h>

#include "akuisisi.h"
#include "tampilan.h"
#include "tombol.h"

typedef char baris_t[TAMPILAN_KOLOM + 1];

struct halaman_t;
// Satu baris daftar statis. aksi dijalankan lebih dulu, lalu masuk ke anak
// (bila ada). nilai = teks rata kanan (ON/OFF, tanda *); tanpa nilai, baris
// yang punya anak bertanda ">".
struct item_t {
    const char *teks;
    const halaman_t *anak;
    void (*aksi)(void);
    const char *(*nilai)(void);
};
// Tiga jenis halaman: daftar statis (item), daftar dinamis (n/teks/pilih;
// memilih = kembali satu tingkat), atau halaman teks (isi, diperbarui 1 Hz).
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

// ---------------------------------------------------------------- Sumber sinyal
static const char *tanda(bool aktif) { return aktif ? "*" : ""; }
static void ke_adc() { akuisisi_set_sumber(SUMBER_ADC, 0, true); }
static void ke_acuan() { akuisisi_set_sumber(SUMBER_ACUAN, 0, true); }
static const char *n_adc() { return tanda(akuisisi_sumber() == SUMBER_ADC); }
static const char *n_acuan() { return tanda(akuisisi_sumber() == SUMBER_ACUAN); }

static const item_t I_SUMBER[] = {
    {"Sensor (ADC)", nullptr, ke_adc, n_adc},
    {"Replay acuan (208)", nullptr, ke_acuan, n_acuan},
};
static const halaman_t H_SUMBER = DAFTAR("Sumber sinyal", I_SUMBER);

// ---------------------------------------------------------------- akar
static const item_t I_AKAR[] = {
    {"Sumber sinyal", &H_SUMBER, nullptr, nullptr},
};
static const halaman_t H_AKAR = DAFTAR("MENU", I_AKAR);

// ---------------------------------------------------------------- navigasi
constexpr int DALAM_MAKS = 4;
static struct { const halaman_t *h; int sel, atas; } tumpuk[DALAM_MAKS];
static int dalam = -1;                     // -1 = tertutup
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

// Semua baris dihitung ulang; tampilan_menu_baris() hanya menggambar yang berubah.
// Diukur di board: bingkai penuh ~200 ms, geser sorotan (dua baris) ~36 ms;
// antrean ISR menampung 711 ms, jadi tidak ada sampel hilang.
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
            t.sel = (t.sel + (i == 2 ? n - 1 : 1)) % n;    // B3 naik, B1 turun, berputar
            gambar(false);
            lapor();
        }
    }
}

void menu_layani(void)
{
    if (dalam < 0 || !tumpuk[dalam].h->isi || millis() - t_isi < 1000) return;
    t_isi = millis();
    gambar(false);
}
#endif
