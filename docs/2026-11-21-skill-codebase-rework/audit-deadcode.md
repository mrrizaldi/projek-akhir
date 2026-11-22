# Dead code audit (read-only), 21 Nov 2026

Method: the `deadcode` skill. vulture/ruff/cppcheck are not installed, so Python AST analysis, grep, and `g++ -fsyntax-only -Wall -Wextra` for the firmware native modules were used. No file was edited. Scope exclusions follow the task: `PA_*` knobs, `test_hw_*`, golden ref, scripts documented in a README, simulation modes.

## Summary

| Component | Findings | Proposed delete | Proposed keep / move |
|---|---|---|---|
| firmware | 3 public functions without callers | 3 | 0 |
| model/src | 2 unused imports | 2 | 0 |
| model/scripts | 1 function, 11 unused imports (in 7 files) | 12 | 0 |
| scripts/ (repo) | 0 | 0 | 0 |
| dashboard | 0 | 0 | 0 |
| presentasi | 0 | 0 | 0 |
| tracked files | 2 (mainboard.zip, residu_ds1.npy) | 1 | 1 |
| model/tests | 1 import | 1 | 0 |

In total 20 delete candidates, 1 keep. All scripts in `model/scripts/`, `scripts/`, `dashboard/` are referenced by a README/Makefile/skill/CI (grep per name, each file has at least one reference outside itself). No unreachable blocks were found (return/raise followed by a statement), no constant `if False/0/True`, and no unused `config.py` constants (every name was searched across all `*.py`). `g++ -Wall -Wextra -Wunused` is clean for `ecg_pipeline`, `ecg_live`, `ina219`, `ecg_mqtt`. Modules that need Arduino (menu, tampilan, rekam, etc.) were not compiled; they were only checked by grepping names.

## firmware

| path:line | kind | evidence | proposal | risk |
|---|---|---|---|---|
| firmware/include/ecg_mqtt.h:35, firmware/src/ecg_mqtt.cpp:21 | function never called `ecg_mqtt_antre_reset` | `grep -rnw ecg_mqtt_antre_reset src include test ../scripts ../model/scripts README.md` returns only the declaration and definition. Not in test_mqtt or the README. | delete declaration + definition | low; `queue_head/isi/hilang` are still used internally |
| firmware/include/ecg_mqtt.h:47, firmware/src/ecg_mqtt.cpp:350 | function never called `ecg_mqtt_tersambung` | same grep: only declaration + definition. | delete; check that the variable `tersambung` is still used by other functions (it is used in ecg_mqtt.cpp) | low |
| firmware/include/display.h:21, firmware/src/display.cpp:313 | function never called `tampilan_monitor` | grep: only declaration + definition. The variable `monitor` is used elsewhere in display.cpp. | delete the accessor | low |

Verification method for the three above: a script scanned all prototypes in `include/*.h` (except `model_int8.h`, `wifi_secrets*.h`), then counted calls in `src/`, `include/`, `test/` outside headers and outside definition lines. Only those three names scored zero. File-local macros/constants (`constexpr`, `#define`, `enum`) were counted: all have at least 2 uses or are used in tests/generators (e.g. `ECG_PT_OFFSET` and `ECG_ZSCORE_EPS` in `ecg_preproc.h` are produced by `export_golden.py` and used by `ecg_pipeline.cpp`).

## model/src

| path:line | kind | evidence | proposal | risk |
|---|---|---|---|---|
| model/src/io_mitdb.py:6 | unused import `CHANNEL`, `RAW_DIR` | `grep -nw CHANNEL src/io_mitdb.py` and `grep -nw RAW_DIR ...` return only the import line. No module imports those names through `src.io_mitdb` (`grep -rn "from src.io_mitdb import"` is empty). | delete from the import line | none |

## model/scripts

| path:line | kind | evidence | proposal | risk |
|---|---|---|---|---|
| model/scripts/prep_beats.py:72 | function never called `available_records(raw_dir=RAW_DIR)` | `grep -rn available_records` in model/ dashboard/ scripts/ returns only the definition (one hit). It only wraps `available_records("mitdb")`, and the `raw_dir` parameter is even ignored. After deletion, the `RAW_DIR` import in the same file may also become unused (check). | delete | none |
| model/scripts/prep_beats.py:10 | unused import `PACED_EXCLUDED` | `grep -nw PACED_EXCLUDED scripts/prep_beats.py` returns only the import line | delete from import | none |
| model/scripts/bench_pantompkins.py:11 | import `FS` | grep -nw FS: only line 11 | delete | none |
| model/scripts/plot_phase0.py:11 | import `FS` | grep -nw FS: only line 11 | delete | none |
| model/scripts/check_poc.py:5 | import `numpy as np` | grep -nw np: line 5 and one string literal on line 40 (`"np.random.seed(SEED)"`), not a use | delete | none |
| model/scripts/check_poc.py:11 | import `PROCESSED_DIR`, `THRESHOLD` | grep -nw: only line 11 | delete | none |
| model/scripts/export_golden.py:11,14 | import `ALIGN_WIN`, `BANDPASS_LOW`, `BANDPASS_HIGH`, `BANDPASS_ORDER` | grep -nw for each name: only the import line (4 names) | delete | none; the bandpass generator uses `src.preprocessing` |
| model/scripts/sweep_jitter.py:14 | import `USE_HOS` | grep -nw USE_HOS: only line 14 | delete | none |
| model/scripts/check_fp.py:53 | import `tensorflow as tf` (local inside `main`) | `grep -n "keras\|tf\b" scripts/check_fp.py`: `tf` is not used; `keras` is used on line 62 via `from tensorflow import keras` | delete only the line `import tensorflow as tf` | none |

## model/tests

| path:line | kind | evidence | proposal | risk |
|---|---|---|---|---|
| model/tests/test_features_rr.py:3 | import `RR_LOCAL_WINDOW_BEATS` | grep -nw: only line 3 | delete from import | none |

## scripts/, dashboard/, presentasi/

No findings. Checks that were run:
- Reference per file: for each `scripts/*`, `dashboard/*.py`, `model/scripts/*.py`, `git grep -l -w <nama> ... ':!laporan' ':!docs/arsip'` was run; all have a reference in a README/Makefile/skill/CI/active document. Those referenced only by one README: `check_fp`, `check_calibration`, `check_lead`, `summarize_ablation`, `plot_walkthrough`, `measure_jitter`, `second_stage_rules`, `cek_docx` (documented as tools run by the user, so kept).
- argparse flags without a reader: the scanner flagged `--mulai/--durasi` (plot_recording) and `--kertas/--ketat/--hanya-galat/--tanpa-prosa/--uji` (cek_tabel); checked manually, all are read through other variable names (`arg.kertas`, `start_s`, etc.). False positives.
- Python functions never called (name appears only once across all tracked `*.py`): only `available_records`. Functions with two occurrences (def + one call) are not considered dead.
- `deck.js` (2 files): all `const` helpers are used more than once.

## Tracked files / artifacts

| path | kind | evidence | proposal | risk |
|---|---|---|---|---|
| hardware/mainboard.zip | tracked binary archive, not referenced | `git grep -F mainboard.zip -- . ':!laporan' ':!docs/arsip'` is empty. `unzip -l`: a copy of 16 Oct 2026 containing `.mcp-backups/`, `mainboard-backups/`, `mainboard.dsn`, `fp-info-cache`, the old `.kicad_pcb` (520 KB). Its contents already exist (latest version) in `hardware/mainboard/`. Commit that brought it: 2410147 "arsip mainboard". | move to the archive or delete if not needed (git keeps the history); repo policy uses `git mv` to `hardware/arsip/` | low; holds old working backups, not a source |
| model/artifacts/metrics/jitter/residu_ds1.npy | tracked intermediate `.npy` | written by `measure_jitter.py:142`; read (referenced) by `model/CLAUDE.md`, `model/README.md`, `jitter-walkthrough.md` as the input for `PA_JITTER=empiris`. | keep: read by the model for empirical jitter, not a discard result | reason to keep; policy B1 only excludes `.npz` |
| model/artifacts/metrics/ablasi/ablasi_seed42.csv | archive CSV not referenced by active documents | `git grep -n ablasi_seed42 -- model`: only `model/docs/arsip/...robustness-changelog.md` ("arsip batch pertama"). Not written by any script. | move to `model/artifacts/arsip/` or delete | low |
| model/artifacts/metrics/{pantompkins_114,fase0_114,fase1_114}.png | sibling figures of record 114 | not referenced by active documents (`git grep pantompkins_114 fase0_114 fase1_114` is empty); regenerated by `bench_pantompkins.py`, `plot_phase0.py`, `plot_phase1.py` (`make plot0/plot1`). | keep: final B1 figures (the `_100` versions are referenced by the book); review if you want to reduce | low |

Note: `model/artifacts/metrics/akuisisi/akuisisi_device.png` (untracked in gitStatus) is not part of the audit.

## Five most certain findings

1. `ecg_mqtt_antre_reset` (firmware/include/ecg_mqtt.h:35, src/ecg_mqtt.cpp:21): zero callers in src, include, test, scripts.
2. `ecg_mqtt_tersambung` (ecg_mqtt.h:47, ecg_mqtt.cpp:350): zero callers.
3. `tampilan_monitor` (display.h:21, display.cpp:313): zero callers.
4. `available_records` (model/scripts/prep_beats.py:72): zero callers, parameter ignored.
5. Dead imports: `model/scripts/export_golden.py` (`ALIGN_WIN`, `BANDPASS_LOW/HIGH/ORDER`) and `model/src/io_mitdb.py` (`CHANNEL`, `RAW_DIR`), import lines only.

Every deletion must be confirmed by the user (deadcode skill gate), followed by `pio test -e native`, `pio run`, `make test`/pytest in `model/`, and `python3 scripts/check_comments.py` before the commit.
