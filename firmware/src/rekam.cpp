#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "rekam.h"

#include <Arduino.h>
#include <LittleFS.h>
#include <sys/stat.h>

#include "akuisisi.h"
#include "daya.h"
#include "ecg_pipeline.h"
#include "menu.h"
#include "perangkat.h"
#include "tampilan.h"

constexpr size_t REKAM_N = REKAM_SAMPEL_MAKS;
constexpr int DAFTAR_MAKS = 64;
constexpr size_t BLOK_BACA = 512;
constexpr size_t BYTE_PER_SAMPEL_MAKS = 6;
constexpr size_t RUANG_BERKAS_PENUH = REKAM_N * BYTE_PER_SAMPEL_MAKS;
constexpr size_t SAMPEL_PER_TULIS = 256;
constexpr char BARIS_JEDA[] = "# jeda\n";
constexpr int BATAS_MAKS = 64;
constexpr size_t BYTE_BLOK_TULIS = SAMPEL_PER_TULIS * BYTE_PER_SAMPEL_MAKS + BATAS_MAKS * sizeof BARIS_JEDA;
constexpr uint32_t BIP_SIMPAN_MS = 400;

static uint16_t *buf, *buf_cadangan;
static size_t n;
static bool aktif, jeda;
static size_t lepas;
static size_t batas[BATAS_MAKS];
static int n_batas;
static int no_simpan;
static uint32_t t_simpan;
static size_t n_sesi_lalu;
static int bagian, lanjutan_dari;
static unsigned lewat_berkas, celah;

struct penulis_t {
    File f;
    const uint16_t *data;
    size_t n, i, lepas;
    size_t batas[BATAS_MAKS];
    int n_batas, k, nomor;
    unsigned lewat;
    bool akhir_sesi;
    char path[24];
};
static penulis_t tulis;
static bool menulis;
static char blok_tulis[BYTE_BLOK_TULIS];

bool rekam_aktif(void) { return aktif; }
bool rekam_dijeda(void) { return aktif && jeda; }
bool rekam_menulis(void) { return menulis; }
bool rekam_tolak(const char *apa)
{
    if (!aktif) return false;
    Serial.printf("DITOLAK: %s selama sesi rekam, simpan dulu (tahan B3 / r)\n", apa);
    return true;
}
int rekam_baru_disimpan(void) { return no_simpan && millis() - t_simpan < 3000 ? no_simpan : 0; }
size_t rekam_n(void) { return n; }
size_t rekam_n_sesi(void) { return n_sesi_lalu + n; }
int rekam_bagian(void) { return bagian; }

static bool ruang_cukup()
{
    const size_t perlu = RUANG_BERKAS_PENUH * (menulis ? 2 : 1);
    return LittleFS.totalBytes() - LittleFS.usedBytes() >= perlu;
}

static void nama(int nomor, char *out, size_t len) { snprintf(out, len, REKAM_POLA, nomor); }

int rekam_daftar(int *nomor, int maks)
{
    int k = 0;
    File d = LittleFS.open(REKAM_DIR);
    if (!d || !d.isDirectory()) return 0;
    for (File f = d.openNextFile(); f && k < maks; f = d.openNextFile()) {
        const int x = atoi(f.name());
        if (x <= 0) continue;
        int j = k++;
        while (j > 0 && nomor[j - 1] > x) { nomor[j] = nomor[j - 1]; j--; }
        nomor[j] = x;
    }
    return k;
}

static int terakhir()
{
    int maks = 0;
    File d = LittleFS.open(REKAM_DIR);
    if (!d || !d.isDirectory()) return 0;
    for (File f = d.openNextFile(); f; f = d.openNextFile()) maks = max(maks, atoi(f.name()));
    return maks;
}

void rekam_siapkan(void)
{
    buf = (uint16_t *)ps_malloc(REKAM_N * sizeof(uint16_t));
    buf_cadangan = (uint16_t *)ps_malloc(REKAM_N * sizeof(uint16_t));
    if (!buf) Serial.println("PERINGATAN: PSRAM gagal, perekaman mentah nonaktif");
    if (!buf_cadangan) Serial.println("PERINGATAN: PSRAM buffer kedua gagal, simpan memblok loop");
    if (!LittleFS.begin(true)) { Serial.println("PERINGATAN: LittleFS gagal mount"); return; }
    LittleFS.mkdir(REKAM_DIR);
    struct stat st;
    if (stat("/littlefs/rekaman.csv", &st) == 0 && !terakhir()) {
        char p[24];
        nama(1, p, sizeof p);
        if (LittleFS.rename("/rekaman.csv", p))
            Serial.printf("rekam: /rekaman.csv lama dipindah ke %s\n", p);
    }
}

static void tutup_tulis(bool gagal)
{
    tulis.f.close();
    menulis = false;
    const float persen = tulis.n ? 100.0f * tulis.lepas / tulis.n : 0.0f;
    if (gagal) Serial.printf("GAGAL: LittleFS penuh setelah %u sampel, %s terpotong\n",
                             (unsigned)tulis.i, tulis.path);
    Serial.printf("SIMPAN %u sampel (%.1f detik, %d segmen), %u terlewat, elektroda lepas %.0f%% -> %s\n",
                  (unsigned)tulis.n, (float)tulis.n / ECG_FS, tulis.n_batas + 1, tulis.lewat, persen,
                  tulis.path);
    no_simpan = tulis.nomor;
    t_simpan = millis();
    if (tulis.lepas > tulis.n / 10)
        Serial.println("PERINGATAN: elektroda lepas >10% — rekaman ini kemungkinan besar kosong.");
    if (tulis.akhir_sesi) tampilan_bunyi(BIP_SIMPAN_MS);
}

static void langkah_tulis()
{
    size_t len = 0;
    const size_t akhir = min(tulis.n, tulis.i + SAMPEL_PER_TULIS);
    for (; tulis.i < akhir; tulis.i++) {
        if (tulis.k < tulis.n_batas && tulis.batas[tulis.k] == tulis.i) {
            len += snprintf(blok_tulis + len, sizeof blok_tulis - len, "%s", BARIS_JEDA);
            tulis.k++;
        }
        len += snprintf(blok_tulis + len, sizeof blok_tulis - len, "%u\n", tulis.data[tulis.i]);
    }
    const bool gagal = tulis.f.write((const uint8_t *)blok_tulis, len) != len;
    if (gagal || tulis.i >= tulis.n) tutup_tulis(gagal);
}

static void selesaikan_tulis()
{
    while (menulis) langkah_tulis();
}

void rekam_layani(void)
{
    if (menulis && !akuisisi_isi()) langkah_tulis();
}

static int simpan(bool akhir_sesi)
{
    aktif = false;
    buzzer(false);
    selesaikan_tulis();
    const int nomor = terakhir() + 1;
    if (nomor > REKAM_NOMOR_MAKS) { Serial.println("GAGAL: nomor rekaman habis, hapus dulu (h<n>)"); return 0; }
    nama(nomor, tulis.path, sizeof tulis.path);
    tulis.f = LittleFS.open(tulis.path, "w");
    if (!tulis.f) { Serial.println("GAGAL membuka LittleFS"); return 0; }
    tulis.lewat = lewat_berkas = (unsigned)akuisisi_lewat();
    const float persen = n ? 100.0f * lepas / n : 0.0f;
    tulis.f.printf("# fs=%u n=%u lewat=%u lepas=%u (%.0f%%)", ECG_FS, (unsigned)n, tulis.lewat,
                   (unsigned)lepas, persen);
    if (lanjutan_dari) tulis.f.printf(" lanjutan=%03d celah=%u", lanjutan_dari, celah);
    tulis.f.print("\n");
    if (n_batas && batas[n_batas - 1] >= n) n_batas--;
    memcpy(tulis.batas, batas, n_batas * sizeof batas[0]);
    tulis.n_batas = n_batas;
    tulis.k = 0;
    tulis.data = buf;
    tulis.n = n;
    tulis.i = 0;
    tulis.lepas = lepas;
    tulis.nomor = nomor;
    tulis.akhir_sesi = akhir_sesi;
    menulis = true;
    if (buf_cadangan) {
        uint16_t *kosong = buf_cadangan;
        buf_cadangan = buf;
        buf = kosong;
    } else {
        selesaikan_tulis();
    }
    return nomor;
}

static void mulai_berkas()
{
    n = lepas = 0;
    n_batas = 0;
    jeda = false;
    akuisisi_nol_lewat();
    aktif = true;
}

static void sambung()
{
    const size_t n_ini = n;
    const int nomor = simpan(false);
    if (!nomor) return;
    if (!ruang_cukup()) {
        tulis.akhir_sesi = true;
        Serial.println("REKAM berhenti: LittleFS tidak cukup untuk berkas berikutnya, tarik data dulu (make pull)");
        tampilan_pesan("PENUH", "tarik data dulu");
        return;
    }
    celah = (unsigned)akuisisi_lewat() - lewat_berkas;
    n_sesi_lalu += n_ini;
    bagian++;
    lanjutan_dari = nomor;
    mulai_berkas();
    Serial.printf("REKAM lanjut bagian %d (lanjutan %03d, celah %u sampel)\n", bagian, nomor, celah);
}

void rekam_sampel(uint16_t s)
{
    if (!aktif || jeda || !buf) return;
    buf[n++] = s;
    if (digitalRead(PIN_LOP) || digitalRead(PIN_LON)) lepas++;
    if (n >= REKAM_N) sambung();
}

void rekam_toggle(void)
{
    if (aktif) { simpan(true); return; }
    const char *tolak = akuisisi_sumber() != SUMBER_ADC ? "REKAM hanya dari sensor"
                      : daya_mode() >= 0 ? "REKAM ditolak: mode daya pN aktif ('p' = normal)"
                      : menu_terbuka() ? "REKAM ditolak: tutup menu dulu"
                      : !ruang_cukup() ? "REKAM ditolak: LittleFS penuh, tarik data dulu" : nullptr;
    if (tolak) {
        Serial.println(tolak);
        tampilan_pesan(ruang_cukup() ? "TOLAK" : "PENUH",
                       akuisisi_replay() ? "hanya sensor ADC" : "rekam ditolak");
        return;
    }
    n_sesi_lalu = 0;
    bagian = 1;
    lanjutan_dari = 0;
    mulai_berkas();
    Serial.println("REKAM mulai");
}

void rekam_jeda(void)
{
    if (!aktif) { Serial.println("REKAM: tidak sedang merekam"); return; }
    jeda = !jeda;
    if (jeda && n && (!n_batas || batas[n_batas - 1] < n)) {
        if (n_batas < BATAS_MAKS) batas[n_batas++] = n;
        else Serial.println("PERINGATAN: batas jeda penuh, segmen ini lebur dengan berikutnya");
    }
    Serial.printf("REKAM %s n=%u (%.1f detik)\n", jeda ? "jeda" : "lanjut", (unsigned)n,
                  (float)n / ECG_FS);
}

bool rekam_dump(int nomor)
{
    selesaikan_tulis();
    if (nomor <= 0) nomor = terakhir();
    char p[24];
    nama(nomor, p, sizeof p);
    File f = nomor > 0 ? LittleFS.open(p, "r") : File();
    if (!f) { Serial.println("Belum ada rekaman."); return false; }
    Serial.println("---MULAI---");
    while (f.available()) Serial.write(f.read());
    Serial.println("---SELESAI---");
    f.close();
    return true;
}

bool rekam_hapus(int nomor)
{
    selesaikan_tulis();
    char p[24];
    nama(nomor, p, sizeof p);
    const bool ok = LittleFS.remove(p);
    Serial.printf("rekam: hapus %s %s\n", p, ok ? "OK" : "GAGAL (tidak ada)");
    return ok;
}

void rekam_cetak_daftar(void)
{
    int no[DAFTAR_MAKS];
    const int k = rekam_daftar(no, DAFTAR_MAKS);
    Serial.printf("rekam: %d berkas, LittleFS %u/%u KB\n", k,
                  (unsigned)(LittleFS.usedBytes() / 1024), (unsigned)(LittleFS.totalBytes() / 1024));
    for (int i = 0; i < k; i++) {
        char p[24];
        nama(no[i], p, sizeof p);
        File f = LittleFS.open(p, "r");
        Serial.printf("  %3d  %6u B  %s\n", no[i], (unsigned)f.size(), f.readStringUntil('\n').c_str());
        f.close();
    }
}
size_t rekam_sampel_n(int nomor)
{
    char p[24];
    nama(nomor, p, sizeof p);
    File f = LittleFS.open(p, "r");
    if (!f) return 0;
    const String h = f.readStringUntil('\n');
    f.close();
    const int k = h.indexOf(" n=");
    return k < 0 ? 0 : (size_t)atol(h.c_str() + k + 3);
}

size_t rekam_muat(int nomor, uint16_t *buf, size_t maks)
{
    selesaikan_tulis();
    char p[24];
    nama(nomor, p, sizeof p);
    File f = nomor > 0 ? LittleFS.open(p, "r") : File();
    if (!f) return 0;
    uint8_t blok[BLOK_BACA];
    size_t k = 0;
    uint32_t v = 0;
    bool ada = false, komentar = false;
    for (int m; k < maks && (m = f.read(blok, sizeof blok)) > 0;) {
        for (int j = 0; j < m && k < maks; j++) {
            const char c = blok[j];
            if (c == '\n') {
                if (ada && !komentar) buf[k++] = (uint16_t)min<uint32_t>(v, 4095);
                v = 0; ada = komentar = false;
            } else if (c == '#' && !ada) komentar = true;
            else if (c >= '0' && c <= '9' && !komentar) { v = v * 10 + (c - '0'); ada = true; }
        }
    }
    if (ada && !komentar && k < maks) buf[k++] = (uint16_t)min<uint32_t>(v, 4095);
    f.close();
    return k;
}
#endif
