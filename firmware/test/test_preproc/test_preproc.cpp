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

static void compare(const char *stage, const float *got, const float *expected,
                       size_t n, float tol)
{
    size_t i_worst = 0;
    float worst = 0.0f;
    for (size_t i = 0; i < n; i++) {
        float d = fabsf(got[i] - expected[i]);
        if (d > worst) { worst = d; i_worst = i; }
    }
    if (worst > tol) {
        char message[192];
        snprintf(message, sizeof(message),
                 "%s: largest difference %.6g at index %zu (got %.6g, expected %.6g)",
                 stage, (double)worst, i_worst,
                 (double)got[i_worst], (double)expected[i_worst]);
        TEST_FAIL_MESSAGE(message);
    }
}

void test_bandpass(void)
{
    float state[ECG_N_SOS * 2];
    memset(state, 0, sizeof(state));
    ecg_bandpass(golden_raw, buf_filtered, GOLDEN_N, state);
    compare("bandpass", buf_filtered, golden_filtered, GOLDEN_N, GOLDEN_TOL_FILTER);
}

void test_bandpass_streaming(void)
{
    float state[ECG_N_SOS * 2];
    memset(state, 0, sizeof(state));
    const size_t block = 64;
    for (size_t i = 0; i < GOLDEN_N; i += block) {
        size_t n = (i + block <= GOLDEN_N) ? block : (GOLDEN_N - i);
        ecg_bandpass(golden_raw + i, buf_filtered + i, n, state);
    }
    compare("bandpass streaming", buf_filtered, golden_filtered,
               GOLDEN_N, GOLDEN_TOL_FILTER);
}

void test_window_zscore(void)
{
    for (int b = 0; b < GOLDEN_N_BEAT; b++) {
        TEST_ASSERT_TRUE_MESSAGE(
            ecg_window_zscore(golden_filtered, GOLDEN_N, golden_r[b], buf_window),
            "window should fit in the signal");
        compare("z-score", buf_window, golden_window + (size_t)b * GOLDEN_WIN_LEN,
                   GOLDEN_WIN_LEN, GOLDEN_TOL_ZSCORE);
    }
}

void test_zscore_properties(void)
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
            "rr_features should succeed for i >= 2");
        compare("rr", rr, golden_rr + (size_t)b * GOLDEN_N_RR,
                   GOLDEN_N_RR, 1e-4f);
    }
}

void test_rr_rejects_early_beat(void)
{
    float rr[3];
    TEST_ASSERT_FALSE(ecg_rr_features(golden_r, GOLDEN_N_BEAT, 0, ECG_FS, rr));
    TEST_ASSERT_FALSE(ecg_rr_features(golden_r, GOLDEN_N_BEAT, 1, ECG_FS, rr));
}

void test_pipeline_whole(void)
{
    float state[ECG_N_SOS * 2];
    memset(state, 0, sizeof(state));
    ecg_bandpass(golden_raw, buf_filtered, GOLDEN_N, state);

    for (int b = 0; b < GOLDEN_N_BEAT; b++) {
        TEST_ASSERT_TRUE(ecg_window_zscore(buf_filtered, GOLDEN_N, golden_r[b], buf_window));
        compare("pipeline utuh", buf_window,
                   golden_window + (size_t)b * GOLDEN_WIN_LEN,
                   GOLDEN_WIN_LEN, GOLDEN_TOL_ZSCORE);
    }
}

static float buf_scratch[GOLDEN_N];
static int buf_r[64];

void test_detect_r(void)
{
    const int n = ecg_detect_r(golden_filtered, GOLDEN_N, buf_scratch, buf_r, 64);
    char message[96];
    snprintf(message, sizeof(message), "got %d R-peaks, expected %d", n, GOLDEN_N_DETECTION);
    TEST_ASSERT_EQUAL_MESSAGE(GOLDEN_N_DETECTION, n, message);
    for (int i = 0; i < n; i++) {
        snprintf(message, sizeof(message), "peak %d: got %d, expected %d",
                 i, buf_r[i], golden_r_detection[i]);
        TEST_ASSERT_INT_WITHIN_MESSAGE(1, golden_r_detection[i], buf_r[i], message);
    }
}

#define R_IDX (ECG_WIN_PRE + ECG_GROUP_DELAY)

void test_align_r_puts_peak_at_r_idx(void)
{
    const int n = ecg_detect_r(golden_filtered, GOLDEN_N, buf_scratch, buf_r, 64);
    int tested = 0;
    for (int i = 0; i < n; i++) {
        const int r = ecg_align_r(golden_filtered, GOLDEN_N, buf_r[i]);
        if (r - ECG_WIN_PRE < 0 || r + ECG_WIN_POST > GOLDEN_N) continue;
        TEST_ASSERT_TRUE(ecg_window_zscore(golden_filtered, GOLDEN_N, r, buf_window));
        int peak = R_IDX - 20;
        for (int k = R_IDX - 20; k <= R_IDX + 20; k++)
            if (buf_window[k] > buf_window[peak]) peak = k;
        char message[96];
        snprintf(message, sizeof(message), "beat %d: peak at %d, expected %d", i, peak, R_IDX);
        TEST_ASSERT_INT_WITHIN_MESSAGE(2, R_IDX, peak, message);
        tested++;
    }
    TEST_ASSERT_GREATER_THAN_MESSAGE(3, tested, "too few beats tested");
}

static ecg_beat_t beat;

void test_live_emits_beat(void)
{
    ecg_live_reset();
    int emitted = 0, matched = 0, peak_correct = 0;

    for (int i = 0; i < GOLDEN_N; i++) {
        if (!ecg_live_push(golden_raw[i], &beat)) continue;
        emitted++;

        int peak = R_IDX - 20;
        for (int k = R_IDX - 20; k <= R_IDX + 20; k++)
            if (beat.window[k] > beat.window[peak]) peak = k;
        if (abs(peak - R_IDX) <= 2) peak_correct++;

        for (int b = 0; b < GOLDEN_N_BEAT; b++)
            if (abs(beat.r_abs - golden_r[b]) <= 20) { matched++; break; }
    }

    char message[128];
    snprintf(message, sizeof(message), "%d beats out, %d match annotations, %d peaks at R_IDX",
             emitted, matched, peak_correct);
    TEST_ASSERT_GREATER_THAN_MESSAGE(3, emitted, message);
    TEST_ASSERT_GREATER_THAN_MESSAGE(3, matched, message);
    TEST_ASSERT_EQUAL_MESSAGE(emitted, peak_correct, message);
    TEST_ASSERT_EQUAL_INT(emitted, ecg_live_total_beat());
}

void test_live_drops_first_two_beats(void)
{
    ecg_live_reset();
    int emitted = 0;
    for (int i = 0; i < GOLDEN_N; i++) {
        if (ecg_live_push(golden_raw[i], &beat)) {
            emitted++;
            TEST_ASSERT_TRUE_MESSAGE(beat.rr[0] > 0.15f && beat.rr[0] < 3.0f,
                                     "RR_prev di luar rentang fisiologis");
        }
    }
    TEST_ASSERT_TRUE(emitted < GOLDEN_N_DETECTION);
}

static void run_all(void)
{
    UNITY_BEGIN();
    RUN_TEST(test_bandpass);
    RUN_TEST(test_bandpass_streaming);
    RUN_TEST(test_window_zscore);
    RUN_TEST(test_zscore_properties);
    RUN_TEST(test_rr_features);
    RUN_TEST(test_rr_rejects_early_beat);
    RUN_TEST(test_pipeline_whole);
    RUN_TEST(test_detect_r);
    RUN_TEST(test_align_r_puts_peak_at_r_idx);
    RUN_TEST(test_live_emits_beat);
    RUN_TEST(test_live_drops_first_two_beats);
    UNITY_END();
}

#ifdef ARDUINO
#include <Arduino.h>
void setup() { Serial.begin(115200); delay(2000); run_all(); }
void loop() {}
#else
int main(int argc, char **argv) { (void)argc; (void)argv; run_all(); return 0; }
#endif
