# Mainboard (PCB rev2)

Proyek KiCad untuk papan induk alat: ESP32-S3-DevKitC-1 N16R8, AD8232, TFT
ST7789 1,47", INA219, modul buzzer pasif, tiga tombol, dan jalur catu
baterai 18650 (TP4056 + boost MT3608) dengan saklar on-off. Semua modul
dipasang lewat header 2,54 mm. Papan dua lapis, 110 × 103 mm.

Kondisi: skematik dan layout lengkap, pemeriksaan otomatis lulus (lihat
**Pemeriksaan**). Belum difabrikasi, dan butir di **Yang belum terverifikasi**
harus dicek pada modul fisik sebelum Gerber dikirim.

## Berkas

| Berkas | Isi |
|---|---|
| `mainboard.kicad_pro`, `.kicad_sch`, `.kicad_pcb` | proyek KiCad 9.0.2 |
| `lib/PA.kicad_sym`, `lib/PA.pretty/` | simbol dan footprint ESP32-S3-DevKitC-1 (library proyek, dirujuk lewat `${KIPRJMOD}`) |
| `cek_board.py` | pemeriksaan netlist, ERC, DRC, dan paritas skematik–PCB |

Berkas dibuat dengan KiCad 9.0.2 dan bisa dibuka KiCad 10. Arah sebaliknya
tidak bisa: berkas KiCad 10 (misalnya skematik rev2 yang disusun dengan
KiCad 10.0.6) ditolak KiCad 9 dengan pesan `Failed to load schematic`.

## Peta pin

Sama dengan `firmware/include/perangkat.h`. Nomor pad U1 mengikuti footprint
resmi Espressif: pad 1–22 kolom kiri dari atas (3V3 … GND), pad 23–44 kolom
kanan dari bawah (GND … GND). Urutan fisik kedua kolom sudah dicocokkan 44/44
dengan gambar pinout resmi ESP32-S3-DevKitC-1.

| Fungsi | GPIO | Pad U1 | Net | Tujuan |
|---|---|---|---|---|
| EKG OUT / LO− / LO+ | 1 / 2 / 42 | 41 / 40 / 39 | `ECG_OUT` / `ECG_LON` / `ECG_LOP` | J3 pin 3 / 4 / 5 |
| TFT SCK / MOSI | 9 / 8 | 15 / 12 | `TFT_SCK` / `TFT_MOSI` | J2 pin 3 / 4 |
| TFT RES / DC | 10 / 11 | 16 / 17 | `TFT_RST` / `TFT_DC` | J2 pin 5 / 6 |
| Buzzer | 13 | 19 | `BUZZ` | J9 pin 2 |
| Tombol 1 / 2 / 3 | 4 / 5 / 6 | 4 / 5 / 6 | `BTN1..3` | SW1..3 ke GND |
| INA219 SDA / SCL | 17 / 18 | 10 / 11 | `I2C_SDA` / `I2C_SCL` | U2 pin 4 / 3 |
| 3V3 | – | 1, 2 | `+3V3` | semua VCC modul, SDN AD8232, BLK TFT |
| 5V | – | 21 | `+5V` | keluaran D2 |
| GND | – | 22, 23, 24, 44 | `GND` | semua pin GND DevKit tersambung |

Urutan pin header modul:

| Ref | Modul | Pin 1 → n |
|---|---|---|
| J3 | AD8232 | GND, 3V3, OUT, LO−, LO+, SDN |
| J2 | TFT ST7789 | GND, VCC, SCL, SDA, RES, DC, CS, BLK (CS ke GND, BLK ke 3V3) |
| U2 | INA219 | VCC, GND, SCL, SDA, VIN−, VIN+ |
| J9 | buzzer A18009 | GND, I/O, VCC |
| J1 | boost MT3608 | VIN+, VIN−, VOUT+, VOUT− |
| J10 | saklar on-off berlampu (di casing) | masuk (VSYS), keluar ke boost (VSW), GND lampu |
| J4 / J5 / J6 | TP4056 | IN+ IN− / B+ B− / OUT+ OUT− |
| J8 | kabel holder 18650 (JST PH) | +, − |

## Catu daya

```
 J8 baterai ── J5 B+/B− (TP4056) ── J6 OUT+ = VBAT_OUT ── U2 VIN+ ─shunt─ VIN− = VBAT_SENSE
                                                                             │
                     J4 IN+ = VCHG ──┬── gate Q1 (R1 10k ke GND)             D
                                     │                                   Q1 AO3401A
                                     └── D1 SS34 ──► VSYS ◄──────────────── S
                                                      │
                                              J10 saklar on-off
                                                      │ VSW
                                     J1 VIN+ ◄────────┘    J1 VOUT+ = VBOOST ── D2 SS34 ──► +5V ── U1 pin 5V, C1 47 µF, C2 100 nF
```

- Tanpa charger: gate Q1 ditarik R1 ke GND, Q1 menyala, baterai mencatu boost.
- Dengan charger: VCHG 5 V mematikan Q1, sehingga baterai hanya menerima arus
  isi dari TP4056 dan tidak mencatu beban. Boost dicatu dari VCHG lewat D1.
  Katoda D1 ada di VSYS (masukan boost), bukan di +5V. Kalau katoda D1 di +5V,
  body diode Q1 tetap mengalirkan baterai ke boost dan sel terkuras selama
  dicas.
- Saklar J10 memutus VSYS sebelum boost. OFF berarti alat mati total, juga
  saat charger tercolok, sedangkan pengisian baterai tetap berjalan karena
  TP4056 ada di depan saklar. Lampu saklar dicatu dari VSYS (±3,0–4,6 V).
- R2 1 MΩ (R_Dummy di skematik rev2) dipertahankan apa adanya: beban ±4 µA
  dari VBAT_SENSE ke GND.

## Layout

| Area | Isi | Alasan |
|---|---|---|
| Tengah | U1, USB menghadap tepi bawah | semua GPIO terpakai ada di kolom kiri kecuali EKG |
| Kanan atas | J3 AD8232, C4 | pad 39–41 U1 sejajar J3 pin 3–5, jalur EKG lurus 9 mm |
| Kanan bawah | jalur baterai, INA219, Q1, D1, D2, header TP4056/boost/baterai | jauh dari AD8232; modul boost di luar papan lewat kabel |
| Kiri | TFT, buzzer, tombol | SPI TFT berlawanan sisi dengan jalur analog |
| Atas U1 | rule area `antena_devkit` | tanpa tembaga dan via di bawah antena WROOM |
| Bawah | rule area `holder_18650` 80 × 24 mm (x 66–146, y 116,5–140,5) + garis silkscreen | tempat holder 18650 berkabel yang ditempel; baterai 65 × 18 mm, holder ±77 × 21 mm, margin 1,5 mm tiap sisi; footprint dilarang, jalur dan GND pour boleh |

Jalur yang dirute manual dan dikunci (`locked`): tiga jalur EKG (F.Cu
0,3 mm), catu AD8232 (3V3 dari pad 2 U1 lewat B.Cu ke C4/J3 pin 2, SDN ke
3V3), dan seluruh jalur daya (0,8 mm). Gate Q1 lewat B.Cu karena urutan pin
SOT-23 (G, D, S searah jarum jam) berlawanan dengan arah net di sekitarnya,
dan gate tidak membawa arus. Sisa sinyal digital dirute Freerouting 2.3.0.
GND dituang di kedua lapis.

Netclass (`mainboard.kicad_pro`): `Power` 0,8 mm/clearance 0,25 mm untuk
`/+5V /VBOOST /VSYS /VSW /VCHG /VBAT_OUT /VBAT_SENSE /BAT+ /BAT-`; `ECG` 0,3 mm
untuk `/ECG_*`; `Default` 0,25 mm, via 0,8/0,4 mm.

## Perbedaan terhadap skematik rev2

Skematik rev2 (`mainboard.kicad_sch`, KiCad 10.0.6, PCB belum di-layout)
dipakai sebagai acuan rangkaian. Perbedaannya:

| Bagian | Rev2 | Mainboard ini | Alasan |
|---|---|---|---|
| Net 3V3 | label `3.3V` (ESP, AD8232, buzzer) dan simbol `+3.3V` (TFT) | satu net `+3V3` | nama berbeda di KiCad = dua net terpisah; VCC TFT tidak tersambung ke 3V3 ESP |
| Pull-up tombol | R11–R13 1 kΩ ke +5V | dihapus, `INPUT_PULLUP` | GPIO ESP32-S3 maksimum 3,6 V |
| BLK TFT | tidak tersambung | ke 3V3 | backlight selalu menyala |
| Katoda D1 | ke +5V | ke VSYS | baterai tidak terkuras saat dicas |
| Saklar daya | tidak ada | J10 di VSYS | |
| Simbol U1 | ESP32-S3-DEVKITC-1-N8R8 | ESP32-S3-DevKitC-1-N16R8 | papan yang dipakai N16R8 |
| GND DevKit | hanya pin GND kanan atas | keempat pin GND | |
| Header boost | 2 pin (Input, Output) | 4 pin dengan GND | GND modul boost punya jalur sendiri |
| Footprint header J1–J9 | belum diisi | PinSocket/PinHeader 2,54 mm, JST PH untuk baterai | |
| Nama net | `SCL`, `OUT`, `buzz`, dll. | berprefiks (`I2C_`, `TFT_`, `ECG_`) | nama sama otomatis menyatu di KiCad |

Ukuran footprint pasif mengikuti rev2: R dan C 0805 HandSolder, tombol
`SW_PUSH_6mm_H7.3mm`. C1 memakai `CP_Radial_D5.0mm_P2.00mm` (pad sama dengan
rev2) agar tanda polaritas tercetak.

## Footprint ESP32-S3-DevKitC-1

Diambil dari library resmi Espressif (`espressif/kicad-libraries`,
`ESP32-S3-DevKitC.kicad_mod` dan simbol `ESP32-S3-DevKitC`). Posisi pad tidak
diubah: 2 × 22 pin, pitch 2,54 mm, jarak antar-baris 22,86 mm. Yang diubah
hanya lubang, dari 0,8 mm menjadi 1,0 mm dengan pad 1,7 mm. Pin header persegi
0,64 mm berdiagonal 0,9 mm, sehingga tidak masuk lubang 0,8 mm. Ukuran 1,0 mm
sama dengan footprint `PinSocket` KiCad. Simbol diturunkan dari format KiCad 10
ke format KiCad 9 tanpa mengubah pin.

## Pemeriksaan

```bash
python3 hardware/mainboard/cek_board.py
```

Hasil yang diharapkan:

```
netlist: 87/87 pin sesuai peta
+5V di luar jalur daya: tidak ada
ERC: error 0 warning 0
DRC error: 0, unconnected: 0, paritas skematik: 0
LULUS
```

Skrip keluar dengan kode 1 bila satu pin saja menyimpang dari peta di atas.
Peta pin di skrip (`PIN_U1`, `PIN_LAIN`) wajib diperbarui bersamaan dengan
`perangkat.h` setiap kali pin dipindah.

## Mengubah desain

1. Buka `mainboard.kicad_pro` di KiCad 9 atau lebih baru.
2. Ubah skematik, lalu **Tools → Update PCB from Schematic** (F8).
3. Jalur yang dikunci tidak ikut dipindah autorouter. Buka kuncinya
   (pilih jalur, `L`) sebelum mengubah bagian analog atau daya.
4. Tuang ulang zona (`B`), lalu jalankan `cek_board.py`.

## Yang belum terverifikasi

1. **Jarak antar-baris header DevKit fisik.** Footprint memakai 22,86 mm
   (resmi Espressif). Ukur papan N16R8 yang dipakai, karena klon bisa berbeda.
2. **Urutan pin tiap modul** (J2, J3, U2, J9) terhadap silkscreen modul yang
   dipegang. Urutan pin TFT 1,47" berbeda antar-vendor.
3. **Ruang mekanik modul.** Ukuran dari penjual saling berbeda (AD8232 35×22
   sampai 36×33 mm, TFT 19,5×44,5 atau 22×38,5 mm, INA219 22×20 mm), dan
   outline badan modul belum digambar di PCB. Bila dibaringkan ke arah dalam
   papan, badan TFT menutupi C6 dan badan AD8232 menutupi H2. Komponen SMD di
   bawahnya aman selama modul terangkat di atas female header. Kepala baut H2
   perlu dicek terhadap sisi bawah modul AD8232.
4. **Jalur catu dengan D1 di VSYS** belum diuji di breadboard. Ukur VSYS dan
   +5V dengan charger tercolok dan tercabut, dan pastikan arus baterai ≈ 0
   saat dicas.
5. **Konektor baterai** memakai JST PH 2 mm. Sesuaikan dengan kabel holder
   18650 yang dipakai, dan ukur holdernya: area di papan 80 × 24 mm.
6. **Tegangan lampu saklar J10.** Lampu dicatu VSYS ±3,0–4,6 V. Lampu LED
   12 V atau neon 220 V tidak akan menyala di tegangan ini; cek tulisan di
   badan saklar sebelum memakai pin lampu.

## Ekspor fabrikasi

Dijalankan setelah semua butir di atas dicek:

```bash
cd hardware/mainboard
kicad-cli pcb export gerbers -o fab/ mainboard.kicad_pcb
kicad-cli pcb export drill -o fab/ mainboard.kicad_pcb
```
