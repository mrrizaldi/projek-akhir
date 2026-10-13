#ifndef ECG_LIVE_H
#define ECG_LIVE_H

#include <stddef.h>
#include "ecg_pipeline.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ECG_LIVE_RING (4 * ECG_FS)
#ifndef ECG_LIVE_TIAP
#define ECG_LIVE_TIAP ECG_FS
#endif
#define ECG_LIVE_HIST 16
#define ECG_LIVE_TIMEOUT (3 * ECG_FS)

typedef struct {
    int r_abs;
    float window[ECG_WIN_LEN_];
    float rr[ECG_N_RR];
    int sinyal_hilang;
} ecg_beat_t;

void ecg_live_reset(void);

int ecg_live_push(float sampel_mentah, ecg_beat_t *beat);

float ecg_live_tersaring_terakhir(void);

size_t ecg_live_total_sampel(void);
int ecg_live_total_beat(void);

#ifdef __cplusplus
}
#endif
#endif
