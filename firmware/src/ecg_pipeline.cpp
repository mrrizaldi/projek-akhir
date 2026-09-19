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

int ecg_rr_features(const int *r, size_t n_r, size_t i, int fs, float out[ECG_N_RR_DASAR])
{
#if ECG_RR_RATIO
    // Bentuk RASIO semua (P3): RR0/avgRR, RR+1/RR0, RR-1/RR0, tRR0.
    // Butuh r[i+1] -> keputusan beat i keluar setelah R berikutnya terdeteksi
    // (tunda 1 beat, GATE G2). Nilai absolut dalam detik dibuang karena berbeda
    // antar-orang: model belajar identitas pasien, lawan semangat inter-patient.
    if (i < 2 || i + 1 >= n_r) {
        return 0;
    }
    const double dt = 1.0 / (double)fs;
    const double rr0 = (r[i] - r[i - 1]) * dt;        // d[i-1]
    const double rr_plus1 = (r[i + 1] - r[i]) * dt;   // d[i]
    const double rr_minus1 = (r[i - 1] - r[i - 2]) * dt;  // d[i-2]

    // Rata-rata & std KAUSAL atas <= ECG_RR_LOCAL_WINDOW interval terakhir,
    // termasuk interval ini. Jendela MENYUSUT di awal — jangan di-pad.
    const size_t j = i - 1;
    const size_t start = (j >= ECG_RR_LOCAL_WINDOW - 1) ? j - (ECG_RR_LOCAL_WINDOW - 1) : 0;
    double jumlah = 0.0, jumlah2 = 0.0;
    for (size_t k = start; k <= j; k++) {
        const double d = (r[k + 1] - r[k]) * dt;
        jumlah += d;
        jumlah2 += d * d;
    }
    const double n = (double)(j - start + 1);
    const double avg = jumlah / n;
    double var = jumlah2 / n - avg * avg;
    if (var < 0.0) var = 0.0;                          // galat pembulatan
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
    const double rr_sebelumnya = (r[i - 1] - r[i - 2]) * dt;

    const size_t j = i - 1;
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
#endif
}

#if ECG_QRSW
float ecg_qrs_lebar(const float *window, float frac)
{
    // Lebar QRS pada `frac` x puncak, dalam SAMPEL. Window sudah z-score dan
    // puncak R sudah didudukkan di ECG_R_IN_WINDOW oleh segmentasi.
    // Toleransi +-ECG_QRSW_CARI karena residu posisi memang +-2 sampel.
    int lo = ECG_R_IN_WINDOW - ECG_QRSW_CARI;
    int hi = ECG_R_IN_WINDOW + ECG_QRSW_CARI;
    if (lo < 0) lo = 0;
    if (hi > ECG_WIN_LEN_ - 1) hi = ECG_WIN_LEN_ - 1;

    int ip = lo;
    for (int i = lo + 1; i <= hi; i++) {
        if (window[i] > window[ip]) ip = i;
    }
    const float ambang = frac * window[ip];

    int kiri = 0;
    for (int i = ip - 1; i >= 0; i--) {
        if (window[i] < ambang) { kiri = i; break; }
    }
    int kanan = ECG_WIN_LEN_ - 1;
    for (int i = ip + 1; i < ECG_WIN_LEN_; i++) {
        if (window[i] < ambang) { kanan = i; break; }
    }
    return (float)(kanan - kiri);
}

int ecg_qrs_width_features(const float *window, float *riwayat, size_t n_riwayat,
                           float out[2])
{
    // riwayat: milik pemanggil, 2 x ECG_RR_LOCAL_WINDOW float (QRSw2 lalu QRSw4),
    // ring sederhana. n_riwayat = berapa beat yang sudah masuk (jenuh di jendela).
    // Normalisasi = rerata KAUSAL lebar w beat terakhir, TERMASUK beat ini —
    // sama bentuknya dengan rata_lokal di ecg_rr_features.
    const float frac[2] = {0.5f, 0.25f};
    for (int c = 0; c < 2; c++) {
        const float lebar = ecg_qrs_lebar(window, frac[c]);
        float *buf = riwayat + c * ECG_RR_LOCAL_WINDOW;
        const size_t slot = n_riwayat % ECG_RR_LOCAL_WINDOW;
        buf[slot] = lebar;
        const size_t n = (n_riwayat + 1 < ECG_RR_LOCAL_WINDOW)
                       ? n_riwayat + 1 : ECG_RR_LOCAL_WINDOW;
        double jumlah = 0.0;
        for (size_t k = 0; k < n; k++) jumlah += buf[k];
        const double rerata = jumlah / (double)n;
        out[c] = (float)(lebar / (rerata > 1e-8 ? rerata : 1e-8));
    }
    return 1;
}
#endif


// ── Pan-Tompkins ────────────────────────────────────────────────────────────
// Port dari model/src/preprocessing.py. Tiap tahap kausal, jadi bisa dijalankan
// per potongan nanti; versi ini masih blok penuh supaya mudah diadu ke golden.

static void pt_bandpass(const float *in, float *out, size_t n)
{
    float state[ECG_PT_N_SOS * 2] = {0.0f};
    for (size_t i = 0; i < n; i++) {
        float x = in[i];
        for (int k = 0; k < ECG_PT_N_SOS; k++) {
            const float *c = &ecg_pt_sos[k * 6];
            float *s = &state[k * 2];
            const float y = c[0] * x + s[0];
            s[0] = c[1] * x - c[4] * y + s[1];
            s[1] = c[2] * x - c[5] * y;
            x = y;
        }
        out[i] = x;
    }
}

// y[i] = (x[i] + 2x[i-1] - 2x[i-3] - x[i-4]) * fs/8  — kernel klasik yang
// digeser 2 sampel agar kausal (lihat docs/preprocessing-walkthrough §3.2).
static void pt_derivative(float *x, size_t n)
{
    const float skala = (float)ECG_FS / 8.0f;
    float h[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    for (size_t i = 0; i < n; i++) {
        const float xi = x[i];
        x[i] = (xi + 2.0f * h[0] - 2.0f * h[2] - h[3]) * skala;
        h[3] = h[2];
        h[2] = h[1];
        h[1] = h[0];
        h[0] = xi;
    }
}

static void pt_mwi(float *x, size_t n)
{
    float buf[ECG_PT_MWI_LEN] = {0.0f};
    double jumlah = 0.0;                 // double: 100k penjumlahan float meleleh
    int pos = 0;
    for (size_t i = 0; i < n; i++) {
        jumlah += x[i] - buf[pos];
        buf[pos] = x[i];
        pos = (pos + 1) % ECG_PT_MWI_LEN;
        x[i] = (float)(jumlah / ECG_PT_MWI_LEN);
    }
}

int ecg_detect_r(const float *filtered, size_t n, float *scratch,
                 int *out, int out_maks)
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

    // Inisialisasi ambang dari 2 detik pertama: asumsinya ada minimal 1 QRS.
    const size_t n_awal = (n < (size_t)(2 * ECG_FS)) ? n : (size_t)(2 * ECG_FS);
    double spki = scratch[0], jumlah = 0.0;
    for (size_t i = 0; i < n_awal; i++) {
        if (scratch[i] > spki) spki = scratch[i];
        jumlah += scratch[i];
    }
    double npki = jumlah / n_awal;

    int jml = 0;
    long terakhir = -(long)ECG_PT_REFRACTORY;
    for (size_t i = 1; i + 1 < n; i++) {
        // Puncak lokal, asimetris (> kiri, >= kanan) supaya plateau datar tidak
        // menghasilkan nol puncak maupun puncak ganda.
        if (!(scratch[i] > scratch[i - 1] && scratch[i] >= scratch[i + 1])) {
            continue;
        }
        if ((long)i - terakhir < (long)ECG_PT_REFRACTORY) {
            continue;
        }
        const double v = scratch[i];
        const double ambang = npki + 0.25 * (spki - npki);
        if (v > ambang) {
            spki = 0.125 * v + 0.875 * spki;
            if (jml < out_maks) out[jml] = (int)i;
            jml++;
            terakhir = (long)i;
        } else {
            npki = 0.125 * v + 0.875 * npki;
        }
    }
    return (jml < out_maks) ? jml : out_maks;
}

int ecg_align_r(const float *filtered, size_t n, int r_kasar)
{
    int lo = r_kasar - ECG_PT_OFFSET;
    int a = lo - ECG_PT_REFINE;
    int b = lo + ECG_PT_REFINE;
    if (a < 0) a = 0;
    if (b > (int)n - 1) b = (int)n - 1;
    if (a > b) return lo - ECG_GROUP_DELAY;

    int puncak = a;
    for (int i = a + 1; i <= b; i++) {
        if (filtered[i] > filtered[puncak]) puncak = i;
    }
    return puncak - ECG_GROUP_DELAY;
}
