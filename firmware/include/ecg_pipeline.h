#ifndef ECG_PIPELINE_H
#define ECG_PIPELINE_H

#include <stddef.h>
#include "ecg_preproc.h"

#define ECG_PT_INIT_N (2 * ECG_FS)

#ifdef __cplusplus
extern "C" {
#endif

void ecg_bandpass(const float *in, float *out, size_t n, float *state);

int ecg_window_zscore(const float *filtered, size_t n, int r, float *out);

int ecg_rr_features(const int *r, size_t n_r, size_t i, int fs, float out[ECG_N_RR_DASAR]);

#if ECG_QRSW
float ecg_qrs_lebar(const float *window, float frac);

int ecg_qrs_width_features(const float *window, float *riwayat, size_t n_riwayat,
                           float out[2]);
#endif

int ecg_detect_r(const float *filtered, size_t n, float *scratch,
                 int *out, int out_maks);

int ecg_align_r(const float *filtered, size_t n, int r_kasar);

#ifdef __cplusplus
}
#endif
#endif
