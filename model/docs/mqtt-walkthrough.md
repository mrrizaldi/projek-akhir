# HW-6: MQTT publication, from a beat on the device to a row on the dashboard

> **Scope:** publishing per-beat classification results from the ESP32-S3 to ThingsBoard CE over MQTT QoS 1, together with the quality gate, the backlog, and the procedure for testing without electrodes.
> **Related code:** `firmware/src/ecg_mqtt.cpp`, `firmware/include/ecg_mqtt.h`, `firmware/src/gate.cpp` (`gate_assess_phase()`), `firmware/src/classifier.cpp` (`publish()`), `firmware/test/test_mqtt/`, `dashboard/`
> **Prerequisite:** [`firmware-walkthrough.md`](firmware-walkthrough.md) §5b–5c, [`acquisition-walkthrough.md`](acquisition-walkthrough.md) §2

Condition: verified on the board (N16R8, 19 Sep 2026). The whole mechanism of
`bab3.tex` §Pipeline Edge-to-Cloud yang Resilien (the report section "Resilient Edge-to-Cloud Pipeline") is in place, and **6 of 6 targets of the
Tabel Rencana Pengukuran (measurement plan table) were measured**: 5 pass, 1 passes at the median but is unstable
at p95 (§7c). `pio test -e native` 23/23, `pio test -e esp32-s3` 16/16, and
telemetry lands in ThingsBoard over WiFi. The resilience test passes: the broker was
frozen for 24 seconds and the time series on the dashboard has **no gaps** (maximum gap
911 ms). Full numbers in §7, bugs that only appear on hardware in §7b.

---

## 1. The big picture

```
        ┌──────────── SIGNAL SOURCE (Sumber sinyal menu) ──────────┐
        │  reference replay : sim_counts[] from golden_raw (rec 208) │
        │  recording replay : /rekam/NNN.csv loaded into PSRAM       │
        │  sensor (ADC)     : adc1_get_raw() — AD8232, electrodes    │
        └──────────────────────────┬───────────────────────────────┘
                                   │ ISR 360 Hz → queue 256
                                   v
   bandpass → Pan-Tompkins → align R → window+z-score → RR features
                                   │  (ecg_live_push)
                                   v
                        INT8 inference (TFLM)  →  p
                                   │
                                   v
                      ┌──── publish(): GATE ────┐
                      │ swing_clean >= THRESHOLD_SWING │
                      │ && !beat.signal_lost        │
                      └──────────────┬────────────────┘
                                     v
        backlog ring 27,000 beats in PSRAM, reserve 64 (ecg_mqtt_queue_fill)
                                     │
                                     v   ecg_mqtt_service(), every loop()
                      PUBLISH QoS 1 ──► broker ──► PUBACK
                                     │                  │
                          batch <=50 │       advance ring AFTER PUBACK
                                     v
                          ThingsBoard CE: ts_kv → widget
```

In one sentence: **a beat that passes the quality gate enters the ring; the ring is drained to
the broker; the ring is only advanced after PUBACK.** The gate in the diagram is the
per-beat gate; in front of it, every session must pass an entry gate in the form of the
calibration phase (§3.1).

---

## 2. Components that are reused (do not rebuild them)

| Part | Location |
|---|---|
| Dummy signal source | `acquisition.cpp` `rp_data` / `sim_counts[]`, the "Sumber sinyal" (signal source) menu or the `'y'` toggle ([firmware §5c](firmware-walkthrough.md)) |
| Broker + rule engine + dashboard | `dashboard/` (ThingsBoard CE) |
| Payload contract (7 fields, QoS 1, topic) | `dashboard/README.md`, `bab3.tex` |
| Proven MQTT wire reference | `dashboard/smoke_test.py` |
| Signal quality assessor | `gate.cpp` `gate_assess_quality()`, `THRESHOLD_SWING` |

The MQTT module **duplicates none** of that list. All that was added
is the MQTT client, the backlog ring, and its gate.

---

## 3. Function by function

### 3.1 Two gates: the calibration phase, then electrode contact

Contact assessment runs every second in `assess_contact()` (called by
`gate_assess_quality()` after the 1-second window), and the calibration phase is assessed per
beat in `gate_assess_phase()`:

```
contact (every second)  LO+ = LO- = 0 throughout that second (ignored in replay)
                        and swing_clean >= THRESHOLD_SWING (60)
                        and hum50 <= THRESHOLD_HUM (500)
calibrating -> good     contact held >= WARMUP_MS (60 seconds, counted from the
                        last time contact was established, not from boot)
                        and RR 300-1500 ms with |dRR| <= 200 ms calm for 30 seconds
                        and contact at that moment
```

The warm-up duration comes from three recording sessions of ±15 minutes (21–22 Oct 2026):
clean swing ≥ 60 from second 0 and a calm RR for 30 seconds were reached at second 30
in all three; 60 seconds = twice the measured pass time. A 10-minute timer from the
session start is not used because it is not supported by data and makes the beat beep
silent for 10 minutes even when the signal is already good. If contact loses any condition →
the warm-up count starts again from zero when contact returns.

While `calibrating`, **the CNN is not run** (bab3: *"inferensi CNN belum
dijalankan"*, "CNN inference not yet run"), nothing is published, and the LED is lit blue. The detector
keeps running; its RR is in fact what is used to assess eligibility. Serial prints the
line `calibrating | RR=… dRR=… | calm …/30 s | swing … | hum … | leadoff … |
contact …/60 s` every 5 seconds.

After the monitoring phase begins, the phase alternates between `good` and `poor` every
second according to contact (LO±, swing, hum), without waiting for a beat and without
repeating the warm-up; serial prints `kualitas: good -> poor (leadoff …, swing …,
hum …)` and the reverse. Swing alone is not enough: in the morning session of 22 Oct 2026
swing stayed ≥ 1,400 and 97–100% of RR was plausible while hum spiked to 2,800
and LO recorded the electrode as detached 41–62% per file. The hum threshold of 500 sits
between the values of a clean session (per-minute median ≤ 370) and the spike of bad contact
(≥ 790).

> **Important: the RR criterion is the ENTRY gate, not the per-beat gate.** After the monitoring
> phase starts, `dRR` is NO LONGER limited. Enforcing `dRR <= 200 ms`
> continuously would silence the very arrhythmias we want to detect: a ventricular
> beat does arrive with a large `dRR`. `bab3.tex` also writes it as a
> condition *"layak untuk fase pemantauan"* ("fit for the monitoring phase"), once only.

The per-beat publication gate:

```c
if (!ecg_mqtt_active()) return;
if (gate_phase() != PHASE_GOOD) { h.withheld++; return; }
if (beat.signal_lost) { h.withheld++; return; }
```

**Two gates, two independent mechanisms.** Swing measures amplitude, RR measures
rhythm eligibility. A fabricated beat without electrodes fails both at once:
swing ~27 counts (< 60) AND RR 0.208 s (< 300 ms). This redundancy is deliberate, and
in line with the `lepas 0%` lesson: one indicator can lie, two indicators
being wrong at the same time is far rarer.

### 3.1b Why replay must pass the calibration gate

`golden_raw` is **record 208**, full of ventricular beats; its `dRR` was measured at
−0.364 s and +0.478 s. The criterion *"dRR ≤ 200 ms for 30 seconds"* **will
never be met**, and it should not be: that criterion is for a **healthy** subject sitting still,
while our test signal is deliberately arrhythmic.

The two cannot be satisfied together, so the gate yields, with an
announcement. That bypass is **derived from the signal source**, not stored as a
flag:

```c
if ((skip_calibration || replay || (warm && rr_quiet)) && q.contact)
    phase = PHASE_GOOD;
```

`replay` is true for both replay sources, reference and recording
(`acquisition_replay()` = a source that is not ADC). During replay, the time and RR gates
are skipped and serial prints `GATE SKIPPED (replay)` when the phase changes.
Returning to Sensor (ADC), through the "Sumber sinyal" menu or a second `y`, calls
`gate_begin_session()` so that body signals return to `calibrating` and
must meet the full gate (60 seconds of contact + 30 seconds of calm RR).
No state left over from replay can open the gate for a body
signal.

The `k` toggle (the "Kalibrasi" → "Lewati (bench)" menu, i.e. Calibration → Skip (bench)) is a manual override for
the bench, separate from replay: `k` ON skips the warm-up and RR conditions for the
ADC path (`GATE SKIPPED (bench)`), but does not skip contact (LO±,
swing, hum). Without electrodes LO is 1, so `k` no longer opens the
gate for ADC noise; bench tests without electrodes use replay. `k` OFF calls `gate_begin_session()` so that the phase returns to `calibrating` with the full
gate, including when the phase is already `good`. The `k` status is read in the status line
(`lewati 0/1`, §4.4).

The gate tests in force (replay, bad contact, good contact) are in §3.1c.

The buzzer follows the phase: the beat beep is silent during `calibrating`, and a long
600 ms tone marks calibration starting (boot, source change, Kalibrasi → Mulai ulang (Calibration → Restart),
`k` OFF) and finishing
(entering `good`).

**Gated on signal quality, not on whether a beat exists.** The reason is measured and
already in the pitfall list of `../CLAUDE.md`:

> Without electrodes, the device fabricates arrhythmia: **~2 beats/second, 57% "ARRHYTHMIA"**.
> The Pan-Tompkins threshold is adaptive relative to the signal present, so "no
> signal" is not a condition it recognizes: even 15 counts of noise has peaks.

If publication were gated on beats, a detached electrode = a flood of false alarms to the broker.
`withheld` is counted so that this holding back is visible in `'s'`, rather than becoming
data that is lost silently.

The third line rejects beats that come out through `ECG_LIVE_TIMEOUT` (asystole /
detached electrode). `ecg_live.h` already instructs it: *"Pemanggil sebaiknya
menaikkan alarm 'sinyal hilang' TERPISAH dari klasifikasi aritmia, supaya tidak
mengotori metrik."* (The caller should raise a "signal lost" alarm SEPARATE from the arrhythmia classification, so as not to
pollute the metrics.)

### 3.1c Contact gate test (22 Oct 2026)

Test condition: N16R8 board, firmware with the contact gate, MLII electrodes.

1. Reference replay, without electrodes (serial, USB):

   ```
   >>> y   replay ON (golden_raw)
           kualitas: calibrating -> good (GERBANG DILEWATI (replay), kontak 2 s, RR tenang 3 s, ayun 2434, dengung 19)
   >>> s   status: ... replay=1 | kualitas good | ... | LO 1 1 | ... ayun 2836
   >>> y   replay OFF (ADC)
   >>> s   status: ... replay=0 | kualitas calibrating | ... | LO 1 1 | mentah 0..9 ayun 1
   ```

   LO is ignored during replay; returning to ADC without electrodes stays
   `calibrating`.
2. Electrodes with bad contact, board plugged into the laptop USB (serial, ±3.5
   minutes): every `calibrating` line shows `lepas 1` and `kontak 0/60 s`;
   swing rises slowly 11 → 395, hum up to 486, RR random 0.20–1.10 s. The gate
   does not pass.
3. Electrodes attached well, powerbank supply (observed by the subject on the screen, no serial
   log): blue LED then a long beep and green LED about 60 seconds after the
   electrodes attach, beat beep starts; the yellow cable clip is pulled off for ±10 seconds →
   orange LED; reattached → green without waiting 60 seconds.

Not yet verified with a serial log: step 3 (the transitions `calibrating -> good
(gerbang penuh, kontak 60 s ...)` and `good -> poor (lepas 1 ...)` being printed).

### 3.2 `confidence`: confidence in the DECISION, not the raw `p`

```c
t.confidence = arrhythmia ? p : 1.0f - p;
```

`p = 0,02` for a normal beat means the device is **very sure**. Sending 0.02 as is
makes the widget show "confidence 2%" exactly when the device is surest.

### 3.3 `ecg_mqtt_payload()`: pure, and therefore testable

```c
size_t ecg_mqtt_payload(char *buf, size_t n, const ecg_mqtt_beat_t *b, size_t nb,
                        uint64_t ts_base_ms);
```

`nb == 1` → a single object; `nb > 1` → an array. Those two forms are not style, they are the
ThingsBoard contract (`dashboard/README.md`: real-time vs batch flush).

**`ts` of each beat = `ts_base_ms + beat.ms`.** This is the core of the resilience claim:
a beat held for 40 seconds in the backlog still carries the time it **occurred**.

`beat.ms` is filled by `publish()` from the sample index of the R peak, not from
`millis()` at the moment the beat comes out:

```c
t.ms = gate_t_session_ms() + (uint32_t)((uint64_t)beat.r_abs * 1000ULL / ECG_FS);
```

Detection runs every 1 second over a 4-second ring, so several beats come out
bunched in the same millisecond; `millis()` at output makes the dashboard
show beats crowded together and then idle (measured: minimum gap between `ts` values
28 ms, while the shortest RR is ~200 ms). As a consequence, samples lost in
the queue shift `ts` by the lost duration, which is why `sampel hilang`
is also reported in the `s` line.
If `ts` were taken at send time, the whole backlog would pile up in one second and the
dashboard graph would lie, and worse, the `smoke_test.py` dedup test
would still pass, so the error would never be caught there.

Insufficient buffer → return **0**, not a truncated payload. Half a JSON is accepted by the
broker as garbage with no visible error on the board. Tested:
`test_payload_buffer_short`.

### 3.4 The backlog ring, and why `peek` is separate from `drop`

```c
size_t ecg_mqtt_queue_peek(ecg_mqtt_beat_t *beats_out, size_t max_count);
void   ecg_mqtt_queue_drop(size_t n);
```

They are separated so that **the read pointer only advances after PUBACK**:

```c
waiting_ack = false;
packet_ack++;
ecg_mqtt_queue_drop(n_in_flight);
sent += n_in_flight;
n_in_flight = 0;
```

If merged into a single `ambil()`, beats are lost every time PUBACK does not arrive,
and QoS 1 becomes decoration. `dashboard/README.md` writes this requirement as a
contract: *"geser read pointer ring buffer hanya setelah PUBACK"* ("advance the ring buffer read pointer only after PUBACK").

The ring capacity is **27,000 beats** (`ECG_MQTT_QUEUE_TARGET`), allocated in PSRAM
at `setup()` and then attached through `ecg_mqtt_queue_attach()`; one entry is 40 bytes,
a total of ~1.05 MB of the 8 MB. If the PSRAM allocation fails, the ring falls back to a
static reserve of 64 beats (`ECG_MQTT_QUEUE_MIN`) and serial prints a warning. This pure
part knows nothing about PSRAM, so the native test just attaches a static array.

Ring full → **drop the OLDEST**. A monitoring device needs the last minute more
than the first minute when the connection has just recovered. What is dropped is recorded in
`ecg_mqtt_queue_lost()`, not hidden.

### 3.5 The MQTT client: four packets, no library

`CONNECT` / `PUBLISH QoS1` / `PUBACK` / `PINGREQ`. Written on top of `WiFiClient`.

The wire format is **not a guess**: `dashboard/smoke_test.py` already talks to the same
broker with the same bytes (`0x10` CONNECT flags `0x80` username-only,
`0x32` PUBLISH QoS1, check `0x40` PUBACK + pid). The C port copies that.

### 3.6 The clock: `configTzTime()` + `ts_base_ms`

SNTP is started with `configTzTime("WIB-7", "pool.ntp.org", "time.google.com")`.
The WIB zone only affects `localtime_r()` for the clock on the monitor screen;
`gettimeofday()` still gives the UTC epoch, so the `ts` of each beat does not change.
`configTime(0, 0, …)` is not used because it forces the TZ to UTC every time WiFi
reconnects.

```c
struct timeval tv;
gettimeofday(&tv, NULL);
const uint64_t now_ms = (uint64_t)tv.tv_sec * 1000ULL + (uint64_t)(tv.tv_usec / 1000);
ts_base_ms = now_ms - (uint64_t)millis();
```

The epoch ms when `millis() == 0`, computed once as soon as SNTP arrives
(`tv_sec ≥ 1.700.000.000`). `gettimeofday()` is used, not `time()`: the resolution of
`time()` is one second and its rounding becomes a systematic error in every `ts`
(§7b bug 6). Once `ts_base_ms` is known, each beat only needs to store the relative time
`ms` (4 bytes) and its time is reconstructed when the payload is assembled. Without a correct clock, `ecg_mqtt_status()` reports `tunggu-jam` and the
backlog **waits**, deliberately not sending with a wrong ts.

---

## 4. How to use it: the full toggling

### 4.1 Once at the start: credentials and broker

```bash
cd dashboard && docker compose up -d      # broker + dashboard
python3 smoke_test.py                     # prints: device ... token=XXXX
cd ../model && make broker-info           # laptop SSID, LAN IP, port 1883, suggested entries

cd ../firmware
cp include/wifi_secrets.example.h include/wifi_secrets.h
$EDITOR include/wifi_secrets.h            # fill in WIFI_DAFTAR and BROKER_DAFTAR
```

`include/wifi_secrets.h` is in `.gitignore`, so credentials never enter git.
**Without that file the firmware still builds and still runs**; only its MQTT
is disabled, with a single warning line at boot (`#if __has_include`).

The lists are arrays: `WIFI_DAFTAR {ssid, sandi}` and
`BROKER_DAFTAR {nama tampil, host, port, token}`. `host` is the laptop's **IP address**
on the board's WiFi network, not `localhost` (the board looks for it on the network,
not on itself) and not a hostname (the firmware does not resolve names).
As a result **the board and laptop must be connected to the same SSID**; `make
broker-info` prints the laptop's SSID so it can be matched. The active entry is chosen through
serial `w<n>` / `b<n>` (index starting at 0) and stored in NVS; entry 0 is used
if nothing has ever been chosen. The old single macros (`WIFI_SSID`, `WIFI_PASS`,
`TB_HOST`, `TB_PORT`, `TB_TOKEN`) are still accepted as a one-entry list.
The full format, servers other than the laptop, and SSID/IP/port troubleshooting:
[network-settings](../../docs/features/network-settings.md).

### 4.2 Serial toggles

| Key | Meaning | Output |
|---|---|---|
| **`y`** | **signal source: ADC ⇄ reference replay** (the "Sumber sinyal" menu chooses among all three sources, including recording replay) | `replay ON (golden_raw)` / `replay OFF (ADC)` |
| **`m`** | **MQTT publication: on ⇄ off** | `wifi ON (saved)` / `wifi OFF (saved)` |
| **`k`** | **skip the calibration gate** (bench only); OFF starts a new session with the full gate | `skip calibration gate ON` / `OFF` |
| `q` | toggle the per-second quality report | `quality \| raw … swing … CLEAN …` |
| `s` | instantaneous status (including MQTT) | see below |
| `r` | record raw to LittleFS `/rekam/NNN.csv` (equivalent to button B3) | `REC start` / `SIMPAN … -> /rekam/NNN.csv` |
| `d` / `d<n>` | dump the last recording / number `<n>` over serial | `---MULAI--- … ---SELESAI---` |
| `w` / `b` | WiFi / broker list; `w<n>` / `b<n>` chooses an entry | `wifi *0 …` / `broker *0 nama  IP:port` |

The two toggles are **orthogonal**, and that is the whole point:

| | `m` OFF | `m` ON |
|---|---|---|
| **`y` ON (replay)** | pipeline & power test, offline | **MQTT test without electrodes** (bench test) |
| **`y` OFF (ADC)** | acquisition & recording, offline | normal operation |

### 4.3 Demo without electrodes: procedure

Prerequisites: the broker is up (`docker compose up -d` in `dashboard/`) and
`wifi_secrets.h` is filled in (§4.1). Open serial with `pio device monitor` from
`firmware/`.

| Step | Action | Expected result on serial |
|---|---|---|
| 1 | boot, wait | `mqtt: WiFi "…" -> 192.168.x.x:1883`, then `mqtt: clock synced, epoch_ms …` and `mqtt connected, backlog 0 beats` |
| 2 | press `m` (if not yet ON) | `wifi ON (saved)` |
| 3 | press `y`, or the menu **Sumber sinyal → REPLAY 208** (Signal source → REPLAY 208) | `replay ON (golden_raw)`; yellow `RP 208` in the top right corner of the screen |
| 4 | wait ~7 seconds | `kualitas: calibrating -> good (GATE SKIPPED (replay), …)`, then `beat …` lines start to appear |
| 5 | press `s` | `mqtt online \| terkirim N \| backlog 0/27000 …` |
| 6 | open `http://localhost:8080` | telemetry arrives on the dashboard |

**Why replay passes the contact gate without special treatment on the publication path:** its swing is
~2700 counts, far above `THRESHOLD_SWING` 60, its hum is ±10–19, and the LO± status is ignored during replay. So the dummy and the body signal
go through the **exact same per-beat gate and publication path**: there is no
`if (dummy)` branch in `publish()` or `ecg_mqtt.cpp`. The only
special treatment of replay is skipping the calibration gate while replay is on, and
that is announced on serial (§3.1b). A dummy-specific branch in the publication path would mean that what is demonstrated is not what is
used.

### 4.4 Reading the status line

Format (three lines; example numbers, `<…>` = fill-in):

```
status: rekam=0 n=0 | replay=1 | kualitas good | beat 44 (12 aritmia, 3 ditahan) | antrean 2 |
        sampel hilang 0 (tick 0) | LO 1 1 | mentah 1204..3550 ayun 2701 clipping 0
        mqtt online | terkirim 41 | backlog 0/27000 | hilang 0 | gagal 0 |
        paket <ack>/<kirim> PDSR <x>% | tunda alat rata <ms> ms maks <ms> ms |
        RTT maks <ms> ms (lambat <n>) | RSSI <dBm> dBm | epoch_ms <epoch>
        INA219 I=<mA> mA V=<V> V P=<mW> mW | bisu 0 | beku 0 | lewati 0 | daya -1 |
        sumber acuan 0 | menu 0 | jeda 0
```

| Column | Meaning |
|---|---|
| `kualitas` | phase: `calibrating`, `good`, or `poor` |
| `ditahan` | beats deliberately NOT published (phase is not `good` / beat timeout) |
| `backlog` | beats waiting in the ring / ring capacity; non-zero = the broker is currently unreachable |
| `hilang` | ring full, oldest beat dropped; the outage exceeded the ring capacity (27,000 beats ≈ 4–7 hours; 64 beats if PSRAM failed) |
| `gagal` | PUBACK did not arrive / did not match, or the packet was not fully written |
| `paket … PDSR` | packets with PUBACK / PUBLISH packets; PDSR is counted per packet, not per beat |
| `tunda alat` | from the beat OCCURRING until its packet enters the ring (§7c) |
| `RTT maks (lambat)` | the worst PUBACK RTT, and how many times it was > 1 second |
| `RSSI` | WiFi signal strength |
| `epoch_ms` | the board clock; used by the measuring tool on the laptop to correct the clock offset |
| `lewati` | the `k` override is active (1) or not (0); replay does not change it |
| `daya` | power measurement ladder step `p0`–`p5`, or `-1` = normal operation ([`firmware-walkthrough.md`](firmware-walkthrough.md) §5d) |
| `sumber` | `adc`, `acuan` (golden 208), or `rekaman` followed by the file number (0 if not a recording replay) |
| `menu` | the on-screen menu is open (1) or not (0) |
| `jeda` | the recording is paused (1) or not (0); `rekam=1` while a recording session is open, including while paused |

`mqtt` can contain: `mati` (toggle `m` off or no credentials), `no-wifi`,
`no-broker`, `tunggu-jam` (SNTP not yet arrived), `online`.

**Loss accounting:** `beat_total − ditahan = terkirim + backlog + hilang`.
That identity is what makes the resilience test measurable, and it only holds
because the replay is **deterministic**: 11 beats per 6.67-second loop, already measured
on the board ([`firmware-walkthrough.md`](firmware-walkthrough.md) §5c, "Terukur di board" (Measured on the board)).

---

## 5. Decisions taken, together with the alternatives rejected

| Decision | Chosen | Rejected, and why |
|---|---|---|
| Location of dummy data | **signal source (ADC)** | *dummy in the publisher*: bypasses the bandpass, detector, and inference. Only JSON + WiFi are tested, while this PA's claim is "classification at the edge". The closer the injection point is to the edge of the system, the more real code gets tested |
| Form of toggle | **runtime (`y`, `m`)** | *compile-time `#ifdef DUMMY`*: two binaries, and what is demonstrated is not what is flashed for operation |
| MQTT client | **written in-house, 4 packets** | *PubSubClient*: a CLAUDE.md gate point (do not add a dependency for something a few lines solve); the wire format is already proven in `smoke_test.py`; precedent in `ina219.cpp`, which also has no library. **If QoS 2, retained, or subscribe is needed, move to PubSubClient: that is the upper limit of this choice** |
| Publication gate | **signal swing** | *whether a beat exists*: even noise produces beats, 57% "ARRHYTHMIA" |
| `ts` | **event time** (`base + millis`) | *send time*: the backlog piles up in one second, and `smoke_test.py` still passes so it goes unnoticed |
| Advancing the ring | **after PUBACK** | *at send time*: QoS 1 becomes decoration |
| Ring full | **drop the oldest** | *reject the new one*: a monitoring device needs the last minute |
| Credentials | **`.gitignore`d header** | *hardcoded* (leaks) / *`build_flags` in `platformio.ini`* (gets committed) |
| Field names | **snake_case** | *camelCase*, which the ThingsBoard docs suggest: the proposal had already written snake_case and it works normally |

---

## 6. What is deliberately NOT done

- **TLS (port 8883).** The broker runs on the local network for the PoC. Moving the
  broker to a VPS requires TLS and certificates in flash, outside the PoC scope.
- **Subscribe / RPC from the dashboard to the device.** No command needs to
  be sent to the device. `ecg_mqtt.cpp` only publishes.
- **A reboot-surviving backlog.** The ring is in PSRAM, which is volatile, in line with the assumption in
  `bab3.tex` (the wearable is charged routinely; power loss is out of scope).
  LittleFS is already used for raw recordings, so the path is available if
  needed.
- **`ecg_sim.h` with longer/more varied recordings.** Added **only if**
  the dashboard needs it; the `golden_raw` replay suffices for all the
  measurements in §7.
- **Adaptive batching / payload compression.** 1 beat/second × ~300 B is nowhere near
  any limit.

---

## 7. Real numbers

Test condition: N16R8 board, 19 Sep 2026, replay ON (no electrodes), ThingsBoard CE
broker on a laptop on the home WiFi network. Build numbers from `pio run`
on the current code with `wifi_secrets.h` filled in.

| Item | Core build (without MQTT) | Main firmware with MQTT |
|---|---|---|
| `pio test -e native` | 17/17 | **23/23** (+6 payload & ring tests) |
| `pio test -e esp32-s3` | 16/16 | **16/16**: inference is untouched |
| RAM (build) | 21.2% | **37.0%** (121,336 B) |
| Flash (build) | 6.6% | **13.5%** (887,873 B) |
| Payload size, 1 beat | - | ~330 B; batch of 50 beats ~15 KB |
| Backlog | - | **27,000 beats** in PSRAM (1,054 KB, 40 B/entry) ≈ 4–7 hours |

**Build measurement note: do not use RAM/Flash numbers measured without
`wifi_secrets.h`.**
Without that file `WIFI_SSID` is `""`, `strlen("")` is folded into a constant by the
compiler, `WiFi.begin()` becomes dead code, and **the whole WiFi stack is
not linked in**: 26.4% / 8.0%, a difference of 358 KB of flash from the real numbers. The two
builds both look like "SUCCESS" and the difference is announced nowhere.

### Data path, measured

| Item | Number |
|---|---|
| Replay beat rate | **1.60 beats/second** (45 beats / 28.2 s) vs 1.58 measured in HW-7 |
| Rows landing in ThingsBoard | 171 rows / 103.2 seconds, **0 duplicate ts** |
| Gap between `ts` values | **433–911 ms**: not bunched, no gaps |
| Quality gate, without electrodes | `beat 19 (7 aritmia, 19 ditahan)` → **terkirim 0** |
| Quality gate, replay | `ditahan 0` → **terkirim 100%** |
| `sampel hilang` during all tests | **0** |

The accounting `beat − ditahan = terkirim + backlog + hilang` matches at every
status capture. Example: `beat 148 = terkirim 147 + backlog 1 + hilang 0`.

### Retest with the contact gate (22 Oct 2026)

Test condition: N16R8 board plugged into the laptop USB, firmware with the contact gate and
the PSRAM session recorder, WiFi `HIFIAIR_9351` (RSSI −31 dBm), ThingsBoard CE broker
4.2.1.1 on the same laptop (`192.168.1.199:1883`), reference replay source
(`y`), ±5.5 minutes (18.40–18.45 WIB).

| Item | Number |
|---|---|
| Beat / sent / backlog / lost / failed | 536 / 536 / 0 / 0 / 0 |
| Packets ACKed | 518 / 518, PDSR **100.0%** |
| Delay on the device (detection → send) | mean 849 ms, maximum 1,402 ms |
| Maximum PUBACK RTT | 3,329 ms (9 slow events) |
| `sampel hilang` | 0 (tick 0) |

The dashboard *Pemantauan EKG* (ECG Monitoring) shows BPM, classification, confidence, signal quality,
BPM and RR graphs, and the per-beat history live; screenshot
`artifacts/metrics/mqtt/20261022-1845-dashboard-replay.png`.

### Resilience test: `docker pause` for 24 seconds

```
[30,2s] mqtt online    | terkirim  20 | backlog  1 | hilang 0 | gagal 0
[32,3s] === docker pause ===
[54,0s] mqtt no-broker | terkirim  28 | backlog 33 | hilang 0 | gagal 1
[56,1s] === docker unpause ===
[58,2s] mqtt tersambung, backlog 43 beat
[82,8s] mqtt online    | terkirim 109 | backlog  0 | hilang 0 | gagal 1
```

`pause` was chosen, not `stop`: the container freezes so CONNECT is not answered
at all (SYN/packets swallowed), and that tests the connect timeout **and**
CONNACK, more brutal than `stop`, which replies with an instant RST. A practical bonus:
`unpause` recovers in 2 seconds, while `docker start` takes ~55 seconds
waiting for ThingsBoard to boot.

What proves the claim in the proposal: a 24-second outage, but the **maximum gap in the
dashboard time series is only 911 ms**: the backlog fills the hole with the
original `ts`, not the `ts` at send time.

The per-beat latency (26.6 ms) does not change: publication only copies a struct into the
ring; the network is handled by `ecg_mqtt_service()` outside the beat path.

---

## 7b. Six bugs that appear ONLY on hardware

All six passed `pio test -e native` and passed the build. Each bug below shows
why "code that builds" is not "code that is correct"; each bug is written as symptom, cause,
the fix in force in the code, and the measured result.

### (1) Waiting for PUBACK blocks the loop → 4,493 samples lost

Symptom: `antrean 255/256` (full), `sampel hilang 4493`, repeated `PUBACK timeout`.
Cause: `publish()` waits for PUBACK in place with a 3-second limit,
inside the loop that is draining the ADC queue. A 256-sample queue @360 Hz =
**711 ms**, so a single timeout already devours a full queue, and the RR
intervals break, which is exactly the failure the HW-4 architecture was built to prevent.

Fix: PUBACK is picked up **across iterations** of `loop()` (`waiting_ack` +
`poll_incoming()`, 5-second timeout), not inside a single call. In addition, `ecg_mqtt_service()`
is limited to every 20 ms: it is called 360×/second, and `WiFi.status()` + `time()` that
many times eat into the budget of 2,778 µs/sample.

Result: 4,493 → **146**.

### (2) `sock.connect()` is still blocking → 2,788 samples lost while the broker boots

Symptom: `sampel hilang` jumps to 2,788 exactly at `docker start`. Cause:
while the broker is DEAD, connect fails instantly (RST), so there is no loss. But while the
broker is **booting**, its port is open and packets are swallowed, so
`sock.connect()` hangs for ~7.7 seconds.

Fix: `sock.connect(ip, port, 300)`, a 300 ms limit, below the queue
depth of 711 ms. And `IPAddress`, not a hostname: DNS resolution is a **separate**
blocking call that is not bounded by that timeout argument.

Result: 2,788 → **290**. The remaining 290 comes from waiting for CONNACK in place
(1,500 ms). CONNACK is therefore also picked up across iterations (`poll_connack()`,
2-second limit) so that no call waits on the network in
place.

Final result: **0**.

### (3) `sock.write()` without checking the return value → truncated packets

The most deceptive symptom: repeated `PUBACK timeout` **even though the broker is healthy**, and
**only** while the backlog is being drained. The broker log is clean: zero clues on
that side. Cause: the MQTT packet was written in 6 separate calls and the return value
was ignored. With a large payload (16 beats ≈ 4.8 KB) the socket does not hold
everything; a short write leaves the MQTT packet **truncated**, the broker waits for the
rest that never comes, and never sends PUBACK.

So the symptom masquerades as a "slow broker", when it is the sender that
lies about how many bytes were written successfully.

The fix in force in the code:

- One packet is assembled in **one buffer** (`packet_buf`): the payload is written directly
  behind the header space, then the MQTT header is attached backwards right before the
  payload. Two separate buffers (payload + packet) take 32 KB of internal RAM for
  a batch of 50; one buffer takes half.
- `send_all()` repeats `sock.write()` for the remainder that has not been
  written, with a 200 ms limit, below the ADC queue depth of 711 ms. Not
  done within that limit → `gagal++` and `disconnect()`, the backlog is not advanced.
- Because of this staged writing, `ECG_MQTT_BATCH_N` = **50** (~15 KB), the lower
  bound of the `bab3.tex` target of 50–100 records per packet.

Result (resilience test §7): `gagal` stops at 1, the only legitimate one, while the
broker was indeed frozen.

### (4) PINGRESP is never read → the read stream desyncs

The firmware sends PINGREQ every 30 seconds; the broker replies with PINGRESP (2 bytes,
`0xD0 0x00`), which is never read. Those two stray bytes settle in the socket
and are then read as the first two bytes of the next "PUBACK": the read stream desyncs
permanently until reconnect.

Fix: `poll_incoming()` reads the 2-byte header, handles PUBACK, and **discards
the contents of other packets entirely** so the following bytes still land on a packet boundary.

This bug is real and its fix is correct, but it is **not the only cause** of
`PUBACK timeout`: with this fix alone, `gagal` was still 4 in 150 seconds.
The remaining cause is bug (5), which was identified through the RTT counters.

### (5) Nagle holds back small segments → PUBACK late by 1–4.8 seconds

The PUBACK RTT counters (`rtt_max`, `rtt_slow`) and the printout of the socket state at
timeout point in one direction:

```
mqtt: PUBACK lambat 1266 ms (1 beat)      <- berulang di ~1.250 ms
mqtt: PUBACK lambat 1278 ms (1 beat)
mqtt: PUBACK lambat 4235 ms (1 beat)
mqtt: PUBACK timeout, 1 beat terbang, 0 byte menunggu dibaca
                                          ^^^ socket KOSONG = bukan desync
27 kejadian >1 detik dalam 130 detik
```

`0 byte menunggu dibaca` (0 bytes waiting to be read) closes off the desync hypothesis: the broker really has not answered yet.
And the value that **repeats at ~1,250 ms** is the characteristic sign of the Nagle algorithm
paired with delayed-ACK: a small segment (a 1-beat payload of ~330 B) is held
until the ACK of the previous segment arrives.

Fix: `sock.setNoDelay(true)` after connect, one line.

| | without `setNoDelay` | with `setNoDelay` |
|---|---|---|
| `gagal` / 150 s | 4 | **0** |
| latency p95 | 13,259 ms | **3,402 ms** |
| latency maximum | 19,926 ms | **4,903 ms** |
| PDSR | 96.7% | **99.5%** |

### (6) `time()` has 1-second resolution → a systematic 1-second error in EVERY `ts`

This bug does not break the system, but it **breaks all latency measurements**.

`sync_clock()` using `time(NULL)` inherits second resolution. The rounding
goes into `ts_base_ms` and from there into **every** `ts` sent: a systematic error of
0–1,000 ms per boot, constant throughout the session. Its symptom: minimum latency shifted
934 / 1,045 / 1,286 / 1,347 ms between boots with nothing changed in the system, and
once jumped uniformly to 3,437 ms at all percentiles at once.

**A uniform shift across all percentiles is a sign of a clock offset, not
latency.** Real latency shifts the tail more than the median.

Fix: `sync_clock()` uses `gettimeofday()` (µs resolution), and the measuring tool
on the laptop (`dashboard/ukur_pipeline.py`) measures the clock offset of both sides through
`epoch_ms` in the status line and then corrects for it. The measured clock offset was −70 to
−414 ms, and the numbers changed drastically:

| | `time()` | `gettimeofday()` + clock correction |
|---|---|---|
| minimum latency | 1,286 ms | **429 ms** |
| median latency | 1,907 ms | **939–1,108 ms** |

**The same pattern in all six:** they fail without an error, and the symptom points to
the wrong place (the broker, not the firmware). In line with the pitfalls of the `MEAN` op in
TFLM and `float` in the ISR ([`firmware-walkthrough.md`](firmware-walkthrough.md)
§5, §5b), the "wrong without noise" pattern.

The second lesson, specifically from (4) vs (5): **two bugs with identical symptoms can
live side by side.** Fixing one does not remove the symptom, and
the only way out is to install counters until the symptom has a number,
rather than reasoning about which is "most likely".

---

## 7c. `bab3.tex` targets, the table *Rencana pengukuran pada pengujian pipeline* (measurement plan for the pipeline test)

Measured with `dashboard/ukur_pipeline.py` (replay ON, no electrodes): Run 1
and 2 `ukur_pipeline.py 180` on 19 Sep 2026, Run 3 `ukur_pipeline.py 120` on
23 Oct 2026 07.22–07.24 with the final firmware (contact gate, PSRAM session
recorder), WiFi `HIFIAIR_9351` RSSI −40 dBm. Latency = the lower bound of the script output.

| Aspect | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| PDSR | ≥ 95% | **100.0%** (292/292) | **99.2%** (253/255) | **100.0%** (188/188) | pass |
| Median latency | ≤ 2 s | **939 ms** | **1,108 ms** | **1,014 ms** | pass |
| p95 latency | ≤ 2 s | **1,404 ms** (pass) | 3,304 ms (fail) | 2,251 ms (fail) | unstable |
| Minimum latency | - | 429 ms | 527 ms | 495 ms | - |
| Local buffer | ±27,000 | 27,000 attached | same | same | pass |
| Integrity during outage | no loss | `hilang 0` | `hilang 0` | `hilang 0` | pass |
| Buffer recovery | ≤ 60 s | ~24 s (43 beats) | same | same | pass |
| Cloud deduplication | duplicates recognized | 0 duplicate ts | same | 0 (267 unique REST rows = sent 267) | pass |

Run 3 also produced the dashboard screenshot used by the book
(`dashboard/preview.png` = `model/artifacts/metrics/mqtt/20261023-0724-dashboard-replay.png`,
Playwright, 2-minute Realtime window).

### Latency broken down

`tunda alat` (beat OCCURS → beat enters the ring in `publish()`; with an empty backlog,
the ring is drained in ≤ 20 ms) is counted by the firmware and is **stable across 7
measurements**: 887 / 880 / 879 / 878 / 876 / 870 / **869 ms**
(max 1,353 ms).

```
latensi median        ~1.000 ms
  sisi alat              869 ms   <- kadens deteksi
  jaringan + cloud      ~130 ms
```

The device side is **architectural**: `ecg_live.h` runs detection every
`ECG_LIVE_EVERY` = 1 second over a 4-second ring, and a new beat may only come out after
`ECG_WIN_POST` = 128 samples (356 ms) after R. The theoretical lower bound is
356–1,356 ms, and the measured minimum of **429 ms** falls in that range.

So **89% of the latency belongs to the device, and that is the detection cadence, not inefficiency.**
Network + ThingsBoard is only ~130 ms.

### The broker is not a source of latency

ThingsBoard runs on the same laptop as 9 other containers, but the broker
is not slow. A 60-second probe (`dashboard/probe_rtt.py`, publishing 1/second from the
laptop to the SAME broker):

```
RTT PUBACK laptop -> broker, n=60
  minimum 0,4 ms   median 1,1 ms   p95 2,5 ms   maksimum 3,5 ms
  > 1000 ms: 0 dari 60
```

The broker answers in **one millisecond**. The ~1 second latency beyond the device side that
appeared in `time()`-based measurements is the clock error of bug (6); the tail that
remains is WiFi retransmission (below). The lesson: the remote component that is
hardest to measure is also the easiest to blame; a direct probe is cheaper
than a guess.

### The p95 tail: TCP retransmission, and why it is not chased

The PUBACK RTT from the board clusters at **1.2 / 2.0 / 4.2 seconds**, which is the TCP RTO
backoff of 1–2–4, a sign that a segment was lost and then resent. Not the broker (see above),
not desync (`sock.available()` = 0 bytes at timeout), and not a weak signal
(**RSSI −50 dBm**). The rest is home WiFi channel contention.

The effect of firmware settings on the share of packets with RTT > 1 second:

| Setting | slow packets |
|---|---|
| without `setNoDelay` and without `setSleep(false)` | 23/207 = 11.1% |
| `setNoDelay(true)` (bug 5) | 18/222 = 8.1% |
| `setNoDelay(true)` + `WiFi.setSleep(false)` | 11/217 = 5.1% |
| same, run 1 / run 2 §7c | 3/292 = **1.0%** / 24/255 = 9.4% |

That last number **swings 1–9% between runs**, and that is why p95 passes in run
1 and fails in run 2. What swings is not the code but the channel.

`WiFi.setSleep(false)` **has a power cost (~+30 mA)**. Power measurement of WiFi mode
must be taken WITH this setting, because it is the configuration of the main firmware.

**Decision: not chased further.** The only firmware lever left
is to allow more than one PUBLISH in flight (QoS-1 pipelining), and that
adds `pid → jumlah beat` bookkeeping plus the rule "advance the ring only after the oldest
ack" to a simple, proven QoS-1 implementation, a real cost
for a 1-in-20 event on a bench-test network. The median passes in two runs, PDSR
passes, and `bab3.tex` calls its targets **indicative** for a test that is
**functional, not clinical**. If the report needs a clean p95, measure on an AP
that is not congested and report n runs, rather than patching the firmware.

---

## 8. Comprehension check

1. Why is `ecg_mqtt_queue_drop()` separated from `ecg_mqtt_queue_peek()`, and
   what breaks if they are merged?
2. The device loses WiFi for 2 minutes and then recovers. How many beats reach the broker, and
   what time does their `ts` show? How does the answer change if the PSRAM
   allocation fails at boot? (hint: 27,000 vs 64 beats)
3. The electrodes are removed but `m` is still ON. How many are sent to the broker,
   and which numbers in the `'s'` line move?
4. Why does replay not need a special branch to pass the quality gate?
5. `ts_base_ms` is still 0 (SNTP has not arrived) but beats keep coming out. Where do
   those beats go, and what happens when the clock finally syncs?
6. Why does `ecg_mqtt_payload()` return 0 instead of truncating the payload?

---

## 9. Supporting scripts & files

| File | Role |
|---|---|
| `firmware/include/ecg_mqtt.h` | contract; the pure part vs the network part separated by `#ifdef ARDUINO` |
| `firmware/src/ecg_mqtt.cpp` | payload + ring (pure), WiFi + MQTT (board) |
| `firmware/test/test_mqtt/test_mqtt.cpp` | 6 tests: single format, array batch, insufficient buffer, FIFO, full ring drops oldest, attach capacity |
| `firmware/include/wifi_secrets.example.h` | credentials template |
| `dashboard/smoke_test.py` | MQTT wire reference + `ts_kv` dedup test |
| `dashboard/ukur_pipeline.py` | measurer of the §7c targets (PDSR, latency with clock correction, dedup) |
| `dashboard/probe_rtt.py` | PUBACK RTT probe laptop → broker |
| `dashboard/README.md` | field contract, and why ThingsBoard |

## 10. Scope and limits of testing

- **Power.** The power measurement ladder `p0`–`p5` covers WiFi/MQTT mode (`p5`, with
  `WiFi.setSleep(false)` active as in the pipeline test). The numbers do not
  exist yet because the INA219 is not yet in the device's current path
  ([`firmware-walkthrough.md`](firmware-walkthrough.md) §5d).
- **Body signal.** All the numbers in this document were measured with replay. Two things
  can only be tested with a body signal: (a) whether `THRESHOLD_SWING` 60 separates a
  detached electrode from a weak body signal (replay at ~2700 counts is too far above
  the threshold); (b) the **full calibration gate** (60 seconds of contact + 30
  seconds of calm RR) together with its publication, which replay skips because record 208 is
  arrhythmic (§3.1b). The contact gate itself has been tested with a body signal without
  MQTT (§3.1c).
- **p95 latency.** The p95 tail depends on the WiFi channel (§7c). A clean
  re-measurement requires an uncongested AP and a report of n runs. The detection cadence of
  the main firmware is the default `ECG_LIVE_EVERY` = `ECG_FS` (1 second), so
  the beep and the wave on the TFT are delayed 1.46 seconds from R. The build flag
  `-D ECG_LIVE_EVERY=90` runs detection every 250 ms (beep delay 0.7 seconds)
  with equivalent DS1 detection accuracy (Se 0.9881 vs 0.9867, PPV 0.9870 vs
  0.9880) and a detection burst of 7.2 ms per round (2.9% CPU). Changing the default
  of the main firmware is a gate point.
- **Dashboard.** The `ecg_snippet` field is accepted and stored in ThingsBoard,
  but `dashboard/dashboard_ekg.json` has no widget that
  draws it.

Functional tests already covered: telemetry lands at the broker (171 rows,
rate 1.60 beats/second, matching the 1.58 beats/second of the replay) and the resilience test (maximum
gap 911 ms for a 24-second outage), §7.
