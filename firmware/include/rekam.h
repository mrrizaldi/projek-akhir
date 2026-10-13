// Rekaman sinyal mentah: buffer PSRAM selama merekam, lalu satu berkas
// bernomor per rekaman di LittleFS (/rekam/001.csv, 002, ...).
//
// Format berkas (dibaca model/scripts/pull_recording.py lewat dump):
//   # fs=360 n=<sampel> lewat=<hilang> lepas=<LO aktif> (<persen>%)
//   <counts ADC per baris>
//   # jeda                  <- batas segmen: rekaman dijeda lalu dilanjutkan
//   <counts ADC per baris>
// n = total sampel semua segmen. Selama jeda sampel tidak disimpan, jadi dua
// segmen yang bersebelahan TIDAK kontinu di waktu.
#ifndef REKAM_H
#define REKAM_H

#include <stddef.h>
#include <stdint.h>
#include "ecg_preproc.h"   // ECG_FS

#define REKAM_DIR  "/rekam"
#define REKAM_POLA "/rekam/%03d.csv"       // snprintf(buf, n, REKAM_POLA, nomor)
constexpr int REKAM_NOMOR_MAKS = 999;
constexpr size_t REKAM_SAMPEL_MAKS = (size_t)ECG_FS * 300;  // 300 detik, PSRAM 216 KB

// Buffer PSRAM + mount LittleFS. Rekaman lama /rekaman.csv dipindah ke nomor 1.
void rekam_siapkan(void);

bool rekam_aktif(void);                    // sesi rekaman terbuka (termasuk saat jeda)
bool rekam_tolak(const char *apa);
bool rekam_dijeda(void);
size_t rekam_n(void);                      // sampel di buffer
void rekam_toggle(void);                   // mulai, atau simpan ke berkas bernomor baru
void rekam_jeda(void);                     // jeda <-> lanjut; no-op bila tidak merekam
// Nomor berkas yang disimpan < 3 detik lalu, untuk label layar; 0 = tidak ada.
int rekam_baru_disimpan(void);
void rekam_sampel(uint16_t s);             // tiap sampel; no-op bila tidak merekam

// Nomor berkas yang ada, urut naik. Return jumlah (<= maks).
int rekam_daftar(int *nomor, int maks);
void rekam_cetak_daftar(void);             // daftar + ukuran + sisa LittleFS ke serial
// Dump ke serial di antara ---MULAI--- / ---SELESAI---. nomor <= 0 = terakhir.
bool rekam_dump(int nomor);
bool rekam_hapus(int nomor);

size_t rekam_sampel_n(int nomor);          // n dari header berkas; 0 = tidak ada
// Isi berkas (counts ADC) ke buf, untuk replay rekaman. Return jumlah sampel.
size_t rekam_muat(int nomor, uint16_t *buf, size_t maks);

#endif
