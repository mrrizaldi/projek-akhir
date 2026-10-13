// Tombol. Kontrak: include/tombol.h
#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "tombol.h"

#include <Arduino.h>
#include "perangkat.h"

constexpr uint32_t DEBOUNCE_MS = 50;

static bool tekan[3], lama[3];
static uint32_t t_ubah[3];

static struct { uint8_t i, e; } suntik[8];
static int s_isi;

bool tombol_ditekan(int i) { return tekan[i]; }

void tombol_suntik(int i, int e)
{
    if (i < 0 || i > 2 || s_isi == 8) return;
    suntik[s_isi].i = i;
    suntik[s_isi++].e = e;
}

int tombol_event(int *i)
{
    if (s_isi) {
        *i = suntik[0].i;
        const int e = suntik[0].e;
        for (int k = 1; k < s_isi; k++) suntik[k - 1] = suntik[k];
        s_isi--;
        return e;
    }
    for (int k = 0; k < 3; k++) {
        *i = k;
        if (tekan[k] && !lama[k] && millis() - t_ubah[k] >= TOMBOL_LAMA_MS) {
            lama[k] = true;
            return TOMBOL_LAMA;
        }
        const bool kini = digitalRead(PIN_BTN[k]) == LOW;
        if (kini == tekan[k] || millis() - t_ubah[k] < DEBOUNCE_MS) continue;
        tekan[k] = kini;
        t_ubah[k] = millis();
        if (kini) { lama[k] = false; return TOMBOL_TEKAN; }
        return lama[k] ? TOMBOL_LEPAS : TOMBOL_PENDEK;
    }
    return TOMBOL_TIDAK;
}
#endif
