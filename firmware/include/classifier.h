#ifndef CLASSIFIER_H
#define CLASSIFIER_H

#include <stddef.h>
#include <stdint.h>
#include "ecg_live.h"

void classifier_begin(void);
size_t classifier_arena(void);
float classifier_threshold(void);

bool classifier_process(const ecg_beat_t &beat);

struct classifier_stats_t {
    int total, arrhythmia, withheld;
    uint32_t latency_sum, latency_n, latency_max;
};
const classifier_stats_t &classifier_stats(void);
void classifier_reset(void);

#endif
