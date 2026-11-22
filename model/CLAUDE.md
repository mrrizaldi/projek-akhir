# CLAUDE.md: model/ (TinyML track)

Full specification: `PRD_Model_Aritmia_TinyML.pdf` (19 pages, Phase 0–8).
Read the relevant phase before touching any file. No vibe-coding.

## Rules

1. **`src/` = PURE modules** (in→out functions, no top-level code, import-safe).
   **`scripts/` = execution** (print, plot, write files). Do not mix.
2. **All constants in `config.py`.** Do not hardcode numbers in `src/`.
3. **DS2 is off limits before Phase 6.** Not validation, not threshold tuning.
   Touch it once in Phase 6–7, that is all.
4. **`sosfilt`, NOT `filtfilt`** (causal; PRD PITFALL #1). `filtfilt` is impossible
   in real time on the MCU → train/deploy mismatch.
5. **Training segmentation uses R-peaks from the ANNOTATION**, not Pan-Tompkins
   (locked decision, PRD Phase 2).
6. **Every finished phase → write a walkthrough.** One file per module in `docs/`,
   name pattern `<modul>-walkthrough.md`. See "Walkthrough per phase" below.
   Plans, designs, and dated changelogs that are finished are not kept; history is in git.
7. **Explanations live in `docs/`, not in `src/`.** `src/` files are written as
   short as possible (almost no comments) so they read as equations
   and are easy to translate to C. If you need to explain "why", the place is the
   walkthrough, not a 40-line docstring.

## Commands

```
make data      # download MIT-BIH (once)        make train     # Phase 5
make check     # check dataset completeness     make eval      # Phase 6
make plot0     # verify Phase 0 (R-peak)        make quantize  # Phase 7
make plot1     # verify Phase 1a (filter)       make export    # .h to firmware
make plot1seg  # verify Phase 1b (segmentation)
make prep      # Phase 2 → per_record/*.npz     make test      # pytest
make split     # Phase 3 → train/test.npz        make poc       # Phase 8 checklist
make pull      # pull a recording from the board
make analyze FILE=data/recordings/<name>.csv   # recording analysis + plot
make pull-power [N=<n>]   # pull the standalone power sweep result /daya/NNN.csv from the board
make broker-info         # SSID, LAN IP, ports 1883/8080, suggested wifi_secrets.h entry
```

`make help` lists all targets (including `data-all`, `split-multi`, `clean`).

## Phase status

One line per phase, only the condition that applies now. Per-phase history is in git.
Long write-ups go in a walkthrough or Bab 4 of the laporan, not here.

| Phase | Status | Current condition & numbers |
|---|---|---|
| 0 Data | done | 48 complete records, `fs == 360`. Rec 114 uses MLII at index 1; rec 102/104 (no MLII) are rejected with `ValueError` |
| 1 Filter & segmentation | done | causal bandpass 0.5–40 Hz order 4 (`sosfilt`). Group delay +4 samples (+11.2 ms) → R at index `WIN_PRE + 4` = **132** |
| 2 RR features & prep | done | `make prep`: **202,560 beats** (Normal 89.7% / Aritmia 10.3%, 215 dropped). DS1 augmented with empirical jitter (1 clean + 2 copies), DS2 clean |
| 3 Split | done | inter-patient: **DS1 152,904 beats / DS2 49,656 beats**, `X_morph` (N,256,1). Cross-patient leakage is mechanically `raise`d |
| 4 Model | done | two inputs, **6,417 params**, no dropout |
| 5 Train | done | `artifacts/model_fp32.keras`, balanced `class_weight`, EarlyStopping(`val_auc`), Adam 1e-3 |
| 6 Evaluation | done | threshold **0.80** from VAL. DS2: **recall 0.6996, precision 0.6235, F1 0.6594, specificity 0.9479, AUC 0.9334**. Median per-patient recall 0.9167; worst rec 232 (0.3541) and 213 (0.2246) |
| 6b On-device segmentation | done (outside PRD) | detector offset 38 samples (DS1). Segmentation does not damage classification: F1 on detected beats 0.6499 vs annotation 0.6594. System recall 0.6035 (annotation 0.6996) because of undetected beats (detector sensitivity for class S 0.6494). `fase6b_segmentasi_deteksi.csv` |
| 6c Jitter robustness | done (outside PRD) | locked: `WIN_PRE/WIN_POST = 128/128`, `JITTER_MODEL = "empiris"`, `JITTER_COPIES = 2`, `THRESHOLD = 0,80`. HOS rejected |
| 7 Quantization | done | full INT8 PTQ (deploy variant): **22.94 KB**, recall 0.7105, F1 0.6604, AUC 0.9344, delta recall **+0.0108** |
| 8 PoC & export | done | `make poc` 8/8 DoD items verified mechanically; `make export` → `firmware/include/model_int8.h`. Copy figures to `laporan/` only with `--laporan` |
| HW-1 Inference on board | done | device probability matches PC (max difference 1 INT8 quantum), **26.6 ms per beat**, tensor arena 12,948 B |
| HW-2 R detection in C | done | Pan-Tompkins (`ecg_detect_r`, `ecg_align_r`) matches Python on 11/11 peaks in the golden |
| HW-3 Live flow | done | `src/ecg_live.cpp`: average load 3.0% of the budget, peak burst 33.4 ms → ADC must go through an ISR + queue |
| HW-4 Production firmware | done | 360 Hz timer ISR → 256 queue → `ecg_live` → inference → LED + serial; lost samples 0 |
| HW-5 Body signal | done | official data = the 22 Oct 2026 midday session (R1–R4, 927.1 s, MLII, one subject), all four "Berhasil"; buku-pa recording quality table. Contact-based calibration gate (LO±, swing 60, hum 500, warm-up 60 s) from three sessions of ±15 minutes on 21–22 Oct. Recordings 10 Sep–11 Oct 2026 = trial runs. Details: `data/recordings/README.md`, `docs/mqtt-walkthrough.md` §3.1 |
| HW-6 MQTT + ThingsBoard | done | calibration gate + contact gate (LO±, swing 60, hum 500), 27,000-beat backlog in PSRAM. PDSR 100.0% / 99.2% / 100.0%, median latency 939 / 1,108 / 1,014 ms (3 repetitions). Open: WiFi mode power. Details: `docs/mqtt-walkthrough.md` |
| HW-7 Replay | done | replay signal source (menu "Sumber sinyal": reference 208 replay or recording replay `/rekam/NNN.csv`; serial `y` = ADC ⇄ reference) replaces the ADC in the ISR; 11 beats per 6.67 s cycle, lost samples 0 |

## Open work

- **(13 Oct 2026) PCB rev2: physical check before fabrication.** The design is in
  [`../hardware/mainboard/`](../hardware/mainboard/README.md) (schematic +
  layout, `cek_board.py` passes). What remains is in the "Yang belum
  terverifikasi" section of that README: row spacing of the physical DevKit
  headers, module pin order, module mechanical space, breadboard test of the
  D1→VSYS path, battery connector, and the voltage of the switch lamp. Measure
  the VIN_ESP voltage after D2 when powered from the battery.
- **(14 Oct 2026) The assembly form in the book waits for the final PCB.** Buku-pa says
  "rangkaian uji dengan peta pin PCB". After the final PCB design is printed,
  update the test hardware table, the assembly photo, and the *wearable* device
  suggestion in Bab 4/5.

List of things that are NOT finished and easy to forget. Items are dated; delete an item
only after it is truly closed (record the closure in the related walkthrough).

- **(23 Oct 2026) A recording starts by itself shortly after the board is plugged into USB.**
  Observed twice: 22 Oct (`rekam=1 n=417` in the first status) and 23 Oct
  (a 30.5 s recording without electrodes, starting ±1 s before the first port was opened).
  ModemManager is already excluded (udev `ID_MM_DEVICE_IGNORE=1`). The cause
  has not been measured: add a print of the trigger source (button B3 / serial `r`) in
  `recorder_toggle()` before guessing. Impact: an empty recording session is saved too,
  and commands rejected during a recording session (e.g. `m`) fail silently in
  scripts.
- **(13 Oct 2026) Power consumption per operating mode.** Power measurement per mode
  (idle, inference, WiFi/MQTT): design in
  [`docs/firmware-walkthrough.md` §5d](docs/firmware-walkthrough.md#5d-tangga-ukur-daya) (rationale in the section "Rasional rancangan").
  The measurement path is ready: from the laptop (serial `p0`-`p5`, `scripts/measure_power.py`
  -> `artifacts/metrics/daya/<ts>.csv`) or standalone from the battery (menu Ukur daya
  / serial `V`, then `make pull-power`; procedure in `firmware/README.md` section
  "Ukur daya tanpa laptop"). The INA219 is already on the battery path (ladder of 14 Oct 2026
  read 3.69 V, ±137–154 mA without WiFi; the battery lasted almost 1 hour).
  **Blocked by the supply:** `p5` needs WiFi ON, which waits for the 5 V converter (the
  WiFi OFF item below). After that, run the ladder without the charger, then fill
  `PLACEHOLDER-DATA daya` in bab4 of buku-pa.
- **(14 Oct 2026) Board WiFi deliberately OFF: emergency state, return it to ON.**
  The 4.x V battery converter output makes the board reset every ±2.5 s during
  `WiFi.begin()`, so the board NVS was set to **Jaringan → WiFi aktif OFF** (serial
  `m`) so that body signal recording from the battery keeps working. The normal
  state of the system is WiFi ON; OFF only until the supply is fixed. WiFi/MQTT tests and
  `p5` are run for now while plugged into USB. Closing, after the user
  sets the converter output to 5.0–5.1 V:
  1. Turn WiFi on: menu **Jaringan → WiFi aktif → ON** or serial `m`
     (line `wifi ON (tersimpan)`).
  2. Power on from the battery without USB: the screen lights up, the full calibration beep once,
     no repeated reset. Then plug in USB and check `s`: RSSI ≠ 0.
  3. Repeat the power ladder **without the TP4056 charger**, laptop on the same SSID
     as the board and ThingsBoard running, then `make pull-power`. The ladder
     `/daya/003.csv` (14 Oct, without WiFi, suspected charger plugged in starting
     +326 s) is not used for the laporan.
  4. Delete this item and the sentence "Selama keluaran konverter belum disetel"
     in `firmware/README.md` section "Hal yang perlu dicek pada rakitan".
- **(14 Oct 2026) Plan, done after WiFi is back ON: recording straight
  to the server.** One recording session is at most 5 files × 300 s
  (1,500 s) in LittleFS 3,456 KiB and must be pulled over USB. The direction the user asked for:
  when WiFi is available, raw samples are streamed to a server on the laptop so that
  recording duration is not limited by LittleFS. The original plan (MQTT to ThingsBoard
  for per-beat classification results) keeps running; the raw stream is an
  addition. Things to design together with the user before starting: the protocol
  (separate MQTT topic or HTTP), the receiver on the laptop that writes CSV in the
  `/rekam/NNN.csv` format so `make analyze` keeps being used, behavior when the
  connection drops (fallback to LittleFS), and the WiFi load on the battery supply
  (depends on the WiFi OFF item above).

## Walkthrough per phase

A walkthrough = a learning document, not a specification (specification = PRD). It contains
the code flow step by step, the math behind it, the reason for each decision,
real numbers, and comprehension-check questions.

- **Write it as soon as the phase is done, do not postpone.** Reasons that are not recorded while
  still fresh get lost, and Bab 4 of the laporan takes its material from here.
- **List of documents + reading order: [`docs/README.md`](docs/README.md).** A new
  walkthrough must be registered there.
- **Fixed skeleton** (do not make a new format every phase): big map (flow
  diagram) → function by function with code + formulas → decisions with the rejected
  alternatives → what is deliberately NOT done → real numbers → comprehension check →
  supporting scripts.
- Documents that are run (record, flash, calibrate) use the standard procedure:
  numbered steps, commands in a code block, expected result.

## Decision points already locked

This table = the living version of PRD APPENDIX B. Fill it in the moment the gavel falls, do not postpone.

| Decision | Value | Short reason |
|---|---|---|
| Classification | binary (Normal/Aritmia) | inter-patient makes F & Q recall ~0 |
| Split | inter-patient de Chazal | intra-patient = false accuracy |
| Filter | causal `sosfilt` | `filtfilt` is impossible on the MCU |
| Segmentation | annotation R-peak | keep the model path pure from detector error |
| Normalization | per-window z-score | immune to amplitude differences, zero statistical leakage |
| Pooling | GlobalAveragePooling1D | far fewer params than Flatten |
| Window size | **128/128 = 256 samples** | 3-seed ablation (Phase 6c) against the baseline 90/160 = 250 samples: DS2 F1 0.5660 → 0.6911. The mechanism is visible per symbol: **recall S rises monotonically with `WIN_PRE`** (90→0.268, 112→0.369, 128→0.42-0.49) because supraventricular beats are told apart by the P wave & PR interval on the left side of the window; recall V does not move; **recall F drops** 0.308→0.15-0.20 (T coverage cut 160→128), a deliberate trade, S is 10× more frequent than F in DS2. The DECIDING variant is the one that lost: 112/144 is also 256 samples, also a multiple of 8, longer T coverage → equal to the baseline. So what pays is the **128 samples of context before R**, not the window length. R at index **132** (128+4) |
| Jitter augmentation | **`empiris` × 2 copies in DS1**, DS2 is never jittered | DS2 F1 0.5660 → 0.6354 even on CLEAN data: jitter works as regularization, not only as training for deploy conditions. `--copies 3` is worse (0.6099), so 2 |
| Threshold | **0.80** | criterion: maximum F1 on VAL, tie-break recall if ΔF1 < 0.005. VAL is also jittered, so the probability spread and its operating point differ from the model without augmentation. Candidates {0.80; 0.85} → recall wins → 0.80. Threshold 0.35 (operating point of the model without augmentation) gives precision 0.19 in this model. Reproduce: `scripts/calibrate_threshold.py` |
| Phase 6 metric aggregation | **beat level** (per-record kept separately) | standard & comparable with the literature (PRD); `fase6_per_record_fp32.csv` for the story of the spread |
| `sklearn.metrics` | **not used**: numpy | TP/FN/FP/TN formulas + Mann-Whitney AUC are a few lines; it also forces a decision on division by zero → 0.0 not NaN (NaN would break the Phase 7 delta table) |
| Butterworth order | **4** (2 biquads) | sharp roll-off; std only drops 5% = morphology intact |
| Beats without `dRR` | **drop** (beats 0 & 1 of each record) | `dRR=0` is a VALID value (stable rhythm), a sentinel clashes with real data; cost 88 of ~100k beats |
| Window↔label alignment | **`prep_beats` does the filtering** (option C) | all beat-dropping policy in one file; `src/` stays pure for the port to C |
| `RR_local_avg` window | **causal, shrinking at the edge** (last 10 RR, including this beat's RR_prev) | symmetric needs future beats → firmware would have to delay 5 beats; causal is consistent with Phase 1 `sosfilt` |
| Edge beat sentinel in `features_rr` | **NaN**, not 0 | in line with the `dRR` row; `prep_beats` drops by index, the sentinel never reaches the model |
| Symbols outside `AAMI_MAP` | **`KeyError`** (not defaulted to Q) | the `BEAT_SYMBOLS` whitelist already filters upstream; a foreign symbol = a leak, must be loud |
| Dropped records | `PACED_EXCLUDED` in `config.py` | 102/104 technical (no MLII), 107/217 methodological (paced) |
| Imbalance strategy | **balanced `class_weight`**, computed by ourselves: `w_c = N/(2·n_c)` → Normal 0.556 / Aritmia 4.947 | does not touch data & does not duplicate beats of the same patient (oversampling = the model memorizes individuals, against the spirit of inter-patient); the PRD forbids using it together with oversampling |
| `pyserial` | **used** (approved), in `requirements.txt` | pulls recordings from the board over serial; no stdlib equivalent, and all tools share one venv |
| `sklearn` for class weight | **not used**: 3 lines of numpy | the `balanced` formula is only `N/(2·n_c)`; CLAUDE.md gate point: do not add a dependency (least of all one as big as sklearn) for what a few lines already solve |
| EarlyStopping monitor | **`val_auc`** (mode max, patience 8, `restore_best_weights`) | `val_recall` can be gamed (guess Aritmia for everything → recall 1.0); `val_loss` is already distorted by `class_weight` so it can no longer be interpreted; AUC is threshold-free & cannot be faked by one class |
| Monitored metrics | **recall, precision, AUC**, NOT accuracy | accuracy 89.9% can be reached by always guessing Normal; showing it only invites misreading |
| Learning rate | **adam default (1e-3)**: ablated, kept | With 1e-3 `val_auc` peaks at epoch 0 then falls monotonically: the production model is the result of ONE epoch, the other 8 epochs are wasted. Ablated 3 LR × 3 seeds + 39 held-out patients: 1e-4 raises AUC in 4/4 evaluation sets, TEST-C F1 +0.124, recall F doubles (0.180→0.359), recall V rises, **but recall S falls 0.4473→0.3126**. 3e-4 is even worse on S (0.2024), so there is no sweet spot in between. The S deficit was verified REAL at an equivalent operating point (6/6 points, `scripts/check_operating_point.py`), not a threshold artifact. Kept because **S is the focus of this research** and the cost of switching (regen `model_int8.h`+`golden_ref.h`, re-validating on the board) is large. This trade is REPORTED, not hidden. The `ablasi.py --lr` knob is left in place. Details: `docs/train-walkthrough.md` §6b |
| Dense 16 dropout | **0.0 (no dropout)**: ablated | val recall: 0.0→**0.700**, 0.2→0.274, 0.3→0.359, 0.5→0.651 (AUC nearly the same for all). Dropout only makes the model more conservative: precision rises, recall falls, while recall is what is lacking. The root of overfitting here is inter-patient variation, not an oversized model |
| INT8 I/O type | **int8 in / int8 out** (`INT8_IO=True`) | end-to-end full INT8: zero float kernels, smallest tensor arena. Firmware that converts float↔int8 uses scale/zero_point from `model_int8.h` (do not hardcode) |
| PTQ calibration samples | **300, stratified from DS1**, seed locked | PRD 100-500; 300 → 30 Aritmia beats, enough to cover the distribution tail, conversion still takes seconds. Stratified so PITFALL #4 (uncalibrated minority class) is impossible |
| QAT | **not used** | PTQ already passes the target (|delta recall| 1.08% < 2%, 22.94 KB < 25 KB); QAT = retrain + a new source of variance for a gain that may not exist |
| Validation set | **DS1 records 101, 114, 201, 220, 223** (`VAL_RECORDS`; 10,349 beats per copy = 20.3% of DS1, arrhythmia 10.11% ≈ the DS1 ratio, S=310 V=714) | val becomes an honest "new patient" simulation → its numbers are fit for choosing the epoch & calibrating the threshold; DS2 stays off limits until Phase 6 |
| Rec 208 must be in train | **yes**: never let it into val/exclude | 372 of 414 class F beats in DS1 are in this record; without it class F nearly vanishes from training |
| Quantized model | **deploy variant** (`build_deploy_model`), not the training model | TFLM computes the `MEAN` op differently from TFLite: PC 0.973 vs device 0.336, without error. Weights copied as they are (identical 1.19e-07), zero retraining |
| Replacement for GlobalAveragePooling | **`DepthwiseConv1D(31)` with weights 1/31**, not `AveragePooling1D` | the pooling op INHERITS the input quantization scale (0.332); the average of 31 values is far smaller → ~3 bits of resolution lost, DS2 recall 0.655→0.528. The convolution op gets its own output scale (0.0429, same as `MEAN`) |
| `Flatten`/`Reshape` in the deploy model | **avoided**: the classification head stays 3-D, `Dense`→`Conv1D` kernel 1 | both bring in `SHAPE`/`PACK`/`STRIDED_SLICE` (dynamic shape); TFLM has no dynamic allocation → device gives 0.418 vs 0.945 |
| Model size limit | **25 KB** (PRD: 20 KB) | the correct deploy variant takes 22.94 KB; ESP32-S3 flash is 16 MB, this limit is about discipline, not capacity. Explicitly approved |
| TRAIN database | **mitdb only** (`TRAIN_DATABASES` = mitdb+svdb is used ONLY in ablation) | Phase D, 2×2 table of 3-6 seeds: svdb lowers F1 by -0.065 (domain shift), the new features patch it +0.070, the combination +0.005 = not a signal. incartdb is even worse (AUC 0.8881 vs 0.9373; recall S 0.331 vs 0.498 for svdb, SEPARATE ranges). Held-out svdb & incartdb are STILL used as the cross-database TEST-B/TEST-C: 85,812 beats, 39 patients. Details: `docs/dataset-walkthrough.md` §4, `docs/README.md` §Eksperimen yang tidak diadopsi |
| Requirement for extra databases | **beat-level annotation, WFDB alphabet** (svdb, incartdb) | `AAMI_MAP` handles it as is. PTB-XL/CPSC/Chapman rejected: per-recording diagnosis, per-beat labels cannot be derived. DS2 mitdb does not change by one byte. Details: `docs/dataset-walkthrough.md` §4 |
| Sampling rate of extra databases | **resample to 360 Hz** (`resample_poly`), not lowering mitdb | `WIN_PRE` is in samples; 128 samples @128 Hz = 1,000 ms, not the 355 ms that was ablated. Going toward 360 keeps the bandpass, `ECG_FS`, and golden unchanged |
| `selaraskan` per database | **svdb & incartdb `True`, mitdb `False`** | svdb annotations are ~6 samples earlier (median +10 vs +3), systematic, above the 4-sample danger threshold. mitdb is the reference of the golden & the locked ablations: aligning it shifts R by ~1 sample |
| `ALIGN_WIN` | **16** (±44 ms) | covers svdb p1..p99 (−9..+15) without reaching the T wave (72-108 samples); `PT_REFINE_WIN` 25 is for the detector spread, too wide here |
| Held-out extra databases | **`sorted(records)[::4]`** (`SPLIT_EVERY_NTH = 4`), not a seed | the rule cannot be coaxed & anyone can verify it. Held-out F in incartdb is only ~13-20 beats (deliberate) → reported as raw TP/FN counts |
| `n_record` per database | **must match**, `build_split_multi` rejects otherwise | the `[::4]` rule over an incomplete list silently gives a different split (65/75 incartdb: I68 wrongly in, I65/I69/I73 missing) |
| Minimum precision of names (stage 2) | **`MIN_NAMED_PRECISION = 0,90`**, not F1 | F1 rewards "name everything V" (precision 37.9%). The device may stay silent, it may not be wrong 6 out of 10. Details: `docs/evaluate-walkthrough.md` §5 Tahap 2 |
| Shape of rhythm features | **3 columns** (RR_prev, RR_ratio, dRR): QRSw & RR ratio exist but are OFF | `PA_QRSW=1` / `PA_RR_RATIO=1` turn them on. On mitdb alone: F1 0.6911 → 0.6882 (not a signal) and the price is recall V 0.944 → 0.898, recall F 0.152 → 0.029. They only win when patching svdb damage. The C code is already there behind `#if ECG_RR_RATIO`/`ECG_QRSW`, compiled & proven not to interfere (17/17) |
| `RR+1` / delay 1 beat (G2) | **NOT used**, but already implemented | Because `PA_RR_RATIO` is not locked, the firmware does not delay beats. If it is enabled later: `ecg_live.cpp` judges `idx_hist-1`, the buffer does NOT change (r_hist[16] already holds RR+1, the 4 s ring is enough), plus `ECG_LIVE_TIMEOUT` 3 seconds for asystole with ratio sentinel 1.0 |
| `MAX_RHYTHM_SCALE` | **0.05**: assert in `quantize_int8` | The INT8 scale of the rhythm tensor is derived from the min/max of 300 calibration samples. One beat with an extreme RR there (record 207: RR_prev = 100 s) widens the scale ~30x and normal RR is left with a few levels → the rhythm branch is DEAD, and the symptom is "poor recall S", not an error. Probability 1.8%/seed. Healthy value 0.0129. Tested both ways |
| Imbalance strategy (K1 tested) | **balanced `class_weight` STAYS** | P1 Table 4 predicts precision +31 points if it is turned off; measured **+0.3 points**. The cause is that threshold calibration DOWNSTREAM absorbs the effect (threshold 0.40 → 0.15). Lesson: even a valid paper ablation does not transfer if there is an adaptive step they do not have. G1 CLOSED on the basis of our own ablation |
| Stage 2 (naming V/S) | **NOT shipped** | The QRS width rule reaches V name precision 91.7% on DS2, but VAL maximum is only 43.9%: 5 patients do not represent the diversity of V morphology. §7 no.4 forbids DS2 from certifying. `scripts/second_stage_rules.py` enforces it itself: without a threshold that passes, no name is shown |
| TFLM library | **`spaziochirale/Chirale_TensorFLowLite`** 2.0.0 | latest release in the PlatformIO registry, works with the Arduino framework. Reference kernels (no ESP-NN yet) → 26 ms/beat becomes the baseline; move to `esp-tflite-micro` if power becomes a constraint |
| PlatformIO board | **`4d_systems_esp32s3_gen4_r8n16`** | not a guess: the id comes from a test project that was already flashed & ran on this hardware |
| On-device segmentation | **compensation 38 + peak alignment ±25 + subtract group delay 4** | without any one of them R does not land at `WIN_PRE+4` (= **132**) and precision falls 4× (0.479→0.124); offset calibrated on DS1 |
| Jitter model | **empirical** (resample from `residu_ds1.npy`), not the paper's uniform ±18 | the measured residual is sharp-core-heavy-tail; uniform ±18 shifts 80% of beats that are actually locked. `seragam` stays so the δ=0..18 sweep is comparable to Table 3 of Dias 2021 |
| Jitter per beat | **independent**, even though in reality it is correlated per record | the correlation partly cancels in RR (RR = difference of two positions); independent overstates RR variance = pessimistic direction, safe |
| Clean copy during augmentation | **always included** (`--copies N` = N imitations ON TOP OF 1 clean copy) | 80% of beats on the device miss by ≤1 sample; that "exact" case is the majority, not an edge case |
| Ablation knobs | **environment** (`PA_WIN_PRE`, `PA_WIN_POST`, `PA_HOS`), not editing final values | without env, `config.py` gives exactly the same values → ablations do not touch a gate point. The winner is only locked through its default (still a gate point) |
| HOS feature (kurtosis+skewness) | **rejected** | 3 seeds: 0.6150±0.0509 vs 0.6354±0.0428 without HOS: full overlap. Not "harmful", but "no evidence of helping"; a feature without evidence still has to be ported to C & maintained. Code + `PA_HOS` knob left in for re-ablation |
| Record with anomalous channel | 114 (MLII idx 1); 102 & 104 without MLII → `raise` | 102/104 paced, dropped in Phase 3 as well |
| Non-beat filter | `BEAT_SYMBOLS` whitelist in `config.py` | unknown symbols get dropped, not let through |

## Pitfalls found so far

- **`wfdb.io.annotation.is_qrs` cannot be used to filter non-beats.**
  Symptom: `[`, `]`, `x`, `)` slip through as "beats". Cause: the wfdb table marks
  the start/end markers of ventricular flutter & non-conducted P-waves as QRS.
  Avoid: the explicit whitelist `config.BEAT_SYMBOLS` (15 AAMI symbols).
- **Equal array LENGTH ≠ aligned beats.** Symptom: none.
  `assert len(windows)==len(labels)` PASSES, loss falls smoothly, and it is only noticed in
  Phase 6 when recall is ~0. Cause: `segment_beats` drops edge beats (rec 100: beat
  0 & 2272), `compute_rr_features` drops beats without RR_prev (beat 0): the sets
  differ, the lengths can coincidentally match. Rec 100 simulated: 100% of rows shifted
  by 1 beat, 68 labels with the wrong symbol although the real arrhythmia count is only 34 (each
  arrhythmia corrupts 2 rows). Avoid: `prep_beats` computes `valid_beat_indices` FIRST,
  all arrays are taken from the same indices. RR is computed from the WHOLE `r` and only then
  sliced: cutting `r` first makes edge beats lose their neighbors.
- **The causal filter's group delay shifts the R-peak by +4 samples.** Symptom: the
  annotated R-peak line misses by ~11 ms to the left of the peak in FILTERED windows
  (`make plot1seg`). Cause: `sosfilt` only sees the past → the output lags.
  **Not a bug, do not correct it.** The shift is consistent (window 90/160: median 94, mean 94.03),
  so the model learns that position and the firmware produces the same thing as long as the
  SOS coefficients are identical. Correcting it in Python without correcting it in C = mismatch.
- **TFLite Micro computes the `MEAN` op differently from regular TFLite.** Symptom: model,
  weights, input, and quantization parameters identical, but PC 0.9727 vs device
  0.3359: all probabilities are squeezed toward the middle, **without any error**.
  Cause: `GlobalAveragePooling1D` → op `MEAN`; two different TFLM libraries give the IDENTICAL
  wrong numbers, so this is a property of TFLM, not a library bug. Avoid:
  `build_deploy_model` swaps to `DepthwiseConv1D` with weights 1/31 (the same average,
  a convolution op). It was only found because there is a PC↔device golden reference.
- **Pooling ops inherit the input quantization scale; convolution ops have their own scale.**
  Symptom: `AveragePooling1D` matches on 6 golden test beats, but DS2 recall falls
  0.655 → 0.528. Cause: the input scale 0.332 is also used for the output, while the
  average of 31 values is far smaller → ~3 bits of resolution wasted. Avoid: use a
  convolution op for the average. General lesson: **matching on a handful of test samples
  ≠ correct**; full-size verification is still needed.
- **The serial monitor grabs `/dev/ttyACM0`.** Symptom: `esptool` fails with
  `Errno 11: Could not exclusively lock port`: the message never mentions
  "monitor". Cause: the VS Code *Upload and Monitor* button is still alive. Avoid:
  `lsof /dev/ttyACM0` to find its PID.
- **The model collapses if the R-peak misses by 4 samples (11 ms).** Symptom (window 90/160): precision
  0.479 → 0.124, symmetric in both directions (R at index 90 or 98, not 94).
  Cause: three `MaxPooling1D(2)` = total stride 8, so a 4-sample shift is
  HALF a pooling bin: the phase of the representation entering GAP changes. The model
  never saw this variation because training uses precise annotations.
  Avoid: the firmware must put R at index `ECG_WIN_PRE + ECG_GROUP_DELAY`
  (**132** for window 128/128; do not memorize the number, `test_preproc.cpp`
  uses the formula). Robustness to small shifts is trained through jitter
  augmentation (Phase 6c).
- **The 200 ms Pan-Tompkins refractory period blocks premature beats.** Symptom:
  detector sensitivity for class S is only 0.6494 vs Normal 0.9614. Cause: supraventricular
  beats arrive too soon after the previous beat, right in the refractory
  window. The effect compounds with the S classification recall that is already
  0.3034. The trade-off of lowering the refractory period can be measured with
  `scripts/eval_detected_segmentation.py`.
- **The live flow load is bursty, not even.** Symptom: the average is only 82 us/sample
  (3% of the budget) but one sample can take 33.4 ms: 12x the budget. Cause:
  detection runs all at once over the 4 s ring, and happens to coincide with
  inference of the newly found beat. Avoid: ADC acquisition in a timer ISR puts
  into a queue (min 13 samples), processing drains it in the main loop. If run in sequence
  in a single flow, ~12 samples are lost every second and RR intervals are corrupted.
- **`.venv` is not used even though it exists.** Symptom: `make plot1` →
  `ModuleNotFoundError: No module named 'numpy'`. Cause: `PY := python` picks the
  pyenv shim, not `.venv/bin/python`. Avoid: `PY` in the Makefile picks
  `.venv/bin/python` automatically if it exists (no need for `source activate`).
- **Acquisition telemetry can lie, in three ways.** (1) **`lepas 0%` from the AD8232 LO
  is NOT a guarantee that there is signal**: LO only needs one low-impedance path,
  and the RL electrode alone already satisfies it; six empty recordings all
  reported `lepas 0%`. (2) **The `make pull` file name = PULL time, not recording
  time** (`pull_recording.py:77` uses `datetime.now()`): a stale recording
  looks new if you forget to press REC. (3) **An ohmmeter on a powered circuit
  gives a wrong number without any sign**: RA–LA read ~0 Ohm (concluded
  shorted), repeated with the power off it became thousands of ohms. Avoid: make the **absolute
  ADC swing** the referee, not the flag. Conversion: 12-bit + atten 11 dB =
  0.757 mV/count, AD8232 gain ~1100 → a healthy ECG ~2 mV (~3000 counts);
  **below ~0.1 mV (~150 counts) means no biopotential at all**,
  and that is not a lead placement problem (bad placement cuts 3–5x,
  not 50x).
- **A locked seed, the result still changes.** Symptom: `np.random.seed(42)` +
  `tf.random.set_seed(42)`, identical code, run twice → DS2 F1 0.6209 vs
  0.5882 (jitter variant). Cause: oneDNN thread scheduling on the CPU changes the order of
  float summation; that small difference picks a different stopping epoch through
  EarlyStopping, and `restore_best_weights` restores different weights.
  Avoid: **never conclude an ablation from one run.** At least 3, report
  mean ± range. In this repo a difference < ~0.04 F1 is not a signal.
- **Training on "corrupted" data raises the numbers on CLEAN data.** Symptom
  (a pleasant one): jitter augmentation raises annotation DS2 F1 0.5660 →
  0.6354, although annotation DS2 has no jitter at all. Cause: the old model
  depended on the exact window phase (three `MaxPooling1D(2)`, stride 8);
  jitter forces it to learn a shape that does not depend on phase: regularization, like
  random crop in computer vision. Lesson: augmentation that imitates deploy
  error is not just "preparing for bad conditions", it improves the model.
- **Plausible physiological reasoning can be wrong, and a proper ablation
  proves it.** Symptom: the argument "`WIN_PRE=90` already contains the P wave
  (PR interval 43-72 samples), so the paper's 128 only buys baseline"
  sounds strong, and loses. `w128` (128/127) F1 0.6775 vs 0.5660 baseline.
  The key to the proof is the third variant: `w112` (112/144) has the SAME length 256,
  divisible by 8, longer T coverage, and the result equals the baseline. So
  what pays is not the window length, not the multiple of 8, but the **pre-R context**.
  Avoid: every claim "X is already enough" needs a comparison variant that isolates
  X, not just a bigger variant.
- **Float inside an ISR kills the ESP32, slowly, not instantly.** Symptom:
  `Guru Meditation Error: Core 1 panic'ed (Coprocessor exception)`, `EXCCAUSE
  0x00000004`, then reboot. It shows up at **second 18**, not second 0, so it passes
  a 20-second test and passes the build. Cause: the ESP32 does not save FPU registers on
  entering an ISR; a float operation there corrupts the FPU state of the interrupted task, and
  the panic only blows up when that task is scheduled again. Avoid: convert in
  `setup()` to an integer table, the ISR only copies (`sim_counts[]` in `main.cpp`).
  **The derived symptom is more deceptive than the crash itself**: the board reboots silently →
  `replay` goes back to `false` → the next measurement reports plausible numbers
  (2 beats/second) but from the wrong object (ADC noise, not replay).
- **How the serial port is opened decides whether the board resets.** Symptom: the board
  reboots (`=== MONITOR ARITMIA SIAP ===`) as soon as the script opens the port, the toggle
  that was "already pressed" is lost, and **the recording session in progress is lost
  entirely** (buffered in PSRAM until stopped). Measured 22 Oct 2026 on
  `/dev/ttyACM0` (ESP32-S3 USB-Serial-JTAG): the pattern `s.dtr = s.rts = False`
  before `s.open()` reset the board 5 out of 5 times, including the recording session
  `rekam=1 n=1803` that was lost; the default `serial.Serial(port, baud)` without
  touching DTR/RTS did not reset it 3 out of 3 times and the recording session survived
  (n 1,450 → 3,461 between two openings). `make pull` uses the default pattern, so it is
  safe. The DTR/RTS False pattern is used only when a clean boot is actually wanted
  (`measure_power.py` waits for `MONITOR ARITMIA SIAP`; `pull_power.py` and
  `record_flow_check.py` wait for the board to answer). After opening the port,
  **verify the state** from the board's reply (`replay ON`, `rekam=1`, swing in
  `s`), do not assume it.
- **Without electrodes, the device invents arrhythmia: ~2 beats/second, 57% "ARITMIA".**
  Cause: the adaptive Pan-Tompkins threshold is relative to the signal that is present, so
  "no signal" is not a condition it recognizes: even 15 counts of noise has
  peaks. Consequence for HW-6: **MQTT publishing must be gated by the signal
  quality assessor (the BAIK phase from contact: LO±, `THRESHOLD_SWING`, `THRESHOLD_HUM`), not by whether a beat exists.** Otherwise,
  a loose electrode = a flood of false alarms to the broker.
- **"Epoch" misleads as a unit of training length: the production model is
  the result of ONE epoch.** Symptom: none. Training finishes normally, metrics are reasonable,
  zero errors. It was only noticed because the `val_auc` curve was printed while diagnosing something
  else (Phase G/T7). Cause: augmented DS1 121,857 beats ÷ `BATCH_SIZE` 64 =
  **1,905 gradient steps per epoch**; for 6,417 params with Adam 1e-3, one
  epoch is already enough to memorize. `val_auc` peaks at **epoch 0** then falls
  monotonically, `patience=8` trains 8 epochs that are all thrown away. Augmentation ×3
  in Phase 6c multiplied the steps/epoch and **nobody revisited the
  training schedule**. Avoid: every time the training data size changes, print the
  `val_auc` curve once and look at where the peak is; do not judge training length
  from the number of epochs. Details: `docs/train-walkthrough.md` §6b.
- **The 0.04 threshold applies to the MEAN OF 3 SEEDS, not just one run.** Symptom:
  identical configuration, identical seed, run twice on the same day →
  DS2 F1 0.6911 vs 0.6535 (difference 0.0376). Cause: the same as the oneDNN pitfall
  above, but it does not go away just by averaging 3 seeds. Consequence:
  repeating 3 seeds does **not** lift a small difference into a signal; what
  raises the discriminating power is a larger test set (`ablasi.py --cross-db`,
  39 held-out patients). Some of the "not a signal" verdicts of Phase A–F become weaker,
  not stronger.
- **Waiting on the network inside a loop that drains the ADC queue = lost samples.**
  Symptom: `antrean 255/256`, `sampel hilang 4493`, repeated `PUBACK timeout`.
  Cause: a 256-sample queue @360 Hz is only **711 ms** deep, so any
  blocking call longer than that starts dropping samples and corrupting RR
  intervals: exactly the failure the HW-4 architecture (ADC in the ISR) was built to
  prevent. Three culprits were found in sequence: waiting 3 s for PUBACK (4,493 lost),
  `sock.connect()` without a limit while the broker was BOOTING (2,788), waiting 1.5 s for CONNACK
  (290). Avoid: all network waits are collected **across iterations** of `loop()`
  (state machine), and `sock.connect(ip, port, 300)`: use `IPAddress`, because
  DNS resolution is a SEPARATE blocking call that is not bounded by the
  timeout argument. Final result: **0**. Details: `docs/mqtt-walkthrough.md` §7b.
- **A `sock.write()` that does not finish makes the MQTT packet truncated, and the symptom
  points at the broker.** Symptom: repeated `PUBACK timeout` although the broker is healthy,
  ONLY while the backlog is drained, and the **broker log is clean**: zero clues on
  that side. Cause: the packet was written in 6 separate calls and the return value was ignored;
  a large payload (16 beats ≈ 4.8 KB) was not fully written, the broker waits for the remainder that
  never comes. Avoid: assemble ONE packet, ONE `write()`, and check the
  length. General lesson: a sender that does not check how many bytes were
  actually sent will blame the receiver.
- **RAM/Flash numbers can lie if the credentials are not there.** Symptom: a build
  "SUCCESS" reports RAM 26.4% / Flash 8.0%; with `wifi_secrets.h` filled in the same figures become
  **33.1% / 13.4%**, a difference of 358 KB of flash. Cause: without that file
  `WIFI_SSID` is `""`, `strlen("")` is folded into a constant, `WiFi.begin()`
  becomes dead code, and the whole WiFi stack is not linked. The difference is not
  announced anywhere. Avoid: measure the build size in the SAME configuration
  as the one used, and state the condition when recording the numbers.
- **Nagle holds small segments; PUBACK becomes late by 1–4.8 seconds.** Symptom:
  random `PUBACK timeout` although the broker is healthy, long-tailed end-to-end latency
  (p95 13.3 s), and a PUBACK RTT that **repeats at ~1,250 ms**. Cause: the payload of
  one beat ~330 B = a small segment, and Nagle holds it until the ACK of the previous
  segment arrives; paired with the broker's delayed-ACK it becomes ~1.25 seconds.
  Avoid: `sock.setNoDelay(true)` after connect. Result: p95 13,259 → **3,402
  ms**, `gagal` 4 → **0**, PDSR 96.7 → 99.5%. What found it was not reasoning
  but an **RTT counter + printing `sock.available()` on timeout** (0 bytes =
  not desync, the broker simply had not answered yet).
- **An unsolicited MQTT packet must still be read.** Symptom: the same as above,
  so two bugs with identical symptoms lived side by side and fixing one did not
  remove the symptom. Cause: PINGREQ is sent every 30 s, PINGRESP
  (2 bytes `0xD0 0x00`) was never read, settled in the socket, then was read
  as the first two bytes of the next PUBACK → the read stream desyncs until
  reconnect. Avoid: read the 2-byte header and **discard the content of other packets entirely**
  so the next bytes fall on a packet boundary. Lesson: if the correct fix
  does not remove the symptom, do not reason about the next suspect: add a
  counter until the symptom has a number.
- **`time()` has 1-second resolution, and its error disguises itself as latency.** Symptom:
  the minimum end-to-end latency shifted 934/1,045/1,286/1,347 ms between boots with
  nothing changed in the system, then once jumped uniformly to 3,437 ms at ALL
  percentiles. Cause: `ts_base_ms` was computed from `time(NULL)`, which has second resolution,
  so the rounding enters every `ts` sent: a systematic error of 0–1,000
  ms per boot, constant throughout the session. Avoid: `gettimeofday()`, and the measuring tool on
  the other side MUST measure the clock difference of both sides then correct for it (the board
  prints `epoch_ms` in the status line). **Distinguishing sign:** a shift that is uniform
  across all percentiles = clock difference; real latency shifts the tail more
  than the median. This error is easily read as
  broker latency, while the directly measured broker RTT is only 1.1 ms median
  (`dashboard/probe_rtt.py`).
- **Blaming a distant component long before measuring it.** Symptom: poor p95 latency,
  and the most plausible explanation ("ThingsBoard shares the laptop with 9 containers")
  was written into a document without testing. Cause: the component that is hardest to measure is also
  the easiest to blame. Avoid: a direct probe: 40 lines of Python
  publishing 1/second to the SAME broker proved its RTT is 1.1 ms median, zero
  events >1 second, in 60 seconds. The board's clustered RTT pattern at
  **1.2 / 2.0 / 4.2 seconds** instead points to TCP RTO backoff 1-2-4 = packet loss
  on WiFi, and RSSI −50 dBm rules out the weak signal theory.
- **`import config` fails from `scripts/`.** Symptom: `ModuleNotFoundError` even when
  run from `model/`. Cause: `python scripts/x.py` puts `scripts/` in
  `sys.path[0]`, not the cwd. Avoid: a 1-line `sys.path.insert` shim (see
  `scripts/plot_phase0.py`); `conftest.py` already handles the pytest side.

## Knowledge channel

Claude Code sessions in this folder do **not** inherit the history of other sessions (history
is stored per working directory). This file is the only one that is always loaded:
write decisions here, not only in chat.
