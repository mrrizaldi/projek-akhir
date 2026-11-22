# Walkthrough map: TinyML model path, Phase 0 → 8

Entry point for learning this pipeline. Each phase has one document: the code
flow step by step, the mathematics behind it, the decisions along with the
alternatives that were rejected, real numbers, and comprehension check questions.

**This is a study document, not a specification.** The official specification is
`PRD_Model_Aritmia_TinyML.pdf`. The binding decisions are the decision point table
in `../CLAUDE.md`.

**Open work** (power consumption, emergency WiFi OFF, recording to the server, PCB rev2):
the dated list is in [`../CLAUDE.md` §Open work](../CLAUDE.md#open-work).
The official body-signal data is the 22 Oct 2026 afternoon session
([`../data/recordings/README.md`](../data/recordings/README.md)); development recordings
are archived in [`../data/arsip/rekaman-uji-coba/`](../data/arsip/rekaman-uji-coba/README.md).

---

## Data flow, one screen

```
data/raw/mitdb/*.dat  (48 MIT-BIH records, 30 minutes @360 Hz)
        │
   [0]  │  io_mitdb.py        select MLII channel, filter out non-beats
        ▼                     → signal, r_locations, symbols
        │
   [1]  │  preprocessing.py   CAUSAL bandpass 0,5-40 Hz, cut 256 samples,
        ▼                       z-score per window   → windows [K,256]
        │
   [2]  │  features_rr.py     RR_prev / RR_ratio / dRR + binary label
        │  prep_beats.py      valid_beat_indices → 44 × per_record/*.npz  [2b]
        ▼                     202.560 beats (DS1 ×3 jittered copies, DS2 clean)
        │
   [3]  │  dataset.py         split PER PATIENT (de Chazal 2004)
        ▼                     train.npz DS1 152.904 | test.npz DS2 49.656
        │
   [4]  │  model.py           morphology CNN + rhythm Dense → 6.417 params
        ▼
        │
   [5]  │  train.py           class_weight, EarlyStopping(val_auc)
        ▼                     → model_fp32.keras   (VAL @0,80: recall 0,654, F1 0,692)
        │
        │  calibrate_threshold.py   threshold 0,80 locked ON VAL
        ▼
   [6]  │  evaluate.py        DS2 opened ONCE → recall 0,700 AUC 0,933
        ▼
        │
   [7]  │  quantize.py        PTQ INT8 → 22,94 KB, recall delta +1,08%
        ▼
   [8]     check_poc.py       8/8 DoD verified
           export_model_h.py  → firmware/include/model_int8.h
        │
  [HW]  │  ecg_pipeline.cpp   preprocessing port to C, checked against the Python golden
        │  TFLite Micro       inference on the ESP32-S3: 26,6 ms/beat
        ▼  acquisition        AD8232 -> make pull -> make analyze -> plot
```

---

## Reading order

In order 0 → 7. Each document assumes the previous ones have been read.

| # | Document | Answers |
|---|---|---|
| 0 | [io-mitdb](io-mitdb-walkthrough.md) | Where the data comes from, why MLII, what is discarded before anything is computed |
| 1 | [preprocessing](preprocessing-walkthrough.md) | Why a causal filter, how Butterworth & Pan-Tompkins work, why a 256 window (128/128) |
| 2 | [features-rr](features-rr-walkthrough.md) | Why rhythm features are needed besides shape, how AAMI labels are mapped, the alignment trap |
| 2b | [prep-beats](prep-beats-walkthrough.md) | Who runs Phase 0-2 over the 44 records, which beats are dropped & the bookkeeping |
| 3 | [dataset](dataset-walkthrough.md) | Why a per-patient split, what identity leakage is |
| 4 | [model](model-walkthrough.md) | Why two branches, why GAP rather than Flatten, where the 6,417 params come from |
| 5 | [train](train-walkthrough.md) | Why accuracy is forbidden, how class weight works, why monitor AUC |
| 6 | [evaluate](evaluate-walkthrough.md) | Why the threshold is locked before DS2, which arrhythmia classes fail & why |
| 6b | [segmentasi-deteksi](detection-segmentation-walkthrough.md) | The cost of on-device segmentation: why a 4-sample shift drops precision 4×, and why the detector discards arrhythmia |
| 6c | [jitter](jitter-walkthrough.md) | How far the R-peak on the device really misses, why the paper's ±18 samples must not be copied, and why training with error actually raises the numbers on clean data |
| 7 | [quantize](quantize-walkthrough.md) | What changes under INT8, why a metric can "rise" while the model does not improve |
| HW | [firmware](firmware-walkthrough.md) | The port to C, the Python↔C golden harness, and why the `MEAN` op must be replaced for TFLM |
| HW | [acquisition](acquisition-walkthrough.md) | **Working guide**: recording from the body, pulling data, assessing quality, making plots |
| HW-6 | [mqtt](mqtt-walkthrough.md) | **Working guide**: two toggles (`y` signal source, `m` publishing), why the dummy is placed at the ADC rather than in the publisher, and why publishing is gated by contact quality (LO±, swing, hum) rather than by whether a beat exists |

Phase 8 has no walkthrough: its content is verification, not a new concept.
Run `make poc` and read `scripts/check_poc.py`.

---

## Traps that shaped the whole design

The traps that most determined the design:

| Trap | Symptom when hit | Covered in |
|---|---|---|
| **Non-causal filter** (`filtfilt`) | Smooth training, accuracy collapses on the device | [1](preprocessing-walkthrough.md) §2 |
| **Window ↔ label alignment** | `assert len(a)==len(b)` PASSES, recall ~0 in Phase 6 | [2](features-rr-walkthrough.md) §3, [2b](prep-beats-walkthrough.md) §1-2 |
| **Patient identity leakage** | A 99% accuracy that means nothing | [3](dataset-walkthrough.md) §1 |
| **Threshold tuned on DS2** | Good numbers that fall apart when an examiner asks | [6](evaluate-walkthrough.md) §0 |
| **Same op, different result in TFLM** | Model correct on the PC, confidence collapses on the device | [HW](firmware-walkthrough.md) §5 |
| **R-peak off by 4 samples** | Precision drops 4×, with no error | [6b](detection-segmentation-walkthrough.md) §2 |
| **Threshold calibrated under the wrong conditions** | AUC nearly intact but F1 drops 20% | [6c](jitter-walkthrough.md) §4 |

Most of these traps **produce no error at all**. That is the common thread: the
most expensive bug in ML is not the one that crashes, but the one that produces
good numbers from a flawed procedure.

---

## Key numbers (quick reference)

Installed configuration (window 256 + jitter augmentation, Phase 6c):

```
dataset     44 records, 202.560 beats — DS1 stacked 3 copies (1 clean + 2 jitter)
split       DS1 152.904 (10,1%) | DS2 49.656 (11,0%, NEVER jittered)
window      128/128 = 256 samples, R lands at index 132 (128 + group delay 4)
model       6.417 params (Conv1D does not depend on window length)
threshold   0,80  (maximum F1 on VAL; VAL is jittered too)
DS2 fp32    recall 0,6996  precision 0,6235  F1 0,6594  AUC 0,9334
DS2 INT8    recall 0,7105  precision 0,6169  F1 0,6604  AUC 0,9344   22,94 KB
device      26,6 ms/beat, tensor arena 12.948 B
per class   V 0,9248 | S 0,4390 | F 0,0670
detection seg. F1 0,6499 (annotation 0,6594), system recall 0,6035
```

Comparison baseline (window 90/160 = 250, no augmentation, threshold 0.35).
This configuration is no longer used; its numbers are kept as the reference point
for the Phase 6c improvement:

```
dataset     100.619 beats | DS1 50.965 | DS2 49.654
DS2 fp32    recall 0,6661  precision 0,4919  F1 0,5659  AUC 0,8866
DS2 INT8    recall 0,6549  precision 0,5302  F1 0,5859  AUC 0,8862
device      26,0 ms/beat, tensor arena 12.756 B, matches PC digit for digit
per class   V 0,9332 | S 0,3034 | F 0,1675
```

Phase 6c ablation (3 seeds, same evaluation chain) that underpins the installed
configuration; details in [jitter](jitter-walkthrough.md) §5:

```
baseline 90/160          F1 DS2 0,5660 ± 0,0202   AUC 0,8870
+ jitter augmentation    F1 DS2 0,6354 ± 0,0428   AUC 0,9084
+ window 128/127         F1 DS2 0,6775 ± 0,0112   AUC 0,9394
empirical jitter on DS2  F1      0,6670 ± 0,0194  (model w128, deploy condition)
```

Both improvements are locked in `config.py`: `WIN_PRE = WIN_POST = 128`
(window 256, the 128/128 variant from the Phase B ablation: F1 DS2 0.6911 ± 0.029),
`JITTER_MODEL = "empiris"`, `JITTER_COPIES = 2`, `THRESHOLD = 0.80`.

The two numbers that most need to be explainable at the thesis defense:

1. **DS2 accuracy 0.9207 is only 3 points above always guessing Normal (0.8902)**,
   even though always-Normal has recall 0 and the model 0.70; that is why accuracy
   is not used. → [5](train-walkthrough.md) §3, [6](evaluate-walkthrough.md) §4
2. **Recall F is only 0.0670**, and why that could be predicted as early as Phase 3
   (372 of the 414 F beats in DS1 are in record 208 alone). →
   [6](evaluate-walkthrough.md) §5

---

## Experiments not adopted

The multi-database, feature, and training regime experiments (Phases A–G) ended
with no configuration change. All were measured over 3–6 seeds, reported as mean ±
half-range, with a signal threshold of 0.04 F1 for the 3-seed mean, and DS2 only
diagnoses. The only result that entered production is the `MAX_RHYTHM_SCALE`
assert ([quantize](quantize-walkthrough.md)). The knobs remain in the code and are
byte-identical when off, so each ablation can be repeated with a single command
(see Supporting analysis tools).

Comparison false alarm burden: FPR 5.21% (2,302 FP out of 2,302 + 41,904 normal beats in DS2) at 60 bpm = 86,400 beats per day, about 89% normal (about 76,900 beats), equivalent to about 4,000 false alarms per day.

| Proposal | Verdict | Brief evidence | Reopened if |
|---|---|---|---|
| K1 `class_weight=None` | dropped | the paper predicts precision +31 points; measured +0.3 points on mitdb+svdb because the downstream threshold calibration absorbs it (threshold 0.40 → 0.15); recall S −0.076 | - |
| K2 `RR+1` / delay 1 beat | built, not locked | implemented through to the firmware (`#if ECG_RR_RATIO`, `ecg_live.cpp` scores `idx_hist-1`), dormant because K3 does not win | K3 wins |
| K3 ratio-shaped RR feature | dropped | part of the "new features" in the 2×2 table below: −0.003 on mitdb | - |
| K4 QRS width (mutual information rank 1–2) | dropped | on mitdb recall V 0.944 → 0.898, recall F 0.152 → 0.029; knob `PA_QRSW=1` | - |
| K5 `RR_local_avg` window 10 → 32 | stopped | the effect sought is smaller than the 0.04 noise floor | a test set with a noise floor < 0.02 exists |
| K6 weighted pooling replacing GAP | stopped | capacity is not the cause: the 6,417-param model is already larger than the main comparison (Farag 2023, 1,267 params, 1,245 trainable; INT8 15–18 KB vs 22.94 KB) | same as K5 |
| K7 first-derivative input | stopped | the paper wins on clean signal but falls below under AWGN noise; must be tested on body recordings | ≥ 3 body recordings swinging > 1,000 counts, tested on body recordings |
| K8 classes F and Q stay in binary | confirmed | even perfect recall F gives only +0.037 F1 (below the threshold); only S can move the main number (+0.113) | - |
| K9 no sklearn (mutual information) | confirmed | dependency gate; the paper's ranking is used as a hypothesis, validated by `ablasi.py` | - |
| K10 PTQ, not QAT | confirmed | PTQ meets the target; the rhythm-scale trap is closed by the `MAX_RHYTHM_SCALE` assert | - |
| T5 k-of-n rule | dropped | 65.3% of DS2 arrhythmia beats are single events; k ≥ 2 discards 87% of TP and keeps the clustered FP (`check_fp.py`) | - |
| T5b signal quality gate for classification | stopped in `model/` | MIT-BIH is too clean to calibrate a quality threshold; the quality gate lives in the firmware ([mqtt](mqtt-walkthrough.md) §3.1) | - |
| T6 scale/warp augmentation, volume per technique | stopped | furthest from the root cause; the difference between techniques is below the noise floor | - |
| T7 weight averaging (`--swa`) | dropped | F1 DS2 0.6911 → 0.6346; at LR 1e-3 there is no plateau to average ([train](train-walkthrough.md) §6b) | tested at LR 1e-4 |
| T9 focal loss | stopped | effect below the noise floor | same as K5 |
| T11 per-patient personalization | stopped | label-free calibration needs an unsupervised anchor that is still unclear | a scoping document first |
| T12 learning rate 1e-4 | built, not locked | AUC up on 4/4 sets, TEST-C F1 +0.124, recall F doubled, but recall S 0.4473 → 0.3126, real at the equivalent operating point ([train](train-walkthrough.md) §6b) | a user decision changes the class focus |
| Training database + svdb / + incartdb | dropped (mitdb only) | svdb +0.076 recall S but precision drops; incartdb AUC 0.8881 and recall S 0.331; the combination cancels out ([dataset](dataset-walkthrough.md) §4) | - |
| Gate A3: subsample F beats of record 208 | rejected | the perfect-F ceiling +0.037 is below the threshold; recall F is low because of patient coverage, not gradient weight | - |
| Larger threshold calibration set (+svdb, +incartdb) | not used | the F1 gap to the DS2 optimum narrows 0.034–0.068 → 0.014–0.020 (`check_calibration.py`, one seed), but using the held-out sets for calibration removes their role as TEST-B/TEST-C | held-out split into calibration/test, user decision |
| Stage 2 V/S naming | not shipped | V name precision 91.7% on DS2, at most 43.9% on VAL; DS2 must not certify (`second_stage_rules.py`) | a VAL that represents the diversity of V morphology |
| Window normalization replaced | withdrawn | the reference (Frontiers Digit Health 2026) leaks through baseline windows that overlap the test set; the z-score here is computed from the window itself so that mechanism does not exist | - |
| Test-time adaptation (BeatRhythm-TTA) | rejected | needs backprop at inference on 12-lead; cannot be deployed on the ESP32-S3 | - |
| GAN / BiLSTM augmentation | rejected | techniques 6–7 of Khosravi Khaliran 2024; the training cost and dependencies are out of proportion to a difference below the noise floor | - |
| Per-RR segmentation + 480-point resampling | rejected | normalizes the beat length so that information from a beat arriving too early is erased from the window; damages S detection | - |
| Khosravi Khaliran 2024 accuracy figure of 98.9% | not compared | a 17-class per-fragment protocol, random split, and 10-fold CV on an already-augmented dataset: two stacked leakages | - |

### One-screen summary

The 2×2 table of dataset × features (signal threshold: < 0.04 F1 is not a signal):

```
F1              OLD features (3)   NEW features (6)
mitdb only      0,6911 +-0,029    0,6882 +-0,023     <- the one DEPLOYED
mitdb+svdb      0,6262 +-0,063    0,6960 +-0,049

svdb hurts -0,065   new features recover +0,070   net +0,005
```

**A pure interaction, not two stacked improvements.** svdb lowers F1 through a
domain shift; the new features only patch that damage; the combination returns
to the starting point. Without the fourth cell (mitdb + new features), the
conclusion is wrong twice over.
The new features on mitdb+svdb make recall S more reliable (±0.156 → ±0.058), not
higher.

Origin of FP in DS2 (`check_fp.py`, 2,302 FP): 2 records contribute 56.6%, 8 records
92.4%. Per symbol: N 1,568 (FPR 0.043), L/LBBB 536 (FPR 0.130), R/RBBB 187
(FPR 0.054). L+R = 31.4% of FP: beats that AAMI calls Normal but whose QRS is wide
like a ventricular one. Record 222 (FPR 0.344) fails through the rhythm branch
(irregular rhythm: 9% nodal escape, 8% premature atrial).

The pattern repeated in K1, T12, and T5: proposals from papers do not transfer if
this pipeline has an adaptive step downstream that the paper does not have
(threshold calibration, per-beat labels). Even a valid paper ablation transfers
only if there is no adaptive step between the knob and the metric.

### Supporting analysis tools

| Script | Purpose |
|---|---|
| `scripts/check_lead.py` | Lead polarity & alignment across databases. Two columns (raw/aligned), two verdicts: do not mix them up. Knob `PA_CHECK_REC` = number of recordings per database (default 8), e.g. `PA_CHECK_REC=20 python scripts/check_lead.py` from the `model/` folder |
| `scripts/check_calibration.py` | How far the VAL calibration is from the DS2 optimum. DS2 diagnoses, does NOT select |
| `scripts/second_stage_rules.py` | V/S naming rules on top of the binary decision. Not shipped: VAL can only certify a precision of 43.9% |
| `scripts/ablasi.py --db` | Multi-database training. Default `mitdb` = the locked path, byte-identical |
| `PA_QRSW=1` `PA_RR_RATIO=1` | Phase D feature knobs. Without the env, the values equal the locked configuration |
| `scripts/check_fp.py` | Origin of the 2,302 FP: spread per record, TP vs FP run length, FP per symbol. The basis for dropping the k-of-n rule |
| `scripts/summarize_ablation.py` | Mean ± half-range per tag + verdict at the 0.04 threshold, so §7 is not computed by hand |
| `scripts/ablasi.py --swa N` | T7 knob: weight averaging of the N epochs with the best `val_auc`. Default 0 = the locked path |
| `scripts/ablasi.py --lr`, `--cross-db` | T12 knob (learning rate) and T8 (TEST-B/TEST-C evaluation, 39 held-out patients) |
| `scripts/check_operating_point.py` | Verification of the recall S trade-off at the equivalent operating point |

---

## How to rerun everything

```
make data && make check     # Phase 0  (once)
make prep                   # Phase 2  → per_record/*.npz
make split                  # Phase 3  → train.npz, test.npz
make train                  # Phase 5  → model_fp32.keras
python scripts/calibrate_threshold.py   # lock the threshold on VAL
make eval                   # Phase 6  → DS2 float32 metrics
make quantize               # Phase 7  → model_int8.tflite + delta table
make poc                    # Phase 8  → 8/8 checklist
make export                 # → firmware/include/model_int8.h
make test                   # 92 pytest tests
cd ../firmware && pio test -e native      # 23 tests on the PC (preprocessing, INA219, MQTT)
                  pio test -e esp32-s3    # preprocessing + inference on the board
```

The seed is locked (`config.SEED = 42`), so the numbers above must come out the same.
