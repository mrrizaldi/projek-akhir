# Rencana: Menu di Perangkat, Resolver Broker, dan Firmware Modular

**Tanggal:** 2026-10-13
**Status:** disetujui user, dalam pengerjaan. Pindahkan ke `docs/arsip/` setelah selesai.
**Ruang lingkup:** `firmware/**`, `model/scripts/` (alat bantu laptop), `model/Makefile`,
dokumentasi firmware & walkthrough terkait.

## Keputusan user

| Topik | Keputusan |
|---|---|
| Ambang tekan lama | **800 ms** (event lama terpicu saat ambang tercapai + bip pendek; event pendek saat dilepas) |
| Replay rekaman | **Daftar beberapa rekaman** bernomor di LittleFS, dipilih dari menu |
| Catu baterai | 18650 → TP4056 → konverter DC-DC keluaran ±4,x V → pin 5V board |
| Broker | Masih lokal (laptop). **Tanpa mDNS** (diputuskan user): host = IP di daftar; `make broker-info` mencetak IP & SSID laptop |
| Modularitas | `main.cpp` hanya merangkai modul |

## Peta tombol

| Konteks | B1 (GPIO4) | B2 (GPIO5) | B3 (GPIO6) |
|---|---|---|---|
| Monitor, pendek | bisu/bunyi bip detak | bekukan layar | rekam / simpan |
| Monitor, lama | — (replay DICABUT dari sini) | buka menu | — |
| Menu, pendek | turun | kembali satu tingkat (di akar = keluar) | naik |
| Menu, lama | keluar ke monitor | pilih / enter | keluar ke monitor |

## Pohon menu

```
MENU
├─ Sumber sinyal ─ Sensor (ADC) | Replay acuan (golden 208) | Replay rekaman → daftar /rekam/NNN.csv
├─ Kalibrasi ───── Mulai ulang | Lewati (bench) ON/OFF | Status (stabil x/600 s, RR tenang, ayun)
├─ Tes perangkat ─ Buzzer | Layar (pola warna) | ADC & lead-off | INA219 | Tombol
├─ Ukur daya ───── Jalankan tangga p0-p5 → hasil di layar + /daya/NNN.csv
├─ Jaringan ────── WiFi (daftar) | Broker (daftar IP) | MQTT ON/OFF | Status
└─ Info ────────── IP, RSSI, broker aktif, V/I INA219, uptime, versi build
```

- Pilihan WiFi, broker, sumber disimpan di NVS (`Preferences`, bagian core arduino-esp32).
- Daftar WiFi/broker di `include/wifi_secrets.h` sebagai array; `wifi_secrets.example.h`
  diperbarui dengan contoh. Kompatibel mundur: makro tunggal `WIFI_SSID/WIFI_PASS/TB_HOST`
  lama tetap diterima sebagai entri pertama.
- Perintah serial lama (`r d s q y m k p0-p5`) tetap berlaku sebagai jalur cadangan.

## Konfigurasi broker

- `wifi_secrets.h`: `WIFI_DAFTAR {ssid, sandi}` dan `BROKER_DAFTAR {nama, host-IP, port, token}`;
  format lama satu entri tetap diterima. Pilihan indeks disimpan di NVS (`w<n>`, `b<n>`, menu).
- Tanpa mDNS: board dan laptop harus satu jaringan WiFi; IP laptop dicek dengan
  `make broker-info` (dari `model/`), yang juga mencetak SSID laptop.

## Modul firmware (sasaran)

| Modul | Isi |
|---|---|
| `tombol.*` | debounce, event PENDEK/LAMA per tombol (ambang 800 ms) |
| `tampilan.*` | layar monitor (dipindah dari main) + layar daftar/menu + layar hasil |
| `menu.*` | pohon menu = array struct statis + navigasi + aksi (pointer fungsi) |
| `gerbang.*` | penilaian kualitas, fase kalibrasi |
| `rekam.*` | rekam, dump, daftar berkas, replay dari LittleFS |
| `daya.*` | tangga p0-p5, rata-rata INA219, simpan CSV |
| `konfig.*` | NVS + daftar WiFi/broker |
| `serial_cmd.*` | parser perintah serial |
| `main.cpp` | `setup`/`loop`, merangkai modul |

Tanpa kelas abstrak/framework. Logika uji perangkat dipakai bersama oleh menu Tes dan
`test/test_hw_*` (tidak ada salinan kode).

## Fase & gerbang lanjut

Tiap fase: `pio run`, `pio test -e native`, `pio test -e esp32-s3` lulus + cek serial di board.

0. **Selesai.** Daftar WiFi/broker + NVS, `make broker-info`, dokumentasi jaringan & rakitan baterai/INA219.
1. **Selesai.** Refactor modular tanpa ubah perilaku (native 23/23, board 34/34). Modul tambahan di luar tabel: `akuisisi` (ISR 360 Hz, sumber ADC/replay), `klasifikasi` (TFLite, publikasi).
2. Modul tombol + kerangka menu + layar menu; replay pindah dari B1-lama ke menu.
3. Menu Sumber (termasuk daftar rekaman), Kalibrasi, Jaringan, Info.
4. Menu Tes perangkat.
5. Menu Ukur daya mandiri (baterai, tanpa laptop) + `make pull-daya`.
6. Dokumentasi pemakaian menu. Paragraf tombol/menu di laporan Bab 3 = gate point (tanya user).

## Rakitan INA219 dengan baterai

Posisi yang dipakai: **sisi baterai** (sesuai catatan PCB rev2), supaya angka mencakup
rugi konverter dan bisa langsung dipakai menghitung umur baterai:

```
18650 ─ TP4056 (OUT+) ─► INA219 VIN+ ─► INA219 VIN− ─► konverter IN+ ─► konverter OUT+ ─► pin 5V board
          (OUT−) ───────────────────── GND bersama ──────────── konverter IN−/OUT− ──── GND board
INA219: VCC→3V3, GND→GND, SDA→GPIO17, SCL→GPIO18
```
Saat mengukur: USB dicabut (kalau tercolok, board ikut dicatu USB dan arus baterai tidak
mewakili). Tegangan bus INA219 terbaca ±3,0-4,2 V (tegangan baterai).
