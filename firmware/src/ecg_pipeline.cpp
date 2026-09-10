// Port golden reference preprocessing ke C. Kontrak & aturan: include/ecg_pipeline.h
//
// STUB — logika algoritma ditulis manual (aturan #1 CLAUDE.md).
// Jalankan `pio test -e native` untuk melihat apa yang belum cocok.
#include "ecg_pipeline.h"

void ecg_bandpass(const float *in, float *out, size_t n, float *state)
{
    // TODO: kaskade ECG_N_SOS biquad, bentuk langsung II transposed:
    //   y      = b0*x + s0
    //   s0_baru = b1*x - a1*y + s1
    //   s1_baru = b2*x - a2*y
    // keluaran section ke-k jadi masukan section ke-(k+1).
    (void)in; (void)out; (void)n; (void)state;
}

int ecg_window_zscore(const float *filtered, size_t n, int r, float *out)
{
    // TODO: cek batas, hitung mean & std populasi atas ECG_WIN_LEN_ sampel,
    // lalu (x - mean) / (std + ECG_ZSCORE_EPS).
    (void)filtered; (void)n; (void)r; (void)out;
    return 0;
}

int ecg_rr_features(const int *r, size_t n_r, size_t i, int fs, float out[3])
{
    // TODO: rr_prev, rr_ratio (jendela kausal <=10, menyusut di awal), drr.
    (void)r; (void)n_r; (void)i; (void)fs; (void)out;
    return 0;
}
