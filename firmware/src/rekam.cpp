// Rekaman ke LittleFS. Kontrak: include/rekam.h
#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "rekam.h"

#include <Arduino.h>
#include <LittleFS.h>
#include <sys/stat.h>

#include "akuisisi.h"
#include "ecg_pipeline.h"
#include "perangkat.h"

constexpr uint32_t DETIK_MAKS = 300;
constexpr size_t REKAM_N = (size_t)ECG_FS * DETIK_MAKS;
constexpr int DAFTAR_MAKS = 64;            // ponytail: batas daftar tampilan saja; nomor baru tetap dari pindai penuh

static uint16_t *buf;
static size_t n;
static bool aktif;
static size_t lepas;                       // sampel dgn LO aktif selama merekam

bool rekam_aktif(void) { return aktif; }
size_t rekam_n(void) { return n; }

static void nama(int nomor, char *out, size_t len) { snprintf(out, len, REKAM_POLA, nomor); }

int rekam_daftar(int *nomor, int maks)
{
    int k = 0;
    File d = LittleFS.open(REKAM_DIR);
    if (!d || !d.isDirectory()) return 0;
    for (File f = d.openNextFile(); f && k < maks; f = d.openNextFile()) {
        const int x = atoi(f.name());
        if (x <= 0) continue;
        int j = k++;                       // sisip urut naik
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
    if (!buf) Serial.println("PERINGATAN: PSRAM gagal, perekaman mentah nonaktif");
    if (!LittleFS.begin(true)) { Serial.println("PERINGATAN: LittleFS gagal mount"); return; }
    LittleFS.mkdir(REKAM_DIR);
    struct stat st;                        // stat(), bukan exists(): exists() mencetak [E] bila tidak ada
    if (stat("/littlefs/rekaman.csv", &st) == 0 && !terakhir()) {
        char p[24];
        nama(1, p, sizeof p);
        if (LittleFS.rename("/rekaman.csv", p))
            Serial.printf("rekam: /rekaman.csv lama dipindah ke %s\n", p);
    }
}

void rekam_sampel(uint16_t s)
{
    if (!aktif || !buf || n >= REKAM_N) return;
    buf[n++] = s;
    if (digitalRead(PIN_LOP) || digitalRead(PIN_LON)) lepas++;
}

static void simpan()
{
    aktif = false;
    buzzer(false);       // menulis berkas memblok loop beberapa detik; bip jangan ikut tertahan
    const int nomor = terakhir() + 1;
    if (nomor > REKAM_NOMOR_MAKS) { Serial.println("GAGAL: nomor rekaman habis, hapus dulu (h<n>)"); return; }
    char p[24];
    nama(nomor, p, sizeof p);
    File f = LittleFS.open(p, "w");
    if (!f) { Serial.println("GAGAL membuka LittleFS"); return; }
    // 'lepas' menjawab yang tidak bisa dijawab data mentah: apakah elektroda
    // benar-benar menempel saat rekaman dibuat? AD8232 memarkir output di
    // mid-rail saat leads-off, dan garis datar itu menyamar sebagai "sinyal
    // tenang" di CSV.
    const unsigned lewat = (unsigned)akuisisi_lewat();
    const float persen = n ? 100.0f * lepas / n : 0.0f;
    f.printf("# fs=%u n=%u lewat=%u lepas=%u (%.0f%%)\n", ECG_FS, (unsigned)n, lewat,
             (unsigned)lepas, persen);
    size_t i = 0;
    for (; i < n; i++) if (f.printf("%u\n", buf[i]) == 0) break;
    f.close();
    if (i < n) Serial.printf("GAGAL: LittleFS penuh setelah %u sampel, %s terpotong\n",
                             (unsigned)i, p);
    Serial.printf("SIMPAN %u sampel (%.1f detik), %u terlewat, elektroda lepas %.0f%% -> %s\n",
                  (unsigned)n, (float)n / ECG_FS, lewat, persen, p);
    if (lepas > n / 10)
        Serial.println("PERINGATAN: elektroda lepas >10% — rekaman ini kemungkinan besar kosong.");
}

void rekam_toggle(void)
{
    if (aktif) { simpan(); return; }
    n = lepas = 0;
    akuisisi_nol_lewat();
    aktif = true;
    Serial.println("REKAM mulai");
}

bool rekam_dump(int nomor)
{
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
#endif
