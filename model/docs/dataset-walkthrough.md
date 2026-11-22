# Walkthrough `src/dataset.py`: Phase 3

> **Scope:** assembling the inter-patient DS1/DS2 split (de Chazal 2004) from the per-record `.npz` files, along with the cross-patient leakage guard.
> **Related code:** `src/dataset.py`, `scripts/build_split.py`, `config.py` (`DS1`, `DS2`, `PACED_EXCLUDED`, `VAL_RECORDS`, `TRAIN_DATABASES`), `tests/test_dataset.py`
> **Prerequisite:** [`prep-beats-walkthrough.md`](prep-beats-walkthrough.md)

A study document, not a specification. The official specification remains
`PRD_Model_Aritmia_TinyML.pdf` p. 11. A continuation of
[`features-rr-walkthrough.md`](features-rr-walkthrough.md) (Phase 2).

The numbers here are the result of `make split` over 44 records. Reproduction:

```
cd model
make prep && make split
```

---

## 0. The big picture: this is where data stops being "per patient"

```
per_record/100.npz  101.npz  ...  (44 files, one per patient)
        │
        │  build_split()  ← selects files by DS1/DS2, does NOT shuffle beats
        ▼
train.npz (DS1, 22 pasien)        test.npz (DS2, 22 pasien)
        │                                  │
        ▼                                  ▼
   Phase 4-5 train                   Phase 6 evaluate (only now may be touched)
```

Phase 3 **computes nothing**. No filter, no new feature,
no normalization. It only stacks arrays and keeps one promise: **not
a single beat from the same patient appears on both sides.**

---

## 1. Why a per-patient split, not a random per-beat one

This is the single decision that most determines whether your final numbers are meaningful
or a lie.

### What happens if beats are shuffled (*intra-patient*)

MIT-BIH is 30 minutes per patient. A patient's beats resemble each other: the QRS
morphology is characteristic of that person (electrode shape, anatomy, lead position). If 100,624
beats are shuffled and then split 80:20, then for almost every beat in the test set there is
a beat **from the same patient, the same minute** in the training set.

The model does not need to learn "what a PVC looks like". It only needs to learn "what the PVC
of patient 208 looks like". Accuracy can be 99%, and **it is useless in the clinic**, because
the patient who comes tomorrow is not in the training set.

This is a form of *data leakage*: not leaking through labels, but through **identity**.

### What we use (*inter-patient*, de Chazal 2004)

22 patients for training, 22 other patients for testing. The model must generalize
to hearts it has never seen, just like the deploy condition on the ESP32.

The price: **accuracy drops drastically**, and that is expected. The intra-patient literature
reports 99%; an honest inter-patient figure is usually far below that. If
your number looks too good, the first suspicion is that the split leaks.

```python
if set(np.unique(train["records"])) & set(np.unique(test["records"])):
    raise ValueError("record leaks across splits")
```

That check runs on every `make split`. It is cheap, and it closes the only way this
leakage could get in silently.

---

## 2. `assert_split_valid()`: three conditions before anything is read

```python
ds1, ds2, paced = set(DS1), set(DS2), set(PACED_EXCLUDED)
if ds1 & ds2:
    raise ValueError(f"DS1 ∩ DS2 is not empty: {sorted(ds1 & ds2)}")
if (ds1 | ds2) & paced:
    raise ValueError(f"paced record included in split: {sorted((ds1 | ds2) & paced)}")
total = len(ds1) + len(ds2) + len(paced)
if total != 48:
    raise ValueError(f"total records {total}, must be 48")
```

It runs **before** any file is opened: if the list is wrong, it fails within
milliseconds, not after reading 44 files.

Condition 3 (`= 48`) is a typo guard. MIT-BIH has exactly 48 records; if
one number is deleted or duplicated while editing `config.py`,
the count is off and the test catches it.

### Why 4 records are dropped, two different reasons

| Record | Reason | Kind |
|---|---|---|
| 102, 104 | no MLII channel → `load_record` raises `ValueError` | **technical** |
| 107, 217 | *pacemaker* patients | **methodological** |

107 is 97% `/` symbols (paced). If it were included, one record would contribute 2,078 beats
of "Arrhythmia", and the model would learn to recognize the *pacemaker*, not arrhythmia. All four
live in a single list `PACED_EXCLUDED` in `config.py`, used by Phase 2 **and**
Phase 3. One source of truth, do not duplicate it.

---

## 3. `stack_records()`: stacking, plus one column that is easy to forget

```python
with np.load(path) as z:
    morph.append(z["windows"])
    rr.append(z["rr"])
    y.append(z["labels"])
    origin.append(np.full(len(z["labels"]), record_int_id(rec, db), dtype=np.int32))
```

`record_int_id` maps a record name to `int32`: mitdb and svdb are already numeric
(offset 0), incartdb `"I01".."I75"` becomes 1001..1075. Those three ranges do not
overlap, so `records` stays unique across databases.

The first three arrays are obvious. The fourth, `records`, is the **trace of each
beat's origin**, and it is the only reason Phase 6 can answer the right question.

A global metric ("recall 0.78") hides something important: 0.78 can mean uniform, or it can be 0.95 in
20 patients and 0.10 in 2 patients. The second possibility is far more dangerous in a
medical device. With `records`, a per-patient metric is just `y[records == r]`.

Without that column, the information is **permanently lost** once the arrays are merged, and
it cannot be reconstructed, because the beat order has already merged.

### `FileNotFoundError`, not `continue`

```python
if not os.path.exists(path):
    raise FileNotFoundError(f"{path}: run `make prep` first")
```

Skipping a missing record would produce a split that is **valid in form
but silently smaller**, and you would only notice when comparing the beat count
with the already-printed Chapter 4.

### `reshape(-1, WIN_LEN, 1)`

```python
"X_morph": np.concatenate(morph).reshape(-1, WIN_LEN, 1).astype(np.float32)
```

`Conv1D` in Keras demands the shape `(batch, langkah_waktu, kanal)`. We have
one channel (MLII), so the last dimension = 1. It is added here, once,
not inside the training loop, so that `train.npz` already has exactly the shape
the model consumes.

---

## 4. Numbers from `make split`

```
DS1     22 record   152904 beat   Normal 137451 (89,9%)   Aritmia 15453 (10,1%)
DS2     22 record    49656 beat   Normal  44206 (89,0%)   Aritmia  5450 (11,0%)
X_morph (152904, 256, 1) / (49656, 256, 1)      X_rr (152904, 3) / (49656, 3)
```

DS1 contains three copies of each beat (one clean + two jittered, see
[`prep-beats-walkthrough.md`](prep-beats-walkthrough.md) §4): $152904 = 3 \times
50968$. Without augmentation, $50968 + 49656 = 100624$, exactly the same as the Phase 2
clean-data total. No beat is lost or counted twice.

### The class ratios are similar, the patient distributions are not

| | DS1 (train) | DS2 (test) |
|---|---|---|
| most arrhythmia | 208 (46.3%), 106 (25.7%), 119 (22.3%) | **232 (77.7%)**, 200 (33.0%), 233 (27.6%) |
| arrhythmia ~zero | 230, 115, 122 (0.0%) | **212 (0.0%)**, 111 (0.0%), 103 (0.1%) |
| beats per record (clean) | 1,616 (rec 124) – 3,360 (rec 215) | 1,516 (rec 123) – 3,248 (rec 213) |

The aggregate ratios are nearly the same (10.1% vs 11.0%): that is a lucky coincidence,
not the result of balancing. **Do not be tempted to "fix" the split to make it more
balanced**: the list belongs to de Chazal 2004 and its purpose is precisely so that your numbers
are comparable with the literature.

What must not be ignored: **rec 212 contributes 2,745 test beats without a single
arrhythmia**, while **rec 232 is dominated by arrhythmia (77.7%)**. The global average
will flatten these two poles. That is why the `records` column is kept.

### Cross-database split (`make split-multi`)

`build_split_multi` assembles the split for the cross-database ablation and writes
`train_multi.npz`, `test_ds2.npz`, and `test_<db>.npz`:

- **train:** DS1 mitdb + the training portion of the databases in `TRAIN_DATABASES`.
- **ds2:** DS2 mitdb as is: the main number comparable with the literature.
- **`<db>_test`:** the held-out set of each additional database, chosen by the rule
  `sorted(records)[::4]` (`split_train_test`), not by a seed.

Databases that have not been prepped are skipped, but a database that is only partly prepped
is rejected with `ValueError`, because the `[::4]` rule over an incomplete list
gives a different split without any sign. The same leakage check applies between
`train` and every test set. The production model is still trained from `train.npz`
(mitdb only).

### Multi-database constants in `config.py`

The goal of Phase A (a supervisor's request): expand the training data. The following distribution
was measured on 19 Sep 2026 from the original PhysioNet annotations mapped through `AAMI_MAP`,
not copied from a paper (the same numbers are frozen in
`tests/test_multidataset.py`):

```
svdb      78 rec, 128 Hz | S 12.198/73rec  V  9.943/67rec  F  23/6rec   Q 79/20rec
incartdb  75 rec, 257 Hz | S  1.960/36rec  V 20.013/70rec  F 219/22rec  Q  6/5rec
```

**Why these two databases.** Both have beat-level annotations (`.atr`, one
symbol per R-peak) with the same WFDB alphabet, so `AAMI_MAP` handles them
without a new mapping. PTB-XL, CPSC, and Chapman were rejected not because of the sampling
frequency, but because their diagnoses are per recording: per-beat labels cannot be
derived from them. The same condition applies to the next database
added to `download_data.py`.

**Expected role.** svdb for recall S (0.422 ± 0.156; from 634 S beats
in ~20 patients to ~11,250 in ~102). incartdb for F concentration: 372 of the 394
mitdb F beats are in record 208 alone (one effective patient), whereas incartdb
spreads 219 beats over 22 records; what is improved is patient coverage, not the beat
count. Q is not helped: 100 beats across three databases (mitdb 8 + 7, svdb 79,
incartdb 6) so Q remains a class that cannot be reported.

**DS2 mitdb does not change by a single byte.** It is the only set comparable with the
literature, and the rule "DS2 selects nothing" can only be enforced if its
composition is not a variable. New data goes into train; the rest becomes a separate
test for cross-database generalization. `load_record(db="mitdb")` is guarded
44/44 records byte-identical to before Phase A.

**`leads`.** The first available lead is chosen. mitdb MLII = the device reference
(AD8232 lead II). incartdb `II` is closest to it. svdb (Holter) does not
name its leads, so `ECG1` is used; its polarity was verified by `scripts/check_lead.py`
(gate A2: 8/8 svdb records positive at R).

**`selaraskan` and `ALIGN_WIN = 16`.** Annotation conventions differ between databases.
Measured over normal beats, the peak position relative to the annotation in the bandpassed signal:

```
mitdb  median  +3   p5..p95  +1..+5     anotasi DI puncak; +3/+4 = group delay
svdb   median +10   p5..p95  -2..+15    ~6 sampel lebih awal, sebaran 3x lebih lebar
```

That +6 sample bias is above this repo's danger threshold (a 4-sample miss drops
precision 0.48 → 0.12) and is systematic, not zero-centered jitter: without correction
every svdb beat is shifted in the same direction and the model reads it as a different morphology, i.e.
learns the dataset identity. So svdb and incartdb are aligned
(`align_r`: shift the annotation to the peak, then restore the group delay; equivalent
to the Pan-Tompkins alignment in the firmware, with a narrower window). mitdb must be
`False`: it is the reference for `golden_ref.h` and all locked ablations, and a median of +3 vs +4
means aligning it shifts R by ~1 sample and invalidates everything.
The half-width of the peak-search window of 16 samples (±44 ms) covers svdb p1..p99
(−9..+15) without reaching the T wave (~200-300 ms = 72-108 samples); 25
(`PT_REFINE_WIN`, ±70 ms) was made for the detector's spread (std 13 samples) and here
is too wide. Measured in the Phase A audit, 1,133 of 48,630 beats of the new
databases (2.33%) wanted to shift ≥ 16 samples and were truncated at the window boundary; that is
accepted, because widening the window lets `argmax` jump to the T
wave, and the remaining shift is still within the spread trained by the jitter augmentation.
`check_lead.py` reads polarity from the "mentah" (raw) column and
alignment from the "selaras" (aligned) column; the "selaras" column must not judge polarity
because `align_r` uses a signed argmax that forces the value at R to be positive.

**The sampling rate is unified to 360 Hz.** `WIN_PRE` is defined in samples,
not time: 128 samples @ 360 Hz = 355 ms (what was ablated and locked), whereas
128 samples @ 128 Hz = 1,000 ms, entirely different physiology. What pays off in the
window ablation is the context of the P wave and the PR interval ~150-200 ms before R,
so the duration is what must be preserved. With a 360 Hz target, `WIN_PRE/WIN_POST`,
the bandpass coefficients, the firmware `ECG_FS`, and `golden_ref.h` do not change.
`resample_to_fs` uses `resample_poly` (polyphase, linear-phase), and the R position
only needs to be rounded as long as the direction is upsampling (indices spread further apart, they cannot
collide); if one day `fs_target < fs_source`, two R's could fall on the same index
(RR = 0), and that must be loud. The `fs` of each record is checked against the
promise `DATASETS[db]["fs"]` before resampling, so that a wrong config table is not
masked by the resample.

**`id_offset`.** See `record_int_id` in §3. Without that map `int("I18")`
raises `ValueError` in `stack_records`, rather than failing with a useful message.

**`SPLIT_EVERY_NTH = 4`.** The held-out set of each additional database = every 4th record
in sorted order (~25%). A rule, not a seed: nothing can be
steered, and anyone can verify it with `sorted(records)[::4]`.
A consequence that has been checked: the incartdb held-out gets only ~13-20 F beats
(I05 = 9, I65 = 4, plus a small remainder) because the largest F records (I18 = 56,
I74 = 48) fall into train. That is intentional; F in test is reported as raw
TP/FN counts, not a recall with decimals.

**`n_record`.** The expected number of complete records (mitdb 48 − 4
`PACED_EXCLUDED` = 44). The held-out rule is computed from the list that EXISTS, so a
database that is only half downloaded produces a different held-out set without any
sign. Measured on 19 Sep with 65/75 incartdb records: I68 entered the held-out set when
it should not have, and I65/I69/I73 were lost (I65 holds 4 F beats). That is why
`build_split_multi` rejects a database whose record count is not exact; a
wrong split is worse than an error. `available_records` also demands `.hea`,
`.dat`, and `.atr` together, because a download still in progress leaves a
`.hea` without an `.atr`.

**`TRAIN_DATABASES = ("mitdb", "svdb")`, incartdb test only.** The held-out set always becomes
test, but the train portion of a database only joins if it is in `TRAIN_DATABASES`.
Phase B measured incartdb as harmful in training even though it contributes 256,454 training beats
(4 variants × 3 seeds):

```
                mitdb      +svdb    +incartdb   +keduanya
AUC            0,9373     0,9314     0,8881      0,9092
recall S       0,4221     0,4980     0,3312      0,4050
```

The recall S ranges +svdb [0.423; 0.573] and +incartdb [0.307; 0.355] are separate:
the effects are opposite, and in "+both" they almost cancel (−0.017).
The cause is not the lead (II ≈ MLII, gate A2) or the resolution (257 > 128 Hz),
but composition: 15,592 V beats from another population blunt the N-vs-S
separation. incartdb is still used as the cross-database test (41,108 beats,
19 patients). The production model is still mitdb only (`model/CLAUDE.md`, row Database
LATIH); `TRAIN_DATABASES` is only used by the ablation path.

**Frozen numbers in `tests/test_multidataset.py`.** All were measured on 19 Sep 2026 and
frozen so that silent changes are noticed. If one fails, the order of
suspects: (1) the record list changed, (2) `AAMI_MAP`/`BEAT_SYMBOLS` edited,
(3) `DATASETS` filled in wrong, not "the numbers happen to differ". VAL is kept similar to DS2
(the threshold is calibrated on VAL then used on DS2), whereas train may
shift because svdb is rich in S.

---

## 5. What is deliberately NOT done

**No `shuffle`.** The order within the file follows the record order. Shuffling
is the business of `model.fit(shuffle=True)` during training: done in memory, per
epoch, and never crossing the train/test boundary.

**No validation split in `train.npz`.** DS1 is split into train/validation
in Phase 5 via `split_train_val`, which is also **per patient**: the records in
`VAL_RECORDS` (101, 114, 201, 220, 223) become validation, and that function
rejects val records outside DS1. DS2 is not involved.

**No additional normalization.** `windows` is already z-scored per window since
Phase 1; `rr` is deliberately left raw (PRD JEBAKAN #2, trap #2). Computing $\mu,\sigma$
here would mean computing it from DS1+DS2 together = leakage.

**DS2 is not read for anything other than being stored.** Rule #4 of `CLAUDE.md`:
forbidden to touch until Phase 6. Its label distribution is printed because that is the Phase 3 DoD,
not to become the basis of any decision.

---

## 6. Comprehension check

1. If rec 208 (46.3% arrhythmia, DS1) were moved to DS2, which metric would change
   the most, and why is that still not a valid reason to move it?
2. `records` is not stored. In Phase 6 you want to know recall per patient. Why
   can it not be reconstructed from `train.npz` alone?
3. The model is trained with `X_morph` of `shape (N, 256)` rather than `(N, 256, 1)`.
   Where does the error appear, and why is it better to fix the shape in
   Phase 3 than in the training script?
4. Someone changes `build_split` to shuffle 100,624 beats and then split
   80:20. Phase 6 accuracy rises from 0.80 to 0.99. What is the name of the mistake, and
   which one-line check in `src/dataset.py` should have prevented it?

## 7. Supporting scripts

| Command | What it shows |
|---|---|
| `make split` | Assemble train/test + a distribution summary per split |
| `make split-multi` | Assemble the cross-database split (ablation) |
| `make test` | All tests; `tests/test_dataset.py` locks the Phase 3 split contract |

---

**[← Phase 2b: prep_beats](prep-beats-walkthrough.md)**  ·  [Walkthrough map](README.md)  ·  **[Phase 4: model →](model-walkthrough.md)**
