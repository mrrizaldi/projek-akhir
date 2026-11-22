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
#include "ecg_live.h"
#include "ina219.h"
#include "board.h"
#include "../golden_ref.h"

constexpr int ROUNDS = 3;
constexpr int ARENA_N = 24 * 1024;
alignas(16) static uint8_t arena[ARENA_N];
static tflite::MicroInterpreter *interp;
static TfLiteTensor *in_morph, *in_rr, *output;

constexpr size_t QUEUE_N = 256;
static volatile uint16_t queue[QUEUE_N];
static volatile size_t write_index, read_index, replay_i;
static volatile uint32_t n_missed;
static uint16_t sim_counts[GOLDEN_N];

static void IRAM_ATTR on_timer()
{
    const size_t next = (write_index + 1) % QUEUE_N;
    if (next == read_index) { n_missed++; return; }
    queue[write_index] = sim_counts[replay_i];
    replay_i = (replay_i + 1) % GOLDEN_N;
    write_index = next;
}

static int beat_emitted, matched, prediction_correct, hr_off;
static uint32_t n_processed, loop_max_us;

void test_model_loaded(void)
{
    const tflite::Model *m = tflite::GetModel(model_int8_tflite);
    static tflite::MicroMutableOpResolver<8> res;
    res.AddConv2D(); res.AddDepthwiseConv2D(); res.AddMaxPool2D();
    res.AddConcatenation(); res.AddLogistic(); res.AddAdd();
    res.AddReshape(); res.AddExpandDims();
#ifdef TFLM_HAS_ERROR_REPORTER
    static tflite::MicroErrorReporter reporter;
    static tflite::MicroInterpreter it(m, res, arena, ARENA_N, &reporter);
#else
    static tflite::MicroInterpreter it(m, res, arena, ARENA_N);
#endif
    interp = &it;
    TEST_ASSERT_EQUAL(kTfLiteOk, interp->AllocateTensors());
    TfLiteTensor *a = interp->input(0), *b = interp->input(1);
    in_rr = a->bytes < b->bytes ? a : b;
    in_morph = a->bytes < b->bytes ? b : a;
    output = interp->output(0);
}

static int8_t to_int8(float x, float scale, int zero)
{
    long q = lroundf(x / scale) + zero;
    return (int8_t)constrain(q, -128L, 127L);
}

static float classifier(const ecg_beat_t &beat)
{
    for (int i = 0; i < ECG_WIN_LEN_; i++)
        in_morph->data.int8[i] = to_int8(beat.window[i], ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO);
    for (int i = 0; i < ECG_N_RR; i++)
        in_rr->data.int8[i] = to_int8(beat.rr[i], ECG_IN_RR_SCALE, ECG_IN_RR_ZERO);
    interp->Invoke();
    return (output->data.int8[0] - ECG_OUT_ZERO) * ECG_OUT_SCALE;
}

static void plot(float f)
{
    static int n, x;
    if (++n < 3) return;
    n = 0;
    const int y = constrain(86 - (int)(f * 0.03f), 30, 141);
    tft.fillRect(x, 30, min(4, TFT_W - x), 112, ST77XX_BLACK);
    tft.drawPixel(x, y, ST77XX_GREEN);
    x = (x + 1) % TFT_W;
}

static void screen_hr(int hr, bool arrhythmia)
{
    float mA, V;
    const bool ina = ina219_read(R_SHUNT, &mA, &V);
    tft.setTextSize(3);
    tft.setTextColor(arrhythmia ? ST77XX_RED : ST77XX_WHITE, ST77XX_BLACK);
    tft.setCursor(4, 3);
    tft.printf("HR %3d", hr);
    tft.setTextSize(2);
    tft.setTextColor(ST77XX_CYAN, ST77XX_BLACK);
    tft.setCursor(200, 8);
    if (ina) tft.printf("%4.0fmA", mA);
    else     tft.print("INA -- ");
}

void test_run_replay_without_lost_samples(void)
{
    static ecg_beat_t beat;
    int hr = 0;
    bool arrhythmia = false;
    uint32_t t_screen = 0, buzz_until = 0;

    hw_timer_t *timer = timerBegin(0, 80, true);
    timerAttachInterrupt(timer, &on_timer, true);
    timerAlarmWrite(timer, 1000000 / ECG_FS, true);
    timerAlarmEnable(timer);

    while (n_processed < (uint32_t)ROUNDS * GOLDEN_N) {
        const uint32_t t0 = micros();
        if (read_index != write_index) {
            const float s = queue[read_index];
            read_index = (read_index + 1) % QUEUE_N;
            n_processed++;
            if (ecg_live_push(s, &beat)) {
                beat_emitted++;
                const float p = classifier(beat);
                arrhythmia = p >= ECG_THRESHOLD;
                hr = (int)lroundf(60.0f / beat.rr[0]);
                buzzer(true);
                buzz_until = millis() + (arrhythmia ? 250 : 50);
                for (int b = GOLDEN_RR_FIRST; b < GOLDEN_N_BEAT && beat.r_abs < GOLDEN_N; b++) {
                    if (abs(beat.r_abs - golden_r[b]) > 20) continue;
                    matched++;
                    const int hr_pc = (int)lroundf(60.0f * ECG_FS / (golden_r[b] - golden_r[b - 1]));
                    if (abs(hr - hr_pc) > 3) hr_off++;
                    if ((arrhythmia ? 1 : 0) == golden_label[b]) prediction_correct++;
                    Serial.printf("  r=%4d (%s) HR %3d (PC %3d) p=%.4f -> %d, PC %d\n",
                                  beat.r_abs, golden_sym[b], hr, hr_pc, p, (int)arrhythmia, golden_label[b]);
                    break;
                }
            }
            plot(ecg_live_filtered_last());
        }
        if (millis() - t_screen >= 1000) { t_screen = millis(); screen_hr(hr, arrhythmia); }
        if (buzz_until && (int32_t)(millis() - buzz_until) >= 0) { buzzer(false); buzz_until = 0; }
        loop_max_us = max(loop_max_us, (uint32_t)(micros() - t0));
    }
    timerAlarmDisable(timer);
    timerEnd(timer);
    buzzer(false);

    Serial.printf("diproses %u sampel, beat %d, cocok %d, benar %d, HR meleset %d, "
                  "sampel hilang %u, loop terlama %u us\n",
                  (unsigned)n_processed, beat_emitted, matched, prediction_correct, hr_off,
                  (unsigned)n_missed, (unsigned)loop_max_us);
    TEST_ASSERT_EQUAL_UINT32_MESSAGE(0, n_missed, "antrean ISR penuh: loop (TFT/inferensi) terlalu lama");
}

void test_beat_detected_each_round(void)
{
    TEST_ASSERT_GREATER_OR_EQUAL(ROUNDS * GOLDEN_N_BEAT - 4, beat_emitted);
}

void test_hr_equals_annotation(void)
{
    TEST_ASSERT_GREATER_THAN_MESSAGE(3, matched, "terlalu sedikit beat cocok anotasi");
    TEST_ASSERT_EQUAL_MESSAGE(0, hr_off, "HR beda > 3 bpm dari RR anotasi");
}

void test_prediction_equals_pc(void)
{
    TEST_ASSERT_EQUAL_MESSAGE(matched, prediction_correct, "label alat beda dari label PC");
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    board_begin();
    Serial.begin(115200);
    delay(2000);
    ina219_begin(I2C_SDA, I2C_SCL);
    for (size_t i = 0; i < GOLDEN_N; i++)
        sim_counts[i] = (uint16_t)constrain(golden_raw[i] * 1000.0f + 2048.0f, 0.0f, 4095.0f);
    ecg_live_reset();

    UNITY_BEGIN();
    RUN_TEST(test_model_loaded);
    RUN_TEST(test_run_replay_without_lost_samples);
    RUN_TEST(test_beat_detected_each_round);
    RUN_TEST(test_hr_equals_annotation);
    RUN_TEST(test_prediction_equals_pc);
    UNITY_END();
}

void loop() {}
