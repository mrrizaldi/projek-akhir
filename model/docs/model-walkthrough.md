# Walkthrough `src/model.py`: Phase 4

> **Scope:** the hybrid two-input 1-D CNN architecture (morphology + rhythm) for binary Normal/Arrhythmia classification, together with its deploy variant.
> **Related code:** `src/model.py`, `config.py` (`CONV_FILTERS`, `CONV_KERNELS`, `POOL_SIZE`, `DENSE_UNITS`, `DROPOUT_RATE`, `WIN_LEN`, `N_RR_FEATURES`), `tests/test_model.py`
> **Prerequisite:** [`dataset-walkthrough.md`](dataset-walkthrough.md)

A study document, not a specification. The official specification remains
`PRD_Model_Aritmia_TinyML.pdf` pp. 12–13. Continues from
[`dataset-walkthrough.md`](dataset-walkthrough.md) (Phase 3).

Reproduction:

```
cd model
.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
from src.model import build_hybrid_model
build_hybrid_model().summary()
"
```

---

## 0. The big picture: two branches, one decision

```
 X_morph [N,256,1]                          X_rr [N,3]
        │                                        │
   Conv1D(16,7) → MaxPool                        │
   Conv1D(32,5) → MaxPool                        │   RR_prev
   Conv1D(32,3) → MaxPool                        │   RR_ratio
   GlobalAveragePooling1D                        │   dRR
        │                                        │
     [N,32]  ──────── Concatenate ──────────  [N,3]
                          │
                      [N,35]
                   Dense(16, ReLU)
                          │
                Dense(1, sigmoid) → p(Arrhythmia)
```

There are two branches because arrhythmia has **two signatures that do not replace
each other**:

| Branch | Captures | Example that only it can see |
|---|---|---|
| Morphology (CNN) | the **shape** of the beat | PVC: widened QRS, missing P wave |
| Rhythm (RR) | the **timing** of arrival | APC: nearly normal shape, but it arrives too early |

The atrial premature beat (`A`), 33 of the 34 arrhythmias in record 100, has a morphology
similar to a normal beat. The CNN alone would miss it. All that distinguishes it is
`RR_ratio` 0.77 vs 1.00. Conversely, a PVC can arrive on time but its shape is
clearly different. Both are needed.

Cost of the RR branch: `Dense(16)` receives 35 inputs, not 32, giving **48 extra
parameters**. Very cheap for information that cannot be obtained from anywhere else.

---

## 1. Why the Functional API, not Sequential

```python
return Model(inputs=[morph_in, rr_in], outputs=out, name="hybrid_ecg")
```

`Sequential` is a straight stack: one input, one path, one output. This model
has **two inputs that meet in the middle**, so Sequential structurally
cannot do it. The Functional API treats layers as functions
(`x = layers.Conv1D(...)(x)`), so branching and merging come down to
who calls whom.

---

## 2. Morphology branch: three tapering blocks

```python
for filters, kernel in zip(CONV_FILTERS, CONV_KERNELS):   # (16,32,32), (7,5,3)
    x = layers.Conv1D(filters, kernel, activation="relu", padding="same")(x)
    x = layers.MaxPooling1D(POOL_SIZE)(x)
```

The journey of the shape:

| Stage | Output | Params | Coverage of 1 neuron (receptive field) |
|---|---|---|---|
| Input | (256, 1) | - | 1 sample = 2.8 ms |
| Conv1D(16, 7) | (256, 16) | 128 | 7 samples ≈ 19 ms |
| MaxPool 2 | (128, 16) | 0 | 39 ms |
| Conv1D(32, 5) | (128, 32) | 2,592 | ~19 original samples ≈ 53 ms |
| MaxPool 2 | (64, 32) | 0 | 106 ms |
| Conv1D(32, 3) | (64, 32) | 3,104 | ~35 original samples ≈ 97 ms |
| MaxPool 2 | (32, 32) | 0 | ~194 ms |
| GAP | (32,) | 0 | the whole window |

**The kernel tapers 7 → 5 → 3** following this logic: at the start, one sample is only
2.8 ms, so a wide kernel is needed to see a meaningful pattern. After two
poolings, one step already represents 11 ms, so a kernel of 3 already
covers ~97 ms, roughly the width of a QRS complex. The filters see local detail
first (slopes, peaks), then the arrangement of that detail (the whole QRS shape).

**Filters grow 16 → 32 → 32** because the lost time resolution is traded
for pattern diversity. The third block does not go up to 64: that would add ~6,000
params by itself and break the budget.

`padding="same"` keeps the length constant before pooling, so the shape arithmetic
is predictable: 256 → 128 → 64 → 32, divisible by 2 at every stage
with no rounding. These numbers also determine the size of the intermediate tensors in the TFLM
tensor arena on the firmware.

---

## 3. `GlobalAveragePooling1D`: the decision that saves the budget

After the last block, the tensor has shape `(32, 32)` = 1,024 numbers. Two ways
to compress it into a vector:

| | `Flatten` | **`GlobalAveragePooling1D`** |
|---|---|---|
| Output | 1,024-dim | 32-dim |
| Params of the next `Dense(16)` | (1,024+3)×16 + 16 = **16,448** | 35×16 + 16 = **576** |
| Model total | ~22,300 | **6,417** |
| INT8 in flash | weights alone ~22 KB | **22.94 KB** whole model, under the 25 KB limit |
| Character | memorizes *where* a pattern appears | shift-tolerant: *whether* a pattern appears |

GAP averages each feature map into one number: "how strongly this filter
fires across the window". For ECG that is a good fit, since the R-peak is already always
at index ~132 thanks to the Phase 1 segmentation, so the model does not need to memorize position.

This is the single biggest reason the model fits on the ESP32. If
`count_params()` jumps into the tens of thousands, the first suspect: `Flatten`
sneaked in.

---

## 4. Merging and the classification head

```python
merged = layers.Concatenate()([x, rr_in])          # 32 + 3 = 35
merged = layers.Dense(DENSE_UNITS, activation="relu")(merged)   # 576 param
out = layers.Dense(1, activation="sigmoid", name="arrhythmia")(merged)   # 17 param
```

`Dense(16)` is where the two sources of information really interact: here
the model can learn rules like "wide QRS **and** low RR_ratio →
very likely PVC". Before this layer, the two branches do not know about each other.

`sigmoid` squashes the raw score to $(0,1)$:

$$\sigma(z) = \frac{1}{1 + e^{-z}}$$

Paired with `binary_crossentropy` (Phase 5). The probability cutoff
is not set in the model: the threshold is **calibrated on VAL (part of DS1), not
DS2**, and its locked value is `THRESHOLD = 0,80` (see
[`evaluate-walkthrough.md`](evaluate-walkthrough.md)). Shifting the threshold
is a legitimate way to trade sensitivity for precision.

### Decision: no dropout

`DROPOUT_RATE = 0.0` in `config.py`. The reason is the data ratio:

$$\frac{40{,}619\ \text{unique training beats}}{6{,}417\ \text{parameters}} \approx 6$$

(121,857 training rows if the jitter copies are counted, ≈ 19 per parameter.) A model
this small with this much data is more likely to **underfit** than
overfit. A dropout of 0.3 on a 16-unit layer means switching off ~5 neurons every step,
which is aggressive for the only place where morphology and rhythm meet, and risks
hurting the minority class, which is only 10%.

The code still provides the path:

```python
if dropout_rate > 0:
    merged = layers.Dropout(dropout_rate)(merged)
```

So `build_hybrid_model(dropout_rate=0.3)` can be used right away
to test dropout. The test in Phase 5 shows that dropout of 0.2/0.3/0.5 lowers
val recall with almost the same AUC, so the value 0.0 is kept (see
[`train-walkthrough.md`](train-walkthrough.md) §6).

---

## 5. Verification

```
Total params: 6,417 (25.07 KB)
```

The breakdown: 128 + 2,592 + 3,104 + 576 + 17. Matches the PRD target of ~6,000.
The parameter count does not depend on window length because of GAP. The 25 KB is float32;
the INT8 result of Phase 7 (deploy variant) is 22.94 KB, under the `MAX_MODEL_KB = 25` limit.
The limit is 25 KB, not 20 KB as in the PRD DoD, because the deploy variant that is correct on
TFLM (without the `MEAN` op and without dynamic shapes, see
[quantize](quantize-walkthrough.md) §4b) already exceeds 20 KB; the ESP32-S3 flash is
16 MB, so this limit is a matter of discipline, not capacity.

Four tests lock the contract (`tests/test_model.py`):

| Test | Catches when... |
|---|---|
| `test_param_budget` | `Flatten` sneaks in, or Dense is oversized |
| `test_two_inputs_one_output` | input/output shapes deviate from the Phase 3 `.npz` |
| `test_predict_dummy_in_probability_range` | the output activation is not sigmoid |
| `test_rhythm_branch_really_used` | `Concatenate` is wired wrongly |

The last one is the most valuable and the easiest to forget: change **only**
`X_rr`, leave morphology at zero, and the output must change. If the RR branch
is disconnected, the model still trains smoothly, accuracy is still reasonable, and there is not
a single error, the kind of bug that stays invisible until APC recall
disappoints in Phase 6.

---

## 5b. There is a second variant that is not trained

`build_deploy_model()` in the same file produces a model with **identical
weights** but two ops swapped, because TFLite Micro computes `MEAN`
(GlobalAveragePooling) differently from regular TFLite. Not a new model, no retraining:
a translator between "the shape that is pleasant to train" and "the shape that a small
runtime executes correctly". See [`firmware-walkthrough`](firmware-walkthrough.md) §5.

## 6. Comprehension check

1. `padding="same"` is replaced with `"valid"`. What does the length of each stage become, and
   why does `count_params()` **not** change?
2. The last Conv block is raised from 32 → 64 filters. What is the total param count, and
   is it still < 25 KB after INT8?
3. GAP is replaced with `GlobalMaxPooling1D`. What changes in meaning for an ECG
   signal that has already been z-scored?
4. The RR branch is removed (morphology-only model). Which arrhythmia class is hurt most,
   and why might the global accuracy metric barely move?

## 7. Supporting scripts

| Command | Looks at |
|---|---|
| `make test` | The whole test suite; 4 tests in `tests/test_model.py` lock the Phase 4 architecture |
| `python -c "...build_hybrid_model().summary()"` | Layer table + `count_params()` |

---

**[← Phase 3: dataset](dataset-walkthrough.md)**  ·  [Walkthrough map](README.md)  ·  **[Phase 5: train →](train-walkthrough.md)**
