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
// Timeout asistol. Dengan ECG_RR_RATIO=1 keputusan beat i menunggu R berikutnya
// (tunda 1 beat). Kalau R itu TIDAK PERNAH datang — elektroda lepas, atau
// asistol — beat terakhir akan tergantung selamanya, dan alat diam justru di
// momen paling kritis. 3 detik = ~20 bpm, di bawah bradikardia apa pun yang
// masih hidup, jadi tidak memicu palsu.
#define ECG_LIVE_TIMEOUT (3 * ECG_FS)

typedef struct {
    int r_abs;                          // indeks absolut R setelah penyelarasan
    float window[ECG_WIN_LEN_];         // sudah z-score, R di ECG_WIN_PRE+ECG_GROUP_DELAY
    float rr[ECG_N_RR];                 // bentuk tergantung ECG_RR_RATIO & ECG_QRSW
    // 1 kalau beat ini dikeluarkan lewat timeout, artinya RR+1 TIDAK terukur dan
    // diisi sentinel netral (rasio 1,0 = "RR berikutnya sama dengan sekarang").
    // Pemanggil sebaiknya menaikkan alarm "sinyal hilang" TERPISAH dari
    // klasifikasi aritmia, supaya tidak mengotori metrik.
    int sinyal_hilang;
} ecg_beat_t;

void ecg_live_reset(void);

// Suapkan satu sampel ADC MENTAH (belum difilter).
// Return 1 kalau ada beat baru siap (diisi ke *beat), 0 kalau belum.
// Dua beat pertama tiap sesi tidak pernah keluar — belum punya RR_prev/dRR,
// sama seperti aturan buang-beat di prep_beats.py.
int ecg_live_push(float sampel_mentah, ecg_beat_t *beat);

// Sampel TERSARING terbaru (bandpass 0,5-40 Hz yang sama dengan pipeline).
// Dipakai penilai kualitas sinyal di firmware: dengung 50 Hz ada di luar pita,
// jadi ayunan sinyal ini mengukur EKG, bukan gangguan jala-jala.
float ecg_live_tersaring_terakhir(void);

// Statistik untuk pemantauan.
size_t ecg_live_total_sampel(void);
int ecg_live_total_beat(void);

#ifdef __cplusplus
}
#endif
#endif  // ECG_LIVE_H
