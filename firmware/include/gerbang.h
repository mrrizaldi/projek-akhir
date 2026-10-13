#ifndef GERBANG_H
#define GERBANG_H

#include <stdint.h>
#include "ecg_live.h"

enum { FASE_KALIBRASI, FASE_BAIK, FASE_BURUK };

constexpr int AMBANG_AYUN = 60;

constexpr uint32_t STABIL_MS = 10UL * 60 * 1000;
constexpr uint32_t RR_TENANG_MS = 30UL * 1000;

struct gerbang_kualitas_t {
    int ayun, ayun_bersih, hum50, mentah_min, mentah_maks;
    bool clipping;
};
const gerbang_kualitas_t &gerbang_kualitas(void);

void gerbang_mulai_sesi(void);
uint32_t gerbang_t_sesi_ms(void);
uint32_t gerbang_tenang_ms(void);

void gerbang_nilai_kualitas(float mentah);
void gerbang_nilai_fase(const ecg_beat_t &beat);
void gerbang_lapor_kalibrasi(const ecg_beat_t &beat);

int gerbang_fase(void);
const char *gerbang_nama_fase(void);

bool gerbang_lewati(void);
void gerbang_set_lewati(bool on);
bool gerbang_lapor(void);
void gerbang_set_lapor(bool on);

#endif
