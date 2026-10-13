#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "klasifikasi.h"

#include <Arduino.h>

#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"
#if __has_include("tensorflow/lite/micro/micro_error_reporter.h")
#include "tensorflow/lite/micro/micro_error_reporter.h"
#define TFLM_PUNYA_ERROR_REPORTER 1
#endif

#include "ecg_mqtt.h"
#include "gerbang.h"
#include "model_int8.h"
#include "tampilan.h"

constexpr int ARENA_N = 24 * 1024;
alignas(16) static uint8_t arena[ARENA_N];
static tflite::MicroInterpreter *interp;
static TfLiteTensor *in_morph, *in_rr, *keluar;

static klasifikasi_hitung_t h;

const klasifikasi_hitung_t &klasifikasi_hitung(void) { return h; }
void klasifikasi_reset(void) { h = klasifikasi_hitung_t{}; }
size_t klasifikasi_arena(void) { return interp->arena_used_bytes(); }
float klasifikasi_ambang(void) { return ECG_THRESHOLD; }

void klasifikasi_mulai(void)
{
    const tflite::Model *m = tflite::GetModel(model_int8_tflite);
    static tflite::MicroMutableOpResolver<8> res;
    res.AddConv2D(); res.AddDepthwiseConv2D(); res.AddMaxPool2D();
    res.AddConcatenation(); res.AddLogistic(); res.AddAdd();
    res.AddReshape(); res.AddExpandDims();
#ifdef TFLM_PUNYA_ERROR_REPORTER
    static tflite::MicroErrorReporter lapor;
    static tflite::MicroInterpreter it(m, res, arena, ARENA_N, &lapor);
#else
    static tflite::MicroInterpreter it(m, res, arena, ARENA_N);
#endif
    interp = &it;
    if (interp->AllocateTensors() != kTfLiteOk) {
        Serial.println("FATAL: AllocateTensors gagal");
        while (true) { tampilan_led(64, 0, 0); delay(200); tampilan_led(0, 0, 0); delay(200); }
    }
    TfLiteTensor *a = interp->input(0), *b = interp->input(1);
    const bool a_kecil = a->bytes < b->bytes;
    in_rr = a_kecil ? a : b;
    in_morph = a_kecil ? b : a;
    keluar = interp->output(0);
}

static int8_t ke_int8(float x, float skala, int nol)
{
    long q = lroundf(x / skala) + nol;
    if (q < -128) q = -128;
    if (q > 127) q = 127;
    return (int8_t)q;
}

static float klasifikasi(const ecg_beat_t &beat)
{
    for (int i = 0; i < ECG_WIN_LEN_; i++)
        in_morph->data.int8[i] = ke_int8(beat.window[i], ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO);
    for (int i = 0; i < ECG_N_RR; i++)
        in_rr->data.int8[i] = ke_int8(beat.rr[i], ECG_IN_RR_SCALE, ECG_IN_RR_ZERO);
    interp->Invoke();
    return (keluar->data.int8[0] - ECG_OUT_ZERO) * ECG_OUT_SCALE;
}

static void publikasi(const ecg_beat_t &beat, float p, bool aritmia)
{
    if (!ecg_mqtt_aktif()) return;
    if (gerbang_fase() != FASE_BAIK) { h.ditahan++; return; }
    if (beat.sinyal_hilang) { h.ditahan++; return; }

    ecg_mqtt_beat_t t;
    t.ms = gerbang_t_sesi_ms() + (uint32_t)((uint64_t)beat.r_abs * 1000ULL / ECG_FS);
    t.rr_ms = beat.rr[0] * 1000.0f;
    t.bpm = (beat.rr[0] > 0.05f) ? 60.0f / beat.rr[0] : 0.0f;
    t.label = aritmia ? 1 : 0;
    t.confidence = aritmia ? p : 1.0f - p;
    t.quality_ok = 1;
    for (int i = 0; i < ECG_SNIPPET_N; i++) {
        const int j = i * (ECG_WIN_LEN_ - 1) / (ECG_SNIPPET_N - 1);
        t.snippet[i] = (int16_t)(beat.window[j] * 1000.0f);
    }
    const uint32_t tunda = millis() - t.ms;
    h.tunda_jml += tunda; h.tunda_n++;
    if (tunda > h.tunda_maks) h.tunda_maks = tunda;

    ecg_mqtt_antre_isi(&t);
}

bool klasifikasi_proses(const ecg_beat_t &beat)
{
    const float p = klasifikasi(beat);
    const bool aritmia = p >= ECG_THRESHOLD;
    h.total++;
    if (aritmia) h.aritmia++;
    const float bpm = (beat.rr[0] > 0.05f) ? 60.0f / beat.rr[0] : 0.0f;
    Serial.printf("beat %4d  p=%.4f  %-7s  RR=%.3fs  %3.0f bpm\n",
                  h.total, p, aritmia ? "ARITMIA" : "normal", beat.rr[0], bpm);
    publikasi(beat, p, aritmia);
    return aritmia;
}
#endif
