# Walkthrough `src/io_mitdb.py`: Phase 0

> **Scope:** loading one beat-annotated PhysioNet record into a single-channel signal, R-peak positions, and beat symbols.
> **Related code:** `src/io_mitdb.py`, `config.py` (`CHANNEL`, `BEAT_SYMBOLS`, `DATASETS`), `scripts/plot_phase0.py`, `tests/test_io_mitdb.py`
> **Prerequisite:** none

A study document, not a specification. The official specification remains
`PRD_Model_Aritmia_TinyML.pdf` pp. 5–6. This phase is the earliest, and its mistakes are
the most expensive: every phase after it uses its output as is.

Reproduction:

```
cd model
make data                 # once: download MIT-BIH
make check                # .hea/.dat/.atr completeness
make plot0 REC=114        # annotated R-peak overlay
```

---

## 0. The contract in one line

```python
signal, r_locations, symbols, fs = load_record("100")
```

| Output | Shape | Content |
|---|---|---|
| `signal` | `[N] float32` | the MLII channel signal, in mV |
| `r_locations` | `[M] int64` | sample indices of the R peaks (cardiologist annotation) |
| `symbols` | `list[str]`, len M | the MIT-BIH symbol per beat |
| `fs` | `int` | sampling rate, guaranteed 360 |

Record 100: `signal` 650,000 samples (30 minutes × 360 Hz), 2,273 beats.

This module is **pure**: no `print`, no plot, no top-level code. That is what
lets it be `import`ed in pytest without loading a 30-minute record along with it.

---

## 1. Anatomy of one MIT-BIH record

Each record is three files with the same name:

| File | Content |
|---|---|
| `100.hea` | text header: channel names, fs, sample count, gain |
| `100.dat` | binary two-channel signal |
| `100.atr` | cardiologist annotation: sample position + symbol per beat |

```python
record = wfdb.rdrecord(path)        # .hea + .dat
annotation = wfdb.rdann(path, "atr")  # .atr
```

The annotation is the most valuable asset of MIT-BIH: two independent cardiologists
marked **every** beat across 30 minutes × 48 recordings. That is why this 1980s dataset
is still the standard for evaluating arrhythmia classification.

---

## 2. Two gates that fail loudly

```python
spec = DATASETS[db]
if record.fs != spec["fs"]:
    raise ValueError(
        f"record {record_id} ({db}): fs={record.fs}, DATASETS promises {spec['fs']}"
    )
channel = select_lead(record_id, record.sig_name, spec["leads"])   # raises if none match
```

For mitdb (`db="mitdb"`, the default), `DATASETS["mitdb"]` promises `fs = 360`
and the lead `("MLII",)`. Other databases (svdb, incartdb) use the same gate
with their own promises, and are then resampled to 360 Hz by `resample_to_fs`.
The `fs` check is done **before** the resample, so that the resample does not mask
a corrupt record or a wrong `config.py` table.

**Why `raise`, not `continue` or a silent resample.** If a single record
with a different `fs` gets through, all its RR features are wrongly scaled (divided by 360 when
it should be something else) and there is not a single sign downstream. A loud failure
at the start is far cheaper than a silently wrong number in Phase 6.

What this gate actually catches:

```
102 → ValueError: record 102: tidak ada kanal ['MLII'], hanya ['V5', 'V2']
104 → ValueError: record 104: tidak ada kanal ['MLII'], hanya ['V5', 'V2']
```

Those two records really do not have MLII. They are also in
`config.PACED_EXCLUDED`, so there are two reasons: **technical** (no channel) and
**methodological** (pacemaker patients).

---

## 3. The channel order trap: record 114

```python
def select_lead(record_id, sig_name, leads):
    for lead in leads:
        if lead in sig_name:
            return sig_name.index(lead)
    raise ValueError(...)

channel = select_lead(record_id, record.sig_name, spec["leads"])
signal = record.p_signal[:, channel].astype(np.float32)
```

It looks trivial, and this is exactly where the trap is. Almost all MIT-BIH records
put MLII in column 0:

```
record 100 → sig_name = ['MLII', 'V5']    → MLII at index 0
record 114 → sig_name = ['V5', 'MLII']    → MLII at index 1  ←
```

`p_signal[:, 0]` will work smoothly for 45 records and **silently take the wrong
channel** for 114. The V5 signal still looks like a normal ECG in the
plot; only the QRS morphology changes, which is exactly what the model learns.

That is why the channel is looked up **by name**, never by a fixed index, and
`select_lead` rejects (rather than falling back to channel 0) if the requested name does not exist.
Its verification: `make plot0 REC=114`: the annotated R-peak lines must land exactly
on the R peaks, plus a mechanical assert compares the `load_record` result with
`p_signal[:, 1]`.

---

## 4. Filtering non-beats, and why `is_qrs` must not be used

The `.atr` file does not only contain beats. It also has event markers:

```python
symbols = np.asarray(annotation.symbol)
is_beat = np.isin(symbols, list(BEAT_SYMBOLS))
```

What is actually discarded:

| Record | Raw annotations | Discarded | Beats remaining |
|---|---|---|---|
| 100 | 2,274 | `+`×1 | 2,273 → `{N: 2239, A: 33, V: 1}` |
| 114 | 1,890 | `+`×3, `~`×7, `\|`×1 | 1,879 → `{N: 1820, V: 43, A: 10, F: 4, J: 2}` |

The meaning of the symbols: `+` rhythm change, `~` signal quality change, `|` an isolated
QRS-like artifact. All are **events**, not beats: if they were included, they would become
"beats" with no QRS in the middle of the window.

### TRAP (JEBAKAN): `wfdb.io.annotation.is_qrs`

The way that looks most natural is to use wfdb's built-in table:

```python
is_beat = [wfdb.io.annotation.is_qrs[s] for s in symbols]   # ← DO NOT
```

The symptom: `[`, `]`, `x`, `)` get through as "beats". The cause is that the wfdb table marks
the **start/end of ventricular flutter** markers and **non-conducted P-waves** as
QRS: correct in signal terminology, wrong for our purposes.

The solution is an **explicit whitelist**, not a blacklist:

```python
BEAT_SYMBOLS = {"N","L","R","e","j", "A","a","J","S", "V","E", "F", "/","f","Q"}
```

15 symbols, exactly those that have an AAMI class. The difference between a whitelist and a blacklist here
is decisive: with a blacklist, a symbol you did not anticipate **gets through**; with a
whitelist, an unknown symbol **gets dropped along with the rest**. For medical data, failing in the direction of
dropping is far safer.

This is also what lets `AAMI_MAP[symbol]` in Phase 2 raise `KeyError`:
anything that reaches there is guaranteed to be in the whitelist already, so a `KeyError`
means something leaked upstream.

---

## 5. Why MLII, and why `float32`

**MLII** (modified limb lead II) is the lead with the most prominent QRS complex
in the majority of people, since the cardiac axis is roughly parallel to it. In practice:
46 of the 48 MIT-BIH records have MLII, and a single-lead sensing device such as the AD8232
in this project also places its electrodes at a position close to lead II. So
choosing MLII is not only about data availability: it preserves the **similarity between
training data and the signal that actually enters the ESP32 at deploy time**.

`astype(np.float32)`: the wfdb default `p_signal` is float64. Half the memory, and the same
as the model's float32 input precision before quantization. 650,000 samples × 48
records: 250 MB vs 125 MB.

---

## 6. Reference numbers

```
48 record lengkap (.hea + .dat + .atr)      → make check
record 100: 650.000 sampel, 2.273 beat, fs 360, kanal ['MLII', 'V5']
record 114: 650.000 sampel, 1.879 beat, fs 360, kanal ['V5', 'MLII']  ← MLII index 1
record 102 & 104: ValueError (tanpa MLII)
```

---

## 7. Comprehension check

1. `channel = 0` is hardcoded. Which record breaks, and why would that bug **not**
   be visible in the signal plot or in the training loss?
2. The `BEAT_SYMBOLS` whitelist is replaced with the blacklist `{"+", "~", "|"}`. Which symbols
   get through, and what is the consequence for the segmented windows?
3. A mismatched `fs` is silently resampled instead of being `raise`d. Which feature
   breaks, and in which phase would you only notice it?
4. Why does this function return the raw `symbols` rather than a binary
   label directly? (Hint: see the use of `symbols` in Phase 6.)

## 8. Supporting scripts

| Command | What it shows |
|---|---|
| `make data` | Download the 48 MIT-BIH records (once) |
| `make check` | Completeness of `.hea`/`.dat`/`.atr` for each record |
| `make plot0 REC=n` | Overlay of annotated R-peaks on the signal: verify the channel is correct |

---

**-**  ·  [Walkthrough map](README.md)  ·  **[Phase 1: preprocessing →](preprocessing-walkthrough.md)**
