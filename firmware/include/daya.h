// INA219 dan tangga ukur daya p0-p5 (docs/arsip/2026-09-16-daya-design.md §1).
// Tiap anak tangga menambah satu beban; ongkos satu tahap = selisih dua anak
// tangga.
//   p0 timer ISR mati          p3 + inferensi CNN
//   p1 + ISR 360 Hz & kuras    p4 + UI: gelombang TFT, bip, LED
//   p2 + ecg_live (DSP)        p5 + radio WiFi & MQTT (= operasi normal)
// Radio WiFi mati di p0-p4. Teks TFT 1 Hz, tombol, dan pembacaan INA219 jalan di
// semua anak tangga, sehingga ongkosnya hilang di selisih.
#ifndef DAYA_H
#define DAYA_H

void daya_mulai(void);                     // pasang INA219
bool daya_ina_ada(void);
const char *daya_ina_teks(void);           // bacaan INA219 untuk baris 's'

int daya_mode(void);                       // -1 = operasi normal, 0..5 = anak tangga
void daya_set_mode(int m);
// true kalau tahap t (2 DSP, 3 CNN, 4 UI) berjalan di mode sekarang.
bool daya_tahap(int t);
void daya_hitung_beat(void);               // tiap beat keluar dari ecg_live
// Tiap iterasi loop(): satu baris 'DAYA ...' per jendela 10 detik.
void daya_layani(void);

// Tangga mandiri (menu Ukur daya / serial 'V'): p0..p5 berurutan, tiap langkah
// buang 1 jendela transien lalu ambil DAYA_BLOK jendela DAYA_JENDELA_MS (bawaan
// 6 x 10 s, sama dengan measure_power.py; build flag -D untuk uji singkat).
// Validasi sama dengan measure_power.py; hasil ke /daya/NNN.csv dengan kolom
//   waktu,mode,n,I_mA,sd_mA,V,P_mW,beat,lewat,replay,sah
// waktu = UTC ISO bila jam NTP tersinkron, selain itu "+<detik uptime>s".
// Selesai -> kembali ke operasi normal.
typedef struct { char mode[4]; float i_ma, sd_ma, v, p_mw; } daya_baris_t;  // mode "pN", "pN!" = tidak sah
void daya_tangga_mulai(void);
bool daya_tangga_aktif(void);
void daya_tangga_tick(void);               // non-blocking, tiap iterasi loop()
int daya_tangga_langkah(void);             // 0..5 sedang berjalan, -1 selesai/tidak aktif
int daya_tangga_hasil(daya_baris_t *keluar, int maks);   // ringkasan per mode tangga terakhir
int daya_tangga_berkas(void);              // nomor /daya/NNN.csv terakhir (0 = belum ada)
// 'v' daftar berkas, 'v<n>' dump berkas n di antara ---MULAI---/---SELESAI---,
// 'V' mulai tangga. false = bukan perintah daya.
bool daya_serial(const char *perintah);

#endif
