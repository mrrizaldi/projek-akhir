# Walkthrough `scripts/prep_beats.py`: Phase 2 (execution)

> **Scope:** executing Phases 0–2 over all records: selecting valid beats, DS1 jitter augmentation, and writing one `.npz` per record.
> **Related code:** `scripts/prep_beats.py`, `src/dataset.py` (`available_records`), `src/features_rr.py` (`assemble_rhythm_features`), `config.py` (`PACED_EXCLUDED`, `JITTER_MODEL`, `JITTER_COPIES`, `DATASETS`), `tests/test_prep_beats.py`
> **Prerequisite:** [`features-rr-walkthrough.md`](features-rr-walkthrough.md)

A study document, not a specification. The counterpart of
[`features-rr-walkthrough.md`](features-rr-walkthrough.md): where that document
covers **the formulas**, this one covers **who runs those formulas
over 44 records and keeps everything aligned**.

Reproduction:

```
cd model
make prep       # 44 record mitdb (+ svdb/incartdb bila sudah diunduh) → data/processed/per_record/*.npz
```

---

## 0. Why this file exists, and why it lives in `scripts/`, not `src/`

`src/` holds pure functions: an array goes in, an array comes out. None of
them knows that MIT-BIH has 48 records, that 4 of them are dropped,
or that the result is stored as `.npz`. All of that is **policy**, and
policy lives here.

```
        src/ (murni, padanannya di C)          scripts/ (eksekusi)
   ┌────────────────────────────────┐    ┌──────────────────────────┐
   │ load_record()                  │    │                          │
   │ apply_bandpass()               │◄───┤   prep_beats.py          │
   │ segment_beats()                │    │   - record mana dipakai  │
   │ zscore_per_window()            │    │   - beat mana dibuang    │
   │ assemble_rhythm_features()            │    │   - tulis .npz, cetak    │
   │ to_aami_class/to_binary_label()│    │                          │
   └────────────────────────────────┘    └──────────────────────────┘
```

This separation is not about tidiness. Functions in `src/` have C counterparts in the ESP32
firmware; if `np.savez` and `print` were nested inside them, porting would turn into
a teardown and reassembly. Conversely, with all the beat-dropping policy
gathered in one function here, the question of which beats are used has
**one** answer that can be read in 4 lines.

`prep_beats.py` is also the only place where the Phase 1 filter is run over all
records; the plot scripts only call `preprocessing.py` for a single record.

---

## 1. `valid_beat_indices()`: the single source of truth for alignment

```python
r = np.asarray(r_locations)
i = np.arange(len(r))
fits = (r - WIN_PRE >= 0) & (r + WIN_POST <= signal_len)
ok = fits & (i >= 2)
if USE_RR_RATIO:
    ok &= i < len(r) - 1
return i[ok]
```

Three conditions, an **intersection** (`&`), not a union:

| Condition | Origin | Reason |
|---|---|---|
| `r - 128 >= 0` and `r + 128 <= N` | Phase 1 | the 256-sample window must fit in the signal |
| `i >= 1` | Phase 2 | needs `r[i-1]` for RR_prev |
| `i >= 2` | Phase 2 | needs the previous beat's RR_prev for dRR |

The last two conditions are condensed into `i >= 2`: beat 2 automatically has both.
The fourth condition (`i < len(r) - 1`) is only active when the ablation knob `PA_RR_RATIO=1` is set:
the ratio form needs the **next** beat's RR, so the last beat of each record
lacks complete features. In the locked configuration this knob is off.

What is returned is **beat indices**, not data arrays. That is the point: one list of
indices is used to slice `windows`, `rr`, `labels`, and `symbols` at once,
so the four can never drift apart from each other.

### Why not "just make the lengths equal"

This is the most expensive pitfall in the whole project, and its symptom is **nothing**:

```python
labels = labels[:len(windows)]     # ← assert panjang LOLOS, data rusak
```

`segment_beats` drops edge beats; `compute_rr_features` cannot fill
beats 0 & 1. Two **different** sets whose lengths can happen to be equal.
Simulation on record 100: 100% of rows shifted by one beat, 68 labels got the wrong
symbol, even though the real arrhythmias in that record are only 34 (each 1 arrhythmia corrupts 2
rows). The loss still decreases smoothly. It is only discovered in Phase 6 when recall is ~0, with no
clue whatsoever about the cause.

Align through **indices**, never through length.

---

## 2. `process_record()`: the order decides right from broken

```python
signal, r, sym, _ = load_record(record_id, db=db)
filtered = apply_bandpass(signal, sos)
if DATASETS[db]["selaraskan"]:
    r = align_r(r, filtered)
if jitter is not None:
    r = jitter(r)

idx = valid_beat_indices(len(signal), r)
windows = zscore_per_window(segment_beats(filtered, r[idx]))
rr = assemble_rhythm_features(r, windows, idx)
labels = np.array([to_binary_label(to_aami_class(sym[i])) for i in idx], dtype=np.int8)
symbols = np.array([sym[i] for i in idx], dtype="<U2")
```

The two steps before `idx` change the R position, not its label:

- **`align_r`** shifts the annotation to the true peak, only for databases
  whose annotation convention differs from mitdb (`DATASETS[db]["selaraskan"]`:
  svdb and incartdb `True`, mitdb `False` because mitdb is the golden reference baseline).
- **`jitter`** shifts the R position for the augmentation copies (§4). The shifted position
  is used for the window **and** the RR features, because a detector that misses damages
  both at once. The label is still taken from the original annotation symbol through `idx`.

`assemble_rhythm_features` calls `compute_rr_features(r)[idx]` in the locked
configuration (optional features are only added when their ablation knob is active). Note the
order of its arguments. Two forms that look equivalent:

```python
rr = compute_rr_features(r)[idx]     # ✓ BENAR — hitung dari r UTUH, baru potong
rr = compute_rr_features(r[idx])     # ✗ SALAH — potong dulu, baru hitung
```

The difference: the `RR_prev` of beat `idx[0]` needs the position of the **previous** beat, which has
already been dropped from `idx`. If `r` is sliced first, the first beat that passes
computes its interval from the wrong neighbor, and the result is still a plausible
number, with no error and no NaN.

Compare with the `windows` line: there `r[idx]` is actually **correct**, because
`segment_beats` cuts the signal around each R-peak independently, with no
need for neighbors. The rule: **a function that needs neighbor context is always given
the whole data; filtering happens afterwards.**

### Two asserts that guard the contract

```python
assert len(windows) == len(rr) == len(labels) == len(symbols) == len(idx)
assert not np.isnan(rr).any(), f"record {record_id}: NaN lolos ke rr"
```

The second is the second safety net. The NaN from beats 0 & 1 should already have been
filtered out by `idx`; if it gets through, it means `valid_beat_indices` and
`compute_rr_features` **disagree** about which beats are valid. It is caught in
`make prep`, which runs in a minute, not in Phase 5 as `loss = nan` with no trace.

---

## 3. Anatomy of the output

```python
{"windows": [K,256] float32,   # morfologi ter-z-score
 "rr":      [K,3]   float32,   # RR_prev, RR_ratio, dRR (N_RR_FEATURES kolom)
 "labels":  [K]     int8,      # 0 Normal / 1 Aritmia
 "symbols": [K]     <U2,       # simbol MIT-BIH asli
 "n_dropped":       int32}     # berapa beat dibuang
```

The last two fields are not used by the model, and that is exactly their purpose.

**`symbols`** stores information that is **permanently lost** once the label
is narrowed down to 0/1. In Phase 6 it is what makes possible the per-AAMI-class recall table
([`evaluate-walkthrough.md`](evaluate-walkthrough.md) §5), the most substantive
finding in Bab 4 (Chapter 4 of the report). If it is not saved at this stage, that information cannot be
reconstructed downstream.

**`n_dropped`** goes into the `.npz`, not merely `print`ed. The figure "of 100,624 beats,
109 were dropped because ..." is a table row in the report; if it is only printed, it
is lost when the terminal is closed.

---

## 4. `available_records()` and `main()`: the policy layer

`main()` calls `available_records(db)` in `src/dataset.py`:

```python
ids = sorted(f[:-4] for f in ada if f.endswith(".hea")
             and f"{f[:-4]}.dat" in ada and f"{f[:-4]}.atr" in ada)
if db == "mitdb":
    excluded = {str(x) for x in PACED_EXCLUDED}
    ids = [i for i in ids if i not in excluded]
```

The record list comes from the **folder contents**, not from a retyped list:
one fewer place for a typo. A record only counts if
`.hea`, `.dat`, and `.atr` are all present, so that an unfinished download fails
here, not as a `FileNotFoundError` in `wfdb.rdann`. `PACED_EXCLUDED`
is taken from `config.py`, the same list used by Phase 3. One source,
do not duplicate it.

`main()` processes each database in `DATASETS` that has been downloaded (those not yet downloaded are
skipped with the message `make data DB=<db>`), then for each record:

1. One clean copy is always processed.
2. For **DS1 mitdb** records only, `JITTER_COPIES` (2) jittered copies are added, using the
   `JITTER_MODEL` model (`"empiris"`). All copies are stacked into the same record `.npz`
   by `gabung()`.
3. DS2 and the extra databases are never jittered: DS2 is the benchmark, and the empirical
   residual was measured from the detector on mitdb at 360 Hz, so it does not apply
   to resampled signals.

Command-line options: `--jitter {none,empiris,seragam,normal}`, `--copies N`,
`--delta` (for `seragam`/`normal`), and `--db <nama...>`.

`main()` prints a per-record table and then the total. The printout is not decoration: the PRD
requires the label distribution to be printed per record as a DoD, and the imbalance
visible there is what justifies `class_weight` in Phase 5.

---

## 5. Real numbers, and what can be read from them

Clean mitdb data (`python scripts/prep_beats.py --jitter none --db mitdb`):

```
44 record  100.624 beat  Normal 90.023 (89,5%)  Aritmia 10.601 (10,5%)  buang 109
```

With the `make prep` defaults (DS1 ×3: one clean + two jittered), mitdb becomes
202,560 beats: DS1 152,904, DS2 49,656.

### Accounting for the 109 dropped beats (clean data)

```
sebaran per record: {3 beat: 21 record, 2 beat: 23 record}
109 = 44×2 (beat 0 & 1, deterministik) + 21 (beat tepi)
```

All 21 of those edge beats are at the **end** of the recording: the last R-peak falls after
sample 649,872, so the `+128` window does not fit in the 650,000 samples.

```
rec 103  r[-1] = 649.875  (butuh <= 649.872)  → dibuang, cuma lewat 3 sampel
rec 113  r[-1] = 649.994  (butuh <= 649.872)  → dibuang
rec 223  r[-1] = 649.849  (butuh <= 649.872)  → lolos
```

### The interesting part: early beats never add to the count

Some records have a first R-peak too close to the start of the signal:

```
rec 220  r[0] = 28   (butuh >= 128)
rec 208  r[0] = 46
rec 100  r[0] = 77
rec 112  r[0] = 124
```

Those beats **do** fail the window condition, but they were already dropped first
by the `i >= 2` condition. Because `valid_beat_indices` uses an **intersection**, a single beat
that fails two conditions is still counted once.

This is why the number can be as neat as 44×2 + 21. If other code were quietly
dropping beats too, accounting this simple would not match, so the figure
109 itself serves as proof that the beat-dropping policy is really
centralized in one place.

### The class distribution per record is extreme

```
rec 212 → 0,0% aritmia        rec 232 → 77,7% aritmia
rec 230 → 0,0%                rec 208 → 46,3%
```

The global imbalance of 10.5% hides the fact that each patient is a different
distribution. This is a direct justification for the Phase 3 decision (split
per patient), and the explanation of why the DS2 metrics are dominated by one or two patients.

---

## 6. What is deliberately NOT done

**Does not merge into one big file.** The output remains one `.npz` per record.
Phase 3 splits by patient, so as long as the data is still per record, the split is just
a matter of choosing files. See [dataset-walkthrough](dataset-walkthrough.md) §0.

**Does not shuffle anything.** The order of beats follows the time order in the recording
(jittered copies are stacked after the clean copy).
Shuffling is a training matter, in memory, per epoch.

**Does not skip records that fail to read.** `load_record` raises `ValueError`
for a record without MLII, and that record is already in `PACED_EXCLUDED`,
so it never gets here. If it did, the program stops,
rather than producing a dataset that is quietly smaller.

---

## 7. Comprehension check

1. The `rr` line is changed to `compute_rr_features(r[idx])`. How many rows have
   wrong values, and why does the `assert len(...)` test still pass?
2. `valid_beat_indices` is changed from an intersection (`&`) to a union (`|`). How many beats
   pass in record 100, and what happens when `compute_rr_features`
   is sliced with those indices?
3. Record 103 has `r[-1] = 649.875`, only 3 samples past the limit. If
   `WIN_POST` is lowered from 128 → 120, how many beats in total are saved across the 44
   records, and what part of the waveform is lost from the window?
4. `symbols` is not saved into the `.npz`. Which table in Bab 4 (Chapter 4 of the report) becomes impossible
   to make, and why can it not be reconstructed from `labels`?

## 8. Supporting scripts

| Command | Looks at |
|---|---|
| `make prep` | Run the 44 records + the label distribution table per record |
| `make plot1seg REC=n` | Window from segmentation + z-score, visual verification |
| `make test` | The whole test suite; `tests/test_prep_beats.py` locks the alignment contract |

---

**[← Phase 2: features_rr](features-rr-walkthrough.md)**  ·  [Walkthrough map](README.md)  ·  **[Phase 3: dataset →](dataset-walkthrough.md)**
