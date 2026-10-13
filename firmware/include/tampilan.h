#ifndef TAMPILAN_H
#define TAMPILAN_H

#include <stdint.h>
#include "ecg_live.h"

void tampilan_mulai(void);
void tampilan_layani(void);

void tampilan_led(uint8_t r, uint8_t g, uint8_t b);
void tampilan_bunyi(uint32_t ms);
void tampilan_hapus_jadwal(void);
void tampilan_pesan(const char *besar, const char *kecil);

void tampilan_beat(const ecg_beat_t &beat, bool aritmia);
void tampilan_sampel(void);

void tampilan_gambar_tombol(int i);

void tampilan_set_monitor(bool on);
bool tampilan_monitor(void);

constexpr int TAMPILAN_BARIS = 6, TAMPILAN_KOLOM = 26;
void tampilan_menu_bingkai(const char *judul, const char *petunjuk1, const char *petunjuk2);
void tampilan_menu_baris(int r, const char *teks, bool sorot, uint16_t warna = 0xFFFF);

bool tampilan_bisu(void);
void tampilan_set_bisu(bool on);
bool tampilan_beku(void);
void tampilan_set_beku(bool on);

#endif
