#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "classifier.h"

#include <Arduino.h>

#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"
#if __has_include("tensorflow/lite/micro/micro_error_reporter.h")
#include "tensorflow/lite/micro/micro_error_reporter.h"
#define TFLM_HAS_ERROR_REPORTER 1
#endif

#include "ecg_mqtt.h"
#include "gate.h"
#include "model_int8.h"
#include "display.h"

constexpr int ARENA_N = 24 * 1024;
alignas(16) static uint8_t arena[ARENA_N];
static tflite::MicroInterpreter *interp;
static TfLiteTensor *in_morph, *in_rr, *output;

static classifier_count_t h;

const classifier_count_t &classifier_count(void) { return h; }
void classifier_reset(void) { h = classifier_count_t{}; }
size_t classifier_arena(void) { return interp->arena_used_bytes(); }
float classifier_threshold(void) { return ECG_THRESHOLD; }

void classifier_begin(void)
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
    if (interp->AllocateTensors() != kTfLiteOk) {
        Serial.println("FATAL: AllocateTensors gagal");
        while (true) { display_led(64, 0, 0); delay(200); display_led(0, 0, 0); delay(200); }
    }
    TfLiteTensor *a = interp->input(0), *b = interp->input(1);
    const bool a_small = a->bytes < b->bytes;
    in_rr = a_small ? a : b;
    in_morph = a_small ? b : a;
    output = interp->output(0);
}

static int8_t to_int8(float x, float scale, int zero)
{
    long q = lroundf(x / scale) + zero;
    if (q < -128) q = -128;
    if (q > 127) q = 127;
    return (int8_t)q;
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

static void publish(const ecg_beat_t &beat, float p, bool arrhythmia)
{
    if (!ecg_mqtt_aktif()) return;
    if (gate_phase() != PHASE_GOOD) { h.withheld++; return; }
    if (beat.sinyal_hilang) { h.withheld++; return; }

    ecg_mqtt_beat_t t;
    t.ms = gate_t_session_ms() + (uint32_t)((uint64_t)beat.r_abs * 1000ULL / ECG_FS);
    t.rr_ms = beat.rr[0] * 1000.0f;
    t.bpm = (beat.rr[0] > 0.05f) ? 60.0f / beat.rr[0] : 0.0f;
    t.label = arrhythmia ? 1 : 0;
    t.confidence = arrhythmia ? p : 1.0f - p;
    t.quality_ok = 1;
    for (int i = 0; i < ECG_SNIPPET_N; i++) {
        const int j = i * (ECG_WIN_LEN_ - 1) / (ECG_SNIPPET_N - 1);
        t.snippet[i] = (int16_t)(beat.window[j] * 1000.0f);
    }
    const uint32_t latency = millis() - t.ms;
    h.latency_sum += latency; h.latency_n++;
    if (latency > h.latency_max) h.latency_max = latency;

    ecg_mqtt_antre_isi(&t);
}

bool classifier_process(const ecg_beat_t &beat)
{
    const float p = classifier(beat);
    const bool arrhythmia = p >= ECG_THRESHOLD;
    h.total++;
    if (arrhythmia) h.arrhythmia++;
    const float bpm = (beat.rr[0] > 0.05f) ? 60.0f / beat.rr[0] : 0.0f;
    Serial.printf("beat %4d  p=%.4f  %-7s  RR=%.3fs  %3.0f bpm\n",
                  h.total, p, arrhythmia ? "ARITMIA" : "normal", beat.rr[0], bpm);
    publish(beat, p, arrhythmia);
    return arrhythmia;
}
#endif
