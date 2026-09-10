// Port golden reference preprocessing ke C. Kontrak & aturan: include/ecg_pipeline.h
// Diverifikasi terhadap Python oleh test/test_preproc/ (pio test -e native).
#include "ecg_pipeline.h"

#include <math.h>

void ecg_bandpass(const float *in, float *out, size_t n, float *state)
{
    for (size_t i = 0; i < n; i++) {
        float x = in[i];
        for (int k = 0; k < ECG_N_SOS; k++) {
            const float *c = &ecg_sos[k * 6];   // b0 b1 b2 a0 a1 a2, a0 == 1
            float *s = &state[k * 2];
            float y = c[0] * x + s[0];
            s[0] = c[1] * x - c[4] * y + s[1];
            s[1] = c[2] * x - c[5] * y;
            x = y;
        }
        out[i] = x;
    }
}

int ecg_window_zscore(const float *filtered, size_t n, int r, float *out)
{
    const int start = r - ECG_WIN_PRE;
    if (start < 0 || (size_t)(start + ECG_WIN_LEN_) > n) {
        return 0;
    }
    const float *w = filtered + start;

    double jumlah = 0.0;
    for (int i = 0; i < ECG_WIN_LEN_; i++) {
        jumlah += w[i];
    }
    const double mean = jumlah / ECG_WIN_LEN_;

    double kuadrat = 0.0;
    for (int i = 0; i < ECG_WIN_LEN_; i++) {
        const double d = w[i] - mean;
        kuadrat += d * d;
    }
    const double std_pop = sqrt(kuadrat / ECG_WIN_LEN_);   // pembagi N, bukan N-1

    for (int i = 0; i < ECG_WIN_LEN_; i++) {
        out[i] = (float)((w[i] - mean) / (std_pop + ECG_ZSCORE_EPS));
    }
    return 1;
}

int ecg_rr_features(const int *r, size_t n_r, size_t i, int fs, float out[3])
{
    if (i < 2 || i >= n_r) {
        return 0;
    }
    const double dt = 1.0 / (double)fs;
    const double rr_prev = (r[i] - r[i - 1]) * dt;
    const double rr_sebelumnya = (r[i - 1] - r[i - 2]) * dt;

    // Rata-rata KAUSAL atas <= ECG_RR_LOCAL_WINDOW interval terakhir, termasuk
    // interval ini. Jendela MENYUSUT di awal — jangan di-pad.
    const size_t j = i - 1;                       // d[j] = RR_prev beat i
    const size_t start = (j >= ECG_RR_LOCAL_WINDOW - 1) ? j - (ECG_RR_LOCAL_WINDOW - 1) : 0;
    double jumlah = 0.0;
    for (size_t k = start; k <= j; k++) {
        jumlah += (r[k + 1] - r[k]) * dt;
    }
    const double rata_lokal = jumlah / (double)(j - start + 1);

    out[0] = (float)rr_prev;
    out[1] = (float)(rr_prev / rata_lokal);
    out[2] = (float)(rr_prev - rr_sebelumnya);
    return 1;
}
