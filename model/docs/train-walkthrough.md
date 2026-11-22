# Walkthrough `src/train.py`: Phase 5

> **Scope:** training the hybrid model on DS1: class weight, the monitored metrics, EarlyStopping, and the training schedule under the locked configuration.
> **Related code:** `src/train.py`, `scripts/train_model.py`, `scripts/ablasi.py`, `src/dataset.py` (`split_train_val`), `config.py` (`EPOCHS`, `BATCH_SIZE`, `EARLY_STOP_*`, `VAL_RECORDS`, `SEED`, `THRESHOLD`), `tests/test_train.py`
> **Prerequisite:** [`model-walkthrough.md`](model-walkthrough.md)

A study document, not a specification. The official specification remains
`PRD_Model_Aritmia_TinyML.pdf` pp. 13–14. Continues from
[`model-walkthrough.md`](model-walkthrough.md) (Phase 4).

Reproduction:

```
cd model
make train          # → artifacts/model_fp32.keras + artifacts/metrics/fase5_training.png
```

---

## 0. The big picture

```
train.npz (DS1, 152.904 beat = 50.968 × 3 salinan)
        │
        │  split_train_val()   ← per pasien: 5 record VAL_RECORDS disisihkan
        ▼
 train 121.857 beat           val 31.047 beat
 (12.315 aritmia, 10,11%)     (3.138 aritmia, 10,11%)
        │                            │
        │  class_weight              │  EarlyStopping(val_auc)
        ▼                            ▼
   model.fit(...)  ──────────►  artifacts/model_fp32.keras
                                artifacts/metrics/fase5_training.png
```

**DS2 is not touched at all in this phase.** Every number you see (loss,
recall, AUC, threshold) comes from DS1. Train and val both contain the
jittered copies (one clean + two jittered per beat), because both are
cut from the same `train.npz`.

---

## 1. The problem: 90% Normal

If the model guesses "Normal" for all 121,857 beats, its accuracy is **89.9%**.
It sounds good and is worth nothing: arrhythmia recall = 0. For early detection, the only
truly dangerous error is the **arrhythmia that slips through** (false
negative), and that is exactly what the model is lazy about learning if left alone.

Without any handling, the gradient from 109,542 Normal beats drowns out the gradient from
12,315 Arrhythmia beats. The model finds a shortcut, and that shortcut looks
successful on the wrong metric.

---

## 2. `make_class_weights()`: equalizing the votes, not copying data

```python
counts = np.bincount(y, minlength=2)
if (counts == 0).any():
    raise ValueError(...)
return {c: len(y) / (2.0 * counts[c]) for c in (0, 1)}
```

The standard *balanced* formula:

$$w_c = \frac{N}{K \cdot n_c}, \qquad K = 2\ \text{classes}$$

For DS1-train:

$$w_0 = \frac{121857}{2 \cdot 109542} = 0.556, \qquad
w_1 = \frac{121857}{2 \cdot 12315} = 4.948$$

What matters is not the numbers but their **product**:

$$n_0 w_0 = 109542 \times 0.556 \approx 60929 \approx 12315 \times 4.948 = n_1 w_1$$

Both classes contribute the same total loss. One misclassified Arrhythmia beat
"shouts" 8.9× louder than one misclassified Normal beat. This is
asserted in `tests/test_train.py::test_two_class_contributions_equal`.

### Why not oversampling

Oversampling duplicates minority beats until balanced. The effect on the loss is similar,
but the duplicates are **beats from the same patients**, so the model gets more
chances to memorize individuals, against the whole spirit of
inter-patient evaluation. Plus the epoch grows ~1.8×. The PRD is firm: pick one, not
both (it can over-correct).

### Why not use `sklearn.utils.class_weight`

The PRD gives `compute_class_weight("balanced", ...)` as an example. Its formula is exactly the two
lines above, and `scikit-learn` is not in `requirements.txt`. The `CLAUDE.md` gate
point rule: do not add a dependency for something a few lines
already solve, especially a package as large as sklearn used for only one function.

---

## 3. Metrics: why `accuracy` is not in the list

```python
metrics=[Recall(name="recall"), Precision(name="precision"), AUC(name="auc")]
```

| Metric | Answers the question | Why it is here |
|---|---|---|
| **Recall** | Of all real arrhythmias, what % are caught? | The most dangerous failure = an arrhythmia slipping through |
| **Precision** | Of all alarms, what % are correct? | False alarms make the device get ignored (*alarm fatigue*) |
| **AUC** | How well does the model **rank** arrhythmia above normal? | Threshold-free, see §4 |

Accuracy is deliberately not monitored. On 90:10 data it can be 89.9% without the model
learning anything; showing it only invites misreading.

---

## 4. EarlyStopping, and why monitor AUC rather than recall

```python
callbacks.EarlyStopping(monitor="val_auc", mode="max",
                        patience=8, restore_best_weights=True)
```

Three candidates were considered:

| Monitor | The problem |
|---|---|
| `val_recall` | Can be "cheated": guess Arrhythmia for everything → recall 1.0, precision destroyed. A metric that can be maximized by a broken model is not a safe guide. |
| `val_loss` | The loss here is already **distorted by `class_weight`**: its value is no longer a likelihood that can be interpreted directly, and it does not move in step with ranking quality. |
| **`val_auc`** (used) | Measures the quality of the probability **ranking**, does not depend on the threshold, and cannot be faked by guessing one class. |

`restore_best_weights=True` matters: after `patience=8` epochs without improvement,
the weights are restored to the best epoch, not the weights of the last epoch, which have already
overfit. `EPOCHS = 60` in `config.py` is only an upper bound; what really
decides when to stop is this callback.

Under the locked configuration, the "best epoch" is **epoch 0**, so
`patience=8` trains 8 epochs that are all thrown away. See §6b.

---

## 5. Training results

The production model (`artifacts/model_fp32.keras`), locked configuration:

```
train 121857 beat (12315 aritmia)  val 31047 beat (3138 aritmia)
class_weight  Normal 0.556  Aritmia 4.948

VAL @ threshold 0.8   TP=2052  FN=1086  FP=743  TN=27166
  recall(sensitivity) 0.6539   precision 0.7342   specificity 0.9734
```

The curve: `artifacts/metrics/fase5_training.png`.

### Reading the numbers honestly

`make train` prints VAL at the locked `THRESHOLD` (0.80), not 0.5. At 0.5
the same model gives recall 0.8445 but precision of only 0.3193 (5,650 false
alarms out of 27,909 normal beats). The threshold 0.80 was chosen on VAL with a maximum-F1
criterion and moves the operating point to recall 0.65 / precision 0.73. That is a
legitimate trade-off because it was calibrated **on val, not DS2**; the procedure belongs to
Phase 6 (`scripts/calibrate_threshold.py`).

**Recall 0.65**: of the 3,138 arrhythmia beats in val, 2,052 were caught and **1,086
slipped through**. For honest inter-patient evaluation this is plausible (the intra-patient
literature reporting 99% plays by different rules), but clearly not yet clinically viable.

**Specificity 0.973**: of 27,909 normal beats, 743 triggered false alarms.

### What the curve shows: real overfitting

Measurement condition of this section and §6: window 90/160 (250 samples), no jitter
augmentation, Adam 1e-3, threshold 0.5. In that configuration val contains 10,348 beats
(1,046 arrhythmias) and the best model gives VAL @0.5: TP=728 FN=318 FP=67 TN=9235
(recall 0.6960, precision 0.9157, specificity 0.9928). The lesson about
overfitting and `restore_best_weights` applies equally to the locked configuration,
which even peaks earlier (§6b).

| | epoch 4 (best) | epoch 12 (stopped) |
|---|---|---|
| train recall | 0.924 | 0.960 |
| **val** recall | 0.696 | 0.772 |
| **val** precision | 0.916 | 0.693 |
| **val AUC** | **0.9432** | 0.9271 |

Train keeps improving while val AUC declines from epoch 4, the definition of
overfitting. `restore_best_weights` is what saves it; without it the saved model
is the epoch 12 version with precision plunging to 0.69.

---

## 6. Dropout: a decision tested with numbers

`DROPOUT_RATE = 0.0` started from the data : parameter ratio
([`model-walkthrough.md`](model-walkthrough.md) §4). Because the curve shows
overfitting, that value was tested, not kept just because it was already written. Four
values, same seed, measurement condition as §5:

| dropout | val AUC | val recall | val precision |
|---|---|---|---|
| **0.0** (used) | 0.9576 | **0.6998** | 0.9470 |
| 0.2 | 0.9616 | 0.2744 | 0.9863 |
| 0.3 | 0.9290 | 0.3585 | 0.9446 |
| 0.5 | 0.9615 | 0.6511 | 0.9813 |

Conclusion: **dropout does not help here, it actually damages recall.** What
happens is that dropout makes the model more conservative (precision up, recall
down), while our problem is precisely insufficient recall. AUC barely
changes, meaning the ability to *rank* is the same; only where the
probabilities pile up relative to 0.5 shifts.

The lesson: overfitting visible in the curve **does not automatically mean
"add regularization"**. Here the root problem is not that the model is too large
(6,417 params), but variation between patients, and dropout cannot cure that.

---

## 6b. Training schedule under the locked configuration

In the window 90/160 configuration without augmentation (§5), training stopped at
epoch 12 with best epoch 4. Under the locked configuration (window 128/128 +
jitter augmentation ×3), the shape of the curve is entirely different.

### The production model is the result of ONE epoch

```
lr 1e-3 (terkunci), seed 7      lr 1e-4, seed 7
epoch 0  val_auc 0,9492  <-     epoch 0   0,8797   masih naik
epoch 1          0,9345         epoch 2   0,9067
epoch 2          0,9279         epoch 2-19  dataran ~0,905-0,911
...      turun monoton          epoch 18  0,9113  <- puncak
epoch 8          0,8635  stop   epoch 26  0,9082  stop
9 epoch, 8 terbuang             27 epoch, membaik selama 19
```

`patience=8` makes training always run 9 epochs, then
`restore_best_weights` restores epoch 0. The remaining eight epochs are pure
overfitting.

**It is that fast because** "epoch" is misleading as a unit. The already augmented
DS1 has 121,857 beats; with `BATCH_SIZE = 64` that is **1,905
gradient steps per epoch**. For a 6,417-parameter model with Adam 1e-3,
one epoch is more than enough to memorize. What looks like
"stopped at epoch 9" is really "stopped after 17,145 steps".

General lesson: **never judge training length by the number of epochs** without
multiplying it by the steps per epoch. The ×3 augmentation in Phase 6c multiplies
the steps per epoch, so every time the training data size changes, the `val_auc` curve
needs to be printed again to see where the peak is.

### Alternative not used: weight averaging (`--swa N`)

Hypothesis: if what picks the final weights is a noisy `val_auc` lottery,
just average the top few epochs instead of picking up the argmax.
`BestWeightAverage` is attached **after** `EarlyStopping` so that it overwrites the result of
`restore_best_weights`.

Safe without recomputing anything: this model has **no BatchNorm**
(Conv1D → MaxPool → GAP → Dense), so the standard SWA pitfall (BN statistics must be
recomputed after the weights are averaged) does not apply.

Result over 3 seeds: DS2 F1 0.6911 → 0.6346 (**−0.057, above the signal threshold**).
The diagnosis prints the averaged epochs: `[0, 1, 2]`.

**Why it failed:** there is no "near tie" to average. The peak is at the edge of the
curve and the rest declines monotonically, so averaging anything means pulling in
worse weights. Weight averaging needs a **plateau**, and at
1e-3 there is no plateau. The `--swa` knob is left behind: at 1e-4 that plateau exists, so
the hypothesis deserves a retest there.

### Learning rate 1e-4 (`--lr`)

| Test set | patients | F1 1e-3 | F1 1e-4 | AUC |
|---|---|---|---|---|
| DS2 | 22 | 0.6535 ±0.0280 | 0.6729 ±0.0483 | 0.9305 → 0.9415 |
| TEST-B (svdb) | 20 | 0.5237 ±0.0084 | 0.5306 ±0.0339 | 0.8667 → 0.8860 |
| TEST-C (incartdb) | 19 | 0.6784 ±0.1080 | **0.8025 ±0.0277** | 0.9352 → 0.9525 |

AUC rises on 4 of 4 sets. But there is a sharp trade-off: **V recall rises in 3 of
3 seeds, S recall falls in 2 of 3**, even though the 1e-4 threshold is looser
(0.53 vs 0.65), which should have raised recall. So this is not an operating-point
artifact: the model really does rank S beats worse.

It means 1e-4 improves the class that is already strong (V) and worsens the weak one
(S), the opposite direction from this project's needs. Per-class recall on
DS2 (mean of 3 seeds), including the middle LR 3e-4:

| LR | recall **S** | recall **V** | recall **F** | DS2 AUC | TEST-C F1 |
|---|---|---|---|---|---|
| **1e-3** (used) | **0.4473** | 0.9151 | 0.1804 | 0.9305 | 0.6784 ±0.1080 |
| 3e-4 | 0.2024 | 0.9663 | 0.3265 | 0.9348 | **0.8481 ±0.0098** |
| 1e-4 | 0.3126 | **0.9736** | **0.3591** | **0.9415** | 0.8025 ±0.0277 |

3e-4 is actually the worst on S, so there is no middle point that satisfies
both: lowering LR lowers S and raises the others. The S deficit
is proven real at equivalent operating points (6 of 6 points,
`scripts/check_operating_point.py`), not a threshold artifact. **LR stays 1e-3.**

Per-class recall at equalized total recall (seed 42):

| total recall | 1e-3 | 3e-4 | 1e-4 |
|---|---|---|---|
| 0.65 | **S 0.436** / V 0.848 | S 0.216 / **V 0.945** | S 0.234 / V 0.943 |
| 0.70 | **S 0.517** / V 0.885 | S 0.295 / **V 0.974** | S 0.320 / V 0.967 |
| 0.80 | **S 0.716** / V 0.933 | S 0.552 / **V 0.985** | S 0.576 / V 0.983 |

Two mechanistic explanations were measured and do not match the data, so the
cause of the S↔V trade-off is not yet known:

| Hypothesis | Test | Result |
|---|---|---|
| The S advantage of 1e-3 = an effect of an undertrained model that "hesitates" | per-class recall at equalized total recall (table above) | does not match: the S advantage persists at 6 of 6 points |
| Longer training = more dependence on morphology, the rhythm branch drowns | contribution of each branch to the merging Dense (`Σ|bobot| × std aktivasi masuk`) | does not match: the rhythm share is 7.3% (1e-3), 7.0% (3e-4), 11.8% (1e-4), actually rising |

`val_auc` cannot be used to choose between LRs: its peak at 1e-3 (0.9492) is
higher than at 1e-4 (0.9113) for the same seed, even though 1e-4 is better
on DS2 in 2 of 3 seeds. VAL (5 patients) picks the epoch within one run;
choosing between regimes needs a larger set, namely TEST-B/TEST-C.

**If the LR is ever moved**, these must follow: a new LR constant in
`config.py` passed on to `compile_model(lr=...)` (currently `config.py`
has no LR constant; `lr=0` means the default `"adam"` 1e-3), the Learning rate row in the decision point table `../CLAUDE.md`, the full
chain rerun (prep → split → train → calibration → eval → quantize →
`export_golden.py` → `make export`), `golden_ref.h` and `model_int8.h` regenerated
together, `pio test`, and the "Key numbers" block in [`README.md`](README.md).

### Methodological side effect: the 0.04 threshold applies to the mean of 3 seeds

Identical configuration, identical seeds, run twice on the same day:

```
batch 1   F1 DS2 0,6911 ±0,0290
batch 2   F1 DS2 0,6535 ±0,0280
selisih   0,0376
```

**Even the mean of 3 seeds wobbles ~0.04 between batches.** The consequence: a difference
below 0.04 does not become a signal just because it was repeated over 3 seeds. What really
raises discriminating power is a **larger test set**, which is the purpose of
TEST-B/TEST-C (39 held-out patients, `ablasi.py --cross-db`).

---

## 7. What is deliberately NOT done

**Does not touch DS2.** Including just to "peek". Once looked at to
make a decision, DS2 is no longer pure and the whole Phase 6 claim falls.

**Does not calibrate the threshold here.** The Keras metrics during training use the default
0.5. Threshold calibration uses the val curve and is a Phase 6 matter
with a recorded procedure (`scripts/calibrate_threshold.py` → 0.80);
`make train` only reads `THRESHOLD` for the VAL summary.

**Does not lower the learning rate.** Default `adam` (1e-3). The consequence is
known: `val_auc` peaks at **epoch 0**, so the production model is the result of
**one epoch** of training (§6b). A lower LR has been ablated (3 LRs × 3 seeds + 39
held-out patients) and **trades S recall for V and F recall**. Because S is the
focus of this research, that trade was rejected and reported as is. The
`ablasi.py --lr` knob is available for retesting.

**The seed is locked** (`np.random.seed(SEED)`, `tf.random.set_seed(SEED)`) before the
model is built. Without it, the results are not reproducible and the numbers in Bab 4 (Chapter 4 of the report) cannot
be repeated by the examiners.

---

## 8. Comprehension check

1. `class_weight` is removed. Predict what happens to accuracy, recall, and
   AUC, and why two of them can look like they *improved*.
2. `restore_best_weights=False`. Which model is saved, and what is its
   precision according to the §5 table?
3. The threshold is lowered from 0.5 → 0.3. In which direction do TP, FP, recall, and precision
   move? Why is this calibration forbidden on DS2?
4. Dropout 0.2 gives the **highest** val AUC (0.9616) but the worst recall
   (0.2744). How can both happen at once?

## 9. Supporting scripts

| Command | Looks at |
|---|---|
| `make train` | Train + save model & curve + val confusion matrix summary |
| `make test` | The whole test suite; `tests/test_train.py` locks the class weight formula and `BestWeightAverage` |

---

**[← Phase 4: model](model-walkthrough.md)**  ·  [Walkthrough map](README.md)  ·  **[Phase 6: evaluate →](evaluate-walkthrough.md)**
