# Walkthrough `src/quantize.py`: Phase 7

> **Scope:** post-training quantization (PTQ) of the model to full INT8 and measuring its impact on the DS2 metrics.
> **Related code:** `src/quantize.py`, `scripts/quantize_int8.py`, `src/model.py` (`build_deploy_model`), `config.py` (`REP_SAMPLES`, `INT8_IO`, `MAX_MODEL_KB`, `MAX_RHYTHM_SCALE`)
> **Prerequisite:** [`evaluate-walkthrough.md`](evaluate-walkthrough.md) (Phase 6)

A study document, not a specification. The official specification remains
`PRD_Model_Aritmia_TinyML.pdf` pp. 16–17.

Reproduction:

```
cd model
make quantize     # → artifacts/model_int8.tflite + artifacts/metrics/fase7_delta.csv
```

---

## 0. The big picture

```
model_fp32.keras (6.417 param, 25,07 KB float32)
        │
        │  PTQ — Post-Training Quantization
        │  needs: representative dataset (300 DS1 samples, stratified)
        ▼
model_int8.tflite   22,94 KB   ← under the 25 KB limit  (deploy variant, §4b)
        │
        │  RE-evaluation on the SAME DS2, the SAME threshold (0,80)
        ▼
float32 vs INT8 delta table   ← final PA deliverable
```

Why this phase exists: the device runs INT8, not float32. The claim
"the impact of quantization is **measured**, not assumed" can only be made if there is
a real delta number.

---

## 1. What actually happens during quantization

Float32 uses 32 bits per number. INT8 uses 8 bits, only 256 values. The mapping
between the two is affine:

$$x_{\text{float}} \approx (q_{\text{int8}} - z) \times s$$

with $s$ = *scale* (the step size) and $z$ = *zero point* (the integer
that maps to zero). Values on the model in force
(`firmware/include/model_int8.h`):

| Tensor | scale | zero point |
|---|---|---|
| morphology input | 0.042908 | −25 |
| rhythm input | 0.012933 | −70 |
| output (probability) | 0.00390625 = 1/256 | −128 |

An output scale of 1/256 with zero −128 makes sense: a sigmoid is always in $[0,1]$, so
the 256 steps are fully used for that range: $p = (q + 128)/256$.

**What needs calibrating is not the weights but the activations.** The weights' range is
already known (just look at it). The activation range of each layer only appears when data
flows through, which is why a *representative dataset* is needed.

---

## 2. `stratified_indices()`: PITFALL #4

```python
for kelas in (0, 1):
    pool = np.flatnonzero(y == kelas)
    if len(pool) == 0:
        raise ValueError(f"class {kelas} is missing from the calibration data (PITFALL #4)")
    pull = max(1, round(n * len(pool) / len(y)))
```

If the 300 calibration samples are drawn randomly from DS1 without stratification, statistically
~30 Arrhythmia beats will indeed be hit. But "usually hit" is not a guarantee,
and if it misses, what breaks is **the class you care about most**:
the typical activations of arrhythmia beats are never seen by the calibrator, their range is
clipped, and INT8 recall collapses with no visible cause.

Stratification makes it deterministic: the calibration class proportion = the DS1 proportion
(270 Normal : 30 Arrhythmia), and an empty class → `raise`, not silence.

The `seed` is locked so that running `make quantize` twice yields an identical `.tflite`,
a reproducibility requirement in the Phase 8 checklist.

### Why 300, not 100 or 500

The PRD gives a range of ~100–500. The more samples, the more stable the activation range
estimate, but the longer the conversion. 300 gives 30 Arrhythmia beats, enough
to cover the tail of the distribution, and the conversion still takes seconds.

---

## 3. `representative_dataset_gen()`: PITFALL #3, and the version that actually runs

This model has **two** inputs. The PRD warns that a single-input generator will
make the converter fail. What the PRD does not say: the **positional list** form
is also a problem in TF 2.21.

```python
yield [X_morph[i:i+1], X_rr[i:i+1]]        # ← GAGAL
```

```
RuntimeError: tensorflow/lite/kernels/conv.cc:345 input->dims->size != 4 (3 != 4)
              Node number 1 (CONV_2D) failed to prepare.
```

The calibrator pairs list elements to input tensors **according to the model's internal
order**, not the order you wrote. In this model the internal order is
`rhythm` first, so the RR vector `(1,3)` gets jammed into the convolution input.
The error message mentions `conv.cc` and the number of dimensions, and says nothing at all about
"wrong input order".

The correct form: a **named dict**.

```python
rr = X_rr[i:i + 1].astype(np.float32)
yield {
    "morphology": X_morph[i:i + 1].astype(np.float32),
    "rhythm": rr.reshape(target_shape) if target_shape else rr,
}
```

The key names = the `Input(..., name=...)` layer names in `src/model.py`. This is one of the
reasons the input layers have been named since Phase 4, not just tidiness.

The deploy variant (§4b) accepts a rhythm input of shape `(1, 1, 3)`, not `(1, 3)`.
That is why `scripts/quantize_int8.py` calls the generator with
`rr_shape=(1, 3)`, and the generator reshapes the RR vector before it is *yield*ed.

---

## 4. `quantize_int8()`: four lines that decide it

```python
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = rep_gen
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
if int8_io:
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
```

| Line | If omitted |
|---|---|
| `optimizations` | no quantization at all |
| `representative_dataset` | becomes *dynamic range quantization*: INT8 weights, activations stay float |
| `supported_ops = ..._INT8` | the converter may insert float kernels as a fallback |
| `inference_*_type = int8` | I/O stays float32, with quantize/dequantize ops at the ends |

The **int8 in / int8 out** decision (`config.INT8_IO = True`) is locked to be
consistent with the firmware plan: not a single float kernel inside the
model. Its verification is mechanical in `tests/test_quantize.py`:

```
dtype semua tensor: {'int8': 39, 'int32': 16}
```

Zero `float32` tensors. The 16 `int32` tensors consist of two kinds,
and both are legitimate in the TFLite INT8 scheme: the **biases** of each convolution layer (the accumulator
of int8×int8 multiplication is stored in 32 bits before being *rescale*d) and the static **shape
constants** for the `Squeeze`/reshape ops that TFLite uses when
implementing `Conv1D` through 2-D convolution.

### Rhythm input scale guard

`quantize_int8` calls `assert_rhythm_scale_sane` before returning the
blob. The INT8 scale of the rhythm input is derived from the min/max of the calibration samples; a single
beat with an extreme RR in the calibration pool (record 207 has `RR_prev` = 100 s)
widens the scale by tens of times, normal RR is left with a few int8 levels, and
the rhythm branch is practically dead. The symptom is poor S recall, not an error. A blob
with a scale above `MAX_RHYTHM_SCALE` (0.05) is rejected with `ValueError`;
the value on the model in force is 0.0129. A healthy scale is theoretically ~0.0197
(p99.99 |X_rr| = 2.51), a broken one ~0.78 (outlier injected: 0.3952), so 0.05
gives ~2.5× headroom from healthy and ~15× below broken. The chance of being hit per seed
was measured on 19 Sep: 4.6% (mitdb only), 1.8% (three databases).

### Consequences for the firmware

```c
// input: z-score result (float) → int8
in_morph->data.int8[i] = to_int8(beat.window[i], ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO);
// output: int8 → probability
return (output_tensor->data.int8[0] - ECG_OUT_ZERO) * ECG_OUT_SCALE;
```

The `scale` and `zero_point` values are *generate*d into `model_int8.h` as the
`ECG_*_SCALE`/`ECG_*_ZERO` macros. Do not hardcode them manually in the firmware,
because they change every time the model is retrained.

---

## 4b. What gets quantized is not the training model but the deploy variant

```python
deploy = build_deploy_model(tf.keras.models.load_model(keras_path))
blob = quantize_int8(deploy, ...)
```

The training model uses `GlobalAveragePooling1D` → the `MEAN` op, and **TFLite Micro
computes `MEAN` differently from regular TFLite**. On the PC the result is 0.973; on the ESP32-S3
the same model gives 0.336, without any error.

`build_deploy_model` swaps two ops, and the weights are copied as is (identical down to
1.19e-07 in float32, so **no retraining**):

| Training model | Deploy model | Why |
|---|---|---|
| `GlobalAveragePooling1D` (`MEAN`) | `DepthwiseConv1D(L)` with weights 1/L, L = sequence length (32 at window 256) | a convolution = the same average, but it gets its own output quantization scale |
| `Dense` | `Conv1D` kernel 1 | stays 3-D → no `Flatten` needed (which brings in a dynamic-shape op) |

The `AveragePooling1D` alternative is **not used**: the pooling op inherits the input
scale (0.332), while the average of 31 values is much smaller than that range →
~3 bits of resolution wasted and DS2 recall drops 0.655 → 0.528 (measured on the
baseline model with window 250, whose sequence length at this point is 31). The convolution gets its own
output scale (0.0429, exactly the same as the `MEAN` choice).
`build_deploy_model` takes the kernel length from the tensor shape, so at the
window 256 in force the kernel is 32.

The full story of chasing this bug: [`firmware-walkthrough`](firmware-walkthrough.md) §5.

---

## 5. `predict_tflite()`: the third pitfall, forgetting to dequantize

```python
inputs = sorted(interp.get_input_details(), key=lambda d: int(np.prod(d["shape"])))
rr_in, morph_in = inputs[0], inputs[1]
```

The input order in the `.tflite` is **not guaranteed** to match the order in Keras (exactly
the problem of §3). Here it is handled by sorting on the **number of elements**:
RR `(1,1,3)` = 3 elements, morphology `(1,256,1)` = 256 elements. The number of dimensions
cannot be used to tell them apart, because in the deploy model both are 3-D.
This method depends on neither name nor order.

Then manual quantization on the way in, manual dequantization on the way out:

```python
np.clip(np.round(x / scale) + zero, -128, 127)     # input
(q.astype(np.float32) - zero) * scale              # output
```

The `clip` is mandatory: z-score values can exceed the range seen during calibration,
and without clip the result *wrap around*: a large positive number becomes an extreme negative.
If the dequantize step on the output is forgotten, the metrics are computed from integers
−128..127 compared against the 0.80 threshold: every q ≥ 1 (p ≳ 0.5)
becomes Arrhythmia, so the operating point silently moves without any error (the PRD
states this explicitly: "forgot to dequantize → nonsense metrics").

---

## 6. Delta table: the final result

Size: **23,488 bytes = 22.94 KB** (< 25 KB), from 25.07 KB float32.

| Metric | Float32 | INT8 | Delta |
|---|---|---|---|
| accuracy | 0.9207 | 0.9198 | −0.0009 |
| precision | 0.6235 | 0.6169 | −0.0067 |
| **recall** | 0.6996 | 0.7105 | **+0.0108** |
| F1 | 0.6594 | 0.6604 | +0.0010 |
| specificity | 0.9479 | 0.9456 | −0.0023 |
| AUC | 0.9334 | 0.9344 | +0.0010 |
| TP/FN/FP/TN | 3813/1637/2302/41904 | 3872/1578/2405/41801 | - |

**|Delta recall| 1.08 points**, below the "ideal < 1–2%" threshold stated in the PRD.
Its viability is proven with numbers, not assumed.

### How to read the numbers that shifted

Recall rises, precision and specificity fall. That is not evidence that INT8 is "more
sensitive". AUC shifts +0.001: the model's ability to rank is practically unchanged,
and that is the honest measure.

What happens: quantization shifts the probability distribution slightly. With a
fixed threshold of 0.80, some beats move sides: 59 more arrhythmias
are caught (FN 1,637 → 1,578) and 103 more false alarms appear (FP 2,302 →
2,405). The direction of this shift is not fixed: on the baseline model (window 250,
threshold 0.35) the direction is reversed: recall −0.0112, precision +0.0383, AUC
−0.0004. What stays constant is the magnitude: small, and AUC barely moves.

This is an important reminder: **a metric difference at a fixed threshold mixes two things**:
a change in model quality and a shift in probability calibration. AUC
separates the two, and AUC says the INT8 model is equivalent.

### Per-class delta and changed labels

The impact of INT8 on ECG arrhythmia in the literature tends to concentrate in class S (Busia
2024), so an aggregate difference can hide one class that drops. Measured
with `scripts/extra_metrics.py` (1 Nov 2026, *threshold* 0.80):

| *Recall* | Float32 | INT8 | Delta |
|---|---|---|---|
| S (1,836 beats) | 0.4390 | 0.4630 | +0.0240 |
| V (3,219 beats) | 0.9248 | 0.9282 | +0.0034 |
| F (388 beats) | 0.0670 | 0.0773 | +0.0103 |
| PR-AUC | 0.7445 | 0.7663 | +0.0218 |
| MCC | 0.6160 | 0.6171 | +0.0011 |

All three classes shift in the same direction as the aggregate *recall* (+0.0108), and
no class falls. The largest is S, +0.0240, slightly above the aggregate
threshold of 0.02 but in the improving direction. Labels change on **272 of 49,656
beats (0.55%)**. This shift is consistent with the explanation above:
INT8 probabilities rise slightly around the *threshold*, so more
beats cross 0.80 in every class.

---

## 7. What is deliberately NOT done

**Does not change the threshold for INT8.** If the threshold were retuned as well,
what is measured is no longer the pure effect of quantization. The evaluation procedure must be identical to
Phase 6: the same DS2, the same threshold, the same metric functions.

**Does not use DS2 as the representative dataset.** Calibration draws from
DS1. Touching DS2 here would leak test set statistics into the model.

**Does not use QAT** (Quantization-Aware Training). PTQ already meets the target
(|delta recall| 0.0108 < 0.02; 22.94 KB < 25 KB); QAT means retraining and
adding one more source of variation for a gain that may not exist.

---

## 8. Comprehension check

1. `converter.representative_dataset` is not set but `optimizations` is.
   The model is still produced and is smaller: what is actually quantized, and
   why is that not enough for the ESP32?
2. Why are there 16 `int32` tensors in a "full-INT8" model, and why is that not a
   violation of the claim?
3. `np.clip(..., -128, 127)` is removed from `_quantize`. When does the bug show up, and
   why does it not show up in most beats?
4. INT8 recall rises 1.1 points and precision falls 0.7 points, while AUC only
   shifts +0.001. Explain why those facts do not contradict each other.

## 9. Supporting scripts

| Command | Output |
|---|---|
| `make quantize` | `model_int8.tflite`, `fase7_delta.csv`, `fase7_confusion_int8.png` |
| `make test` | the whole pytest suite; 9 tests in `tests/test_quantize.py` lock calibration, the full-INT8 claim, and the rhythm input scale |

---

**[← Phase 6b: detection segmentation](detection-segmentation-walkthrough.md)**  ·  [Walkthrough map](README.md)  ·  **[firmware: port to ESP32-S3 →](firmware-walkthrough.md)**
