---
tags: [feature-docs]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Skill, Write]
---

dokumentasikan fitur ini: the firmware has a calibration gate (`gate`) and there is no docs page for it yet. Write the docs.

You cannot run commands or read the repo beyond what is pasted here. Write the full new page, the exact edits to any other files, the commands you would run, and your final report. Write any command output you cannot see as [N].

Background from me: I tuned the thresholds during the bench session on 21 Okt 2026 after S02 kept starting classification with a loose electrode. In my experience the gate usually passes after about 70 seconds.

## What the code does

- `firmware/include/gate.h` defines the phases `PHASE_CALIBRATION`, `PHASE_GOOD`, `PHASE_BAD` and the thresholds `THRESHOLD_SWING = 60`, `THRESHOLD_HUM = 500`, `WARMUP_MS = 60UL * 1000`, `RR_QUIET_MS = 30UL * 1000`.
- `firmware/src/gate.cpp`: `gate_assess_quality(float raw)` runs once per sample from the main loop, accumulates min/max of the filtered signal and the raw ADC, counts lead-off pin reads (`PIN_LOP`, `PIN_LON`), and runs a Goertzel at 50 Hz (`FREQUENCY_MAINS_HZ`). Every `ECG_FS` samples it computes `swing` (peak to peak), `hum50` (mains amplitude), `swing_clean = swing - GAIN_50HZ * 2 * amp50`, `clipping`, `leadoff`, then calls `assess_contact`.
- `assess_contact` marks contact good when not lead-off (or replay), `swing_clean >= THRESHOLD_SWING` and `hum50 <= THRESHOLD_HUM`; outside calibration it moves the phase between `PHASE_GOOD` and `PHASE_BAD` and prints `kualitas: <from> -> <to>` on change.
- `gate_assess_phase(beat)` runs per detected beat: an RR outside 0.300..1.500 s or |dRR| above 0.200 s resets the calm timer. In `PHASE_CALIBRATION` the phase becomes `PHASE_GOOD` when contact has held `WARMUP_MS` and RR has been calm `RR_QUIET_MS`, or when the skip flag or replay is on, and contact is good. It beeps once (`BEEP_CALIBRATION_MS`) and prints the `kualitas: calibrating -> good` line.
- `gate_set_skip(bool)` toggles the skip flag (refused while recording through `recorder_reject`); the menu entry toggles it.
- `gate_report_calibration(beat)` prints a progress line every 5000 ms during calibration.

## grep output I already ran

```
$ grep -n "gate_\|assess_contact" firmware/src/gate.cpp | grep -E "^[0-9]+:(void|static void|const char|uint32_t|int|bool|const gate)"
28:const gate_quality_t &gate_quality(void) { return q; }
37:void gate_begin_session(void)
48:void gate_set_skip(bool on)
55:const char *gate_phase_name(void)
60:void gate_assess_phase(const ecg_beat_t &beat)
83:static void assess_contact(void)
97:void gate_report_calibration(const ecg_beat_t &beat)
114:void gate_assess_quality(float raw)
$ grep -n "THRESHOLD_SWING\|THRESHOLD_HUM\|WARMUP_MS\|RR_QUIET_MS" firmware/include/gate.h
9:constexpr int THRESHOLD_SWING = 60;
10:constexpr int THRESHOLD_HUM = 500;
12:constexpr uint32_t WARMUP_MS = 60UL * 1000;
13:constexpr uint32_t RR_QUIET_MS = 30UL * 1000;
$ grep -n "gate_assess_quality\|gate_assess_phase\|ecg_live_push\|gate_begin_session" firmware/src/main.cpp
66:    gate_begin_session();
93:        const int has_beat = dsp ? ecg_live_push(sample, &beat) : 0;
94:        if (dsp) gate_assess_quality(sample);
99:            gate_assess_phase(beat);
$ grep -n "gate_set_skip\|n_skip" firmware/src/menu.cpp
86:    gate_set_skip(!gate_skip());
89:static const char *n_skip() { return on_off(gate_skip()); }
```
