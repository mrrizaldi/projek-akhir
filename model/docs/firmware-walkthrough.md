# Walkthrough `firmware/`: port to the ESP32-S3

> **Scope:** porting preprocessing, R detection, and INT8 inference to the ESP32-S3, along with the golden harness that keeps C↔Python equivalence.
> **Related code:** `firmware/src/ecg_pipeline.cpp`, `firmware/src/ecg_live.cpp`, `firmware/src/main.cpp`, `firmware/src/acquisition.cpp`, `firmware/src/buttons.cpp`, `firmware/src/menu.cpp`, `firmware/src/power.cpp`, `firmware/src/board.cpp`, `firmware/include/board.h`, `firmware/include/ecg_preproc.h`, `firmware/include/model_int8.h`, `firmware/test/golden_ref.h`, `firmware/platformio.ini`
> **Prerequisite:** [`quantize-walkthrough.md`](quantize-walkthrough.md) (Phase 7)

A study document, not a specification. This is the hardware path in PRD Appendix C.

Reproduction:

```
cd firmware
pio test -e native      # preprocessing, INA219, payload & MQTT ring on the PC, no board
pio test -e esp32-s3    # preprocessing, inference, and PCB peripherals on the real board
pio run                 # build the main firmware (env esp32-s3)
```

`platformio.ini` contains two envs:

| Env | Content | Used for |
|---|---|---|
| `esp32-s3` | `main.cpp` + the entire pipeline + MQTT + PCB devices (TFT, buzzer, buttons, INA219) | the main firmware (the `pio run` default) and tests on the board |
| `native` | pure modules without Arduino | `pio test -e native` on the PC |

---

## 0. The big picture

```
model/src/preprocessing.py  ─┐  golden reference (Python)
model/src/features_rr.py    ─┤
                             ▼
              scripts/export_golden.py
                             │
        ┌────────────────────┴────────────────────┐
        ▼                                         ▼
firmware/include/ecg_preproc.h          firmware/test/golden_ref.h
  SOS coefficients, constants             signal + result of each stage
        │                                         │
        ▼                                         ▼
firmware/src/ecg_pipeline.cpp  ──── tested by ──── test_preproc/
        │                                          test_inference/
        ▼                                              ▲
firmware/include/model_int8.h ─────────────────────────┘
  (from model/scripts/export_model_h.py)
```

Its single rule: **Python is the truth.** If C and Python differ,
C is wrong, until proven otherwise with numbers.

---

## 1. Why a golden reference is needed

The biggest risk of the hardware path is not code that crashes, but **train/deploy
mismatch**: the filter in C differs slightly from the one used in training, the distribution of the window
entering the model shifts, and accuracy collapses **without a single
error**. The device stays on, the LED still blinks, numbers still come out.

That is why the test vectors are written **before** the C code. If made afterward, the temptation
is to tune the tolerance until the already-written code passes, which is
justification, not verification.

`golden_ref.h` contains record 208 (DS1), the first 2,400 samples:
`golden_raw` → `golden_filtered` → `golden_window` → `golden_rr` →
`golden_prob_int8`. Nine beats: N, F, V, N, V, V, N, V, V.

The GENERATED header contains no comments; its content is read from here:

| Symbol | Meaning |
|---|---|
| `ECG_N_RR` | Defined in `model_int8.h` and `ecg_preproc.h`, both behind `#ifndef` so they do not collide |
| `ECG_N_RR_BASE`, `ECG_RR_RATIO`, `ECG_QRSW` | The shape of the rhythm features (Phase D): the RR column count only (without QRSw/HOS) and the knobs `PA_RR_RATIO`/`PA_QRSW` |
| `ECG_R_IN_WINDOW`, `ECG_QRSW_SEARCH` | The R position in the window (`WIN_PRE` + group delay) and the ±4 peak-search tolerance for `ecg_qrs_width()` |
| `ECG_PT_OFFSET`, `ECG_PT_REFINE`, `ECG_GROUP_DELAY` | R-peak alignment, mandatory order `r - ECG_PT_OFFSET` → peak within ±`ECG_PT_REFINE` → `- ECG_GROUP_DELAY` (§2 `ecg_align_r`) |
| `ecg_sos`, `ECG_N_SOS` | Butterworth 0.5-40 Hz order 4, `{b0, b1, b2, a0, a1, a2}` per row; causal, the +4 sample group delay is left in place |
| `ECG_IN_*_SCALE/ZERO`, `ECG_OUT_*` | Affine quantization: `q = round(x / scale) + zero_point`, `x = (q - zero_point) * scale` |
| `GOLDEN_RR_FIRST` | Beats 0 & 1 have no RR_prev/dRR: the `golden_rr` rows and their probabilities are 0, do not test them. RR is computed from the R-peaks of this excerpt only, not the whole record, because C only has the beats that are in the excerpt |
| `GOLDEN_RR_LAST` | 1 if `PA_RR_RATIO` is active: the last beat needs a next beat that is not in the excerpt |
| `GOLDEN_TOL_*` | float32 vs float64 tolerance (§3) |
| `golden_rr` | Per beat: RR_prev, RR_ratio, dRR |
| `golden_r_detection` | Pan-Tompkins R-peaks over `golden_filtered`, RAW indices (not yet compensated/aligned) |

`export_golden.py` asserts that filtering the 2,400-sample excerpt is identical
to filtering the whole signal and then cutting it (a causal filter), so the test vectors
stand on their own.

---

## 2. Three functions in `ecg_pipeline.cpp`

### `ecg_bandpass`: a cascade of 4 biquads, transposed direct-form II

```c
float y = c[0]*x + s[0];          // b0*x + state0
s[0] = c[1]*x - c[4]*y + s[1];    // b1*x - a1*y + state1
s[1] = c[2]*x - c[5]*y;           // b2*x - a2*y
x = y;                            // feed the next section
```

`ecg_sos` is stored `{b0,b1,b2,a0,a1,a2}` per row; `a0` is always 1 (scipy already
normalized it), so its index is skipped: `a1` is in column 4, not 3.

**The `state` belongs to the caller, not the function.** That is what lets the filter be called
per chunk of samples without changing the result, which is the actual working condition, because the ADC
delivers samples flowing, never 2,400 at once.

### `ecg_window_zscore`: divisor N, not N−1

```c
const double std_pop = sqrt(squares / ECG_WIN_LEN_);
```

numpy `std()` defaults to the divisor $N$ (population). Using $N-1$ (sample)
gives a difference of ~0.2%, which slips past the eye and is caught by the tolerance.

### `ecg_rr_features`: a causal window that shrinks

```c
const size_t start = (j >= ECG_RR_LOCAL_WINDOW - 1) ? j - (ECG_RR_LOCAL_WINDOW - 1) : 0;
```

`ECG_RR_LOCAL_WINDOW` is *generated* from `config.py`, `10` is not written here.
If one day the number is changed in Python and C is still 10, nothing crashes:
Python and C just silently compute different rhythms.

### `ecg_detect_r`: Pan-Tompkins, five stages

```c
pt_bandpass(filtered, scratch, n);        // 5-15 Hz, 2 biquads, causal
pt_derivative(scratch, n);                // (x[i] + 2x[i-1] - 2x[i-3] - x[i-4]) * fs/8
for (...) scratch[i] *= scratch[i];       // square
pt_mwi(scratch, n);                       // 54-sample moving average (150 ms)
// then adaptive threshold + 200 ms refractory period
```

`scratch` is provided by the caller (n floats): **no dynamic allocation**, a reasonable requirement
on an MCU and one that also makes its memory use visible at the call site.

Two details that are easy to get wrong when porting:

- **The MWI accumulator uses `double`.** The moving average adds and
  subtracts hundreds of thousands of times; with `float` the error accumulates until the adaptive
  threshold shifts too.
- **The derivative kernel is shifted by 2 samples** to be causal (its original form needs
  `x[i+1]`, `x[i+2]`). That shift is part of the contract, not a correction.

The C detection matches Python on 11 of 11 peaks in `golden_raw`.

### `ecg_align_r`: three corrections that must not be missed

```c
int lo = r_coarse - ECG_PT_OFFSET;                   // 38: median delay (DS1 calibration)
int peak = argmax(filtered, lo - 25 .. lo + 25);     // the actual R peak
return peak - ECG_GROUP_DELAY;                       // 4: causal bandpass shift
```

The result puts R at index **94** in the window, the same as the training window.
A miss of 4 samples in either direction and precision falls from 0.479 to 0.124;
the number was measured in [Phase 6b](detection-segmentation-walkthrough.md) §2.

The test `test_align_r_puts_peak_at_r_idx` guards it as a property, not
as a number: it cuts the window from the `ecg_align_r` result and then makes sure
the peak lands at `R_IDX = ECG_WIN_PRE + ECG_GROUP_DELAY`. Its search
is limited to ±20 around `R_IDX`; a global `argmax` cannot be used because
record 208 has closely spaced beats (697 → 853) so a window this wide often
contains a taller neighboring R.

The principle: **a test that guards a property must write down the property, not the result of
its computation.** An R index written as a literal number in more than one
place will be left behind when the window changes, and the test fails with a message that
accuses the firmware.

---

## 3. Tolerance: float32 vs float64, and why it does not spread

The golden is computed by scipy with float64; the device is float32 (the ESP32-S3 FPU is only
single-precision, `double` is emulated in software and slow). In a **recursive IIR**
filter, that precision difference accumulates:

```
selisih terukur pada tahap bandpass: 2,09e-4  (amplitudo ~0,4)
```

Not a bug: what is forbidden is a **systematic** difference: an index shift, swapped coefficients,
`a0` being read in. That is why the tolerance is not simply loosened;
`test_pipeline_whole` runs raw → bandpass → z-score entirely in C
then compares to the golden window, and passes.

The reason is elegant: **the z-score divides by the standard deviation**, so a shift
experienced by the whole window together gets normalized too. A Phase 1 decision
taken for cross-patient immunity also gives precision tolerance on the
device.

---

## 4. `test_bandpass_streaming`: a test with no counterpart in Python

```c
const size_t block = 64;
for (size_t i = 0; i < GOLDEN_N; i += block) {
    size_t n = (i + block <= GOLDEN_N) ? block : (GOLDEN_N - i);
    ecg_bandpass(golden_raw + i, buf_filtered + i, n, state);
}
```

Called per block of 64 samples, the result must equal a single run of 2,400
samples. If the biquad `state` does not persist across calls, the single test stays
green and this one goes red. This bug is impossible to detect from the Python side, because in
Python the signal is always available whole.

---

## 5. The TFLite Micro trap: the same op, a different result

This is the biggest trap of the hardware path, and almost entirely invisible without the
harness.

### Symptom

The model, weights, input, and quantization parameters are identical. The result is not:

```
beat 2 (V):  PC 0,9727   device 0,3359
beat 3 (N):  PC 0,0039   device 0,0391
```

Everything is pushed toward the middle: the model still ranks correctly, but its confidence
collapses. At a threshold of 0.35, an arrhythmia beat turns into "normal".

### Investigation

| Step | Result | Conclusion |
|---|---|---|
| Feed the **golden** window & RR directly | still off | not its C port |
| Compare the device vs header quantization parameters | identical | not a wrong scale/zero |
| PC with the reference kernel (not XNNPACK) | 0.969 | the PC is consistent, the device deviates |
| **Swap the TFLM library** (Chirale → tanakamasayuki) | **the identical wrong numbers** | not a bug in one library: a property of TFLM |

Two independent implementations agree on the wrong number. That is what kills
the "library bug" hypothesis and points to the **op**.

### Cause

`GlobalAveragePooling1D` becomes the `MEAN` op, and TFLM computes it differently from
regular TFLite. The solution is to change how that average is **written**, not
to change the model.

### Four ways to write the average, and why three are rejected

| Average written as | Size | On PC | On device |
|---|---|---|---|
| `MEAN` (training model) | 17.8 KB | 0.973 | **0.336** (wrong) |
| `AVERAGE_POOL_2D` | 20.8 KB | 0.945 | 0.945 (matches), but **recall DS2 0.528** |
| `AVERAGE_POOL_2D` + `Flatten` | 19.4 KB | 0.945 | **0.418** (wrong) |
| **`DEPTHWISE_CONV_2D` weights 1/31** | 22.9 KB | 0.973 | **0.973** (used) |

**Why pooling fails even though its result is "correct":** a pooling op **inherits the
quantization scale of its input** (0.332 here), whereas a convolution op gets its
**own output scale** (0.0429, exactly what `MEAN` chose). The average of 31 values is
much smaller than the input range, so pooling throws away ~3 bits of resolution.
On 6 test beats it is almost invisible; on the 49,654 DS2 beats, recall falls from 0.655
to 0.528.

**Why `Flatten` fails:** it brings in `SHAPE`, `PACK`, `STRIDED_SLICE`,
dynamic-shape ops, and TFLM has no dynamic allocation.

**Why DepthwiseConv1D works:** a convolution with the kernel $[\frac{1}{31},
\dots]$ mathematically *is* an average (identical down to 1.19e-07 in
float32), but it is a convolution op: it gets its own output scale, and
`DEPTHWISE_CONV_2D` is among the most mature kernels in TFLM.

This lives as `build_deploy_model()` in `model/src/model.py`: the training model goes in,
a variant comes out with the weights copied as is. **No retraining.**

---

## 5b. The live flow (`ecg_live.cpp`)

It combines everything already verified into one path: ADC samples come in
one by one, a ready-to-classify beat comes out.

```c
int ecg_live_push(float sample_raw, ecg_beat_t *beat);
```

Inside it:

```
raw sample
   → ecg_bandpass (state persists)  → 4-second ring
   → every 1 second: ecg_detect_r over the whole ring
   → ecg_align_r  (R lands at ECG_WIN_PRE + ECG_GROUP_DELAY = 132)
   → ecg_window_zscore + ecg_rr_features
   → beat out
```

**Inference is deliberately NOT inside this module.** The caller runs it
so that `ecg_live` can be tested in `pio test -e native` without TFLite Micro at
all, and that separates flow logic bugs from inference bugs.

The first two beats of each session never come out: they do not have `RR_prev`/`dRR` yet,
exactly the same rule as `valid_beat_indices` in `prep_beats.py`.

### Tested without electrodes

`golden_raw` is replayed sample by sample as if it came from a 360 Hz ADC.
Because the answer is already known, the whole chain can be verified:

```
beat keluar   : 6 (6 cocok anotasi, 6 prediksi benar)
  r= 697 (F) p=0.9961 -> 1   r=1378 (V) p=0.9922 -> 1
  r= 853 (V) p=0.9805 -> 1   r=1579 (V) p=0.9805 -> 1
  r=1181 (N) p=0.0039 -> 0   r=1860 (N) p=0.0117 -> 0
```

This replay mode is not a temporary tool. Even with electrodes attached, it is
the only way to test the firmware **deterministically**: a body signal
is never the same twice, so a change in results cannot be told apart as "the code
changed" or "the heart is different". It also separates two kinds of failure: if
the replay is correct but the real signal is a mess, the problem is in acquisition/analog.

### The load is bursty, and that determines the firmware architecture

```
rata-rata    :     82 us/sampel dari anggaran 2778 us  → beban 3,0%
puncak burst : 33.428 us (deteksi 4 detik + inferensi bersamaan)
antrean min  : 13 sampel
```

The average is very loose, but **the peak is 12× the budget of a single sample**. If
acquisition and processing run in a single sequential flow, 12 samples would be lost
each time detection runs, and lost samples corrupt the RR interval, the feature
that most determines class S.

The consequence for the production firmware: **the ADC must be fed by a timer ISR into a
queue**, and `ecg_live_push` drains that queue in the main loop. A burst only
piles up ~13 samples temporarily, then drains because the average load is 3%.

What the test asserts is not the peak but the average; the peak is reported
so the queue can be sized with a number, not a guess.

---

## 5c. The production firmware (`main.cpp`)

```
360 Hz timer ISR ──► 256-sample queue ──► main loop
   adc1_get_raw()                             ├─ ecg_live_push + gate_assess_quality
   (or rp_data[] during replay)               ├─ gate_assess_phase (calibration gate)
                                              ├─ inference per beat (monitoring phase)
                                              ├─ publish → MQTT backlog ring
                                              ├─ ecg_mqtt_service (non-blocking)
                                              ├─ signal quality LED (blue/orange/green)
                                              ├─ TFT: HR, INA219 ⇄ clock, REC/PAUSE/replay, waveform
                                              ├─ buzzer: beep per beat (scheduled, silent during calibration)
                                              ├─ buttons B1/B2/B3: monitor (mute, freeze, record/pause; long B3 saves) / menu
                                              └─ on-screen menu (when open)
```

The PCB rev1 pin map and the device installation order are in
`firmware/include/board.h` and `firmware/src/board.cpp`, used
jointly by `main.cpp` and the `test_hw_*` device tests. The pin table is in
[acquisition](../../docs/features/acquisition.md); the button map and menu tree
are in [buttons-and-menu](../../docs/features/buttons-and-menu.md).

The meaning of the LED and the recording procedure are in
[`acquisition-walkthrough.md`](acquisition-walkthrough.md) §2–3; the calibration gate and
publishing are in [`mqtt-walkthrough.md`](mqtt-walkthrough.md) §3.

**The ADC is read INSIDE the ISR, not in the loop.** This is a direct consequence of the
§5b finding: the load clumps up to 33 ms. If the ISR only raises a flag and the
loop reads the ADC, the samples are still read, but **late**, because the ADC
takes the value when it is read, not when it should have been. Timing jitter of the size of that burst
goes straight into the RR interval.

`adc1_get_raw()` is used, not `analogRead()`: the latter carries locking
and is not safe to call from an ISR.

A queue of 256 samples (0.7 seconds): far above the 13 needed, but cheap
(512 bytes) and gives room for WiFi/MQTT, which also uses loop time. This limit of
711 ms is what bounds every network operation in `ecg_mqtt.cpp`
([`mqtt-walkthrough.md`](mqtt-walkthrough.md) §7b).
`n_lewat` counts the samples lost when the queue is full; the number **must
stay 0**, and is also saved to the recording file.

### Buttons and menu: the screen changes, the processing does not

`buttons.cpp` only produces per-button events: `TEKAN` (press), `PENDEK` (released
before 800 ms), `LAMA` (still held when 800 ms is reached, without waiting for
release), and `LEPAS` (release). The meaning of the events is assembled by the caller: `main.cpp` for monitor
mode (short B1 mute, short B2 freeze, short B3 record, long B2 open menu),
and `menu.cpp` while the menu is open (short B3/B1 up/down, long B2 select,
short B2 back, long B1/B3 straight to monitor). Short actions happen on
release because the same press could continue into a long press.

The menu is not a separate mode. `loop()` still drains the queue, runs
`ecg_live`, inference, recording, and MQTT on every iteration; all that changes is
who uses the screen (`display_set_monitor(false)`) and who
receives button events. The waveform is not drawn while the menu is open, but
the beat beep is still scheduled and the NeoPixel still follows the phase.

As a consequence, every menu drawing runs in the same `loop()` as
the queue draining and blocks it while drawing. The limit is the
ISR queue depth, 256 samples = **711 ms**. The menu tree is an array of static
structs; `display_menu_row()` remembers the content of each row and only redraws
rows that changed, so moving the highlight touches only two rows.

Measured on the board (13 Oct 2026):

| Operation | Time |
|---|---|
| Full menu frame (title, six rows, hint) | ±200 ms |
| Moving the highlight (two rows) | ±36 ms |
| ISR queue depth | 711 ms |
| Samples lost during navigation | 0 |

Text pages (Status, Info) are recomputed once per second with the same rule:
rows whose content has not changed are not drawn. The exception that blocks
longer than 711 ms is the Tes perangkat (device tests) menu (sound, screen pattern ±2 seconds,
wait for a button up to 10 seconds); during a test, the acquisition timer is stopped so
no samples are counted as lost, and the queue does not overflow.

Navigation can be tested without a finger: serial `t1`–`t3` injects a short press and
`T1`–`T3` a long press, and every menu movement prints
`menu: <judul> [i/n] <baris>`.

### Measured on the board (no electrodes, the ADC reads noise)

Test conditions: the core build without the MQTT module and without the replay table.

```
RAM   21,2% (69.404 B)    Flash 6,4% (419.209 B)
antrean saat burst: 12 sampel      sampel hilang: 0
```

A queue of 12 when checked in the middle of a burst: matching the 13 computed from the
§5b measurement.

### Three signal sources (the Sumber sinyal menu)

The source is chosen from the **Sumber sinyal** (Signal source) menu and stored in NVS so it stays
in effect after boot:

| Source | ISR queue content | Purpose |
|---|---|---|
| Sensor (ADC) | `adc1_get_raw()` from the AD8232 | operation and body signal recording |
| REPLAY 208 | `golden_raw` of record 208 (2400 samples, 9 beats), played repeatedly | identical load for power measurement, MQTT tests without electrodes |
| Replay rekaman (recording replay) | the file `/rekam/NNN.csv` loaded into PSRAM (max. 300 seconds), played repeatedly | replaying a body signal that was once recorded through the production path; `#` lines (header, `# jeda`) are skipped so segments play back to back |

During replay, the top right corner of the monitor screen shows `RP 208` (reference) or
`RP#NNN` (recording) in yellow. Serial `y` remains as a fallback path:
ADC ⇄ reference replay. Both replays
use a single branch in the ISR that reads whichever array `rp_data` points to:

```cpp
if (rp_data) {
    queue[write_index] = rp_data[replay_i];      // integers only: golden converted once in acquisition_begin()
    if (++replay_i >= rp_n) replay_i = 0;
} else {
    queue[write_index] = (uint16_t)adc1_get_raw(CHANNEL_ECG);
}
```

Loading a recording file blocks `loop()` (it reads LittleFS); during that time the timer
is stopped so no lost samples are recorded. PSRAM is safe to read in this ISR
because the ISR is not installed with `ESP_INTR_FLAG_IRAM`, so it is
held off while flash is being written.

A single branch in the ISR, and **the whole path downstream does not change**: bandpass,
detection, alignment, inference, LED, REC, and MQTT all run as
usual. If the simulation has its own path, what is validated is not the production
path.

The scale is free (the bandpass removes DC, the z-score removes scale); what is forbidden is only
clipping at the rail. 1000 counts/mV puts the R peak (~1.5 mV) at ~3550.

Two uses, and the second is actually the more important:

1. **An identical workload each repetition**, a requirement for measuring power per mode (HW-7).
   Without a signal, there are no beats, and the inference mode measures zero work.
2. **The number of beats that SHOULD come out is known exactly.** That is what
   lets data loss on the MQTT path be measured, not just felt:
   lost beats = expected beats − beats that reach the broker. Every change of
   source (menu or `y`) resets `ecg_live` and the beat counter so that
   the count starts from zero. During replay (reference or recording), the
   warm-up and calm-RR conditions of the calibration gate are skipped; that bypass is derived
   from the signal source so it stops together with the replay
   ([`mqtt-walkthrough.md`](mqtt-walkthrough.md) §3.1b).

The consequence: pipeline resilience tests do not need to wait for electrodes.

#### TRAP (JEBAKAN): float inside an ISR kills the board, slowly

Multiplying directly in `on_timer()` looks reasonable:

```cpp
float v = golden_raw[replay_i] * SCALE_REPLAY + OFFSET_REPLAY;   // WRONG
```

That code builds cleanly and runs for about 20 seconds, then:

```
Guru Meditation Error: Core 1 panic'ed (Coprocessor exception).
EXCCAUSE: 0x00000004
Rebooting...
```

The ESP32 **does not save the FPU registers on ISR entry**. A float operation there
corrupts the FPU state of the task being interrupted, and the panic only appears when
that task is scheduled again, so it is **not an immediate crash**, which lets it slip through
short tests. Measured: panic at second 18.49.

The remedy is a one-time conversion in `acquisition_begin()` (called by `setup()`) into
`static uint16_t sim_counts[GOLDEN_N]` (4,800 bytes), and the ISR just copies
integers. The cost is RAM 21.2% → 22.7%.

The derived symptom is more dangerous than the crash itself: the board silently reboots,
`replay` goes back to `false`, and the next measurement reports **a plausible
number but of the wrong object**: 2 beats/second from ADC noise, not from the replay.

#### Measured on the board

Test conditions: board N16R8, 18 Sep 2026, no electrodes, replay ON.

```
periode putaran : 11 beat / 6,67 detik golden  (1,58 beat/detik)
p per putaran   : 0,984 0,996 0,019 0,996 0,988 0,078 0,992 0,996 0,500 0,988 0,078
                  → 7 ARITMIA + 4 normal, sama persis tiap putaran
sampel hilang   : 0        antrean puncak: 21 dari 256
mentah          : 1168..3618 counts (ayun 2720) — sesuai 1000 c/mV + 2048
```

The golden has **9 annotated beats**, and the device emits **11**. The two extra are an
artifact of the **loop seam**: the last sample connects to the first sample, and
that discontinuity looks like a QRS to the detector. One of them comes out
with exactly `p = 0,500`: the model cannot decide either. For MQTT
accounting, **11 beats per loop** is used, not 9: what is counted is what
the device sends, not what is in the annotations.

#### Without electrodes and without replay, this device invents arrhythmia

With a floating ADC input (no electrodes, replay OFF), the firmware
emits **~2 beats/second, 57% classified as ARRHYTHMIA**. Small
noise (swing 15 counts) still has peaks, and an adaptive-threshold Pan-Tompkins
always finds something: its threshold is relative to the signal that exists, so
"no signal" is not a condition it recognizes.

That is why MQTT publishing is gated by the signal quality assessor (`THRESHOLD_SWING`)
and the calibration phase, not by whether a beat exists
([`mqtt-walkthrough.md`](mqtt-walkthrough.md) §3.1). Without that gate,
detached electrodes = a flood of false alarms to the broker.

### A small trap: BPM from `millis()`

Computing BPM from the time difference between prints produces "2000 bpm", because beats come out **in clusters**: detection runs once per
second and then emits several beats at once. The time gap between prints is not
the gap between beats. BPM must be computed from `beat.rr[0]`, the only source
that actually measures the heart interval.

---

## 5d. The power measurement ladder

Consumption is separated per stage through mode isolation: each rung adds one
load, and the cost of one stage is the difference between two rungs. One rung is
chosen via serial `p0`–`p5`; `p` followed by another letter (e.g. `px`) returns to
normal operation. The whole ladder is run in two ways: from the laptop
(`measure_power.py`, below) or by the board itself (the standalone ladder, the menu
**Ukur daya** (Measure power) or serial `V`).

| Mode | What runs | The isolated cost |
|---|---|---|
| `p0` | timer ISR off, WiFi radio off, LED off | the base: ESP32-S3 + AD8232 + TFT (backlight) + regulator |
| `p1` | + the 360 Hz ISR and queue draining | acquisition |
| `p2` | + `ecg_live_push()` and the quality assessor | DSP: bandpass, R detection, segmentation |
| `p3` | + per-beat CNN inference | TinyML |
| `p4` | + TFT waveform, beep, LED | interface |
| `p5` | + WiFi radio (`setSleep(false)`) and MQTT publishing | radio = normal operation |

The 1 Hz TFT text, buttons, and INA219 reading run in all modes so
their cost cancels in the differences. The signal source must be replay: without a signal there are
no beats, and `p3` would measure zero inference. The radio is turned off with
`esp_wifi_stop()`, not `WiFi.mode(WIFI_OFF)`; the latter also de-inits the
driver and races with the WiFi task, the symptom being a `LoadProhibited` panic on core 0.

While the measurement mode is active, the INA219 is read every 100 ms (longer than the conversion
average of 128 samples, ~68 ms) and averaged per 10-second window. One
line per window:

```
DAYA p3 n=101 I=<mA> sd=<mA> mA V=<V> P=<mW> mW beat=17 lewat=0 replay=1
```

`sd` is the standard deviation of the 100 ms readings within the window, `beat` the number of beats
that came out of `ecg_live` in that window (proof the DSP load is running), and
`lewat` the lost samples (must be 0). The INA219 uses PGA ÷8 (`0x3FFF`,
±320 mV = ±3.2 A at 0.1 ohm) because WiFi TX bursts exceed the ±400 mA of
PGA ÷1; the shunt register LSB stays 10 µV.

`model/scripts/measure_power.py` runs the ladder: reading the `s` status,
turning on replay if it is not yet on, sending each mode, discarding the first window
(mode-change transient), taking 6 windows (60 seconds) per mode, writing a CSV to
`model/artifacts/metrics/daya/<ts>.csv`, then printing the mean ± std per mode
and the difference between modes. Mechanical checks: current rises monotonically `p0 ≤ … ≤ p5`, each
difference > 2 × std, `lewat = 0`, and `beat > 0` from `p2`. The script stops without
writing a CSV if the bus voltage is < 1 V, i.e. if the INA219 is not in the device's
current path.

Interpretation note: `loop()` never sleeps, so the 240 MHz CPU is fully active in
all modes. The `p1`–`p3` difference is the cost of additional instructions on a CPU that
is already active, and can sink below 2 × std; the script check reports it
as a stage not yet measured, not as a number.

### Design rationale

- **Modes via serial command, not a build flag.** Reflashing between modes
  changes the board's thermal condition and adds an uncontrolled variable.
- **`p2` is one DSP block.** `ecg_live_push()` does the bandpass, detection, and
  segmentation behind one door (`firmware/include/ecg_live.h`); separating
  bandpass from detection means dismantling a module that is already verified by the
  golden.
- **No INA219 library.** `Wire` is already in the Arduino framework, and
  a new dependency is a gate point. The formulas in `ina219.cpp`:
  `I [mA] = Vshunt_reg × 0,01 / R_SHUNT`, `V [V] = (Vbus_reg >> 3) × 0,004`.
- **The INA219 quiescent current is counted.** The module VCC is taken from the board 3V3 (load
  side), so its quiescent current (±1 mA) is in all modes: it cancels in the
  differences between modes, and is stated openly when the absolute number is reported.
- **I2C on GPIO 17/18.** Both are ADC2 pins, which go completely dead as soon as WiFi is on
  (acquisition-walkthrough §1). Using them for I2C sacrifices nothing,
  whereas GPIO 1–10 are ADC1, which is still needed.
- **The shunt on the positive side (high-side).** A shunt on the GND line raises the
  board's ground reference relative to the laptop ground; the USB data line and the AD8232
  ADC reading shift too, even though that signal is exactly what the consumption is
  measuring. The INA219 is designed for high-side (common-mode up to 26 V).
- **A multimeter cross-check is mandatory.** The shunt calibration can drift with no sign
  at all; comparison with a multimeter (procedure step 6) is the only
  defense, and `R_SHUNT` is the only constant that is corrected.
- **The assert `Σ selisih = p3 − p0` is not used.** That equation is telescoping,
  always algebraically true whatever the numbers; that check can never
  fail. The two checks used (monotonic and difference > 2 × std) can fail, and
  their failures point to different causes: monotonic failing = mode gating leaks;
  a sunk difference = that stage is not yet measured.

The oscilloscope or GPIO marker alternative is not used because its transient results
are hard to turn into a table of averages. The alternative of logging current with timestamps
then matching it offline is not used because it demands time synchronization
and fast INA219 sampling; mode isolation gives a steady-state average with
less work.

### The current state of the measurement path

The raw INA219 registers (`pio test -e esp32-s3 -f test_hw_ina219 -v`, 13 Oct
2026, board powered from the laptop USB):

```
mentah: shunt 0x3400 (13312 x 10 uV) | bus 0x000A -> 1 x 4 mV, CNVR 1 OVF 0
mentah: shunt 0x55FF (22015 x 10 uV) | bus 0x000A -> 1 x 4 mV, CNVR 1 OVF 0
mentah: shunt 0x4FFF (20479 x 10 uV) | bus 0x0002 -> 0 x 4 mV, CNVR 1 OVF 0
```

The bus voltage (VIN− relative to GND) is 0–4 mV, while the shunt voltage jumps
133–220 mV between readings. A current of 1.3–2.2 A at a bus of 0 V cannot come from a
load; both VIN pins are floating. The INA219 is not yet in the device's current path, and the
board receives power directly from the USB connector. The current figures on screen and in the
status line in this condition are not the device's consumption. The measurement path (firmware + script) has been tested
end to end with `--force`: all six modes confirmed, `lewat = 0` in all
modes, and the radio reconnects at `p5`.

### Power measurement procedure

The INA219 is installed on the battery side: TP4056 `OUT+` → `VIN+` → `VIN−` → the input of the
DC-DC converter, whose output powers the board's 5V pin. The circuit, pin table,
and check readings: [power-measurement](../../docs/features/power-measurement.md);
what to check on the board regulator: [`firmware/README.md`](../../firmware/README.md)
section Measurements. Because the current is measured at the cell, the result already includes converter
losses and is directly usable for battery life (mAh capacity divided by current in
mA), without an efficiency conversion.

The procedure below commands the ladder from the laptop over serial. An ordinary USB cable
cannot be used during measurement, because its VBUS also powers the board and
splits current with the battery. The serial path uses a USB data cable without VBUS:
the red wire (VBUS) is cut and its end insulated, while D+, D−, and GND
stay connected.

1. Assemble the supply circuit and connect the INA219 logic pins with all supplies
   disconnected.
2. Unplug the TP4056 charger input, then power the device from the battery.
3. Connect the data cable without VBUS to the board USB port used for serial.
   Make sure the port appears (`pio device list`).
4. Type `s` in `pio device monitor`. The `INA219` line must show `V`
   3.0–4.2 V and `I` positive and stable. If not, follow the readings table in the
   README.
5. Close the serial monitor (the port must not be used by two programs), then run
   from the `model/` folder:

   ```
   .venv/bin/python scripts/measure_power.py
   ```

   Duration is about 7.5 minutes (6 modes × 70 seconds). For `p5` to represent
   normal operation, an active broker must be reachable; check with `make broker-info`
   (port 1883 `terbuka`) before starting. The bus voltage < 1 V check in the script
   still applies to the battery: the minimum cell voltage is 3.0 V so a reading below
   1 V only appears if the INA219 is not in the current path.
6. Cross-check once with a multimeter in current mode inserted at the
   same point (between TP4056 `OUT+` and the converter input) on one mode; the difference
   is corrected through `R_SHUNT` in `board.h`
   (`R_baru = R_lama × I_ina219 / I_multimeter`).
7. Repeat at several cell voltages (e.g. a full cell and a cell around 3.5 V):
   the current on the battery side rises as the cell voltage falls, because the converter
   maintains output power.

### The standalone ladder and `make pull-power`

The standalone ladder removes the need for the data cable without VBUS: the board
runs `p0`–`p5` itself from the battery, stores the result, and the laptop
pulls it after measurement is finished. Step-by-step procedure:
[power-measurement](../../docs/features/power-measurement.md).

Its content is the same as `measure_power.py`, moved to `power.cpp`:

- Each step: discard 1 transient window, take 6 windows of 10 seconds
  (`POWER_BLOCK`, `POWER_WINDOW_MS`), a total of ±7 minutes. The windows are recorded by
  the same `power_service()` as the `DAYA` line; `power_sweep_tick()` only
  moves the step so `loop()` is not held up except when writing the CSV
  at the end.
- The ADC source is moved to reference replay during the ladder and restored afterward,
  so the load is identical between repetitions.
- The menu is closed during the ladder so `p4` measures the real
  monitor screen, not a menu screen that is nearly still. The results page opens by itself
  at the end.
- The validity criteria per step are the same as the script: V bus ≥ 1 V, `lewat = 0` (from
  `p1`), `beat > 0` (from `p2`), and current rises by more than 2 × sd from the previous
  step. A failed step shows `pN!` on screen and `sah = 0` in the CSV.
  A ladder aborted midway (mode changed from outside, INA219 stops answering)
  makes all steps invalid.
- Results go to `/daya/NNN.csv`, columns `waktu,mode,n,I_mA,sd_mA,V,P_mW,beat,lewat,replay,sah`;
  `waktu` is UTC ISO if the NTP clock is synchronized, otherwise `+<detik uptime>s`.

`make pull-power` (`scripts/pull_power.py`) sends `v` for the file list,
then `v<n>` (default: the last file; `N=<n>` for others), saves to
`model/artifacts/metrics/daya/<YYYYmmdd-HHMM>-board-NNN.csv`, and repeats
validation with the `measure_power.py` criteria so that the board's and the laptop's assessments
can be compared. The script exits with code 1 if any step is INVALID (TIDAK SAH).

## 6. Device numbers

Test conditions: board N16R8, 18 Sep 2026, window 256, `pio test -e esp32-s3`.

```
inferensi     : 26,6 ms per detak (240 MHz, kernel referensi tanpa ESP-NN)
tensor arena  : 12.948 byte dari 24.576 dialokasikan
model         : 22,94 KB
heap bebas    : 312.396 byte
RAM firmware  : 74.284 byte (22,7% dari 320 KB)   build inti + 4.800 B tabel replay
Flash firmware: 430.569 byte (6,6% dari 6,25 MB)  build inti
```

The complete main firmware build (with the MQTT module and a filled `wifi_secrets.h`),
`pio run`: **RAM 37.0% (121,336 B), Flash 13.5% (887,873 B)**. The difference
from the core build is the WiFi stack, MQTT packet buffers, and the backup ring;
details in [`mqtt-walkthrough.md`](mqtt-walkthrough.md) §7.

The cost of window 256 compared with the window 250 tested as a comparison: inference
26.0 → 26.6 ms (+0.6 ms), arena 12,756 → 12,948 B, model 22.91 → 22.94 KB.
Commensurate with F1 +0.09.

One beat ~0.8 seconds, so 26 ms = **3.3% duty cycle**, loose enough for
continuous operation. If power becomes a constraint, `esp-tflite-micro` with the ESP-NN kernel
(S3-specific SIMD) can cut it several-fold; the difference is good material
for discussion in the report.

The `+119 KB flash` is the TFLM library, not the model (22.9 KB). That is why
`MicroMutableOpResolver<8>` registers exactly the 8 ops used, not
`AllOpsResolver`, which pulls in all kernels.

---

## 7. Comprehension check

1. `state` in `ecg_bandpass` is moved to a `static` variable inside the function.
   Which test stays green, and when does the bug appear on a real device?
2. Why does `AVERAGE_POOL_2D` pass the 6-beat golden test but fail on the 49,654 DS2
   beats, and what lesson is there about the size of the test set?
3. The model is retrained and then `make quantize`d, but `make export` is forgotten.
   What happens on the device, and why is there no error?
4. `resolver.AddMean()` is removed even though the deploy model no longer uses `MEAN`.
   What is the effect on flash size, and why is `AllOpsResolver` avoided?

## 8. Commands

| Command | What it shows |
|---|---|
| `pio test -e native` | 23 tests on the PC: `test_preproc` 11 (preprocessing, R detection, live flow), `test_ina219` 6, `test_mqtt` 6 |
| `pio test -e esp32-s3` | 29 tests on the board: `test_preproc` 11, `test_inference` 5, `test_hw_integration` 5, `test_hw_tft` 2, `test_hw_adc` 2, `test_hw_buttons` 2, `test_hw_buzzer` 1, `test_hw_ina219` 1 |
| `pio test -e esp32-s3 -f test_hw_buzzer` | a single suite only |
| `pio test -e esp32-s3 -v` | plus `Serial.printf` output (benchmark, DIAG, device readings) |
| `pio run` | build the main firmware (env `esp32-s3`), see RAM/Flash |
| `pio run -t upload` | flash the main firmware |
| `cd model && make export` | regenerate `model_int8.h` after the model changes |
| `cd model && .venv/bin/python scripts/measure_power.py` | the `p0`–`p5` power measurement ladder from the laptop → `artifacts/metrics/daya/<ts>.csv` (§5d) |
| `cd model && make pull-power [N=<n>]` | pull the standalone ladder result `/daya/NNN.csv` → `artifacts/metrics/daya/<YYYYmmdd-HHMM>-board-NNN.csv` (§5d) |

---

**[← Phase 7: quantize](quantize-walkthrough.md)**  ·  [Walkthrough map](README.md)  ·  **[signal acquisition →](acquisition-walkthrough.md)**
