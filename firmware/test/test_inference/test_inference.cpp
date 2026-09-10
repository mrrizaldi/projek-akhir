// Uji inferensi INT8 di ESP32-S3 sungguhan.
//
//   pio test -e esp32-s3
//
// Rantai penuh: golden_raw -> bandpass C -> z-score C -> TFLite Micro,
// dibandingkan ke golden_prob_int8 (jawaban dari interpreter TFLite di PC).
// Kalau angka di device beda dari di PC, model yang sama dijalankan berbeda —
// itu yang harus ketahuan DI SINI, bukan saat alat sudah dipasang ke orang.
#include <Arduino.h>
#include <unity.h>

#include "tensorflow/lite/micro/micro_interpreter.h"
// TFLM lama (2022) menuntut ErrorReporter di argumen ke-4; yang baru menghapusnya.
#if __has_include("tensorflow/lite/micro/micro_error_reporter.h")
#include "tensorflow/lite/micro/micro_error_reporter.h"
#define TFLM_PUNYA_ERROR_REPORTER 1
#endif
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "model_int8.h"      // GENERATED: bobot + scale/zero_point
#include "ecg_pipeline.h"
#include "../golden_ref.h"

// Tensor arena WAJIB di RAM internal, bukan PSRAM: inferensi menyentuhnya
// ribuan kali per detak dan PSRAM lewat SPI jauh lebih lambat.
constexpr int kArenaSize = 24 * 1024;
alignas(16) static uint8_t tensor_arena[kArenaSize];

static tflite::MicroInterpreter *interpreter = nullptr;
static TfLiteTensor *in_morph = nullptr;
static TfLiteTensor *in_rr = nullptr;
static TfLiteTensor *out = nullptr;

static float buf_filtered[GOLDEN_N];
static float buf_window[GOLDEN_WIN_LEN];
static uint32_t us_terpakai[GOLDEN_N_BEAT];

static void siapkan_model(void)
{
    const tflite::Model *model = tflite::GetModel(model_int8_tflite);
    TEST_ASSERT_EQUAL_MESSAGE(TFLITE_SCHEMA_VERSION, model->version(),
                              "skema flatbuffer model != versi library");

    // Persis 8 op yang dipakai model deploy — jangan AllOpsResolver, dia
    // menarik seluruh kernel TFLM dan membengkakkan flash ~100 KB.
    static tflite::MicroMutableOpResolver<8> resolver;
    resolver.AddConv2D();
    resolver.AddDepthwiseConv2D();   // rata-rata 31 langkah (pengganti MEAN)
    resolver.AddMaxPool2D();
    resolver.AddConcatenation();     // gabung cabang morfologi + ritme
    resolver.AddLogistic();          // sigmoid
    resolver.AddAdd();
    resolver.AddReshape();
    resolver.AddExpandDims();

#ifdef TFLM_PUNYA_ERROR_REPORTER
    static tflite::MicroErrorReporter lapor;
    static tflite::MicroInterpreter statis(model, resolver, tensor_arena, kArenaSize, &lapor);
#else
    static tflite::MicroInterpreter statis(model, resolver, tensor_arena, kArenaSize);
#endif
    interpreter = &statis;
    TEST_ASSERT_EQUAL_MESSAGE(kTfLiteOk, interpreter->AllocateTensors(),
                              "AllocateTensors gagal — arena kurang besar?");

    // Urutan input di .tflite TIDAK dijamin sama dengan di Keras. Bedakan lewat
    // jumlah dimensi: RR (1,3) 2 dimensi, morfologi (1,250,1) 3 dimensi.
    TfLiteTensor *a = interpreter->input(0);
    TfLiteTensor *b = interpreter->input(1);
    const bool a_kecil = a->bytes < b->bytes;      // RR 3 byte vs morfologi 250
    in_rr = a_kecil ? a : b;
    in_morph = a_kecil ? b : a;
    out = interpreter->output(0);
}

static int8_t ke_int8(float x, float scale, int zero)
{
    long q = lroundf(x / scale) + zero;
    if (q < -128) q = -128;
    if (q > 127) q = 127;
    return (int8_t)q;
}

void test_model_termuat(void)
{
    siapkan_model();
    TEST_ASSERT_EQUAL(kTfLiteInt8, in_morph->type);
    TEST_ASSERT_EQUAL(kTfLiteInt8, in_rr->type);
    TEST_ASSERT_EQUAL(kTfLiteInt8, out->type);
    TEST_ASSERT_EQUAL(GOLDEN_WIN_LEN, (int)in_morph->bytes);
    TEST_ASSERT_EQUAL(GOLDEN_N_RR, (int)in_rr->bytes);
}

// Rantai penuh di device, dibandingkan ke jawaban PC.
void test_inferensi_cocok_dengan_pc(void)
{
    float state[ECG_N_SOS * 2];
    memset(state, 0, sizeof(state));
    ecg_bandpass(golden_raw, buf_filtered, GOLDEN_N, state);

    for (int b = GOLDEN_RR_FIRST; b < GOLDEN_N_BEAT; b++) {
        TEST_ASSERT_TRUE(ecg_window_zscore(buf_filtered, GOLDEN_N, golden_r[b], buf_window));

        float rr[3];
        TEST_ASSERT_TRUE(ecg_rr_features(golden_r, GOLDEN_N_BEAT, b, ECG_FS, rr));

        for (int i = 0; i < GOLDEN_WIN_LEN; i++) {
            in_morph->data.int8[i] = ke_int8(buf_window[i], ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO);
        }
        for (int i = 0; i < GOLDEN_N_RR; i++) {
            in_rr->data.int8[i] = ke_int8(rr[i], ECG_IN_RR_SCALE, ECG_IN_RR_ZERO);
        }

        const uint32_t t0 = micros();
        TEST_ASSERT_EQUAL(kTfLiteOk, interpreter->Invoke());
        us_terpakai[b] = micros() - t0;

        const float p = (out->data.int8[0] - ECG_OUT_ZERO) * ECG_OUT_SCALE;

        char pesan[128];
        snprintf(pesan, sizeof(pesan), "beat %d (%s): device %.4f vs PC %.4f",
                 b, golden_sym[b], p, golden_prob_int8[b]);
        TEST_ASSERT_FLOAT_WITHIN_MESSAGE(GOLDEN_TOL_PROB, golden_prob_int8[b], p, pesan);

        // Keputusan akhir harus sama, bukan cuma probabilitasnya berdekatan.
        TEST_ASSERT_EQUAL_MESSAGE(golden_label[b], p >= GOLDEN_THRESHOLD ? 1 : 0, pesan);
    }
}

// DIAGNOSTIK: suapi window & RR GOLDEN langsung (lewati preprocessing C).
// Kalau ini cocok tapi test rantai-penuh tidak → salahnya di preprocessing.
// Kalau ini ikut meleset → salahnya di sisi inferensi/kuantisasi.
void test_diagnostik_input_golden(void)
{
    for (int b = GOLDEN_RR_FIRST; b < GOLDEN_N_BEAT; b++) {
        const float *w = golden_window + (size_t)b * GOLDEN_WIN_LEN;
        const float *rr = golden_rr + (size_t)b * GOLDEN_N_RR;
        for (int i = 0; i < GOLDEN_WIN_LEN; i++)
            in_morph->data.int8[i] = ke_int8(w[i], ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO);
        for (int i = 0; i < GOLDEN_N_RR; i++)
            in_rr->data.int8[i] = ke_int8(rr[i], ECG_IN_RR_SCALE, ECG_IN_RR_ZERO);
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

    // Reproducer minimal: masukan bernilai NOL (float) -> q = zero_point.
    for (int i = 0; i < GOLDEN_WIN_LEN; i++) in_morph->data.int8[i] = ECG_IN_MORPH_ZERO;
    for (int i = 0; i < GOLDEN_N_RR; i++)    in_rr->data.int8[i] = ECG_IN_RR_ZERO;
    interpreter->Invoke();
    Serial.printf("DIAG nol    : q_out=%d  p=%.6f\n",
                  (int)out->data.int8[0],
                  (out->data.int8[0] - ECG_OUT_ZERO) * ECG_OUT_SCALE);

    // Beat 2 dalam domain int8 mentah, plus 5 nilai input pertama.
    const float *w2 = golden_window + (size_t)2 * GOLDEN_WIN_LEN;
    const float *r2 = golden_rr + (size_t)2 * GOLDEN_N_RR;
    for (int i = 0; i < GOLDEN_WIN_LEN; i++)
        in_morph->data.int8[i] = ke_int8(w2[i], ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO);
    for (int i = 0; i < GOLDEN_N_RR; i++)
        in_rr->data.int8[i] = ke_int8(r2[i], ECG_IN_RR_SCALE, ECG_IN_RR_ZERO);
    interpreter->Invoke();
    Serial.printf("DIAG beat2  : q_out=%d  morph[0..4]=%d,%d,%d,%d,%d  rr=%d,%d,%d\n",
                  (int)out->data.int8[0],
                  in_morph->data.int8[0], in_morph->data.int8[1], in_morph->data.int8[2],
                  in_morph->data.int8[3], in_morph->data.int8[4],
                  in_rr->data.int8[0], in_rr->data.int8[1], in_rr->data.int8[2]);
}

// Angka untuk Bab 4: latensi per detak & pemakaian arena.
void test_latensi_dan_memori(void)
{
    uint32_t total = 0, maks = 0;
    for (int b = GOLDEN_RR_FIRST; b < GOLDEN_N_BEAT; b++) {
        total += us_terpakai[b];
        if (us_terpakai[b] > maks) maks = us_terpakai[b];
    }
    const int n = GOLDEN_N_BEAT - GOLDEN_RR_FIRST;
    const size_t arena = interpreter->arena_used_bytes();

    Serial.printf("\n=== BENCHMARK ESP32-S3 ===\n");
    Serial.printf("inferensi     : %lu us rata-rata, %lu us maksimum (%d beat)\n",
                  (unsigned long)(total / n), (unsigned long)maks, n);
    Serial.printf("tensor arena  : %u byte terpakai dari %d byte dialokasikan\n",
                  (unsigned)arena, kArenaSize);
    Serial.printf("heap bebas    : %u byte\n", (unsigned)ESP.getFreeHeap());
    Serial.printf("CPU           : %u MHz\n", (unsigned)ESP.getCpuFreqMHz());
    Serial.printf("==========================\n");

    // Satu detak ~0,8 detik. Inferensi harus jauh di bawah itu supaya kontinu.
    TEST_ASSERT_LESS_THAN_UINT32_MESSAGE(200000, maks,
        "inferensi > 200 ms — terlalu lambat untuk kontinu, pertimbangkan ESP-NN");
    TEST_ASSERT_LESS_OR_EQUAL_MESSAGE(kArenaSize, arena, "arena kurang besar");
}

void setup()
{
    Serial.begin(115200);
    delay(2000);            // tunggu USB-CDC siap sebelum test menulis
    UNITY_BEGIN();
    RUN_TEST(test_model_termuat);
    RUN_TEST(test_diagnostik_input_golden);
    RUN_TEST(test_inferensi_cocok_dengan_pc);
    RUN_TEST(test_latensi_dan_memori);
    UNITY_END();
}

void loop() {}
