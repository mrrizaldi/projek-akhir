#ifndef KLASIFIKASI_H
#define KLASIFIKASI_H

#include <stddef.h>
#include <stdint.h>
#include "ecg_live.h"

void klasifikasi_mulai(void);
size_t klasifikasi_arena(void);
float klasifikasi_ambang(void);

bool klasifikasi_proses(const ecg_beat_t &beat);

struct klasifikasi_hitung_t {
    int total, aritmia, ditahan;
    uint32_t tunda_jml, tunda_n, tunda_maks;
};
const klasifikasi_hitung_t &klasifikasi_hitung(void);
void klasifikasi_reset(void);

#endif
