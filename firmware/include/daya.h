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

#endif
