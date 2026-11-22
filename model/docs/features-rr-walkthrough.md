# Walkthrough `src/features_rr.py`: Phase 2

> **Scope:** mapping beat symbols to a binary label and the three rhythm features (RR_prev, RR_ratio, dRR) per beat.
> **Related code:** `src/features_rr.py`, `config.py` (`AAMI_MAP`, `ARRHYTHMIA_SYMBOLS`, `RR_LOCAL_WINDOW_BEATS`), `scripts/prep_beats.py`, `tests/test_features_rr.py`
> **Prerequisite:** [`preprocessing-walkthrough.md`](preprocessing-walkthrough.md)

A study document, not a specification. The official specification remains
`PRD_Model_Aritmia_TinyML.pdf` pp. 10–11. A continuation of
[`preprocessing-walkthrough.md`](preprocessing-walkthrough.md) (Phase 1).

All numbers here are from **the whole of record 100** (2273 beats, `fs = 360 Hz`).
Reproduction:

```
cd model
.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
import numpy as np
from src.io_mitdb import load_record
from src.features_rr import compute_rr_features
sig, r, sym, fs = load_record('100')
print(compute_rr_features(r)[:5])
"
```

> The file `src/features_rr.py` is deliberately **without comments**. The explanation is here:
> the code is kept as short as possible so it is easy to read as an equation and
> easy to match against its C port (`firmware/src/ecg_pipeline.cpp`).

---

## 0. The big picture: where Phase 2 stands

Phase 1 produces the **shape** (morphology) of each beat. Phase 2 adds
**rhythm**, then gives each beat a label.

```
 load_record()  →  signal, r_locations, symbols
        │                  │                │
        │ (Fase 1)         │ (Fase 2a)      │ (Fase 2b)
        ▼                  ▼                ▼
  bandpass → segment   compute_rr_       to_aami_class
  → z-score            features()        → to_binary_label
        │                  │                │
   windows [K,256]     rr [K,3]         labels [K]
        └──────────────────┴────────────────┘
                           │
                  valid_beat_indices()   ◄── prep_beats.py, BUKAN src/
                           │
                    data/processed/per_record/<rec>.npz
```

The model receives **two inputs**: a 256-sample morphology window and a
3-number rhythm vector. Both are mandatory: a PVC and a normal beat can look similar in shape,
and what distinguishes them is precisely its premature arrival.

---

## 1. Two label stages: why not directly 0/1

```python
def to_aami_class(symbol: str) -> str:
    return AAMI_MAP[symbol]

def to_binary_label(aami_class: str) -> int:
    return int(aami_class in ARRHYTHMIA_SYMBOLS)
```

Three successive narrowings:

```
anotasi wfdb   ~40 simbol   "N" "L" "V" "A" "+" "~" "|" ...
     │  load_record()  ← whitelist BEAT_SYMBOLS (INI yang memfilter)
     ▼
beat saja      15 simbol   "N" "L" "V" "A" ...
     │  to_aami_class()   ← memetakan, tidak membuang
     ▼
superclass AAMI  5 kelas   N  S  V  F  Q
     │  to_binary_label() ← mengerucutkan
     ▼
label biner      2 kelas   0 = Normal, 1 = Aritmia
```

`to_aami_class` **discards nothing**. One symbol in, one class out.
The filtering of non-beats is already done in `load_record`.

### `AAMI_MAP` is a table, not an algorithm

```python
AAMI_MAP = {"N":"N", "L":"N", "R":"N", "e":"N", "j":"N",
            "A":"S", "a":"S", "J":"S", "S":"S",
            "V":"V", "E":"V", "F":"F",
            "/":"Q", "f":"Q", "Q":"Q"}
```

The rule lives as **data in `config.py`**, not as a chain of `if`s in
`src/`. Changing "L → S" takes a single config line, `src/` is untouched.

**L & R (bundle branch block) → N** is a decision that feels wrong
clinically (LBBB is clearly pathological) but is right methodologically: the AAMI
EC57 standard and de Chazal 2004 put them in N, and the entire inter-patient literature
uses that convention. If we deviate, our numbers cannot be compared
with anyone's.

### Why `AAMI_MAP[symbol]`, not `.get(symbol, "Q")`

`.get` with a default would **silently** label an unknown symbol as Q →
Arrhythmia. The bracket raises `KeyError`. If the upstream whitelist leaks, you know
right then, not in Phase 6 when recall is suddenly strange and there is no
clue why.

### `int(... in ...)`

```python
"V" in {"V","S","F","Q"}   →  True   →  int(True) = 1
"N" in {"V","S","F","Q"}   →  False  →  int(False) = 0
```

`bool` is a subclass of `int` in Python, so the cast is a no-op in value. Its purpose is to
make `np.array(labels, dtype=np.int8)` in `prep_beats` not produce
`dtype=bool`, which would trouble the Phase 5 class weight.

**An asymmetry to be aware of:** membership is checked in `ARRHYTHMIA_SYMBOLS`,
so an unknown class silently falls to 0 (Normal). Safe *only because*
`to_aami_class` already raises `KeyError` upstream: these two functions are always
called as a pair.

---

## 2. `compute_rr_features()`: three rhythm numbers per beat

### 2.1 Why RR, why three

The RR interval = the time distance between beats. From it, three features:

| Feature | Formula | Captures |
|---|---|---|
| `RR_prev` | $(r_i - r_{i-1}) / f_s$ | the absolute speed of this beat |
| `RR_ratio` | $\text{RR}_{\text{prev}} / \overline{\text{RR}}_{\text{lokal}}$ | premature/late **relative to that person's rhythm** |
| `dRR` | $\text{RR}_{\text{prev},i} - \text{RR}_{\text{prev},i-1}$ | change: the fast-then-pause pattern typical of PVC |

`RR_prev` alone is not enough: 0.6 seconds is normal for a person with HR 100,
but premature for a person with HR 60. `RR_ratio` normalizes to that
patient's own rhythm, and **this is the feature that survives crossing the inter-patient
split**, because it carries no baseline heart-rate bias of the training patients.

### 2.2 The code walk, line by line

```python
r = np.asarray(r_locations, dtype=np.float64)
m = len(r)
out = np.full((m, 3), np.nan, dtype=np.float64)
if m < 2:
    return out.astype(np.float32)
```

The NaN canvas first. Rows that do not get filled **stay NaN**: that is the contract,
not an oversight (§2.5). A record with < 2 beats returns immediately; without this guard
`np.diff` produces an empty array and the division below blows up.

```python
d = np.diff(r) / fs                      # [1.0, 2.0, 1.0]  detik
```

$M$ beats → $M-1$ intervals. The index shift that must be held tightly:

$$d[i-1] \ \text{adalah}\ \text{RR}_{\text{prev}}\ \text{milik beat}\ i$$

Beat 0 has no predecessor: that is why `d` is one shorter than `r`.

```python
w = RR_LOCAL_WINDOW_BEATS                # 10
j = np.arange(m - 1)
start = np.maximum(0, j - w + 1)
csum = np.concatenate(([0.0], np.cumsum(d)))
local_avg = (csum[j + 1] - csum[start]) / (j + 1 - start)
```

A **causal** average over at most the last 10 intervals, including this
interval itself:

$$\overline{\text{RR}}_{\text{lokal}}[j] = \frac{1}{j - s + 1}\sum_{k=s}^{j} d[k],
\qquad s = \max(0,\ j - 9)$$

`np.cumsum` makes a **prefix sum**, so the sum of a window of any width
finishes in two operations: `csum[j+1] - csum[start]`. The zero in front (`[0.0]`)
makes `csum[0] = 0` so the formula also holds for `start = 0`.

```python
out[1:, 0] = d                           # RR_prev  → baris 1..M-1
out[1:, 1] = d / local_avg               # RR_ratio → baris 1..M-1
out[2:, 2] = np.diff(d)                  # dRR      → baris 2..M-1
return out.astype(np.float32)
```

`out[1:]` and `out[2:]` are a direct translation of the index shift
above: RR_prev starts to exist at beat 1, dRR only at beat 2 (it needs two RRs).

### 2.3 Numerical example

```python
r = [0, 360, 1080, 1440]        # fs = 360
d = [1.0, 2.0, 1.0]             # detik
local_avg = [1.000, 1.500, 1.333]
```

| beat | RR_prev | RR_ratio | dRR | interpretation |
|---|---|---|---|---|
| 0 | NaN | NaN | NaN | no predecessor |
| 1 | 1.00 | 1.00 | NaN | no comparison RR yet |
| 2 | 2.00 | 1.33 | +1.00 | **pause**: 33% slower than the local rhythm |
| 3 | 1.00 | 0.75 | −1.00 | **premature**: 25% faster |

Beats 2 & 3 are a pair: that is the signature of an extrasystole: one beat comes early,
then a compensatory pause.

### 2.4 Decision: a CAUSAL window, shrinking at the edge

The PRD marks this as a DECISION POINT. There are two choices:

| | symmetric (5 left + 5 right) | **causal (10 left)** ← chosen |
|---|---|---|
| Needs future beats | yes | no |
| Can run on the ESP32 | must delay 5 beats (~4 seconds) | immediately |
| Consistent with Phase 1 | no (causal `sosfilt`) | yes |
| Rhythm estimate | slightly smoother | sufficient |

The deciding reason is the same as PRD TRAP #1 (JEBAKAN #1): anything that needs the future
is impossible on a device that receives samples one by one, and train/deploy mismatch
is more expensive than a slightly coarser average.

At the start of a record the window **shrinks**, it is not padded: the 3rd beat uses the average of the 3
intervals that really exist. Zero padding would create a false interval of 0
seconds that drags `local_avg` down and makes `RR_ratio` blow up.

In the firmware, `ecg_rr_features` (`firmware/src/ecg_pipeline.cpp`) re-sums
at most 10 intervals from the R index history for each beat: O(10) per
beat, with no additional state beyond the R history that is already stored.

### 2.5 Decision: NaN, not 0

Beats 0 and 1 of each record do not have all the features. They are given NaN, **not** 0.

`dRR = 0` is a **valid and frequent** value: it means "stable rhythm", precisely the hallmark
of a Normal beat. If 0 is also used as the marker for "unknown", the model
learns from two different things that look identical. NaN has no valid
interpretation, so it is safe as a sentinel.

A bonus: NaN is a **free alignment bug detector**. If `loss = nan` appears in
Phase 5, it is direct proof that `valid_beat_indices` did not drop beats 0 & 1,
not a mystery that has to be hunted.

The cost: 2 beats per record × 44 records = **88 beats out of ~100,000**.

### 2.6 What is deliberately NOT done

**No mean/std normalization.** PRD TRAP #2 (JEBAKAN #2): computing $\mu,\sigma$ from the
DS1+DS2 combination is data leakage: test set statistics seep into training.
The RR scale is already $O(1)$ as is (0.5–1.2 seconds), so there is nothing that needs
scaling. Compare with `zscore_per_window` in Phase 1: that is allowed because its
statistics come from **inside the window itself**, needing nothing from the dataset.

**No filtering of anything.** The function returns `[M, 3]` the full length of
`r_locations`. The reason is in §3.

### 2.7 Optional features (inactive in the locked configuration)

`src/features_rr.py` also contains `compute_rr_ratio_features` (the 4-column
ratio form, needing the RR of the next beat), `qrs_width_features` (QRSw2 & QRSw4), and
`hos_features` (kurtosis & skewness). All three are assembled by `assemble_rhythm_features`
only if the knobs `PA_RR_RATIO`, `PA_QRSW`, or `PA_HOS` are turned on, and are used
for ablation. The locked configuration uses the three columns above only: on mitdb,
the extra features do not give an F1 difference that exceeds the run-to-run variation.

`assemble_rhythm_features` is the only place that builds `X_rr` for three
callers (`prep_beats`, `ablasi`, `sweep_jitter`), plus `export_golden`
so that the golden tests the features that are actually used. If the knob logic
is duplicated, the three would silently diverge and the ablation would compare different
things.

- **HOS** (`PA_HOS=1`, Dias 2021 Eq. 12-13, `[K,2]`). The incoming window is already
  z-scored (mean 0, std 1), so the second denominator of the formulas is just 1 and what
  remains are the raw 4th and 3rd moments; this feature is nearly free on the MCU. Kurtosis
  is reported raw (not excess) following Eq. 12, and the moments use the divisor
  N, not N−1: the window length is fixed, so the difference is constant (~0.4%) and
  absorbed by the first layer's weights. It attaches to the rhythm branch because it is two
  scalars, not a time series.
- **QRS width** (`PA_QRSW=1`, `[K,2]`). P3 (Algorithms 13:75) gives QRSw2 and
  QRSw4 ranks 1-2 of 85 features by mutual information: one scalar that
  separates V (wide QRS > 120 ms) from S (narrow, arriving early) and N.
  The width is measured by walking left and right from the peak at `R_IN_WINDOW` (132)
  until the amplitude drops below `frac` × peak; if it never drops, the window edge
  is used. The peak search tolerates ±4 samples (`ECG_QRSW_SEARCH`)
  because the mitdb residual is ±2. Normalization is to the causal mean of the last
  `RR_LOCAL_WINDOW_BEATS` (10) beats, not 32 as in P3, so that one window constant applies
  to all features and is consistent with the decision point "causal, shrinking at the
  edge"; 32 remains as a further ablation (K5). Zero additional buffer on the MCU.
- **RR ratios** (`PA_RR_RATIO=1`, `[m,4]`: RR0/avgRR, RR+1/RR0, RR-1/RR0, tRR0;
  P3 ranks #3, #4, #10). Absolute values (seconds) differ between people, so the
  model can learn patient identity; the window is already normalized but the default
  RR features are still absolute seconds. `RR+1` needs the next beat, so the last column is
  NaN and `valid_beat_indices` drops the last beat of each record. In the firmware
  this means delaying 1 beat (gate G2); `export_golden` marks the last beat
  as untested through `GOLDEN_RR_LAST`.

---

## 3. Alignment: the most expensive trap in this phase

The contract: **row index == beat index**, forever. The caller writes

```python
rr = compute_rr_features(r)[idx]        # BENAR
rr = compute_rr_features(r[idx])        # SALAH
```

The difference is subtle but fatal. `r[idx]` cuts the R-peak list first, so the first
beat that passes loses its real neighbor and its `RR_prev` is computed from the
wrong beat, silently, with no error.

### Why the filtering is not here

The three beat-drop conditions come from three different places:

1. the window fits in the signal → belongs to `segment_beats` (Phase 1)
2. has `RR_prev` → belongs to `compute_rr_features` (Phase 2)
3. has `dRR` → belongs to `compute_rr_features` (Phase 2)

If each function drops on its own, the result is **three different sets
whose lengths can coincidentally be the same**. `assert len(windows) == len(labels)`
will PASS, the loss goes down smoothly, and it is only discovered in Phase 6 when recall is ~0.

A simulation of record 100: 100% of rows shifted by 1 beat, 68 labels get the wrong symbol
even though there are only 34 real arrhythmias: each 1 arrhythmia damages 2 rows.

That is why all beat-drop policy is gathered in a single function,
`valid_beat_indices` in `scripts/prep_beats.py`, and `src/` stays pure:

```python
r = np.asarray(r_locations)
i = np.arange(len(r))
fits = (r - WIN_PRE >= 0) & (r + WIN_POST <= signal_len)
return i[fits & (i >= 2)]
```

An intersection (`&`), not a union. `i >= 2` covers the RR_prev and dRR conditions at once:
beat 2 definitely has both.

---

## 4. Record 100 numbers (quick reference)

```
beat            = 2273        baris NaN = 2  (beat 0 & 1)
simbol          = N:2239  A:33  V:1
label biner     = Normal 2239 (98,5%)   Aritmia 34 (1,5%)

           mean      std      min      max
RR_prev   0.7946   0.0488   0.5222   1.1306    detik
RR_ratio  0.9996   0.0502   0.6729   1.3967    tanpa satuan
dRR      -0.0000   0.0632  -0.3444   0.5944    detik
```

Two important readings:

**The features do separate.** Median `RR_ratio`: Normal **1.0003** vs Arrhythmia
**0.7664**. The arrhythmia beats of record 100 are almost all `A` (atrial premature):
arriving ~23% faster than the local rhythm, exactly what is expected.

**`dRR` mean $\approx$ 0 is correct, not a bug.** Forward differences summed
over a record always approach zero (telescoping): a heart cannot keep
slowing down forever. What is informative is the deviation, not the mean.

**The imbalance is extreme (1.5%)**, and that is normal for MIT-BIH. This is precisely the
reason Phase 5 uses class weighting. If the distribution looks balanced,
the label mapping is wrong.

### The whole dataset (`make prep`)

Clean data, no augmentation (`python scripts/prep_beats.py --jitter none --db mitdb`):

```
44 record   100.624 beat   Normal 90.023 (89,5%)   Aritmia 10.601 (10,5%)
dibuang     109 beat = 88 (beat 0 & 1 tiap record) + 21 (window tak muat di tepi)
```

The `make prep` default adds two jittered copies for the DS1 records
(augmentation, see [`jitter-walkthrough.md`](jitter-walkthrough.md)) so that the
total is 202,560 beats; DS2 stays one clean copy.

The global ratio of 10.5% is far friendlier than record 100 (1.5%): record 100
happens to be a calm patient. The distribution itself is wild: **212 → 0% arrhythmia**
(contributes not a single positive example), **232 → 77.7%** (the majority is
arrhythmia). This is why the split must be per patient: if 232 goes into train and
212 into test, your numbers speak about two different diseases.

---

## 5. Comprehension check

1. `RR_LOCAL_WINDOW_BEATS` is changed 10 → 3. What happens to the `RR_ratio` of a PVC
   beat that appears right after another premature beat? (Hint: a short window
   gets contaminated by abnormal beats too.)
2. Why may `compute_rr_features` be called with a whole `r` that contains
   beats that will later be dropped, but `segment_beats` may not?
3. If NaN is replaced with 0 and `valid_beat_indices` forgets to drop beats 0 & 1, what symptom
   appears in Phase 5, and why is that more dangerous than `loss = nan`?
4. Record 232 has many consecutive `A` beats. What happens to its
   `local_avg`, and can `RR_ratio` still be trusted there?

## 6. Supporting scripts

| Command | What it shows |
|---|---|
| `make test` | All tests; `tests/test_features_rr.py` locks the behavior of `features_rr` |
| `make prep` | Phase 2 end-to-end → 44 × `per_record/*.npz` + a distribution table |

---

**[← Phase 1: preprocessing](preprocessing-walkthrough.md)**  ·  [Walkthrough map](README.md)  ·  **[Phase 2b: prep_beats →](prep-beats-walkthrough.md)**
