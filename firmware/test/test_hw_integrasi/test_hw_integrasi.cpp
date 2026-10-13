// Integrasi di board: seluruh perangkat terpasang seperti firmware utama, lalu
// golden_raw diputar lewat jalur akuisisi sungguhan:
//   timer ISR 360 Hz -> antrean -> ecg_live (bandpass, deteksi R, window, RR)
//   -> HR -> inferensi TFLM,
// sementara TFT menggambar gelombang + HR, INA219 dibaca tiap detik, dan
// buzzer berbunyi per detak. Beban tampilan ikut dihitung, jadi test ini
// menangkap sampel yang hilang karena loop terblokir, bukan hanya salah hitung.
//
//   pio test -e esp32-s3 -f test_hw_integrasi
//
// Bedanya dengan test_inference/test_alur_hidup: di sana sampel float
// disuapkan langsung tanpa ISR, tanpa konversi counts, dan tanpa perangkat.
#include <Arduino.h>
#include <unity.h>

#include "tensorflow/lite/micro/micro_interpreter.h"
#if __has_include("tensorflow/lite/micro/micro_error_reporter.h")
#include "tensorflow/lite/micro/micro_error_reporter.h"
#define TFLM_PUNYA_ERROR_REPORTER 1
#endif
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "model_int8.h"
#include "ecg_live.h"
#include "ina219.h"
#include "perangkat.h"
#include "../golden_ref.h"

constexpr int PUTARAN = 3;                 // 3 x 6,7 detik golden_raw
constexpr int ARENA_N = 24 * 1024;
alignas(16) static uint8_t arena[ARENA_N];
static tflite::MicroInterpreter *interp;
static TfLiteTensor *in_morph, *in_rr, *keluar;

// Antrean dan konversi counts sama dengan main.cpp: float hanya di setup(),
// ISR menyalin integer.
constexpr size_t ANTRE_N = 256;
static volatile uint16_t antre[ANTRE_N];
static volatile size_t tulis, baca, replay_i;
static volatile uint32_t n_lewat;
static uint16_t sim_counts[GOLDEN_N];

static void IRAM_ATTR on_timer()
{
    const size_t berikut = (tulis + 1) % ANTRE_N;
    if (berikut == baca) { n_lewat++; return; }
    antre[tulis] = sim_counts[replay_i];
    replay_i = (replay_i + 1) % GOLDEN_N;
    tulis = berikut;
}

// Hasil satu kali jalan, dinilai oleh test-test di bawah.
static int beat_keluar, cocok, prediksi_benar, hr_meleset;
static uint32_t n_diproses, loop_maks_us;

void test_model_termuat(void)
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
    TEST_ASSERT_EQUAL(kTfLiteOk, interp->AllocateTensors());
    TfLiteTensor *a = interp->input(0), *b = interp->input(1);
    in_rr = a->bytes < b->bytes ? a : b;
    in_morph = a->bytes < b->bytes ? b : a;
    keluar = interp->output(0);
}

static int8_t ke_int8(float x, float skala, int nol)
{
    long q = lroundf(x / skala) + nol;
    return (int8_t)constrain(q, -128L, 127L);
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

static void layar_hr(int hr, bool aritmia)
{
    float mA, V;
    const bool ina = ina219_baca(R_SHUNT, &mA, &V);
    tft.setTextSize(3);
    tft.setTextColor(aritmia ? ST77XX_RED : ST77XX_WHITE, ST77XX_BLACK);
    tft.setCursor(4, 3);
    tft.printf("HR %3d", hr);
    tft.setTextSize(2);
    tft.setTextColor(ST77XX_CYAN, ST77XX_BLACK);
    tft.setCursor(200, 8);
    if (ina) tft.printf("%4.0fmA", mA);
    else     tft.print("INA -- ");
}

void test_jalankan_replay_tanpa_sampel_hilang(void)
{
    static ecg_beat_t beat;
    int hr = 0;
    bool aritmia = false;
    uint32_t t_layar = 0, buzz_sampai = 0;

    hw_timer_t *timer = timerBegin(0, 80, true);
    timerAttachInterrupt(timer, &on_timer, true);
    timerAlarmWrite(timer, 1000000 / ECG_FS, true);
    timerAlarmEnable(timer);

    while (n_diproses < (uint32_t)PUTARAN * GOLDEN_N) {
        const uint32_t t0 = micros();
        if (baca != tulis) {
            const float s = antre[baca];
            baca = (baca + 1) % ANTRE_N;
            n_diproses++;
            if (ecg_live_push(s, &beat)) {
                beat_keluar++;
                const float p = klasifikasi(beat);
                aritmia = p >= ECG_THRESHOLD;
                hr = (int)lroundf(60.0f / beat.rr[0]);
                buzzer(true);
                buzz_sampai = millis() + (aritmia ? 250 : 50);
                // Putaran pertama dibandingkan ke jawaban PC. Putaran berikutnya
                // tidak: RR di sambungan ujung-awal golden_raw tidak ada di PC.
                for (int b = GOLDEN_RR_FIRST; b < GOLDEN_N_BEAT && beat.r_abs < GOLDEN_N; b++) {
                    if (abs(beat.r_abs - golden_r[b]) > 20) continue;
                    cocok++;
                    const int hr_pc = (int)lroundf(60.0f * ECG_FS / (golden_r[b] - golden_r[b - 1]));
                    if (abs(hr - hr_pc) > 3) hr_meleset++;
                    if ((aritmia ? 1 : 0) == golden_label[b]) prediksi_benar++;
                    Serial.printf("  r=%4d (%s) HR %3d (PC %3d) p=%.4f -> %d, PC %d\n",
                                  beat.r_abs, golden_sym[b], hr, hr_pc, p, (int)aritmia, golden_label[b]);
                    break;
                }
            }
            plot(ecg_live_tersaring_terakhir());
        }
        if (millis() - t_layar >= 1000) { t_layar = millis(); layar_hr(hr, aritmia); }
        if (buzz_sampai && (int32_t)(millis() - buzz_sampai) >= 0) { buzzer(false); buzz_sampai = 0; }
        loop_maks_us = max(loop_maks_us, (uint32_t)(micros() - t0));
    }
    timerAlarmDisable(timer);
    timerEnd(timer);
    buzzer(false);

    Serial.printf("diproses %u sampel, beat %d, cocok %d, benar %d, HR meleset %d, "
                  "sampel hilang %u, loop terlama %u us\n",
                  (unsigned)n_diproses, beat_keluar, cocok, prediksi_benar, hr_meleset,
                  (unsigned)n_lewat, (unsigned)loop_maks_us);
    TEST_ASSERT_EQUAL_UINT32_MESSAGE(0, n_lewat, "antrean ISR penuh: loop (TFT/inferensi) terlalu lama");
}

void test_beat_terdeteksi_tiap_putaran(void)
{
    // 9 beat per putaran; dua beat pertama sesi tidak pernah keluar.
    TEST_ASSERT_GREATER_OR_EQUAL(PUTARAN * GOLDEN_N_BEAT - 4, beat_keluar);
}

void test_hr_sama_dengan_anotasi(void)
{
    TEST_ASSERT_GREATER_THAN_MESSAGE(3, cocok, "terlalu sedikit beat cocok anotasi");
    TEST_ASSERT_EQUAL_MESSAGE(0, hr_meleset, "HR beda > 3 bpm dari RR anotasi");
}

void test_prediksi_sama_dengan_pc(void)
{
    TEST_ASSERT_EQUAL_MESSAGE(cocok, prediksi_benar, "label alat beda dari label PC");
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    perangkat_mulai();
    Serial.begin(115200);
    delay(2000);
    ina219_mulai(I2C_SDA, I2C_SCL);     // boleh absen; diuji test_hw_ina219
    for (size_t i = 0; i < GOLDEN_N; i++)
        sim_counts[i] = (uint16_t)constrain(golden_raw[i] * 1000.0f + 2048.0f, 0.0f, 4095.0f);
    ecg_live_reset();

    UNITY_BEGIN();
    RUN_TEST(test_model_termuat);
    RUN_TEST(test_jalankan_replay_tanpa_sampel_hilang);
    RUN_TEST(test_beat_terdeteksi_tiap_putaran);
    RUN_TEST(test_hr_sama_dengan_anotasi);
    RUN_TEST(test_prediksi_sama_dengan_pc);
    UNITY_END();
}

void loop() {}
