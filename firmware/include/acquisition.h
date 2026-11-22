#ifndef ACQUISITION_H
#define ACQUISITION_H

#include <stddef.h>
#include <stdint.h>

constexpr size_t QUEUE_N = 256;

void acquisition_begin(void);
bool acquisition_fetch(uint16_t *sample);
size_t acquisition_fill(void);
uint32_t acquisition_missed(void);
uint32_t acquisition_tick_lost(void);
void acquisition_zero_missed(void);
void acquisition_timer(bool running);

enum { SOURCE_ADC, SOURCE_REFERENCE, SOURCE_RECORDING };
int acquisition_source(void);
int acquisition_source_recording(void);
bool acquisition_replay(void);
bool acquisition_set_source(int source, int number, bool save);
void acquisition_switch_source(void);

#endif
