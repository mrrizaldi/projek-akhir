# Walkthrough `src/evaluate.py`: Phase 6

> **Scope:** threshold calibration on VAL then evaluation of the float32 model on DS2 (inter-patient), including the dissection of failures per class and per patient.
> **Related code:** `src/evaluate.py`, `scripts/calibrate_threshold.py`, `scripts/eval_fp32.py`, `config.py` (`THRESHOLD`)
> **Prerequisite:** [`train-walkthrough.md`](train-walkthrough.md) (Phase 5)

A study document, not a specification. The official specification remains
`PRD_Model_Aritmia_TinyML.pdf` p. 15.

Configuration measured in this document: window 128/128 (256 samples), DS1
augmented with empirical jitter (1 clean copy + 2 jittered copies), threshold
0.80. Measurement conditions: the `model_fp32.keras` and `fase6_*.csv` artifacts from the
full chain of 18 Sep 2026.

Reproduction:

```
cd model
python scripts/calibrate_threshold.py   # kalibrasi di VAL (DS1)
make eval                               # evaluasi di DS2
```

> **This is the most decisive phase in the entire PA.** The numbers here are the primary
> scientific claim. Everything done in phases 0–5 is preparation so that
> these numbers are honest.

---

## 0. An order that must not be reversed

```
Fase 5 selesai → model_fp32.keras beku
        │
        ▼
calibrate_threshold.py   ← pakai VAL (5 record DS1). Threshold ditetapkan DI SINI.
        │
        ▼  config.THRESHOLD = 0.80   (dikunci)
        │
        ▼
    make eval            ← DS2 dibuka. SEKALI. Dilapor apa adanya.
```

**The PRD trap (JEBAKAN) for Phase 6:** if the threshold is tuned by looking at DS2 results, DS2
stops being a test set. What you report is no longer "performance on
new patients", but "the best performance I could hunt down on the test patients", and
an examiner who understands will attack exactly that.

That is why calibration has its own script (`calibrate_threshold.py`) which
structurally **cannot** touch DS2: it only loads `train.npz` and then
takes the VAL records through `split_train_val`.

---

## 1. Why the metrics are written by hand, not with `sklearn.metrics`

The PRD gives `confusion_matrix` and `classification_report` as examples. All of it is
arithmetic on four numbers:

$$\text{recall} = \frac{TP}{TP+FN}, \quad
\text{precision} = \frac{TP}{TP+FP}, \quad
\text{specificity} = \frac{TN}{TN+FP}$$

$$F_1 = \frac{2 \cdot \text{precision} \cdot \text{recall}}{\text{precision}+\text{recall}}$$

As with `class_weight` in Phase 5: the `CLAUDE.md` gate point forbids adding a
dependency for something a few lines already solve. A non-trivial bonus:
writing it yourself forces you to decide what happens when the denominator is zero.

```python
div = lambda a, b: a / b if b else 0.0
```

A model that never guesses positive has `TP+FP = 0`. sklearn emits a
warning and returns 0; here it is explicit: **0.0, not NaN**. NaN would
propagate into the Phase 7 delta table and corrupt the float32 vs INT8 comparison.

---

## 2. Threshold calibration: criteria written BEFORE seeing the results

The locked criterion: **maximum F1, tie-break to recall when the F1 difference is < 0.005**
(`F1_TIE_MARGIN` in `calibrate_threshold.py`).

The criterion has to be set first: choosing the threshold that "looks best"
after reading the sweep table is tuning that cannot be
defended. With an explicit criterion, `calibrate_threshold.py`
produces the same number every time anyone runs it.

Sweep on VAL (5 DS1 records, 31,047 beats including jittered copies; some
rows from `fase5_threshold_sweep.csv`):

| thr | recall | precision | F1 | specificity |
|---|---|---|---|---|
| 0.20 | 0.9446 | 0.1480 | 0.2559 | 0.3888 |
| 0.50 | 0.8445 | 0.3193 | 0.4634 | 0.7976 |
| 0.70 | 0.7240 | 0.6085 | 0.6612 | 0.9476 |
| 0.75 | 0.6909 | 0.6704 | 0.6805 | 0.9618 |
| **0.80** (chosen) | **0.6539** | **0.7342** | **0.6917** | **0.9734** |
| 0.85 | 0.6141 | 0.7837 | 0.6886 | 0.9809 |
| 0.90 | 0.5542 | 0.8504 | 0.6710 | 0.9890 |

Maximum F1 is at 0.80 (0.6917). The only other candidate within the margin is 0.85
(difference 0.0031); the tie-break picks the higher recall, so 0.80.

A threshold of 0.80 looks high, but it is not a sign of a conservative model. VAL
is assembled from augmented DS1 so it also contains jittered copies, and
shifted windows tend to be given a higher Aritmia probability.
The probability distribution shifts upward, and the correct operating point shifts
with it. At a threshold of 0.35 this model only reaches a precision of 0.19 on VAL.
The consequence: **the threshold belongs to one trained model, not a pipeline
constant**: every retraining must be followed by `calibrate_threshold.py`.

The shape of the trade-off: raising the threshold always raises precision and
lowers recall. There is no universally "correct" threshold; there is only
the threshold that matches the cost of errors in its domain.

---

## 3. `roc_auc()`: why it is written by hand and why it matters

AUC = the probability that a random arrhythmia beat is given a higher score
than a random normal beat. It is computed through the **Mann–Whitney U** statistic,
not by drawing a curve:

$$\text{AUC} = \frac{\sum_{i \in \text{pos}} r_i - \frac{n_{+}(n_{+}+1)}{2}}{n_{+} \cdot n_{-}}$$

with $r_i$ = the probability rank. **Tied values** (`ties`) are given
the average rank, otherwise a model that outputs an identical probability
for all samples would look like AUC 1.0 when it should be 0.5. That is asserted
in `test_auc_perfect_random_and_ties`.

Why AUC is reported together with recall: **AUC does not depend on the threshold**. If the
threshold changes, recall and precision change with it but AUC does not,
so it is what can compare *model quality* across configurations.
The comparison between variants in [`jitter-walkthrough.md`](jitter-walkthrough.md)
relies on this property.

### 3b. PR-AUC and MCC: metrics for an 11% positive class

ROC-AUC uses *specificity*, and *specificity* is easily high when the Normal class
is 89%. Two complementary metrics, computed with numpy in `src/evaluate.py`:

- `average_precision()` = PR-AUC: the area under the *precision*–*recall* curve,
  $\text{AP} = \sum_n (R_n - R_{n-1}) P_n$ over every unique probability value.
  Tied probabilities are merged into one point. Its baseline is the **prevalence**
  (a random model gives AP = the positive proportion), not 0.5 as with ROC-AUC.
- `mcc()` = the Matthews correlation coefficient at a fixed *threshold*, using all four
  cells of the *confusion matrix*. A zero denominator → 0.0 (the same as the
  divide-by-zero policy of `binary_metrics`).

DS2 results (`scripts/extra_metrics.py`, 1 Nov 2026):

| | Float32 | INT8 |
|---|---|---|
| PR-AUC | 0.7445 | 0.7663 |
| prevalence (PR-AUC baseline) | 0.1098 | 0.1098 |
| MCC @ 0.80 | 0.6160 | 0.6171 |
| mean per-recording *recall* (21 arrhythmia recordings) | 0.7402 | 0.7446 |
| median per-recording *recall* | 0.9167 | 0.9167 |

The per-recording mean is the EC57 "average" statistic (the mean of the per-recording
statistic); beat-level *recall* is the "gross" statistic. The mean of 0.7402 is below
the median of 0.9167 because recordings 232 and 213 pull it down (§5).
Reference for the choice of metrics: Saito & Rehmsmeier 2015, Chicco & Jurman 2020/2023
(`docs/2026-11-01-bab4-metrics-crosscheck/klasifikasi.md` at the repo root).

---

## 4. DS2 results

```
DS2  49.656 beat dari 22 pasien  (5.450 aritmia)   threshold 0,80 (dari DS1/val)
  TP=3813  FN=1637  FP=2302  TN=41904
  recall 0,6996   precision 0,6235   F1 0,6594
  specificity 0,9479   accuracy 0,9207   AUC 0,9334
```

Compare with VAL @0.80: recall 0.6539 → **0.6996**, precision 0.7342 →
**0.6235**, F1 0.6917 → **0.6594**. The VAL→DS2 gap appears mainly in
precision: on truly new patients, more Normal beats have an
unrecognized morphology and get flagged as Aritmia. This comparison is a
rough estimate, because VAL contains jittered copies while DS2 is clean.

**Accuracy 0.9207 is deliberately not made the headline.** Guessing Normal for all
beats already gives 0.8902 (44,206 of 49,656 beats). That 3-point difference
hides the real difference: always-Normal has recall 0, this
model 0.70. That is why accuracy is not used as the main metric on
imbalanced data.

### Comparison model

The comparison configuration used in Phases 6b and 6c is the baseline model:
window 90/160 (250 samples), no augmentation, threshold 0.35 (calibrated on
clean VAL), DS2 49,654 beats.

| | baseline (90/160, 0.35) | current (128/128 + jitter, 0.80) |
|---|---|---|
| recall | 0.6661 | **0.6996** |
| precision | 0.4919 | **0.6235** |
| F1 | 0.5659 | **0.6594** |
| specificity | 0.9152 | **0.9479** |
| AUC | 0.8866 | **0.9334** |
| accuracy | 0.8878 (below always-Normal 0.8902) | 0.9207 |

The explanation of the difference (window and augmentation) is in
[`jitter-walkthrough.md`](jitter-walkthrough.md) §5.

---

## 5. Failure dissection: which classes fall

This is where the `symbols` (Phase 2) and `records` (Phase 3) columns pay for themselves.

### Per AAMI class

| Class | n in DS2 | recall | interpretation |
|---|---|---|---|
| **V** (ventricular) | 3,219 | **0.9248** | clearly different morphology → the CNN catches it |
| **S** (supraventricular) | 1,836 | **0.4390** | shape similar to normal, differing in the P wave and timing |
| **F** (fusion) | 388 | **0.0670** | almost total failure |
| Q | 7 | 0.5714 | too few to conclude anything |
| N (normal) | 44,206 | FP rate 0.0521 | 2,302 false alarms |

Three findings worth including in Chapters 4–5:

**1. V is good, S and F fall: this is the classic inter-patient pattern**, not a bug. The PRD
itself predicted it (the reason classification was made binary). The 128/128
window raises recall S and lowers recall F relative to the baseline (S 0.3034
→ 0.4390, F 0.1675 → 0.0670); this trade-off is deliberate and explained in
[`jitter-walkthrough.md`](jitter-walkthrough.md) §5.

**2. The F failure could be predicted from the dataset composition.** Of the 414 class F beats
in DS1, **372 are in record 208 alone**. The model never saw fusion
from diverse patients, so what it learned is "fusion in patient 208's
heart". On the test side the pattern is the same: **362 of the 388 F beats in DS2 are in
record 213**, and recall F there is 0.0387. Class F is practically tested by one
patient different from the one patient who taught it, a direct consequence of
the dataset composition, not an architecture error.

**3. One patient drags down the global metric.** Recall per patient:

```
median recall  0,9167  (atas 21 pasien beraritmia)
rec 232        0,3541  ← 1.381 aritmia, semuanya kelas S
rec 213        0,2246  ← 610 aritmia, 362 di antaranya kelas F
rec 100        0,2059  ← cuma 34 aritmia
```

Median 0.92 vs aggregate 0.70: a big gap. The main cause is rec 232: 1,381 of the
1,836 S beats in all of DS2 are in this patient, and recall S there is only 0.3541
whereas in the other DS2 patients it is 0.6967. One patient holds 25% of all
DS2 arrhythmia, so its failure dominates the beat-level number.

Aggregation stays at the **beat level** (a PRD decision, standard & comparable with the
literature), but the per-record table is kept in
`artifacts/metrics/fase6_per_record_fp32.csv` so that the story behind it can be
told.

### Stage 2: naming the arrhythmia (experimented with, not shipped)

`scripts/second_stage_rules.py` tests naming rules on top of the binary decision. Stage 2
is not trained and is not in `model_int8.h`; it is a scalar rule over beats already
flagged by stage 1, so it cannot change F1, only rename existing TP/FP.
Its ceiling is the stage 1 recall. Only two axes:

```
                  QRS sempit            QRS lebar
prematur+jeda     S                     V (PVC prematur)
tepat waktu       N / tak dinamai       V atau F
```

- **F has no branch.** A fusion beat is a collision of normal and
  ventricular depolarization, so its morphology is between N and V; no feature
  separates something from its own component. P3 measured it: 65 F → VEB,
  0 F → SVEB.
- **Q has no branch.** 100 beats across three databases, and the remainder bucket would be
  dominated by FP (~2,300 : 1 in DS2): naming it "Q" would mean labelling false alarms
  with a clinical class name.
- **S is not named yet.** The S branch waits for gate G2: without RR+1/RR0 there is no
  compensatory pause axis, and S is not separable from normal beats that happen to be fast.
  Naming S from the RR ratio alone gives +P 42% (P5).
- **Raw QRS width, not normalized.** The model features are normalized relative to the
  patient's baseline (good for N vs abnormal), but "V = wide QRS" is
  an absolute physiological threshold. Both come from the same window, zero additional buffer.
- **The threshold criterion = minimum precision (`MIN_NAMED_PRECISION = 0,90`), not F1.**
  Maximizing the V class F1 among flagged beats rewards
  "name everything V" (V ~50% of those flagged): the first experiment landed at the
  bottom of the grid, 4,387 named V, only 1,664 correct (precision 37.9%). The smallest threshold
  whose precision is ≥ 0.90 is chosen (the largest coverage at the promised precision);
  if there is none, the V name is not displayed. The device may stay silent ("tipe tak pasti", type uncertain),
  but must not say "V" if it is wrong 6 times out of 10. On DS2 a threshold of 40 ms gives
  precision 91.7% with coverage 40.4% (30 ms: 51.7%), but the threshold is calibrated
  on VAL, and VAL's maximum is only 43.9%; DS2 must not certify, so
  stage 2 is not shipped (`model/CLAUDE.md`, row Stage 2 (naming V/S)).

---

## 6. What is deliberately NOT done

**Not repeating training in reaction to DS2 results.** Once a model
is improved based on DS2, DS2 becomes validation and the inter-patient claim collapses.
The valid improvement path: go back to DS1/VAL, change something, re-evaluate on
VAL, **then** open DS2 again, and the number of times DS2 was opened is openly recorded in
the report.

**Not shifting the threshold after seeing DS2.** The same reason.

**Not dropping rec 232 from the report.** Removing the hardest patient so that the
numbers look good is a form of manipulation. The right way: report the aggregate,
then explain its distribution.

---

## 7. Comprehension check

1. Guessing "Normal" for all DS2 beats gives accuracy 0.8902, only 3 points
   below the model (0.9207). Which metric shows the model is far more
   useful, and why?
2. Recall of class F is 0.0670. Go back to Phase 3: which decision makes this result
   practically unavoidable, and what would have to change to
   fix it?
3. The threshold is raised 0.80 → 0.90 on DS2 and precision improves. Why must that
   number still not be reported as a result?
4. DS2 AUC is 0.9334 while F1 is only 0.6594. How can a model "rank"
   well but perform moderately when forced to choose 0/1?
5. Why does the threshold of 0.35 that is correct for the baseline model give a precision of 0.19
   on the current model?

## 8. Supporting scripts

| Command | Output |
|---|---|
| `python scripts/calibrate_threshold.py` | The val sweep table + `fase5_threshold_sweep.csv` |
| `make eval` | `fase6_confusion_fp32.png`, `fase6_metrics_fp32.csv`, `fase6_per_record_fp32.csv` |
| `make test` | the whole pytest suite; 8 tests in `tests/test_evaluate.py` lock the metric & AUC formulas |

---

**[← Phase 5: train](train-walkthrough.md)**  ·  [Walkthrough map](README.md)  ·  **[Phase 6b: detection segmentation →](detection-segmentation-walkthrough.md)**
