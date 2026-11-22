# model/: the TinyML track

The development track of the binary arrhythmia classification model (Normal vs Arrhythmia), from
MIT-BIH data to the C header for the ESP32-S3 firmware.

- **Specification:** `PRD_Model_Aritmia_TinyML.pdf` (this folder).
- **Working rules and phase status:** `CLAUDE.md` (this folder).
- **Explanation per phase:** [`docs/README.md`](docs/README.md).

## Environment

- Python 3.11.9 (`.python-version`), venv `.venv`, dependencies `requirements.txt`.
- All scripts are run from this folder, for example `python scripts/check_dataset.py`.
- The MIT-BIH dataset is in `data/raw/mitdb/` (git-ignored), downloaded with `make data`.

## Structure

| Folder/file | Contents |
|---|---|
| `config.py` | All constants (FS, bandpass, window, label map, threshold) |
| `src/` | Pure modules (functions from input → output, no side effects) |
| `scripts/` | Execution scripts: download, prep, train, evaluate, quantize, export, ablation |
| `tests/` | pytest for the DoD of each phase |
| `artifacts/` | Trained model, `model_int8.tflite`, metrics and plots |
| `docs/` | Walkthrough per phase ([map](docs/README.md)) |

## Main commands

```bash
make data && make check   # unduh & cek dataset
make prep && make split   # Fase 2-3
make train                # Fase 5
make eval                 # Fase 6 (float32, DS2)
make quantize             # Fase 7 (PTQ INT8)
make poc                  # Fase 8 (checklist DoD)
make export               # model_int8.h -> firmware/include/
make test                 # pytest
make pull                 # tarik rekaman dari board -> data/recordings/
make analyze FILE=data/recordings/<berkas>.csv
```

Full list of targets: `make help`. Plot targets use `REC=<record>` (default
100), for example `make plot0 REC=114`.

## Scripts (`scripts/`)

All are run from the `model/` folder. Scripts that import `config` install a
one-line `sys.path.insert` because `python scripts/x.py` puts `scripts/` in
`sys.path[0]`; `conftest.py` does the same for pytest. The explanation of the
flow and the reasons is in the walkthrough named in the last column.

| Script | Command | Purpose and notes |
|---|---|---|
| `download_data.py` | `python scripts/download_data.py [svdb incartdb \| --all]` | Download PhysioNet databases to `data/raw/<db>/`. Safe to repeat (wfdb skips files that already exist). Sizes ~100 MB mitdb, ~200 MB svdb, ~700 MB incartdb (12 channels). Database requirement: beat-level annotations (see [dataset](docs/dataset-walkthrough.md) §4) |
| `check_dataset.py` | `make check` | Check that files are complete, read record 100, summarize labels, plot the first 30 seconds of the MLII channel with annotation symbols |
| `plot_phase0.py` | `make plot0 REC=100` | Phase 0 DoD: the annotated R-peak lines must land EXACTLY on the R peak. A miss means the channel was read wrongly ([io-mitdb](docs/io-mitdb-walkthrough.md)) |
| `plot_phase1.py` | `make plot1` | Raw vs bandpass: the time, PSD, and spectrogram panels use the same time window so that high energy in the spectrogram can be matched to the QRS ([preprocessing](docs/preprocessing-walkthrough.md)) |
| `plot_phase1_segment.py` | `make plot1seg` | Each `WIN_LEN`-sample window, R on the center line; after z-score all windows are comparable (mean ~0, std ~1) |
| `plot_walkthrough.py` | `python scripts/plot_walkthrough.py 100` | The two companion figures for preprocessing: the training path (raw → filter → segment → z-score) and the Pan-Tompkins cascade |
| `bench_pantompkins.py` | `python scripts/bench_pantompkins.py 100` | Detector sensitivity/precision against annotations, ±150 ms tolerance (PRD pp. 7-9), greedy 1-to-1 pairing from the annotation side. The detector is NOT used by training segmentation |
| `prep_beats.py` | `make prep` | Phase 0-2 per record → `per_record/<rec>.npz` ([prep-beats](docs/prep-beats-walkthrough.md)) |
| `build_split.py` | `make split`, `--combined` | Phase 3 ([dataset](docs/dataset-walkthrough.md)). `--combined` writes `train_multi.npz`/`test_ds2.npz`/`test_<db>.npz` and does not overwrite `train.npz`/`test.npz`, which are still used to reproduce the locked ablation |
| `train_model.py` | `make train` | Phase 5 ([train](docs/train-walkthrough.md)) |
| `calibrate_threshold.py` | `python scripts/calibrate_threshold.py` | Lock the threshold on VAL ([evaluate](docs/evaluate-walkthrough.md) §2) |
| `eval_fp32.py` | `make eval` | Phase 6 on DS2; the threshold is used as is from `config.THRESHOLD` |
| `quantize_int8.py` | `make quantize` | Phase 7; the evaluation procedure is exactly the same as Phase 6 so that delta = the quantization effect only ([quantize](docs/quantize-walkthrough.md)) |
| `check_poc.py` | `make poc` | Phase 8: each PRD DoD item p. 17 is verified mechanically; exit code ≠ 0 if any fails. Checks the `CLAUDE.md` table only in the decision point section |
| `export_model_h.py` | `make export` | `model_int8.tflite` → `firmware/include/model_int8.h`. Different from `xxd -i`: it also carries the scale & zero_point of each tensor ([firmware](docs/firmware-walkthrough.md)) |
| `export_golden.py` | `python scripts/export_golden.py` | `ecg_preproc.h` + `golden_ref.h` ([firmware](docs/firmware-walkthrough.md) §1, §3) |
| `extra_metrics.py` | `.venv/bin/python scripts/extra_metrics.py` | DS2 float32 and INT8: PR-AUC (*average precision*) with prevalence as the baseline, MCC at `THRESHOLD`, per-AAMI-class *recall* S/V/F (symbols from `per_record/<rek>.npz`, DS2 order checked against `y`), mean and median per-recording *recall*, number of labels changed by quantization → `artifacts/metrics/fase7_metrik_tambahan.csv` ([evaluate](docs/evaluate-walkthrough.md) §3b, [quantize](docs/quantize-walkthrough.md) §6) |
| `window_quality.py` | `.venv/bin/python scripts/window_quality.py <rekaman.csv> ...` | Orphanidou 2015 SQI per 10-second window → `artifacts/metrics/kualitas/jendela10s_<rekaman>.csv` ([akuisisi](docs/acquisition-walkthrough.md) §6) |
| `eval_detected_segmentation.py` | `python scripts/eval_detected_segmentation.py` | Cost of Pan-Tompkins segmentation vs annotation ([detection-segmentation](docs/detection-segmentation-walkthrough.md)). The comparison numbers are read from the output of `eval_fp32.py`, not memorized |
| `measure_jitter.py`, `sweep_jitter.py` | `python scripts/measure_jitter.py`, `python scripts/sweep_jitter.py [--tag dasar]` | DS1 detector residual and metrics as a function of jitter ([jitter](docs/jitter-walkthrough.md)) |
| `ablasi.py` | `python scripts/ablasi.py --tag <nama> [--jitter empiris --copies 2]` | One end-to-end variant, see below |
| `summarize_ablation.py` | `python scripts/summarize_ablation.py [--tag A B] [--vs A]` | Mean ± half-range per tag, F1 threshold verdict 0.04, tags with < 3 seeds are flagged |
| `check_lead.py`, `check_calibration.py`, `check_fp.py`, `check_operating_point.py`, `second_stage_rules.py` | see [docs/README.md](docs/README.md) §Supporting analysis tools | Experiment diagnostics; DS2 only diagnoses, it does not choose parameters |
| `pull_recording.py` | `make pull [N=n]` | Pull a recording from the board ([akuisisi](docs/acquisition-walkthrough.md)). If the board is still recording, the script stops & saves it first. Other port: `ECG_PORT=/dev/ttyACM1` |
| `analyze_recording.py` | `make analyze FILE=... [TITLE="R1"]` | Rate recording quality with numbers, see below |
| `quality_trend.py` | `.venv/bin/python scripts/quality_trend.py <berkas-1.csv> [<lanjutan>.csv ...]` | Per-second quality of one recording session (continuation files are joined in order, a `celah` other than 0 is warned about, files with `# jeda` are rejected) with the firmware gate formula: filtered swing, 50 Hz hum (1-second FFT bin = Goertzel bin of `gate.cpp`), `ayun_bersih`, clipping, plausible RR, duration of calm RR. Prints a per-minute summary and the first second each gate condition is met; per-second table → `artifacts/metrics/kualitas/<berkas-1>-sesi<k>.csv`. The basis of the 60 s warm-up duration of the calibration gate ([mqtt](docs/mqtt-walkthrough.md) §3.1) |
| `plot_recording.py` | `make plot FILE=... [START=detik]` | ECG graph of the best 60 seconds (or starting at a given second) in 10-second rows + HR per beat ([akuisisi](docs/acquisition-walkthrough.md) §5) |
| `measure_power.py`, `pull_power.py` | `.venv/bin/python scripts/measure_power.py`, `make pull-power [N=n]` | Power ladder from the laptop and from the board ([firmware](docs/firmware-walkthrough.md) §5d) |
| `broker_info.py` | `make broker-info` | Laptop WiFi SSID, LAN IPv4, port status, suggested `wifi_secrets.h` entry. The firmware does not resolve hostnames, so broker = an IP address and the board must be on the same SSID. Uses `ip -j` (iproute2, Linux only) and `nmcli -t` |

### `ablasi.py`

One variant = one process. The window size and HOS are read by `config` at import,
so a variant is chosen through the environment, not through arguments:

```bash
python scripts/ablasi.py --tag bersih
python scripts/ablasi.py --tag jitter --jitter empiris --copies 2
PA_WIN_PRE=128 PA_WIN_POST=127 python scripts/ablasi.py --tag w128 --jitter empiris --copies 2
PA_HOS=1 python scripts/ablasi.py --tag hos --jitter empiris --copies 2
```

Each variant goes through the same chain: assemble DS1 → split per patient → train →
calibrate the threshold on VAL → measure on DS2 (annotation segmentation and empirically
jittered). The threshold is not retuned on any test set. Results accumulate in
`artifacts/metrics/ablasi/ablasi.csv`, one row per variant; only the main seed's model is
saved, so `check_calibration.py` and
`check_operating_point.py` work on a single seed. `ablasi.csv` has no `db`
column: the header is only written when the file does not yet exist, so adding a column would
shift old rows; the database is encoded in `tag`. `lintas_db.csv` (TEST-B/C)
has a `db` column, and `summarize_ablation.py` recognizes the column prefix (`anot_` or
not) from the header, then uses the key `tag|db` so that one tag in two databases
is not averaged into one. Half-range is used, not stdev, because n=3
is too small for a meaningful stdev.

The tag prefix in `ablasi.csv` marks the experiment group: no prefix =
window/jitter/HOS ablation (Phase 6c; `w128s3` = `--copies 3`), `fb_` = training
database (`fb_svdb`, `fb_incartdb`, `fb_multi`, `fb_svdb_nocw` = without
`class_weight`), `fd_` = the 2×2 dataset × feature table (`fd_mitdb_only`, `fd_both`,
`fd_qrsw`, `fd_rr`), `g_` = training regime (`g_swa3` = `--swa 3`, `g_lr1e4`,
and the diagnosis runs `g_diag`, `g_diagbase`, `g_lrdiag`), `t8_` = learning rate
with `--cross-db` (`t8_lr1e3`, `t8_lr3e4`, `t8_lr1e4`; TEST-B/C rows in
`lintas_db.csv`).
The verdict of each group is in [docs/README.md](docs/README.md) §Experiments not adopted;
`ablasi_seed42.csv` is explained in
[jitter](docs/jitter-walkthrough.md) §5.

Jitter copies are only for mitdb. Other databases are not jittered because the residual
pool (`residu_ds1.npy`) was measured from the detector on mitdb at 360 Hz; using it for
beats of 128/257 Hz that have been resampled stacks two sources of position error, and
the second has never been measured. If needed, measure the residual in that
database first with `measure_jitter.py`.

### `analyze_recording.py`

Input: the firmware `dump` output (lines `# fs=.. n=.. lewat=..` then one ADC
value per line; format in [akuisisi](docs/acquisition-walkthrough.md) §3). All
computations run per segment and are then merged: the filter starts from zero at the beginning of each
segment and RR intervals never cross a `# jeda`
(`tests/test_analyze_recording.py`).

- **Periodic heartbeat without detecting peaks.** Pan-Tompkins is easily fooled by
  50 Hz hum (its energy leaks through the square + integration and is counted as
  QRS). Autocorrelation of the 5-15 Hz QRS band energy asks something else that is more
  noise-tolerant: whether the pattern repeats with a period of 0.4-1.5 seconds. Segments shorter
  than 1.5 seconds are skipped.
- **False-positive guard.** A heartbeat gives one dominant autocorrelation peak;
  periodic interference (hum and its harmonics) gives a series of equal peaks
  with uniform spacing. Another peak whose height is ≥ 80% of the main peak is counted
  as an "equal peak".
- **Physiological range 30-200 bpm.** The proportion of RR that falls in this range
  is reported; outside it is almost certainly a false detection.
