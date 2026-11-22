# dashboard/: ThingsBoard CE and pipeline measurement

The MQTT broker, rule engine, and web dashboard are all handled by a single
platform: **ThingsBoard Community Edition**. There is no Mosquitto, no extra
backend, and no custom web app. The reasoning is in `bab3.tex` §deduplikasi
(deduplication section): the claim "dedup without additional components"
depends on the ThingsBoard `ts_kv` behavior, so replacing the broker
invalidates that claim.

## Run

```bash
cd dashboard
docker compose up -d            # boot pertama ~2 menit; UI hidup duluan, REST
                                # baru bisa dipakai setelah skema DB terpasang
python3 smoke_test.py           # bikin device + uji jalur telemetri
python3 provision_dashboard.py  # bikin dashboard + tulis dashboard_ekg.json
```

The UI is at <http://localhost:8080>, login `tenant@thingsboard.org` / `tenant`.

Stop: `docker compose stop` (data is kept). Remove everything: `docker compose down -v`.

ThingsBoard is self-hosted instead of using `demo.thingsboard.io`, because
demo registration is redirected to ThingsBoard Cloud, whose telemetry
retention is limited by plan, and the resilience test needs a controlled
broker disconnect without cutting the laptop's connection. Moving to a VPS
only requires adding a broker entry in the firmware
([network-settings](../docs/features/network-settings.md)).

## Contract with the firmware

| Item | Value |
|---|---|
| Host / port | IP address of the laptop on the same WiFi network as the board, `1883` (plaintext); the laptop IP and SSID are printed by `make broker-info` in `model/` |
| MQTT username | device access token |
| MQTT password | empty |
| Topic | `v1/devices/me/telemetry` |
| Real-time | `{"ts":…, "values":{…}}` |
| Batch flush | `[{"ts":…,"values":{…}}, …]` |
| QoS | 1, ring buffer read pointer advances only after PUBACK |

The fields inside `values` follow the payload structure table (Tabel struktur
payload) in `bab3.tex` §\ref{subsubsec:payload-json}: `bpm`,
`rr_interval_ms`, `label`, `label_str`, `confidence`, `signal_quality`,
`ecg_snippet`.

Note: the ThingsBoard documentation recommends camelCase for key names (it
makes Rule Engine scripts easier). The payload uses snake_case, following the
payload table in Chapter 3, and works normally; hand-written Rule Engine
script nodes must account for this difference.

## Measuring the pipeline test targets

```bash
python3 ukur_pipeline.py 150      # board tersambung, broker hidup
```

Measures two targets from the `bab3.tex` table *Rencana pengukuran pada
pengujian pipeline* (measurement plan for the pipeline test): **end-to-end
latency** (acquisition → available in the API) and **PDSR** (packets with
PUBACK / total packets, taken from the firmware counters over serial, not
guessed from the data). Latency is reported as a lower bound AND an upper
bound, because a row that has only just become visible may have been available
before the REST call was sent; the difference between the two bounds is the
cost of the measurement tool itself, and it is printed too.

The script reads the status (`s`) and then turns on replay (`y`) if it is not
already active; during replay, the warm-up and quiet-RR conditions of the
calibration gate are skipped automatically, so no electrodes are needed. The
measured results are in
[`mqtt-walkthrough.md`](../model/docs/mqtt-walkthrough.md) §7c.

Details of how `ukur_pipeline.py` measures (needs `pyserial`, which is in
`model/requirements.txt`):

- **Idempotent with respect to replay.** `y` is a toggle, so the status is read
  first and `y` is sent only if replay is not on. `k` (gate override) is not
  sent; replay already bypasses the calibration gate in the firmware.
- **The board vs laptop clock offset is corrected.** The script requests the
  status (`s`), records the laptop time when the line arrives, then compares it
  with the `epoch_ms` printed by the board: `ts_laptop = ts_board - offset`.
  Without this correction the clock offset would be read as latency. The
  residual error is the serial cost (~ms).
- **Two latency bounds.** A row becomes visible between the `sebelum` (before)
  and `sesudah` (after) times of the REST call. `sesudah` charges the REST
  slowness to the system (upper bound, including the polling period bias of
  ~100 ms); `sebelum` gives a lower bound free of that. The minimum latency is
  also printed as a lower bound.
- **PDSR from the LAST status line only.** Lines from the clock-offset
  measurement phase still show 0 packets; taking them makes PDSR read 0%.

`probe_rtt.py` uses a separate device so that the `esp32s3-ekg-01` telemetry is
not polluted; its purpose and results are in
[`mqtt-walkthrough.md`](../model/docs/mqtt-walkthrough.md).

`smoke_test.py` tests the ESP32 → broker → `ts_kv` path without hardware and
without dependencies, in order:

1. The device is created through REST and its token is retrieved (provisioning).
2. MQTT CONNECT with username = access token and empty password is accepted.
3. A single-record payload arrives in `ts_kv` with the device's `ts`, not the
   arrival time on the server.
4. A batch payload (array of multiple timestamped key-value entries) is
   accepted by the built-in Save Timeseries node without an additional rule
   chain.
5. Republishing with an identical `ts` (different values) UPSERTs the row
   instead of adding one. This is what happens when a PUBACK is lost and a
   QoS-1 batch is resent, and it is the most fragile claim: if this assert
   fails, the dedup claim in Chapter 3 does not hold. The script waits 2
   seconds before reading because the rule engine is asynchronous.

MQTT 3.1.1 is written directly on top of a socket (CONNECT, PUBLISH QoS 1,
PUBACK, DISCONNECT) instead of using `paho-mqtt`: 60 lines of socket code are
cheaper than a new dependency for a single test script, and it also serves as
a compact reference for the packet sequence the firmware imitates, especially
waiting for PUBACK before advancing the ring buffer read pointer.

## Dashboard

`provision_dashboard.py` builds the dashboard "Pemantauan EKG" (ECG
Monitoring) through REST and then exports the result to `dashboard_ekg.json`.
It is built with a script, not by clicking in the UI, so that it can be
repeated after `docker compose down -v` and so that the diff is visible in
git. The script is idempotent: a dashboard with the same title is deleted
first.

Seven widgets, all built into ThingsBoard, with no custom widgets and no
hand-written JS: BPM card, classification card, signal quality card,
confidence card, BPM chart, R-R interval chart, and history table.

Two pitfalls handled by the script:

- **`typeFullFqn` must be prefixed with the scope**, `"system.time_series_chart"`,
  not `"time_series_chart"`. Without the prefix, REST still saves the dashboard
  with status 200 and complains about nothing; only the UI rejects it, and each
  widget shows "Problem loading widget configuration". For that reason the
  script verifies each fqn through `/api/widgetType?fqn=...` after saving; that
  assert catches a failure that is invisible from REST.
- **The built-in widgets' `defaultConfig` contains a room temperature
  example.** If `units`, `decimals`, and `settings.icon` are not overridden,
  BPM is shown as "76 degC" with a thermostat icon. All overrides are in the
  `WIDGETS` table.

BPM and the R-R interval are deliberately split into two charts. Combined in a
single chart, BPM (60-100) is squashed against the bottom because RR (600-1000)
dominates the axis, and the right-axis configuration (`yAxisId`) does not stick
through REST. Two charts auto-scale on their own without extra axis
configuration.

The card widgets (latest value) use their own timewindow and do not follow the
dashboard timewindow; the timeseries widgets do follow it. Each widget's
`defaultConfig` is copied per widget (not shared), and the default `yAxes` axis
(`default`) is not removed.

## Rule chain

None. The **Save Timeseries** node in the default Root Rule Chain already
accepts the multiple timestamped key-value array format as is, using each
record's `ts` as the event time. A new rule chain export is needed only if an
alarm rule (early notification) is added.

## Multi-patient (outside the MVP scope)

The MVP uses one device for one patient. Design notes for an extension:

ThingsBoard stores each `ts_kv` row as owned by an **entity**, and the entity is
the device. So if one device is used by several patients in turn, the patient
identity must move together with the data. Two ways, with very different
costs:

- **Patient = Customer, the device stays a single device.** The patient identity
  is written as a server-side attribute that is replaced each session. Zero
  firmware changes, but old history "moves" to the new patient when the
  attribute is replaced, which is wrong for medical records.
- **`patientId` becomes one field inside `values`.** Each record carries its own
  owner, history stays correct retroactively, and the rule chain can use the
  Change Originator node to split into per-patient Assets without touching the
  firmware again. The cost is ±10 bytes out of ±150 bytes per record, which
  means the PSRAM ring buffer capacity drops by about 7% (±27,000 → ±25,000
  records), still far above the 4-hour target.

The second way is the one chosen for the extension, and a single field is
enough. This field is absent from the MVP because there is only one patient and
the payload table in Chapter 3 does not include it.
