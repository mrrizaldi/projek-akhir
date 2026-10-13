#include <unity.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#include "../golden_ref.h"
#include "ecg_pipeline.h"
#include "ecg_live.h"

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

void test_bandpass(void)
{
    float state[ECG_N_SOS * 2];
    memset(state, 0, sizeof(state));
    ecg_bandpass(golden_raw, buf_filtered, GOLDEN_N, state);
    bandingkan("bandpass", buf_filtered, golden_filtered, GOLDEN_N, GOLDEN_TOL_FILTER);
}

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

void test_rr_features(void)
{
    float rr[3];
    for (int b = GOLDEN_RR_FIRST; b < GOLDEN_N_BEAT; b++) {
        TEST_ASSERT_TRUE_MESSAGE(
            ecg_rr_features(golden_r, GOLDEN_N_BEAT, b, ECG_FS, rr),
            "rr_features seharusnya berhasil untuk i >= 2");
        bandingkan("rr", rr, golden_rr + (size_t)b * GOLDEN_N_RR,
                   GOLDEN_N_RR, 1e-4f);
    }
}

void test_rr_menolak_beat_awal(void)
{
    float rr[3];
    TEST_ASSERT_FALSE(ecg_rr_features(golden_r, GOLDEN_N_BEAT, 0, ECG_FS, rr));
    TEST_ASSERT_FALSE(ecg_rr_features(golden_r, GOLDEN_N_BEAT, 1, ECG_FS, rr));
}

void test_pipeline_utuh(void)
{
    float state[ECG_N_SOS * 2];
    memset(state, 0, sizeof(state));
    ecg_bandpass(golden_raw, buf_filtered, GOLDEN_N, state);

    for (int b = 0; b < GOLDEN_N_BEAT; b++) {
        TEST_ASSERT_TRUE(ecg_window_zscore(buf_filtered, GOLDEN_N, golden_r[b], buf_window));
        bandingkan("pipeline utuh", buf_window,
                   golden_window + (size_t)b * GOLDEN_WIN_LEN,
                   GOLDEN_WIN_LEN, GOLDEN_TOL_ZSCORE);
    }
}

static float buf_scratch[GOLDEN_N];
static int buf_r[64];

void test_detect_r(void)
{
    const int n = ecg_detect_r(golden_filtered, GOLDEN_N, buf_scratch, buf_r, 64);
    char pesan[96];
    snprintf(pesan, sizeof(pesan), "dapat %d R-peak, harus %d", n, GOLDEN_N_DETEKSI);
    TEST_ASSERT_EQUAL_MESSAGE(GOLDEN_N_DETEKSI, n, pesan);
    for (int i = 0; i < n; i++) {
        snprintf(pesan, sizeof(pesan), "peak %d: dapat %d, harus %d",
                 i, buf_r[i], golden_r_deteksi[i]);
        TEST_ASSERT_INT_WITHIN_MESSAGE(1, golden_r_deteksi[i], buf_r[i], pesan);
    }
}

#define R_IDX (ECG_WIN_PRE + ECG_GROUP_DELAY)

void test_align_r_menaruh_puncak_di_r_idx(void)
{
    const int n = ecg_detect_r(golden_filtered, GOLDEN_N, buf_scratch, buf_r, 64);
    int diuji = 0;
    for (int i = 0; i < n; i++) {
        const int r = ecg_align_r(golden_filtered, GOLDEN_N, buf_r[i]);
        if (r - ECG_WIN_PRE < 0 || r + ECG_WIN_POST > GOLDEN_N) continue;
        TEST_ASSERT_TRUE(ecg_window_zscore(golden_filtered, GOLDEN_N, r, buf_window));
        int puncak = R_IDX - 20;
        for (int k = R_IDX - 20; k <= R_IDX + 20; k++)
            if (buf_window[k] > buf_window[puncak]) puncak = k;
        char pesan[96];
        snprintf(pesan, sizeof(pesan), "beat %d: puncak di %d, harus %d", i, puncak, R_IDX);
        TEST_ASSERT_INT_WITHIN_MESSAGE(2, R_IDX, puncak, pesan);
        diuji++;
    }
    TEST_ASSERT_GREATER_THAN_MESSAGE(3, diuji, "terlalu sedikit beat teruji");
}

static ecg_beat_t beat;

void test_live_mengeluarkan_beat(void)
{
    ecg_live_reset();
    int keluar = 0, cocok = 0, puncak_benar = 0;

    for (int i = 0; i < GOLDEN_N; i++) {
        if (!ecg_live_push(golden_raw[i], &beat)) continue;
        keluar++;

        int puncak = R_IDX - 20;
        for (int k = R_IDX - 20; k <= R_IDX + 20; k++)
            if (beat.window[k] > beat.window[puncak]) puncak = k;
        if (abs(puncak - R_IDX) <= 2) puncak_benar++;

        for (int b = 0; b < GOLDEN_N_BEAT; b++)
            if (abs(beat.r_abs - golden_r[b]) <= 20) { cocok++; break; }
    }

    char pesan[128];
    snprintf(pesan, sizeof(pesan), "%d beat keluar, %d cocok anotasi, %d puncak di R_IDX",
             keluar, cocok, puncak_benar);
    TEST_ASSERT_GREATER_THAN_MESSAGE(3, keluar, pesan);
    TEST_ASSERT_GREATER_THAN_MESSAGE(3, cocok, pesan);
    TEST_ASSERT_EQUAL_MESSAGE(keluar, puncak_benar, pesan);
    TEST_ASSERT_EQUAL_INT(keluar, ecg_live_total_beat());
}

void test_live_membuang_dua_beat_pertama(void)
{
    ecg_live_reset();
    int keluar = 0;
    for (int i = 0; i < GOLDEN_N; i++) {
        if (ecg_live_push(golden_raw[i], &beat)) {
            keluar++;
            TEST_ASSERT_TRUE_MESSAGE(beat.rr[0] > 0.15f && beat.rr[0] < 3.0f,
                                     "RR_prev di luar rentang fisiologis");
        }
    }
    TEST_ASSERT_TRUE(keluar < GOLDEN_N_DETEKSI);
}

static void jalankan(void)
{
    UNITY_BEGIN();
    RUN_TEST(test_bandpass);
    RUN_TEST(test_bandpass_streaming);
    RUN_TEST(test_window_zscore);
    RUN_TEST(test_zscore_sifat);
    RUN_TEST(test_rr_features);
    RUN_TEST(test_rr_menolak_beat_awal);
    RUN_TEST(test_pipeline_utuh);
    RUN_TEST(test_detect_r);
    RUN_TEST(test_align_r_menaruh_puncak_di_r_idx);
    RUN_TEST(test_live_mengeluarkan_beat);
    RUN_TEST(test_live_membuang_dua_beat_pertama);
    UNITY_END();
}

#ifdef ARDUINO
#include <Arduino.h>
void setup() { Serial.begin(115200); delay(2000); jalankan(); }
void loop() {}
#else
int main(int argc, char **argv) { (void)argc; (void)argv; jalankan(); return 0; }
#endif
