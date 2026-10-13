// Inferensi TFLM INT8 per beat dan publikasi hasilnya ke antrean MQTT.
#ifndef KLASIFIKASI_H
#define KLASIFIKASI_H

#include <stddef.h>
#include <stdint.h>
#include "ecg_live.h"

// Memuat model ke arena. Gagal = berhenti di sini dengan LED merah berkedip.
void klasifikasi_mulai(void);
size_t klasifikasi_arena(void);            // byte arena terpakai
float klasifikasi_ambang(void);            // p >= ambang = ARITMIA

// Satu beat fase BAIK/BURUK: inferensi, baris 'beat' di serial, publikasi.
// Return true = ARITMIA.
bool klasifikasi_proses(const ecg_beat_t &beat);

// Hitungan sesi untuk baris status 's'.
struct klasifikasi_hitung_t {
    int total, aritmia, ditahan;           // ditahan = tidak dipublikasi
    uint32_t tunda_jml, tunda_n, tunda_maks;   // tunda sisi alat, ms
};
const klasifikasi_hitung_t &klasifikasi_hitung(void);
void klasifikasi_reset(void);

#endif
