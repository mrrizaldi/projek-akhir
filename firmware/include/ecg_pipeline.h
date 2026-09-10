// Kontrak preprocessing on-device. Implementasi ada di src/ecg_pipeline.cpp
// dan HARUS menghasilkan angka yang sama dengan model/src/preprocessing.py
// (dibuktikan oleh test/test_preproc/, bandingkan ke test/golden_ref.h).
//
// Golden reference-nya Python. Kalau C dan Python beda, C yang salah.
#ifndef ECG_PIPELINE_H
#define ECG_PIPELINE_H

#include <stddef.h>
#include "ecg_preproc.h"   // GENERATED: koefisien SOS + konstanta

#ifdef __cplusplus
extern "C" {
#endif

// Bandpass kausal 0,5-40 Hz, 4 second-order section (ecg_sos di ecg_preproc.h).
// Streaming: state disimpan antar-panggilan supaya bisa dipanggil per potongan
// sinyal tanpa mengubah hasil. `state` = ECG_N_SOS x 2 float, di-nol-kan sekali.
//
// JANGAN memfilter maju-mundur. filtfilt mustahil real-time; model dilatih
// dengan filter kausal, dan group delay +4 sampel adalah bagian dari kontrak.
void ecg_bandpass(const float *in, float *out, size_t n, float *state);

// Potong window [r - ECG_WIN_PRE, r + ECG_WIN_POST) lalu z-score DI DALAM
// window itu sendiri: (x - mean) / (std + ECG_ZSCORE_EPS).
// std = populasi (pembagi N), bukan sampel (N-1) — numpy std() default.
// Return 0 kalau window tidak muat di sinyal.
int ecg_window_zscore(const float *filtered, size_t n, int r, float *out);

// Fitur ritme dari indeks R-peak. rr_prev = (r[i]-r[i-1])/fs;
// rr_ratio = rr_prev / rata-rata KAUSAL <=10 interval terakhir (jendela
// menyusut di awal); drr = rr_prev sekarang - rr_prev sebelumnya.
// Butuh i >= 2. Return 0 kalau belum cukup beat.
int ecg_rr_features(const int *r, size_t n_r, size_t i, int fs, float out[3]);

#ifdef __cplusplus
}
#endif
#endif  // ECG_PIPELINE_H
