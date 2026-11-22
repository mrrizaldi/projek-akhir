# Jitter walkthrough: robustness to segmentation error

> **Scope:** measuring the detector's R-peak position error, measuring its impact on the model, then training a model that is robust to it (jitter augmentation) and choosing the window size through ablation.
> **Related code:** `scripts/measure_jitter.py`, `scripts/sweep_jitter.py`, `scripts/ablasi.py`, `src/preprocessing.py` (`jitter_r`), `scripts/prep_beats.py`, `config.py` (`WIN_PRE`, `WIN_POST`, `JITTER_MODEL`, `JITTER_COPIES`, `USE_HOS`)
> **Prerequisite:** [`detection-segmentation-walkthrough.md`](detection-segmentation-walkthrough.md) (Phase 6b)

Phase 6c, outside the PRD. An adaptation of Dias et al. 2021 (*Arrhythmia classification from
single-lead ECG signals using the inter-patient paradigm*, CMPB 202:105948,
doi:10.1016/j.cmpb.2021.105948), the part that they ablated themselves.
`detection-segmentation-walkthrough.md` found the problem; this document measures
and fixes it.

---

## 0. One-screen map

```
                    cardiologist annotation     Pan-Tompkins on the device
                           │                          │
                           └──── the difference? ───────┘
                                      │
                         scripts/measure_jitter.py        ← Task 1: MEASURE
                                      │
                       residu_ds1.npy (pool of 50.601 differences)
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
        src/preprocessing.jitter_r()            scripts/sweep_jitter.py
        (used to train)                         (used to measure)  ← Task 2
                    │                                   │
                    ▼                                   ▼
        scripts/ablasi.py  ← Task 3-5            metric vs δ curve
        (train variants, compare)
```

In one sentence: **all Phase 6 numbers are cut from perfect annotated R-peaks,
whereas the device cuts from detections that miss; this document measures the price of
that difference, then trains the model to be robust.**

---

## 1. The problem, stated slowly

Phase 2 cuts windows from the `r` of the **cardiologist annotation**. That is the right decision
and remains right: the training path must be clean of detector error, otherwise
we never know whether the model or the detector is what is broken.

But that decision has a consequence. On the device, there is no cardiologist. What exists is `ecg_detect_r` → `ecg_align_r`, and its result misses.
`detection-segmentation-walkthrough.md` §2 already recorded how sensitive this model is:
**a shift of just 4 samples (11 ms) drops precision 0.479 → 0.124.**

So a metric measured with annotations is an upper bound, not a forecast.
The question: how far reality is from that upper bound.

Dias 2021 faced the same problem and solved it with one simple idea:
**if the R position on the device misses, just corrupt the R position in the training data,
then measure.** They called it *jitter*.

---

## 2. `scripts/measure_jitter.py`: do not borrow other people's numbers

The paper uses uniform jitter ±δ with δ ≤ 18 samples (50 ms), taken from the
QRS detection literature. They **do not have a detector**, so a borrowed number
was the only choice.

We have the detector. So the first step is not to imitate δ=18, but to measure.

The chain measured is exactly the chain the firmware runs:

```python
r_used = refine_peaks(pan_tompkins_detect(filtered, FS) - PT_DETECTOR_OFFSET, filtered)
pasangan = pair_detected(r_used, r_anot, tolerance)

cocok = pasangan >= 0
residu = r_used[cocok] - r_anot[pasangan[cocok]]
```

`refine_peaks()` and `pair_detected()` are **not rewritten**: both already exist
from Phase 6b (`scripts/eval_detected_segmentation.py`, `src/evaluate.py`). What
is new is only the collection of statistics.

DS1 only. The δ resulting from this script is used for training, and anything used for training
must not look at DS2.

### The result: the distribution is unlike anyone's guess

```
DS1: 51.021 beat anotasi, 50.601 terpasangkan, 420 terlewat (0,82%),
     2.605 deteksi palsu
residu : median 0,0   mean 0,14   std 6,07   p5 −3   p95 +2
|residu|: p95 18   p99 26   maks 54 sampel  (50 / 72 ms)
```

Notice that the last two lines quarrel: the signed residual p95 is only +2, but the p95
of its **absolute value** is 18. That is not a miscalculation, it is the sign of a heavy-tailed distribution.
The ECDF explains it:

| |residu| ≤ | proportion of beats |
|---|---|
| 1 sample | 79.85% |
| 2 samples | 90.22% |
| 3 samples | 92.27% |
| 5 samples | 93.15% |
| 10 samples | 93.57% |
| 18 samples | 95.00% |
| 26 samples | 99.00% |

Read it as: **93% of beats are practically locked on exactly** (≤5 samples), then ~7% miss
far, up to 54 samples. Not uniform, not normal: a mixture of
"locked on" and "lost track".

The tail has an address. Per record, `|p95|`:

| record | std | \|p95\| | note |
|---|---|---|---|
| 112, 115, 220, 230 | 0.4–0.7 | 1 | detector nearly perfect |
| 108 | 14.8 | 26 | 829 false detections |
| 203 | 10.8 | 30 | 126 missed beats |
| 207 | 17.4 | 28 | ventricular flutter |

So the tail is not a uniform property of the detector, but **a few noisy records**.
That matters for interpreting the results: a jitter-robust model is actually being
trained to be robust against *bad records*, not against everyday
imprecision.

One more thing was measured, and jitter cannot cure it at all:

```
beat terlewat per kelas AAMI: N 0,4%   F 1,7%   V 3,7%   S 6,8%
```

A beat that is never detected never reaches the model. No augmentation
helps a lost beat: that is the detector's business (the 200 ms refractory
period blocks premature beats, see the trap in `../CLAUDE.md`).

---

## 3. `src/preprocessing.jitter_r()`: three models, one default

```python
def jitter_r(r_locations: np.ndarray, delta: int = 0, rng=None,
             model: str = "empiris") -> np.ndarray:
    r = np.asarray(r_locations, dtype=np.int64)
    if model != "empiris" and delta == 0:
        return r
    rng = np.random.default_rng() if rng is None else rng

    if model == "empiris":
        jitter_pool = np.load(RESIDUAL_DS1)
        geser = rng.choice(jitter_pool, size=len(r)).astype(np.int64)
    elif model == "seragam":
        geser = rng.integers(-delta, delta + 1, size=len(r))
    elif model == "normal":
        geser = np.rint(rng.normal(0.0, float(delta), size=len(r))).astype(np.int64)
    else:
        raise ValueError(f"unknown jitter model: {model}")

    return np.maximum.accumulate(r + geser)
```

Three decisions in those lines:

**(a) Default `empiris`, not `seragam`.** The real distribution is sharp-core-heavy-tail;
uniform ±18 would shift the 80% of beats that are actually locked on. Resampling
from the real residual pool assumes no shape at all, and the test
`test_empirical_mimics_measured_distribution` keeps its variance at ~6 samples.
`seragam` is still provided so the δ=0..18 sweep can be compared directly with
Table 3 of the paper.

**(b) Per-beat jitter is INDEPENDENT, even though reality is correlated.** Record 108
is noisy throughout the record: its errors cluster, they are not random per beat. That correlation
partly **cancels itself out** in the RR feature, because RR is the difference of two positions:
if two neighboring beats both shift +20, the RR does not change at
all. Independent means the RR variance is **overstated**. That is the pessimistic direction,
so it is safe: the model is trained to face RR damage that is worse than reality.

**(c) `np.maximum.accumulate` preserves order.** A 54-sample tail could make two
beats swap places if the RR is short, and that produces a negative RR, a
failure mode that a real detector **cannot** produce (the 200 ms
refractory period = 72 samples prevents it). Preserving order is more honest than
allowing it.

### Only the knife shifts, not the diagnosis

In `prep_beats.process_record`, the jittered positions are used **entirely**:

```python
if jitter is not None:
    r = jitter(r)
idx = valid_beat_indices(len(signal), r)
windows = zscore_per_window(segment_beats(filtered, r[idx]))
rr = assemble_rhythm_features(r, windows, idx)
labels = np.array([to_binary_label(to_aami_class(sym[i])) for i in idx], dtype=np.int8)
```

If only the window is jittered while RR is still computed from the annotation,
the RR feature becomes a perfect information leak and the measured robustness is false.
A detector that misses damages both at once.

The label stays from the original annotation: what changes is **where we cut**,
not the patient's disease.

---

## 4. `scripts/sweep_jitter.py`: the metric as a curve, not a single number

The paper's Table 3 protocol, run on a model that is **not** retrained:
δ = 0, 2, …, 18, five seeds per δ, plus one `empiris` row.

The expensive part (reading the record + bandpass of 650,000 samples × 22 records) is done
**once** and cached; what is repeated per δ is only the window cutting. Without that
one sweep takes tens of minutes.

### Result: our model is far more fragile than the paper's model

The baseline model (window 90/160, no augmentation), threshold 0.35 calibrated on
clean VAL, DS2:

| jitter | recall | precision | F1 | AUC | recall S | recall V |
|---|---|---|---|---|---|---|
| annotation (δ=0) | 0.6661 | 0.4919 | **0.5659** | 0.8866 | 0.303 | 0.933 |
| uniform δ=2 | 0.7371 | 0.2813 | 0.4072 | 0.8520 | 0.471 | 0.942 |
| uniform δ=4 | 0.8288 | 0.1960 | 0.3170 | 0.8165 | 0.686 | 0.951 |
| uniform δ=18 | 0.7920 | 0.2113 | 0.3336 | 0.8191 | 0.624 | 0.935 |
| **empirical** | 0.7080 | 0.3335 | **0.4534** | 0.8586 | 0.410 | 0.935 |

Compare with the paper (Table 3): their N sensitivity goes 94.5 → 93.7 from δ=0
to δ=18. **Barely moves.** Ours: F1 0.566 → 0.317 at δ=4 alone.

The difference is that big because what is compared is not the same thing.
Their classification relies on **summary statistics** of the window (max, min,
variance, RMS, kurtosis, skewness), all of which are **shift-immune**: shifting the
window a little does not change the variance of its content. We use **Conv1D**, which
reads the waveform shape at specific positions, and three `MaxPooling1D(2)`
make a 4-sample shift = half a pooling bin.

That also explains Tables 6-8 of the paper: their RR and HOS groups are flat with respect to
jitter, while the morphology group collapses (SeS 79.1 → 68.0, Table 7). Our morphology branch
is the entire model.

### An interpretation trap: most of that damage is about the threshold

Notice the AUC column: 0.8866 → 0.8586 under empirical jitter. Down 3%. Meanwhile
F1 is down 20%. **The probability ordering is nearly intact; what broke is the operating point.**
Jitter shifts the whole probability distribution upward (a shifted window
looks "abnormal"), so the threshold of 0.35 calibrated on clean data
is suddenly too loose and FP explodes.

The consequence is important for reading every table in this section: **a retrained
model MUST have its threshold recalibrated**, and comparisons at a
fixed threshold of 0.35 would mislead.

---

## 5. `scripts/ablasi.py`: one variant, one process, the same chain

```
assemble DS1 (+ jittered copies) → split val per patient → train →
calibrate threshold on VAL → measure DS2 (annotation AND empirical jitter)
```

All variants pass through an identical chain; only one knob differs. Results
accumulate as rows in `artifacts/metrics/ablasi/ablasi.csv`.

The window size and HOS knobs are read by `config.py` **at import**, so they cannot be
changed in the middle of a process. That is why they go through the environment, and each variant runs
in its own process. The `config.py` default is 128/128 without HOS, so a variant
with window 90/160 must state its window explicitly:

```bash
PA_WIN_PRE=90  PA_WIN_POST=160          python scripts/ablasi.py --tag bersih
PA_WIN_PRE=90  PA_WIN_POST=160          python scripts/ablasi.py --tag jitter --jitter empiris --copies 2
PA_WIN_PRE=128 PA_WIN_POST=127          python scripts/ablasi.py --tag w128   --jitter empiris --copies 2
PA_WIN_PRE=112 PA_WIN_POST=144          python scripts/ablasi.py --tag w112   --jitter empiris --copies 2
PA_WIN_PRE=90  PA_WIN_POST=160 PA_HOS=1 python scripts/ablasi.py --tag hos    --jitter empiris --copies 2
                                        python scripts/ablasi.py --tag w128b  --jitter empiris --copies 2
PA_WIN_PRE=128 PA_WIN_POST=127          python scripts/ablasi.py --tag w128s3 --jitter empiris --copies 3
```

Each line is repeated with `--seed 42`, `--seed 7`, and `--seed 13`.

Without env, `config.py` uses its default values, so the ablation does not change
the final values and does not touch a gate point. The winning variant is locked by
changing the default in `config.py`, and that is a user decision.

**The clean copy is always included** (`--copies N` = N jittered copies ON TOP of one
clean copy). The reason is in the §2 numbers: 80% of beats on the device miss by ≤1 sample,
so the "exact" case is not a rare case that may be sacrificed.

### Before reading the results: one seed is not enough, and this is not a platitude

A single run per variant cannot be trusted. Two runs with the **same seed and the
same code** give different numbers (DS2 F1 annotation):

| variant | run-1 (seed 42) | run-2 (seed 42) |
|---|---|---|
| clean | 0.5669 | 0.5642 |
| jitter | 0.6209 | **0.5882** |
| w128 | 0.6676 | 0.6657 |

`np.random.seed` + `tf.random.set_seed` do **not** lock the result on CPU:
oneDNN thread scheduling changes the order of float summation, and in a model that
stops through EarlyStopping that small difference picks a different epoch.

That is why each variant is run **3 times** and what is reported is the mean ±
half-range. A difference below ~0.04 F1 here is **not a signal**.

The run-1 column comes from `artifacts/metrics/ablasi/ablasi_seed42.csv`: the first
batch of five variants (`bersih`, `jitter`, `w128`, `w112`, `hos`), all seed
42, written before `ablasi.py` had a `seed` column. Its header differs from
`ablasi.csv`, so that file is deliberately not merged and is not read by
`summarize_ablation.py`; it is kept as evidence of the nondeterminism above.
`ablasi.csv` holds all runs tagged with a seed; delete that file to start
clean. The `menit` column records the duration of one process from assembly to measurement:
0.6–0.8 minutes without augmentation, 1.1–2.0 minutes for mitdb variants with
`--copies 2` or 3, 1.5–10.1 minutes for multi-database variants (`fb_*` and
`fd_*`), and 1.5–4.2 minutes for follow-up mitdb runs (`t8_*` and `g_*`), all
CPU without GPU.

Each variant gets its own threshold from the VAL calibration (0.40–0.90 across the first five
variants), so variants are judged by F1 and AUC, not recall alone:
recall at two different operating points is not comparable.

### Result: three seeds per variant, DS2

| variant | window | F1 annotation | AUC annotation | F1 jitter | threshold |
|---|---|---|---|---|---|
| `bersih` (baseline) | 90/160 | 0.5660 ± 0.0202 | 0.8870 ± 0.0191 | 0.5423 ± 0.0359 | 0.40–0.50 |
| `jitter` | 90/160 | **0.6354** ± 0.0428 | 0.9084 ± 0.0163 | 0.6154 ± 0.0353 | 0.60–0.80 |
| `w128` | 128/127 | **0.6775** ± 0.0112 | **0.9394** ± 0.0047 | **0.6670** ± 0.0194 | 0.55–0.85 |
| `w112` | 112/144 | 0.5786 ± 0.0311 | 0.9069 ± 0.0113 | 0.5607 ± 0.0337 | 0.55–0.85 |
| `hos` | 90/160 + HOS | 0.6150 ± 0.0509 | 0.8882 ± 0.0363 | 0.6099 ± 0.0501 | 0.55–0.70 |
| `w128b` | 128/128 | **0.6911** ± 0.0290 | 0.9373 ± 0.0087 | **0.6750** ± 0.0208 | 0.50–0.75 |
| `w128s3` | 128/127, 3 copies | 0.6099 ± 0.0254 | 0.9146 ± 0.0163 | 0.5964 ± 0.0242 | 0.45–0.90 |

Variants other than `bersih` use `empiris` jitter; the number of jittered copies is 2,
except `w128s3` (3).

**1. Jitter augmentation wins, and wins TWICE.** The `jitter` range
[0.593–0.678] does not overlap with `bersih` [0.546–0.587]. The unexpected part: the
improvement also appears on **annotated DS2**, which is clean data with no
jitter at all. So jitter here is not just "training the deploy condition",
it works as **regularization**: the model is forced to stop depending on
exact phase and learn a more general shape. The very same effect as
random crop in computer vision.

**2. The paper's window wins, and the reason is not a physiological argument.** `w128`
beats all variants with window 90/160 in every column, with the narrowest range
(±0.0112 F1, ±0.0047 AUC). The counter-argument, "250 is enough, all the paper
buys is a baseline" (§6), does not hold.

But notice `w112`: its length is the **same** 256 samples, divisible by 8, and
its T coverage is longer than `w128`. The result is equal to the baseline, far below
`w128`. So what pays is **not** the window length and **not** the multiple of 8,
but **the 128 samples of context before R**. The PR segment and the baseline before P
carry information, not empty space.

### Per symbol: where that window actually pays

The aggregate hides the mechanism. Recall per AAMI superclass (3 seeds):

| variant | `WIN_PRE` | recall S | recall V | recall F |
|---|---|---|---|---|
| `bersih` | 90 | 0.268 ± 0.044 | 0.933 | 0.308 |
| `jitter` | 90 | 0.271 ± 0.025 | 0.922 | 0.169 |
| `w112` | 112 | 0.369 ± 0.061 | 0.933 | 0.138 |
| `w128b` | 128 | 0.422 ± 0.156 | 0.944 | 0.152 |
| `w128` | 128 | 0.487 ± 0.172 | 0.942 | 0.196 |

**Recall V barely moves** (0.91–0.94 across all variants). Ventricular beats
have an oddly wide QRS: a window of any size captures it.

**Recall S rises monotonically with `WIN_PRE`**: 90 → 0.268, 112 → 0.369, 128 → 0.42–0.49.
This is the mechanism, and it makes physiological sense: supraventricular beats
are distinguished by the **P wave and PR interval**, exactly what sits on the left side of the
window. Adding context before R gives the model more P evidence.

This **refutes** the physiological argument in §6: "PR is 43–72 samples, so
`WIN_PRE = 90` already contains P with room to spare". The P wave does fit, but fitting
alone is not enough. The model needs P **along with the baseline before it** to know that
what it sees is a P, not a ripple. What the extra 38 samples buy is context, not
coverage.

There is a price, stated honestly: **recall F drops** (0.308 → 0.15–0.20). Fusion beats
are a mixture of normal and ventricular morphology, and the shorter T coverage
(160 → 128 samples) cuts half of their evidence. Class F is only ~390 beats in DS2 and
its range is wide, so do not over-interpret it, but do not hide it
either. The exchange: **+0.15 to +0.22 recall S traded for −0.11 to −0.16
recall F**, and S is ten times more numerous in DS2.

**3. HOS is not proven to pay.** Its mean is below `jitter` (0.6150 vs
0.6354) but its range is the widest of all variants (±0.0509) and overlaps
fully. The honest conclusion is not "HOS damages", but **"there is no
evidence HOS helps"**, and a feature without evidence still has to be reimplemented
in C, tested, and maintained. Rejected because of cost, not because it was proven
bad.

**4. The configuration locked in `config.py`.** `WIN_PRE/WIN_POST = 128/128`,
`JITTER_MODEL = "empiris"`, `JITTER_COPIES = 2`. The 128/128 form (`w128b`) was
chosen over 128/127 because the result is equivalent (0.6911 vs 0.6775, a difference below the
0.04 threshold) and the length of 256 is divisible by stride 8 so that the pooling chain
256 → 128 → 64 → 32 runs without truncation. Three jittered copies
(`w128s3`, 0.6099) are worse than two (`w128`, 0.6775), so two. The production model's
threshold was recalibrated on VAL and became 0.80; its DS2 result is in
[`evaluate-walkthrough.md`](evaluate-walkthrough.md) §4 (F1 0.6594, one training
run, still within the spread of the `w128b` runs).

---

## 6. Window size: two competing arguments

The paper uses 256 samples: 128 before R, 127 after. This repo's baseline is 250:
90 before, 160 after. The total length is nearly the same (711 vs 694 ms); what differs is the **position of R**.

| | pre-R | post-R |
|---|---|---|
| baseline | 90 samples = 250 ms | 160 samples = 444 ms |
| paper | 128 samples = 355 ms | 127 samples = 353 ms |

The physiological argument for 90/160: the normal PR interval is 120–200 ms = 43–72 samples,
so `WIN_PRE = 90` already contains the P wave with room to spare, and the paper's extra 38 samples
only buy a baseline before P. Conversely on the right: at
slow heart rates, the T wave can exceed 353 ms; the paper's window cuts it off,
the baseline window does not, and a wide T is precisely a marker of ventricular beats.

The arithmetic argument for 256: the total CNN stride = 8 (three poolings), and
256 is divisible by 8 whereas 250 is not (250 → 125 → 62 → 31, with rounding).

Because there is a physiological argument for 90/160 and an arithmetic argument for 128/127,
an experiment was decided on. A third candidate, **112/144 = 256**, takes the multiple of 8
without cutting T.

**The result (§5) breaks the physiological argument above.** `w128` wins,
`w112` does not, even though `w112` has the same length and a longer T coverage.
The only thing that distinguishes `w128` is the 128 samples before R.

The methodological lesson is bigger than the numbers: the reasoning "the P wave
already fits in 90 samples, so 128 just buys a baseline" is **plausible
but not true**. What decides is the experiment, not the argument that reads well.

---

## 7. HOS: two scalars that are nearly free

The paper uses kurtosis and skewness (Eq. 12-13). Alone, these features are **poor**:
class S sensitivity is only 2.2% (Table 8). What is interesting is not their strength,
but that they are **flat with respect to jitter**: 2.2 → 17.0 from δ=0 to δ=18, rising,
not falling. Statistical moments do not care if the window shifts a little.

In this repo the cost is almost zero, because the incoming window is **already z-scored**:

```
mean = 0, std = 1  →  denominator of Eq. 12-13 becomes 1
kurtosis = mean(s⁴)      skewness = mean(s³)
```

Two passes over 256 floats already in RAM. On the MCU that is not noticeable.

Attached to the **rhythm branch**, not the morphology branch: two scalars are not a time
series, and the RR branch is where summary features gather. `N_RR_FEATURES`
becomes 5 and the model adjusts by itself: one source of truth, no twin numbers
in two places.

**The result: not proven to pay** (§5, point 3). Its mean is below the variant
without HOS and its range is the widest of all variants. Most likely
because Conv1D already reads the whole window shape: the 3rd and 4th moments do not
add anything it has not already seen, unlike the paper's linear classifier, which
only has summaries.

Not adopted. The `hos_features` code is left in `src/features_rr.py`
along with the knob `PA_HOS`: repeating its ablation (for example for another
window configuration) takes a single command, and what is expensive is not those 5 lines but
rediscovering how to test them.

---

## 8. What is deliberately NOT done

- **The paper's two-moving-average filter (200 ms & 600 ms) was not adopted.** Cheaper
  on the MCU (no recursive IIR, no group delay), but the paper **never
  ablated it**: not a single table compares its filter
  with an alternative. A precedent, not evidence. A preprocessing improvement candidate
  with evidence is the multi-stage denoising + motion artifact detection paper, and
  that answers our real problem (noisy body recordings), not the MIT-BIH problem.
- **Classes F & Q were not dropped** even though the paper drops them. Our problem definition is
  binary (Normal vs Arrhythmia) and F/Q go into Arrhythmia. This is a methodological difference
  that is **recorded as a comparison limit**, not changed: the paper's SeS 92.5 is
  not directly comparable with our recall.
- **The paper's RR features (`ln`, median ±15 beats, whole-record mean) were not
  tested.** `ln` helps a linear classifier (LDA) because it makes the distribution more
  symmetric; for an NN with already-normalized inputs the benefit is unclear.
  The whole-record mean is also not causal: on the device, the "whole record"
  does not exist yet when the first beat arrives.
- **Augmentation is not run per epoch.** Windows are cut up front, so
  jitter is static: N fixed copies, not a new draw each epoch.
  Per-epoch needs a generator that re-cuts from the raw signal: that is a
  rework of the data path for a benefit not yet proven necessary.
- **Undetected beats are not simulated.** Jitter moves the
  window; it cannot imitate a beat that is missing entirely (0.82% in DS1,
  6.8% for class S). That is a detector problem and is measured separately in Phase 6b.

---

## 9. Comprehension check

1. Why does `jitter_r` return `np.maximum.accumulate(r + geser)` and not
   just `r + geser`? What failure mode is prevented, and why is that mode
   impossible on a real detector?
2. The measured residual has a signed p95 of +2 but an absolute p95 of 18. How can those two numbers
   coexist, and what does it mean for choosing the jitter model?
3. In the sweep, AUC only drops 3% while F1 drops 20%. What is broken, and
   what is the cheapest fix?
4. Why **must** the RR feature also be computed from the jittered positions?
   What would happen to the robustness figure if it were computed from the annotation?
5. The paper reports that jitter barely lowers its performance, ours collapses.
   Name one architectural difference that explains it.
6. Why is the clean copy still included when training with jitter augmentation?

## 10. Supporting scripts

| Script | Content |
|---|---|
| `scripts/measure_jitter.py` | measure the alignment residual in DS1 → CSV, PNG, `residu_ds1.npy` |
| `scripts/sweep_jitter.py` | DS2 metrics as a function of δ (the paper's Table 3 protocol) |
| `scripts/ablasi.py` | one variant end-to-end → a row in `ablasi.csv` |
| `tests/test_jitter.py` | the properties of `jitter_r` that, if broken, make the results lie |
