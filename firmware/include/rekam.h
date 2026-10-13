// Rekaman sinyal mentah: buffer PSRAM selama merekam, lalu satu berkas
// bernomor per rekaman di LittleFS (/rekam/001.csv, 002, ...).
//
// Format berkas (dibaca model/scripts/pull_recording.py lewat dump):
//   # fs=360 n=<sampel> lewat=<hilang> lepas=<LO aktif> (<persen>%)
//   <counts ADC per baris>
#ifndef REKAM_H
#define REKAM_H

#include <stddef.h>
#include <stdint.h>

#define REKAM_DIR  "/rekam"
#define REKAM_POLA "/rekam/%03d.csv"       // snprintf(buf, n, REKAM_POLA, nomor)
constexpr int REKAM_NOMOR_MAKS = 999;

// Buffer PSRAM + mount LittleFS. Rekaman lama /rekaman.csv dipindah ke nomor 1.
void rekam_siapkan(void);

bool rekam_aktif(void);
size_t rekam_n(void);                      // sampel di buffer
void rekam_toggle(void);                   // mulai, atau simpan ke berkas bernomor baru
void rekam_sampel(uint16_t s);             // tiap sampel; no-op bila tidak merekam

// Nomor berkas yang ada, urut naik. Return jumlah (<= maks).
int rekam_daftar(int *nomor, int maks);
void rekam_cetak_daftar(void);             // daftar + ukuran + sisa LittleFS ke serial
// Dump ke serial di antara ---MULAI--- / ---SELESAI---. nomor <= 0 = terakhir.
bool rekam_dump(int nomor);
bool rekam_hapus(int nomor);

#endif
