// Harness pembanding C vs Python. Data uji: test/golden_ref.h (GENERATED).
//
//   pio test -e native      di PC, tanpa board
//
// Yang diuji per tahap, bukan cuma hasil akhir: kalau probabilitas meleset,
// tahap mana yang salah harus langsung ketahuan.
#include <unity.h>
#include <math.h>
#include <string.h>
#include <stdio.h>

#include "../golden_ref.h"
#include "ecg_pipeline.h"

static float buf_filtered[GOLDEN_N];
static float buf_window[GOLDEN_WIN_LEN];

static void bandingkan(const char *tahap, const float *dapat, const float *harus,
                       size_t n, float tol)
{
    size_t i_terburuk = 0;
    float terburuk = 0.0f;
    for (size_t i = 0; i < n; i++) {
        float d = fabsf(dapat[i] - harus[i]);
        if (d > terburuk) { terburuk = d; i_terburuk = i; }
    }
    if (terburuk > tol) {
        char pesan[192];
        snprintf(pesan, sizeof(pesan),
                 "%s: selisih terbesar %.6g di indeks %zu (dapat %.6g, harus %.6g)",
                 tahap, (double)terburuk, i_terburuk,
                 (double)dapat[i_terburuk], (double)harus[i_terburuk]);
        TEST_FAIL_MESSAGE(pesan);
    }
}

// Tahap 1 — bandpass kausal atas seluruh potongan sekaligus.
void test_bandpass(void)
{
    float state[ECG_N_SOS * 2];
    memset(state, 0, sizeof(state));
    ecg_bandpass(golden_raw, buf_filtered, GOLDEN_N, state);
    bandingkan("bandpass", buf_filtered, golden_filtered, GOLDEN_N, GOLDEN_TOL_FILTER);
}

// Tahap 1b — streaming: dipanggil per potongan HARUS sama dengan sekali jalan.
// Kalau ini gagal sementara test_bandpass lolos, state antar-panggilan bocor.
void test_bandpass_streaming(void)
{
    float state[ECG_N_SOS * 2];
    memset(state, 0, sizeof(state));
    const size_t blok = 64;
    for (size_t i = 0; i < GOLDEN_N; i += blok) {
        size_t n = (i + blok <= GOLDEN_N) ? blok : (GOLDEN_N - i);
        ecg_bandpass(golden_raw + i, buf_filtered + i, n, state);
    }
    bandingkan("bandpass streaming", buf_filtered, golden_filtered,
               GOLDEN_N, GOLDEN_TOL_FILTER);
}

// Tahap 2 — segmentasi + z-score per window.
void test_window_zscore(void)
{
    for (int b = 0; b < GOLDEN_N_BEAT; b++) {
        TEST_ASSERT_TRUE_MESSAGE(
            ecg_window_zscore(golden_filtered, GOLDEN_N, golden_r[b], buf_window),
            "window seharusnya muat di sinyal");
        bandingkan("z-score", buf_window, golden_window + (size_t)b * GOLDEN_WIN_LEN,
                   GOLDEN_WIN_LEN, GOLDEN_TOL_ZSCORE);
    }
}

// Sifat z-score: mean 0, std 1. Lolos walau golden salah — menangkap salah rumus.
void test_zscore_sifat(void)
{
    TEST_ASSERT_TRUE(ecg_window_zscore(golden_filtered, GOLDEN_N, golden_r[0], buf_window));
    float mean = 0.0f;
    for (int i = 0; i < GOLDEN_WIN_LEN; i++) mean += buf_window[i];
    mean /= GOLDEN_WIN_LEN;
    float var = 0.0f;
    for (int i = 0; i < GOLDEN_WIN_LEN; i++) var += (buf_window[i] - mean) * (buf_window[i] - mean);
    TEST_ASSERT_FLOAT_WITHIN(1e-3f, 0.0f, mean);
    TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1.0f, sqrtf(var / GOLDEN_WIN_LEN));
}

// Tahap 3 — fitur RR. Beat 0 & 1 golden sudah punya tetangga (diambil dari
// record utuh), jadi indeks di sini relatif ke daftar r yang sama.
void test_rr_features(void)
{
    float rr[3];
    for (int b = 2; b < GOLDEN_N_BEAT; b++) {
        TEST_ASSERT_TRUE_MESSAGE(
            ecg_rr_features(golden_r, GOLDEN_N_BEAT, b, ECG_FS, rr),
            "rr_features seharusnya berhasil untuk i >= 2");
        // Catatan: golden_rr dihitung dari r record UTUH; beat 0-1 di daftar ini
        // memakai tetangga di luar potongan, jadi yang dibandingkan mulai b=2.
        bandingkan("rr", rr, golden_rr + (size_t)b * GOLDEN_N_RR, 1, 1e-3f);
    }
}

int main(int argc, char **argv)
{
    (void)argc; (void)argv;
    UNITY_BEGIN();
    RUN_TEST(test_bandpass);
    RUN_TEST(test_bandpass_streaming);
    RUN_TEST(test_window_zscore);
    RUN_TEST(test_zscore_sifat);
    RUN_TEST(test_rr_features);
    return UNITY_END();
}
