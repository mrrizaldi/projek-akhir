---
tags: [feature-docs]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Skill, Write]
---

dokumentasikan fitur ini: the firmware has a calibration gate (`gerbang`) and there is no docs page for it yet. Write the docs.

You cannot run commands or read the repo beyond what is pasted here. Write the full new page, the exact edits to any other files, the commands you would run, and your final report. Write any command output you cannot see as [N].

Background from me: I tuned the thresholds during the bench session on 21 Okt 2026 after S02 kept starting classification with a loose electrode. In my experience the gate usually passes after about 70 seconds.

## What the code does

- `firmware/include/gerbang.h` defines the phases `FASE_KALIBRASI`, `FASE_BAIK`, `FASE_BURUK` and the thresholds `AMBANG_AYUN = 60`, `AMBANG_DENGUNG = 500`, `PEMANASAN_MS = 60UL * 1000`, `RR_TENANG_MS = 30UL * 1000`.
- `firmware/src/gerbang.cpp`: `gerbang_nilai_kualitas(float mentah)` runs once per sample from the main loop, accumulates min/max of the filtered signal and the raw ADC, counts lead-off pin reads (`PIN_LOP`, `PIN_LON`), and runs a Goertzel at 50 Hz (`FREK_JALA_HZ`). Every `ECG_FS` samples it computes `ayun` (peak to peak), `hum50` (mains amplitude), `ayun_bersih = ayun - GAIN_50HZ * 2 * amp50`, `clipping`, `lepas`, then calls `nilai_kontak`.
- `nilai_kontak` marks contact good when not lead-off (or replay), `ayun_bersih >= AMBANG_AYUN` and `hum50 <= AMBANG_DENGUNG`; outside calibration it moves the phase between `FASE_BAIK` and `FASE_BURUK` and prints `kualitas: <from> -> <to>` on change.
- `gerbang_nilai_fase(beat)` runs per detected beat: an RR outside 0.300..1.500 s or |dRR| above 0.200 s resets the calm timer. In `FASE_KALIBRASI` the phase becomes `FASE_BAIK` when contact has held `PEMANASAN_MS` and RR has been calm `RR_TENANG_MS`, or when the skip flag or replay is on, and contact is good. It beeps once (`BIP_KALIB_MS`) and prints the `kualitas: calibrating -> good` line.
- `gerbang_set_lewati(bool)` toggles the skip flag (refused while recording through `rekam_tolak`); the menu entry toggles it.
- `gerbang_lapor_kalibrasi(beat)` prints a progress line every 5000 ms during calibration.

## grep output I already ran

```
$ grep -n "gerbang_\|nilai_kontak" firmware/src/gerbang.cpp | grep -E "^[0-9]+:(void|static void|const char|uint32_t|int|bool|const gerbang)"
28:const gerbang_kualitas_t &gerbang_kualitas(void) { return q; }
37:void gerbang_mulai_sesi(void)
48:void gerbang_set_lewati(bool on)
55:const char *gerbang_nama_fase(void)
60:void gerbang_nilai_fase(const ecg_beat_t &beat)
83:static void nilai_kontak(void)
97:void gerbang_lapor_kalibrasi(const ecg_beat_t &beat)
114:void gerbang_nilai_kualitas(float mentah)
$ grep -n "AMBANG_AYUN\|AMBANG_DENGUNG\|PEMANASAN_MS\|RR_TENANG_MS" firmware/include/gerbang.h
9:constexpr int AMBANG_AYUN = 60;
10:constexpr int AMBANG_DENGUNG = 500;
12:constexpr uint32_t PEMANASAN_MS = 60UL * 1000;
13:constexpr uint32_t RR_TENANG_MS = 30UL * 1000;
$ grep -n "gerbang_nilai_kualitas\|gerbang_nilai_fase\|ecg_live_push\|gerbang_mulai_sesi" firmware/src/main.cpp
66:    gerbang_mulai_sesi();
93:        const int ada_beat = dsp ? ecg_live_push(sampel, &beat) : 0;
94:        if (dsp) gerbang_nilai_kualitas(sampel);
99:            gerbang_nilai_fase(beat);
$ grep -n "gerbang_set_lewati\|n_lewati" firmware/src/menu.cpp
86:    gerbang_set_lewati(!gerbang_lewati());
89:static const char *n_lewati() { return on_off(gerbang_lewati()); }
```
