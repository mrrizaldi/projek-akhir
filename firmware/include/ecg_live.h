// Alur hidup: sampel ADC masuk satu per satu, beat siap-klasifikasi keluar.
//
// Menggabungkan seluruh rantai yang sudah terverifikasi: bandpass streaming ->
// deteksi Pan-Tompkins berkala -> penyelarasan R -> potong window + z-score ->
// fitur RR. Inferensi TIDAK di sini — pemanggil yang menjalankannya, supaya
// modul ini bisa diuji di native tanpa TFLite Micro.
#ifndef ECG_LIVE_H
#define ECG_LIVE_H

#include <stddef.h>
#include "ecg_pipeline.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ECG_LIVE_RING (4 * ECG_FS)      // 4 detik riwayat sinyal terfilter
#define ECG_LIVE_TIAP ECG_FS            // jalankan deteksi tiap 1 detik
#define ECG_LIVE_HIST 16                // R-peak terakhir yg disimpan utk fitur RR

typedef struct {
    int r_abs;                          // indeks absolut R setelah penyelarasan
    float window[ECG_WIN_LEN_];         // sudah z-score, R di indeks 94
    float rr[ECG_N_RR];                 // RR_prev, RR_ratio, dRR
} ecg_beat_t;

void ecg_live_reset(void);

// Suapkan satu sampel ADC MENTAH (belum difilter).
// Return 1 kalau ada beat baru siap (diisi ke *beat), 0 kalau belum.
// Dua beat pertama tiap sesi tidak pernah keluar — belum punya RR_prev/dRR,
// sama seperti aturan buang-beat di prep_beats.py.
int ecg_live_push(float sampel_mentah, ecg_beat_t *beat);

// Statistik untuk pemantauan.
size_t ecg_live_total_sampel(void);
int ecg_live_total_beat(void);

#ifdef __cplusplus
}
#endif
#endif  // ECG_LIVE_H
