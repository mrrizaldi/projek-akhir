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
   tombol B3 (pendek: rekam/jeda/lanjut, tahan: simpan) → PSRAM → LittleFS  (/rekam/NNN.csv)
                          │
                     make pull                      ← colok USB ke laptop
                          ▼
              model/data/recordings/<tanggal-jam>.csv
                          │
                     make analisis FILE=...
                          ▼
     angka kualitas per segmen di terminal + grafik di artifacts/metrics/akuisisi/akuisisi_*.png
```

---

## 1. Rangkaian & penempatan

| Kabel | GPIO | Posisi elektroda |
|---|---|---|
| `OUTPUT` | **1** (ADC1_CH0) | — |
| `LO+` | 42 | — |
| `LO−` | 2 | — |
| B3 (rekam/jeda/simpan) | 6 | — |
| **RA (merah)** | — | bawah selangka kanan |
| **LA (kuning)** | — | bawah rusuk kiri ← mengukur bersama merah |
| **RL (hijau)** | — | bawah rusuk kanan (referensi) |

Pin OUTPUT wajib di **ADC1 (GPIO1–10)**; ADC2 (GPIO11–20) mati total begitu
WiFi menyala. Jalur OUTPUT yang putus membuat pin ADC mengambang dan menyerap
jala-jala; gejalanya `dengung50` ~930 counts di laporan `q` walau elektroda
terpasang (lihat §7).

Tabel di atas adalah bagian akuisisi dari peta pin PCB rev1
(`firmware/include/perangkat.h`). Peta lengkap, termasuk TFT, buzzer, tombol
B1/B2, dan INA219, serta peta tombol dan menu di layar, ada di
[`firmware/README.md`](../../firmware/README.md).
Jalur akuisisi dapat diperiksa tanpa elektroda dengan
`pio test -e esp32-s3 -f test_hw_adc` (ADC terbaca, timer tepat 360 sampel per
detik, status LO dicetak).

Sumbu merah→kuning meniru **MLII**, lead yang dipakai MIT-BIH ("In most
records, the upper signal is a modified limb lead II (MLII), obtained by
placing the electrodes on the chest", PhysioNet `mitdbdir/intro.htm`). AD8232
mengukur beda tegangan pad RA dan pad LA; menurut segitiga Einthoven, sumbu
RA→LA adalah Lead I dan RA→kaki kiri adalah Lead II, sehingga pad kuning (LA)
ditaruh di bawah rusuk kiri sebagai wakil kaki kiri. Penempatan dada pada
panduan SparkFun *AD8232 Heart Rate Monitor Hookup Guide* (LA di dada kiri
dekat lengan) dan diagram 3-lead klinis menaruh kuning di dada kiri atas; yang
terukur dengan cara itu adalah Lead I, yang morfologi QRS-nya berbeda dari data
latih model. Panduan SparkFun tidak menyebut lead yang dihasilkan.

**Daya: powerbank.** Selama USB laptop tertancap saat merekam, dengung 50 Hz
menang. Contoh dari rekaman uji coba (arsip, `20260910-1938` vs `-1948`): 266%
(laptop) vs 46% (powerbank).

**Elektroda sekali tempel.** Sekali dilepas, gel mengangkat minyak kulit dan
kontaknya turun. Contoh dari rekaman uji coba (arsip, `20260910-1948`, `-1951`,
`-2019`): ayunan menurun monoton 691 → 250 → 195 counts mengikuti jumlah
pemasangan ulang.

---

## 2. Arti LED

LED (NeoPixel) adalah **satu-satunya indikator kualitas sinyal**; layar tidak
menuliskan kualitas. Status rekaman tidak ditampilkan lewat LED, melainkan di
pojok kanan atas layar (§3). LED mengukur **ayunan sinyal setelah bandpass 0,5–40 Hz**, pakai fungsi
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
| **Biru** | fase kalibrasi | stabilisasi elektroda; inferensi belum jalan |
| **Oranye** | ayunan bersih < 60 | kontak kurang atau dengung dominan — **jangan rekam** |
| **Hijau** | ayunan bersih ≥ 60 | sinyal sehat, boleh rekam |

Tiga keadaan, tanpa kedip, dan tidak berubah saat merekam. Merekam saat
oranye = rekaman kosong; perbaiki elektrodanya lebih dulu. Merah berkedip
hanya muncul bila inisialisasi TFLM gagal saat boot (bukan keadaan kualitas).

**Fase kalibrasi (biru).** Setiap sesi dimulai di fase kalibrasi dan baru
berpindah ke pemantauan bila tiga syarat terpenuhi bersamaan: sesi sudah
berjalan ≥ 10 menit, RR 300–1500 ms dengan |dRR| ≤ 200 ms tenang selama
30 detik, dan ayunan bersih ≥ 60 (rincian: [`mqtt-walkthrough.md`](mqtt-walkthrough.md)
§3.1). Selama biru, LED tidak menunjukkan oranye/hijau, jadi kualitas kontak
dibaca dari `q` atau dari halaman menu **Kalibrasi → Status** (waktu stabil,
RR tenang, ayunan, sampel hilang; diperbarui tiap detik).

Siapa yang boleh melewati syarat waktu-stabil dan RR-tenang (syarat ayunan
≥ 60 **tidak pernah** dilewati):

| Keadaan | Waktu-stabil & RR-tenang | Keterangan |
|---|---|---|
| sumber = ADC, `k` OFF | **berlaku penuh** | kondisi perekaman resmi |
| sumber = replay acuan atau replay rekaman (menu **Sumber sinyal**; `y` untuk replay acuan) | **dilewati otomatis** selama replay aktif | record 208 aritmik, tidak akan pernah RR-tenang; rekaman yang diputar ulang bukan kontak elektroda yang sedang menstabil, sehingga syarat stabilisasi tidak bermakna; keduanya tanpa elektroda. Serial: `GERBANG DILEWATI (replay)`. Bypass hilang begitu sumber kembali ke Sensor (ADC) |
| lewati ON (`k`, atau menu **Kalibrasi → Lewati (bench)**) | dilewati — **override manual untuk bench** | serial: `GERBANG DILEWATI (bench)`. Mematikannya memulai **sesi baru**, jadi gerbang penuh (termasuk 10 menit) berlaku lagi dari nol |

Jangan merekam data resmi dengan `k` ON: gerbangnya tidak menjamin apa-apa.

**Clipping tidak punya warna.** Pola LED tambahan akan menumpuk arti di satu
warna. Konsekuensinya sinyal yang terpotong di rail tampil **hijau** — LED hanya
mengukur ayunan, dan sinyal terpotong justru berayun lebar. Clipping tetap
dihitung, cek lewat serial:

```
q   laporan kualitas tiap detik (toggle), kolom `clipping`
s   status sesaat, kolom `clipping`
```

Sebelum mulai merekam, aktifkan `q` dan pastikan `clipping 0`. Hijau saja tidak
cukup.

---

## 3. Merekam

Pojok kanan atas layar monitor menunjukkan status rekaman:

| Tampilan | Warna | Arti |
|---|---|---|
| `RECmm:ss` | merah | sedang merekam; waktu = panjang sinyal tersimpan |
| `JEDAm:ss` | kuning | rekaman dijeda; sampel tidak disimpan |
| `SIMPAN` + `/rekam/NNN.csv` | hijau | berkas baru tersimpan (tampil 3 detik) |
| `TERKUNCI` + `tahan B3=simpan` | oranye | menu ditolak karena sesi rekam terbuka (tampil 2 detik, bip tolak) |
| `TOLAK` + `hanya sensor ADC` | oranye | mulai rekam ditolak karena sumber bukan Sensor (ADC) (tampil 2 detik, bip tolak) |
| `RP 208` / `RP#NNN` | kuning | sumber sinyal replay (acuan / rekaman `NNN`), bukan sensor |
| kosong | — | sumber Sensor (ADC), tidak merekam |

Kotak tombol B3 di baris bawah berlabel `B3 REC` saat tidak merekam, `B3 JEDA`
saat merekam, dan `B3 LANJUT` saat dijeda, dengan petunjuk `tahan=SIMPAN`.

1. Pasang elektroda baru sesuai §1. Board diberi daya dari powerbank; USB laptop
   **tercabut**. Pastikan sumber sinyal **Sensor (ADC)**: pojok kanan atas TFT
   tidak menampilkan `RP 208` atau `RP#NNN`. Pilihan sumber tersimpan di NVS,
   sehingga replay yang dipilih sebelumnya tetap aktif setelah boot; ganti lewat
   menu **Sumber sinyal → Sensor (ADC)** (tahan B2 untuk membuka menu).
   Rekam hanya dapat dimulai dari sensor: bila sumber masih replay, B3 dan
   serial `r` ditolak dengan `TOLAK` di layar dan `REKAM hanya dari sensor` di
   serial.
2. Pastikan kualitas sinyal: LED **hijau**, atau selama fase kalibrasi (biru)
   `BERSIH ≥ 60` dan `clipping 0` di laporan `q`.
3. Dari layar monitor (menu tertutup), tekan pendek **B3** (GPIO 6). Pojok kanan
   atas menampilkan `REC00:00` merah yang terus berjalan, dan serial mencetak
   `REKAM mulai`. LED tetap menunjukkan kualitas sinyal. Selama menu terbuka B3
   adalah tombol navigasi dan serial `r` ditolak (`REKAM ditolak: tutup menu
   dulu`), sehingga rekaman selalu dimulai dari layar monitor.
4. Duduk diam, lengan bertumpu, **25 detik**.
5. Bila perekaman perlu dihentikan sementara (subjek bergerak, kabel
   tersenggol), tekan pendek **B3** untuk menjeda. Layar menampilkan `JEDA`
   kuning dan serial mencetak `REKAM jeda n=<sampel> (<detik> detik)`. Tekan
   pendek **B3** lagi untuk melanjutkan; serial mencetak `REKAM lanjut ...`.
   Bagian yang dijeda tidak disimpan, dan berkas mencatat batasnya sebagai baris
   `# jeda`.
6. Tahan **B3** sampai bip panjang (800 ms) untuk berhenti dan menyimpan, baik
   dari keadaan merekam maupun dijeda. Layar menampilkan `SIMPAN` hijau dengan
   nama berkasnya. Hasil yang diharapkan di serial:

   ```
   SIMPAN <n> sampel (<detik> detik, <k> segmen), 0 terlewat, elektroda lepas 0% -> /rekam/001.csv
   ```

   Bila muncul `PERINGATAN: elektroda lepas >10%`, rekaman kemungkinan besar
   kosong; ulangi dari langkah 1.

**Menu dan jalur sinyal terkunci selama sesi rekam.** Sejak `REKAM mulai`
sampai berkas tersimpan, termasuk selama dijeda, menahan B2 tidak membuka menu:
layar menampilkan `TERKUNCI` / `tahan B3=simpan` selama 2 detik dengan bip
tolak, dan serial mencetak `DITOLAK: menu selama sesi rekam, simpan dulu (tahan
B3 / r)`. Perintah serial yang mengubah jalur sinyal (`y`, `V`, `p0`–`p5`, `k`,
`w<n>`, `b<n>`) ditolak dengan pesan `DITOLAK: ...` yang sama. Dengan kunci ini
satu berkas tidak pernah bercampur sensor dan replay, dan tidak berlubang tanpa
baris `# jeda` (tes perangkat menjeda akuisisi, tangga daya memaksa replay 208).
Untuk mengganti sumber, menjalankan tes, mengukur daya, atau mengganti jaringan,
**simpan rekaman lebih dulu** (tahan B3), baru buka menu. B1 pendek (bisu), B2
pendek (beku), serta perintah baca `s`, `l`, `q`, `v` tetap berlaku selama sesi.

Padanan serial: `r` = mulai, atau berhenti dan simpan (juga saat dijeda);
`j` = jeda / lanjut. Serial `s` menampilkan `rekam 1` selama sesi rekaman
terbuka (termasuk saat dijeda) dan `jeda 0/1`.

Seluruh sesi disangga di PSRAM selama merekam dan baru ditulis ke LittleFS
sesudah berhenti; berkas yang sudah tertulis bertahan walau board mati, tetapi
sesi yang belum dihentikan hilang bila daya putus. Penulisan flash ditunda
karena setiap tulis flash menahan interrupt akuisisi dan membuang sampel
(`firmware/README.md` §Jebakan, Akuisisi). Sesudah berhenti, sesi dipecah
menjadi berkas per 5 menit sinyal (`REKAM_SAMPEL_MAKS` = 360 × 300 sampel;
waktu jeda tidak dihitung); header berkas lanjutan memuat `lanjutan=NNN
celah=0`, dan selama merekam layar menampilkan waktu total sesi beserta
`bagian <k>`. Panjang sesi maksimum dicetak saat mulai (`REKAM mulai (maks 5
bagian = 1500 detik)` dengan LittleFS kosong), jadi tarik data sesudah tiap
subjek (`firmware/README.md` bagian Merekam, Rekaman panjang). Bila `lewat=`
di header lebih dari 0, ada sampel yang tidak terambil di berkas itu dan RR di
sekitarnya tidak sahih.
Tiap rekaman disimpan sebagai berkas bernomor baru (`/rekam/001.csv`, `002`,
...); daftarnya dilihat dengan serial `l` dan berkas lama dihapus dengan `h<n>`.
Rekaman yang tersimpan dapat diputar ulang di board lewat menu **Sumber sinyal
→ Replay rekaman**; replay melewati baris `#`, sehingga segmen diputar
bersambung tanpa jeda. Persentase `elektroda lepas` berasal dari pin LO+/LO−;
nilai 0% bukan jaminan ada sinyal (LO cukup dipuaskan satu jalur impedansi
rendah), jadi wasitnya tetap ayunan di §6.

### Format berkas rekaman

```
# fs=360 n=<total sampel> lewat=<hilang> lepas=<LO aktif> (<persen>%)
<counts ADC, satu sampel per baris>
...
# jeda
<counts ADC segmen berikutnya>
...
```

- `n` = jumlah sampel seluruh segmen.
- Baris `# jeda` memisahkan dua segmen. Dua segmen yang bersebelahan **tidak
  kontinu** dalam waktu: sinyal selama jeda tidak ada di berkas.
- Jeda yang langsung diikuti simpan tidak menghasilkan baris `# jeda` di akhir
  berkas, dan jeda tanpa sampel baru tidak menghasilkan segmen kosong.
- Rekaman tanpa jeda tidak memuat baris `# jeda` dan sama dengan format lama.

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
`lepas=<n> (<persen>%)`, jumlah sampel dengan LO aktif selama merekam. Baris
`# jeda` di dalam berkas ikut tertarik apa adanya (format: §3).

Bila board masih merekam atau dijeda, `make pull` menghentikan dan menyimpannya
lebih dulu secara otomatis.

Nama berkas = **waktu tarik**, bukan waktu rekam (`datetime.now()` di
`pull_recording.py`). `make pull` menarik rekaman bernomor terakhir; bila tidak
ada rekaman baru sejak tarikan sebelumnya, rekaman lama itu tertarik lagi dengan
nama baru. Rekaman bernomor lain: `make pull N=<n>` (nama berkas diberi akhiran
`-rekam-NNN`); daftar nomor di board: serial `l`.

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

   Untuk berkas berisi `# jeda`, baris pertama menyebut jumlah segmen dan satu
   baris per segmen mendahului ringkasan gabungan. Contoh dari rekaman uji coba
   (arsip) `20261011-1834` yang disisipi satu `# jeda` buatan sesudah sampel
   ke-4000:

   ```
   20261011-1834-jeda: 10947 sampel = 30.4 detik @ 360 Hz, 0 sampel terlewat, 2 segmen (dipisah jeda)
     segmen 1      11.1 detik   R-peak   11   RR   10   autokorelasi 0.45 @ 60 bpm, 1 puncak setara
     segmen 2      19.3 detik   R-peak   22   RR   21   autokorelasi 0.22 @ 69 bpm, 4 puncak setara
     ADC          1461..3110   clipping 0 sampel OK
     ...
     R-peak       33 dalam 30.4 detik
   ```

   Jumlah RR = R-peak − jumlah segmen (10 + 21 = 33 − 2): interval antara
   R-peak terakhir segmen 1 dan R-peak pertama segmen 2 tidak dihitung karena
   melintasi jeda.

3. Grafiknya otomatis tersimpan di:

   ```
   artifacts/metrics/akuisisi/akuisisi_<nama>.png
   ```

Buka dengan `xdg-open artifacts/metrics/akuisisi/akuisisi_<nama>.png` (grafik
contoh uji coba di atas: `artifacts/arsip/akuisisi-uji-coba/akuisisi_20260910-2019.png`).
Tiga panel: ADC mentah, hasil bandpass + garis R-peak, dan spektrum (pita merah
= 50 Hz, pita hijau = pita EKG). Untuk rekaman berjeda ditambah panel keempat:
seluruh rekaman setelah bandpass pada sumbu waktu gabungan (waktu jeda tidak
dihitung), dengan batas segmen sebagai garis vertikal putus-putus. Garis yang
sama muncul di dua panel pertama bila batasnya jatuh dalam 6 detik pertama.

4. Grafik satu menit untuk dilihat detak per detak:

   ```
   make grafik FILE=data/recordings/<nama>.csv            # 60 detik terbaik
   make grafik FILE=data/recordings/<nama>.csv MULAI=120  # mulai detik 120
   ```

   Hasil: `artifacts/metrics/akuisisi/rekaman_<nama>_detik-<awal>.png`, enam
   baris 10 detik sinyal bandpass 0,5–40 Hz dengan tanda ▼ di setiap R
   terdeteksi, ditambah panel HR per detak. Tanpa `MULAI`,
   `plot_rekaman.py` menggeser jendela 60 detik tiap 5 detik dan memilih yang
   RR tak wajarnya (< 30 atau > 200 bpm) paling sedikit, lalu yang derau
   > 60 Hz-nya paling kecil relatif terhadap pita EKG. Tanda R memakai
   deteksi Pan-Tompkins yang dikoreksi `PT_DETECTOR_OFFSET` lalu diselaraskan
   ke puncak (`selaraskan_r`), sama dengan rantai firmware. Rekaman berjeda
   dicari per segmen; segmen yang lebih pendek dari jendela dilewati. Contoh
   keluaran:

   ```
   jendela detik 240-300: RR tak wajar 0, derau >60 Hz 5.6% pita EKG, HR median 78 bpm (61-95), 76 R
   ```

### Analisis per segmen

`analyze_recording.py` memecah berkas pada setiap `# jeda` dan menghitung tiap
segmen secara terpisah, lalu menggabungkan hasilnya:

| Hitungan | Per segmen | Penggabungan |
|---|---|---|
| Rerata (DC) dan bandpass 0,5–40 Hz | filter mulai dari keadaan nol di awal tiap segmen; transien awal segmen diperlakukan sama dengan transien awal rekaman | sinyal tersaring disambung untuk grafik |
| R-peak Pan-Tompkins | dideteksi per segmen | indeks digeser ke sumbu waktu gabungan |
| RR dan BPM | `diff` R-peak di dalam segmen | disambung; **tidak ada RR yang melintasi jeda** |
| Energi pita (dengung, derau, drift, pita EKG) | per segmen | dijumlahkan, lalu dirasiokan |
| Autokorelasi denyut | per segmen; segmen ≤ 1,5 detik dilewati; segmen ≥ 60 detik dihitung per jendela 30 detik lalu diambil median (`JENDELA_AUTOKORELASI_S`) | rerata berbobot panjang segmen; jumlah puncak setara dibulatkan |
| ADC min/maks, clipping | seluruh sampel | — |

Alasannya: sinyal sebelum dan sesudah jeda tidak bersambung dalam waktu.
Menjalankan filter menyambung akan memasukkan lompatan baseline sebagai
transien palsu, dan RR yang melintasi jeda bukan interval detak sungguhan.
Berkas tanpa `# jeda` adalah satu segmen dan memberi keluaran yang identik
dengan versi sebelum dukungan jeda (diverifikasi pada 27 rekaman arsip: teks
dan PNG sama persis). Uji: `tests/test_analyze_recording.py`.

---

## 6. Membaca angkanya

| Metrik | Target | Kalau meleset |
|---|---|---|
| `sampel terlewat` | **0** | timer bermasalah — laporkan, ini bug firmware |
| `clipping` | **0** | sinyal terpotong, baseline terlalu dekat rail |
| `dengung 50Hz` | < 15% | cabut USB laptop, pilin kabel, cek RL |
| `derau >60Hz` | < 50% | sebagian ditekan bandpass, ikut membaik kalau 50 Hz turun |
| `drift <0.5Hz` | < 10% | subjek bergerak, atau elektroda bergeser |
| `denyut` | ADA, autokorelasi > 0,25 (rekaman ≥ 60 detik: median per 30 detik, ditandai `(median per 30 s)`) | lihat di bawah |
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

Autokorelasi mencari SATU jarak antardetak yang dominan. Pada rekaman panjang
detak jantung berubah antarmenit, sehingga puncaknya melebar dan nilainya
turun walau sinyalnya bagus. Karena itu segmen ≥ 60 detik dinilai per jendela
30 detik dan diambil mediannya. Terukur pada rekaman 300 detik 14 Okt 2026
(arsip uji coba): seluruh rekaman 0,24 (di bawah ambang), per 30 detik
0,25–0,44 dengan median 0,36, HR median per menit 70–81 bpm. Segmen < 60 detik
tetap dinilai utuh; keluaran rekaman arsip 44 detik `20260910-2019` identik
sebelum dan sesudah perubahan ini.

Vonis `PALSU — N puncak setara` berarti autokorelasi tinggi tapi puncaknya
berderet seragam. Jantung memberi **satu** puncak dominan; variabilitas denyut
alami membuat puncak berikutnya meluruh. Deretan puncak setara = gangguan mesin.

---

## 7. Kalau bermasalah

| Gejala | Kemungkinan | Cek |
|---|---|---|
| LED oranye terus | elektroda habis / lead tertukar | ganti elektroda baru; pastikan kuning di rusuk kiri, hijau di rusuk kanan |
| `make pull` → "Tidak bisa membuka" | serial monitor lain terbuka | `lsof /dev/ttyACM0`, tutup PlatformIO monitor di VS Code |
| `make pull` → "Tidak ada rekaman" | belum pernah merekam dan menyimpan | rekam lebih dulu (§3) |
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
| `r` | mulai merekam / berhenti dan simpan, juga dari keadaan jeda (setara B3 pendek saat tidak merekam, B3 tahan saat merekam) |
| `j` | jeda / lanjut rekaman (setara B3 pendek saat merekam) |
| `d` / `d<n>` | dump rekaman terakhir / nomor `<n>` ke serial (`make pull` memakai `d`; tidak ada tombol fisiknya) |
| `l` | daftar rekaman di LittleFS: nomor, ukuran, header |
| `h<n>` | hapus rekaman nomor `<n>` |
| `s` | status sesaat: rekam, jeda, jumlah sampel, fase, beat, antrean, sampel hilang, LO, ayunan, clipping, MQTT, INA219 |
| `q` | toggle laporan kualitas tiap detik |
| `k` | toggle override gerbang kalibrasi untuk uji meja; OFF = sesi baru, gerbang penuh dari nol (lihat §2); setara menu Kalibrasi → Lewati (bench) |
| `y` | toggle sumber sinyal ADC ⇄ replay acuan; ketiga sumber (termasuk replay rekaman) dipilih dari menu Sumber sinyal |
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
