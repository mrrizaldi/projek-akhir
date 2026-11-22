# Gaps against targets (1 Nov 2026)

**Status:** active work list. Finished items are struck out of this list and
their closure is recorded in the related document (walkthrough, `model/CLAUDE.md`, the book).
**Target sources:** Chapter 1 objectives, Chapter 3 test plan
(`tab:pengujian-model`, `tab:pengujian-pipeline`), PRD
(`model/PRD_Model_Aritmia_TinyML.pdf`, DoD p. 17 and Appendix C p. 18),
`model/CLAUDE.md` §Open work, `hardware/mainboard/README.md` §Not yet
verified.
**How to scan:** `grep -rn PLACEHOLDER laporan/buku-pa/bab`, the Chapter 4
achievement and limitation tables, then match each Chapter 3 target against its
measurement method in Chapter 4.

In short: the only numeric target that has **not been measured at all** is
power consumption per mode. The rest are met with a coverage caveat (the metric
was measured differently from the plan, one repetition, one subject), or are
hardware and figure work.

## A. Targets not yet met

| # | Target | Source | Status | Blocker | Next action |
|---|---|---|---|---|---|
| A1 | Current and power per operating mode (6 levels `p0`–`p5`) | `bab3.tex` power plan; PRD Appendix C | Not measured (`bab4.tex` `\PlaceholderData` power) | Level 5 needs WiFi; the board resets every ±2.5 s during `WiFi.begin()` with the 4.x V converter | User tunes the converter to 5.0–5.1 V. Then: WiFi ON (`m`), ladder from battery without charger, `make pull-power`, fill in Chapter 4 |
| A2 | Radio current cost without sleep mode (estimate ±30 mA) | `bab4.tex` Latency item | Not measured | Same as A1 | Measured together at level 5 of the A1 ladder |
| A3 | Status of the on-device model path | Chapter 1 objective, item 2 | Partly achieved, only because of A1 | A1 | After A1: achievement table, abstract, Chapter 5 |
| A4 | Inference latency while WiFi/MQTT is active | `bab3.tex` `tab:pengujian-model` | Measured 26.6 ms without radio | None (board over USB is enough) | Re-measure inference latency with WiFi ON over USB |
| A5 | p95 latency (reference ≤ 2,000 ms, not a target) | `bab4.tex` `tab:target-pipeline` | 1,404 / 3,304 / 2,251 ms in three repetitions | WiFi channel contention (suspected) | Repeat on an uncrowded access point, more repetitions |

## B. Targets met with narrower coverage than planned

| # | Target | Chapter 3 plan | What Chapter 4 measured | To close |
|---|---|---|---|---|
| B1 | Data integrity during disconnection | WiFi forcibly cut, capacity ±4–7 hours | Broker frozen for 24 s once, queue configuration 64 | Repeat with a real WiFi disconnection on the 27,000-entry ring, packet size 50 |
| B2 | Buffer fill | Entries counted during streaming and disconnection | Installed capacity; filled 43 of 27,000 (0.16%) | Part of B1, with a long backlog |
| B3 | Flush time | From recovery until the buffer is empty | ≤ 24.6 s with a small packet size | Part of B1 |
| B4 | End-to-end latency | Mean, until the dashboard shows it | Median, until the row can be read from the REST API (±100 ms) | Enough to state explicitly in Chapter 4 as a metric change with the reason |
| B5 | Pipeline with a healthy subject | Body signal sent over MQTT | All sending done with a replay signal | One body-signal session with WiFi ON (after A1 or over USB without a charger) |
| B6 | Calibration gate: transition on good contact | Contact 60 s + calm R-R 30 s | Observed on the screen with a power bank supply, no serial log | One test over USB with the laptop charger unplugged, save the log `calibrating -> good` and `good -> poor` |
| B7 | C and Python equivalence | Reference data | One 6.67 s excerpt of record 208 without class S | Optional: a second reference data set containing S beats |
| B8 | Preprocessing load at window 256 | `tab:parameter-eksperimen` row d | 82 µs and 33.4 ms measured at window 250 | Re-measure the load with the current firmware (device only) |
| B9 | Human observation test (sound, screen, buttons) | `bab3.tex` hardware plan | Judged through the menu, results not stored | Record the device test results to a file |

## C. PRD targets not mentioned in Chapter 4

| # | PRD target | Condition | Proposal |
|---|---|---|---|
| C1 | INT8 model < 20 KB (PRD p. 3, 16, 17) | 22.94 KB; the 25 KB limit was approved by the user (`model/CLAUDE.md` decision "Batas ukuran model") | State in Chapter 4 that the limit was relaxed, with the reason (deploy variant) |
| C2 | Window of 250 samples (PRD p. 5) | 256 through a three-seed ablation | Already covered by the Chapter 4 ablation, no action needed |
| C3 | Pan-Tompkins sensitivity > 99% on record 100 (PRD p. 9) | Chapter 4 reports 13/13 in the first 10 s and 0.9469 on DS2 | Run `bench_pantompkins.py 100` and report the figure for all of record 100 |
| C4 | Reproducible with a locked seed (PRD DoD) | Not met: F1 0.6911 vs 0.6535 on identical runs (oneDNN) | Write it as a limitation in Chapter 4 |

## D. Hardware and figures

| # | Work | Who | Notes |
|---|---|---|---|
| D1 | Physical check of PCB rev2: DevKit header spacing, module pin order, mechanical clearance, D1→VSYS trace, battery connector, switch lamp voltage | User | `hardware/mainboard/README.md` §Not yet verified |
| D2 | Hardware table, assembly photos, wearable suggestions in Chapter 4/5 | User + Claude | After the PCB is printed |
| D3 | 12 placeholder figures (9 in Chapter 3, 3 in Chapter 4) | User | `laporan/buku-pa/gambar/daftar-placeholder.md`. `fig:4-bufer` is a data plot, a decision is needed on whether its plot script gets written |
| D4 | ThingsBoard alarm rules and the `ecg_snippet` widget | Claude | Both are stated as not existing in Chapter 3/4; optional |

## E. Stale book content in `buku-pa`

User decision 1 Nov 2026: `buku-pa` (the full book) is left as it is. The
stage 1 book `progres-pa-1` is already free of INA219 and the power supply, so
E1–E3 do not appear there. The sentence "waktu stabil" (stable time) in the
Chapter 3 menu paragraph of `buku-pa` is also left alone (it has been fixed in
`progres-pa-1`). These items are done when `buku-pa` is prepared for the next stage.


| # | Location | Current content | Fact | Proposal |
|---|---|---|---|---|
| E1 | `bab4.tex` Power Consumption item (line ±866) | Board still powered over USB and the INA219 input pin floating | INA219 is already on the battery path: `model/artifacts/metrics/daya/20261014-1629-board-003.csv` (3.69 V, ±137 mA, mode 0) | Blocker = the WiFi level waits for the 5 V converter; the 14 Oct figure is not used because the charger is suspected to have been plugged in |
| E2 | `bab4.tex` model path analysis (line ±1082) | "INA219 belum dirakit pada jalur catu baterai" (INA219 not yet assembled on the battery supply path) | Same as E1 | Same as E1 |
| E3 | `bab5.tex` Suggestion 1 (line ±38) | "INA219 perlu dirakit pada sisi baterai" (INA219 needs to be assembled on the battery side) | Same as E1 | Replace the suggestion: tune the converter to 5 V, then run the ladder |

## F. Open firmware findings

| # | Finding | Next step |
|---|---|---|
| F1 | Recording starts by itself shortly after the board is plugged into USB (22 and 23 Oct) | Print the trigger source in `recorder_toggle()` (button B3 / serial `r`), then replug several times |
| F2 | The recording session is lost if power is cut before `SIMPAN`; the live path loses ±4.7 s per part while saving | Recorded in `firmware/README.md` §Deliberate limits. Root cause: the acquisition ISR is not IRAM-safe. Worked on only if requested |
| F3 | Peak queue rose from 12 → 21 samples (`bab4.tex` live flow item) | Trace with a per-stage queue fill counter |
| F4 | The 200 ms refractory period as the cause of S sensitivity 0.6494 | Ablate the refractory period with `model/scripts/eval_detected_segmentation.py` |

## Suggested order

1. A1 (5 V converter by the user) unlocks A1–A3, B5, and the ThingsBoard test from battery.
2. B6 and A4 can be done now over USB, without waiting for the converter.
3. E1–E3 as soon as permission to edit the book is given.
4. C1, C3, C4 are small additions to Chapter 4 that close the gap against the PRD.
5. D1–D3 run in parallel by the user.
