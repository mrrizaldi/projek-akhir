// Gerbang kualitas sinyal: ayunan 1 detik dan fase kalibrasi -> pemantauan.
// Aturannya bab3.tex §Pengujian Pipeline tahap 1-2; rinciannya di gerbang.cpp.
#ifndef GERBANG_H
#define GERBANG_H

#include <stdint.h>
#include "ecg_live.h"

enum { FASE_KALIBRASI, FASE_BAIK, FASE_BURUK };

// Ambang kualitas sinyal, dari akuisisi-walkthrough.md §2 (angka empiris, bukan
// tebakan: kontak segar 691 counts, elektroda dipakai ulang 195).
constexpr int AMBANG_AYUN = 60;            // ayunan TERSARING 1 detik, counts ADC

// Kualitas sinyal 1 detik terakhir (LED, HR, publikasi, laporan serial).
struct gerbang_kualitas_t {
    int ayun, ayun_bersih, hum50, mentah_min, mentah_maks;
    bool clipping;
};
const gerbang_kualitas_t &gerbang_kualitas(void);

// Sesi baru: bip panjang, ecg_live dari nol, fase KALIBRASI, jadwal bip kosong.
void gerbang_mulai_sesi(void);
uint32_t gerbang_t_sesi_ms(void);          // millis() saat sesi dimulai

// Tiap sampel, SETELAH ecg_live_push (membaca sampel tersaring terbaru).
void gerbang_nilai_kualitas(float mentah);
// Tiap beat, SEBELUM keputusan inferensi.
void gerbang_nilai_fase(const ecg_beat_t &beat);
// Baris 'calibrating ...' di serial, paling sering tiap 5 detik.
void gerbang_lapor_kalibrasi(const ecg_beat_t &beat);

int gerbang_fase(void);
const char *gerbang_nama_fase(void);

// Lewati gerbang masuk untuk bench ('k'). OFF memulai sesi baru.
bool gerbang_lewati(void);
void gerbang_set_lewati(bool on);
// Cetak baris kualitas tiap detik ('q').
bool gerbang_lapor(void);
void gerbang_set_lapor(bool on);

#endif
