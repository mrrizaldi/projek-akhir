#ifndef AKUISISI_H
#define AKUISISI_H

#include <stddef.h>
#include <stdint.h>

constexpr size_t ANTRE_N = 256;

void akuisisi_mulai(void);
bool akuisisi_ambil(uint16_t *sampel);
size_t akuisisi_isi(void);
uint32_t akuisisi_lewat(void);
uint32_t akuisisi_tick_hilang(void);
void akuisisi_nol_lewat(void);
void akuisisi_timer(bool jalan);

enum { SUMBER_ADC, SUMBER_ACUAN, SUMBER_REKAM };
int akuisisi_sumber(void);
int akuisisi_sumber_rekam(void);
bool akuisisi_replay(void);
bool akuisisi_set_sumber(int sumber, int nomor, bool simpan);
void akuisisi_ganti_sumber(void);

#endif
