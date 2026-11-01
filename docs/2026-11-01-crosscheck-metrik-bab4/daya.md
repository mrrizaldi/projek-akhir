# Crosscheck rencana ukur daya terhadap standar dan literatur

Kondisi: rencana ukur di `firmware/README.md` §Catu daya, `model/docs/firmware-walkthrough.md` §5d,
`firmware/src/daya.cpp`, `firmware/src/ina219.cpp`, `firmware/include/ina219.h` (dibaca 1 Nov 2026).
Konfigurasi yang berlaku sekarang: `INA219_CONFIG = 0x3FFF`, pembacaan tiap 100 ms
(`PERIODE_BACA_INA219_MS`) tanpa memeriksa bit CNVR, rata-rata per jendela 10 s, 1 jendela transien
dibuang, 6 jendela per tingkat, satu kali tangga.

Penanda: **[TL]** = dibaca teks lengkap, **[A]** = hanya abstrak/metadata, **[INF]** = kesimpulan
saya dari sumber, bukan kalimat sumber.

## 0. Temuan teknis kunci (dasar tabel)

1. **0x3FFF = PGA ÷8, BADC 128 sampel, SADC 128 sampel, MODE 111 (shunt dan bus, kontinu).** Datasheet
   INA219 hlm. 9: pada mode 111 perangkat *"continuously converts the shunt voltage up to the number set
   in the shunt voltage averaging function ... The device then converts the bus voltage up to the number
   set in the bus voltage averaging"*. Hlm. 10: *"when configured for 12-bit and 128 sample averaging, up
   to 68 ms in time between sampling these two values is possible"*. Tabel 5 hlm. 20: 128 sampel = 68,10 ms.
   **[INF]** Satu siklus = 68,10 ms shunt + 68,10 ms bus = 136,2 ms, sehingga arus shunt hanya
   terintegrasi ±50 % dari waktu. Rata-rata tetap tak bias selama beban tidak sinkron dengan siklus
   INA219, tetapi separuh energi tidak pernah dilihat.
2. **Pembacaan 100 ms tidak sinkron dengan hasil 136,2 ms.** **[INF]** Dalam 10 s hanya ±73 hasil baru
   untuk 100 pembacaan (`n=101` di log), jadi ±27 % pembacaan adalah duplikat. `sd` per jendela dihitung
   dari bacaan berduplikat dan bukan ketidakpastian rata-rata. CNVR (bit 1 register bus) menandai hasil
   baru dan dihapus dengan membaca Power Register (datasheet hlm. 23).
3. **ADC INA219 mengintegrasikan, tidak mencuplik titik.** Hlm. 11: *"The internal ADC is based on a
   delta-sigma (ΔΣ) front-end with a 500-kHz (±30%) typical sampling rate."* **[INF]** Jadi kekhawatiran
   Nyquist "532 µs vs lonjakan µs/ms" tidak berlaku untuk RATA-RATA: tiap konversi 12-bit adalah rata-rata
   dari modulator 500 kHz selama 532 µs, dan 128 konversi berurutan menutup 68,10 ms tanpa celah. Yang
   tidak bisa diukur adalah PUNCAK lonjakan. Banbury 2021 hlm. 13 mendukung logika yang sama untuk EMON:
   *"Since these internal sampling rates are typically well-within the time constant of the decoupling
   DUT's power delivery decoupling capacitance, the rate has no impact on the score."*
4. **Perbaikan murah [INF]:** set BADC ke 12-bit tunggal (532 µs), SADC tetap 128: config **0x39FF**.
   Cakupan shunt = 68,10 / (68,10 + 0,532) = 99,2 %. Baca hanya saat CNVR = 1 (polling ≤ 10 ms), lalu baca
   Power Register untuk menghapus CNVR, sehingga tiap hasil masuk tepat sekali. Alternatif: MODE 101
   (shunt saja, kontinu) = cakupan 100 %, dan tegangan bus dibaca sekali per jendela dengan pindah mode
   sesaat. Tegangan sel berubah lambat, jadi bus 532 µs cukup. Ini menyentuh `include/ina219.h` dan
   `daya.cpp`, jadi `test_ina219` dan `test_hw_ina219` perlu dijalankan ulang.
5. **Arus WiFi ESP32-S3 (datasheet v2.2, Tabel 5-7 hlm. 66, pada 3,3 V, 25 °C):** TX puncak 340 mA
   (802.11b 1 Mbps @21 dBm), 283–291 mA (g/n), RX 88–91 mA. Arus modem-sleep 240 MHz WAITI = 32,9/47,6 mA
   (Tabel 5-9 hlm. 67). Panduan ESP-IDF "Low Power Mode in Wi-Fi Scenarios" (ESP32-S3, v6.1): 160 MHz,
   WIFI_PS_MIN_MODEM, DFS OFF, DTIM1 = rata-rata 40,1 mA, maks 235,8 mA, min 37,8 mA. **[INF]** Rasio
   puncak/rata-rata ±6 menunjukkan arus yang sangat berlonjak, sehingga cakupan waktu penuh (butir 4)
   lebih penting daripada laju cuplik. Perkiraan "+30 mA" untuk `setSleep(false)` di rencana tidak
   bersumber. Datasheet memberi RX ≈ 88 mA dibanding modem-sleep 33–48 mA di 240 MHz; ini isyarat kasar
   bahwa kenaikannya bisa lebih besar. Ukur, jangan memperkirakan.
6. **Tidak ada standar medis yang terverifikasi menetapkan ambang daya/umur baterai** (bagian 1, baris 12).

## 1. Tabel crosscheck

| # | Rencana kami | Praktik standar/literatur (sumber + halaman/tabel) | Status | Saran konkret |
|---|---|---|---|---|
| 1 | Alat: modul INA219 (shunt 0,1 Ω, 12-bit) dibaca ESP32 sendiri lewat I2C | MLPerf Tiny/EnergyRunner memakai EMON eksternal: ST LPM01A, Joulescope JS110, Keysight N6705 (Banbury 2021 hlm. 13; README EnergyRunner §Energy Mode Hardware). LPM01A maks 50 mA (README, BOM), jadi tidak cocok untuk ESP32 ber-WiFi. Espressif menyarankan Joulescope atau Nordic PPK2 (ESP-IDF "Current Consumption Measurement of Modules"). Monitor INA di board ESP32-S3 dipakai pada paper ber-review: INA226 di rel 3V3 (Moura 2026 hlm. 11). Pengukuran on-device lazim < 10 kHz dan divalidasi terhadap profiler eksternal (Otii, 50 kHz) (Müller 2024 hlm. 4, 11). | Beda tapi dapat dipertanggungjawabkan | Pertahankan INA219 untuk arus RATA-RATA per mode. Nyatakan eksplisit bahwa puncak lonjakan tidak diukur. Bila lab punya PPK2/Joulescope/osiloskop + shunt, pakai sekali untuk memvalidasi rata-rata `p0` dan `p5` (baris 9). |
| 2 | Config 0x3FFF (shunt + bus kontinu, 128/128), baca tiap 100 ms tanpa CNVR | Datasheet INA219 hlm. 9–10, Tabel 5 hlm. 20, CNVR hlm. 23 (bagian 0 butir 1–2) | **Kurang** | Ganti ke 0x39FF (bus 532 µs, shunt 128 sampel), poll CNVR, ambil tiap hasil tepat sekali. Cakupan naik dari ±50 % ke 99,2 %, tanpa duplikat. Laporkan `n` sebagai jumlah konversi (±145 per 10 s). |
| 3 | Rata-rata 10 s terhadap lonjakan WiFi (ratusan mA, orde ms) | ΔΣ 500 kHz (INA219 hlm. 11). Laju EMON tidak memengaruhi skor karena kapasitor dekopling (Banbury hlm. 13). Profiler eksternal ≤ 250 kHz karena jejak daya sudah tersaring kapasitansi on-board (Müller hlm. 4). Pembanding: osiloskop 5,16 kHz di belakang Current Ranger ber-LPF 7 kHz mencatat ESP32 MQTT maks 254–381 mA, rata-rata 52–57 mA (Álvarez-Rosado 2022 hlm. 5–7, Tabel 3). | Sesuai untuk rata-rata (setelah baris 2 diperbaiki); tidak mampu mengukur puncak | Laporkan hanya rata-rata. Puncak arus dikutip dari datasheet (Tabel 5-7) sebagai acuan desain catu, bukan sebagai hasil ukur. Periksa bit OVF di tiap jendela dan catat bila pernah 1. |
| 4 | Sisi baterai (antara TP4056 OUT+ dan konverter), memuat rugi konverter | EEMBC/MLPerf: satu catu bertegangan tetap, dan hanya daya ke DUT yang diukur: *"Only the power delivered to the core is measured. Furthermore, only one power supply is allowed"* (Banbury hlm. 13). Efisiensi SMPS disebut sebagai variabel (hlm. 13). Li 2020 mengukur hanya SoC pada 2,85 V (hlm. 3). Moura mengukur rel 3V3 (hlm. 11). Álvarez-Rosado: tegangan catu 3,7/5/9 V mengubah energi per siklus 27,43 → 60,28 mJ (Tabel 5, hlm. 7). | Beda tapi dapat dipertanggungjawabkan | Sisi baterai tepat untuk umur baterai dan konsumsi sistem. (a) Jadikan **daya (mW)** metrik utama, karena arus di sisi sel naik saat V sel turun. (b) Untuk tangga `p0`–`p5`, ganti sel dengan **catu bench tetap 3,7 V** di titik TP4056 OUT+ supaya ulangan sebanding, dan pakai sel hanya untuk uji habis-baterai. (c) Sebut bahwa selisih antartahap memuat η konverter. |
| 5 | Tangga mandiri dari baterai tanpa USB; jalur laptop lewat kabel tanpa VBUS | EnergyRunner: DUT terisolasi secara listrik dari host lewat IO Manager + level shifter, dan level shifter dicatu dari kanal yang tidak diukur. *"Only ONE power supply is allowed to supply the DUT during measurement"* (README §Energy Mode Hardware). | Sesuai (tangga mandiri); jalur laptop kurang bersih | Angka resmi dari tangga mandiri saja. Jalur laptop berbagi GND dan D+/D− dengan host, jadi dipakai hanya untuk debug. Sebut bahwa modul INA219 (dicatu 3V3 board, IQ maks 1 mA, INA219 hlm. 1) ikut terhitung. |
| 6 | 60 s per tingkat sesudah membuang 1 jendela transien | MLPerf: *"run inference for a minimum of 10 seconds and 10 iterations"* (Banbury hlm. 8). Ada iterasi pemanasan sebelum timestamp (README EnergyRunner). Moura: 5 pemanasan (hlm. 11). | Sesuai | Pertahankan. Di `p3`, ±17 beat per 10 s × 6 jendela ≈ 100 inferensi per tingkat, sehingga syarat ≥ 10 iterasi terpenuhi. |
| 7 | Satu kali tangga, tanpa ulangan | MLPerf: median dari 5 run (Banbury hlm. 8). Akbari 2025: N = 30 percobaan × 20 inferensi, mean ± sd (§2.6). Moura: median 60 run + 95 % CI (hlm. 11–12). Lambert 2021: uji t/Mann–Whitney antarkondisi (§3.5). | **Kurang** | Jalankan tangga ≥ 5 kali pada kondisi tetap (catu bench, suhu dicatat). Laporkan median dan rentang (atau mean ± 95 % CI) dari rata-rata per tangga. Selisih antartahap dihitung per ulangan dan diberi CI. |
| 8 | Kriteria sah: arus naik > 2 × sd (sd bacaan 100 ms) | Statistik di atas memakai sebaran rata-rata antar-run/ulangan, bukan sebaran sampel mentah. | Kurang (kecil) | Pisahkan "pengukuran sah" (V bus, `lewat = 0`, `beat > 0`, OVF = 0) dari "selisih terdeteksi". Selisih yang CI-nya memuat nol dilaporkan "tidak terbedakan pada resolusi X mA", bukan "tidak sah". |
| 9 | Kalibrasi: satu titik, multimeter mode arus seri pada satu mode, koreksi `R_SHUNT` | Datasheet: galat arus ±0,2 % tipikal, ±0,5 % maks (INA219A), offset PGA ÷8 ±40 µV tipikal, ±200 µV maks (A) / ±100 µV (B) (hlm. 5), yaitu ±0,4 mA tipikal dan ±1–2 mA maks pada 0,1 Ω. Shunt modul: *"0.1 Ω sense resistor, with 1% gain error"* (Lambert 2021 hlm. 8). Espressif: ammeter biasa *"have a relatively high internal resistance, resulting in a significant voltage drop"* (ESP-IDF guide). Prasetyawati 2023 mengkalibrasi INA219 dengan beban resistor/lampu DC terhadap DMM, regresi linear, MAPE. Akurasi kanal tegangan shunt 93,71 % vs tegangan beban 99,27 % (hlm. 1). Müller: regresi linear terhadap alat acuan lazim dipakai (hlm. 4). | **Kurang** | (a) Ukur offset nol: jalur beban diputus, catat rata-rata shunt 60 s, kurangkan. (b) Kalibrasi gain dengan **beban resistor daya** (DC stabil) pada 3 titik yang mengapit rentang alat (mis. ±100, 200, 400 mA) terhadap DMM, lalu regresi linear I_ref = a·I_ina + b. Laporkan a, b, R² dan galat sisa. (c) Jangan pasang DMM seri pada ESP32 yang berlonjak, karena burden voltage dan perata-rataan DMM tidak diketahui. |
| 10 | Metrik: mA dan mW rata-rata per mode; belum ada energi per inferensi dan umur baterai | MLPerf: *"measure the total energy used in the timing window and compute micro-Joules per inference"* (Banbury hlm. 8). Akbari 2025: 3532 ± 6 µJ per inferensi = P × latensi (§3.3). Moura: energi bersih = E_gross − P_idle·T (pers. 8a–8b, hlm. 11). Umur baterai: t = kapasitas (mAh) / arus beban (mA) (Álvarez-Rosado pers. 1, hlm. 7, tanpa derating). Zambrano 2026: 40 mA via DMM, *"does not include detailed profiling of transient or peak power consumption"* (hlm. 17). | **Kurang** | (a) **Energi per inferensi (µJ)** = (P_p3 − P_p2) · T_jendela / N_beat per jendela, ditambah cek silang latensi (`test_inference`) × ΔP. Catat bahwa `loop()` tidak tidur, jadi angka ini adalah ongkos tambahan pada CPU yang sudah aktif. (b) **Umur baterai**: uji habis-baterai langsung di mode `p5` (sel penuh → reset/brownout, catat jam) sebagai angka utama. Rumus E_sel / P_rata-rata hanya sebagai pembanding. Faktor derating tidak saya temukan di sumber resmi, jadi jangan dikutip tanpa sumber. |
| 11 | `p5` = `setSleep(false)`, diperkirakan +30 mA | Tabel 5-7/5-9 datasheet ESP32-S3 (hlm. 66–67) dan tabel ESP-IDF low-power Wi-Fi (bagian 0 butir 5) | Kurang (asumsi tak bersumber) | Hapus angka +30 mA dari dokumen rencana; biarkan diukur. Sebut bahwa `setSleep(false)` sama dengan operasi normal di firmware (`ecg_mqtt.cpp`), jadi `p5` = konsumsi operasional. |
| 12 | Tanpa ambang / standar | IEC 60601-1-11:2015 memiliki §8.5 "Additional requirements for an INTERNAL ELECTRICAL POWER SOURCE", §8.5.1 "Indication of state" (daftar isi, sampel iTeh hlm. 5). Isi klausul tidak terbaca (paywall). IEC 60601-2-47:2012 (sistem EKG ambulatori) tidak dapat diakses. Syarat durasi 24 jam TIDAK terverifikasi. | Tidak ada syarat terverifikasi | Jangan klaim kesesuaian standar. Laporkan "waktu operasi terukur" dari uji habis-baterai. Bila ingin mengaitkan dengan Holter 24 jam, perlu sumber klinis/standar yang benar-benar dibaca. |
| 13 | Suhu dan kondisi sel tidak dicatat | Datasheet ESP32-S3: pengukuran pada 3,3 V, 25 °C (hlm. 66). Moura: 25 ± 2 °C, CPU dikunci 240 MHz, radio dimatikan saat inferensi (hlm. 11). | Kurang (kecil) | Catat suhu ruang, tegangan sel awal/akhir, versi firmware (commit), frekuensi CPU, dan AP/RSSI WiFi untuk `p5` di CSV atau metadata. |

## 2. Daftar sumber

| Kunci usulan | Judul | Penulis | Tahun | Venue | DOI | Scopus ID | Status | Path |
|---|---|---|---|---|---|---|---|---|
| banbury_2021 | MLPerf Tiny Benchmark | C. Banbury et al. | 2021 | NeurIPS Datasets & Benchmarks (arXiv:2106.07597v4) | 10.48550/arXiv.2106.07597 | – | TL | `laporan/pustaka/belum-dirujuk/riset-pengukuran/tinyml/banbury_2021.pdf` |
| eembc_energyrunner | EnergyRunner benchmark framework (README, user guide) | EEMBC | 2021– | github.com/eembc/energyrunner | – | – | TL | `.../riset-pengukuran/tinyml/eembc_energyrunner_README.md` |
| mlperftiny_rules | MLPerf Tiny Inference Rules | MLCommons | – | github.com/mlcommons/tiny | – | – | TL (tidak memuat rincian metode energi; merujuk ke runner) | `.../tinyml/mlperftiny_rules.adoc`, `.../tinyml/mlperftiny_runner_README.md` |
| ti_ina219 | INA219 Zerø-Drift, Bidirectional Current/Power Monitor With I2C Interface (SBOS448G) | Texas Instruments | 2015 | datasheet | – | – | TL | `.../riset-pengukuran/daya/ti_ina219_2015.pdf` |
| ti_ina226 | INA226 (SBOS547C) | Texas Instruments | 2026 (rev.) | datasheet | – | – | TL, dipakai hanya untuk alternatif (konversi 140 µs–8,244 ms, rata-rata hingga 1024, galat gain 0,1 % maks) | `.../daya/ti_ina226_2026.pdf` |
| espressif_2026 | ESP32-S3 Series Datasheet v2.2 | Espressif | 2026 | datasheet | – | – | TL | `.../daya/espressif_2026.pdf` |
| espidf_current | Current Consumption Measurement of Modules (ESP32-S3, ESP-IDF v6.1) | Espressif | 2026 | dokumentasi web | – | – | TL | `.../daya/espidf_current_measurement.html/.txt` |
| espidf_lowpower_wifi | Low Power Mode in Wi-Fi Scenarios (ESP32-S3, ESP-IDF v6.1) | Espressif | 2026 | dokumentasi web | – | – | TL | `.../daya/espidf_lowpower_wifi.html/.txt` |
| akbari_2025 | Atrial Fibrillation Detection on the Embedded Edge: Energy-Efficient Inference on a Low-Power Microcontroller | Y. Akbari, ..., O. Faust | 2025 | Sensors 25(21):6601 | 10.3390/s25216601 | 105021612220 | TL (XML Europe PMC PMC12608751; PDF MDPI terblokir) | `.../daya/akbari_2025.xml/.txt` |
| moura_2026 | On-Device Edge AI for Monthly Energy Forecasting on ESP32-S3 Using 3-Day Windows | G. A. Moura et al. | 2026 | IEEE Access 14 | 10.1109/ACCESS.2026.3658109 | 105029005786 | TL | `.../daya/moura_2026.pdf` |
| muller_2024 | TinyEP: TinyML-Enhanced Energy Profiling for Extreme Edge Devices | K. Müller, J. Weidner, N. Franchi, P. Wägemann | 2024 | IEEE Access 12 | 10.1109/ACCESS.2024.3520089 | 85212574653 | TL | `.../daya/muller_2024.pdf` |
| alvarez-rosado_2022 | Energy consumption of an internet of things development board | G. L. Álvarez-Rosado et al. | 2022 | Revista de Ciencias Tecnológicas 5(4):e234 | 10.37636/recit.v5n4e234 | – (tidak dicek terindeks) | TL | `.../daya/alvarez-rosado_2022.pdf` |
| prasetyawati_2023 | Calibration and Validation of INA219 as Sensor Power Monitoring System using Linear Regression | F. Y. Prasetyawati, D. Harjunowibowo, A. Fauzi, B. Utomo | 2023 | AIUB J. Sci. Eng. 22(3) | 10.53799/AJSE.V22I3.595 | 85181943451 | TL | `.../daya/prasetyawati_2023.pdf` |
| lambert_2021 | Power Consumption Profiling of a Lightweight Development Board: Sensing with the INA219 and Teensy 4.0 Microcontroller | J. Lambert, R. Monahan, K. Casey | 2021 | Electronics 10(7):775 | 10.3390/electronics10070775 | 85103003397 | TL | `.../daya/lambert_2021.pdf` |
| li_2020 | Low Power Optimisations for IoT Wearable Sensors Based on Evaluation of Nine QRS Detection Algorithms | J. Li et al. | 2020 | IEEE OJCAS | 10.1109/OJCAS.2020.3009822 | – | TL (sudah di repo) | `laporan/pustaka/li_2020.pdf` |
| zambrano_2026 | Real-Time Cardiac Arrhythmia Classification Using TinyML on Ultra-Low-Cost Microcontrollers | M. Zambrano-de la Torre et al. | 2026 | Bioengineering 13:532 | 10.3390/bioengineering13050532 | – | TL (sudah di repo) | `laporan/pustaka/zambrano_2026.pdf` |
| crespi_2026 | Pruning dense neural networks for efficient edge deployment in IoT applications | L. Crespí-Castañer et al. | 2026 | Applied Soft Computing 186:114175 | 10.1016/j.asoc.2025.114175 | – | TL (sudah di repo; hanya menyebut PPK2, tanpa rincian) | `laporan/pustaka/crespi_2026.pdf` |
| iec_60601-1-11 | IEC 60601-1-11:2015 (sampel iTeh) | IEC | 2015 | standar | – | – | Hanya daftar isi | `.../daya/iec_60601-1-11_2015_sample.pdf` |
| mayo_2026 | Energy Profiling of Secure MQTT over WiFi on ESP32-Based IoT Devices | E. Mayo et al. | 2026 | IEEE ICC | 10.1109/ICC59461.2026.11587875 | 105045371895 | Metadata saja (paywall; abstrak tidak tersedia di Scopus API) | – |
| sari_2024 | Comparing the Accuracy of INA219, PZEM-004T, and MAX471 Sensors ... Solar Panels | Y. Sari et al. | 2024 | ICIC 2024 | 10.1109/ICIC64337.2024.10956405 | 105004582735 | Metadata saja (paywall) | – |
| iec_60601-2-47 | IEC 60601-2-47:2012 Ambulatory electrocardiographic systems | IEC | 2012 | standar | – | – | Tidak diakses (paywall) | – |

Path `...` = `/home/mrrizaldi/dev/projek-akhir/laporan/pustaka/belum-dirujuk/riset-pengukuran/`.

### Kutipan kunci (persis)

- **banbury_2021**, hlm. 8: *"Energy – Identical to latency, but in addition to measuring the number of
  inferences per second, measure the total energy used in the timing window and compute micro-Joules per
  inference. The same method of taking the median of five measurements is used."* Hlm. 8: *"run inference
  for a minimum of 10 seconds and 10 iterations"*. Hlm. 13: *"Only the power delivered to the core is
  measured. Furthermore, only one power supply is allowed to power the core"*; *"on-board SMPS conversion
  efficiency may vary considerably"*; *"the rate has no impact on the score."*
- **eembc_energyrunner**, §Energy Mode Hardware: *"IMPORTANT NOTE: Only ONE power supply is allowed to
  supply the DUT during measurement."*; *"Since Energy Mode supplies power to the device at a different
  voltage than the host USB, we need to electrically isolate the DUT."* BOM: *"Energy Monitor (50mA max.)
  | STMicro. LPM01A"*.
- **ti_ina219**, hlm. 9: *"it continuously converts the shunt voltage up to the number set in the shunt
  voltage averaging function (Configuration register, SADC bits). The device then converts the bus
  voltage up to the number set in the bus voltage averaging"*. Hlm. 10: *"when configured for 12-bit and
  128 sample averaging, up to 68 ms in time between sampling these two values is possible."* Hlm. 11:
  *"The internal ADC is based on a delta-sigma (ΔΣ) front-end with a 500-kHz (±30%) typical sampling
  rate."* Hlm. 23: CNVR clears on *"Reading the Power Register"*. Hlm. 5: current measurement error
  ±0,2 % tip / ±0,5 % maks, VOS PGA ÷8 ±40 µV tip / ±200 µV maks (A).
- **espressif_2026**, hlm. 66: *"TX current consumption is rated at a 100% duty cycle."* Tabel 5-7: TX
  340/291/283/286 mA, RX 88/91 mA. Hlm. 64 (Tabel 5-2 cat. 4): *"If you use a single power supply, the
  recommended output current is 500 mA or more."*
- **espidf_current**: *"ordinary ammeters have a relatively high internal resistance, resulting in a
  significant voltage drop. This may cause the module to enter an unstable state"*; *"We recommend two
  options: the Joulescope ammeter and the Power Profiler Kit II from Nordic."*
- **espidf_lowpower_wifi**, tabel konfigurasi WIFI_PS_MIN_MODEM: 160 MHz, DFS OFF, DTIM1 → average
  40,1 mA, max 235,8 mA, min 37,8 mA. *"All currents in the table are average currents, and the measured
  data are obtained by testing in a shielded box."*
- **akbari_2025**, §2.6: *"we conducted 30 independent power measurement trials (N = 30). In each trial,
  the MCU performed 20 consecutive model inferences."* §3.3: *"The sample period is 1 ms, which results
  from a 1 kHz sampling frequency for the current measurement."* Catatan: paper ini tidak konsisten
  (§1: 12,85 mA pada 1,8 V; §3.3: 13,72 mA pada 1,8 V; §2.6: catu 1,7 V). Kutip metodenya, jangan
  angkanya.
- **moura_2026**, hlm. 11: *"Radios and watchdogs are disabled; CPU is fixed at 240 MHz; ambient
  temperature is 25 ± 2 °C."*; *"We report the median over 60 runs after 5 warmups."*; *"An INA226 on the
  3V3 rail (Rshunt = 0.1 Ω, averaging = 1, continuous mode) samples bus voltage/current."*; *"All reported
  on-device energy values correspond to baseline-subtracted measurements"*. Hlm. 12: *"Idle power
  Pbaseline is measured as the mean of 200 samples (200 µs apart) with Wi-Fi disabled"*.
- **muller_2024**, hlm. 4: *"most approaches stick to a sampling rate of 250 kHz or lower"*; *"simple
  linear regression models are sometimes used to fit the ADC readings to reference hardware during
  calibration."* Hlm. 11: *"the power profiler samples the system's consumed power with a frequency of
  50 kHz, which is later used as ground truth during error calculation."*
- **alvarez-rosado_2022**, hlm. 5: *"resulting in a sample frequency of 5.1613KHz for Channel 1, taking
  8192 samples."* Hlm. 6: *"The current ranger has a hardware 7kHz RC Low Pass Filter at the output"*.
  Hlm. 7, Tabel 3: 3,7 V mean 57,03 mA, max 254,4 mA. Pers. (1): *"t = battery(mAh)/load (mA)"*.
- **prasetyawati_2023**, hlm. 1: *"The system undergoes calibration using fixed DC lamps and resistors as
  voltage loads, with digital multimeters, oscilloscopes, and power data loggers employed for comparative
  analysis. Calibration employs the linear regression technique"*.
- **lambert_2021**, hlm. 8: *"The INA219 contains a precision amplifier that measures the voltage drop
  across a 0.1 Ω sense resistor, with 1% gain error."* Paper ini tidak melaporkan laju cuplik atau
  validasi terhadap alat acuan, sehingga hanya preseden pemakaian INA219, bukan bukti akurasi.
- **li_2020**, hlm. 3: *"The PPK provides the real-time current measurement results ... with a resolution
  down to 13 µs. In this paper, all current measurements refer to the average current consumption of the
  nRF52832 SoC only when supplied with 2.85 V."*
- **zambrano_2026**, hlm. 17: *"the average current consumption (approximately 40 mA) was measured using a
  digital multimeter connected in series with the power source"*; *"this value represents an average
  estimate and does not include detailed profiling of transient or peak power consumption."*
- **crespi_2026**, hlm. 7: *"power profiling ... was carried out using the Power Profiler Kit II provided by
  Nordic Semiconductor."*

## 3. Celah terpenting (urut dari paling berisiko di sidang)

1. **INA219 hanya mengintegrasikan arus ±50 % dari waktu, dan 27 % bacaan adalah duplikat** (0x3FFF +
   baca 100 ms tanpa CNVR). Penguji yang membaca datasheet hlm. 9–10 dapat menyerangnya langsung.
   Perbaikannya murah: 0x39FF + polling CNVR (bagian 0 butir 4), lalu `test_ina219`/`test_hw_ina219`
   dijalankan ulang.
2. **Tidak ada kalibrasi offset/gain terhadap acuan.** Rencana DMM seri pada beban berlonjak lemah
   (burden voltage, perata-rataan DMM tidak diketahui). Kalibrasi resistor 3 titik + offset nol + regresi
   (Prasetyawati 2023; Müller 2024), dan bila memungkinkan validasi sekali dengan PPK2/Joulescope.
3. **Satu kali tangga tanpa ulangan dan tanpa ketidakpastian rata-rata.** `sd` bacaan bukan galat
   rata-rata. Literatur memakai median 5 run (MLPerf), N = 30 (Akbari), atau 60 run + 95 % CI (Moura).
   Selisih `p1`–`p3` hampir pasti di bawah derau tanpa ulangan.
4. **Metrik pembanding literatur tidak ada:** energi per inferensi (µJ) dan waktu operasi baterai. µJ per
   inferensi bisa diturunkan dari data tangga (ΔP · T / N_beat). Umur baterai sebaiknya dari uji
   habis-baterai di `p5`, bukan dari rumus dengan faktor derating yang tidak bersumber.
5. **Sisi baterai tanpa tegangan tetap:** angka bergantung SOC sel dan η konverter, sehingga antarulangan
   tidak sebanding. Untuk tangga, pakai catu bench 3,7 V di posisi sel dan jadikan mW metrik utama. Di
   dokumen, hapus angka "+30 mA" untuk `setSleep(false)` yang tidak bersumber.

Catatan proses: abstrak Scopus untuk Mayo 2026 dan Sari 2024 tidak tersedia (field kosong). Isi
klausul IEC 60601-1-11 §8.5.1 dan IEC 60601-2-47 tidak terbaca, sehingga tidak ada klaim standar di
laporan ini.
