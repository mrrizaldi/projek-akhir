// Keluaran antarmuka alat: layar monitor TFT, NeoPixel, buzzer (klik, bip
// detak, bip kalibrasi).
//
// Layar landscape 320x172:
//   atas   HR (merah bila detak terakhir ARITMIA), arus/tegangan INA219,
//          status (REC detik / REPLAY / fase kualitas)
//   tengah gelombang EKG tersaring 0,5-40 Hz, skala otomatis per sapuan
//   bawah  tiga kotak tombol, kuning selama ditekan
// Selama menu terbuka layar yang sama dipakai menu (tampilan_menu_*).
#ifndef TAMPILAN_H
#define TAMPILAN_H

#include <stdint.h>
#include "ecg_live.h"

void tampilan_mulai(void);                 // bingkai layar monitor; sesudah perangkat_mulai()
// Tiap iterasi loop(): LED, teks 1 Hz, mematikan buzzer yang sudah habis waktunya.
void tampilan_layani(void);

void tampilan_led(uint8_t r, uint8_t g, uint8_t b);
void tampilan_bunyi(uint32_t ms);          // non-blocking
void tampilan_hapus_jadwal(void);          // buang bip detak yang menunggu

// Per beat (HR + jadwal bip) dan per sampel (bip terjadwal + gelombang).
void tampilan_beat(const ecg_beat_t &beat, bool aritmia);
void tampilan_sampel(void);

void tampilan_gambar_tombol(int i);        // kotak tombol i, kuning selama ditekan

// false = layar diserahkan ke menu: gelombang & teks monitor berhenti digambar
// (pipeline, bip, LED tetap jalan). true = layar monitor digambar ulang penuh.
void tampilan_set_monitor(bool on);
bool tampilan_monitor(void);

// Layar menu/halaman teks: judul di atas, TAMPILAN_BARIS baris x TAMPILAN_KOLOM
// huruf, dua baris petunjuk tombol di bawah. Baris yang isinya tidak berubah
// tidak digambar ulang. bingkai() mengosongkan layar dan ingatan baris.
constexpr int TAMPILAN_BARIS = 6, TAMPILAN_KOLOM = 26;
void tampilan_menu_bingkai(const char *judul, const char *petunjuk1, const char *petunjuk2);
void tampilan_menu_baris(int r, const char *teks, bool sorot, uint16_t warna = 0xFFFF);

bool tampilan_bisu(void);
void tampilan_set_bisu(bool on);
bool tampilan_beku(void);
void tampilan_set_beku(bool on);

#endif
