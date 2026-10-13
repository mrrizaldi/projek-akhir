# firmware/ — program ESP32-S3 (PlatformIO)

Firmware alat pemantau EKG: akuisisi AD8232 pada 360 Hz, preprocessing dan
deteksi R-peak on-device, klasifikasi aritmia per detak dengan TFLite Micro
(model INT8 dari `model/`), lalu publikasi hasil ke ThingsBoard lewat MQTT
dengan ring buffer PSRAM sebagai penyangga saat koneksi putus.

Board: ESP32-S3 N16R8 (16 MB flash, 8 MB PSRAM), board id PlatformIO
`4d_systems_esp32s3_gen4_r8n16`. Seluruh konfigurasi ada di
[`platformio.ini`](platformio.ini); semua perintah dijalankan dari folder ini.

Penjelasan rinci: [`firmware-walkthrough`](../model/docs/firmware-walkthrough.md)
(port preprocessing dan TFLM), [`mqtt-walkthrough`](../model/docs/mqtt-walkthrough.md)
(publikasi, PDSR, latensi), [`akuisisi-walkthrough`](../model/docs/akuisisi-walkthrough.md)
(merekam sinyal tubuh).

## Environment PlatformIO

| Env | Kegunaan | Sumber yang di-build | Library |
|---|---|---|---|
| `esp32-s3` (bawaan) | Firmware utama: akuisisi, klasifikasi, MQTT | semua `src/` kecuali `hwtest.cpp` | Chirale_TensorFLowLite |
| `hwtest` | Uji perangkat keras PCB: AD8232, TFT ST7789, buzzer, tiga tombol, INA219 | `hwtest.cpp`, `ecg_live.cpp`, `ecg_pipeline.cpp`, `ina219.cpp` | Adafruit ST7735/ST7789, Adafruit GFX |
| `native` | Uji unit di PC tanpa board | `ecg_pipeline.cpp`, `ecg_live.cpp`, `ina219.cpp`, `ecg_mqtt.cpp` | — |

Build flag yang relevan:

- `esp32-s3` dan `hwtest` memakai `-I test` karena `test/golden_ref.h` menjadi
  sumber sinyal replay.
- `hwtest`: `HWTEST_SIM` memilih sumber sinyal awal (0 = ADC, 1 = dummy teratur,
  2 = rekaman record 208); `ECG_LIVE_TIAP=90` menjalankan deteksi tiap 250 ms.
  Firmware utama memakai nilai bawaan `ECG_LIVE_TIAP = ECG_FS` (deteksi tiap
  1 detik).

## Perintah

```bash
pio run                                  # build env esp32-s3
pio run -t upload                        # build + flash firmware utama
pio device monitor                       # serial 115200
pio run -e hwtest -t upload && pio device monitor   # firmware uji hardware
pio test -e native                       # 23 test di PC: test_preproc, test_ina219, test_mqtt
pio test -e esp32-s3                     # di board: test_preproc + test_inference
pio device list                          # cek port
```

`pio run` tanpa `-e` hanya mem-build `esp32-s3` (`default_envs`). Env `native`
tidak memiliki `main()`, sehingga hanya dipakai lewat `pio test`.

## Struktur

| Lokasi | Isi |
|---|---|
| `src/main.cpp` | Firmware utama: ISR ADC 360 Hz → antrean → loop; gerbang kalibrasi sinyal; inferensi; rekam ke LittleFS; perintah serial |
| `src/ecg_pipeline.cpp` | Port preprocessing Python ke C (bandpass kausal, deteksi Pan-Tompkins, penyelarasan R, window + z-score, fitur RR) |
| `src/ecg_live.cpp` | Alur streaming: sampel masuk satu per satu, beat siap-klasifikasi keluar |
| `src/ecg_mqtt.cpp` | Payload JSON, antrean backlog, klien MQTT di atas `WiFiClient` (tanpa library tambahan) |
| `src/ina219.cpp` | Konversi register INA219 ke mA/mV (fungsi murni) |
| `src/hwtest.cpp` | Program uji hardware (env `hwtest`), memiliki `setup()`/`loop()` sendiri |
| `include/` | Header kontrak; `model_int8.h` dan `ecg_preproc.h` hasil generate (lihat [`include/README.md`](include/README.md)) |
| `test/golden_ref.h` | Golden reference Python, hasil `model/scripts/export_golden.py` |
| `test/test_*` | Suite Unity: `test_preproc`, `test_inference`, `test_ina219`, `test_mqtt` |
| `arsip/` | Program uji sekali pakai yang tidak lagi di-build (lihat bagian Arsip) |

## Pin map

Firmware utama (`src/main.cpp`) dan program uji (`src/hwtest.cpp`) memakai pin
map yang berbeda. `main.cpp` memakai susunan breadboard; `hwtest.cpp` memakai
pin map PCB ([catatan PCB rev2](../model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md) §5).

| Fungsi | `main.cpp` (breadboard) | `hwtest.cpp` (PCB) |
|---|---|---|
| EKG OUT AD8232 | GPIO 8 (ADC1_CH7) | GPIO 1 (ADC1_CH0) |
| AD8232 LO+ / LO− | 17 / 7 | 42 / 2 |
| Tombol | REC = 6, DUMP = 5 | B1 / B2 / B3 = 4 / 5 / 6 |
| TFT ST7789 SCK / MOSI / RST / DC | — | 9 / 8 / 10 / 11 (CS ke GND) |
| Buzzer (modul pasif, aktif LOW) | — | 13 |
| INA219 SDA / SCL | — | 17 / 18 (VCC modul 3V3) |
| NeoPixel onboard | 48 | — |

Tombol memakai pull-up internal dan aktif ke GND.

Indikator NeoPixel pada firmware utama: merah = merekam, biru = kalibrasi
(stabilisasi), oranye = ayunan sinyal di bawah ambang, hijau = sinyal baik,
merah berkedip = inisialisasi TFLM gagal.

## Kredensial WiFi dan ThingsBoard

```bash
cp include/wifi_secrets.example.h include/wifi_secrets.h
```

Isi `WIFI_SSID`, `WIFI_PASS`, `TB_HOST` (IP laptop yang menjalankan
`docker compose`, bukan `localhost`), `TB_PORT`, dan `TB_TOKEN` (access token
device, dicetak oleh `dashboard/smoke_test.py`). `wifi_secrets.h` di-ignore git.
Tanpa berkas ini firmware tetap ter-build dan berjalan dengan MQTT nonaktif.

## Perintah serial

Firmware utama (`main.cpp`):

| Tombol | Fungsi |
|---|---|
| `r` | Mulai rekam / simpan rekaman ke `/rekaman.csv` (LittleFS) |
| `d` | Dump rekaman ke serial (dipakai `make pull` di `model/`) |
| `s` | Status: fase kualitas, jumlah beat, antrean, sampel hilang, status MQTT, PDSR, RSSI |
| `y` | Toggle sumber sinyal ADC ↔ replay `golden_raw`; replay melewati gerbang kalibrasi |
| `k` | Toggle lewati gerbang kalibrasi (hanya untuk bench) |
| `m` | Toggle publikasi MQTT |
| `q` | Toggle laporan kualitas sinyal per detik |

Program uji (`hwtest.cpp`):

| Tombol | Fungsi |
|---|---|
| `y` | Ganti sumber: ADC → dummy teratur → rekaman 208 |
| `+` / `-` | BPM dummy teratur ±10 (30–180) |
| `[` / `]` | Nada buzzer −/+250 Hz (500–6.000 Hz), bunyi 300 ms |
| `r` / `d` / `s` | Rekam, dump, status (protokol sama dengan `main.cpp`) |
| `a` | Toggle alir sampel mentah |
| `g` | Diagnosa rangkaian buzzer |

Tombol fisik pada `hwtest`: B1 bisu/bunyi bip per beat (tahan 2 detik = ganti
sumber), B2 bekukan gelombang dan bip, B3 mulai/simpan rekaman.

## Arsip

`arsip/buzztest.cpp` adalah uji buzzer terpisah (GPIO 13 dan LED onboard saja)
yang dipakai untuk memisahkan masalah buzzer dari `hwtest`. Env `buzztest`
tidak lagi tercantum di `platformio.ini`, sehingga berkas ini tidak di-build.
Indeks arsip: [`model/docs/arsip/README.md`](../model/docs/arsip/README.md).
