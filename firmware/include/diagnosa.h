// Tes perangkat PCB, dipakai BERSAMA oleh menu "Tes perangkat" dan test device
// test/test_hw_* (tidak ada salinan kode di test).
//
// Prasyarat: perangkat_mulai() sudah dipanggil. Tiap fungsi memblok (paling
// lama ~2 s, diag_tombol sampai batas_ms) dan mencetak ringkas ke Serial.
// Pemanggil yang menjalankan akuisisi sebaiknya mematikan timer selama tes
// (akuisisi_timer(false)): selama memblok, antrean ISR penuh dan sampel hilang.
// diag_layar menimpa layar; pemanggil menggambar ulang sesudahnya.
#ifndef DIAGNOSA_H
#define DIAGNOSA_H

#include <stdint.h>

typedef struct {
    bool lulus;
    char ringkas[64];   // teks pendek siap tampil, mis. "INA219 0x40 ok V=3,92 I=112mA"
} diag_hasil_t;

// Pin GPIO 13 dipegang LEDC (bukan direbut SPI), keluaran dibalik, diam = HIGH,
// bunyi = gelombang kotak ~50 % LOW; lalu tiga bip pendek untuk didengar.
diag_hasil_t diag_buzzer(void);
// Ukuran layar, waktu fillScreen penuh (bukti SPI mengirim), lalu pola empat
// pita warna + "TFT OK" selama ~2 s untuk dilihat.
diag_hasil_t diag_layar(void);
// ADC EKG: 100 bacaan dalam 0..4095, min/maks selama ~1 s, status LO+/LO-.
// Lulus tidak bergantung elektroda.
diag_hasil_t diag_adc(void);
// INA219 menjawab di I2C, bacaan V/I dalam rentang chip. V bus < 1 V ditandai
// (shunt tidak di jalur catu) tetapi tetap lulus.
diag_hasil_t diag_ina219(void);
// Menunggu B1, B2, B3 masing-masing ditekan sekali (tepi tekan; tombol yang
// sedang ditahan saat mulai harus dilepas dulu). Kembali paling lambat batas_ms.
diag_hasil_t diag_tombol(uint32_t batas_ms);

#endif
