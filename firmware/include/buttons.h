#ifndef BUTTONS_H
#define BUTTONS_H

#include <stdint.h>

enum {
    BUTTON_NONE,
    BUTTON_PRESS,
    BUTTON_SHORT,
    BUTTON_LONG,
    BUTTON_RELEASE,
};

constexpr uint32_t BUTTON_LONG_MS = 800;

int buttons_event(int *i);
bool buttons_pressed(int i);

void buttons_inject(int i, int e);

#endif
