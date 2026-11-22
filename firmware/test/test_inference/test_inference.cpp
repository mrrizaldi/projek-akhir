#include <Arduino.h>
#include <unity.h>

#include "tensorflow/lite/micro/micro_interpreter.h"
#if __has_include("tensorflow/lite/micro/micro_error_reporter.h")
#include "tensorflow/lite/micro/micro_error_reporter.h"
#define TFLM_HAS_ERROR_REPORTER 1
#endif
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "model_int8.h"
#include "ecg_pipeline.h"
#include "ecg_live.h"
#include "../golden_ref.h"

constexpr int kArenaSize = 24 * 1024;
constexpr uint32_t WAIT_USB_CDC_MS = 2000;
alignas(16) static uint8_t tensor_arena[kArenaSize];

static tflite::MicroInterpreter *interpreter = nullptr;
static TfLiteTensor *in_morph = nullptr;
static TfLiteTensor *in_rr = nullptr;
static TfLiteTensor *out = nullptr;

static float buf_filtered[GOLDEN_N];
static float buf_window[GOLDEN_WIN_LEN];
static uint32_t us_used[GOLDEN_N_BEAT];

static void prepare_model(void)
{
    const tflite::Model *model = tflite::GetModel(model_int8_tflite);
    TEST_ASSERT_EQUAL_MESSAGE(TFLITE_SCHEMA_VERSION, model->version(),
                              "skema flatbuffer model != versi library");

    static tflite::MicroMutableOpResolver<8> resolver;
    resolver.AddConv2D();
    resolver.AddDepthwiseConv2D();
    resolver.AddMaxPool2D();
    resolver.AddConcatenation();
    resolver.AddLogistic();
    resolver.AddAdd();
    resolver.AddReshape();
    resolver.AddExpandDims();

#ifdef TFLM_HAS_ERROR_REPORTER
    static tflite::MicroErrorReporter reporter;
    static tflite::MicroInterpreter static_interpreter(model, resolver, tensor_arena, kArenaSize, &reporter);
#else
    static tflite::MicroInterpreter static_interpreter(model, resolver, tensor_arena, kArenaSize);
#endif
    interpreter = &static_interpreter;
    TEST_ASSERT_EQUAL_MESSAGE(kTfLiteOk, interpreter->AllocateTensors(),
                              "AllocateTensors failed: arena too small?");

    TfLiteTensor *a = interpreter->input(0);
    TfLiteTensor *b = interpreter->input(1);
    const bool a_small = a->bytes < b->bytes;
    in_rr = a_small ? a : b;
    in_morph = a_small ? b : a;
    out = interpreter->output(0);
}

static int8_t to_int8(float x, float scale, int zero)
{
    long q = lroundf(x / scale) + zero;
    if (q < -128) q = -128;
    if (q > 127) q = 127;
    return (int8_t)q;
}

void test_model_loaded(void)
{
    prepare_model();
    TEST_ASSERT_EQUAL(kTfLiteInt8, in_morph->type);
    TEST_ASSERT_EQUAL(kTfLiteInt8, in_rr->type);
    TEST_ASSERT_EQUAL(kTfLiteInt8, out->type);
    TEST_ASSERT_EQUAL(GOLDEN_WIN_LEN, (int)in_morph->bytes);
    TEST_ASSERT_EQUAL(GOLDEN_N_RR, (int)in_rr->bytes);
}

void test_inference_matches_pc(void)
{
    float state[ECG_N_SOS * 2];
    memset(state, 0, sizeof(state));
    ecg_bandpass(golden_raw, buf_filtered, GOLDEN_N, state);

    for (int b = GOLDEN_RR_FIRST; b < GOLDEN_N_BEAT; b++) {
        TEST_ASSERT_TRUE(ecg_window_zscore(buf_filtered, GOLDEN_N, golden_r[b], buf_window));

        float rr[3];
        TEST_ASSERT_TRUE(ecg_rr_features(golden_r, GOLDEN_N_BEAT, b, ECG_FS, rr));

        for (int i = 0; i < GOLDEN_WIN_LEN; i++) {
            in_morph->data.int8[i] = to_int8(buf_window[i], ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO);
        }
        for (int i = 0; i < GOLDEN_N_RR; i++) {
            in_rr->data.int8[i] = to_int8(rr[i], ECG_IN_RR_SCALE, ECG_IN_RR_ZERO);
        }

        const uint32_t t0 = micros();
        TEST_ASSERT_EQUAL(kTfLiteOk, interpreter->Invoke());
        us_used[b] = micros() - t0;

        const float p = (out->data.int8[0] - ECG_OUT_ZERO) * ECG_OUT_SCALE;

        char message[128];
        snprintf(message, sizeof(message), "beat %d (%s): device %.4f vs PC %.4f",
                 b, golden_sym[b], p, golden_prob_int8[b]);
        TEST_ASSERT_FLOAT_WITHIN_MESSAGE(GOLDEN_TOL_PROB, golden_prob_int8[b], p, message);

        TEST_ASSERT_EQUAL_MESSAGE(golden_label[b], p >= GOLDEN_THRESHOLD ? 1 : 0, message);
    }
}

void test_diagnostic_golden_input(void)
{
    for (int b = GOLDEN_RR_FIRST; b < GOLDEN_N_BEAT; b++) {
        const float *w = golden_window + (size_t)b * GOLDEN_WIN_LEN;
        const float *rr = golden_rr + (size_t)b * GOLDEN_N_RR;
        for (int i = 0; i < GOLDEN_WIN_LEN; i++)
            in_morph->data.int8[i] = to_int8(w[i], ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO);
        for (int i = 0; i < GOLDEN_N_RR; i++)
            in_rr->data.int8[i] = to_int8(rr[i], ECG_IN_RR_SCALE, ECG_IN_RR_ZERO);
        interpreter->Invoke();
        const float p = (out->data.int8[0] - ECG_OUT_ZERO) * ECG_OUT_SCALE;
        Serial.printf("DIAG beat %d (%s): golden-in %.4f | PC %.4f\n",
                      b, golden_sym[b], p, golden_prob_int8[b]);
    }
    Serial.printf("DIAG tensor: morph dims=%d [%d,%d,%d] scale=%.8f zero=%d\n",
                  in_morph->dims->size, in_morph->dims->data[0],
                  in_morph->dims->data[1], in_morph->dims->size > 2 ? in_morph->dims->data[2] : -1,
                  in_morph->params.scale, in_morph->params.zero_point);
    Serial.printf("DIAG tensor: rr    dims=%d [%d,%d] scale=%.8f zero=%d\n",
                  in_rr->dims->size, in_rr->dims->data[0], in_rr->dims->data[1],
                  in_rr->params.scale, in_rr->params.zero_point);
    Serial.printf("DIAG header : morph scale=%.8f zero=%d | rr scale=%.8f zero=%d\n",
                  ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO, ECG_IN_RR_SCALE, ECG_IN_RR_ZERO);
    Serial.printf("DIAG out    : scale=%.8f zero=%d | header %.8f %d\n",
                  out->params.scale, out->params.zero_point, ECG_OUT_SCALE, ECG_OUT_ZERO);

    for (int i = 0; i < GOLDEN_WIN_LEN; i++) in_morph->data.int8[i] = ECG_IN_MORPH_ZERO;
    for (int i = 0; i < GOLDEN_N_RR; i++)    in_rr->data.int8[i] = ECG_IN_RR_ZERO;
    interpreter->Invoke();
    Serial.printf("DIAG zero   : q_out=%d  p=%.6f\n",
                  (int)out->data.int8[0],
                  (out->data.int8[0] - ECG_OUT_ZERO) * ECG_OUT_SCALE);

    const float *w2 = golden_window + (size_t)2 * GOLDEN_WIN_LEN;
    const float *r2 = golden_rr + (size_t)2 * GOLDEN_N_RR;
    for (int i = 0; i < GOLDEN_WIN_LEN; i++)
        in_morph->data.int8[i] = to_int8(w2[i], ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO);
    for (int i = 0; i < GOLDEN_N_RR; i++)
        in_rr->data.int8[i] = to_int8(r2[i], ECG_IN_RR_SCALE, ECG_IN_RR_ZERO);
    interpreter->Invoke();
    Serial.printf("DIAG beat2  : q_out=%d  morph[0..4]=%d,%d,%d,%d,%d  rr=%d,%d,%d\n",
                  (int)out->data.int8[0],
                  in_morph->data.int8[0], in_morph->data.int8[1], in_morph->data.int8[2],
                  in_morph->data.int8[3], in_morph->data.int8[4],
                  in_rr->data.int8[0], in_rr->data.int8[1], in_rr->data.int8[2]);
}

void test_lifecycle(void)
{
    static ecg_beat_t beat;
    ecg_live_reset();
    int emitted = 0, matched = 0, correct = 0;
    uint32_t us_max = 0;
    const uint32_t t_begin = micros();

    for (int i = 0; i < GOLDEN_N; i++) {
        const uint32_t t0 = micros();
        const int beat_ready = ecg_live_push(golden_raw[i], &beat);
        uint32_t dt = micros() - t0;
        if (!beat_ready) { if (dt > us_max) us_max = dt; continue; }
        (void)dt;

        for (int k = 0; k < GOLDEN_WIN_LEN; k++)
            in_morph->data.int8[k] = to_int8(beat.window[k], ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO);
        for (int k = 0; k < GOLDEN_N_RR; k++)
            in_rr->data.int8[k] = to_int8(beat.rr[k], ECG_IN_RR_SCALE, ECG_IN_RR_ZERO);
        TEST_ASSERT_EQUAL(kTfLiteOk, interpreter->Invoke());
        const float p = (out->data.int8[0] - ECG_OUT_ZERO) * ECG_OUT_SCALE;
        const int prediction = (p >= GOLDEN_THRESHOLD) ? 1 : 0;

        dt = micros() - t0;
        if (dt > us_max) us_max = dt;
        emitted++;

        for (int b = 0; b < GOLDEN_N_BEAT; b++) {
            if (abs(beat.r_abs - golden_r[b]) <= 20) {
                matched++;
                if (prediction == golden_label[b]) correct++;
                Serial.printf("  beat r=%4d (%s) p=%.4f -> %d, expected %d %s\n",
                              beat.r_abs, golden_sym[b], p, prediction, golden_label[b],
                              prediction == golden_label[b] ? "OK" : "WRONG");
                break;
            }
        }
    }

    const uint32_t us_run = micros() - t_begin;
    const uint32_t us_mean = us_run / GOLDEN_N;
    const float load = 100.0f * us_mean / 2778.0f;
    const uint32_t backlog = (us_max + 2777) / 2778;

    Serial.printf("\n=== LIVE FLOW ===\n");
    Serial.printf("beats out     : %d (%d match annotations, %d predictions correct)\n",
                  emitted, matched, correct);
    Serial.printf("total         : %lu us for %d samples (%.1f s of signal)\n",
                  (unsigned long)us_run, GOLDEN_N, (float)GOLDEN_N / ECG_FS);
    Serial.printf("average       : %lu us/sample of a 2778 us budget -> load %.1f%%\n",
                  (unsigned long)us_mean, load);
    Serial.printf("burst peak    : %lu us (4 s detection + inference together)\n",
                  (unsigned long)us_max);
    Serial.printf("queue min     : %lu samples so a burst leaves no gap\n",
                  (unsigned long)backlog);
    Serial.printf("==================\n");

    TEST_ASSERT_GREATER_THAN_MESSAGE(3, matched, "too few beats match the annotations");
    TEST_ASSERT_EQUAL_MESSAGE(matched, correct, "a prediction differs from the PC answer");

    TEST_ASSERT_LESS_THAN_UINT32_MESSAGE(2778, us_mean,
        "average > 2778 us/sample: real time at 360 Hz is impossible");
    TEST_ASSERT_LESS_THAN_UINT32_MESSAGE(ECG_LIVE_RING, backlog * 4,
        "burst too long for the 4 s ring");
}

void test_latency_and_memory(void)
{
    uint32_t total = 0, max_us = 0;
    for (int b = GOLDEN_RR_FIRST; b < GOLDEN_N_BEAT; b++) {
        total += us_used[b];
        if (us_used[b] > max_us) max_us = us_used[b];
    }
    const int n = GOLDEN_N_BEAT - GOLDEN_RR_FIRST;
    const size_t arena = interpreter->arena_used_bytes();

    Serial.printf("\n=== BENCHMARK ESP32-S3 ===\n");
    Serial.printf("inference     : %lu us average, %lu us maximum (%d beats)\n",
                  (unsigned long)(total / n), (unsigned long)max_us, n);
    Serial.printf("tensor arena  : %u bytes used of %d bytes allocated\n",
                  (unsigned)arena, kArenaSize);
    Serial.printf("free heap     : %u bytes\n", (unsigned)ESP.getFreeHeap());
    Serial.printf("CPU           : %u MHz\n", (unsigned)ESP.getCpuFreqMHz());
    Serial.printf("==========================\n");

    TEST_ASSERT_LESS_THAN_UINT32_MESSAGE(200000, max_us,
        "inference > 200 ms: too slow for continuous use, consider ESP-NN");
    TEST_ASSERT_LESS_OR_EQUAL_MESSAGE(kArenaSize, arena, "arena too small");
}

void setup()
{
    Serial.begin(115200);
    delay(WAIT_USB_CDC_MS);
    UNITY_BEGIN();
    RUN_TEST(test_model_loaded);
    RUN_TEST(test_diagnostic_golden_input);
    RUN_TEST(test_inference_matches_pc);
    RUN_TEST(test_latency_and_memory);
    RUN_TEST(test_lifecycle);
    UNITY_END();
}

void loop() {}
