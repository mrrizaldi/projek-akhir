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

// Tahap 3 — fitur RR. golden_rr dihitung dari golden_r yang sama, jadi C punya
// input identik dengan Python. Beat 0 & 1 tak punya RR_prev/dRR → dilewati.
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

// Beat 0 & 1 wajib DITOLAK, bukan diisi nilai asal — dRR=0 itu nilai sah
// (ritme stabil), jadi sentinel 0 akan bentrok dengan data asli.
void test_rr_menolak_beat_awal(void)
{
    float rr[3];
    TEST_ASSERT_FALSE(ecg_rr_features(golden_r, GOLDEN_N_BEAT, 0, ECG_FS, rr));
    TEST_ASSERT_FALSE(ecg_rr_features(golden_r, GOLDEN_N_BEAT, 1, ECG_FS, rr));
}

// Uji rantai UTUH: mentah -> bandpass C -> z-score C, dibandingkan ke window
// golden. Ini yang membuktikan selisih presisi float32 di filter tidak merambat
// jadi masalah di masukan model — z-score membagi dengan std, jadi galat
// bersama ikut ternormalisasi.
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

// Tahap 3c — deteksi R-peak. Diadu ke deret indeks dari Python.
static float buf_scratch[GOLDEN_N];
static int buf_r[64];

void test_detect_r(void)
{
    const int n = ecg_detect_r(golden_filtered, GOLDEN_N, buf_scratch, buf_r, 64);
    char pesan[96];
    snprintf(pesan, sizeof(pesan), "dapat %d R-peak, harus %d", n, GOLDEN_N_DETEKSI);
    TEST_ASSERT_EQUAL_MESSAGE(GOLDEN_N_DETEKSI, n, pesan);
    for (int i = 0; i < n; i++) {
        // Toleransi 1 sampel: beda pembulatan float bisa menggeser puncak lokal.
        snprintf(pesan, sizeof(pesan), "peak %d: dapat %d, harus %d",
                 i, buf_r[i], golden_r_deteksi[i]);
        TEST_ASSERT_INT_WITHIN_MESSAGE(1, golden_r_deteksi[i], buf_r[i], pesan);
    }
}

// Sifat yang HARUS berlaku: setelah penyelarasan, puncak R mendarat di indeks
// 94 dalam window — persis seperti window training. Meleset 4 sampel saja
// menjatuhkan precision model 4x.
void test_align_r_menaruh_puncak_di_94(void)
{
    const int n = ecg_detect_r(golden_filtered, GOLDEN_N, buf_scratch, buf_r, 64);
    int diuji = 0;
    for (int i = 0; i < n; i++) {
        const int r = ecg_align_r(golden_filtered, GOLDEN_N, buf_r[i]);
        if (r - ECG_WIN_PRE < 0 || r + ECG_WIN_POST > GOLDEN_N) continue;
        TEST_ASSERT_TRUE(ecg_window_zscore(golden_filtered, GOLDEN_N, r, buf_window));
        // Cari puncak DI SEKITAR 94 saja. argmax global tidak bisa dipakai:
        // record 208 punya detak berdekatan (697 -> 853), jadi window 250 sampel
        // sering memuat R tetangga yang lebih tinggi.
        int puncak = 94 - 20;
        for (int k = 94 - 20; k <= 94 + 20; k++)
            if (buf_window[k] > buf_window[puncak]) puncak = k;
        char pesan[96];
        snprintf(pesan, sizeof(pesan), "beat %d: puncak di %d, harus 94", i, puncak);
        TEST_ASSERT_INT_WITHIN_MESSAGE(2, 94, puncak, pesan);
        diuji++;
    }
    TEST_ASSERT_GREATER_THAN_MESSAGE(3, diuji, "terlalu sedikit beat teruji");
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
    RUN_TEST(test_align_r_menaruh_puncak_di_94);
    UNITY_END();
}

// Test yang sama jalan di dua tempat: `pio test -e native` (PC) dan
// `pio test -e esp32-s3` (FPU sungguhan). Arduino tidak punya main().
#ifdef ARDUINO
#include <Arduino.h>
void setup() { Serial.begin(115200); delay(2000); jalankan(); }
void loop() {}
#else
int main(int argc, char **argv) { (void)argc; (void)argv; jalankan(); return 0; }
#endif
