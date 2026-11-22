#ifndef GATE_H
#define GATE_H

#include <stdint.h>
#include "ecg_live.h"

enum { PHASE_CALIBRATION, PHASE_GOOD, PHASE_BAD };

constexpr int THRESHOLD_SWING = 60;
constexpr int THRESHOLD_HUM = 500;

constexpr uint32_t WARMUP_MS = 60UL * 1000;
constexpr uint32_t RR_QUIET_MS = 30UL * 1000;

struct gate_quality_t {
    int swing, swing_clean, hum50, raw_min, raw_max;
    bool clipping, leadoff, contact;
};
const gate_quality_t &gate_quality(void);

void gate_begin_session(void);
uint32_t gate_t_session_ms(void);
uint32_t gate_quiet_ms(void);
uint32_t gate_contact_ms(void);

void gate_assess_quality(float raw);
void gate_assess_phase(const ecg_beat_t &beat);
void gate_report_calibration(const ecg_beat_t &beat);

int gate_phase(void);
const char *gate_phase_name(void);

bool gate_skip(void);
void gate_set_skip(bool on);
bool gate_report(void);
void gate_set_report(bool on);

#endif
