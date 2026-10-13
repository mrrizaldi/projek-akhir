// Tombol B1/B2/B3: debounce dan event per tombol. Aksi tiap event dirangkai
// pemanggil (main.cpp), modul ini tidak tahu arti tombol.
#ifndef TOMBOL_H
#define TOMBOL_H

#include <stdint.h>

enum {
    TOMBOL_TIDAK,      // tidak ada event
    TOMBOL_TEKAN,      // baru ditekan (setelah debounce)
    TOMBOL_PENDEK,     // dilepas sebelum TOMBOL_LAMA_MS
    TOMBOL_LAMA,       // masih ditahan saat TOMBOL_LAMA_MS tercapai
    TOMBOL_LEPAS,      // dilepas setelah TOMBOL_LAMA
};

constexpr uint32_t TOMBOL_LAMA_MS = 2000;

// Satu event per panggilan, *i diisi indeks tombol 0..2. Panggil berulang
// sampai TOMBOL_TIDAK.
int tombol_event(int *i);
bool tombol_ditekan(int i);

#endif
