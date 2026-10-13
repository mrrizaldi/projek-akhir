// Keluaran antarmuka alat: layar monitor TFT, NeoPixel, buzzer (klik, bip
// detak, bip kalibrasi).
//
// Layar landscape 320x172:
//   atas   HR (merah bila detak terakhir ARITMIA), arus/tegangan INA219,
//          status (REC detik / REPLAY / fase kualitas)
//   tengah gelombang EKG tersaring 0,5-40 Hz, skala otomatis per sapuan
//   bawah  tiga kotak tombol, kuning selama ditekan
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

bool tampilan_bisu(void);
void tampilan_set_bisu(bool on);
bool tampilan_beku(void);
void tampilan_set_beku(bool on);

#endif
