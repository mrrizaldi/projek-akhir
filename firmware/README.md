# firmware/ — program ESP32-S3 (PlatformIO)

Firmware alat pemantau EKG: akuisisi AD8232 pada 360 Hz, preprocessing dan
deteksi R-peak on-device, klasifikasi aritmia per detak dengan TFLite Micro
(model INT8 dari `model/`), tampilan TFT (HR, gelombang, status, daya),
bip buzzer per detak, lalu publikasi hasil ke ThingsBoard lewat MQTT dengan
ring buffer PSRAM sebagai penyangga saat koneksi putus. Sumber sinyal,
kalibrasi, tes perangkat, ukur daya, dan jaringan diatur dari menu di layar
dengan tiga tombol (bagian Pemakaian di perangkat).

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
pio test -e esp32-s3                     # 29 test di board: test_preproc, test_inference, test_hw_*
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
| `test_hw_buzzer` | esp32-s3 | `diag_buzzer()`: GPIO 13 tersambung ke LEDC setelah SPI dan TFT terpasang, diam = HIGH, bunyi = gelombang kotak; tiga bip untuk didengar |
| `test_hw_tft` | esp32-s3 | Inisialisasi TFT, lalu `diag_layar()`: transfer SPI satu layar penuh; pola warna untuk dilihat |
| `test_hw_adc` | esp32-s3 | `diag_adc()`: ADC GPIO 1 terbaca; timer menghasilkan 360 sampel per detik; nilai mentah dan LO dicetak |
| `test_hw_ina219` | esp32-s3 | `diag_ina219()`: INA219 menjawab di I2C, bacaan dalam rentang fisik chip; nilai dan register mentah (shunt, bus, OVF) dicetak |
| `test_hw_tombol` | esp32-s3 | Pin B1–B3 HIGH saat diam (tidak macet), `diag_tombol()` kembali tepat pada batas waktu; tombol tidak boleh ditekan selama suite ini. Uji tekan sungguhan lewat menu Tes perangkat |
| `test_hw_integrasi` | esp32-s3 | Replay `golden_raw` lewat ISR 360 Hz → antrean → `ecg_live` → HR → inferensi, dengan TFT, INA219, dan buzzer aktif: tanpa sampel hilang, HR dan label sama dengan anotasi/PC |

Test perangkat hanya menjadikan syarat lulus hal yang dapat diukur tanpa
manusia dan tanpa elektroda. Bunyi buzzer dan isi layar dinilai langsung
(instruksi dicetak dengan `-v`); nilai ADC, LO, dan INA219 bergantung pada
elektroda dan catu, sehingga dicetak dan tidak dijadikan syarat lulus.
Fungsi `diag_*` di `src/diagnosa.cpp` dipakai bersama oleh suite `test_hw_*`
dan menu Tes perangkat; tidak ada salinan logika uji.

Jumlah test: native 23 (`test_preproc` 11, `test_ina219` 6, `test_mqtt` 6);
board 29 (`test_preproc` 11, `test_inference` 5, `test_hw_integrasi` 5,
`test_hw_tft` 2, `test_hw_adc` 2, `test_hw_tombol` 2, `test_hw_buzzer` 1,
`test_hw_ina219` 1).

## Struktur

| Lokasi | Isi |
|---|---|
| `src/main.cpp` | Firmware utama: hanya merangkai modul di bawah (`setup()`/`loop()`) dan memetakan event tombol mode monitor; selama menu terbuka event diteruskan ke `menu.cpp` |
| `src/akuisisi.cpp` | Timer ISR 360 Hz → antrean → `loop()`; sumber sinyal ADC AD8232, replay acuan `golden_raw`, atau replay rekaman `/rekam/NNN.csv`; pilihan tersimpan di NVS |
| `src/gerbang.cpp` | Kualitas sinyal (ayunan 1 detik, clipping) dan fase kalibrasi → pemantauan |
| `src/klasifikasi.cpp` | Inferensi TFLM INT8 per beat dan publikasi hasilnya ke antrean MQTT |
| `src/tampilan.cpp` | Layar TFT (monitor dan layar menu), NeoPixel, buzzer (klik, bip detak, bip kalibrasi) |
| `src/tombol.cpp` | Debounce dan event tekan/pendek/lama (ambang 800 ms) per tombol B1–B3; event suntikan dari serial `t`/`T` |
| `src/menu.cpp` | Pohon menu (array struct statis + pointer fungsi), navigasi tiga tombol, halaman teks diperbarui 1 Hz |
| `src/diagnosa.cpp` | Tes perangkat (buzzer, layar, ADC & lead-off, INA219, tombol) untuk menu Tes perangkat dan `test_hw_*` |
| `src/rekam.cpp` | Rekaman mentah: buffer PSRAM, berkas bernomor `/rekam/NNN.csv` di LittleFS, daftar, dump, hapus, muat untuk replay |
| `src/daya.cpp` | Pembacaan INA219, tangga ukur daya `p0`–`p5` (serial `p`), tangga mandiri dengan hasil `/daya/NNN.csv` (menu Ukur daya, serial `V`/`v`) |
| `src/konfig.cpp` | Daftar WiFi dan broker dari `wifi_secrets.h`; pilihan WiFi, broker, dan sumber sinyal di NVS |
| `src/serial_cmd.cpp` | Perintah serial (bagian Perintah serial) |
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

## Catu daya dan pengukuran arus

### Rangkaian catu baterai

Board dicatu sel 18650 lewat modul pengisi TP4056 dan konverter DC-DC yang
keluarannya (±4,x V) masuk ke pin 5V board. INA219 disisipkan di sisi baterai,
di antara keluaran TP4056 dan masukan konverter:

```
18650 ─ TP4056 OUT+ ─► INA219 VIN+ ─(shunt 0,1 Ω)─ INA219 VIN− ─► konverter IN+ ─► konverter OUT+ ─► pin 5V board
        TP4056 OUT− ─────────────────── GND bersama ──────────── konverter IN−/OUT− ──────────── GND board

INA219 logika: VCC → 3V3 board, GND → GND board, SDA → GPIO 17, SCL → GPIO 18
```

| Pin INA219 | Sambungan | Kelompok |
|---|---|---|
| `VIN+` | TP4056 `OUT+` | jalur arus |
| `VIN−` | konverter `IN+` | jalur arus |
| `VCC` | 3V3 board (bukan 5V: pull-up I2C modul terhubung ke VCC) | logika |
| `GND` | GND board, sama dengan TP4056 `OUT−` dan GND konverter | logika |
| `SDA` / `SCL` | GPIO 17 / GPIO 18 | logika |

GND rangkaian diambil dari `OUT−` TP4056, bukan `B−`, agar proteksi
baterai modul tetap berada di jalur. Sambungan jalur arus disolder, karena
seluruh arus alat melewatinya.

Posisi sisi baterai dipilih karena arus yang terbaca adalah arus yang benar-benar
ditarik dari sel, sudah termasuk rugi konverter. Umur baterai dihitung
langsung sebagai kapasitas (mAh) dibagi arus terukur, tanpa asumsi efisiensi
konverter dan regulator. Tegangan bus yang dibaca INA219 (`VIN−` terhadap GND)
adalah tegangan baterai dikurangi jatuh tegangan shunt, yaitu 3,0–4,2 V.

### Syarat dan pemeriksaan saat mengukur

1. **USB board dicabut.** Bila USB tercolok, board ikut dicatu VBUS USB dan
   arus di sisi baterai tidak mewakili konsumsi alat. Masukan pengisi TP4056
   juga dicabut, agar arus berasal dari sel dan tegangan bus adalah tegangan
   sel.
2. Nyalakan alat dari baterai. Layar atas menampilkan arus, tegangan, dan daya
   INA219; nilai yang sama tercetak di baris `INA219` pada serial `s`.
3. Bacaan yang benar: `V` 3,0–4,2 V dan `I` positif dan stabil.

| Bacaan | Arti | Tindakan |
|---|---|---|
| `V` ≈ 0 V, `I` melompat-lompat | `VIN+`/`VIN−` mengambang (tidak tersambung ke jalur arus) | Periksa sambungan `VIN±` |
| `I` negatif | `VIN+` dan `VIN−` tertukar | Tukar dua kabel `VIN`; tidak ada komponen yang rusak |
| `I` ≈ 0 mA sementara alat menyala | Arus mengalir lewat jalur lain (USB masih tercolok) | Cabut USB |
| INA219 tidak menjawab | Kabel I2C atau VCC modul | `pio test -e esp32-s3 -f test_hw_ina219 -v` |

Rentang ukur: INA219 dikonfigurasi PGA ÷8 (`INA219_CONFIG = 0x3FFF` di
[`include/ina219.h`](include/ina219.h)), ±320 mV pada shunt 0,1 Ω = ±3,2 A,
dengan resolusi 10 µV / 0,1 Ω = 0,1 mA. Arus di sisi baterai lebih besar dari
arus di sisi 5V dengan faktor V_keluaran / (V_baterai × efisiensi konverter),
sehingga burst TX WiFi terbaca paling besar saat sel mendekati 3,0 V. Puncak
burst dirata-ratakan oleh konversi 128 sampel (±68 ms). Bit `OVF` register bus
(dicetak `test_hw_ina219 -v`) menandai arus di luar rentang.

### Hal yang perlu dicek pada rakitan

- **Margin regulator 3,3 V board.** Keluaran konverter ±4,x V masuk ke pin 5V,
  lalu ke regulator 3,3 V board. Tegangan masukan minimum regulator tersebut
  belum diverifikasi di repo ini. Identifikasi komponen regulator pada board
  N16R8 (tanda pada kemasan atau skematik board), periksa tegangan dropout di
  datasheet-nya pada arus burst WiFi, dan bandingkan dengan keluaran konverter
  saat beban. Bila margin tipis, gejalanya reset `Brownout detector was
  triggered` saat WiFi aktif (mode `p5`). Pemeriksaan langsung: ukur pin 3V3
  dengan multimeter selama `p5` berjalan; nilainya harus tetap sekitar 3,3 V.
- Bila jalur dari pin 5V ke regulator melewati dioda (periksa skematik board),
  jatuh tegangan dioda ikut mengurangi margin di atas.

Arti tiap anak tangga `p0`–`p5`, kriteria sah, dan prosedur lewat laptop
(`model/scripts/measure_power.py`):
[`model/docs/firmware-walkthrough.md`](../model/docs/firmware-walkthrough.md) §5d.

### Ukur daya tanpa laptop

Tangga `p0`–`p5` dijalankan board sendiri dari menu **Ukur daya**, sehingga
selama pengukuran tidak ada kabel USB yang ikut mencatu board. Hasil disimpan
ke `/daya/NNN.csv` di LittleFS dan ditarik ke laptop sesudahnya.

Syarat: INA219 terdeteksi saat boot (tanpa INA219 tangga dibatalkan dengan
pesan `tangga: INA219 tidak terdeteksi, batal`). Agar `p5` mewakili operasi
normal, WiFi dan broker aktif harus terjangkau selama pengukuran.

1. Rakit INA219 di sisi baterai sesuai bagian Rangkaian catu baterai di atas.
2. Cabut USB board dan masukan pengisi TP4056, lalu nyalakan alat dari baterai.
   Baris atas layar monitor harus menunjukkan `V` 3,0–4,2 V dan `I` positif dan
   stabil (tabel bacaan di atas).
3. Tahan **B2** sampai bip pendek (800 ms) untuk membuka menu. Pilih
   **Ukur daya → Mulai tangga p0-p5** (B1/B3 pendek memindah sorotan, tahan B2
   memilih).
4. Menu menutup dan layar kembali ke monitor selama tangga berjalan, supaya
   langkah `p4` mengukur beban UI yang sebenarnya. Bila sumber sinyal ADC,
   tangga berpindah ke replay acuan dan kembali ke ADC di akhir; bila sumber
   sudah replay (acuan atau rekaman), sumber itu yang dipakai. Jangan menekan
   tombol.
5. Tunggu ±7 menit (6 langkah × 7 jendela × 10 detik; jendela pertama tiap
   langkah dibuang sebagai transien). Di akhir, board kembali ke operasi normal
   dan halaman **Ukur daya** terbuka sendiri.
6. Baca tabel di layar: satu baris per langkah berisi mode, arus rata-rata (mA),
   dan daya (mW); nomor berkas `#NNN` di ujung baris pertama. Tanda `!` sesudah
   nama mode (mis. `p3!`) berarti langkah itu **tidak sah** (tegangan bus < 1 V,
   ada sampel hilang, tidak ada beat, atau arus tidak naik lebih dari 2 × sd
   dari langkah sebelumnya). Halaman yang sama dapat dibuka lagi lewat
   **Ukur daya → Hasil terakhir**.
7. Colokkan USB ke laptop, tutup monitor serial lain, lalu dari folder `model/`:

   ```bash
   make pull-daya          # berkas terakhir
   make pull-daya N=3      # berkas /daya/003.csv
   ```

   Hasil: `model/artifacts/metrics/daya/<YYYYmmdd-HHMM>-board-NNN.csv` (kolom
   `waktu,mode,n,I_mA,sd_mA,V,P_mW,beat,lewat,replay,sah`), ringkasan per mode
   di terminal, dan validasi ulang dengan kriteria `measure_power.py`. Skrip
   keluar dengan kode 1 dan mencetak `GAGAL (TIDAK SAH)` beserta alasannya bila
   ada langkah yang tidak sah. Port lain: `ECG_PORT=/dev/ttyACM1 make pull-daya`.

Tangga yang sama dapat dimulai lewat serial `V`; berkas di board didaftar dengan
`v` dan dicetak dengan `v<n>`. Uji singkat jalur ini tanpa menunggu 7 menit:
`PLATFORMIO_BUILD_FLAGS="-DDAYA_JENDELA_MS=2000 -DDAYA_BLOK=2" pio run -t upload`.

## Antarmuka alat

Layar TFT 320×172 (landscape):

- atas: HR (merah bila detak terakhir diklasifikasi aritmia; `--` bila tidak ada
  detak selama 3 detik), arus/tegangan/daya INA219, dan status
  (`REC <detik>`, `REPLAY` untuk replay acuan, `RP#NNN` untuk replay rekaman,
  `KALIB`, `BAIK`, `BURUK`, warnanya sama dengan NeoPixel);
- tengah: gelombang EKG tersaring 0,5–40 Hz, skala otomatis per sapuan;
- bawah: tiga kotak tombol berlabel keadaan (`B1 BUNYI`/`BISU`,
  `B2 JALAN`/`BEKU`, `B3 REC`/`STOP`), kuning selama ditekan.

Buzzer berbunyi 50 ms per detak dan 250 ms untuk detak yang diklasifikasi
aritmia. Bip dan gelombang ditunda sama rata 1,46 detik dari R (kadens deteksi
+ post-window + margin), sehingga jarak antar-bip sama dengan RR dan R
tergambar tepat saat bipnya berbunyi. HR dan bip hanya muncul bila ayunan
sinyal bersih di atas ambang (gerbang yang sama dengan publikasi MQTT).
Selama fase kalibrasi bip detak senyap; bunyi panjang 600 ms menandai
kalibrasi mulai (boot, ganti sumber, Kalibrasi → Mulai ulang, lewati
kalibrasi OFF) dan selesai (masuk fase BAIK).

Indikator NeoPixel: merah = merekam, biru = kalibrasi (stabilisasi), oranye =
ayunan sinyal di bawah ambang, hijau = sinyal baik, merah berkedip =
inisialisasi TFLM gagal. Arti tombol dan menu: bagian Pemakaian di perangkat.

## Pemakaian di perangkat

Tiga tombol B1 (GPIO 4), B2 (GPIO 5), B3 (GPIO 6). Tekan **pendek** = dilepas
sebelum 800 ms, aksinya terjadi saat dilepas. Tekan **lama** = masih ditahan
saat 800 ms tercapai, aksinya terjadi saat itu juga (tanpa menunggu dilepas)
dan ditandai bip pendek. Setiap tekanan berbunyi klik 20 ms.

### Peta tombol

| Konteks | B1 | B2 | B3 |
|---|---|---|---|
| Monitor, pendek | bisu / bunyikan bip detak | bekukan / jalankan gelombang dan bip | mulai / simpan rekaman (setara `r`) |
| Monitor, lama | — | buka menu | — |
| Menu, pendek | turun (melingkar) | kembali satu tingkat; di akar = tutup menu | naik (melingkar) |
| Menu, lama | langsung ke monitor | pilih / masuk | langsung ke monitor |

Di halaman teks (Status, Info, hasil tes, hasil ukur daya) B1/B3 pendek tidak
berbuat apa-apa; B2 pendek kembali. Dua baris bawah layar menu selalu
menampilkan petunjuk tombol yang berlaku.

Menu hanya mengganti isi layar dan arti tombol. Akuisisi, deteksi, inferensi,
rekaman, publikasi MQTT, NeoPixel, dan bip detak tetap berjalan selama menu
terbuka. Gelombang tidak digambar selama menu terbuka; layar monitor digambar
ulang saat menu ditutup.
Rekaman yang sedang berjalan tetap merekam, dan untuk menyimpannya menu
ditutup lebih dulu lalu B3 ditekan.

### Pohon menu

```
MENU
├─ Sumber sinyal ── Sensor (ADC) | Replay acuan (208) | Replay rekaman ─► daftar /rekam/NNN.csv
├─ Kalibrasi ────── Mulai ulang | Lewati (bench) ON/OFF | Status
├─ Tes perangkat ── Buzzer | Layar (pola warna) | ADC & lead-off | INA219 | Tombol (10 s)
├─ Ukur daya ────── Mulai tangga p0-p5 | Hasil terakhir
├─ Jaringan ─────── WiFi ─► daftar | Broker ─► daftar | MQTT ON/OFF | Status
└─ Info
```

Tanda `*` di sebelah kanan menandai pilihan aktif, `>` menandai submenu.
Pilihan sumber sinyal, WiFi, dan broker disimpan di NVS dan dipulihkan saat
boot.

| Halaman | Isi dan aksi |
|---|---|
| Sumber sinyal | **Sensor (ADC)**: AD8232 lewat elektroda. **Replay acuan (208)**: `golden_raw` record 208 diputar berulang (setara `y`). **Replay rekaman**: daftar berkas `/rekam/NNN.csv` beserta durasinya; memilih satu memuat berkas ke PSRAM (maksimal 300 detik pertama) lalu memutarnya berulang dan kembali ke halaman Sumber sinyal. Rekaman yang gagal dimuat (< 1 detik) tidak mengubah sumber. Ganti sumber memulai sesi kalibrasi baru dan mengenolkan hitungan beat. Kedua replay melewati syarat waktu-stabil dan RR-tenang gerbang kalibrasi |
| Kalibrasi | **Mulai ulang**: sesi kalibrasi baru dan hitungan klasifikasi dari nol. **Lewati (bench)**: setara `k`; OFF memulai sesi baru dengan gerbang penuh. **Status**: fase, waktu stabil x/600 s, RR tenang x/30 s, ayunan dan ambangnya, status lewati dan replay, sampel hilang; diperbarui tiap detik |
| Tes perangkat | Menjalankan satu fungsi `diag_*` (sama dengan `test_hw_*`) lalu membuka halaman hasil `LULUS`/`GAGAL` dengan ringkasan bacaan. Selama tes akuisisi dijeda. **Buzzer**: tiga bip untuk didengar. **Layar**: pola empat pita warna dan `TFT OK` ±2 detik. **ADC & lead-off**: rentang ADC ±1 detik dan status LO±; lulus tidak bergantung elektroda. **INA219**: V/I dan alamat; V bus < 1 V ditandai `bukan jalur catu`. **Tombol (10 s)**: tekan B1, B2, B3 masing-masing sekali dalam 10 detik |
| Ukur daya | **Mulai tangga p0-p5**: tangga mandiri (prosedur di bagian Ukur daya tanpa laptop). **Hasil terakhir**: tabel mode, arus, dan daya tangga terakhir; `pN!` = langkah tidak sah |
| Jaringan | **WiFi** / **Broker**: daftar dari `wifi_secrets.h`, memilih entri = setara `w<n>` / `b<n>` (disimpan, sambung ulang). **MQTT**: setara `m`. **Status**: status MQTT, SSID, IP, RSSI, host:port broker, jumlah terkirim dan backlog |
| Info | IP dan RSSI, broker aktif, V/I INA219, uptime, versi git (`git describe` saat build), tanggal dan jam build |

Setiap gerakan di menu dicetak ke serial (`menu: <judul> [i/n] <baris>`), dan
tombol dapat disuntik lewat serial `t1`–`t3` / `T1`–`T3`, sehingga navigasi
dapat diuji tanpa menekan tombol fisik.

## Konfigurasi jaringan dan broker

Board tersambung ke satu jaringan WiFi dan satu broker MQTT ThingsBoard pada
satu waktu. Keduanya dipilih dari daftar yang ditulis di `include/wifi_secrets.h`
saat build ([`src/konfig.cpp`](src/konfig.cpp)). Indeks pilihan aktif disimpan
di NVS (`Preferences`), sehingga tetap berlaku setelah board di-reset atau
dicabut catunya. Entri 0 dipakai bila belum pernah ada pilihan.

**Board dan laptop yang menjalankan broker harus terhubung ke jaringan WiFi
(SSID) yang sama.** Firmware tidak me-resolve nama host; host broker adalah
alamat IP laptop di jaringan tersebut, dan alamat itu hanya terjangkau dari
jaringan yang sama. Contoh kegagalan: board memakai SSID `myinternet`,
sedangkan laptop sedang tersambung ke SSID lain; WiFi board tersambung, tetapi
broker tidak pernah terjangkau. SSID yang sedang dipakai laptop dicetak oleh
`make broker-info`.

### Format `include/wifi_secrets.h`

`wifi_secrets.h` di-ignore git. Tanpa berkas ini firmware tetap ter-build dan
berjalan dengan MQTT nonaktif (satu baris `mqtt NONAKTIF` di serial saat boot).
Acuan format adalah [`include/wifi_secrets.example.h`](include/wifi_secrets.example.h);
contoh di bawah tidak memuat kredensial asli.

```c
#define WIFI_DAFTAR { \
    {"nama-wifi",  "sandi-wifi"}, \
    {"hotspot-hp", "sandi-hotspot"}, \
}

#define BROKER_DAFTAR { \
    {"laptop rumah",  "192.168.1.10", 1883, "token-device-thingsboard"}, \
    {"laptop kampus", "10.0.0.5",     1883, "token-device-thingsboard"}, \
}
```

| Daftar | Medan | Isi |
|---|---|---|
| `WIFI_DAFTAR` | `{ssid, sandi}` | Jaringan 2,4 GHz yang juga dipakai laptop/server broker |
| `BROKER_DAFTAR` | `{nama tampil, host, port, token}` | `nama tampil` hanya untuk daftar `b` dan log; `host` alamat IPv4 broker; `port` MQTT plaintext (1883); `token` access token device ThingsBoard |

Aturan isi:

- `host` wajib berupa alamat IP, misalnya `"192.168.1.10"`. Nama host
  (termasuk `localhost`) tidak di-resolve: firmware mencetak
  `mqtt: host broker "..." bukan alamat IP` dan MQTT dinonaktifkan. `localhost`
  juga salah secara makna, karena dari sisi board nama itu menunjuk board
  sendiri.
- Format lama dengan makro tunggal `WIFI_SSID`, `WIFI_PASS`, `TB_HOST`,
  `TB_PORT`, `TB_TOKEN` tetap diterima dan diperlakukan sebagai daftar
  berisi satu entri.
- Daftar boleh dipendekkan; indeks tersimpan yang melewati panjang daftar
  kembali ke entri 0.

### Mengisi dan mengganti server

1. Jalankan ThingsBoard di laptop, lalu ambil access token device:

   ```bash
   cd dashboard && docker compose up -d
   python3 smoke_test.py          # mencetak: device ... token=XXXX
   ```

2. Cetak SSID, IP, status port, dan saran entri:

   ```bash
   cd model && make broker-info
   ```

   Contoh keluaran:

   ```
   Hostname : debian-aldi
   SSID     : 0000  -> board harus terhubung ke SSID yang sama
   IPv4 LAN :
     wlp4s0       10.53.213.57
   Port localhost:
     1883  terbuka  (MQTT ThingsBoard)
     8080  terbuka  (UI/REST ThingsBoard)

   Saran entri (firmware/include/wifi_secrets.h):
     WIFI_DAFTAR:
       {"0000", "<sandi>"},
     BROKER_DAFTAR:
       {"laptop", "10.53.213.57", 1883, "<token>"},   // wlp4s0, berlaku selama IP ini
   ```

   Interface docker, bridge, veth, dan loopback diabaikan karena tidak
   terlihat dari board.

3. Salin `include/wifi_secrets.example.h` menjadi `include/wifi_secrets.h`
   (sekali saja), lalu isi `WIFI_DAFTAR` dengan SSID laptop dan
   `BROKER_DAFTAR` dengan IP laptop dan token.

4. Build dan flash: `pio run -t upload`.

5. Pilih entri aktif. Pilihan disimpan ke NVS:
   - serial `w` / `b` menampilkan daftar dengan tanda `*` pada entri aktif;
     `w<n>` memilih WiFi dan menyambung ulang, `b<n>` memilih broker dan
     menyambung ulang ke broker tersebut (`<n>` mulai dari 0);
   - menu perangkat **Jaringan → WiFi / Broker** menampilkan daftar yang sama;
     tahan B2 pada entri untuk memilihnya (bagian Pemakaian di perangkat);
   - tanpa pilihan tersimpan, entri 0 dipakai.

   Saat boot dan setiap kali pilihan berganti, serial mencetak
   `konfig: wifi <i>/<n> "<ssid>" | broker <i>/<n> <nama> (<host>:<port>)`.

6. Verifikasi dengan serial `s`: status MQTT `online` dan jumlah terkirim
   bertambah. Di UI ThingsBoard (<http://localhost:8080>), tab *Latest
   telemetry* device menerima beat baru.

Berpindah di antara entri yang sudah ada di daftar cukup lewat langkah 5,
tanpa build ulang. Menambah atau mengubah entri (termasuk IP laptop yang
berubah) memerlukan langkah 3–5.

### Memakai server selain laptop ini

Broker dapat berupa ThingsBoard di komputer lain dalam jaringan yang sama atau
di VPS. Syaratnya:

1. Server dapat dijangkau dari jaringan WiFi board lewat alamat IP: IP LAN
   untuk komputer di jaringan yang sama, IP publik untuk VPS. Nama DNS tidak
   didukung.
2. Port MQTT plaintext (bawaan 1883) terbuka di firewall server. Firmware tidak
   memakai TLS.
3. Token diambil dari device di server tersebut, bukan dari laptop ini. Pada
   server lain, jalankan `python3 smoke_test.py` di server itu (skrip memakai
   `localhost:8080`), atau salin access token dari UI ThingsBoard: *Entities →
   Devices → device → Copy access token*.
4. Tambahkan entri `{"nama", "IP", 1883, "token"}` ke `BROKER_DAFTAR`, lalu
   lanjutkan dari langkah 4 di atas.

### Troubleshooting

Status MQTT pada serial `s`: `no-wifi` = WiFi belum tersambung, `no-broker` =
WiFi tersambung tetapi broker tidak terjangkau, `tunggu-jam` = tersambung dan
menunggu sinkronisasi jam, `online` = normal, `mati` = MQTT dinonaktifkan.

| Gejala | Penyebab | Tindakan |
|---|---|---|
| `no-broker` terus-menerus, port 1883 di laptop `terbuka` | Board dan laptop berada di SSID berbeda | Bandingkan baris `SSID` di `make broker-info` dengan entri aktif di serial `w`; pindahkan laptop ke SSID board, atau pilih/tambah entri WiFi yang sama dengan laptop |
| Broker berhenti terjangkau setelah pindah jaringan atau restart laptop | IP laptop berubah (DHCP) | `make broker-info`, perbarui IP di `BROKER_DAFTAR`, flash ulang; reservasi DHCP di router mencegah perubahan IP |
| `make broker-info`: port 1883 `TERTUTUP` | ThingsBoard belum jalan atau belum selesai boot | `cd dashboard && docker compose up -d`, tunggu ±2 menit, ulangi |
| Port 1883 terbuka, SSID sama, board tetap `no-broker` | Firewall laptop memblokir TCP 1883 masuk | Buka TCP 1883 masuk dari subnet LAN |
| SSID sama, firewall terbuka, board tetap `no-broker` | *AP/client isolation* (umum di WiFi kampus, kantor, dan hotspot publik) memblokir lalu lintas antarklien | Pakai hotspot ponsel atau router sendiri untuk board dan laptop |
| `no-wifi` terus-menerus | SSID/sandi salah, atau jaringan hanya 5 GHz | Periksa entri `WIFI_DAFTAR`; ESP32-S3 hanya mendukung 2,4 GHz |
| `mqtt: host broker "..." bukan alamat IP` | `host` berisi nama, bukan IP | Ganti dengan IP dari `make broker-info` |
| `mqtt NONAKTIF: include/wifi_secrets.h belum ada` | Berkas belum dibuat | Langkah 3 |

## Perintah serial

| Huruf | Fungsi |
|---|---|
| `r` | Mulai rekam / simpan rekaman ke berkas bernomor baru `/rekam/NNN.csv` (LittleFS) |
| `l` | Daftar rekaman: nomor, ukuran, header tiap berkas, dan pemakaian LittleFS |
| `d` / `d<n>` | Dump rekaman terakhir / rekaman nomor `<n>` ke serial (`make pull` di `model/` memakai `d`) |
| `h<n>` | Hapus rekaman nomor `<n>` |
| `s` | Status tiga baris: fase kualitas, jumlah beat, antrean, sampel hilang; status MQTT, PDSR, RSSI; INA219, bisu/beku, lewati, mode daya, `sumber adc\|acuan\|rekaman <n>`, `menu 0/1` |
| `y` | Toggle sumber sinyal ADC ↔ replay acuan `golden_raw` (dari replay rekaman kembali ke ADC); selama replay gerbang kalibrasi dilewati. Pilihan disimpan di NVS seperti dari menu |
| `k` | Toggle lewati gerbang kalibrasi (hanya untuk bench); OFF memulai sesi baru dengan gerbang penuh |
| `p0`–`p5` | Satu anak tangga ukur daya, baris `DAYA` tiap 10 detik; `p` + huruf lain = operasi normal (`model/docs/firmware-walkthrough.md` §5d) |
| `V` | Mulai tangga daya mandiri `p0`–`p5` (sama dengan menu Ukur daya → Mulai), hasil ke `/daya/NNN.csv` |
| `v` / `v<n>` | Daftar berkas `/daya/` / cetak `/daya/<n>.csv` di antara `---MULAI---` dan `---SELESAI---` (`make pull-daya` memakai ini) |
| `t1`–`t3` / `T1`–`T3` | Suntik tekan pendek / lama tombol B1–B3; diproses sama dengan tombol fisik (uji menu tanpa menekan tombol) |
| `m` | Toggle publikasi MQTT |
| `w` / `w<n>` | Daftar `WIFI_DAFTAR` (`*` = aktif) / pilih entri `<n>`, disimpan di NVS lalu sambung ulang |
| `b` / `b<n>` | Daftar `BROKER_DAFTAR` (`*` = aktif) / pilih entri `<n>`, disimpan di NVS lalu sambung ulang |
| `q` | Toggle laporan kualitas sinyal per detik |

Nomor entri WiFi dan broker dimulai dari 0; nomor rekaman dan berkas daya dimulai dari 1.
Angka sesudah huruf ditunggu sampai 500 ms per digit, sehingga dapat diketik
langsung di `pio device monitor`; `t`/`T` hanya membaca satu digit. `d` ditolak
selama merekam.
