# Crosscheck of the power measurement plan against standards and literature

Condition: measurement plan in `firmware/README.md` §Measurements "Battery supply and WiFi", `model/docs/firmware-walkthrough.md` §5d,
`firmware/src/power.cpp`, `firmware/src/ina219.cpp`, `firmware/include/ina219.h` (read 1 Nov 2026).
Configuration in force now: `INA219_CONFIG = 0x3FFF`, read every 100 ms
(`PERIOD_READ_INA219_MS`) without checking the CNVR bit, mean per 10 s window, 1 transient window
dropped, 6 windows per level, one ladder run.

Markers: **[TL]** = full text read, **[A]** = abstract/metadata only, **[INF]** = my
inference from the source, not a sentence of the source.

## 0. Key technical findings (basis of the table)

1. **0x3FFF = PGA ÷8, BADC 128 samples, SADC 128 samples, MODE 111 (shunt and bus, continuous).** INA219
   datasheet p. 9: in mode 111 the device *"continuously converts the shunt voltage up to the number set
   in the shunt voltage averaging function ... The device then converts the bus voltage up to the number
   set in the bus voltage averaging"*. P. 10: *"when configured for 12-bit and 128 sample averaging, up
   to 68 ms in time between sampling these two values is possible"*. Table 5 p. 20: 128 samples = 68.10 ms.
   **[INF]** One cycle = 68.10 ms shunt + 68.10 ms bus = 136.2 ms, so the shunt current is only
   integrated about 50% of the time. The mean stays unbiased as long as the load is not synchronous with the INA219
   cycle, but half of the energy is never seen.
2. **Reading every 100 ms is not synchronous with the 136.2 ms result.** **[INF]** In 10 s there are only about 73 new results
   for 100 reads (`n=101` in the log), so about 27% of the reads are duplicates. The `sd` per window is computed
   from the duplicated readings and is not the uncertainty of the mean. CNVR (bit 1 of the bus register) marks a new
   result and is cleared by reading the Power Register (datasheet p. 23).
3. **The INA219 ADC integrates, it does not sample a point.** P. 11: *"The internal ADC is based on a
   delta-sigma (ΔΣ) front-end with a 500-kHz (±30%) typical sampling rate."* **[INF]** So the Nyquist
   worry "532 µs vs µs/ms spikes" does not apply to the AVERAGE: each 12-bit conversion is the average
   of a 500 kHz modulator over 532 µs, and 128 consecutive conversions cover 68.10 ms without gaps. What
   cannot be measured is the spike PEAK. Banbury 2021 p. 13 supports the same logic for EMON:
   *"Since these internal sampling rates are typically well-within the time constant of the decoupling
   DUT's power delivery decoupling capacitance, the rate has no impact on the score."*
4. **Cheap fix [INF]:** set BADC to a single 12-bit (532 µs), SADC stays 128: config **0x39FF**.
   Shunt coverage = 68.10 / (68.10 + 0.532) = 99.2%. Read only when CNVR = 1 (polling ≤ 10 ms), then read the
   Power Register to clear CNVR, so each result enters exactly once. Alternative: MODE 101
   (shunt only, continuous) = 100% coverage, and the bus voltage is read once per window by switching mode
   briefly. The cell voltage changes slowly, so a 532 µs bus is enough. This touches `include/ina219.h` and
   `power.cpp`, so `test_ina219` and `test_hw_ina219` must be rerun.
5. **ESP32-S3 WiFi current (datasheet v2.2, Table 5-7 p. 66, at 3.3 V, 25 °C):** TX peak 340 mA
   (802.11b 1 Mbps @21 dBm), 283–291 mA (g/n), RX 88–91 mA. Modem-sleep current at 240 MHz WAITI = 32.9/47.6 mA
   (Table 5-9 p. 67). ESP-IDF guide "Low Power Mode in Wi-Fi Scenarios" (ESP32-S3, v6.1): 160 MHz,
   WIFI_PS_MIN_MODEM, DFS OFF, DTIM1 = average 40.1 mA, max 235.8 mA, min 37.8 mA. **[INF]** The
   peak/average ratio of about 6 shows a very spiky current, so full-time coverage (item 4)
   matters more than the sampling rate. The "+30 mA" estimate for `setSleep(false)` in the plan is
   unsourced. The datasheet gives RX ≈ 88 mA against modem-sleep 33–48 mA at 240 MHz; this is a rough hint
   that the increase can be larger. Measure, do not estimate.
6. **No verified medical standard sets a power/battery life threshold** (section 1, row 12).

## 1. Crosscheck table

| # | Our plan | Standard/literature practice (source + page/table) | Status | Concrete suggestion |
|---|---|---|---|---|
| 1 | Tool: INA219 module read by the ESP32 itself over I2C (0.1 Ω shunt, 12-bit) | MLPerf Tiny/EnergyRunner use an external EMON: ST LPM01A, Joulescope JS110, Keysight N6705 (Banbury 2021 p. 13; EnergyRunner README §Energy Mode Hardware). LPM01A max 50 mA (README, BOM), so unsuitable for an ESP32 with WiFi. Espressif recommends Joulescope or Nordic PPK2 (ESP-IDF "Current Consumption Measurement of Modules"). An INA monitor on an ESP32-S3 board is used in peer-reviewed papers: INA226 on the 3V3 rail (Moura 2026 p. 11). On-device measurement is usually < 10 kHz and validated against an external profiler (Otii, 50 kHz) (Müller 2024 p. 4, 11). | Different but defensible | Keep the INA219 for the AVERAGE current per mode. State explicitly that spike peaks are not measured. If the lab has a PPK2/Joulescope/oscilloscope + shunt, use it once to validate the `p0` and `p5` means (row 9). |
| 2 | Config 0x3FFF (shunt + bus continuous, 128/128), read every 100 ms without CNVR | INA219 datasheet p. 9–10, Table 5 p. 20, CNVR p. 23 (section 0 items 1–2) | **Lacking** | Change to 0x39FF (bus 532 µs, shunt 128 samples), poll CNVR, take each result exactly once. Coverage rises from about 50% to 99.2%, with no duplicates. Report `n` as the number of conversions (about 145 per 10 s). |
| 3 | 10 s mean against WiFi spikes (hundreds of mA, ms order) | ΔΣ 500 kHz (INA219 p. 11). The EMON rate does not affect the score because of decoupling capacitors (Banbury p. 13). External profiler ≤ 250 kHz because the power trace is already filtered by on-board capacitance (Müller p. 4). Comparison: an oscilloscope at 5.16 kHz behind a Current Ranger with a 7 kHz LPF recorded ESP32 MQTT max 254–381 mA, average 52–57 mA (Álvarez-Rosado 2022 p. 5–7, Table 3). | Conforms for the mean (after row 2 is fixed); cannot measure peaks | Report only the mean. Cite the peak current from the datasheet (Table 5-7) as a supply design reference, not as a measured result. Check the OVF bit in every window and note it if it was ever 1. |
| 4 | Battery side (between TP4056 OUT+ and the converter), includes converter losses | EEMBC/MLPerf: one fixed-voltage supply, and only the power to the DUT is measured: *"Only the power delivered to the core is measured. Furthermore, only one power supply is allowed"* (Banbury p. 13). SMPS efficiency is named as a variable (p. 13). Li 2020 measures only the SoC at 2.85 V (p. 3). Moura measures the 3V3 rail (p. 11). Álvarez-Rosado: supply voltage 3.7/5/9 V changes the energy per cycle 27.43 → 60.28 mJ (Table 5, p. 7). | Different but defensible | The battery side is right for battery life and system consumption. (a) Make **power (mW)** the main metric, because the current on the cell side rises when the cell V falls. (b) For the `p0`–`p5` ladder, replace the cell with a **fixed 3.7 V bench supply** at the TP4056 OUT+ point so repeats are comparable, and use the cell only for the drain-the-battery test. (c) State that the difference between stages includes the converter η. |
| 5 | Standalone ladder from the battery without USB; the laptop path through a cable without VBUS | EnergyRunner: the DUT is electrically isolated from the host through an IO Manager + level shifter, and the level shifter is powered from an unmeasured channel. *"Only ONE power supply is allowed to supply the DUT during measurement"* (README §Energy Mode Hardware). | Conforms (standalone ladder); laptop path less clean | Official figures from the standalone ladder only. The laptop path shares GND and D+/D− with the host, so it is used only for debugging. State that the INA219 module (powered from the board 3V3, max IQ 1 mA, INA219 p. 1) is counted too. |
| 6 | 60 s per level after dropping 1 transient window | MLPerf: *"run inference for a minimum of 10 seconds and 10 iterations"* (Banbury p. 8). There are warm-up iterations before the timestamp (EnergyRunner README). Moura: 5 warm-ups (p. 11). | Conforms | Keep. At `p3`, about 17 beats per 10 s × 6 windows ≈ 100 inferences per level, so the ≥ 10 iterations requirement is met. |
| 7 | One ladder run, no repeats | MLPerf: median of 5 runs (Banbury p. 8). Akbari 2025: N = 30 trials × 20 inferences, mean ± sd (§2.6). Moura: median of 60 runs + 95% CI (p. 11–12). Lambert 2021: t-test/Mann–Whitney between conditions (§3.5). | **Lacking** | Run the ladder ≥ 5 times under a fixed condition (bench supply, temperature noted). Report the median and range (or mean ± 95% CI) of the per-ladder means. The difference between stages is computed per repeat and given a CI. |
| 8 | Validity criterion: current rises > 2 × sd (sd of the 100 ms readings) | The statistics above use the spread of the mean between runs/repeats, not the spread of raw samples. | Lacking (minor) | Separate "valid measurement" (bus V, `lewat = 0`, `beat > 0`, OVF = 0) from "difference detected". A difference whose CI contains zero is reported as "not distinguishable at X mA resolution", not "invalid". |
| 9 | Calibration: one point, multimeter in series current mode at one mode, correct `R_SHUNT` | Datasheet: current error ±0.2% typical, ±0.5% max (INA219A), PGA ÷8 offset ±40 µV typical, ±200 µV max (A) / ±100 µV (B) (p. 5), that is ±0.4 mA typical and ±1–2 mA max at 0.1 Ω. Module shunt: *"0.1 Ω sense resistor, with 1% gain error"* (Lambert 2021 p. 8). Espressif: ordinary ammeters *"have a relatively high internal resistance, resulting in a significant voltage drop"* (ESP-IDF guide). Prasetyawati 2023 calibrates the INA219 with resistor/DC lamp loads against a DMM, linear regression, MAPE. Accuracy of the shunt voltage channel 93.71% vs load voltage 99.27% (p. 1). Müller: linear regression against a reference instrument is common (p. 4). | **Lacking** | (a) Measure the zero offset: load path disconnected, record the shunt mean for 60 s, subtract. (b) Calibrate the gain with **power resistor loads** (stable DC) at 3 points spanning the range of the instrument (e.g. about 100, 200, 400 mA) against a DMM, then linear regression I_ref = a·I_ina + b. Report a, b, R² and the residual error. (c) Do not put a DMM in series on a spiky ESP32, because the burden voltage and the DMM averaging are unknown. |
| 10 | Metrics: mean mA and mW per mode; no energy per inference or battery life yet | MLPerf: *"measure the total energy used in the timing window and compute micro-Joules per inference"* (Banbury p. 8). Akbari 2025: 3,532 ± 6 µJ per inference = P × latency (§3.3). Moura: net energy = E_gross − P_idle·T (eq. 8a–8b, p. 11). Battery life: t = capacity (mAh) / load current (mA) (Álvarez-Rosado eq. 1, p. 7, no derating). Zambrano 2026: 40 mA via DMM, *"does not include detailed profiling of transient or peak power consumption"* (p. 17). | **Lacking** | (a) **Energy per inference (µJ)** = (P_p3 − P_p2) · T_window / N_beat per window, plus a cross-check of latency (`test_inference`) × ΔP. Note that `loop()` does not sleep, so this figure is the extra cost on an already active CPU. (b) **Battery life**: a drain-the-battery test directly in mode `p5` (full cell → reset/brownout, record hours) as the main figure. The formula E_cell / P_mean only as a comparison. I did not find a derating factor in an official source, so do not cite one without a source. |
| 11 | `p5` = `setSleep(false)`, estimated +30 mA | ESP32-S3 datasheet Tables 5-7/5-9 (p. 66–67) and the ESP-IDF low-power Wi-Fi table (section 0 item 5) | Lacking (unsourced assumption) | Remove the +30 mA figure from the plan document; let it be measured. State that `setSleep(false)` equals normal operation in the firmware (`ecg_mqtt.cpp`), so `p5` = operational consumption. |
| 12 | No threshold / standard | IEC 60601-1-11:2015 has §8.5 "Additional requirements for an INTERNAL ELECTRICAL POWER SOURCE", §8.5.1 "Indication of state" (table of contents, iTeh sample p. 5). The clause text could not be read (paywall). IEC 60601-2-47:2012 (ambulatory ECG systems) is not accessible. A 24-hour duration requirement is NOT verified. | No verified requirement | Do not claim conformance to a standard. Report "measured operating time" from the drain-the-battery test. If a link to the 24-hour Holter is wanted, a clinical/standard source that was actually read is needed. |
| 13 | Temperature and cell condition not recorded | ESP32-S3 datasheet: measured at 3.3 V, 25 °C (p. 66). Moura: 25 ± 2 °C, CPU locked at 240 MHz, radio off during inference (p. 11). | Lacking (minor) | Record the room temperature, start/end cell voltage, firmware version (commit), CPU frequency, and WiFi AP/RSSI for `p5` in the CSV or metadata. |

## 2. Source list

| Proposed key | Title | Authors | Year | Venue | DOI | Scopus ID | Status | Path |
|---|---|---|---|---|---|---|---|---|
| banbury_2021 | MLPerf Tiny Benchmark | C. Banbury et al. | 2021 | NeurIPS Datasets & Benchmarks (arXiv:2106.07597v4) | 10.48550/arXiv.2106.07597 | – | TL | `laporan/pustaka/belum-dirujuk/riset-pengukuran/tinyml/banbury_2021.pdf` |
| eembc_energyrunner | EnergyRunner benchmark framework (README, user guide) | EEMBC | 2021– | github.com/eembc/energyrunner | – | – | TL | `.../riset-pengukuran/tinyml/eembc_energyrunner_README.md` |
| mlperftiny_rules | MLPerf Tiny Inference Rules | MLCommons | – | github.com/mlcommons/tiny | – | – | TL (does not contain energy method details; refers to the runner) | `.../tinyml/mlperftiny_rules.adoc`, `.../tinyml/mlperftiny_runner_README.md` |
| ti_ina219 | INA219 Zerø-Drift, Bidirectional Current/Power Monitor With I2C Interface (SBOS448G) | Texas Instruments | 2015 | datasheet | – | – | TL | `.../riset-pengukuran/daya/ti_ina219_2015.pdf` |
| ti_ina226 | INA226 (SBOS547C) | Texas Instruments | 2026 (rev.) | datasheet | – | – | TL, used only for the alternative (conversion 140 µs–8.244 ms, averaging up to 1024, gain error 0.1% max) | `.../daya/ti_ina226_2026.pdf` |
| espressif_2026 | ESP32-S3 Series Datasheet v2.2 | Espressif | 2026 | datasheet | – | – | TL | `laporan/pustaka/espressif_esp32s3_datasheet.pdf` |
| espidf_current | Current Consumption Measurement of Modules (ESP32-S3, ESP-IDF v6.1) | Espressif | 2026 | web documentation | – | – | TL | `.../daya/espidf_current_measurement.html/.txt` |
| espidf_lowpower_wifi | Low Power Mode in Wi-Fi Scenarios (ESP32-S3, ESP-IDF v6.1) | Espressif | 2026 | web documentation | – | – | TL | `.../daya/espidf_lowpower_wifi.html/.txt` |
| akbari_2025 | Atrial Fibrillation Detection on the Embedded Edge: Energy-Efficient Inference on a Low-Power Microcontroller | Y. Akbari, ..., O. Faust | 2025 | Sensors 25(21):6601 | 10.3390/s25216601 | 105021612220 | TL (XML Europe PMC PMC12608751; MDPI PDF blocked) | `.../daya/akbari_2025.xml/.txt` |
| moura_2026 | On-Device Edge AI for Monthly Energy Forecasting on ESP32-S3 Using 3-Day Windows | G. A. Moura et al. | 2026 | IEEE Access 14 | 10.1109/ACCESS.2026.3658109 | 105029005786 | TL | `.../daya/moura_2026.pdf` |
| muller_2024 | TinyEP: TinyML-Enhanced Energy Profiling for Extreme Edge Devices | K. Müller, J. Weidner, N. Franchi, P. Wägemann | 2024 | IEEE Access 12 | 10.1109/ACCESS.2024.3520089 | 85212574653 | TL | `.../daya/muller_2024.pdf` |
| alvarez-rosado_2022 | Energy consumption of an internet of things development board | G. L. Álvarez-Rosado et al. | 2022 | Revista de Ciencias Tecnológicas 5(4):e234 | 10.37636/recit.v5n4e234 | – (not checked for indexing) | TL | `.../daya/alvarez-rosado_2022.pdf` |
| prasetyawati_2023 | Calibration and Validation of INA219 as Sensor Power Monitoring System using Linear Regression | F. Y. Prasetyawati, D. Harjunowibowo, A. Fauzi, B. Utomo | 2023 | AIUB J. Sci. Eng. 22(3) | 10.53799/AJSE.V22I3.595 | 85181943451 | TL | `.../daya/prasetyawati_2023.pdf` |
| lambert_2021 | Power Consumption Profiling of a Lightweight Development Board: Sensing with the INA219 and Teensy 4.0 Microcontroller | J. Lambert, R. Monahan, K. Casey | 2021 | Electronics 10(7):775 | 10.3390/electronics10070775 | 85103003397 | TL | `.../daya/lambert_2021.pdf` |
| li_2020 | Low Power Optimisations for IoT Wearable Sensors Based on Evaluation of Nine QRS Detection Algorithms | J. Li et al. | 2020 | IEEE OJCAS | 10.1109/OJCAS.2020.3009822 | – | TL (already in the repo) | `laporan/pustaka/li_2020.pdf` |
| zambrano_2026 | Real-Time Cardiac Arrhythmia Classification Using TinyML on Ultra-Low-Cost Microcontrollers | M. Zambrano-de la Torre et al. | 2026 | Bioengineering 13:532 | 10.3390/bioengineering13050532 | – | TL (already in the repo) | `laporan/pustaka/zambrano_2026.pdf` |
| crespi_2026 | Pruning dense neural networks for efficient edge deployment in IoT applications | L. Crespí-Castañer et al. | 2026 | Applied Soft Computing 186:114175 | 10.1016/j.asoc.2025.114175 | – | TL (already in the repo; only mentions PPK2, no details) | `laporan/pustaka/crespi_2026.pdf` |
| iec_60601-1-11 | IEC 60601-1-11:2015 (iTeh sample) | IEC | 2015 | standard | – | – | Table of contents only | `.../daya/iec_60601-1-11_2015_sample.pdf` |
| mayo_2026 | Energy Profiling of Secure MQTT over WiFi on ESP32-Based IoT Devices | E. Mayo et al. | 2026 | IEEE ICC | 10.1109/ICC59461.2026.11587875 | 105045371895 | Metadata only (paywall; abstract not available in the Scopus API) | – |
| sari_2024 | Comparing the Accuracy of INA219, PZEM-004T, and MAX471 Sensors ... Solar Panels | Y. Sari et al. | 2024 | ICIC 2024 | 10.1109/ICIC64337.2024.10956405 | 105004582735 | Metadata only (paywall) | – |
| iec_60601-2-47 | IEC 60601-2-47:2012 Ambulatory electrocardiographic systems | IEC | 2012 | standard | – | – | Not accessed (paywall) | – |

Path `...` = `/home/mrrizaldi/dev/projek-akhir/laporan/pustaka/belum-dirujuk/riset-pengukuran/`.

### Key quotes (exact)

- **banbury_2021**, p. 8: *"Energy – Identical to latency, but in addition to measuring the number of
  inferences per second, measure the total energy used in the timing window and compute micro-Joules per
  inference. The same method of taking the median of five measurements is used."* P. 8: *"run inference
  for a minimum of 10 seconds and 10 iterations"*. P. 13: *"Only the power delivered to the core is
  measured. Furthermore, only one power supply is allowed to power the core"*; *"on-board SMPS conversion
  efficiency may vary considerably"*; *"the rate has no impact on the score."*
- **eembc_energyrunner**, §Energy Mode Hardware: *"IMPORTANT NOTE: Only ONE power supply is allowed to
  supply the DUT during measurement."*; *"Since Energy Mode supplies power to the device at a different
  voltage than the host USB, we need to electrically isolate the DUT."* BOM: *"Energy Monitor (50mA max.)
  | STMicro. LPM01A"*.
- **ti_ina219**, p. 9: *"it continuously converts the shunt voltage up to the number set in the shunt
  voltage averaging function (Configuration register, SADC bits). The device then converts the bus
  voltage up to the number set in the bus voltage averaging"*. P. 10: *"when configured for 12-bit and
  128 sample averaging, up to 68 ms in time between sampling these two values is possible."* P. 11:
  *"The internal ADC is based on a delta-sigma (ΔΣ) front-end with a 500-kHz (±30%) typical sampling
  rate."* P. 23: CNVR clears on *"Reading the Power Register"*. P. 5: current measurement error
  ±0.2% typ / ±0.5% max, VOS PGA ÷8 ±40 µV typ / ±200 µV max (A).
- **espressif_2026**, p. 66: *"TX current consumption is rated at a 100% duty cycle."* Table 5-7: TX
  340/291/283/286 mA, RX 88/91 mA. P. 64 (Table 5-2 cat. 4): *"If you use a single power supply, the
  recommended output current is 500 mA or more."*
- **espidf_current**: *"ordinary ammeters have a relatively high internal resistance, resulting in a
  significant voltage drop. This may cause the module to enter an unstable state"*; *"We recommend two
  options: the Joulescope ammeter and the Power Profiler Kit II from Nordic."*
- **espidf_lowpower_wifi**, WIFI_PS_MIN_MODEM configuration table: 160 MHz, DFS OFF, DTIM1 → average
  40.1 mA, max 235.8 mA, min 37.8 mA. *"All currents in the table are average currents, and the measured
  data are obtained by testing in a shielded box."*
- **akbari_2025**, §2.6: *"we conducted 30 independent power measurement trials (N = 30). In each trial,
  the MCU performed 20 consecutive model inferences."* §3.3: *"The sample period is 1 ms, which results
  from a 1 kHz sampling frequency for the current measurement."* Note: this paper is inconsistent
  (§1: 12.85 mA at 1.8 V; §3.3: 13.72 mA at 1.8 V; §2.6: supply 1.7 V). Cite its method, not
  its figures.
- **moura_2026**, p. 11: *"Radios and watchdogs are disabled; CPU is fixed at 240 MHz; ambient
  temperature is 25 ± 2 °C."*; *"We report the median over 60 runs after 5 warmups."*; *"An INA226 on the
  3V3 rail (Rshunt = 0.1 Ω, averaging = 1, continuous mode) samples bus voltage/current."*; *"All reported
  on-device energy values correspond to baseline-subtracted measurements"*. P. 12: *"Idle power
  Pbaseline is measured as the mean of 200 samples (200 µs apart) with Wi-Fi disabled"*.
- **muller_2024**, p. 4: *"most approaches stick to a sampling rate of 250 kHz or lower"*; *"simple
  linear regression models are sometimes used to fit the ADC readings to reference hardware during
  calibration."* P. 11: *"the power profiler samples the system's consumed power with a frequency of
  50 kHz, which is later used as ground truth during error calculation."*
- **alvarez-rosado_2022**, p. 5: *"resulting in a sample frequency of 5.1613KHz for Channel 1, taking
  8192 samples."* P. 6: *"The current ranger has a hardware 7kHz RC Low Pass Filter at the output"*.
  P. 7, Table 3: 3.7 V mean 57.03 mA, max 254.4 mA. Eq. (1): *"t = battery(mAh)/load (mA)"*.
- **prasetyawati_2023**, p. 1: *"The system undergoes calibration using fixed DC lamps and resistors as
  voltage loads, with digital multimeters, oscilloscopes, and power data loggers employed for comparative
  analysis. Calibration employs the linear regression technique"*.
- **lambert_2021**, p. 8: *"The INA219 contains a precision amplifier that measures the voltage drop
  across a 0.1 Ω sense resistor, with 1% gain error."* This paper does not report the sampling rate or
  validation against a reference instrument, so it is only a precedent for using the INA219, not evidence of accuracy.
- **li_2020**, p. 3: *"The PPK provides the real-time current measurement results ... with a resolution
  down to 13 µs. In this paper, all current measurements refer to the average current consumption of the
  nRF52832 SoC only when supplied with 2.85 V."*
- **zambrano_2026**, p. 17: *"the average current consumption (approximately 40 mA) was measured using a
  digital multimeter connected in series with the power source"*; *"this value represents an average
  estimate and does not include detailed profiling of transient or peak power consumption."*
- **crespi_2026**, p. 7: *"power profiling ... was carried out using the Power Profiler Kit II provided by
  Nordic Semiconductor."*

## 3. Top gaps (ordered from most risky at the defense)

1. **The INA219 only integrates the current about 50% of the time, and 27% of the readings are duplicates** (0x3FFF +
   reading every 100 ms without CNVR). An examiner who reads datasheet p. 9–10 can attack this directly.
   The fix is cheap: 0x39FF + CNVR polling (section 0 item 4), then `test_ina219`/`test_hw_ina219`
   rerun.
2. **No offset/gain calibration against a reference.** The plan of a series DMM on a spiky load is weak
   (burden voltage, DMM averaging unknown). Calibrate with 3-point resistors + zero offset + regression
   (Prasetyawati 2023; Müller 2024), and if possible validate once with a PPK2/Joulescope.
3. **One ladder run without repeats and without uncertainty of the mean.** The `sd` of the readings is not the error of the
   mean. The literature uses the median of 5 runs (MLPerf), N = 30 (Akbari), or 60 runs + 95% CI (Moura).
   The `p1`–`p3` difference is almost certainly below the noise without repeats.
4. **Comparison metrics from the literature are missing:** energy per inference (µJ) and battery operating time. µJ per
   inference can be derived from the ladder data (ΔP · T / N_beat). Battery life should come from a
   drain-the-battery test in `p5`, not from a formula with an unsourced derating factor.
5. **Battery side without fixed voltage:** the figures depend on the cell SOC and the converter η, so repeats
   are not comparable. For the ladder, use a 3.7 V bench supply at the cell position and make mW the main metric. In the
   document, remove the unsourced "+30 mA" figure for `setSleep(false)`.

Process note: the Scopus abstracts for Mayo 2026 and Sari 2024 are not available (empty field). The text of
IEC 60601-1-11 §8.5.1 and IEC 60601-2-47 could not be read, so there is no standard claim in
this report.
