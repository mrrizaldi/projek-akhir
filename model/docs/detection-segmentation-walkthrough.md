# Walkthrough Phase 6b: on-device segmentation cost

> **Scope:** measures how much is lost when windows are cut from Pan-Tompkins detections instead of annotated R-peaks, and sets the R-peak alignment order the firmware must follow.
> **Related code:** `scripts/eval_detected_segmentation.py`, `src/evaluate.py` (`pair_detected`), `config.py` (`PT_DETECTOR_OFFSET`, `PT_REFINE_WIN`, `GROUP_DELAY_SAMPLES`, `PT_REFRACTORY_MS`), `firmware/include/ecg_preproc.h`
> **Prerequisite:** [`evaluate-walkthrough.md`](evaluate-walkthrough.md) (Phase 6)

A study document, not a specification. An extra experiment outside the PRD, answering
a question that Phase 6 leaves unanswered.

Reproduction:

```
cd model
python scripts/eval_detected_segmentation.py
```

---

## 0. The question

Every Phase 6 number is measured with windows cut from the **R-peaks annotated
by the cardiologist**, a perfect position. On the device, windows are cut from
the **Pan-Tompkins detections**. Two things change at once:

1. A beat that is **not detected** never reaches the model
2. A detected beat has an R position that is **slightly off**

The cost has to be measured. Without this number, the Phase 6 recall holds for the laboratory,
not for the device.

**Discipline:** the detector offset is calibrated on **DS1**; DS2 tunes nothing.
The model is float32 (not INT8) so that only the segmentation changes. DS2 is
looked at a second time here: purely to measure, no parameter is taken
from it.

---

## 1. Three corrections the firmware must make

### a. Detector offset (~38 samples)

Pan-Tompkins works on the already filtered signal and has its own bandpass,
derivative, and 150 ms integration, all of which add delay. Measured on DS1 over
47,848 pairs:

```
median 38 sampel (105,6 ms), std 13,0, p10 21, p90 52
```

The median is compensated; a std of 13 samples is the jitter that remains.

### b. Alignment to the true peak

Median compensation alone leaves ±13 samples of jitter. The remedy is cheap: after the
detector points to a rough location, search for the **maximum peak** within ±25 samples (±70 ms)
around it.

### c. Restoring the filter group delay (+4 samples)

This is the subtlest one, and the most damaging if missed.

Training windows are cut at `r_annotated - WIN_PRE`, while the filtered signal
shifts the R peak by **+4 samples** (PITFALL of Phase 1). So during training,
R always lands at **`WIN_PRE + 4`**, index **132** in the 128/128 window that
is in force (94 in the 90/160 baseline window).

The alignment in (b) finds the peak in the filtered signal, which is `r + 4`. If used
directly, the window starts at `r + 4 - WIN_PRE` and R lands at
`WIN_PRE` (128), not 132. That is why the alignment result is reduced by 4
(`GROUP_DELAY_SAMPLES`).

---

## 2. The model is VERY sensitive to the R position

Shift by 4 samples, 11 milliseconds, in either direction. Measured on the baseline model
(window 90/160, no augmentation, threshold 0.35), so the correct position
is index 94:

| R position in window | recall | precision | F1 |
|---|---|---|---|
| 90 | 0.8952 | **0.1243** | 0.2182 |
| **94** (as in training) | 0.6821 | **0.4794** | **0.5631** |
| 98 | 0.9007 | **0.1249** | 0.2194 |

Precision drops **almost 4×** for an 11 ms shift, and symmetrically in both directions.

### Why so sensitive, when there is GlobalAveragePooling?

GAP does discard *absolute position* information, but the layers before GAP have three
`MaxPooling1D(2)` with a total stride of **8**. A shift of 4 samples is **half a pooling
bin**. A sample that used to fall in bin A moves to bin B, so the representation
entering GAP really changes phase. The model never saw this variation
during training because all windows were segmented from precise annotations.

Practical consequence: **the firmware must put R at index `WIN_PRE + 4`**
(132), and that is not a cosmetic detail. This sensitivity is also the basis of Phase 6c:
the model in force is trained with R positions shifted according to the measured detector
residual, so that it does not depend on the exact window phase. See
[`jitter-walkthrough.md`](jitter-walkthrough.md).

---

## 3. Results

The numbers below are measured for two models: the **baseline** (window 90/160, no
augmentation, threshold 0.35) and the **model in force** (window 128/128, jitter
augmentation, threshold 0.80; measurement condition: the same script, 13 Oct 2026).
The detector statistics do not depend on the model, so they are the same for both:

```
Detektor di DS2: 47.074 terdeteksi, 2.638 terlewat (sensitivity 0,9469),
                 2.194 deteksi palsu
```

Detections are paired to annotations by `src/evaluate.pair_detected` (greedy
1-to-1, ±150 ms tolerance) from the DETECTION side, the reverse of `bench_pantompkins`
which pairs from the annotation side: the device works from detections, so each R-peak
it finds is classified, whether or not a real beat exists. A detection without
a pair gets index −1 (false detection) and is still classified. System-level
recall uses all real arrhythmias as the denominator, including those that never
reach the model because the detector missed them.

### A. Classification on beats that were detected

| | baseline: annotation | baseline: detection | in force: annotation | in force: detection |
|---|---|---|---|---|
| recall | 0.6661 | **0.6821** | 0.6996 | **0.7279** |
| precision | 0.4919 | **0.4794** | 0.6235 | **0.5869** |
| F1 | 0.5659 | **0.5631** | 0.6594 | **0.6499** |

For both models, the F1 with detection segmentation differs by less than 0.01 from the F1
with annotations. **On-device segmentation does not damage classification**, provided
the three corrections in §1 are made.

### B. System level

```
                aritmia asli   tertangkap   recall sistem
baseline           5.453         3.084         0,5656   (anotasi 0,6661)
berlaku            5.453         3.291         0,6035   (anotasi 0,6996)
```

System recall drops by about 10 points from the recall with annotations. All of the
loss comes from beats that were never detected, not from shifted windows:
on detected beats, recall is actually slightly higher (A).

### C. False detections

2,194 windows without a real beat. In the baseline, **43.9%** are classified as Arrhythmia, giving
964 extra false alarms on top of the 3,349 already there. In the model in force,
**50.4%**, giving 1,106 extra false alarms on top of 2,316.

---

## 4. Most important finding: the detector discards arrhythmias more often

Pan-Tompkins sensitivity per AAMI class on DS2:

| Class | Sensitivity |
|---|---|
| N (normal) | 0.9614 |
| **S (supraventricular)** | **0.6494** |
| V (ventricular) | 0.9146 |
| F (fusion) | 0.9820 |
| **Normal vs Arrhythmia** | **0.9614 vs 0.8296** |

The cause is structural: supraventricular beats arrive **prematurely**, and Pan-Tompkins
blocks detection during a **200 ms refractory period** after the previous beat
(`PT_REFRACTORY_MS` in `config.py`). A beat that arrives too early gets
blocked, yet "arrives too early" is the very definition of a premature beat.

The effect compounds: the classification recall of class S is already low (0.4390 on the model
in force, 0.3034 on the baseline), and only 65% of S beats even reach the
model. This is the quantitative explanation of why class S is the weakest point of the whole system, and a clear
direction for improvement: lowering the refractory period raises S sensitivity at the cost of
more false detections. That trade-off can be measured with the same script.

---

## 5. What this means for the firmware

```c
// urutan wajib di alur hidup on-device
r_kasar   = pan_tompkins(filtered)      // punya delay ~38 sampel
r_kompen  = r_kasar - 38                // kompensasi median (kalibrasi DS1)
r_halus   = argmax(filtered, r_kompen +- 25)   // puncak sebenarnya
r_used   = r_halus - 4                 // kembalikan group delay -> R di indeks 132
window    = filtered[r_used - 128 : r_used + 128]   // WIN_PRE / WIN_POST
```

The same constants in the firmware: `ECG_PT_OFFSET` 38, `ECG_GROUP_DELAY` 4,
`ECG_WIN_PRE`/`ECG_WIN_POST` 128 (`firmware/include/ecg_preproc.h`). If even one
step is skipped, precision drops by up to 4× (measured on the baseline) without
a single error.

---

## 6. Comprehension check

1. Why does a 4-sample shift damage the model when GAP should make the model
   shift-tolerant? (Hint: compute the total stride of the three MaxPooling layers.)
2. Classification recall on detected beats (0.7279) is slightly HIGHER
   than with annotations (0.6996). Why is that not evidence that detection is better?
3. The refractory period is lowered from 200 to 150 ms. Which metric improves, which
   worsens, and how can it be measured without touching DS2 again?
4. Why does this experiment use the float32 model, not the INT8 one that will actually be
   used on the device?

## 7. Scripts

| Command | Output |
|---|---|
| `python scripts/eval_detected_segmentation.py` | All the numbers above + `fase6b_segmentasi_deteksi.csv` |
| `python scripts/bench_pantompkins.py 100` | Detector accuracy per record + plot |

---

**[← Phase 6: evaluate](evaluate-walkthrough.md)**  ·  [Walkthrough map](README.md)  ·  **[firmware: port to ESP32-S3 →](firmware-walkthrough.md)**
