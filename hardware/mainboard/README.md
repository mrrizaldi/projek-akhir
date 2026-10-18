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
| `cek_board.py` | pemeriksaan netlist, ERC, DRC, dan paritas skematik–PCB; memanggil `cek_tata_letak.py` |
| `cek_tata_letak.py` | pemeriksaan pcbnew (`/usr/bin/python3`): lebar jalur per netclass, jarak courtyard ≥ 1 mm, teks depan dan belakang |
| `tata_letak.py` | alat layout (`/usr/bin/python3`): posisi terkunci, rute manual, pembersihan sesudah autoroute, pad GND solid, tuang zona, penempat teks, ukiran |

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
| Kiri | TFT, buzzer; tombol SW1–SW3 berjajar tegak di tepi kiri (x 53–57,5, y 57,5–88) | SPI TFT berlawanan sisi dengan jalur analog; tombol mudah dijangkau dari sisi papan |
| Atas U1 | rule area `antena_devkit` | tanpa tembaga dan via di bawah antena WROOM |
| Bawah | rule area `holder_18650` 80 × 24 mm (x 66–146, y 116,5–140,5) + garis silkscreen | tempat holder 18650 berkabel yang ditempel; baterai 65 × 18 mm, holder ±77 × 21 mm, margin 1,5 mm tiap sisi; footprint dilarang, jalur dan GND pour boleh |

Jalur yang dirute manual dan dikunci (`locked`): tiga jalur EKG (F.Cu),
catu AD8232 (3V3 dari pad 2 U1 lewat B.Cu ke C4/J3 pin 2, SDN ke 3V3),
I2C ke INA219 (SDA di F.Cu; SCL turun lewat via ke B.Cu di x 118 dan
menyeberang di bawah SDA, karena urutan pin INA219 SCL–SDA terbalik terhadap
urutan dari DevKit), 3V3 ke INA219, 3V3 sisi kiri (U1 pad 2 ke C3), dan
seluruh jalur daya (termasuk cabang gate Q1 dan R2). Gate Q1 lewat B.Cu
karena urutan pin SOT-23 (G, D, S searah jarum jam) berlawanan dengan arah
net di sekitarnya, dan gate tidak membawa arus. Sisa sinyal digital dirute
Freerouting 2.3.0. GND dituang di kedua lapis.

Batas JLCPCB untuk 2 lapis 1 oz (halaman *PCB Capabilities*): jalur/clearance
0,10 mm, jalur ke lubang PTH 0,28 mm (rekomendasi 0,35 mm), via lubang 0,15 /
pad 0,25 mm (lubang < 0,3 mm lebih mahal), ring PTH 0,18 mm (rekomendasi
0,25 mm), teks silkscreen tinggi 1,0 mm dan garis 0,15 mm, tembaga ke tepi
0,2 mm. Profil papan ini adalah profil "ideal teknis": lebar mengikuti
kebutuhan arus menurut IPC-2221 (1 oz, kenaikan suhu 10 °C: 0,3 mm ±1 A,
1,0 mm ±2,4 A), jarak dan ring mengikuti rekomendasi JLCPCB.

| Netclass (`mainboard.kicad_pro`) | Net | Lebar | Clearance | Via |
|---|---|---|---|---|
| `Default` | sinyal digital, `+3V3`, GND | 0,3 mm | 0,35 mm | 0,9/0,4 mm |
| `ECG` | `/ECG_*` | 0,4 mm | 0,35 mm | 0,9/0,4 mm |
| `Power` | `/+5V /VBOOST /VSYS /VSW /VCHG /VBAT_OUT /VBAT_SENSE /BAT+ /BAT-` | 1,0 mm | 0,35 mm | 1,2/0,6 mm |

Arus terbesar di papan: jalur baterai/boost ±1 A puncak (MT3608 dibatasi
2 A), sehingga 1,0 mm memberi margin di atas batas boost. Sinyal hanya
membawa miliampere; 0,3 mm dipilih karena tiga kali minimum JLCPCB dan muat di
sela pin DevKit tanpa menyempit (0,3 + 2 × 0,35 = 1,0 mm ≤ celah 1,04 mm).

Jarak antar-courtyard komponen minimal 1,0 mm. Semua pad GND memakai thermal
relief kecuali C2-2, yang disambung penuh (*solid*) karena hanya mendapat satu
spoke di sela antara U1 dan jalur +5V.

Teks: referensi di silkscreen (tinggi ≥ 1,0 mm, batas JLCPCB) dan value di
Fab, sejajar sumbu header dan di sisi yang berlawanan, tanpa menumpuk dan
tidak di atas pad. Pengecualian: ref C4 mendatar di atas C4, karena celah
9 mm antara U1 dan J3 tidak muat teks tegak.

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
hanya lubang dan pad: lubang 0,8 mm menjadi 1,0 mm, pad oval 2,0 mm (mendatar)
× 1,5 mm (tegak), ring 0,25 mm sesuai rekomendasi JLCPCB. Pin header persegi
0,64 mm berdiagonal 0,9 mm, sehingga tidak masuk lubang 0,8 mm; 1,0 mm sama
dengan footprint `PinSocket` KiCad. Pad 1,5 mm tegak menyisakan celah 1,04 mm
antar-pin satu kolom, cukup untuk jalur 0,3 mm + clearance 2 × 0,35 mm. Jalur
3V3 ke AD8232 dan I2C ke INA219 menyeberangi kolom pin lewat celah ini. Simbol diturunkan dari format KiCad 10
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
lebar jalur: 0 temuan
jarak courtyard: 0 temuan
teks: 0 temuan
LULUS
```

Skrip keluar dengan kode 1 bila satu pin saja menyimpang dari peta di atas,
bila ada jalur lebih tipis dari netclass-nya, dua courtyard berjarak < 1 mm,
atau teks menumpuk, di atas pad, keluar tepi, atau tidak searah header.
Peta pin di skrip (`PIN_U1`, `PIN_LAIN`) wajib diperbarui bersamaan dengan
`perangkat.h` setiap kali pin dipindah.

## Ukiran nama

Silkscreen sisi belakang, dicerminkan agar terbaca dari bawah, di balik area
holder (yang bebas footprint sehingga sisi belakangnya tanpa pad):

| Baris | Teks | Tinggi | Posisi |
|---|---|---|---|
| 1 | Muhammad Rafi Rizaldi | 2,5 mm | (106; 125) |
| 2 | 3123600001 | 2,0 mm | (106; 131) |

Teksnya diatur di `UKIRAN` dan `POSISI_UKIRAN` (`tata_letak.py`).

## Mengubah desain

Perubahan rangkaian:

1. Buka `mainboard.kicad_pro` di KiCad 9 atau lebih baru.
2. Ubah skematik. Penerapan ke board lewat skrip pcbnew (lihat skill
   `kicad-pcb-pa` aturan 5), bukan F8, agar nama net tetap `/NAMA`.

Rute ulang seluruh papan (posisi di `POSISI`, rute manual di fungsi `rute_*`
pada `tata_letak.py`), dijalankan dari `hardware/mainboard/`:

```bash
/usr/bin/python3 tata_letak.py hapus
/usr/bin/python3 tata_letak.py rute
/usr/bin/python3 tata_letak.py tuang
```

Lalu autoroute sisa sinyal dengan Freerouting (server MCP kicad: `open_project`,
`autoroute` dengan `maxPasses` 60), kemudian:

```bash
/usr/bin/python3 tata_letak.py bersih
/usr/bin/python3 tata_letak.py solid
/usr/bin/python3 tata_letak.py teks
/usr/bin/python3 tata_letak.py ukiran
/usr/bin/python3 tata_letak.py tuang
python3 cek_board.py
```

Hasil yang diharapkan: baris terakhir `cek_board.py` adalah `LULUS`.
Freerouting bisa melapor sukses sambil meninggalkan sambungan; bila DRC
melapor `unconnected`, sambungan itu ditambahkan ke fungsi `rute_*` di
`tata_letak.py` lalu seluruh urutan diulang dari `hapus`.

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
