// Akuisisi: timer ISR 360 Hz -> antrean -> loop(). Sumber sinyal ADC AD8232,
// replay golden_raw (record 208), atau replay rekaman /rekam/NNN.csv.
//
// ADC dibaca di ISR, BUKAN di loop: beban pemrosesan menggumpal — rata-rata
// 82 us/sampel tapi puncaknya 33 ms saat deteksi dan inferensi bersamaan. Kalau
// ADC dibaca di loop, ~12 sampel hilang tiap detik dan interval RR rusak
// (docs/firmware-walkthrough.md §5b).
#ifndef AKUISISI_H
#define AKUISISI_H

#include <stddef.h>
#include <stdint.h>

constexpr size_t ANTRE_N = 256;            // >= 13 (puncak burst), dibulatkan pangkat 2

// Menyiapkan sampel replay lalu menjalankan timer. Dipanggil terakhir di setup().
void akuisisi_mulai(void);
// Mengambil satu sampel dari antrean; false = antrean kosong.
bool akuisisi_ambil(uint16_t *sampel);
size_t akuisisi_isi(void);                 // sampel menunggu di antrean
uint32_t akuisisi_lewat(void);             // sampel hilang karena antrean penuh
void akuisisi_nol_lewat(void);
// Timer mati = p0 tangga daya.
void akuisisi_timer(bool jalan);

// Sumber sinyal. Semua replay melewati gerbang waktu kalibrasi (gerbang.cpp).
enum { SUMBER_ADC, SUMBER_ACUAN, SUMBER_REKAM };
int akuisisi_sumber(void);
int akuisisi_sumber_rekam(void);           // nomor /rekam/NNN.csv bila SUMBER_REKAM
bool akuisisi_replay(void);                // sumber != ADC
// Ganti sumber lalu sesi baru (kalibrasi + hitungan dari nol). SUMBER_REKAM
// memuat berkas nomor ke PSRAM (timer dihentikan selama memuat). simpan =
// pilihan ditulis ke NVS dan dipakai lagi saat boot. false = rekaman gagal
// dimuat, sumber tidak berubah.
bool akuisisi_set_sumber(int sumber, int nomor, bool simpan);
// ADC <-> replay golden_raw (serial 'y'); dari replay rekaman kembali ke ADC.
void akuisisi_ganti_sumber(void);

#endif
