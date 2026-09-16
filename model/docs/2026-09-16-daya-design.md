# Desain Pengukuran Konsumsi Daya & Penentuan Baterai — HW-7

Tanggal: 2026-09-16
Status: disetujui (hasil brainstorming), belum diimplementasikan
Acuan: `laporan/proposal-pa/bab/bab3.tex` baris 533, 590–593 (rencana pengukuran
perangkat keras); `bab2.tex` baris 327, 342 (gap penelitian terdahulu)

Dokumen ini tidak mengubah metodologi Bab 3. Bab 3 sudah mengunci instrumen
(INA219 atau USB power meter) dan metriknya (arus & daya rata-rata, mA/mW, saat
inferensi kontinu). Yang dirancang di sini adalah **cara mengukurnya** supaya
angkanya bisa dipertanggungjawabkan, dan cara menurunkannya jadi kapasitas
baterai.

---

## 0. Kenapa ini dikerjakan sekarang

Dua alasan, keduanya soal urutan yang tidak bisa dibalik.

**Pertama, HW-5 tidak memblokir ini.** Yang dibebani saat pengukuran adalah
komputasi (ISR 360 Hz, deteksi tiap 1 detik, inferensi per detak), bukan
elektroda. Beban itu dibangkitkan dari replay, dan replay justru lebih baik
daripada tubuh nyata karena bebannya identik tiap ulangan.

**Kedua, WiFi belum ada — dan itu keuntungan.** Mengukur sekarang memberi
baseline "edge murni". Mengukur lagi setelah HW-6 memberi angka kedua.
Selisihnya adalah ongkos pipeline edge-to-cloud, satu angka yang persis
menjawab gap yang ditulis sendiri di Bab 2 (TinyCES dan 1D-TA-DSC sama-sama
"tidak menyertakan evaluasi konsumsi daya pada kondisi operasi kontinu").
Kalau MQTT masuk lebih dulu, baseline itu hilang dan tidak bisa direkonstruksi.

Konsekuensi administratif: label **"HW-6 opsional, di luar PoC"** di
`model/CLAUDE.md` bertentangan dengan Bab 2 yang memakai resiliensi
edge-to-cloud sebagai klaim orisinalitas. Label itu dicabut sebagai bagian
dari pekerjaan ini.

---

## 1. Tangga mode beban

Konsumsi per fase dipisahkan lewat **isolasi mode**, bukan lewat sinkronisasi
timestamp. Tiap mode dijalankan sampai steady-state, rata-ratanya diukur, dan
ongkos tiap tahap = selisih antar-mode. Tanpa sinkronisasi waktu, tiap angka
bisa dicek ulang multimeter, dan tiap angka adalah rata-rata steady-state —
bukan cuplikan yang berisik.

Mode dipilih lewat **perintah serial**, bukan build flag. Flash ulang antar-mode
mengubah kondisi termal board dan menambah variabel yang tidak dikendalikan.

| Perintah | Yang jalan | Mengukur |
|---|---|---|
| `p0` | board hidup, timer ISR dimatikan | dasar: ESP32 idle + AD8232 + regulator |
| `p1` | + ISR 360 Hz + kuras antrean | ongkos akuisisi murni |
| `p2` | + `ecg_live_push()` | ongkos DSP (bandpass + deteksi + segmentasi) |
| `p3` | + inferensi TFLM per detak | = firmware produksi, ongkos TinyML |
| `p4` | `p3` + LED kualitas menyala | ongkos LED, diukur terpisah |

**Tangga ini mengikuti batas modul, bukan batas konseptual.** `ecg_live_push()`
mengerjakan bandpass + deteksi + segmentasi di balik satu pintu
(`firmware/include/ecg_live.h`). Memisahkan bandpass dari deteksi berarti
membongkar `ecg_live.cpp` — kode yang sudah terverifikasi 11/11 native dan 5/5
device di HW-3. Tidak sepadan. `p2` diterima sebagai satu blok DSP.

**LED padam di `p0`–`p3`.** `PIN_LED 48` adalah NeoPixel; WS2812 menarik puluhan
mA saat terang, berpotensi melebihi ongkos inferensi CNN yang sedang diukur.
Kalau LED menyala selama pengukuran, angka yang keluar bercerita tentang LED,
bukan tentang TinyML. Ongkosnya diukur sendiri di `p4`.

### 1.1 Sumber sinyal: replay wajib

Tanpa sinyal, `ecg_live_push()` tidak pernah mengeluarkan beat, jadi inferensi
tidak pernah jalan dan `p3` akan mengukur nol inferensi. Elektroda lepas di sini
bukan merepotkan — membuat pengukuran tidak ada artinya.

Sampel disuapkan dari `golden_raw` yang di-loop dari flash, menggantikan
`adc1_get_raw()` di ISR. Akibatnya beban deterministik: jumlah detak per menit
sama persis tiap ulangan, jadi dua pengukuran bisa dibandingkan. Ini keunggulan
replay, bukan kompromi.

---

## 2. Pembacaan INA219

### 2.1 Tanpa dependency baru

`Adafruit_INA219` tidak dipakai. `Wire` sudah ada di framework Arduino, dan
menambah dependency adalah gate point di `CLAUDE.md`.

Register kalibrasi on-chip **dilewati seluruhnya**. Alih-alih menghitung
`Current_LSB` dan menulis nilai ajaib supaya chip yang mengalikan, register
shunt voltage dibaca langsung dan pembagian dilakukan di software:

```
I [mA] = Vshunt_reg × 0,01 mV/LSB / R_SHUNT [ohm]
V [V]  = (Vbus_reg >> 3) × 4 mV
```

Dua akibat, dua-duanya menguntungkan: tidak ada angka ajaib yang tidak bisa
dipertanggungjawabkan, dan **`R_SHUNT` jadi knob kalibrasi eksplisit**. Shunt
0,1 ohm pada breakout murah toleransinya sering ±1%; begitu multimeter bilang
lain, yang dikoreksi satu konstanta.

### 2.2 Konfigurasi

- Rentang bus **16 V** (VBUS 5 V, tidak perlu 32 V)
- PGA **÷1** (±40 mV ≈ ±400 mA pada 0,1 ohm) — cukup untuk beban ini, dan
  resolusinya paling halus
- Mode **averaging 128 sampel** (~68 ms per pembacaan). Averaging di chip itu
  wajib: arus perangkat ini berdenyut mengikuti burst 33 ms yang sudah terukur
  di HW-3, dan pembacaan sesaat akan melompat-lompat tanpa arti.

### 2.3 Siapa yang membaca

**DUT sendiri**, cetak 1 Hz. Tidak perlu MCU kedua.

INA219 disuplai dari sisi beban, jadi arus diamnya (~1 mA) ikut terhitung di
**semua** mode — lenyap sendiri di selisih antar-mode, dan untuk angka absolut
dinyatakan terus terang di walkthrough.

---

## 3. Pemasangan fisik

Tidak ada rangkaian baru. Yang diputus **hanya VBUS**; D+/D−/GND utuh, jadi
serial monitor tetap jalan dan mode `p0`–`p4` tetap bisa diperintah dari
keyboard.

```
Laptop  ─┬─ VBUS (merah) ──► [INA219 VIN+] (shunt) [VIN−] ──► 5V board
         ├─ D+  (hijau) ─────────────────────────────────► board   JANGAN diputus
         ├─ D−  (putih) ─────────────────────────────────► board   JANGAN diputus
         └─ GND (hitam) ─────────────────────────────────► board   JANGAN diputus

INA219 VCC ─ 3V3 board      INA219 SDA ─ GPIO 11
INA219 GND ─ GND board      INA219 SCL ─ GPIO 12
```

Modul yang dipakai varian **header 6 pin** (`VCC GND SCL SDA VIN+ VIN-`), tanpa
blok terminal sekrup. Dua kelompok pin yang berbeda fungsi ada dalam satu
deretan, jadi pemetaannya ditulis tegas:

| Pin | Ke mana | Kelompok |
|---|---|---|
| `VIN+` | kawat merah USB sisi **laptop** | jalur diukur (arus beban) |
| `VIN-` | kawat merah USB sisi **board** (ke pin 5V) | jalur diukur (arus beban) |
| `VCC` | **3V3** board | logika |
| `GND` | GND board | logika |
| `SDA` | GPIO 11 | logika |
| `SCL` | GPIO 12 | logika |

**`VCC` wajib 3V3, jangan 5V.** Pull-up I2C modul tersambung ke VCC-nya sendiri;
VCC 5V menarik SDA/SCL ke 5V dan memberi tegangan berlebih ke GPIO ESP32-S3 yang
cuma tahan 3,3V. Chip INA219 sendiri kuat sampai 5,5V — yang rusak ESP32-nya.

Urutan pasang: empat pin logika dulu dengan USB tercabut, pastikan board masih
menyala normal, baru potong kawat merah dan sisipkan VIN+/VIN−. Kalau VIN+ dan
VIN− tertukar tidak ada yang rusak, arus cuma terbaca **negatif** — penanda yang
jelas bahwa dua kawat tinggal ditukar.

**Konsekuensi varian 6-pin:** seluruh arus board lewat pin dupont, bukan terminal
sekrup. Sambungan tekan yang longgar = board reboot acak di tengah pengukuran
atau arus terbaca naik-turun tanpa sebab — pola kegagalan yang sama dengan yang
memacetkan HW-5. Header modul ini masuk daftar solder bersama AD8232, dan dua
kawat VBUS lebih aman disolder langsung ke pin daripada mengandalkan dupont.

**Cara memutus VBUS:** kabel USB korban — kupas selubung di tengah, potong
hanya kawat merah, sambungkan dua ujungnya ke `VIN+`/`VIN−`. Tiga kawat lain
dibiarkan utuh. Hasilnya jadi kabel ukur permanen. Alternatif USB breakout
pass-through lebih rapi tapi harus menunggu barang; ini alat ukur, kerapiannya
tidak dinilai.

**JANGAN**: menyuplai board dari pin 5V pakai powerbank sambil USB tetap colok.
Arus akan terbagi dua jalur dan angka yang keluar lebih kecil dari yang
sebenarnya, tanpa peringatan apa pun.

### 3.1 Pemilihan pin I2C

GPIO 11 & 12 adalah pin **ADC2**, dan ADC2 mati total begitu WiFi menyala
(`akuisisi-walkthrough.md` §1). Untuk proyek yang pasti menyalakan WiFi di
HW-6, kapasitas ADC di pin itu sudah pasti hangus — menghabiskannya untuk I2C
tidak mengorbankan apa pun, sementara memakai GPIO 1–10 akan memakan ADC1 yang
masih berharga. **GPIO 4 dilarang**: jalurnya terbukti putus (14 Sep 2026).

### 3.2 Kenapa high-side

Shunt dipasang di sisi positif, bukan di jalur GND. Shunt di GND akan mengangkat
referensi ground board terhadap ground laptop; begitu ground bergeser, jalur
data USB dan pembacaan ADC AD8232 ikut bergeser — merusak sinyal yang justru
sedang diukur konsumsinya. INA219 memang dibuat untuk high-side (common-mode
sampai 26 V).

---

## 4. Pencatat: `model/scripts/measure_power.py`

Mengikuti pola yang sudah ada — `pull_recording.py` dan `analyze_recording.py`
sama-sama bicara serial dari `model/scripts/`.

Tugas: kirim perintah mode, tunggu **60 detik per mode**, rekam tiap baris ke
CSV, lalu cetak tabel rata-rata ± std per mode dan simpan PNG ke
`artifacts/metrics/daya_<ts>.png` (senapas dengan `akuisisi_*.png`).

**Cek yang ditinggalkan** (aturan: logika non-trivial meninggalkan satu cek yang
bisa dijalankan): assert bahwa

```
Σ(selisih tiap tahap) == (p3 − p0)   dalam toleransi
```

Kalau tangga modenya tidak konsisten, skrip gagal — bukan diam-diam
menghasilkan tabel yang salah.

---

## 5. Validasi

Tiga lapis, semuanya mekanis:

1. **Konsistensi tangga** — jumlah selisih `p0→p1→p2→p3` harus sama dengan
   `p3 − p0` terukur (assert di skrip, §4).
2. **Cek silang multimeter** — INA219 dicabut dari terminal sekrup, multimeter
   (mode arus) dicolok di celah VBUS yang sama, dibandingkan di satu mode.
   Kalibrasi shunt bisa meleset tanpa tanda apa pun; ini satu-satunya
   pertahanan.
3. **`n_lewat` wajib 0 di tiap mode** — kalau sampel bolong, bebannya bukan
   beban sebenarnya dan angkanya tidak mewakili apa pun.

---

## 6. Dari mA ke mAh

Angka mA di 5 V **tidak boleh** langsung jadi mAh baterai. LiPo 3,7 V nominal;
yang kekal adalah daya, bukan arus.

```
P [mW]         = V_terukur × I_terukur            (di sisi 5 V)
I_baterai [mA] = P / (3,7 × eta)                  eta = efisiensi regulator
mAh            = I_baterai × jam_target / 0,8     0,8 = kapasitas terpakai LiPo
```

Melewatkan konversi ini membuat kapasitas meleset ~35% ke arah yang salah —
terlalu kecil. Satuan ditulis menempel di tiap langkah karena kesalahan jenis
ini tidak akan ditangkap test apa pun: ia jalan mulus, keluar angka, dan
angkanya salah.

**Dua hal dinyatakan sebagai belum diketahui, bukan ditebak:**

- **WiFi/MQTT belum ada.** Angka ini baseline edge murni dan akan naik setelah
  HW-6. Itu justru alasan urutannya daya-dulu (§0).
- **eta regulator dev board** tidak ada di datasheet mana pun. Dipakai asumsi
  **0,85**, ditulis sebagai asumsi di walkthrough, bukan sebagai fakta.

### 6.1 Terbuka: target jam operasi

`jam_target` belum diputuskan dan **tidak ada di Bab 3**. Sampai user
memutuskan, dipakai **12 jam** sebagai asumsi kerja, dan hasilnya disajikan
sebagai tabel mAh untuk beberapa target (8 / 12 / 24 jam) supaya keputusannya
bisa diambil dari angka, bukan sebelum angka.

---

## 7. Keluaran

- `firmware/src/main.cpp` — tangga mode `p0`–`p4`, pembaca INA219, sumber replay
- `model/scripts/measure_power.py` — pencatat + tabel + PNG + assert
- `model/artifacts/metrics/daya_<ts>.csv` & `.png`
- `model/docs/daya-walkthrough.md` — aturan 7 `model/CLAUDE.md`: fase selesai →
  walkthrough, jangan ditunda
- `model/CLAUDE.md` — baris status **HW-7**, dan cabut label "opsional, di luar
  PoC" di HW-6

## 8. Yang sengaja TIDAK dilakukan

- **Tidak memakai osiloskop / penanda GPIO.** Menangkap transien lebih akurat,
  tapi hasilnya sulit dijadikan tabel rata-rata dan alatnya belum tentu ada.
- **Tidak mencatat arus + timestamp lalu mencocokkan offline.** Butuh
  sinkronisasi waktu yang rapi dan sampling INA219 cepat; isolasi mode memberi
  angka steady-state yang lebih bersih dengan kerja lebih sedikit.
- **Tidak memecah `p2` jadi bandpass vs deteksi.** Membongkar modul terverifikasi
  (§1).
- **Tidak mengukur dari baterai LiPo langsung.** Lebih representatif, tapi
  menuntut LiPo + modul charger/proteksi yang belum ada; konversi §6
  menjembataninya.
- **Tidak menyentuh HW-6.** Spek terpisah, dikerjakan sesudah baseline daya
  terkunci.
