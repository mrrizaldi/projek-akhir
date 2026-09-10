# Walkthrough akuisisi sinyal — dari elektroda ke grafik

Panduan kerja, bukan spesifikasi. Ini yang kamu jalankan sendiri di meja:
merekam dari badan, menarik data, menilai kualitas, membuat grafik.

Lanjutan dari [`firmware-walkthrough.md`](firmware-walkthrough.md).

---

## 0. Alur satu layar

```
elektroda → AD8232 → ESP32-S3 (timer 360 Hz)
                          │
                     tombol REC → PSRAM → LittleFS  (/rekaman.csv di board)
                          │
                     make pull                      ← colok USB ke laptop
                          ▼
              model/data/recordings/<tanggal-jam>.csv
                          │
                     make analisis FILE=...
                          ▼
     angka kualitas di terminal + grafik di artifacts/metrics/akuisisi_*.png
```

---

## 1. Rangkaian & penempatan

| Kabel | GPIO | Posisi elektroda |
|---|---|---|
| `OUTPUT` | **4** (ADC1) | — |
| `LO+` | 17 | — |
| `LO−` | 7 | — |
| REC | 6 | — |
| DUMP | 5 | — |
| **RA (merah)** | — | bawah selangka kanan |
| **LA (kuning)** | — | bawah rusuk kiri ← mengukur bersama merah |
| **RL (hijau)** | — | bawah rusuk kanan (referensi) |

Sumbu merah→kuning meniru **MLII**, lead yang dipakai MIT-BIH. Kalau kuning
ditaruh di dada kiri atas (seperti diagram 3-lead klinis), yang terukur jadi
Lead I — morfologi QRS-nya berbeda dari data latih model.

**Daya: powerbank.** Selama USB laptop tertancap saat merekam, dengung 50 Hz
menang. Terukur: 266% (laptop) vs 46% (powerbank).

**Elektroda sekali tempel.** Sekali dilepas, gel mengangkat minyak kulit dan
kontaknya turun. Terukur menurun monoton: 691 → 250 → 195 counts mengikuti
jumlah pemasangan ulang.

---

## 2. Arti LED

LED mengukur **ayunan sinyal setelah bandpass 0,5–40 Hz** — jadi dengung 50 Hz
(di luar pita) tidak ikut terhitung. Ini pakai fungsi `ecg_bandpass` yang sama
dengan pipeline model.

| LED | Ayunan tersaring | Artinya |
|---|---|---|
| **Hijau** | ≥ 60 | boleh rekam |
| **Oranye** | < 60 | kontak kurang — **jangan rekam** |
| **Merah kedip** | — | clipping, sinyal terpotong |
| **Merah tetap** | — | sedang merekam |

Merekam saat oranye = rekaman kosong. Perbaiki dulu elektrodanya.

---

## 3. Merekam

1. Powerbank, USB laptop **tercabut**
2. Tunggu LED **hijau**
3. Tekan **REC** (GPIO 6) → LED merah
4. Duduk diam, lengan bertumpu, **25 detik**
5. Tekan **REC** lagi → tersimpan ke LittleFS di board

Rekaman bertahan walau board mati — tersimpan di flash, bukan RAM.
Maksimum 5 menit; rekaman baru menimpa yang lama.

---

## 4. Menarik data ke laptop

Colok USB, lalu:

```
cd model
make pull
```

Keluarannya:

```
15877 baris -> data/recordings/20260910-2019.csv
# fs=360 n=15877 lewat=0
```

Kalau kamu lupa menekan REC untuk berhenti, `make pull` menghentikan &
menyimpannya dulu secara otomatis.

Semuanya jalan di `.venv` yang sama — `pyserial` sudah masuk `requirements.txt`.
Port bukan `/dev/ttyACM0`? `ECG_PORT=/dev/ttyACM1 make pull`.

---

## 5. Menganalisis

```
make analisis FILE=data/recordings/20260910-2019.csv
```

Keluarannya angka, bukan kesan:

```
percobaan: 15877 sampel = 44.1 detik @ 360 Hz, 0 sampel terlewat
  ADC          3363..3558   clipping 0 sampel OK
  dengung 50Hz   39.1% dari pita EKG   TERLALU BESAR
  derau >60Hz   191.3% dari pita EKG   TERLALU BESAR
  drift <0.5Hz    2.1% dari pita EKG
  denyut       autokorelasi 0.14 @ 88 bpm   TIDAK ADA denyut jelas
  R-peak       169 dalam 44.1 detik
```

Grafiknya otomatis tersimpan:

```
artifacts/metrics/akuisisi_<nama>.png
```

Buka dengan `xdg-open artifacts/metrics/akuisisi_20260910-2019.png`.
Tiga panel: ADC mentah, hasil bandpass + garis R-peak, dan spektrum (pita merah
= 50 Hz, pita hijau = pita EKG).

---

## 6. Membaca angkanya

| Metrik | Target | Kalau meleset |
|---|---|---|
| `sampel terlewat` | **0** | timer bermasalah — laporkan, ini bug firmware |
| `clipping` | **0** | sinyal terpotong, baseline terlalu dekat rail |
| `dengung 50Hz` | < 15% | cabut USB laptop, pilin kabel, cek RL |
| `derau >60Hz` | < 50% | sebagian ditekan bandpass, ikut membaik kalau 50 Hz turun |
| `drift <0.5Hz` | < 10% | kamu bergerak, atau elektroda bergeser |
| `denyut` | ADA, autokorelasi > 0,25 | lihat di bawah |
| `BPM masuk akal` | > 90% | butuh dengung turun dulu |

### Dua metrik denyut, dan kenapa keduanya perlu

**Autokorelasi** bertanya "apakah pola berulang tiap 0,4–1,5 detik?". Dia tahan
derau karena dengung 50 Hz berulang tiap 20 ms — jauh di luar jendela itu.

**Pan-Tompkins** bertanya "di mana lonjakan energi?". Dengung yang kuat bocor
lewat tahap kuadrat + integrasi dan terhitung sebagai QRS — itu sebabnya ia bisa
melaporkan 169 "R-peak" dalam 44 detik.

Vonis `PALSU — N puncak setara` berarti autokorelasi tinggi tapi puncaknya
berderet seragam. Jantung memberi **satu** puncak dominan; variabilitas denyut
alami membuat puncak berikutnya meluruh. Deretan puncak setara = gangguan mesin.

---

## 7. Kalau bermasalah

| Gejala | Kemungkinan | Cek |
|---|---|---|
| LED oranye terus | elektroda habis / lead tertukar | ganti elektroda baru; pastikan kuning di rusuk kiri, hijau di rusuk kanan |
| `make pull` → "Tidak bisa membuka" | serial monitor lain terbuka | `lsof /dev/ttyACM0`, tutup PlatformIO monitor di VS Code |
| `make pull` → "Tidak ada rekaman" | belum pernah menekan REC | rekam dulu |
| dengung > 200% | USB laptop tertancap saat merekam | powerbank |
| amplitudo kecil, dengung rendah | LA & RL tertukar | tukar kuning dan hijau |
| ADC 0 mutlak | pin/jalur korslet atau modul tak bertenaga | `s` di serial, lihat status |

### Perintah serial (kalau ingin mengendalikan dari laptop)

Board menerima satu huruf lewat serial 115200:

| Huruf | Efek |
|---|---|
| `r` | mulai / berhenti merekam (setara tombol REC) |
| `d` | dump rekaman |
| `s` | status: sedang merekam? berapa sampel? LO? |

Berguna kalau tombolnya sulit dijangkau, atau untuk memastikan board tidak
sedang merekam.

---

## 8. Riwayat percobaan (rujukan)

Semua rekaman tersimpan di `data/recordings/`, bernama tanggal-jam.

| # | Daya | Dengung | Denyut | Pelajaran |
|---|---|---|---|---|
| 1–2 | laptop | 83%, 266% | palsu | USB laptop = dengung menang |
| 3 | powerbank | 51% | tidak ada | elektroda ikut bergeser — dua variabel berubah sekaligus |
| **4** | powerbank | **46%** | **ADA 0,49 @ 97 bpm** | satu-satunya yang berhasil |
| 5 | powerbank | 46% | tidak ada | elektroda mulai lelah |
| 6 | ? | 312% | palsu | dengung setinggi ini = tercolok laptop |
| 7 | powerbank | **39%** | tidak ada | dengung terbaik, tapi elektroda sudah habis |

Satu perubahan per percobaan. Percobaan 3 mengubah daya **dan** menggeser
elektroda sekaligus, dan hasilnya ambigu selama beberapa putaran.

---

**[← firmware — port ke ESP32-S3](firmware-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **—**
