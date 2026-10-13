// Menu di perangkat: pohon halaman statis (array struct + pointer fungsi),
// navigasi tiga tombol, dan halaman teks yang diperbarui 1 Hz. Isi pohon dan
// peta tombol: docs/arsip/2026-10-13-firmware-menu-plan.md.
//
// Menu hanya mengganti layar dan arti tombol: akuisisi, deteksi, inferensi,
// rekam, bip, dan MQTT tetap berjalan di latar.
//
//   B3 pendek naik      B1 pendek turun     B2 tahan pilih / masuk
//   B2 pendek kembali satu tingkat (di akar = keluar)
//   B1 tahan / B3 tahan keluar langsung ke monitor
//
// Tiap gerakan dicetak ke serial ("menu: <judul> [i/n] <baris>") supaya
// navigasi bisa diuji lewat event tombol suntikan ('t').
#ifndef MENU_H
#define MENU_H

bool menu_terbuka(void);
void menu_buka(void);                      // dari monitor: B2 tahan
void menu_tombol(int i, int e);            // event tombol (tombol.h) selama menu terbuka
void menu_layani(void);                    // tiap loop(): halaman teks 1 Hz

#endif
