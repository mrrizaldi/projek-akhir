#ifndef TOMBOL_H
#define TOMBOL_H

#include <stdint.h>

enum {
    TOMBOL_TIDAK,
    TOMBOL_TEKAN,
    TOMBOL_PENDEK,
    TOMBOL_LAMA,
    TOMBOL_LEPAS,
};

constexpr uint32_t TOMBOL_LAMA_MS = 800;

int tombol_event(int *i);
bool tombol_ditekan(int i);

void tombol_suntik(int i, int e);

#endif
