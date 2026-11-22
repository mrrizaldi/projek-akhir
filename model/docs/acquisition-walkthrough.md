# Signal acquisition walkthrough: from electrode to plot

> **Scope:** the procedure for recording ECG from the body with the main firmware, pulling the recording to the laptop, and assessing its quality.
> **Related code:** `firmware/src/main.cpp`, `firmware/include/board.h`, `model/scripts/pull_recording.py`, `model/scripts/analyze_recording.py`, `model/Makefile` (targets `pull`, `analisis`)
> **Prerequisite:** [`firmware-walkthrough.md`](firmware-walkthrough.md)

A working guide, not a specification: recording from the body, pulling data,
assessing quality, making plots.

> **Data status.** The official report data = the 22 Oct 2026 afternoon session (R1–R4,
> `data/recordings/`, index in `data/recordings/README.md`). Other recordings in
> `data/recordings/` are development recordings, and the 10 Sep – 21 Oct 2026
> recordings that are not used are archived in
> [`data/arsip/rekaman-uji-coba/`](../data/arsip/rekaman-uji-coba/README.md)
> (their plots in `artifacts/arsip/akuisisi-uji-coba/`). All numbers in this document
> labelled *example from a trial recording (archive)* only illustrate the
> procedure, **not results**. The procedure itself applies.

---

## 0. One-screen flow

```
elektroda → AD8232 → ESP32-S3 (timer 360 Hz)
                          │
   tombol B3 (pendek: rekam/jeda/lanjut, tahan: simpan) → PSRAM → LittleFS  (/rekam/NNN.csv)
                          │
                     make pull                      ← colok USB ke laptop
                          ▼
              model/data/recordings/<tanggal-jam>.csv
                          │
                     make analyze FILE=...
                          ▼
     angka kualitas per segmen di terminal + grafik di artifacts/metrics/akuisisi/akuisisi_*.png
```

---

## 1. Wiring & placement

| Wire | GPIO | Electrode position |
|---|---|---|
| `OUTPUT` | **1** (ADC1_CH0) | - |
| `LO+` | 42 | - |
| `LO−` | 2 | - |
| B3 (record/pause/save) | 6 | - |
| **RA (red)** | - | below the right collarbone |
| **LA (yellow)** | - | below the left rib ← measures together with red |
| **RL (green)** | - | below the right rib (reference) |

The OUTPUT pin must be on **ADC1 (GPIO1–10)**; ADC2 (GPIO11–20) goes completely dead
as soon as WiFi is on. A broken OUTPUT line leaves the ADC pin floating and picking up
mains hum; the symptom is `dengung50` ~930 counts in the `q` report even though the
electrodes are attached (see §7).

This pin table is the acquisition part of the PCB rev1 pin map
(`firmware/include/board.h`). The full map, including the TFT, buzzer, buttons
B1/B2, and INA219, as well as the on-screen button and menu map, is in
[`firmware/README.md`](../../firmware/README.md).
The acquisition path can be checked without electrodes with
`pio test -e esp32-s3 -f test_hw_adc` (ADC readable, timer exactly 360 samples per
second, LO status printed).

The red→yellow axis imitates **MLII**, the lead used by MIT-BIH ("In most
records, the upper signal is a modified limb lead II (MLII), obtained by
placing the electrodes on the chest", PhysioNet `mitdbdir/intro.htm`). The AD8232
measures the voltage difference between the RA pad and the LA pad; according to Einthoven's triangle, the
RA→LA axis is Lead I and RA→left leg is Lead II, so the yellow pad (LA)
is placed below the left rib as a stand-in for the left leg. The chest placement in
the SparkFun *AD8232 Heart Rate Monitor Hookup Guide* (LA on the left chest
near the arm) and the clinical 3-lead diagram put yellow on the upper left chest; what
is measured that way is Lead I, whose QRS morphology differs from the model's
training data. The SparkFun guide does not state which lead results.

**Power: power bank.** While the laptop USB is plugged in during recording, the 50 Hz hum
wins. Example from a trial recording (archive, `20260910-1938` vs `-1948`): 266%
(laptop) vs 46% (power bank).

**Single-use electrodes.** Once removed, the gel lifts skin oil and its
contact drops. Example from a trial recording (archive, `20260910-1948`, `-1951`,
`-2019`): the swing decreases monotonically 691 → 250 → 195 counts following the number
of re-attachments.

---

## 2. Meaning of the LED

The LED (NeoPixel) is the **only signal quality indicator**; the screen does not
write out quality. Recording status is not shown through the LED, but in the
top right corner of the screen (§3). The LED follows the gate phase, and the phase is judged from
**contact**: the AD8232 LO± pins, the **signal swing after the 0.5–40 Hz bandpass** (the
same `ecg_bandpass` function as the model pipeline), and the 50 Hz hum.

That bandpass **does not kill 50 Hz**, it only attenuates it by −9.3 dB (gain 0.342;
measured from `ecg_sos` with `sosfreqz`). Large hum from the laptop USB being
plugged in still lets a third through and can fake a green LED, an example
from a trial (archive): raw swing 990 counts with filtered swing 380,
even though the content was mains, not ECG. That is why the firmware measures the 50 Hz amplitude with Goertzel
(1 second = 50 whole cycles, the bin is exact) and then **subtracts** its contribution:

```
ayun_bersih = ayun_tersaring − 0,342 × dengung50_puncak-ke-puncak
```

This `ayun_bersih` value is what is judged against the threshold of 60, and what `q`
prints as `BERSIH`. The peak-to-peak 50 Hz hum (`dengung50` in `q`)
is judged against the threshold of 500, and LO± is judged detached if even one sample within
that second shows detached.

The LED is evaluated every 250 ms in the following priority order (`update_led()`):

| LED | Condition | Meaning |
|---|---|---|
| **Blue** | calibration phase | electrode stabilization; inference is not running yet |
| **Orange** | BURUK (bad) phase: LO± detached, clean swing < 60, or 50 Hz hum > 500 | poor contact or dominant hum: **do not record** |
| **Green** | BAIK (good) phase: LO± attached, clean swing ≥ 60, hum ≤ 500 | healthy signal, OK to record |

Three states, no blinking, and no change while recording. Recording while
orange = an empty recording; fix the electrodes first. Blinking red
appears only if TFLM initialization fails at boot (not a quality state).

**Calibration phase (blue).** Every session starts in the calibration phase. Every second the
firmware judges **contact**: LO+ and LO− not detached throughout that second,
clean swing ≥ 60, and 50 Hz hum ≤ 500. The phase moves to monitoring once
contact has held for **60 seconds** (counted from when contact formed, not
from when the board was powered on) and RR 300–1500 ms with |dRR| ≤ 200 ms has been calm for
30 seconds (details: [`mqtt-walkthrough.md`](mqtt-walkthrough.md) §3.1). A long
beep marks that transition, and the per-beat beep only sounds after it.
While blue, the LED does not show orange/green, so contact quality is read
from `q` or from the menu page **Kalibrasi → Status** (Calibration → Status; `Kontak x/60 s`, calm RR,
swing and hum against their thresholds, lost samples; updated every
second). After monitoring has started, worsening contact moves the phase to
BURUK (orange LED, beats held back) and back to BAIK as soon as contact recovers, without
repeating the 60 seconds.

Who may skip the warm-up and calm-RR conditions (the contact condition for the
ADC sensor is **never** skipped):

| State | Warm-up & calm RR | Notes |
|---|---|---|
| source = ADC, `k` OFF | **fully applies** | the official recording condition |
| source = reference replay or recording replay (the **Sumber sinyal** (Signal source) menu; `y` for reference replay) | **skipped automatically** while replay is active; LO± is also ignored | record 208 is arrhythmic and will never be calm in RR; a replayed recording is not an electrode contact that is stabilizing, so the stabilization condition is meaningless; both are without electrodes. Serial: `GERBANG DILEWATI (replay)`. The bypass disappears as soon as the source returns to Sensor (ADC) |
| skip ON (`k`, or menu **Kalibrasi → Lewati (bench)** (Calibration → Skip (bench))) | skipped: **manual override for the bench** | serial: `GERBANG DILEWATI (bench)`. The contact condition still applies, so without electrodes the gate does not open. Turning it off starts a **new session**, so the full gate applies again from zero |

Do not record official data with `k` ON: the gate guarantees nothing.

**Clipping has no color.** An extra LED pattern would stack meanings onto one
color. As a consequence, a signal clipped at the rail shows **green**: the LED only
measures swing, and a clipped signal swings widely. Clipping is still
counted, check it via serial:

```
q   laporan kualitas tiap detik (toggle), kolom `clipping`
s   status sesaat, kolom `clipping`
```

Before starting to record, enable `q` and make sure `clipping 0`. Green alone is
not enough.

---

## 3. Recording

The top right corner of the monitor screen shows the recording status:

| Display | Color | Meaning |
|---|---|---|
| `RECmm:ss` | red | recording; time = length of the stored signal |
| `JEDAm:ss` | yellow | recording paused; samples are not stored |
| `SIMPAN` + `/rekam/NNN.csv` | green | a new file was saved (shown for 3 seconds) |
| `TERKUNCI` + `tahan B3=simpan` | orange | menu rejected because a recording session is open (shown for 2 seconds, reject beep) |
| `TOLAK` + `hanya sensor ADC` | orange | start of recording rejected because the source is not Sensor (ADC) (shown for 2 seconds, reject beep) |
| `RP 208` / `RP#NNN` | yellow | replay signal source (reference / recording `NNN`), not the sensor |
| empty | - | source is Sensor (ADC), not recording |

The B3 button box on the bottom row is labelled `B3 REC` when not recording, `B3 JEDA`
when recording, and `B3 LANJUT` when paused, with the hint `tahan=SIMPAN`.

1. Attach new electrodes according to §1. The board is powered from the power bank; the laptop USB
   is **unplugged**. Make sure the signal source is **Sensor (ADC)**: the top right corner of the TFT
   does not show `RP 208` or `RP#NNN`. The source choice is stored in NVS
   so a previously chosen replay stays active after boot; change it via the
   menu **Sumber sinyal → Sensor (ADC)** (hold B2 to open the menu).
   Recording can only be started from the sensor: if the source is still replay, B3 and
   serial `r` are rejected with `TOLAK` on the screen and `REKAM hanya dari sensor` on
   serial.
2. Make sure signal quality is good: the LED is **green**, or during the calibration phase (blue)
   `BERSIH ≥ 60` and `clipping 0` in the `q` report.
3. From the monitor screen (menu closed), press **B3** briefly (GPIO 6). The top right corner
   shows a running red `REC00:00`, and serial prints
   `REKAM mulai`. The LED continues to show signal quality. While the menu is open, B3
   is a navigation button and serial `r` is rejected (`REKAM ditolak: tutup menu
   dulu`) so recording is always started from the monitor screen.
4. Sit still, arms resting, for **25 seconds**.
5. If recording needs to be stopped temporarily (the subject moves, a cable
   is bumped), press **B3** briefly to pause. The screen shows a yellow `JEDA`
   and serial prints `REKAM jeda n=<sampel> (<detik> detik)`. Press
   **B3** briefly again to resume; serial prints `REKAM lanjut ...`.
   The paused part is not stored, and the file records its boundary as a
   `# jeda` line.
6. Hold **B3** until the long beep (800 ms) to stop and save, from either
   the recording or the paused state. The screen shows a green `SIMPAN` with
   the file name. Expected result on serial:

   ```
   SIMPAN <n> sampel (<detik> detik, <k> segmen), 0 terlewat, elektroda lepas 0% -> /rekam/001.csv
   ```

   If `PERINGATAN: elektroda lepas >10%` appears, the recording is most likely
   empty; repeat from step 1.

**The menu and signal path are locked during a recording session.** From `REKAM mulai`
until the file is saved, including while paused, holding B2 does not open the menu:
the screen shows `TERKUNCI` / `tahan B3=simpan` for 2 seconds with a reject
beep, and serial prints `DITOLAK: menu selama sesi rekam, simpan dulu (tahan
B3 / r)`. Serial commands that change the signal path (`y`, `V`, `p0`–`p5`, `k`,
`w<n>`, `b<n>`) are rejected with the same `DITOLAK: ...` message. With this lock
a single file never mixes sensor and replay, and never has a hole without a
`# jeda` line (the device tests pause acquisition, the power ladder forces replay 208).
To change the source, run tests, measure power, or change networks,
**save the recording first** (hold B3), then open the menu. Short B1 (mute), short B2
(freeze), and the read commands `s`, `l`, `q`, `v` remain valid during the session.

Serial equivalents: `r` = start, or stop and save (also while paused);
`j` = pause / resume. Serial `s` shows `rekam 1` while a recording session is
open (including while paused) and `jeda 0/1`.

The whole session is buffered in PSRAM while recording and only written to LittleFS
after stopping; files already written survive a board power-off, whereas a
session that has not been stopped is lost if power is cut. Flash writes are deferred
because every flash write holds off the acquisition interrupt and drops samples
(`firmware/README.md` §Jebakan, Akuisisi). After stopping, the session is split
into files of 5 minutes of signal each (`RECORDER_SAMPLE_MAX` = 360 × 300 samples;
paused time is not counted); the header of a continuation file contains `lanjutan=NNN
celah=0`, and while recording the screen shows the total session time along with
`bagian <k>`. The maximum session length is printed at the start (`REKAM mulai (maks 5
bagian = 1500 detik)` with an empty LittleFS), so pull the data after each
subject (`firmware/README.md` section Merekam, Rekaman panjang). If `lewat=`
in the header is greater than 0, some samples were not captured in that file and the RR
around them is not valid.
Each recording is stored as a newly numbered file (`/rekam/001.csv`, `002`,
...); the list is viewed with serial `l` and old files are deleted with `h<n>`.
Stored recordings can be replayed on the board via the menu **Sumber sinyal
→ Replay rekaman** (Signal source → Replay recording); replay skips the `#` lines so segments are played
back to back without a pause. The `elektroda lepas` (electrode detached) percentage comes from the LO+/LO− pins;
a value of 0% is not a guarantee that there is a signal (LO is satisfied by a single low-impedance
path), so the referee remains the swing in §6.

### Recording file format

```
# fs=360 n=<total sampel> lewat=<hilang> lepas=<LO aktif> (<persen>%)
<counts ADC, satu sampel per baris>
...
# jeda
<counts ADC segmen berikutnya>
...
```

- `n` = the number of samples across all segments.
- A `# jeda` line separates two segments. Two adjacent segments are **not
  continuous** in time: the signal during the pause is not in the file.
- A pause immediately followed by save does not produce a `# jeda` line at the end
  of the file, and a pause without new samples does not produce an empty segment.
- A recording without a pause contains no `# jeda` line and is the same as the old format.

---

## 4. Pulling data to the laptop

1. Close any other serial monitor holding the port (PlatformIO monitor, VS Code).
2. Plug in USB, then run:

   ```
   cd model
   make pull
   ```

3. Expected result (example format from a trial recording; the file is now
   in `data/arsip/rekaman-uji-coba/`):

   ```
   15877 baris -> data/recordings/20260910-2019.csv
   # fs=360 n=15877 lewat=0
   ```

The second line is the file header: `fs` the sample rate, `n` the number of samples, `lewat`
the samples lost because the queue was full. The main firmware also writes
`lepas=<n> (<persen>%)`, the number of samples with LO active while recording. The
`# jeda` lines inside the file are pulled as they are (format: §3).

If the board is still recording or paused, `make pull` stops and saves it
first automatically.

The file name = the **pull time**, not the recording time (`datetime.now()` in
`pull_recording.py`). `make pull` pulls the last numbered recording; if there is
no new recording since the previous pull, that old recording is pulled again with a
new name. Another numbered recording: `make pull N=<n>` (the file name gets the suffix
`-rekam-NNN`); the list of numbers on the board: serial `l`.

Everything runs in the same `.venv`: `pyserial` is already in `requirements.txt`.
Port is not `/dev/ttyACM0`? `ECG_PORT=/dev/ttyACM1 make pull`.

---

## 5. Analyzing

1. Run from `model/`:

   ```
   make analyze FILE=data/recordings/<nama>.csv
   ```

2. The expected result is numbers, not impressions. Example from a failed trial
   recording (archive), `make analyze FILE=data/arsip/rekaman-uji-coba/20260910-2019.csv`:

   ```
   20260910-2019: 15877 samples = 44.1 seconds @ 360 Hz, 0 samples missed
     ADC          3363..3558   clipping 0 samples (0.000%, threshold 0.1%) OK
     50Hz hum       39.1% of ECG band   TOO LARGE
     noise >60Hz   191.3% of ECG band   TOO LARGE
     drift <0.5Hz    2.1% of ECG band
     pulse        autocorrelation 0.14 @ 88 bpm   NO clear pulse
     R-peak       169 in 44.1 seconds
   ```

   The `BPM` line (mean, min, max, percent plausible) is also printed if
   more than two R-peaks are detected.

   For a file containing `# jeda`, the first line states the number of segments and one
   line per segment precedes the combined summary. Example from a trial recording
   (archive) `20261011-1834` into which one artificial `# jeda` was inserted after the
   4000th sample:

   ```
   20261011-1834-jeda: 10947 sampel = 30.4 detik @ 360 Hz, 0 sampel terlewat, 2 segmen (dipisah jeda)
     segmen 1      11.1 detik   R-peak   11   RR   10   autokorelasi 0.45 @ 60 bpm, 1 puncak setara
     segmen 2      19.3 detik   R-peak   22   RR   21   autokorelasi 0.22 @ 69 bpm, 4 puncak setara
     ADC          1461..3110   clipping 0 sampel (0.000%, ambang 0.1%) OK
     ...
     R-peak       33 dalam 30.4 detik
   ```

   The RR count = R-peaks − number of segments (10 + 21 = 33 − 2): the interval between the
   last R-peak of segment 1 and the first R-peak of segment 2 is not counted because it
   crosses the pause.

3. The plot is saved automatically at:

   ```
   artifacts/metrics/akuisisi/akuisisi_<nama>.png
   ```

Open with `xdg-open artifacts/metrics/akuisisi/akuisisi_<nama>.png` (the trial
example plot above: `artifacts/arsip/akuisisi-uji-coba/akuisisi_20260910-2019.png`).
Three panels: raw ADC, the bandpass result + R-peak lines, and the spectrum (red band
= 50 Hz, green band = ECG band). For a paused recording a fourth panel is added:
the whole recording after bandpass on a combined time axis (paused time is not
counted), with segment boundaries as dashed vertical lines. The same lines
appear in the first two panels if a boundary falls within the first 6 seconds.

4. A one-minute plot for viewing beat by beat:

   ```
   make plot FILE=data/recordings/<nama>.csv            # 60 detik terbaik
   make plot FILE=data/recordings/<nama>.csv MULAI=120  # mulai detik 120
   ```

   Result: `artifacts/metrics/akuisisi/rekaman_<nama>_detik-<awal>.png`, six
   rows of 10 seconds of 0.5–40 Hz bandpass signal with a ▼ mark at every detected
   R, plus a per-beat HR panel. Without `MULAI`,
   `plot_recording.py` slides a 60-second window every 5 seconds and chooses the one with the
   fewest implausible RR (< 30 or > 200 bpm), then the one whose >60 Hz
   noise is smallest relative to the ECG band. The R marks use the
   Pan-Tompkins detection corrected by `PT_DETECTOR_OFFSET` and then aligned
   to the peak (`align_r`), the same as the firmware chain. Paused recordings are
   searched per segment; segments shorter than the window are skipped. Example
   output:

   ```
   jendela detik 240-300: RR tak wajar 0, derau >60 Hz 5.6% pita EKG, HR median 78 bpm (61-95), 76 R
   ```

### Per-segment analysis

`analyze_recording.py` splits the file at every `# jeda` and computes each
segment separately, then combines the results:

| Computation | Per segment | Combination |
|---|---|---|
| Mean (DC) and 0.5–40 Hz bandpass | the filter starts from zero state at the start of each segment; the initial transient of a segment is treated the same as the initial transient of a recording | the filtered signal is concatenated for the plot |
| Pan-Tompkins R-peak | detected per segment | indices shifted to the combined time axis |
| RR and BPM | `diff` of R-peaks within the segment | concatenated; **no RR crosses a pause** |
| Band energy (hum, noise, drift, ECG band) | per segment | summed, then ratioed |
| Beat autocorrelation | per segment; segments ≤ 1.5 seconds skipped; segments ≥ 60 seconds computed per 30-second window then the median is taken (`AUTOCORRELATION_WINDOW_S`) | mean weighted by segment length; the equivalent peak count is rounded |
| ADC min/max, clipping | all samples | - |

The reason: the signal before and after a pause is not continuous in time.
Running the filter over the concatenation would introduce a baseline jump as a
false transient, and an RR that crosses a pause is not a real beat interval.
A file without `# jeda` is a single segment and gives output identical
to the version before pause support (verified on 27 archive recordings: text
and PNG exactly the same). Test: `tests/test_analyze_recording.py`.

---

## 6. Reading the numbers

| Metric | Target | If missed |
|---|---|---|
| `sampel terlewat` | **0** | timer problem: report it, this is a firmware bug |
| `clipping` | ≤ 0.1% of samples at the firmware rail (≥ 4090 or ≤ 5) | repeated clipped peaks: baseline too close to the rail, or electrode/cable shaken. The clean 22 Oct 2026 recordings have at most 0.010% (R peaks occasionally touch 4095), disturbed recordings ≥ 0.135% |
| `dengung 50Hz` | < 15% | unplug the laptop USB, twist the cable, check RL |
| `derau >60Hz` | < 50% | partly suppressed by the bandpass, improves too if 50 Hz drops |
| `drift <0.5Hz` | < 10% | the subject moves, or an electrode shifts |
| `denyut` | PRESENT, autocorrelation > 0.25 (recordings ≥ 60 seconds: median per 30 seconds, marked `(median per 30 s)`) | see below |
| `BPM masuk akal` | > 90% (30–200 bpm) | lower the hum first |

The thresholds for `dengung`, `derau`, `denyut`, and `BPM masuk akal` are the thresholds
used by `analyze_recording.py` for the verdicts `OK` / `TERLALU BESAR` /
`TIDAK KONSISTEN`.

The main referee for whether a signal exists is the **absolute ADC swing**, not the LO flag.
Conversion: 12-bit ADC with 11 dB attenuation ≈ 0.757 mV/count at the pin, AD8232 gain
~1100, so a healthy ECG of ~2 mV ≈ ~3,000 counts. A swing below ~150 counts
(~0.1 mV) means no biopotential at all; poor lead placement
only cuts it 3–5×, not 50×.

### Two pulse metrics, and why both are needed

**Autocorrelation** checks whether the pattern repeats every 0.4–1.5 seconds. It is robust to
noise because the 50 Hz hum repeats every 20 ms, far outside that window.

**Pan-Tompkins** looks for energy spikes. Strong hum leaks
through the squaring + integration stage and counts as QRS, which is why it can
report 169 "R-peaks" in 44 seconds.

Autocorrelation looks for ONE dominant inter-beat distance. In long recordings the
heart rate changes across minutes so the peak widens and its value
drops even though the signal is good. That is why segments ≥ 60 seconds are judged per
30-second window and the median is taken. Measured on the 300-second recording of 14 Oct 2026
(trial archive): whole recording 0.24 (below the threshold), per 30 seconds
0.25–0.44 with a median of 0.36, median HR per minute 70–81 bpm. Segments < 60 seconds
are still judged whole; the output of the 44-second archive recording `20260910-2019` is identical
before and after this change.

The verdict `PALSU — N puncak setara` (FAKE: N equivalent peaks) means high autocorrelation but the peaks
line up uniformly. A heart gives **one** dominant peak; natural beat variability
makes the following peaks decay. A row of equivalent peaks = machine interference.

### SQI per 10-second window (Orphanidou 2015)

The `analyze_recording.py` verdict applies per recording so one bad minute in a
300-second recording can be hidden. `scripts/window_quality.py` judges each
10-second window without overlap with the SQI of Orphanidou et al. 2015
(`laporan/pustaka/orphanidou_2015.pdf`, pp. 834–836):

1. HR = 60 / mean RR in the window, must be 40–180 bpm.
2. Longest RR gap ≤ 3 seconds.
3. Longest / shortest RR ratio < 2.2.
4. If all three pass: cut each QRS to the width of the median RR with R in the center,
   average them into a template, compute the correlation of each cut against the template.
   Mean correlation ≥ 0.66 (the paper's threshold: *sensitivity* 94%, *specificity* 97%
   against manual annotation).

R-peaks use the same chain as the plot (`plot_recording.r_peaks`:
`PT_DETECTOR_OFFSET` compensation, `PT_REFINE_WIN` alignment) on the
*bandpass* signal. Cuts truncated by the window edge are discarded.

```bash
cd model
.venv/bin/python scripts/window_quality.py data/recordings/20261022-1256-rekam-001.csv \
  data/recordings/20261022-1256-rekam-002.csv data/recordings/20261022-1257-rekam-003.csv \
  data/recordings/20261022-1257-rekam-004.csv
```

Results of the official 22 Oct 2026 recordings:

| Recording | Windows | Pass rules 1–3 | Pass all | Median / minimum correlation |
|---|---|---|---|---|
| R1 `-1256-rekam-001` | 30 | 100% | 100% | 0.991 / 0.981 |
| R2 `-1256-rekam-002` | 30 | 100% | 100% | 0.987 / 0.967 |
| R3 `-1257-rekam-003` | 30 | 100% | 100% | 0.985 / 0.967 |
| R4 `-1257-rekam-004` | 2 | 100% | 100% | 0.982 / 0.980 |

Negative control on the archived trial recordings (§8): a noise-floor recording
(swing 16–55 counts) passes 0% of windows, the 14 Oct 2026 recording passes 93.3%, so
this judge can indeed reject. **Trap:** this SQI does not judge amplitude.
The archived recording `20261011-1823` swings only 176 counts and still passes one
of its windows, because correlation is not scale sensitive. The absolute ADC swing remains the referee of
whether a biopotential exists; the SQI judges beat regularity on top of it.

---

## 7. When there is a problem

| Symptom | Likely cause | Check |
|---|---|---|
| LED orange all the time | electrode used up / leads swapped | replace with a new electrode; make sure yellow is on the left rib, green on the right rib |
| `make pull` → "Tidak bisa membuka" (cannot open) | another serial monitor is open | `lsof /dev/ttyACM0`, close the PlatformIO monitor in VS Code |
| `make pull` → "Tidak ada rekaman" (no recording) | never recorded and saved | record first (§3) |
| hum > 200% | laptop USB plugged in while recording | power bank |
| small amplitude, low hum | LA & RL swapped | swap yellow and green |
| `dengung50` ~930 counts in `q` even though electrodes are attached | OUTPUT line broken, ADC pin floating | check the OUTPUT cable → GPIO1; make sure the pin is on ADC1 |
| swing stuck at 40–55 counts (noise floor, ~38 µV input-referred) | the AD8232 module header connection is not soldered / intermittent | solder the module header, record again |
| `elektroda lepas 0%` but the recording is empty | LO satisfied by a single path (e.g. RL only) | judge from the swing, not from LO |
| ADC absolute 0 | pin/line shorted or module unpowered | `s` on serial, look at the status |
| LED blue all the time | calibration phase not yet passed (60 seconds contact + 30 seconds calm RR) | check **Kalibrasi → Status**: `Kontak 0/60 s` means contact has not formed (new electrodes, clip fully clamped); hum above 500 → use the power bank supply (22 Oct 2026 test: bad signal when plugged into the laptop USB, good with a power bank) |

Measuring circuit resistance with an ohmmeter must be done with power off;
an ohmmeter on a powered circuit gives a wrong number with no sign of it.

### Serial commands

The board accepts a single letter over serial 115200 (`pio device monitor`):

| Letter | Effect |
|---|---|
| `r` | start recording / stop and save, also from the paused state (equivalent to short B3 when not recording, long B3 while recording) |
| `j` | pause / resume recording (equivalent to short B3 while recording) |
| `d` / `d<n>` | dump the last recording / number `<n>` to serial (`make pull` uses `d`; it has no physical button) |
| `l` | list recordings in LittleFS: number, size, header |
| `h<n>` | delete recording number `<n>` |
| `s` | instantaneous status: recording, pause, sample count, phase, beats, queue, lost samples, LO, swing, clipping, MQTT, INA219 |
| `q` | toggle the per-second quality report |
| `k` | toggle the calibration gate override for bench tests; OFF = new session, full gate from zero (see §2); equivalent to menu Kalibrasi → Lewati (bench) |
| `y` | toggle signal source ADC ⇄ reference replay; all three sources (including recording replay) are chosen from the Sumber sinyal menu |
| `m` | toggle MQTT publishing |

The letters `y` and `m` are described in [`mqtt-walkthrough.md`](mqtt-walkthrough.md) §4.
Serial is useful when the buttons are hard to reach, or to make sure the board is not
recording. A Python script that sets `s.dtr = s.rts = False` before
`s.open()` resets the board, and a reset in the middle of a recording session loses
the entire session. Open the port with the default `serial.Serial(port, 115200)` without
touching DTR/RTS (like `make pull`) if the board may be recording, then
verify the state from the board's reply (`s`), do not assume it (`model/CLAUDE.md`
§Jebakan).

---

## 8. Acquisition trial data (archive, not results)

The official data (22 Oct 2026 afternoon session) and the development recordings of 15–22 Oct 2026
are stored in `data/recordings/`, named by pull date-time. The trial recordings of 10 Sep – 21 Oct 2026 are in
[`data/arsip/rekaman-uji-coba/`](../data/arsip/rekaman-uji-coba/README.md)
along with their circuit conditions. This table contains the first seven trial
recordings (breadboard circuit, 10 Sep 2026), kept because
their lessons shaped the procedure of §1 and §3, not as results.

| # | Power | Hum | Pulse | Lesson |
|---|---|---|---|---|
| 1–2 | laptop | 83%, 266% | fake | laptop USB = hum wins |
| 3 | power bank | 51% | none | the electrode shifted too: two variables changed at once |
| **4** | power bank | **46%** | **PRESENT 0.49 @ 97 bpm** | the only one that succeeded |
| 5 | power bank | 46% | none | the electrode began to tire |
| 6 | ? | 312% | fake | hum this high = plugged into the laptop |
| 7 | power bank | **39%** | none | the best hum, but the electrode was already used up |

One change per trial. Trial 3 changed the power **and** shifted the
electrode at once so the result cannot be attributed to either.

**Example of a trial recording that has signal** (archive, not an official reference):
`data/arsip/rekaman-uji-coba/20260915-1130.csv`: swing 3,128 counts,
hum 3.3%, autocorrelation 0.27 @ 87 bpm, 64 R-peaks in 47.2 seconds, plausible BPM
100% (20 clipped samples at the upper rail). Useful as a comparison for the plot shape
when testing `make analyze`.

---

**[← firmware: port to ESP32-S3](firmware-walkthrough.md)**  ·  [Walkthrough map](README.md)  ·  **-**
