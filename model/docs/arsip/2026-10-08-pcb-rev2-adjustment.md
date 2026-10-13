# Penyesuaian skematik PCB rev1 → rev2

Sumber: `~/Downloads/schematic_rev_1.pdf` (KiCad `mainboard.kicad_sch`).
Lingkup dokumen ini: **TFT, buzzer, tombol, AD8232**, ditambah pin map rev2.
Rangkaian baterai/power path **sengaja ditunda**. Catatannya cuma satu baris
per item di §6 supaya tidak hilang.

Prinsip yang menyatukan semua perubahan di bawah:

> **ESP32-S3 itu perangkat 3,3 V. GPIO tidak tahan 5 V** (batas VDD + 0,3 = 3,6 V).
> +5V hanya boleh dipakai untuk **beban daya** (VIN board).
> Semua yang menyentuh GPIO ambil dari **3V3**, termasuk modul yang punya
> transistor sendiri (modul buzzer, §2).

Rev1 melanggar prinsip ini di tiga tempat: pull-up tombol, VCC INA219, dan
divider TFT, yang dirancang untuk logika 5 V padahal sumbernya 3,3 V.

Uji breadboard untuk rangkaian rev2 ini ada di `firmware/src/hwtest.cpp`
(`pio run -e hwtest -t upload`).

---

## 1. TFT ST7789 1,47" 172×320

### Rev1 (salah)

Keempat jalur (SCL, SDA, RES, DC) diberi divider 2k2/3k3:

```
 GPIO9 ───[R2 2k2]───┬─────────── J2.3 SCL
                     │
                  [R3 3k3]
                     │
                    GND

 Tegangan di pin TFT = 3,3 V × 3k3 / (2k2 + 3k3) = 1,98 V
 Datasheet ST7789:  VIH ≥ 0,7 × VDDI = 0,7 × 3,3 = 2,31 V      → HIGH tak terbaca ✗
```

Divider seperti ini hanya masuk akal kalau sumbernya **5 V**
(5 × 3k3/5k5 = 3,0 V). ESP32-S3 sudah 3,3 V, jadi level TFT dan ESP sama
dan tidak perlu konversi apa pun. Ini sudah terbukti di breadboard: TFT
langsung jalan tanpa resistor.

Masalah kedua: **J2 cuma 7 pin**, padahal modulnya **8 pin** (ada CS).
Kalau dicetak dengan header 7 pin, pin header bergeser satu posisi dari pin
modul dan semua sinyal masuk ke pin yang salah.

### Rev2

```
 ESP32-S3                         J2 (1×8, ikuti urutan silkscreen modul)
 ─────────                        ──────────────────────────────────────
 GND     ───────────────────────── 1 GND
 3V3     ───────────────────────── 2 VCC
 GPIO9   ───────────────────────── 3 SCL   (= SPI SCK, BUKAN I2C)
 GPIO8   ───────────────────────── 4 SDA   (= SPI MOSI, BUKAN I2C)
 GPIO10  ───────────────────────── 5 RES
 GPIO11  ───────────────────────── 6 DC
 GND     ───────────────────────── 7 CS    (diikat GND → firmware wajib SPI_MODE3)
 3V3     ───────────────────────── 8 BLK   (GPIO13 sekarang milik buzzer, §2)
```

| Aksi | Komponen |
|---|---|
| Hapus | R3, R4, R6, R8 (3k3 ke GND) |
| Ganti jadi jumper / 0 Ω | R2, R5, R7, R9. Boleh **33 Ω** untuk meredam ringing SCK; taruh dekat ESP |
| Ubah | J2: 1×7 → **1×8**, tambah CS |
| Opsional | BLK ke GPIO **12** (PWM, bebas sejak buzzer pindah ke 13) supaya backlight bisa diredupkan/dimatikan. Backlight 3 LED kemungkinan beban terbesar setelah WiFi, dan konsumsi daya diukur di bab3 |

> ⚠️ Urutan pin modul 1,47" **berbeda antar-vendor**. Cocokkan J2 dengan
> silkscreen modul yang dipegang, jangan dengan gambar di internet.

---

## 2. Buzzer: modul pasif 3 pin di GPIO 13

Diperbarui 11 Okt 2026. Rencana sebelumnya (SFM-27 aktif + Q2 2N2222 + R14
di GPIO 12) **dibatalkan**, alasannya di "Riwayat" di akhir bagian ini.

### Part yang dipakai: modul buzzer pasif A18009

Data dari listing toko (tidak ada datasheet):

| Parameter | Nilai | Catatan |
|---|---|---|
| Bentuk | Modul PCB 3,3 × 1,3 cm, **3 pin**: VCC, GND, I/O | Transistor penggerak sudah ada di modul |
| Tegangan kerja | 3,3–5 V | **Dipakai 3V3**, lihat di bawah |
| Penggerak | Gelombang kotak **2–5 kHz** | Tanpa osilator. DC cuma memberi "klik" sekali |
| Logika I/O | **Aktif LOW**: I/O LOW = arus mengalir ke buzzer | Listing: "kalau cuma GND cuma nyala sebentar lalu mati". Seri aktifnya (A07009): "I/O Low level → buzzer voice" |

Aktif LOW berarti transistor di modul hampir pasti **PNP** (biasanya S8550):
emitor di VCC, basis ditarik ke I/O lewat resistor. Ini simpulan dari
perilaku, belum dicek fisik. Cara memastikan: baca tulisan di badan
transistor modul (S8550 / 9012 = PNP).

### Rangkaian

```
 ESP32-S3                  Modul buzzer pasif (A18009)
 ────────                  ───────────────────────────
 3V3     ───────────────── VCC      ← BUKAN +5V
 GND     ───────────────── GND
 GPIO13  ───────────────── I/O      diam = HIGH, bunyi = gelombang kotak

 Di dalam modul (terduga):
                VCC
                 │
                 E
 I/O ──[R ~1k]── B   PNP (S8550)
                 C
                 │
                BZ  pasif
                 │
                GND
```

| Aksi | Komponen | Alasan |
|---|---|---|
| **Hapus** | BZ1 SFM-27, Q2 2N2222, R10 2k2, R14 10k | Transistor sudah ada di modul |
| **Ganti** | Footprint BZ1 → header **1×3** (VCC, GND, I/O) untuk modul | Urutan pin ikuti silkscreen modul yang dipegang |
| **Ubah** | Net buzzer GPIO 12 → **GPIO 13**, VCC header ke **3V3** | Lihat "Kenapa 3V3" |
| Ubah | TFT BLK: GPIO 13 → 3V3 (atau GPIO 12 kalau mau PWM) | GPIO 13 tidak boleh dipakai dua perangkat |

### Kenapa VCC harus 3V3, bukan 5V

PNP baru mati kalau tegangan basis hampir sama dengan emitornya, yaitu VCC.
GPIO ESP32-S3 paling tinggi 3,3 V:

| VCC modul | I/O HIGH (3,3 V) | Akibat |
|---|---|---|
| 5 V | V_EB = 1,7 V → **PNP tetap menyala** | Buzzer tidak pernah benar-benar diam. Arus dari 5 V mengalir lewat sambungan E–B masuk ke pin GPIO, melanggar prinsip di atas |
| **3V3** | V_EB = 0 → PNP mati | Diam saat HIGH, bunyi saat gelombang kotak |

Ongkosnya, suara sedikit lebih pelan dibanding 5 V. Kerasnya dikembalikan
dengan menyetel nada ke frekuensi resonansi buzzer (lihat Firmware).

### Firmware (`hwtest.cpp`)

- **Diam = HIGH.** Firmware lama menahan pin LOW di antara bip. Untuk modul
  aktif-LOW, itu sama dengan menyuruhnya bunyi terus.
- Pin di-set HIGH di **baris pertama** `setup()` (`pasang_buzzer()`).
- Gelombang kotak dari LEDC dengan `output_invert = 1`, sehingga duty 0 berarti
  HIGH (diam) dan bip tetap gelombang kotak 50%. Bawaan 2000 Hz. Cari nada
  paling keras dengan `[` / `]` di serial (±250 Hz), lalu kunci angkanya di `nada_hz`.
- `BUZZER_PASIF 0` kalau ternyata modul yang terpasang yang aktif (A07009):
  cukup LOW = bunyi, HIGH = diam, tanpa PWM. Dua modul ini dijual di satu
  halaman toko, jadi bisa saja tertukar. Cirinya: modul aktif bagian bawah
  buzzer-nya tertutup rapat, sedangkan modul pasif memperlihatkan PCB hijau.
- Saat boot, sebelum `setup()`, pin GPIO 13 mengambang. Pada modul pasif ini
  aman: paling buruk cuma "klik" sekali, karena DC tidak menghasilkan nada.

### Diagnosa di breadboard: tombol B2

B2 menjalankan 4 fase × 3 detik, dengan nama fase tampil di TFT:

| Fase | Isi GPIO 13 | Modul pasif + VCC 3V3 yang benar |
|---|---|---|
| 1 HIGH | 3,3 V tetap | diam |
| 2 LOW | 0 V tetap | "klik", lalu diam |
| 3 PWM 2 kHz | gelombang kotak | bunyi terus |
| 4 LEPAS | pin dilepas (input) | diam atau "klik" |

- Bunyi di fase 1 → VCC masih 5 V, atau I/O tidak benar-benar ke GPIO 13.
- Bunyi terus di semua fase → buzzer tidak dikendalikan GPIO 13. Cek kabel I/O,
  dan pastikan BLK TFT tidak ikut tersambung ke GPIO 13.
- Fase 2 bunyi panjang → modul yang terpasang ternyata yang aktif.

### Riwayat: kenapa SFM-27 + Q2 dibatalkan

Rencana 8 Okt 2026: buzzer piezo aktif SFM-27 (3–24 V, ≥95 dB @12 V, 2,3–3,9
kHz tetap, varian continuous/intermittent) di +5V, digerakkan Q2 2N2222 dari
GPIO 12 lewat R10 2k2, ditambah R14 10k basis→GND supaya tidak bunyi liar saat
boot. Hitungannya benar (I_B ≈ 1,1 mA, β_paksa ≈ 18 → jenuh). Diganti karena:

1. Buzzer **aktif** cuma bisa satu nada dan bunyi liar kalau basis mengambang.
   Varian intermittent bahkan membuat pola "tit-tit" sendiri yang menabrak
   bip per beat.
2. Bip per beat butuh nada yang bisa diatur → buzzer **pasif**.
3. Modul 3 pin sudah membawa transistornya sendiri, jadi Q2, R10, dan R14
   tidak diperlukan lagi.

Pelajaran yang muncul saat uji: **modul buzzer 3 pin murah biasanya aktif
LOW**, kebalikan dari rangkaian NPN rev1 (HIGH = bunyi). Firmware yang menganggap
HIGH = bunyi akan membuat buzzer berbunyi terus tepat di saat ia mengira
buzzer sedang diam.

---

## 3. Tombol

### Rev1 (salah)

```
 +5V ──[R11 10k]──┬──── GPIO4        ← 5 V masuk GPIO setiap tombol dilepas ✗
                  │
                 SW1
                  │
                 GND
 (SW2/R12 → GPIO5 dan SW3/R13 → GPIO6 sama persis)
```

### Rev2: pilihan A (disarankan), tanpa resistor

```
 GPIO4 ────┬──── SW1 ──── GND
           │
     pull-up internal ~45 kΩ ke 3V3 (INPUT_PULLUP di firmware)
```

Dikali tiga untuk GPIO 4 / 5 / 6. **Hapus R11, R12, R13.**

Kenapa cukup:
- Firmware sudah memakai `INPUT_PULLUP` dan debounce 50 ms (`main.cpp`,
  `hwtest.cpp`), jadi resistor dan kapasitor eksternal tidak menambah apa-apa.
- Jalur tombol di PCB pendek, jadi pull-up lemah 45k tidak gampang kemasukan noise.

### Rev2: pilihan B, kalau tetap ingin pull-up eksternal

```
 3V3 ──[10k]──┬──── GPIO4
              │
             SW1
              │
             GND
```

Ujung atas resistor pindah dari **+5V ke 3V3**. Tidak ada perubahan lain.

### Penempatan

| Tombol | GPIO | Fungsi di firmware utama | Catatan |
|---|---|---|---|
| SW1 / button_1 | 4 | baru (belum ada) | 8 Okt 2026 sempat tidak terbaca dan direncanakan pindah ke GPIO14; 9 Okt 2026 normal kembali di GPIO4, jadi tetap pakai 4 |
| SW2 / button_2 | 5 | DUMP | |
| SW3 / button_3 | 6 | REC | |

---

## 4. AD8232

Rev1 memindahkan EKG dari GPIO 8 (breadboard) ke **GPIO 1**. Ini sudah
benar, karena GPIO 8 jadi bebas untuk TFT dan GPIO 1 tetap di ADC1 yang tidak
mati saat WiFi menyala. Ada dua hal di simbolnya yang masih perlu dibetulkan.

```
 J3 AD8232                    ESP32-S3
 ─────────                    ────────
 1 GND   ──── simbol power GND        ← rev1 pakai LABEL "GND": cek, bisa tidak tersambung
 2 3.3V  ──── +3V3
 3 OUT   ──── GPIO1  (ADC1_CH0)
 4 LO−   ──── GPIO2
 5 LO+   ──── GPIO42
 6 SDN   ──── +3V3                    ← rev1 mengambang (label hanya muncul sekali)
```

- **GND:** di KiCad, label lokal `GND` tidak dijamin menyatu dengan simbol
  power `GND`. Ganti dengan simbol power, lalu pastikan di Net Inspector
  bahwa J3-1 ada di net `GND`.
- **SDN:** datasheet AD8232 menyebut *"when not using this feature,
  permanently tie SDN to +VS"*. SDN LOW mematikan chip, dan pin yang
  mengambang hasilnya tidak tentu.
- **Layout:** jauhkan trace GPIO1 dari GPIO8/GPIO9 (SPI TFT, puluhan MHz),
  dan beri ground pour di antaranya. SPI yang berisik di dekat jalur
  analog EKG langsung terlihat sebagai noise di sinyal.

---

## 5. Pin map rev2

| Fungsi | GPIO | Nama net yang disarankan |
|---|---|---|
| EKG OUT | 1 | `ECG_OUT` |
| EKG LO− / LO+ | 2 / 42 | `ECG_LON` / `ECG_LOP` |
| TFT SCK / MOSI | 9 / 8 | `TFT_SCK` / `TFT_MOSI` |
| TFT RES / DC | 10 / 11 | `TFT_RST` / `TFT_DC` |
| TFT BLK | 3V3 (atau 12 kalau PWM) | `TFT_BLK` |
| Buzzer (modul pasif, aktif LOW) | 13 | `BUZZ` |
| Tombol 1 / 2 / 3 | 4 / 5 / 6 | `BTN1` / `BTN2` / `BTN3` |
| INA219 SDA / SCL | 17 / 18 | `I2C_SDA` / `I2C_SCL` |
| NeoPixel | 48 | onboard |

**Nama net berprefiks itu penting.** Di KiCad, label yang namanya sama
otomatis jadi satu kabel. Rev1 memberi nama `SCL`/`SDA` ke TFT (yang
sebenarnya SPI) dan ke INA219 (I2C), sehingga kedua bus tersambung jadi
satu. Dengan prefiks `TFT_` dan `I2C_`, tabrakan seperti ini tidak bisa
terjadi tanpa sengaja.

Hindari: GPIO 26–37 (flash + PSRAM octal N16R8), 0/3/45/46 (strapping),
19/20 (USB).

---

## 6. Ditunda: rangkaian baterai (jangan lupa)

- Mini360 = buck, Vin ≥ 4,75 V. Tidak bisa dipakai dari Li-ion 3,0–4,2 V → ganti dengan boost ke 5 V.
- Katoda SS34 harus ke node input konverter (pin 2 Q1), bukan ke +5V. Kalau tidak, baterai tetap terkuras saat dicas.
- INA219: VCC ke **3V3** (pull-up I2C modul ikut VCC), I2C ke GPIO 17/18, nama net `I2C_*`.
- INA219 di sisi baterai: arus puncak ~550 mA > ±400 mA → firmware PGA ÷4 (`0x17FF`).
- Belum ada saklar power.
- Rprog TP4056 (default 1 A) harus disesuaikan dengan kapasitas baterai.

---

## 7. Checklist sebelum kirim ke pabrik

- [ ] J2 diganti 1×8, urutan pin sesuai silkscreen modul
- [ ] R2–R9: 4 dihapus, 4 jadi jumper/0 Ω/33 Ω
- [ ] R11–R13 dihapus (atau ujungnya dipindah ke 3V3)
- [ ] BZ1/Q2/R10/R14 dihapus, diganti header 1×3 modul buzzer pasif (VCC ke **3V3**, I/O ke GPIO 13)
- [ ] TFT BLK tidak lagi di GPIO 13 (ke 3V3, atau GPIO 12)
- [ ] Diagnosa B2 di `hwtest`: hanya fase 3 yang berbunyi
- [ ] J3-1 pakai simbol power GND, J3-6 SDN ke 3V3
- [ ] Semua net diberi nama berprefiks (§5), tidak ada `SCL`/`SDA` polos
- [ ] Semua pin GND ESP tersambung (rev1 cuma J3_1)
- [ ] Label part U1: N8R8 → **N16R8** (pinout sama, cuma BOM)
- [ ] **ERC bersih**: label yang muncul cuma sekali = sinyal mengambang
- [ ] Rangkaian sudah diuji di breadboard dengan `pio run -e hwtest`
