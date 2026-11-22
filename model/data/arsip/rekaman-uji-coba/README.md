# Archive of trial recordings (10 September to 21 October 2026)

31 AD8232 recordings taken during development and kept outside the official
data (midday session of 22 Oct 2026). Archived so they are not mixed up with
the recordings in [`../../recordings/`](../../recordings/README.md).

**For development only (circuit diagnosis, analysis script tests), not result
data.** Do not cite them as results in the report.

| Date | Files | Circuit and supply | Notes |
|---|---|---|---|
| 10 Sep 2026 | 6 (`20260910-*`) | breadboard, AD8232 OUTPUT to GPIO 4; supply from laptop USB, then power bank | laptop vs power bank supply trial and electrode re-attachment |
| 14 Sep 2026 | 8 (`20260914-*`) | breadboard, OUTPUT moved from GPIO 4 to GPIO 8 that day (the GPIO 4 trace was broken); power bank | circuit still changing |
| 15 Sep 2026 | 11 (`20260915-*`) | breadboard, GPIO 8, older main firmware; power bank | mostly failed (noise floor, suspected unsoldered AD8232 module header) |
| 11 Oct 2026 | 2 (`20261011-*`) | test circuit with the PCB pin map, OUTPUT to GPIO 1; older hardware test firmware | 1 recording fully lead-off, 1 recording with signal |
| 14 Oct 2026 | 1 (`20261014-2014-rekam-001`) | test circuit with the PCB pin map, battery supply, WiFi OFF; firmware with a 300 s recording limit that silently discarded samples after it | recorded for about 45 minutes, first 300 s stored; good signal (autocorrelation 0.36 median per 30 s, 97% plausible RR), muscle noise at 29 to 31 s and 106 to 111 s. Not counted as official data because it was taken before the continued-recording firmware fix (15 Oct 2026) |
| 14 to 15 Oct 2026 (recording time not noted) | 1 (`20261021-1425-rekam-002`) | test circuit with the PCB pin map | board #2 file left behind in LittleFS and only pulled on 21 Oct 2026; 1,909 samples (5.3 s), too short to analyze |
| 21 Oct 2026 | 2 (`20261021-1712-rekam-001`, `-002`) | test circuit with the PCB pin map, laptop USB plugged in, yellow electrode on the upper left chest | test of the recorder fix (session buffered in PSRAM, written after stopping): one 342.6 s session, continuous RR past second 300 (0 RR < 0.5 s out of 418), header `lewat=0` |

Shared conditions: one subject, Lead II (except 21 Oct 2026: yellow on the upper left chest, Lead I), wet-gel electrodes, firmware that has since been
replaced (same CSV format: header `# fs=360 n=... lewat=... [lepas=...]`).
File name = **pull** time, not recording time.

The analysis plots are in `model/artifacts/arsip/akuisisi-uji-coba/`.
Circuit diagnosis (noise floor, broken trace, lead-off): table §7 "When there is a problem"
in [`model/docs/acquisition-walkthrough.md`](../../../docs/acquisition-walkthrough.md).
Re-analyzing (the plot results go into `artifacts/metrics/akuisisi/`):

```
cd model
make analyze FILE=data/arsip/rekaman-uji-coba/20260915-1130.csv
```
