#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "buttons.h"

#include <Arduino.h>
#include "board.h"

constexpr uint32_t DEBOUNCE_MS = 50;

static bool pressed[3], long_held[3];
static uint32_t t_change[3];

static struct { uint8_t i, e; } injected[8];
static int injected_count;

bool buttons_pressed(int i) { return pressed[i]; }

void buttons_inject(int i, int e)
{
    if (i < 0 || i > 2 || injected_count == 8) return;
    injected[injected_count].i = i;
    injected[injected_count++].e = e;
}

int buttons_event(int *i)
{
    if (injected_count) {
        *i = injected[0].i;
        const int e = injected[0].e;
        for (int k = 1; k < injected_count; k++) injected[k - 1] = injected[k];
        injected_count--;
        return e;
    }
    for (int k = 0; k < 3; k++) {
        *i = k;
        if (pressed[k] && !long_held[k] && millis() - t_change[k] >= BUTTON_LONG_MS) {
            long_held[k] = true;
            return BUTTON_LONG;
        }
        const bool current = digitalRead(PIN_BTN[k]) == LOW;
        if (current == pressed[k] || millis() - t_change[k] < DEBOUNCE_MS) continue;
        pressed[k] = current;
        t_change[k] = millis();
        if (current) { long_held[k] = false; return BUTTON_PRESS; }
        return long_held[k] ? BUTTON_RELEASE : BUTTON_SHORT;
    }
    return BUTTON_NONE;
}
#endif
