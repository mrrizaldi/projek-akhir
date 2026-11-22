# Body-signal recordings

Destination folder of `make pull` (`scripts/pull_recording.py`): every recording
pulled from the board is stored here as `<tanggal-jam-tarik>.csv`, or
`<tanggal-jam-tarik>-rekam-NNN.csv` when pulled by number (`make pull N=<n>`).

**The official report data = the midday session of 22 Oct 2026** (the rows marked in Notes per session).
The other rows are development recordings (warm-up duration measurement, Lead I,
contact events) and are **not used as result data**. The other trial recordings
of 10 Sep to 21 Oct 2026 are archived in
[`../arsip/rekaman-uji-coba/`](../arsip/rekaman-uji-coba/README.md).

Procedure for recording, pulling, and analyzing: [`../../docs/acquisition-walkthrough.md`](../../docs/acquisition-walkthrough.md).
The analysis results (`make analyze FILE=data/recordings/<nama>.csv`) fill the
`PLACEHOLDER-DATA` markers in `laporan/buku-pa/` (`grep -rn PLACEHOLDER-DATA laporan/buku-pa`).

## Notes per session

| Session | Files | Notes |
|---|---|---|
| 15 Oct 2026 | `20261015-1727-rekam-003`, `-004` | two separate sessions; 004 contains motion artifacts and clipping |
| 21 Oct 2026 | `20261021-1549-rekam-001` … `20261021-1550-rekam-006` | one 1,658 second session. **Lead I** (yellow on the upper left chest following the SparkFun guide), not MLII; used to measure the warm-up duration of the calibration gate, not for classification results. Recorded with firmware that wrote files to flash in the middle of the session, so the first ±4.7 seconds of files 002 to 006 lost samples without being recorded (header `lewat=0`; RR compressed ±40%). Drop the first 5 seconds of files 002 to 006 when computing RR. R peaks touched the upper rail 4095 on 71% of beats (clipping on 0.62% of samples) |
| 22 Oct 2026 | `20261022-1219-rekam-002` … `20261022-1220-rekam-005` | one 903 second session, MLII (yellow below the left rib), power bank, new electrodes, 2nd repeat of the calibration gate warm-up duration. No lost samples (`lewat=0`). 50 Hz hum 13 to 28 in the first 30 seconds, then rising in steps up to ±1,100 (35 to 130 seconds) and settling at 190 to 360; electrode off (LO) 14% / 0% / 41% / 62% per file; a jolt at 810 to 840 seconds (reported by the subject at minute 13) with clipping. File 003 (5 to 10 minutes) is the cleanest: hum 3.3%, noise 4.7%, clipping 0 |
| 22 Oct 2026 (±12.38 to 12.54 WIB) | `20261022-1256-rekam-001`, `-002`, `20261022-1257-rekam-003`, `-004` | **Official report data** (user decision 22 Oct 2026, buku-pa "Tabel kualitas rekaman R1–R4"). One 927.1 second session without a pause, MLII, power bank, new electrodes, subject S01 = the author, Laboratorium MSECT PENS. 3rd repeat of the calibration gate warm-up duration. `lewat=0`, LO 0%, all four Berhasil (successful) (hum 1.9 to 3.8%, autocorrelation 0.28 to 0.38, plausible BPM 100%), saturated 1/5/9/1 samples (≤ 0.010%) |
