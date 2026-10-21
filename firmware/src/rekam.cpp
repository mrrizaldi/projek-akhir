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

constexpr size_t SESI_N = REKAM_N * REKAM_BAGIAN_MAKS;

static uint16_t *buf;
static size_t n, batas_sesi;
static bool aktif, jeda, berhenti_penuh, tertahan;
static int bagian_maks, bagian_lapor;
static size_t lepas_bagian[REKAM_BAGIAN_MAKS];
static uint32_t lewat_awal[REKAM_BAGIAN_MAKS + 1];
static size_t batas[BATAS_MAKS];
static int n_batas;
static int no_simpan;
static uint32_t t_simpan;

struct penulis_t {
    File f;
    const uint16_t *data;
    size_t n, i, lepas, byte;
    size_t batas[BATAS_MAKS];
    int n_batas, k, bagian, n_bagian, nomor_awal;
    unsigned lewat;
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
int rekam_bagian(void) { return (int)min<size_t>(n / REKAM_N, bagian_maks ? bagian_maks - 1 : 0) + 1; }
size_t rekam_n(void) { return n - (size_t)(rekam_bagian() - 1) * REKAM_N; }
size_t rekam_n_sesi(void) { return n; }

static size_t ruang_bebas() { return LittleFS.totalBytes() - LittleFS.usedBytes(); }

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
    buf = (uint16_t *)ps_malloc(SESI_N * sizeof(uint16_t));
    if (!buf) Serial.println("PERINGATAN: PSRAM gagal, perekaman mentah nonaktif");
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

static unsigned lewat_bagian(int k)
{
    const int n_bagian = (int)((n + REKAM_N - 1) / REKAM_N);
    return lewat_awal[k + 1 < n_bagian ? k + 1 : REKAM_BAGIAN_MAKS] - lewat_awal[k];
}

static bool buka_bagian(int k)
{
    const int nomor = tulis.nomor_awal + k;
    tulis.bagian = k;
    nama(nomor, tulis.path, sizeof tulis.path);
    tulis.f = LittleFS.open(tulis.path, "w");
    if (!tulis.f) {
        menulis = false;
        tertahan = true;
        Serial.printf("GAGAL membuka %s: bagian %d-%d tetap di PSRAM, ulangi simpan dengan r / tahan B3\n",
                      tulis.path, k + 1, tulis.n_bagian);
        tampilan_pesan("GAGAL SIMPAN", "tekan r ulangi");
        return false;
    }
    const size_t awal = (size_t)k * REKAM_N;
    tulis.data = buf + awal;
    tulis.n = min(n - awal, REKAM_N);
    tulis.i = 0;
    tulis.k = 0;
    tulis.lepas = lepas_bagian[k];
    tulis.lewat = lewat_bagian(k);
    tulis.n_batas = 0;
    for (int j = 0; j < n_batas; j++)
        if (batas[j] > awal && batas[j] < awal + tulis.n) tulis.batas[tulis.n_batas++] = batas[j] - awal;
    const float persen = tulis.n ? 100.0f * tulis.lepas / tulis.n : 0.0f;
    tulis.byte = tulis.f.printf("# fs=%u n=%u lewat=%u lepas=%u (%.0f%%)", ECG_FS, (unsigned)tulis.n,
                                tulis.lewat, (unsigned)tulis.lepas, persen);
    if (k) tulis.byte += tulis.f.printf(" lanjutan=%03d celah=0", nomor - 1);
    tulis.byte += tulis.f.print("\n");
    menulis = true;
    tertahan = false;
    return true;
}

static void tutup_tulis(bool gagal)
{
    tulis.f.close();
    const size_t ukuran = LittleFS.open(tulis.path, "r").size();
    const float persen = tulis.n ? 100.0f * tulis.lepas / tulis.n : 0.0f;
    if (gagal) Serial.printf("GAGAL: LittleFS penuh setelah %u sampel, %s terpotong\n",
                             (unsigned)tulis.i, tulis.path);
    if (ukuran != tulis.byte)
        Serial.printf("PERINGATAN: %s berukuran %u B, tertulis %u B\n", tulis.path, (unsigned)ukuran,
                      (unsigned)tulis.byte);
    Serial.printf("SIMPAN %u sampel (%.1f detik, %d segmen), %u terlewat, elektroda lepas %.0f%% -> %s\n",
                  (unsigned)tulis.n, (float)tulis.n / ECG_FS, tulis.n_batas + 1, tulis.lewat, persen,
                  tulis.path);
    if (tulis.lepas > tulis.n / 10)
        Serial.println("PERINGATAN: elektroda lepas >10% — rekaman ini kemungkinan besar kosong.");
    no_simpan = tulis.nomor_awal + tulis.bagian;
    t_simpan = millis();
    menulis = false;
    if (!gagal && tulis.bagian + 1 < tulis.n_bagian) { buka_bagian(tulis.bagian + 1); return; }
    tampilan_bunyi(BIP_SIMPAN_MS);
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
    const size_t ditulis = tulis.f.write((const uint8_t *)blok_tulis, len);
    tulis.byte += ditulis;
    const bool gagal = ditulis != len;
    if (gagal || tulis.i >= tulis.n) tutup_tulis(gagal);
}

static void selesaikan_tulis()
{
    while (menulis) langkah_tulis();
}

static void simpan_sesi()
{
    aktif = false;
    buzzer(false);
    lewat_awal[REKAM_BAGIAN_MAKS] = akuisisi_lewat();
    if (n_batas && batas[n_batas - 1] >= n) n_batas--;
    tulis.n_bagian = (int)((n + REKAM_N - 1) / REKAM_N);
    if (!tulis.n_bagian) { Serial.println("REKAM: sesi kosong, tidak ada yang disimpan"); return; }
    tulis.nomor_awal = terakhir() + 1;
    Serial.printf("REKAM berhenti: %u sampel (%.1f detik), menulis %d berkas dari PSRAM\n", (unsigned)n,
                  (float)n / ECG_FS, tulis.n_bagian);
    buka_bagian(0);
}

void rekam_layani(void)
{
    if (aktif && rekam_bagian() != bagian_lapor) {
        bagian_lapor = rekam_bagian();
        Serial.printf("REKAM lanjut bagian %d (di PSRAM, ditulis saat berhenti)\n", bagian_lapor);
    }
    if (berhenti_penuh) {
        berhenti_penuh = false;
        const bool ruang = bagian_maks < REKAM_BAGIAN_MAKS;
        Serial.printf("REKAM berhenti: batas sesi %d bagian (%u detik) tercapai%s\n", bagian_maks,
                      (unsigned)(batas_sesi / ECG_FS), ruang ? ", LittleFS tidak cukup untuk bagian berikutnya" : "");
        tampilan_pesan(ruang ? "RUANG PENUH" : "BATAS SESI", "menyimpan...");
        simpan_sesi();
    }
    if (menulis && !akuisisi_isi()) langkah_tulis();
}

void rekam_sampel(uint16_t s)
{
    if (!aktif || jeda || !buf) return;
    const size_t k = n / REKAM_N;
    if (n % REKAM_N == 0) lewat_awal[k] = akuisisi_lewat();
    buf[n++] = s;
    if (digitalRead(PIN_LOP) || digitalRead(PIN_LON)) lepas_bagian[k]++;
    if (n >= batas_sesi) { aktif = false; berhenti_penuh = true; }
}

void rekam_toggle(void)
{
    if (aktif) { simpan_sesi(); return; }
    if (tertahan) { buka_bagian(tulis.bagian); return; }
    const int nomor_akhir = terakhir();
    bagian_maks = (int)min<size_t>(REKAM_BAGIAN_MAKS, ruang_bebas() / RUANG_BERKAS_PENUH);
    bagian_maks = min(bagian_maks, REKAM_NOMOR_MAKS - nomor_akhir);
    const char *tolak = akuisisi_sumber() != SUMBER_ADC ? "REKAM hanya dari sensor"
                      : daya_mode() >= 0 ? "REKAM ditolak: mode daya pN aktif ('p' = normal)"
                      : menu_terbuka() ? "REKAM ditolak: tutup menu dulu"
                      : menulis ? "REKAM ditolak: masih menyimpan sesi sebelumnya"
                      : !buf ? "REKAM ditolak: PSRAM tidak tersedia"
                      : nomor_akhir >= REKAM_NOMOR_MAKS ? "REKAM ditolak: nomor rekaman habis, hapus dulu (h<n>)"
                      : bagian_maks <= 0 ? "REKAM ditolak: LittleFS penuh, tarik data dulu" : nullptr;
    if (tolak) {
        Serial.println(tolak);
        const bool tunggu = menulis;
        tampilan_pesan(tunggu ? "TUNGGU" : akuisisi_sumber() != SUMBER_ADC || daya_mode() >= 0 || menu_terbuka() ? "TOLAK" : "PENUH",
                       tunggu ? "masih menyimpan" : akuisisi_replay() ? "hanya sensor ADC" : "rekam ditolak");
        return;
    }
    batas_sesi = (size_t)bagian_maks * REKAM_N;
    n = 0;
    n_batas = 0;
    jeda = false;
    berhenti_penuh = false;
    bagian_lapor = 1;
    memset(lepas_bagian, 0, sizeof lepas_bagian);
    memset(lewat_awal, 0, sizeof lewat_awal);
    akuisisi_nol_lewat();
    aktif = true;
    Serial.printf("REKAM mulai (maks %d bagian = %u detik)\n", bagian_maks, (unsigned)(batas_sesi / ECG_FS));
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
