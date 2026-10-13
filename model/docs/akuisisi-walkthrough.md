# Walkthrough akuisisi sinyal — dari elektroda ke grafik

> **Ruang lingkup:** prosedur merekam EKG dari tubuh dengan firmware utama, menarik rekaman ke laptop, dan menilai kualitasnya.
> **Kode terkait:** `firmware/src/main.cpp`, `firmware/include/perangkat.h`, `model/scripts/pull_recording.py`, `model/scripts/analyze_recording.py`, `model/Makefile` (target `pull`, `analisis`)
> **Prasyarat:** [`firmware-walkthrough.md`](firmware-walkthrough.md)

Panduan kerja, bukan spesifikasi: merekam dari badan, menarik data, menilai
kualitas, membuat grafik.

> **Status data (13 Okt 2026).** Pengujian rekaman sinyal tubuh secara resmi
> **dimulai 13 Oktober 2026**; rekaman resmi masuk `data/recordings/`. Rekaman
> 10 Sep – 11 Okt 2026 adalah **uji coba** dan diarsipkan di
> [`data/arsip/rekaman-uji-coba/`](../data/arsip/rekaman-uji-coba/README.md)
> (grafiknya di `artifacts/arsip/akuisisi-uji-coba/`). Semua angka di dokumen ini
> yang berlabel *contoh dari rekaman uji coba (arsip)* hanya menggambarkan
> prosedur, **bukan hasil**. Prosedurnya sendiri berlaku.

---

## 0. Alur satu layar

```
elektroda → AD8232 → ESP32-S3 (timer 360 Hz)
                          │
                  tombol B3 (REC) → PSRAM → LittleFS  (/rekam/NNN.csv di board)
                          │
                     make pull                      ← colok USB ke laptop
                          ▼
              model/data/recordings/<tanggal-jam>.csv
                          │
                     make analisis FILE=...
                          ▼
     angka kualitas di terminal + grafik di artifacts/metrics/akuisisi/akuisisi_*.png
```

---

## 1. Rangkaian & penempatan

| Kabel | GPIO | Posisi elektroda |
|---|---|---|
| `OUTPUT` | **1** (ADC1_CH0) | — |
| `LO+` | 42 | — |
| `LO−` | 2 | — |
| B3 (REC) | 6 | — |
| **RA (merah)** | — | bawah selangka kanan |
| **LA (kuning)** | — | bawah rusuk kiri ← mengukur bersama merah |
| **RL (hijau)** | — | bawah rusuk kanan (referensi) |

Pin OUTPUT wajib di **ADC1 (GPIO1–10)**; ADC2 (GPIO11–20) mati total begitu
WiFi menyala. Jalur OUTPUT yang putus membuat pin ADC mengambang dan menyerap
jala-jala; gejalanya `dengung50` ~930 counts di laporan `q` walau elektroda
terpasang (lihat §7).

Tabel di atas adalah bagian akuisisi dari peta pin PCB rev1
(`firmware/include/perangkat.h`). Peta lengkap, termasuk TFT, buzzer, tombol
B1/B2, dan INA219, ada di [`firmware/README.md`](../../firmware/README.md).
Jalur akuisisi dapat diperiksa tanpa elektroda dengan
`pio test -e esp32-s3 -f test_hw_adc` (ADC terbaca, timer tepat 360 sampel per
detik, status LO dicetak).

Sumbu merah→kuning meniru **MLII**, lead yang dipakai MIT-BIH. Kalau kuning
ditaruh di dada kiri atas (seperti diagram 3-lead klinis), yang terukur jadi
Lead I — morfologi QRS-nya berbeda dari data latih model.

**Daya: powerbank.** Selama USB laptop tertancap saat merekam, dengung 50 Hz
menang. Contoh dari rekaman uji coba (arsip, `20260910-1938` vs `-1948`): 266%
(laptop) vs 46% (powerbank).

**Elektroda sekali tempel.** Sekali dilepas, gel mengangkat minyak kulit dan
kontaknya turun. Contoh dari rekaman uji coba (arsip, `20260910-1948`, `-1951`,
`-2019`): ayunan menurun monoton 691 → 250 → 195 counts mengikuti jumlah
pemasangan ulang.

---

## 2. Arti LED

LED mengukur **ayunan sinyal setelah bandpass 0,5–40 Hz**, pakai fungsi
`ecg_bandpass` yang sama dengan pipeline model.

Bandpass itu **tidak membunuh 50 Hz**, cuma meredamnya −9,3 dB (gain 0,342;
diukur dari `ecg_sos` dengan `sosfreqz`). Dengung besar karena USB laptop
tertancap tetap lolos sepertiganya dan sanggup memalsukan LED hijau — contoh
dari uji coba (arsip): ayunan mentah 990 counts dengan ayunan tersaring 380,
padahal isinya jala-jala, bukan EKG. Karena itu firmware mengukur amplitudo 50 Hz dengan Goertzel
(1 detik = 50 siklus bulat, binnya tepat) lalu **mengurangkan** kontribusinya:

```
ayun_bersih = ayun_tersaring − 0,342 × dengung50_puncak-ke-puncak
```

Angka `ayun_bersih` inilah yang menyetir LED, dan yang dicetak `q` sebagai
`BERSIH`.

LED dievaluasi tiap 250 ms dengan urutan prioritas berikut (`perbarui_led()`):

| LED | Kondisi | Artinya |
|---|---|---|
| **Merah** | sedang merekam | hanya itu, tidak ada arti lain |
| **Biru** | fase kalibrasi | stabilisasi elektroda; inferensi belum jalan |
| **Oranye** | ayunan bersih < 60 | kontak kurang atau dengung dominan — **jangan rekam** |
| **Hijau** | ayunan bersih ≥ 60 | sinyal sehat, boleh rekam |

Empat keadaan, tanpa kedip. Merekam saat oranye = rekaman kosong; perbaiki
elektrodanya lebih dulu. Pojok kanan atas TFT menampilkan keadaan yang sama
dengan warna yang sama: `REC <detik>` (merah), `KALIB` (biru muda), `BURUK`
(oranye), `BAIK` (hijau), ditambah `REPLAY` (kuning) saat sumber sinyal replay.

**Fase kalibrasi (biru).** Setiap sesi dimulai di fase kalibrasi dan baru
berpindah ke pemantauan bila tiga syarat terpenuhi bersamaan: sesi sudah
berjalan ≥ 10 menit, RR 300–1500 ms dengan |dRR| ≤ 200 ms tenang selama
30 detik, dan ayunan bersih ≥ 60 (rincian: [`mqtt-walkthrough.md`](mqtt-walkthrough.md)
§3.1). Selama biru, LED tidak menunjukkan oranye/hijau, jadi kualitas kontak
dibaca dari `q`.

Siapa yang boleh melewati syarat waktu-stabil dan RR-tenang (syarat ayunan
≥ 60 **tidak pernah** dilewati):

| Keadaan | Waktu-stabil & RR-tenang | Keterangan |
|---|---|---|
| sumber = ADC, `k` OFF | **berlaku penuh** | kondisi perekaman resmi |
| sumber = replay (`y`) | **dilewati otomatis** selama replay aktif | record 208 aritmik, tidak akan pernah RR-tenang; tanpa elektroda. Serial: `GERBANG DILEWATI (replay)`. Bypass hilang begitu replay dimatikan |
| `k` ON | dilewati — **override manual untuk bench** | serial: `GERBANG DILEWATI (bench)`. Mematikan `k` memulai **sesi baru**, jadi gerbang penuh (termasuk 10 menit) berlaku lagi dari nol |

Jangan merekam data resmi dengan `k` ON: gerbangnya tidak menjamin apa-apa.

**Clipping tidak punya warna.** Merah hanya berarti satu hal: sedang merekam.
Konsekuensinya sinyal yang terpotong di rail tampil **hijau** — LED hanya
mengukur ayunan, dan sinyal terpotong justru berayun lebar. Clipping tetap
dihitung, cek lewat serial:

```
q   laporan kualitas tiap detik (toggle), kolom `clipping`
s   status sesaat, kolom `clipping`
```

Sebelum menekan REC, aktifkan `q` dan pastikan `clipping 0`. Hijau saja tidak
cukup.

---

## 3. Merekam

1. Pasang elektroda baru sesuai §1. Board diberi daya dari powerbank; USB laptop
   **tercabut**.
2. Pastikan kualitas sinyal: LED **hijau**, atau selama fase kalibrasi (biru)
   `BERSIH ≥ 60` dan `clipping 0` di laporan `q`.
3. Tekan **B3 REC** (GPIO 6). LED menjadi merah, TFT menampilkan `REC` beserta
   detiknya, dan serial mencetak `REKAM mulai`.
4. Duduk diam, lengan bertumpu, **25 detik**.
5. Tekan **B3 REC** lagi. Hasil yang diharapkan di serial:

   ```
   SIMPAN <n> sampel (<detik> detik), 0 terlewat, elektroda lepas 0% -> /rekam/001.csv
   ```

   Bila muncul `PERINGATAN: elektroda lepas >10%`, rekaman kemungkinan besar
   kosong; ulangi dari langkah 1.

Rekaman disangga di PSRAM selama merekam, lalu ditulis ke LittleFS saat B3
ditekan kedua kali, sehingga bertahan walau board mati. Maksimum 5 menit
(`DETIK_MAKS` = 300). Tiap rekaman disimpan sebagai berkas bernomor baru
(`/rekam/001.csv`, `002`, ...); daftarnya dilihat dengan serial `l` dan berkas
lama dihapus dengan `h<n>`. Persentase `elektroda
lepas` berasal dari pin LO+/LO−; nilai 0% bukan jaminan ada sinyal (LO cukup
dipuaskan satu jalur impedansi rendah), jadi wasitnya tetap ayunan di §6.

---

## 4. Menarik data ke laptop

1. Tutup serial monitor lain yang memegang port (PlatformIO monitor, VS Code).
2. Colok USB, lalu jalankan:

   ```
   cd model
   make pull
   ```

3. Hasil yang diharapkan (contoh format dari rekaman uji coba; berkasnya kini
   di `data/arsip/rekaman-uji-coba/`):

   ```
   15877 baris -> data/recordings/20260910-2019.csv
   # fs=360 n=15877 lewat=0
   ```

Baris kedua adalah header berkas: `fs` laju sampel, `n` jumlah sampel, `lewat`
sampel yang hilang karena antrean penuh. Firmware utama juga menulis
`lepas=<n> (<persen>%)`, jumlah sampel dengan LO aktif selama merekam.

Bila board masih merekam, `make pull` menghentikan dan menyimpannya lebih dulu
secara otomatis.

Nama berkas = **waktu tarik**, bukan waktu rekam (`datetime.now()` di
`pull_recording.py`). `make pull` menarik rekaman bernomor terakhir; bila B3
tidak ditekan sejak tarikan sebelumnya, rekaman lama itu tertarik lagi dengan
nama baru. Rekaman bernomor lain ditarik lewat serial `d<n>`.

Semuanya jalan di `.venv` yang sama — `pyserial` sudah masuk `requirements.txt`.
Port bukan `/dev/ttyACM0`? `ECG_PORT=/dev/ttyACM1 make pull`.

---

## 5. Menganalisis

1. Jalankan dari `model/`:

   ```
   make analisis FILE=data/recordings/<nama>.csv
   ```

2. Hasil yang diharapkan berupa angka, bukan kesan. Contoh dari rekaman uji
   coba (arsip) yang gagal, `make analisis FILE=data/arsip/rekaman-uji-coba/20260910-2019.csv`:

   ```
   20260910-2019: 15877 sampel = 44.1 detik @ 360 Hz, 0 sampel terlewat
     ADC          3363..3558   clipping 0 sampel OK
     dengung 50Hz   39.1% dari pita EKG   TERLALU BESAR
     derau >60Hz   191.3% dari pita EKG   TERLALU BESAR
     drift <0.5Hz    2.1% dari pita EKG
     denyut       autokorelasi 0.14 @ 88 bpm   TIDAK ADA denyut jelas
     R-peak       169 dalam 44.1 detik
   ```

   Baris `BPM` (rerata, min, maks, persen masuk akal) ikut tercetak bila
   terdeteksi lebih dari dua R-peak.

3. Grafiknya otomatis tersimpan di:

   ```
   artifacts/metrics/akuisisi/akuisisi_<nama>.png
   ```

Buka dengan `xdg-open artifacts/metrics/akuisisi/akuisisi_<nama>.png` (grafik
contoh uji coba di atas: `artifacts/arsip/akuisisi-uji-coba/akuisisi_20260910-2019.png`).
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
| `drift <0.5Hz` | < 10% | subjek bergerak, atau elektroda bergeser |
| `denyut` | ADA, autokorelasi > 0,25 | lihat di bawah |
| `BPM masuk akal` | > 90% (30–200 bpm) | turunkan dengung lebih dulu |

Ambang `dengung`, `derau`, `denyut`, dan `BPM masuk akal` adalah ambang yang
dipakai `analyze_recording.py` untuk vonis `OK` / `TERLALU BESAR` /
`TIDAK KONSISTEN`.

Wasit utama ada tidaknya sinyal adalah **ayunan ADC absolut**, bukan flag LO.
Konversi: ADC 12-bit dengan atenuasi 11 dB ≈ 0,757 mV/count di pin, gain AD8232
~1100, sehingga EKG sehat ~2 mV ≈ ~3.000 counts. Ayunan di bawah ~150 counts
(~0,1 mV) berarti tidak ada biopotensial sama sekali; penempatan lead yang buruk
hanya memangkas 3–5×, bukan 50×.

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
| `make pull` → "Tidak ada rekaman" | belum pernah menekan B3 REC | rekam lebih dulu |
| dengung > 200% | USB laptop tertancap saat merekam | powerbank |
| amplitudo kecil, dengung rendah | LA & RL tertukar | tukar kuning dan hijau |
| `dengung50` ~930 counts di `q` walau elektroda terpasang | jalur OUTPUT putus, pin ADC mengambang | periksa kabel OUTPUT → GPIO1; pastikan pin di ADC1 |
| ayunan tertahan 40–55 counts (lantai derau, ~38 µV input-referred) | sambungan header modul AD8232 tidak tersolder / intermiten | solder header modul, ulangi rekam |
| `elektroda lepas 0%` tetapi rekaman kosong | LO dipuaskan satu jalur (mis. RL saja) | nilai dari ayunan, bukan dari LO |
| ADC 0 mutlak | pin/jalur korslet atau modul tak bertenaga | `s` di serial, lihat status |
| LED biru terus | fase kalibrasi belum lulus (≥ 10 menit + RR tenang 30 detik) | tunggu; `k` hanya untuk uji meja (bukan rekaman resmi) |

Mengukur resistansi rangkaian dengan ohmmeter wajib dalam keadaan daya mati;
ohmmeter pada rangkaian bertegangan memberi angka salah tanpa tanda apa pun.

### Perintah serial

Board menerima satu huruf lewat serial 115200 (`pio device monitor`):

| Huruf | Efek |
|---|---|
| `r` | mulai / berhenti merekam (setara tombol B3) |
| `d` / `d<n>` | dump rekaman terakhir / nomor `<n>` ke serial (`make pull` memakai `d`; tidak ada tombol fisiknya) |
| `l` | daftar rekaman di LittleFS: nomor, ukuran, header |
| `h<n>` | hapus rekaman nomor `<n>` |
| `s` | status sesaat: rekam, jumlah sampel, fase, beat, antrean, sampel hilang, LO, ayunan, clipping, MQTT, INA219 |
| `q` | toggle laporan kualitas tiap detik |
| `k` | toggle override gerbang kalibrasi untuk uji meja; OFF = sesi baru, gerbang penuh dari nol (lihat §2) |
| `y` | toggle sumber sinyal replay ⇄ ADC |
| `m` | toggle publikasi MQTT |

Huruf `y` dan `m` diuraikan di [`mqtt-walkthrough.md`](mqtt-walkthrough.md) §4.
Serial berguna bila tombol sulit dijangkau, atau untuk memastikan board tidak
sedang merekam. Skrip Python yang membuka port serial dapat me-reset board
(pyserial menegaskan DTR/RTS); setel `s.dtr = s.rts = False` sebelum
`s.open()` dan verifikasi state dari balasan board, jangan diasumsikan.

---

## 8. Data uji coba akuisisi (arsip, bukan hasil)

Rekaman resmi (mulai 13 Okt 2026) tersimpan di `data/recordings/`, bernama
tanggal-jam tarik. Rekaman uji coba 10 Sep – 11 Okt 2026 ada di
[`data/arsip/rekaman-uji-coba/`](../data/arsip/rekaman-uji-coba/README.md)
beserta kondisi rangkaiannya. Tabel berikut adalah tujuh rekaman uji coba
pertama (rangkaian breadboard, 10 Sep 2026) — dipertahankan karena
pelajarannya membentuk prosedur §1 dan §3, bukan sebagai hasil.

| # | Daya | Dengung | Denyut | Pelajaran |
|---|---|---|---|---|
| 1–2 | laptop | 83%, 266% | palsu | USB laptop = dengung menang |
| 3 | powerbank | 51% | tidak ada | elektroda ikut bergeser — dua variabel berubah sekaligus |
| **4** | powerbank | **46%** | **ADA 0,49 @ 97 bpm** | satu-satunya yang berhasil |
| 5 | powerbank | 46% | tidak ada | elektroda mulai lelah |
| 6 | ? | 312% | palsu | dengung setinggi ini = tercolok laptop |
| 7 | powerbank | **39%** | tidak ada | dengung terbaik, tapi elektroda sudah habis |

Satu perubahan per percobaan. Percobaan 3 mengubah daya **dan** menggeser
elektroda sekaligus, sehingga hasilnya tidak dapat diatribusikan ke salah satu.

**Contoh rekaman uji coba yang bersinyal** (arsip, bukan acuan resmi):
`data/arsip/rekaman-uji-coba/20260915-1130.csv` — ayunan 3.128 counts,
dengung 3,3%, autokorelasi 0,27 @ 87 bpm, 64 R-peak dalam 47,2 detik, BPM masuk
akal 100% (20 sampel clipping di rail atas). Berguna sebagai pembanding bentuk
grafik saat menguji `make analisis`.

---

**[← firmware — port ke ESP32-S3](firmware-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **—**
