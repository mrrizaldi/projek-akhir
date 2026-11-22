#include "ecg_pipeline.h"

#include <math.h>

constexpr int COEF_PER_SOS = 6;

void ecg_bandpass(const float *in, float *out, size_t n, float *state)
{
    for (size_t i = 0; i < n; i++) {
        float x = in[i];
        for (int k = 0; k < ECG_N_SOS; k++) {
            const float *c = &ecg_sos[k * COEF_PER_SOS];
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

    double total = 0.0;
    for (int i = 0; i < ECG_WIN_LEN_; i++) {
        total += w[i];
    }
    const double mean = total / ECG_WIN_LEN_;

    double squares = 0.0;
    for (int i = 0; i < ECG_WIN_LEN_; i++) {
        const double d = w[i] - mean;
        squares += d * d;
    }
    const double std_pop = sqrt(squares / ECG_WIN_LEN_);

    for (int i = 0; i < ECG_WIN_LEN_; i++) {
        out[i] = (float)((w[i] - mean) / (std_pop + ECG_ZSCORE_EPS));
    }
    return 1;
}

int ecg_rr_features(const int *r, size_t n_r, size_t i, int fs, float out[ECG_N_RR_DASAR])
{
#if ECG_RR_RATIO
    if (i < 2 || i + 1 >= n_r) {
        return 0;
    }
    const double dt = 1.0 / (double)fs;
    const double rr0 = (r[i] - r[i - 1]) * dt;
    const double rr_plus1 = (r[i + 1] - r[i]) * dt;
    const double rr_minus1 = (r[i - 1] - r[i - 2]) * dt;

    const size_t j = i - 1;
    const size_t start = (j >= ECG_RR_LOCAL_WINDOW - 1) ? j - (ECG_RR_LOCAL_WINDOW - 1) : 0;
    double total = 0.0, total2 = 0.0;
    for (size_t k = start; k <= j; k++) {
        const double d = (r[k + 1] - r[k]) * dt;
        total += d;
        total2 += d * d;
    }
    const double n = (double)(j - start + 1);
    const double avg = total / n;
    double var = total2 / n - avg * avg;
    if (var < 0.0) var = 0.0;
    const double sd = sqrt(var);

    out[0] = (float)(rr0 / avg);
    out[1] = (float)(rr_plus1 / rr0);
    out[2] = (float)(rr_minus1 / rr0);
    out[3] = (float)((rr0 - avg) / (sd > 1e-8 ? sd : 1e-8));
    return 1;
#else
    if (i < 2 || i >= n_r) {
        return 0;
    }
    const double dt = 1.0 / (double)fs;
    const double rr_prev = (r[i] - r[i - 1]) * dt;
    const double rr_before = (r[i - 1] - r[i - 2]) * dt;

    const size_t j = i - 1;
    const size_t start = (j >= ECG_RR_LOCAL_WINDOW - 1) ? j - (ECG_RR_LOCAL_WINDOW - 1) : 0;
    double total = 0.0;
    for (size_t k = start; k <= j; k++) {
        total += (r[k + 1] - r[k]) * dt;
    }
    const double local_mean = total / (double)(j - start + 1);

    out[0] = (float)rr_prev;
    out[1] = (float)(rr_prev / local_mean);
    out[2] = (float)(rr_prev - rr_before);
    return 1;
#endif
}

#if ECG_QRSW
float ecg_qrs_width(const float *window, float frac)
{
    int lo = ECG_R_IN_WINDOW - ECG_QRSW_CARI;
    int hi = ECG_R_IN_WINDOW + ECG_QRSW_CARI;
    if (lo < 0) lo = 0;
    if (hi > ECG_WIN_LEN_ - 1) hi = ECG_WIN_LEN_ - 1;

    int ip = lo;
    for (int i = lo + 1; i <= hi; i++) {
        if (window[i] > window[ip]) ip = i;
    }
    const float threshold = frac * window[ip];

    int left = 0;
    for (int i = ip - 1; i >= 0; i--) {
        if (window[i] < threshold) { left = i; break; }
    }
    int right = ECG_WIN_LEN_ - 1;
    for (int i = ip + 1; i < ECG_WIN_LEN_; i++) {
        if (window[i] < threshold) { right = i; break; }
    }
    return (float)(right - left);
}

int ecg_qrs_width_features(const float *window, float *history, size_t n_history,
                           float out[2])
{
    const float frac[2] = {0.5f, 0.25f};
    for (int c = 0; c < 2; c++) {
        const float width = ecg_qrs_width(window, frac[c]);
        float *buf = history + c * ECG_RR_LOCAL_WINDOW;
        const size_t slot = n_history % ECG_RR_LOCAL_WINDOW;
        buf[slot] = width;
        const size_t n = (n_history + 1 < ECG_RR_LOCAL_WINDOW)
                       ? n_history + 1 : ECG_RR_LOCAL_WINDOW;
        double total = 0.0;
        for (size_t k = 0; k < n; k++) total += buf[k];
        const double mean_value = total / (double)n;
        out[c] = (float)(width / (mean_value > 1e-8 ? mean_value : 1e-8));
    }
    return 1;
}
#endif

static void pt_bandpass(const float *in, float *out, size_t n)
{
    float state[ECG_PT_N_SOS * 2] = {0.0f};
    for (size_t i = 0; i < n; i++) {
        float x = in[i];
        for (int k = 0; k < ECG_PT_N_SOS; k++) {
            const float *c = &ecg_pt_sos[k * COEF_PER_SOS];
            float *s = &state[k * 2];
            const float y = c[0] * x + s[0];
            s[0] = c[1] * x - c[4] * y + s[1];
            s[1] = c[2] * x - c[5] * y;
            x = y;
        }
        out[i] = x;
    }
}

static void pt_derivative(float *x, size_t n)
{
    const float scale = (float)ECG_FS / 8.0f;
    float h[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    for (size_t i = 0; i < n; i++) {
        const float xi = x[i];
        x[i] = (xi + 2.0f * h[0] - 2.0f * h[2] - h[3]) * scale;
        h[3] = h[2];
        h[2] = h[1];
        h[1] = h[0];
        h[0] = xi;
    }
}

static void pt_mwi(float *x, size_t n)
{
    float buf[ECG_PT_MWI_LEN] = {0.0f};
    double total = 0.0;
    int pos = 0;
    for (size_t i = 0; i < n; i++) {
        total += x[i] - buf[pos];
        buf[pos] = x[i];
        pos = (pos + 1) % ECG_PT_MWI_LEN;
        x[i] = (float)(total / ECG_PT_MWI_LEN);
    }
}

int ecg_detect_r(const float *filtered, size_t n, float *scratch,
                 int *out, int out_max)
{
    if (n < 3) {
        return 0;
    }
    pt_bandpass(filtered, scratch, n);
    pt_derivative(scratch, n);
    for (size_t i = 0; i < n; i++) {
        scratch[i] *= scratch[i];
    }
    pt_mwi(scratch, n);

    const size_t n_start = (n < (size_t)ECG_PT_INIT_N) ? n : (size_t)ECG_PT_INIT_N;
    double spki = scratch[0], total = 0.0;
    for (size_t i = 0; i < n_start; i++) {
        if (scratch[i] > spki) spki = scratch[i];
        total += scratch[i];
    }
    double npki = total / n_start;

    int sum = 0;
    long last = -(long)ECG_PT_REFRACTORY;
    for (size_t i = 1; i + 1 < n; i++) {
        if (!(scratch[i] > scratch[i - 1] && scratch[i] >= scratch[i + 1])) {
            continue;
        }
        if ((long)i - last < (long)ECG_PT_REFRACTORY) {
            continue;
        }
        const double v = scratch[i];
        const double threshold = npki + 0.25 * (spki - npki);
        if (v > threshold) {
            spki = 0.125 * v + 0.875 * spki;
            if (sum < out_max) out[sum] = (int)i;
            sum++;
            last = (long)i;
        } else {
            npki = 0.125 * v + 0.875 * npki;
        }
    }
    return (sum < out_max) ? sum : out_max;
}

int ecg_align_r(const float *filtered, size_t n, int r_coarse)
{
    int lo = r_coarse - ECG_PT_OFFSET;
    int a = lo - ECG_PT_REFINE;
    int b = lo + ECG_PT_REFINE;
    if (a < 0) a = 0;
    if (b > (int)n - 1) b = (int)n - 1;
    if (a > b) return lo - ECG_GROUP_DELAY;

    int peak = a;
    for (int i = a + 1; i <= b; i++) {
        if (filtered[i] > filtered[peak]) peak = i;
    }
    return peak - ECG_GROUP_DELAY;
}
