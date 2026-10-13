# firmware/ — program ESP32-S3 (PlatformIO)

Firmware alat pemantau EKG: akuisisi AD8232 pada 360 Hz, preprocessing dan
deteksi R-peak on-device, klasifikasi aritmia per detak dengan TFLite Micro
(model INT8 dari `model/`), tampilan TFT (HR, gelombang, status, daya),
bip buzzer per detak, lalu publikasi hasil ke ThingsBoard lewat MQTT dengan
ring buffer PSRAM sebagai penyangga saat koneksi putus.

Board: ESP32-S3 N16R8 (16 MB flash, 8 MB PSRAM), board id PlatformIO
`4d_systems_esp32s3_gen4_r8n16`, di atas PCB rev1. Seluruh konfigurasi ada di
[`platformio.ini`](platformio.ini); semua perintah dijalankan dari folder ini.

Penjelasan rinci: [`firmware-walkthrough`](../model/docs/firmware-walkthrough.md)
(port preprocessing dan TFLM), [`mqtt-walkthrough`](../model/docs/mqtt-walkthrough.md)
(publikasi, PDSR, latensi), [`akuisisi-walkthrough`](../model/docs/akuisisi-walkthrough.md)
(merekam sinyal tubuh).

## Environment PlatformIO

| Env | Kegunaan | Sumber yang di-build | Library |
|---|---|---|---|
| `esp32-s3` (bawaan) | Firmware utama dan test di board | semua `src/` | Chirale_TensorFLowLite, Adafruit ST7735/ST7789, Adafruit GFX |
| `native` | Test unit di PC tanpa board | `ecg_pipeline.cpp`, `ecg_live.cpp`, `ina219.cpp`, `ecg_mqtt.cpp` | — |

`esp32-s3` memakai `-I test` karena `test/golden_ref.h` menjadi sumber sinyal
replay. Kadens deteksi memakai nilai bawaan `ECG_LIVE_TIAP = ECG_FS` (deteksi
tiap 1 detik); `-D ECG_LIVE_TIAP=90` tersedia sebagai knob ablasi.

## Perintah

```bash
pio run                                  # build env esp32-s3
pio run -t upload                        # build + flash firmware utama
pio device monitor                       # serial 115200
pio test -e native                       # 23 test di PC: test_preproc, test_ina219, test_mqtt
pio test -e esp32-s3                     # 33 test di board: test_preproc, test_inference, test_hw_*
pio test -e esp32-s3 -f test_hw_buzzer   # satu suite saja
pio test -e esp32-s3 -v                  # plus keluaran Serial (benchmark, bacaan perangkat)
pio device list                          # cek port
```

`pio run` tanpa `-e` hanya mem-build `esp32-s3` (`default_envs`). Env `native`
tidak memiliki `main()`, sehingga hanya dipakai lewat `pio test`. Saat
`pio test`, isi `main.cpp` dikecualikan (`PIO_UNIT_TESTING`), sehingga setiap
suite memiliki `setup()`/`loop()` sendiri.

## Test

| Suite | Env | Yang diuji |
|---|---|---|
| `test_preproc` | native, esp32-s3 | Bandpass, z-score, fitur RR, deteksi R, alur hidup; dibandingkan ke `golden_ref.h` |
| `test_ina219` | native | Konversi register INA219 ke mA dan V |
| `test_mqtt` | native | Payload JSON dan ring backlog MQTT |
| `test_inference` | esp32-s3 | Inferensi TFLM INT8 sama dengan interpreter PC, latensi, arena |
| `test_hw_buzzer` | esp32-s3 | GPIO 13 tersambung ke LEDC setelah SPI dan TFT terpasang, diam = HIGH, bunyi = gelombang kotak; tiga bip untuk didengar |
| `test_hw_tft` | esp32-s3 | Inisialisasi TFT dan transfer SPI satu layar penuh; pola warna untuk dilihat |
| `test_hw_adc` | esp32-s3 | ADC GPIO 1 terbaca, timer menghasilkan 360 sampel per detik; nilai mentah dan LO dicetak |
| `test_hw_ina219` | esp32-s3 | INA219 menjawab di I2C, bacaan dalam rentang fisik chip; nilai dicetak |
| `test_hw_integrasi` | esp32-s3 | Replay `golden_raw` lewat ISR 360 Hz → antrean → `ecg_live` → HR → inferensi, dengan TFT, INA219, dan buzzer aktif: tanpa sampel hilang, HR dan label sama dengan anotasi/PC |

Test perangkat hanya menjadikan syarat lulus hal yang dapat diukur tanpa
manusia dan tanpa elektroda. Bunyi buzzer dan isi layar dinilai langsung
(instruksi dicetak dengan `-v`); nilai ADC, LO, dan INA219 bergantung pada
elektroda dan catu, sehingga dicetak dan tidak dijadikan syarat lulus.

## Struktur

| Lokasi | Isi |
|---|---|
| `src/main.cpp` | Firmware utama: ISR ADC 360 Hz → antrean → loop; gerbang kalibrasi sinyal; inferensi; TFT, buzzer, tombol; rekam ke LittleFS; perintah serial |
| `src/perangkat.cpp` | Pemasangan perangkat PCB: SPI dan TFT, buzzer LEDC, tombol, pin LO, ADC |
| `src/ecg_pipeline.cpp` | Port preprocessing Python ke C (bandpass kausal, deteksi Pan-Tompkins, penyelarasan R, window + z-score, fitur RR) |
| `src/ecg_live.cpp` | Alur streaming: sampel masuk satu per satu, beat siap-klasifikasi keluar |
| `src/ecg_mqtt.cpp` | Payload JSON, antrean backlog, klien MQTT di atas `WiFiClient` (tanpa library tambahan) |
| `src/ina219.cpp` | Konversi register INA219 ke mA/V (fungsi murni) dan akses I2C |
| `include/` | Header kontrak; `perangkat.h` memuat pin map; `model_int8.h` dan `ecg_preproc.h` hasil generate (lihat [`include/README.md`](include/README.md)) |
| `test/golden_ref.h` | Golden reference Python, hasil `model/scripts/export_golden.py` |
| `test/test_*` | Suite Unity (lihat bagian Test) |

## Pin map (PCB rev1)

Sumber tunggal: [`include/perangkat.h`](include/perangkat.h).

| Fungsi | GPIO |
|---|---|
| EKG OUT AD8232 | 1 (ADC1_CH0) |
| AD8232 LO+ / LO− | 42 / 2 (pull-up internal; 1 = elektroda lepas) |
| TFT ST7789 SCK / MOSI / RST / DC | 9 / 8 / 10 / 11 (CS ke GND, BLK ke 3V3) |
| Buzzer (modul pasif A18009, aktif LOW, VCC 3V3) | 13 |
| Tombol B1 / B2 / B3 | 4 / 5 / 6 (ke GND, pull-up internal) |
| INA219 SDA / SCL | 17 / 18 (alamat 0x40, VCC modul 3V3) |
| NeoPixel onboard | 48 |

Urutan pemasangan wajib: `SPI.begin(9, -1, 8)` dipanggil sebelum buzzer
dipasang ke LEDC. Di ESP32-S3, MISO −1 diganti MISO bawaan FSPI, yaitu GPIO 13,
dan pin itu dijadikan input; bila LEDC dipasang lebih dulu, buzzer kehilangan
pinnya dan tidak berbunyi. `perangkat_mulai()` memegang urutan ini dan
`test_hw_buzzer` memeriksanya dari register GPIO matrix.

## Antarmuka alat

Layar TFT 320×172 (landscape):

- atas: HR (merah bila detak terakhir diklasifikasi aritmia; `--` bila tidak ada
  detak selama 3 detik), arus/tegangan/daya INA219, dan status
  (`REC <detik>`, `REPLAY`, `KALIB`, `BAIK`, `BURUK`, warnanya sama dengan NeoPixel);
- tengah: gelombang EKG tersaring 0,5–40 Hz, skala otomatis per sapuan;
- bawah: tiga kotak tombol, kuning selama ditekan.

Buzzer berbunyi 50 ms per detak dan 250 ms untuk detak yang diklasifikasi
aritmia. Bip dan gelombang ditunda sama rata 1,46 detik dari R (kadens deteksi
+ post-window + margin), sehingga jarak antar-bip sama dengan RR dan R
tergambar tepat saat bipnya berbunyi. HR dan bip hanya muncul bila ayunan
sinyal bersih di atas ambang (gerbang yang sama dengan publikasi MQTT).

| Tombol | Tekan | Tahan 2 detik |
|---|---|---|
| B1 (GPIO 4) | bisu / bunyikan bip detak | ganti sumber ADC ⇄ replay (setara `y`) |
| B2 (GPIO 5) | bekukan / jalankan gelombang dan bip | — |
| B3 (GPIO 6) | mulai / simpan rekaman (setara `r`) | — |

Setiap tekanan tombol berbunyi klik 20 ms. Dump rekaman hanya lewat serial `d`
(dipakai `make pull` di `model/`).

Indikator NeoPixel: merah = merekam, biru = kalibrasi (stabilisasi), oranye =
ayunan sinyal di bawah ambang, hijau = sinyal baik, merah berkedip =
inisialisasi TFLM gagal.

## Kredensial WiFi dan ThingsBoard

```bash
cp include/wifi_secrets.example.h include/wifi_secrets.h
```

Isi `WIFI_SSID`, `WIFI_PASS`, `TB_HOST` (IP laptop yang menjalankan
`docker compose`, bukan `localhost`), `TB_PORT`, dan `TB_TOKEN` (access token
device, dicetak oleh `dashboard/smoke_test.py`). `wifi_secrets.h` di-ignore git.
Tanpa berkas ini firmware tetap ter-build dan berjalan dengan MQTT nonaktif.

## Perintah serial

| Huruf | Fungsi |
|---|---|
| `r` | Mulai rekam / simpan rekaman ke `/rekaman.csv` (LittleFS) |
| `d` | Dump rekaman ke serial (dipakai `make pull` di `model/`) |
| `s` | Status: fase kualitas, jumlah beat, antrean, sampel hilang, status MQTT, PDSR, RSSI, INA219, bisu/beku |
| `y` | Toggle sumber sinyal ADC ↔ replay `golden_raw`; replay melewati gerbang kalibrasi |
| `k` | Toggle lewati gerbang kalibrasi (hanya untuk bench) |
| `m` | Toggle publikasi MQTT |
| `q` | Toggle laporan kualitas sinyal per detik |
