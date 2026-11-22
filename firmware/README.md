# firmware/: ESP32-S3 program (PlatformIO)

Firmware of the ECG monitor: AD8232 acquisition at 360 Hz, on-device
preprocessing and R-peak detection, per-beat arrhythmia classification with
TFLite Micro (INT8 model from `model/`), TFT display, beat beeps, and
publication to ThingsBoard over MQTT. How each part works is in the feature
pages under [`docs/features/`](../docs/features/architecture.md); this page is
the quickstart.

Board: ESP32-S3 N16R8 (16 MB flash, 8 MB PSRAM), PlatformIO board id
`4d_systems_esp32s3_gen4_r8n16`, on PCB rev1. The whole configuration is in
[`platformio.ini`](platformio.ini); every command runs from this folder. Pin
map and circuit rationale: `hardware/mainboard/README.md`.

## PlatformIO environments

| Env | Purpose | Sources built | Libraries |
|---|---|---|---|
| `esp32-s3` (default) | Main firmware and on-board tests | all of `src/` | Chirale_TensorFLowLite, Adafruit ST7735/ST7789, Adafruit GFX |
| `native` | Unit tests on the PC, no board | `ecg_pipeline.cpp`, `ecg_live.cpp`, `ina219.cpp`, `ecg_mqtt.cpp` | none |

`esp32-s3` builds with `-I test` because `test/golden_ref.h` is the reference
replay source. Detection runs every `ECG_LIVE_EVERY` samples, default `ECG_FS`
(once per second); `-D ECG_LIVE_EVERY=90` is available as an ablation knob.

Notes on `platformio.ini`:

- `default_envs = esp32-s3` is required. Without it a plain `pio run` also
  links `native`, which has no `main()`, and fails with
  `undefined reference to main`.
- The board profile already carries `-DBOARD_HAS_PSRAM`; the flag is not
  repeated.
- `build_src_flags` fills `GIT_VERSION` from `git describe --always --dirty`
  (shown in Menu > Info). The flag applies only to `src/`, so libraries are not
  recompiled on every commit.
- Chirale_TensorFLowLite uses the reference kernels (no ESP-NN); the inference
  latency figures in this repo are reference-kernel baselines.
- The ST7789 is initialised with `SPI_MODE3` because CS is tied to GND.
- `test_build_src = yes`: the suites build `src/`; `main.cpp` is empty under
  `PIO_UNIT_TESTING`, so each suite has its own `setup()`/`loop()`.
- Serial runs over the S3 built-in USB JTAG/serial; USB-CDC is not enabled. If
  `pio device monitor` shows nothing, add
  `-D ARDUINO_USB_CDC_ON_BOOT=1 -D ARDUINO_USB_MODE=1` to `build_flags` of
  `esp32-s3`.

## Commands

```bash
pio run                                  # build env esp32-s3
pio run -t upload                        # build and flash the main firmware
pio device monitor                       # serial 115200
pio test -e native                       # 23 tests on the PC: test_preproc, test_ina219, test_mqtt
pio test -e esp32-s3                     # 29 tests on the board: test_preproc, test_inference, test_hw_*
pio test -e esp32-s3 -f test_hw_buzzer   # one suite only
pio test -e esp32-s3 -v                  # plus Serial output (benchmarks, device readings)
pio device list                          # check the port
```

The port moves between `/dev/ttyACM*` and `/dev/ttyUSB*`; do not hard-code it.
Serial commands for driving the board without buttons are listed in
[serial-commands](../docs/features/serial-commands.md).

## Tests

`native` runs the signal-path, INA219 conversion and MQTT payload suites
against `test/golden_ref.h` on the PC. `esp32-s3` adds the TFLM inference suite
and the `test_hw_*` device suites, which share the `diag_*` functions with the
on-device menu "Tes perangkat" (device test). Suite contents, pass criteria and
counts: [diagnostics](../docs/features/diagnostics.md).

## Structure

| Code | Feature page |
|---|---|
| `src/main.cpp`, `src/menu.cpp` (wiring) | [architecture](../docs/features/architecture.md) |
| `src/acquisition.cpp`, `src/board.cpp` | [acquisition](../docs/features/acquisition.md) |
| `src/ecg_pipeline.cpp`, `src/ecg_live.cpp` | [signal-pipeline](../docs/features/signal-pipeline.md) |
| `src/classifier.cpp` | [classification](../docs/features/classification.md) |
| `src/gate.cpp` | [calibration-gate](../docs/features/calibration-gate.md) |
| `src/display.cpp` | [display-and-buzzer](../docs/features/display-and-buzzer.md) |
| `src/buttons.cpp`, `src/menu.cpp` | [buttons-and-menu](../docs/features/buttons-and-menu.md) |
| `src/recorder.cpp` | [recording](../docs/features/recording.md) |
| `src/app_settings.cpp`, `include/wifi_secrets.example.h` | [network-settings](../docs/features/network-settings.md) |
| `src/serial_cmd.cpp` | [serial-commands](../docs/features/serial-commands.md) |
| `src/ecg_mqtt.cpp` | [mqtt-telemetry](../docs/features/mqtt-telemetry.md) |
| `src/power.cpp`, `src/ina219.cpp` | [power-measurement](../docs/features/power-measurement.md) |
| `src/diagnostics.cpp`, `test/test_*` | [diagnostics](../docs/features/diagnostics.md) |
| `include/model_int8.h`, `include/ecg_preproc.h`, `test/golden_ref.h` (GENERATED) | [model-pipeline](../docs/features/model-pipeline.md), [`include/README.md`](include/README.md) |

## Pitfalls

Board-proven behavior that is easy to break and not covered by a single
feature page. Pitfalls owned by one feature are on its page.

**Device** (pin order and lead-off pull-ups: [acquisition](../docs/features/acquisition.md))

- `tft.init()` calls `SPI.begin()` again after `board_begin` has started the
  bus, but `SPIClass::begin()` returns at once when the bus is already up, so
  the SPI-before-buzzer order survives the TFT init.
- The buzzer module is active LOW (LOW = sound, HIGH = silent).
  `attach_buzzer` drives the pin HIGH with `digitalWrite` before LEDC takes it
  over, because an unset pin can read LOW to the module and beep at boot. The
  LEDC channel uses `LEDC_TIMER_0` (the timer `ledcSetup` configures) with
  `output_invert = 1`, so `ledcWriteTone(channel, TONE_IDLE)` (duty 0) gives
  HIGH = silent while the square wave still sounds.
- `TONE_HZ` (`board.h`, 2000 Hz) is a knob: a passive buzzer is loudest at its
  resonant frequency, which differs per part.
- LO+/LO- do not drive the LED. LO only reports a fully detached electrode, and
  on 3 leads without a tight RL electrode it stays on even with a good signal;
  the LED follows the gate phase, which uses the cleaned swing
  ([acquisition walkthrough](../model/docs/acquisition-walkthrough.md) §2).
- `neopixelWrite()` disables interrupts for about 30 µs per call, so the LED is
  refreshed at most every `PERIOD_LED_MS` (250 ms), not every loop pass.
- The display cannot be read back (CS to GND, no MISO). `diag_screen` judges SPI
  from the duration of a full `fillScreen` (320 x 172 x 2 B = 110 KB, at least
  11 ms even at 80 MHz); below `FILL_MIN_US` (5 ms) nothing was transferred.
- INA219: an absent module answers `0x0000` or `0xFFFF`, so `ina219_begin`
  writes the configuration and reads it back to tell "not fitted" from 0 mA.
  One 128-sample averaged result takes about 68 ms; `power_service` reads every
  100 ms. The on-chip calibration register is unused: `R_SHUNT` divides in
  software and is the calibration knob against a multimeter
  ([firmware walkthrough](../model/docs/firmware-walkthrough.md) §5d).

**Acquisition and pipeline**: ISR, queue, lost ticks and replay are in
[acquisition](../docs/features/acquisition.md); beat emission, Pan-Tompkins
initialisation and z-score in [signal-pipeline](../docs/features/signal-pipeline.md);
quality swing, clipping and RR entry criteria in
[calibration-gate](../docs/features/calibration-gate.md). Measured load:
section Measurements.

**TFLite Micro**: input order, arena placement, resolver and `ErrorReporter`
are in [classification](../docs/features/classification.md).

**Network and clock** (MQTT time budgets and `configTzTime`:
[mqtt-telemetry](../docs/features/mqtt-telemetry.md))

- The radio is stopped for the power sweep with `esp_wifi_stop()` and
  `esp_wifi_start()`, not `WiFi.mode(WIFI_OFF)`: the latter also deinitialises
  the driver and races the WiFi task (`LoadProhibited` panic on core 0)
  ([firmware walkthrough](../model/docs/firmware-walkthrough.md) §5d).
- `sock.setNoDelay(true)` (`TCP_NODELAY`), `WiFi.setSleep(false)`, reading
  PINGRESP and `gettimeofday()` instead of `time()` in `ecg_mqtt.cpp` each
  prevent a fault that appears only on the board
  ([mqtt walkthrough](../model/docs/mqtt-walkthrough.md) §7b).
- `Preferences::begin(NS, NOT_READ_ONLY)` is used for reads too, because
  read-only mode fails when the namespace does not exist yet; write mode
  creates it.

**LittleFS** (no flash writes during a session: [recording](../docs/features/recording.md))

- File existence is checked with `stat()`, not `LittleFS.exists()`, and
  directories (`/rekam`, `/daya`) are created with `mkdir` before they are
  opened: `exists()` and `open()` on a missing path print `[E]` to serial.
- A recording is loaded for replay in `READ_BLOCK` (512 B) blocks and parsed by
  hand; `readStringUntil` per line is too slow for 108,000 lines.

## Deliberate limits

Limits that span more than one feature. Limits of a single feature are on its
page.

| Limit | Effect | If it must change |
|---|---|---|
| The recording session lives only in PSRAM until it stops | Power loss or reset mid-session loses the whole session, not just the last part | Saving to flash mid-session needs an IRAM-safe acquisition ISR (ADC read without `adc1_get_raw`, replay from internal RAM) |
| Writing files after a session holds the acquisition ISR | The live path loses samples while each part is written (counted in `sampel hilang`, see Measurements); RR and beat classification in that window are not valid | Same as the row above |
| The beep schedule uses the sample clock already processed by `ecg_live` | During a detection burst a beep is late by at most the burst length (about 33 ms) | Use the index of the sample entering the queue |
| The menu recording list holds 64 entries (`recorder_list(rec_no, 64)`, serial `LIST_MAX`) | Display limit only; a new file number still comes from a full scan | none needed |
| Choosing a WiFi entry during power modes `p0` to `p4` | `settings_choose_wifi` calls `ecg_mqtt_begin()`, so the radio comes back on | Choose the network in normal operation |

## Measurements

Measured values that the code cannot prove. Each row carries its measurement
condition.

| Quantity | Value | Condition | Source |
|---|---|---|---|
| Processing load per sample | mean 82 µs of a 2,778 µs budget (3.0 %); burst peak 33,428 µs when 4-second detection and inference coincide; the burst needs 13 samples of queue, so `QUEUE_N` = 256 (711 ms) | `pio test -e esp32-s3 -f test_inference -v`, board N16R8, 12 Sep 2026 | [firmware walkthrough](../model/docs/firmware-walkthrough.md) §5b |
| Float in the ISR | `Coprocessor exception` panic after 18.49 s | float conversion inside `on_timer`, board N16R8 | [firmware walkthrough](../model/docs/firmware-walkthrough.md) §5c |
| Reference replay amplitude | R peak about 3,550 counts after `SCALE_REPLAY` 1000 counts/mV + `OFFSET_REPLAY` 2048, below the 4095 rail | `golden_raw`, record 208 | [firmware walkthrough](../model/docs/firmware-walkthrough.md) §5c |
| Ticks lost to flash writes | 52, 55 and 53 lost ticks per 18 KB file written while recording; 313 when six 18 KB files are written after the session; 11 when four files are deleted | board N16R8 on PCB rev1, 21 Oct 2026, `count_lost_ticks` | this page |
| RR distortion from mid-session writes | RR compressed by about 40 % for about 4.7 s at the start of each continuation file | 21 Oct 2026 session, firmware that wrote files mid-session | [recordings README](../model/data/recordings/README.md) |
| Inference | 26.6 ms per beat at 240 MHz, reference kernels; tensor arena 12,948 B of 24,576 B allocated | `test_inference`, board N16R8, window 256, 18 Sep 2026 | [firmware walkthrough](../model/docs/firmware-walkthrough.md) §6 |
| Op resolver | `AllOpsResolver` adds about 100 KB of flash over the 8-op `MicroMutableOpResolver` | main firmware build, Chirale_TensorFLowLite, value recorded 13 Oct 2026 | this page |

### LittleFS capacity

The LittleFS partition is the `spiffs` entry of the board's default partition
table `default_16MB.csv` (offset `0xC90000`, size `0x360000` = 3,456 KiB). On an
empty file system LittleFS reports 36 KiB used (serial `l`, 21 Oct 2026). One
part reserves `FULL_FILE_SPACE` = 108,000 samples x 6 B = 648,000 B (a real
300 s file is about 540 KB):

| Starting state | Free space | Parts that fit | Maximum session |
|---|---|---|---|
| no recordings | 3,420 KiB = 3,502,080 B | 5 | 1,500 s |
| one 300 s file (about 527 KiB) left | about 2,893 KiB | 4 | 1,200 s |

A different partition table changes these numbers; the session limit itself is
computed at start ([recording](../docs/features/recording.md)).

### Battery supply and WiFi

The board WiFi is deliberately OFF (NVS switch "Jaringan > WiFi aktif", serial
`m`) until the battery converter output is set to 5.0 to 5.1 V; the open item
is in [`model/CLAUDE.md` §Open work](../model/CLAUDE.md#open-work). The
converter output (about 4.x V) feeds the board 5V pin and then the board 3.3 V
regulator.

Observed with that battery build, 14 Oct 2026: the board resets about every
2.5 s right after `WiFi.begin()`, the screen never lights up, and the 600 ms
calibration beep is cut by the reset so it sounds broken (9 resets per 20 s
with WiFi, 0 without; a 7-minute power sweep from the battery without WiFi ran
with no reset). The cause has not been measured with a multimeter. This is why
the WiFi switch and network changes are refused during a recording session
([network-settings](../docs/features/network-settings.md)).

Checks on the assembly:

1. Identify the 3.3 V regulator on the N16R8 board (package marking or board
   schematic), read its dropout at WiFi burst current in the datasheet, and
   compare with the converter output under load. A thin margin shows as a
   `Brownout detector was triggered` reset while WiFi is active (mode `p5`).
2. If the path from the 5V pin to the regulator passes a diode (check the board
   schematic), its drop reduces the margin further.
3. Measure the 3V3 pin with a multimeter while `p5` runs; it must stay near
   3.3 V.

## Feature pages

[architecture](../docs/features/architecture.md) ·
[acquisition](../docs/features/acquisition.md) ·
[signal-pipeline](../docs/features/signal-pipeline.md) ·
[classification](../docs/features/classification.md) ·
[calibration-gate](../docs/features/calibration-gate.md) ·
[display-and-buzzer](../docs/features/display-and-buzzer.md) ·
[buttons-and-menu](../docs/features/buttons-and-menu.md) ·
[recording](../docs/features/recording.md) ·
[network-settings](../docs/features/network-settings.md) ·
[serial-commands](../docs/features/serial-commands.md) ·
[mqtt-telemetry](../docs/features/mqtt-telemetry.md) ·
[power-measurement](../docs/features/power-measurement.md) ·
[diagnostics](../docs/features/diagnostics.md) ·
[model-pipeline](../docs/features/model-pipeline.md)

Deep dives: [firmware walkthrough](../model/docs/firmware-walkthrough.md)
(preprocessing port and TFLM), [mqtt walkthrough](../model/docs/mqtt-walkthrough.md)
(publication, PDSR, latency), [acquisition walkthrough](../model/docs/acquisition-walkthrough.md)
(recording body signals).
