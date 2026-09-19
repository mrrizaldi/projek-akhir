// Kontrak preprocessing on-device. Implementasi ada di src/ecg_pipeline.cpp
// dan HARUS menghasilkan angka yang sama dengan model/src/preprocessing.py
// (dibuktikan oleh test/test_preproc/, bandingkan ke test/golden_ref.h).
//
// Golden reference-nya Python. Kalau C dan Python beda, C yang salah.
#ifndef ECG_PIPELINE_H
#define ECG_PIPELINE_H

#include <stddef.h>
#include "ecg_preproc.h"   // GENERATED: koefisien SOS + konstanta

#ifdef __cplusplus
extern "C" {
#endif

// Bandpass kausal 0,5-40 Hz, 4 second-order section (ecg_sos di ecg_preproc.h).
// Streaming: state disimpan antar-panggilan supaya bisa dipanggil per potongan
// sinyal tanpa mengubah hasil. `state` = ECG_N_SOS x 2 float, di-nol-kan sekali.
//
// JANGAN memfilter maju-mundur. filtfilt mustahil real-time; model dilatih
// dengan filter kausal, dan group delay +4 sampel adalah bagian dari kontrak.
void ecg_bandpass(const float *in, float *out, size_t n, float *state);

// Potong window [r - ECG_WIN_PRE, r + ECG_WIN_POST) lalu z-score DI DALAM
// window itu sendiri: (x - mean) / (std + ECG_ZSCORE_EPS).
// std = populasi (pembagi N), bukan sampel (N-1) — numpy std() default.
// Return 0 kalau window tidak muat di sinyal.
int ecg_window_zscore(const float *filtered, size_t n, int r, float *out);

// Fitur ritme dari indeks R-peak. rr_prev = (r[i]-r[i-1])/fs;
// rr_ratio = rr_prev / rata-rata KAUSAL <=10 interval terakhir (jendela
// menyusut di awal); drr = rr_prev sekarang - rr_prev sebelumnya.
// Butuh i >= 2. Return 0 kalau belum cukup beat.
// Bentuk keluaran tergantung ECG_RR_RATIO di ecg_preproc.h (GENERATED):
//   0 -> rr_prev (detik), rr_ratio, drr        butuh i >= 2
//   1 -> RR0/avgRR, RR+1/RR0, RR-1/RR0, tRR0  butuh i >= 2 DAN i+1 < n_r
// Varian rasio menunda keputusan 1 beat: beat i tidak bisa dinilai sebelum R
// berikutnya terdeteksi (GATE G2). Semua rasio -> fs-independen & tak membocorkan
// identitas pasien. Return 0 kalau belum cukup beat.
int ecg_rr_features(const int *r, size_t n_r, size_t i, int fs, float out[ECG_N_RR_DASAR]);

#if ECG_QRSW
// Lebar QRS pada `frac` x puncak, dalam SAMPEL, dari window ter-z-score.
float ecg_qrs_lebar(const float *window, float frac);

// QRSw2 & QRSw4 dinormalisasi ke rerata KAUSAL ECG_RR_LOCAL_WINDOW beat terakhir.
// `riwayat` milik pemanggil: 2 x ECG_RR_LOCAL_WINDOW float, di-nol-kan sekali.
// `n_riwayat` = jumlah beat yang sudah masuk sebelum panggilan ini.
int ecg_qrs_width_features(const float *window, float *riwayat, size_t n_riwayat,
                           float out[2]);
#endif

// Deteksi R-peak Pan-Tompkins atas sinyal yang SUDAH di-bandpass 0,5-40 Hz.
// Kaskade: bandpass 5-15 Hz -> turunan -> kuadrat -> integrasi 150 ms ->
// ambang adaptif + refraktori 200 ms.
//
// `scratch` disediakan pemanggil, n float — tidak ada alokasi dinamis.
// Menulis indeks MENTAH (belum dikompensasi) ke out[], mengembalikan jumlahnya.
int ecg_detect_r(const float *filtered, size_t n, float *scratch,
                 int *out, int out_maks);

// Ubah indeks mentah detektor jadi indeks siap potong window.
//   r - ECG_PT_OFFSET  ->  puncak sebenarnya dlm +-ECG_PT_REFINE  ->  - ECG_GROUP_DELAY
// Hasilnya menaruh puncak R di indeks ECG_WIN_PRE+ECG_GROUP_DELAY dalam window, sama seperti saat
// training. Meleset 4 sampel saja menjatuhkan precision dari 0,48 ke 0,12
// (docs/segmentasi-deteksi-walkthrough.md).
int ecg_align_r(const float *filtered, size_t n, int r_kasar);

#ifdef __cplusplus
}
#endif
#endif  // ECG_PIPELINE_H
