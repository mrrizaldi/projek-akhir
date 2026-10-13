// STUB SEMENTARA — diisi agen fase 4/5 (worktree terpisah). Kontrak persis
// yang disepakati koordinator; menu.cpp, main.cpp, dan serial_cmd.cpp memakai
// header ini sampai digabung.
//
// Saat menggabungkan:
//   fase 4: tidak perlu apa-apa — begitu include/diagnosa.h ada, header itu
//           yang dipakai dan stub diag_* (weak) kalah oleh definisi aslinya.
//   fase 5: hapus blok "daya tangga" di bawah (deklarasinya pindah ke daya.h)
//           — atau hapus berkas ini + src/stub_fase45.cpp dan ganti
//           #include "stub_fase45.h" dengan "diagnosa.h" + "daya.h".
#ifndef STUB_FASE45_H
#define STUB_FASE45_H

#include <stdint.h>
#include "daya.h"

#if __has_include("diagnosa.h")
#include "diagnosa.h"
#else
// diisi agen fase 4
typedef struct { bool lulus; char ringkas[64]; } diag_hasil_t;
diag_hasil_t diag_buzzer(void);
diag_hasil_t diag_layar(void);             // menggambar pola sendiri di TFT
diag_hasil_t diag_adc(void);
diag_hasil_t diag_ina219(void);
diag_hasil_t diag_tombol(uint32_t batas_ms);
#endif

// ---- daya tangga — diisi agen fase 5
typedef struct { char mode[4]; float i_ma, sd_ma, v, p_mw; } daya_baris_t;
void daya_tangga_mulai(void);
bool daya_tangga_aktif(void);
void daya_tangga_tick(void);               // tiap putaran loop()
int daya_tangga_langkah(void);             // 0..5, -1 selesai
int daya_tangga_hasil(daya_baris_t *keluar, int maks);
int daya_tangga_berkas(void);              // nomor /daya/NNN.csv terakhir
bool daya_serial(const char *perintah);    // "v" daftar, "v<n>" dump

#endif
