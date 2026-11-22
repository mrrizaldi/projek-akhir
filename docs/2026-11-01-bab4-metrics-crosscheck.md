# Crosscheck of Chapter 4 metrics against standards and literature (1 Nov 2026)

**Status:** active, waiting for the user's decision (section 4). Actions taken from here are recorded in
[`2026-11-01-target-gaps.md`](2026-11-01-target-gaps.md) or related documents.
**Question:** do the metrics and measurement methods in `laporan/buku-pa/bab/bab4.tex`
(`tab:parameter-eksperimen`) conform to established standards and paper practice, judged from the
methods in the full text, not from the abstract.
**Method:** five parallel research runs, one per metric category, using Scopus, WebSearch, and
full-text downloads. The detailed report per category, containing the crosscheck table, the list of
sources with exact quotes and pages, and the top five gaps, is in the folder
[`2026-11-01-bab4-metrics-crosscheck/`](2026-11-01-bab4-metrics-crosscheck/).
The downloaded PDFs and texts (gitignored) are in
`laporan/pustaka/belum-dirujuk/riset-pengukuran/{klasifikasi,tinyml,akuisisi,pipeline,daya}/`.
Sources whose key already exists in `referensi.bib` are stored in `laporan/pustaka/<kunci>.pdf`.
The index of quotes and cited pages for the `progres-pa-1` measurements, with links to the local PDF
right at the quoted page, is in `laporan/pustaka/indeks-rujukan-pengukuran.html` (opened
in a browser from that folder). The index is HTML because the Chrome PDF viewer does not
follow `file://` links from inside a PDF.

| Chapter 4 category | Detailed report | Full-text sources |
|---|---|---|
| a, b. Classification and quantization | [klasifikasi.md](2026-11-01-bab4-metrics-crosscheck/klasifikasi.md) | 16 |
| c, d. On-device performance and preprocessing | [tinyml.md](2026-11-01-bab4-metrics-crosscheck/tinyml.md) | 19 |
| e. Body signal acquisition | [akuisisi.md](2026-11-01-bab4-metrics-crosscheck/akuisisi.md) | 18 |
| f. Edge-to-cloud pipeline | [pipeline.md](2026-11-01-bab4-metrics-crosscheck/pipeline.md) | 18 |
| g. Power consumption (planned) | [daya.md](2026-11-01-bab4-metrics-crosscheck/daya.md) | 15 |

The paywalled standard texts could not be read: ANSI/AAMI EC57 and EC13, IEC 60601-2-25,
-2-27, -2-47, and -1-11, and Kligfield 2007. Their content is quoted through a reference
implementation (PhysioNet `bxb`/`sumstats` for EC57) or secondary quotes, and
is marked in the detailed reports.

## 1. Verdict per category

| Category | Conforms to standard/literature | Different, but defensible | Lacking |
|---|---|---|---|
| a. Classification | de Chazal inter-patient split, pacemaker recordings dropped, Q dropped, gross statistics, accuracy not a reference, threshold from VAL per patient, system recall with ±150 ms matching (`tab:segmentasi-deteksi`) | Binary class (EC57 only knows VEB and SVEB), first 5 minutes not dropped (inter-patient paper convention), per-patient median (EC57 "average" = mean per recording) | PR-AUC and MCC not yet reported; QRS detector +P not written; mean per recording not yet reported |
| b. Quantization | Δ threshold relative to float32 is in line with MLPerf Inference ("within 1% of FP32") | 0.02 is the author's own design threshold; Zambrano 2026 uses accuracy with a per-beat split (the authors admit leakage) | Δ per class S/V/F and the percentage of changed labels are not reported; Busia 2024 shows the INT8 impact is concentrated in class S |
| c. On-device performance | Model size, `arena_used_bytes` (the TFLM way), 200 ms comparison stricter than the literature (Tran 2025: 400 ms) | RAM/Flash from the build report, not runtime peak | Latency from 7 inferences without repeats (MLPerf Tiny: ≥ 10 s and ≥ 10 iterations, 5 runs, median); max not reported although the code already prints it |
| d. Real-time preprocessing | C–Python equivalence stricter than all ECG papers read; the criterion "queue < capacity" matches Liu & Layland (assumption A2, buffering) | The 82 µs figure is an aggregate utilization (busy time / number of samples) | The 33.4 ms peak out of 6.67 s is the *maximal observed*, not the WCET (Wilhelm 2008); not yet measured with WiFi active and at window 256 |
| e. Acquisition | 0.5–40 Hz band (CinC 2017 AliveCor, BITalino), 50 Hz hum definition identical to PLIratio Gajdzik 2026, saturated-sample check, RR range 30–200 BPM | The 15% and 90% thresholds are self-made (Rahman 2022: there is no standard SQI threshold); a causal non-linear-phase filter is valid for rhythm, not ST | R-peak/HR not validated against a reference (EC13: ±10% or ±5 bpm); autocorrelation > 0.25 without a reference; assessment per recording, not per 10 s window; dynamic range ±1.3–1.5 mV against the ±5 mV of IEC 60601-2-25 |
| f. Pipeline | PDSR = round-trip loss RFC 6673 §4.3 with Tmax 5 s; clock offset correction more explicit than Adochiei 2025, Kim 2026, Silva 2021; the 2 s target is in line with ITU-T G.1010 (Responsive ~2 s, Table I.2 preferred < 2 s, acceptable < 4 s) | Median as the main statistic (RFC 6703 §5.2) | Mean, SD, min, max not yet reported (RFC 6703 §3.1); clock uncertainty not reported (RFC 7679 §3.7, RFC 7680 §2.8.3 MUST); the disconnection test = `docker pause` once, the WiFi reconnect path is untested |
| g. Power | Per-mode mean from the INA219 is valid, because the ΔΣ ADC integrates rather than sampling a point (datasheet p. 11) | The battery side includes converter efficiency (MLPerf measures one fixed rail) | Config `0x3FFF` samples the current about 50% of the time; no calibration; one ladder run without repeats; energy per inference and battery life not yet planned |

## 2. Already closed in the book

Four items from the detailed reports are already handled by Chapter 4 and need no action:

1. **End-to-end classification with the detector** (klasifikasi.md gap 1).
   `tab:segmentasi-deteksi` reports a system recall of 0.6035 with R from
   Pan-Tompkins and ±150 ms matching (`model/scripts/eval_detected_segmentation.py`,
   `src/evaluate.pair_detected`).
2. **DS2 used for ablation** (klasifikasi.md gap 2). Chapter 4 writes it
   as a limitation in the dataset paragraph and the per-patient recall paragraph.
3. **Zhong 2022 as an end-to-end latency comparison** (pipeline.md item 8).
   Chapter 3 cites Zhong only for BER, and the latency budget refers to
   Skorin-Kapov 2010.
4. **QoS 1 duplicates** (pipeline.md item 12). Chapter 4 already states that zero
   duplicate ts does not mean duplicates never arrive, and the mechanism is tested
   with a republish smoke test.

The detector +P can already be computed from the Chapter 4 numbers: 47,074 / (47,074 + 2,194) =
0.9555.

## 3. Actions, grouped by cost

### A. Only needs writing (no re-measurement)

| # | Action | Basis |
|---|---|---|
| A1 | Latency definition made uniform: from R-peak (ts) until the row is available in the REST API, dashboard rendering not included; the median justified with RFC 6703 §5.2 | Chapter 3 `tab:pengujian-pipeline` writes "pembaruan dashboard" (dashboard update) and "rata-rata" (average) (same as target-gaps B4) |
| A2 | PDSR written as first-attempt round-trip success (RFC 6673), Tmax 5 s, with the Clopper–Pearson CI: pooled 733/735 = 99.02–99.97%, lowest repeat 97.20% | Recomputed with `scipy.stats.beta`: 292/292 98.74–100, 253/255 97.20–99.90, 188/188 98.06–100 |
| A3 | The 2 s budget reference extended with ITU-T G.1010 Figure 2 and Table I.2, and ITU-T H.810 §6.1.7.5 (measured parameters ~1 s, alarm ~10 s) | pipeline.md item 8 |
| A4 | Detector QRS +P 0.9555 added to `tab:sensitivity-detektor`, with the 150 ms window mentioned | EC57 asks for QRS Se and +P (`bxb -w 0.15`) |
| A5 | One protocol sentence: the whole recording is used (not the EC57 5-minute learning period), Q dropped 7 beats (Mondéjar 2019), binary metric rather than EC57 VEB/SVEB | klasifikasi.md items 1, 4, 5 |
| A6 | The Δrecall threshold 0.02 written as a design threshold; Zambrano used only as an example of magnitude | klasifikasi.md item 15 |
| A7 | Acquisition scope limits: 0.5–40 Hz band for rhythm, not ST; ΔRR gate only in the calibration phase; dynamic range ±1.3–1.5 mV as a design limitation that explains saturated samples at the R peak | akuisisi.md items 1, 2, 8 |
| A8 | If R-peak/HR validation is not done: the acquisition result is written as functional status, not accuracy (precedent Torad 2026 §4) | akuisisi.md gap 1 |
| A9 | Inference latency: the max figure from 7 beats (already printed by `test_inference`) is quoted, and the 9 `Invoke()` calls before measurement are described as warm-up | tinyml.md section 0 |
| A10 | The disconnection test written as a broker failure, not a link failure, if the WiFi disconnection test is not done | pipeline.md item 11 (same as target-gaps B1) |

### B. Recompute from existing data

| # | Action | Data |
|---|---|---|
| B1 | PR-AUC (prevalence line 0.11) and MCC at threshold 0.80 on DS2 | `model/data/processed/test.npz` + float32 model |
| B2 | Mean recall per recording (the EC57 "average" statistic) next to the median | `model/artifacts/metrics/fase6_per_record_fp32.csv` |
| B3 | Δ float32 vs INT8 per class S/V/F and the percentage of beats whose label changes | Existing INT8 evaluation of DS2 |
| B4 | Pipeline latency: mean ± SD, min, max; median and p95 per 1-minute interval (ITU-T Y.1541); p95 with rank ⌈0.95n⌉ (RFC 2330 §11.3), not `int(0.95*(n-1))` in `dashboard/ukur_pipeline.py:112` | Logs of repeats 1–3, if the per-beat samples were saved |
| B5 | Recording quality per 10 s window with the three Orphanidou rules (HR 40–180, RR gap ≤ 3 s, max/min RR ratio < 2.2) and template correlation (threshold 0.66), reported as the percentage of windows that pass | The four official recordings of 22 Oct 2026 |
| B6 | Semi-automatic manual R-peak annotation over 927 s (correcting the Pan-Tompkins output), then Se and +P with 150 ms tolerance | The same recordings; manual work by the user |

### C. Re-measure on the board

| # | Action | Notes |
|---|---|---|
| C1 | Inference latency: 5 runs × 1,000 `Invoke()`, first 10 dropped; report median, p99, max; repeated with WiFi+MQTT active (A/B) | Closes target-gaps A4; the literature has no such A/B data yet |
| C2 | Preprocessing load ≥ 30 minutes with the body signal and WiFi active, window 256: histogram per call, queue high-water mark, lost samples | Closes target-gaps B8 |
| C3 | `ESP.getMinFreeHeap()` and `uxTaskGetStackHighWaterMark()` after a long run | Runtime peak RAM |
| C4 | INT8 equivalence on the board over hundreds of DS2 windows including class S; kernel test (identical int8 input) separated from the chain test | Same as target-gaps B7 |
| C5 | A real WiFi disconnection test (AP switched off), ≥ 3 repeats, graded durations; lost data counted against the beats produced | Same as target-gaps B1 |
| C6 | Intrinsic noise: AD8232 input shorted for 10 s; IEC 60601-2-25 limit 30 µV p-p ≈ 44 counts, 15 µV RMS ≈ 22 counts | Bench test without extra equipment |
| C7 | Optional: simultaneous recording with a Polar H10, Bland-Altman HR and the percentage of windows within ±5 bpm/±10% (EC13) | Needs equipment |

### D. Change the firmware before power is measured

| # | Action | Basis |
|---|---|---|
| D1 | `INA219_CONFIG` `0x3FFF` → `0x39FF` (bus 532 µs, shunt 128 samples), read only when CNVR = 1 and then clear through the Power Register; current coverage ±50% → 99.2%, no double reads. Rerun `test_ina219` and `test_hw_ina219` | `firmware/include/ina219.h:15`; INA219 datasheet p. 9–10, Table 5 p. 20, p. 23. Mode 111 converts shunt then bus alternately, 68.10 ms each |
| D2 | Calibration: zero offset 60 s with no load, then gain with 3 power resistor loads against a DMM, linear regression | Prasetyawati 2023; Espressif forbids a series DMM on the ESP32 (burden voltage) |
| D3 | Ladder ≥ 5 times from a 3.7 V bench supply at the cell position, mW as the main metric, report median and range | MLPerf Tiny median of 5 runs; Moura 2026 |
| D4 | Extra metrics: energy per inference ≈ (P_p3 − P_p2) × T / N_beat; operating time from a drain-the-battery test in `p5` | MLPerf Tiny µJ/inference; battery derating not found sourced |
| D5 | The "+30 mA" figure for `setSleep(false)` removed from the plan and measured | Unsourced; ESP32-S3 datasheet Tables 5-7 and 5-9 imply a larger difference |

## 4. User decisions

Work focus: the stage 1 book `progres-pa-1` first (user decision 1 Nov 2026).
Items outside the scope of the stage 1 book (pipeline, power) are deferred.

| # | Question | Decision |
|---|---|---|
| 1 | Item A entered into the book | `progres-pa-1`: A4, A5, A6, A7, A8 applied (1 Nov 2026). B1–B3 and B5 already computed (1 Nov 2026, `model/scripts/extra_metrics.py` and `window_quality.py`; figures in `model/docs/evaluate-walkthrough.md` §3b, `quantize-walkthrough.md` §6, `acquisition-walkthrough.md` §6) and entered into `progres-pa-1` Chapter 4 except PR-AUC: MCC, mean recall per recording, INT8 Δ per class, SQI per window (references `syversen_2024`, `richardson_2024`, `chicco_2020`). PR-AUC is not reported in the book because Richardson et al. 2024 show that ROC-AUC withstands class imbalance whereas PR-AUC does not. A9 needs the max latency figure from the board. `buku-pa` has not been edited and follows when the full book is worked on |
| 2 | p95 latency target (option ITU-T G.1010 "acceptable < 4 s", worst p95 3,304 ms) | Deferred, outside the stage 1 book |
| 3 | D1, INA219 config `0x39FF` + CNVR before the power ladder | Deferred, outside the stage 1 book |
| 4 | R-peak/HR validation | A8: the acquisition result is written as functional status, not accuracy, because there is no reference medical device yet. B6 and C7 are not done. The writing is done later together with the other A items |

### Follow-up decisions (1 Nov 2026, evening)

User rule: parameters and thresholds in the report are taken from the **standard first, then a
journal or book**; those without a reference are removed. Applied in
`progres-pa-1` (commit `d0ffc38` and after):

| Item | Before | After | Reference |
|---|---|---|---|
| Quantization threshold | \|Δrecall\| < 0.02 | INT8 F1 ≥ 99% of float32 F1; ratio of all metrics reported, precision 98.93% | `reddi_2020` |
| Model size | < 25 KB | Fits in the ESP32-S3 *flash* (0.36% of the app partition); arena 7.5% of the 320 KB RAM. Not compared with models on other devices because the architectures differ (user decision) | `espressif_esp32s3_wroom1`, `espressif_esp32s3_datasheet` |
| Latency, per-sample load, memory | target without citation | same target, given a citation | `tran_2025`, `busia_2025`, `david_2021` |
| Offline acquisition | hum < 15%, autocorrelation > 0.25, plausible BPM > 90%, saturation 0.1%, status Berhasil (successful) | SQI per 10 s window; hum and saturation reported without a threshold | `syversen_2024`, `gajdzik_2026` |
| Calibration gate | row in the parameter table | leaves the table; stays a Chapter 3 design and a Chapter 4 functional test | n/a |
| C vs Python equivalence test | functional test | **dropped entirely** (result item, per-stage table, achievement, Chapter 5 finding, abstract, Chapter 3 plan) | n/a |
| PR-AUC | proposed addition | not reported; ROC-AUC defended with Richardson 2024 | `richardson_2024` |
| Pipeline (category f) | n/a | deferred | n/a |

Consequence of dropping the equivalence test: the DS2 figures (measured on a computer) no longer
have written evidence in the book that the on-device model behaves the same.
The `MEAN` op bug (`model/CLAUDE.md` pitfalls) remains recorded in the repo.

## 5. Candidate references for `referensi.bib`

Not yet added. Keys, DOIs, and quotes are in the detailed reports. The most
useful for item A: `ietf_rfc6703`, `ietf_rfc7679`, `ietf_rfc6673`,
`itu_g1010`, `itu_h810` (pipeline); `banbury_2021` MLPerf Tiny (performance and
power); `luz_2016`, `mondejar_2019`, `saito_2015` (PDF already present), `chicco_2023`
(classification); `gajdzik_2026`, `orphanidou_2015` (PDF already present),
`clifford_2017`, `torad_2026` (acquisition); `ti_ina219`, `prasetyawati_2023`
(power). The DOIs of Reddi 2020, Wilhelm 2008, and Liu & Layland 1973 were checked in Scopus
(85092007781, 43949126892, 84974687699). The DOI of Scrugli 2022 has not been checked.

## 6. Process notes

- Two research runs sent the user's email address once to the Unpaywall API while looking for
  the open access version. Later research must not use the user's email for
  third-party services.
- Technical claims checked directly: the INA219 config (`firmware/include/ina219.h:15`),
  the p95 formula and the 50 ms sleep loop (`dashboard/ukur_pipeline.py:47,112`), the dynamic
  range ((4,095 − 1,900) × 0.757 / 1,100 = 1.51 mV; 1,900 × 0.757 / 1,100 =
  1.31 mV), the Clopper–Pearson CI, and the DOIs in section 5.
