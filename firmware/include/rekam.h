#ifndef REKAM_H
#define REKAM_H

#include <stddef.h>
#include <stdint.h>
#include "ecg_preproc.h"

#define REKAM_DIR  "/rekam"
#define REKAM_POLA "/rekam/%03d.csv"
constexpr int REKAM_NOMOR_MAKS = 999;
#ifndef REKAM_DETIK
#define REKAM_DETIK 300
#endif
constexpr size_t REKAM_DETIK_MAKS = REKAM_DETIK;
constexpr size_t REKAM_SAMPEL_MAKS = (size_t)ECG_FS * REKAM_DETIK_MAKS;

void rekam_siapkan(void);

bool rekam_aktif(void);
bool rekam_tolak(const char *apa);
bool rekam_dijeda(void);
bool rekam_menulis(void);
void rekam_layani(void);
size_t rekam_n(void);
size_t rekam_n_sesi(void);
int rekam_bagian(void);
void rekam_toggle(void);
void rekam_jeda(void);
int rekam_baru_disimpan(void);
void rekam_sampel(uint16_t s);

int rekam_daftar(int *nomor, int maks);
void rekam_cetak_daftar(void);
bool rekam_dump(int nomor);
bool rekam_hapus(int nomor);

size_t rekam_sampel_n(int nomor);
size_t rekam_muat(int nomor, uint16_t *buf, size_t maks);

#endif
