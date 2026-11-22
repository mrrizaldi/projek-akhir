---
name: firmware-limits
description: PA repo layer for firmware that has a limit or does something slow inside loop(). Use whenever you write, edit, or review firmware/src (recorder.cpp, acquisition.cpp, display.cpp, serial_cmd.cpp) that touches a full buffer or array, RECORDER_SECONDS/RECORDER_N, the ISR queue, LittleFS or PSRAM capacity, recording file numbers, or file writes and network calls in loop(). Also for complaints like "rekaman terpotong", "sampel hilang", "buffer penuh", "loop macet", "simpan memblok", "data hilang", "rekam berhenti sendiri", "recording stops early", "samples missing", and when planning a recording-limit test. Loads the general user skill firmware-bounded-limits first, then adds the PA values, names, and files.
---

# Firmware limits (PA layer)

Load the user-scope skill `firmware-bounded-limits` first; this skill adds only what is specific to the PA repo.

## Values and names in the PA firmware

Use these names exactly in code, messages, and test plans, because the general skill uses generic names.

- ISR queue: `QUEUE_N = 256` (`firmware/include/acquisition.h`) at `ECG_FS = 360` Hz, so 256 / 360 = 711 ms. `loop()` takes one sample per iteration. Compare every save, retry, and wait constant with 711 ms.
- The queue fill is read through `acquisition_fill()`; a save chunk runs only when `acquisition_fill() == 0`.
- Lost samples are counted by `acquisition_missed()` (the sum of `n_missed` and `n_tick_lost`). A failure-path test matches the reported number against the difference of `acquisition_missed()`.
- Recording limits in `firmware/include/recorder.h`: `RECORDER_SECONDS` (default 300), `RECORDER_PART` (default 6), `RECORDER_NUMBER` (default 999). `RECORDER_N` in `firmware/src/recorder.cpp` derives from `ECG_FS * RECORDER_SECONDS`, so the build flag is `RECORDER_SECONDS`, not `RECORDER_N`.
- The current recording design (`recorder.cpp`): the whole session is held in PSRAM with `SESSION_N = RECORDER_N * RECORDER_PART_MAX` and written to LittleFS only after it stops, from `recorder_service()` when `acquisition_fill() == 0`. Per-part capacity is `FULL_FILE_SPACE`, and `part_max` is computed at start from free space and `RECORDER_NUMBER_MAX`. Changes start from this design, not from a new one, because the scheme already exists in the repo.
- Counter names: samples dropped by the queue are `missed` (`acquisition_missed()`, also the `lewat=` field in the CSV header); data not yet saved is `not_saved` (not in the firmware yet; add it to the `s` status line when a test needs it). Do not use `skipped`: the status line already uses `lewati` for the bench calibration-gate skip.
- The container writer in `recorder.cpp` checks its own limit; functions on the sample path (`recorder_sample`) only write `active = false` and mark the event.
- The session flag in `recorder.cpp` is `active`; every stop path writes `active = false` before `Serial`, `display_message`, or `display_sound`, so a slow output cannot let more samples in.

## Display and serial text

Display text is Indonesian, for people: `RUANG PENUH`, `BATAS SESI`, `TUNGGU`, `TOLAK`, `PENUH`, `GAGAL SIMPAN`. The REC line (`REC05:00`, in `display.cpp`) shows only while samples really enter the container; while `acquisition_missed()` is above zero it is replaced by `HILANG` (red), and while saving it shows `SIMPAN..` then `SIMPAN`. A new message follows that style through `display_message(large, small)`.

Serial commands at 115200 for tests: `r` start or stop recording, `j` pause, `s` status (contains `rekam=<0|1> n=<n>`, `antrean <n>`, `sampel hilang <n> (tick <n>)`), `l` list files, `d<n>` dump a file, `h<n>` delete, `y` switch signal source (replay without a sensor; `r` refuses when the source is not ADC: serial `REKAM hanya dari sensor`, display `TOLAK`, so recording-limit tests use the sensor, not replay). A counter a test needs that is not in the `s` line is added to the status line in the same change. The full command list is in `docs/features/serial-commands.md`.

## Tests on the PA board

Make the limit small through a build flag, run from `firmware/`, one literal command per test:

```bash
PLATFORMIO_BUILD_FLAGS="-DRECORDER_SECONDS=10" pio run -t upload
```

Limits in PA files are found with `grep -nE "(>=|==|>) *[A-Z_]*(_MAX|_N)" firmware/src/*.cpp`, because PA limit constants end in `_MAX` or `_N`. A pause test reads the exact sample count from the counter (`n=` in the `s` line) before and after the pause, and the expected line uses the difference.

The real limit (300 seconds) is crossed once on the board. When a board is attached, Claude runs the test and reads the serial output; a result not yet run is written as an expectation and its checklist item stays `[ ]` (strict rule C in `CLAUDE.md`).

## Docs and checker

- An options block for the user carries one recommendation with its reason, because the decision stays with the user.
- A limit that only drops a UI signal is recorded in `firmware/README.md` §Deliberate limits.
- The procedure goes into the recording feature page `docs/features/recording.md`; pitfalls with measured numbers go into the right subsystem list of `firmware/README.md` §Pitfalls; test flags are documented there too.
- Code carries no comments (skill `no-code-comments`); `python3 scripts/check_comments.py` must exit 0.
