#ifndef DISPLAY_H
#define DISPLAY_H

#include <stdint.h>
#include "ecg_live.h"

void display_begin(void);
void display_service(void);

void display_led(uint8_t r, uint8_t g, uint8_t b);
void display_sound(uint32_t ms);
void display_clear_schedule(void);
void display_message(const char *large, const char *small);

void display_beat(const ecg_beat_t &beat, bool arrhythmia);
void display_sample(void);

void display_draw_button(int i);

void display_set_monitor(bool on);

constexpr int DISPLAY_ROWS = 6, DISPLAY_COLUMNS = 26;
void display_menu_frame(const char *title, const char *hint1, const char *hint2);
void display_menu_row(int r, const char *text, bool highlight, uint16_t color = 0xFFFF);

bool display_mute(void);
void display_set_mute(bool on);
bool display_freeze(void);
void display_set_freeze(bool on);

#endif
