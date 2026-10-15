# 08 — Rencana Bab 4 untuk PA kita

Bab 4 adalah bab yang paling berbeda dari korpus. Bahan kita jauh lebih banyak
(Fase 0–8, 6b, 6c, ablasi A–G, HW-1 sampai HW-7), dan sebagian uji tertahan
oleh hal fisik. Dokumen ini menyusun bahan itu ke kerangka beku 4.1–4.7.

**Tentang angka.** Angka di sini dikutip dari `model/CLAUDE.md` (status 19
Sep 2026) dan ditandai `[MC]`. Gunanya menunjukkan bentuk cerita, **bukan**
untuk disalin ke laporan. Saat menulis, ambil ulang dari sumbernya. Angka yang
berasal dari versi model lama ditandai `[lama]` dan wajib dihitung ulang.

---

## 1. Pembuka bab (templat)

"Bab ini memaparkan eksperimen untuk memvalidasi tiga jalur yang dirancang
pada Bab 3, yaitu *preprocessing* sinyal EKG secara *real-time* di
mikrokontroler, inferensi model CNN INT8 di ESP32-S3, dan *pipeline*
*edge-to-cloud* yang tahan terhadap putusnya koneksi. Pada tahap progres ini,
{ringkasan yang sudah diukur penuh}, sedangkan {yang belum} dijadwalkan pada
tahap berikutnya. Pembahasan mencakup parameter eksperimen, karakteristik
data, tempat dan waktu ujicoba, spesifikasi peralatan, hasil eksperimen per
jalur, dan analisis yang dikaitkan kembali dengan tujuan pada Subbab 1.3."

## 2. Prinsip penyusunan 4.6: per tujuan, bukan per fase

Korpus mengurutkan 4.6 secara kronologis (AFIB) atau mengikuti tahap metode
(GDD). Untuk kita, urutan kronologis akan menghasilkan sebelas subbab yang
melompat-lompat antara Python, C, dan jaringan. Lebih kuat **dikelompokkan
per tujuan**, lalu kronologis di dalamnya. Dengan begitu 4.7 tinggal menilai
per tujuan, dan rantai Permasalahan → Tujuan → Hasil (02 §8) terlihat langsung.

`\subsubsection` di preamble kita bernomor huruf (a., b., c.), cocok untuk
butir di dalam setiap jalur.

```
4.6 Hasil Eksperimen
    (pembuka: tabel perubahan terhadap rancangan Bab 3)
    4.6.1 Jalur Preprocessing Real-Time (Tujuan 1)
          a. verifikasi preprocessing di Python
          b. port ke C dan uji kesetaraan
          c. alur hidup dan beban komputasi
          d. segmentasi di perangkat
          e. akuisisi sinyal tubuh
    4.6.2 Jalur Model TinyML On-Device (Tujuan 2)
          a. pelatihan dan pemilihan titik operasi
          b. evaluasi DS2
          c. ketahanan terhadap galat segmentasi
          d. ablasi dan keputusan desain
          e. kuantisasi INT8
          f. kesetaraan dan kinerja di perangkat
          g. konsumsi daya
    4.6.3 Jalur Pipeline Edge-to-Cloud Resilien (Tujuan 3)
          a. gerbang kalibrasi dan kualitas sinyal
          b. streaming normal
          c. putus koneksi dan pemulihan bufer
          d. latensi dan dekomposisinya
          e. dashboard
4.7 Analisis Hasil Eksperimen
    4.7.1 Ketercapaian Tujuan 1
    4.7.2 Ketercapaian Tujuan 2
    4.7.3 Ketercapaian Tujuan 3
    4.7.4 Perbandingan dengan penelitian terkait (protokol evaluasi)
    4.7.5 Keterbatasan dan status proof of concept
```

## 3. Subbab 4.1–4.5

### 4.1 Parameter Eksperimen

Satu tabel per kategori (pola AFIB 4.1 a–d), setiap metrik disertai target
dari tabel rencana Bab 3 dan alasan pemilihannya (pola BYOM: alasan
bersitasi).

| Kategori | Metrik | Target (sumber) | Alasan / acuan |
|---|---|---|---|
| a. Kualitas klasifikasi | recall, precision, F1, specificity, AUC, confusion matrix, per kelas AAMI, per pasien | "recall kelas Aritmia tinggi" (Tabel rencana model) → **perlu dipertegas, lihat catatan** | standar evaluasi aritmia (AAMI, de Chazal). Accuracy **tidak dipakai** (keputusan terkunci) |
| b. Dampak kuantisasi | delta tiap metrik float32 vs INT8 | "penurunan kecil" → pakai ambang PRD (selisih recall < 2%) | |
| c. Kinerja di perangkat | latensi inferensi per detak, duty cycle, tensor arena, heap, RAM/Flash, ukuran model | < interval antardetak; muat SRAM/flash; ukuran ≤ 25 KB (decision point) | |
| d. Preprocessing di MCU | kesetaraan C vs Python, beban per sampel, puncak burst, sampel hilang | identik dalam toleransi 1 kuantum INT8; sampel hilang 0 | |
| e. Akuisisi | ayunan ADC (counts dan mV), dengung %, R-peak terdeteksi, BPM wajar % | ayunan jauh di atas lantai derau (±150 counts) | |
| f. Pipeline | PDSR, latensi end-to-end (median, p95), entri bufer, data hilang, waktu flush, duplikat | ≥ 95%; ≤ 2 detik; tanpa overflow; 0; ≤ 60 detik; dikenali (Tabel rencana pipeline) | |
| g. Daya | arus dan daya rata-rata per mode | "hemat daya" → **perlu dipertegas** | |

**Catatan target kabur.** Tiga target di tabel rencana proposal tidak bisa
divonis karena tidak berangka ("tinggi", "kecil", "hemat daya"). Ini persis
anti-pola D1 AFIB. Sebelum progres, ambil angka dari DoD PRD (8 item yang
dicek `scripts/check_poc.py`) atau nyatakan terang bahwa targetnya indikatif
dan bandingkan dengan acuan tertentu (penelitian terkait atau baseline).

Tambahkan subbab kecil **4.1.x Lingkup Tahap Progres** (pola GDD 4.1.4):

| Diukur penuh | Fungsional/parsial | Ditunda + alasan |
|---|---|---|
| model DS2, kuantisasi, kesetaraan, kinerja di perangkat, pipeline dengan replay, akuisisi sinyal tubuh | gerbang penuh dengan sinyal tubuh | daya (pembacaan INA219 lewat I2C belum), PCB rev2 |

### 4.2 Karakteristik Data

Ikuti tiga bagian AFIB 4.2 (data latih, data perangkat, penyelarasan), lalu
perluas.

a. **Data sekunder latih/uji.** MIT-BIH Arrhythmia Database: 48 record, 360
Hz, sadapan MLII. Record 102 dan 104 (tanpa MLII) serta 107 dan 217 (paced)
dibuang. Label AAMI dipetakan ke biner Normal/Aritmia. Split inter-patient
DS1/DS2 (de Chazal), VAL = record 101, 114, 201, 220, 223. Augmentasi jitter
empiris dua salinan hanya di DS1. Tabel:

| Himpunan | Record/pasien | Beat | % Aritmia | Dipakai untuk |
|---|---|---|---|---|
| DS1 (dengan augmentasi) | `[MC]` | 152.904 `[MC]` | 10,1 `[MC]` | latih |
| VAL | 5 record | 10.349 per salinan (31.047 dengan augmentasi) `[MC]` | 10,1 `[MC]` | pilih epoch, kalibrasi threshold |
| DS2 | `[MC]` 22 pasien | 49.656 `[MC]` | 11,0 `[MC]` | uji, dibuka sekali |
| TEST-B svdb, TEST-C incartdb | 39 pasien `[MC]` | 85.812 `[MC]` | | uji lintas basis data |

b. **Data primer perangkat.** Rekaman AD8232 di `data/recordings/`: berapa
rekaman, durasi, subjek, kondisi (Lead II, stabilisasi). Termasuk rekaman yang
gagal, karena itu bukti diagnosis masalah akuisisi. Subjek **anonim**: hanya kode (S01,
S02, ...), jenis kelamin dan rentang usia bila perlu. Tanpa nama dan tanpa
foto wajah. Kondisi "subjek sehat" dan persetujuan disebut satu kalimat.

c. **Data replay.** `golden_raw` dan record 208 yang diputar dari ISR sebagai
pengganti sinyal tubuh. Jelaskan mengapa sah: jalur hilir identik, hanya
sumber ADC yang diganti.

d. **Penyelarasan PC ↔ perangkat** (padanan AFIB 4.2 c, versi lebih kuat):
filter kausal `sosfilt` yang sama, *group delay* +4 sampel, R di indeks 132,
z-score per window, koefisien dan model dari satu sumber (`model_int8.h`,
`golden_ref.h`).

e. **Data telemetri.** Struktur payload MQTT dan `ts` waktu kejadian.

### 4.3 Tempat Ujicoba

**Laboratorium** (keputusan user, nama lab diisi saat pasti), disertai alasan
(pola AFIB/BYOM 4.3): peralatan pendukung dan lingkungan terkontrol. Bila
sebagian pengembangan dilakukan di luar lab (mis. ablasi model di komputer
pribadi), pisahkan dua lokasi seperti AFIB 4.3. Tambahkan kondisi yang relevan
untuk hardware: jaringan WiFi (RSSI terukur sekitar −50 dBm `[MC]`, ukur ulang
di lab), broker ThingsBoard di laptop lokal.

### 4.4 Waktu Ujicoba

Rentang per jalur. Tanggal di bawah berasal dari **commit**, sehingga bisa
berbeda dari tanggal percobaan. Ambil tanggal final dari log/rekaman.

| Kegiatan | Rentang menurut repo |
|---|---|
| Model Fase 0–8 | s.d. 10 Sep 2026 |
| Port C dan firmware HW-1 sampai HW-4 | 10–12 Sep 2026 |
| Akuisisi sinyal tubuh HW-5 | 10 Sep – 11 Okt 2026 (rekaman di `model/data/recordings/`) |
| Segmentasi 6b, jitter 6c, kunci window | 12–18 Sep 2026 |
| Ablasi A–G | 19 Sep 2026 |
| Pipeline MQTT HW-6 | 18–19 Sep 2026 |
| PCB rev2 | Okt 2026 (belum selesai) |

Tambahkan kalimat tanggal potong data progres (pola OFFLINE dan GDD 4.4).

### 4.5 Spesifikasi Peralatan Ujicoba

Dua tabel (perangkat keras dan perangkat lunak) dengan **versi persis**.
AFIB menulis "-" pada kolom versi. Jangan ditiru.

| Perangkat keras | Isi |
|---|---|
| Mikrokontroler | ESP32-S3 N16R8, board id `4d_systems_esp32s3_gen4_r8n16` |
| Sensor | AD8232 + elektroda wet-gel Lead II |
| Pengukur daya | INA219 (bila daya sudah diukur) |
| Perakitan | breadboard / PCB rev1 / rev2, sebut yang dipakai per uji |
| Komputer | spesifikasi mesin latih dan broker |
| Jaringan | router/AP WiFi |

| Perangkat lunak | Versi |
|---|---|
| Python | 3.11.9 |
| TensorFlow, NumPy, SciPy, wfdb | **tidak dipatok** di `requirements.txt`. Ambil dari `pip freeze` di `model/.venv` |
| PlatformIO platform espressif32, framework Arduino | dari `pio pkg list` |
| TFLite Micro | `spaziochirale/Chirale_TensorFLowLite` 2.0.0 |
| ThingsBoard CE | `thingsboard/tb-postgres:4.2.1.1` |

Subbagian opsional **Validitas pengukuran**. Isinya jebakan alat ukur yang
sudah ditangani: reset DTR saat membuka serial, resolusi `time()` yang
menyamar jadi latensi, ohmmeter di rangkaian bertegangan, ukuran build yang
berubah tanpa kredensial WiFi. Penguji teknik menghargai bagian ini. Korpus
tidak punya.

## 4. Subbab 4.6

### Pembuka 4.6: tabel perubahan terhadap rancangan

Pola baru, gabungan pengakuan OFFLINE (rencana vs terukur) dan tabel keputusan
`model/CLAUDE.md`.

| Aspek | Rancangan Bab 3 | Realisasi | Alasan + bukti |
|---|---|---|---|
| Ukuran window | 250 sampel (90/160) | 256 (128/128) | ablasi 3 seed, recall S naik dengan konteks pre-R |
| Threshold | 0,35 | 0,80 | VAL ikut ber-jitter, kriteria F1 maksimum tetap |
| Augmentasi | tidak ada | jitter empiris ×2 di DS1 | F1 DS2 naik bahkan pada data bersih |
| Batas ukuran model | 20 KB | 25 KB (disetujui) | varian deploy yang benar 22,9 KB |
| Pooling di model deploy | GlobalAveragePooling1D | DepthwiseConv1D(31) bobot 1/31 | op MEAN di TFLM salah hitung tanpa error |
| Perangkat keras | {versi di proposal} | breadboard → PCB rev1 → rev2 | pin map dan level tegangan |

### 4.6.1 Jalur Preprocessing Real-Time (Tujuan 1)

Setiap butir mengikuti P15 (03): tujuan uji → setup → bukti → observasi →
kondisi awal + perbaikan → hasil → vonis → jembatan.

| Butir | Isi utama | Bukti (tabel/gambar) | Angka kunci |
|---|---|---|---|
| a. Verifikasi di Python | R-peak MLII, bandpass kausal, segmentasi | plot fase 0, fase 1, segmentasi | group delay +4 sampel (+11,2 ms) `[MC]` |
| b. Port C + kesetaraan | preprocessing dan Pan-Tompkins di C diadu dengan golden Python | **tabel kesetaraan** | deteksi 11/11 puncak `[MC]`, `pio test -e native` lulus |
| c. Alur hidup dan beban | ISR 360 Hz → antrean → loop | diagram alur ISR (placeholder), tabel beban | 82 µs/sampel = 3,0% anggaran, burst 33,4 ms, antrean min 13 `[MC]`; produksi: antrean 12 saat burst, hilang 0 `[MC]` |
| d. Segmentasi di perangkat | biaya detektor terhadap recall sistem | tabel sensitivity detektor per kelas | sensitivity S 0,6494 vs Normal 0,9614; recall sistem 0,6035 (anotasi 0,6996) `[MC]` (`fase6b_segmentasi_deteksi.csv`) |
| e. Akuisisi sinyal tubuh | rekaman AD8232, diagnosis eliminasi satu variabel | **tabel kualitas rekaman** + plot rekaman berhasil vs gagal | 1 rekaman 3128 counts, 6 rekaman 40–55 counts `[MC]` |

Butir e adalah **kondisi awal + perbaikan versi panjang** (pola AFIB 4.6.1).
Tuliskan rantai eliminasinya (elektroda, jack, kabel LO, modul+kabel,
penempatan LA, lalu header belum disolder → PCB). Itu bukti metode, bukan aib.
Statusnya tetap ditulis "sebagian".

Format tabel kesetaraan:

| Beat | Label | P(aritmia) PC | P(aritmia) perangkat | Selisih (kuantum INT8) |
|---|---|---|---|---|

Format tabel kualitas rekaman:

| Rekaman | Durasi | Ayunan (counts / mV) | Dengung % | R-peak | BPM wajar % | Status |
|---|---|---|---|---|---|---|

### 4.6.2 Jalur Model TinyML On-Device (Tujuan 2)

| Butir | Isi utama | Bukti | Angka kunci |
|---|---|---|---|
| a. Pelatihan dan titik operasi | class weight, EarlyStopping val_auc, threshold dari VAL | kurva latih | model produksi = 1 epoch, ditulis jujur `[MC]` |
| b. Evaluasi DS2 | confusion matrix lengkap, metrik turunan, per kelas, per pasien | **tabel CM + metrik**, plot CM, tabel per kelas, sebaran per pasien | TP 3813 FN 1637 FP 2302 TN 41904; recall 0,6996, precision 0,6235, F1 0,6594, specificity 0,9479, AUC 0,9334 `[MC]`; median recall per pasien 0,9167, terburuk rec 232 dan 213 `[MC]` |
| c. Ketahanan galat segmentasi | jitter terukur, latih ulang dengan jitter | histogram residu, sweep jitter | inti tajam (80% ≤ 1 sampel), ekor sampai 54 `[MC]` |
| d. Ablasi dan keputusan | yang dikunci, yang ditolak, yang bukan sinyal | **tabel ablasi** | ambang beda bermakna sekitar 0,04 F1, rerata 3 seed `[MC]` |
| e. Kuantisasi INT8 | PTQ full INT8, varian deploy | **tabel delta** + plot CM INT8 | 22,94 KB, delta recall +0,0108 `[MC]` |
| f. Kesetaraan dan kinerja di perangkat | probabilitas perangkat vs PC, sumber daya | tabel kesetaraan, **tabel sumber daya** | 26,6 ms/detak, arena 12.948 B, heap bebas 312.396 B, `pio test -e esp32-s3` 16/16 `[MC]` |
| g. Konsumsi daya | per mode | tabel daya | **belum diukur** (rancangan: `model/docs/arsip/2026-09-16-daya-design.md`). Tetap tulis subbabnya dengan status dan rencana |

Butir b **tidak boleh** meniru AFIB ("kurang lebih 4.000"). Tulis keempat sel
CM persis dan rumus metrik sekali saja (pola P12). Per kelas AAMI dan per
pasien yang ada di `model/CLAUDE.md` masih dari model lama, jadi **hitung ulang**
dengan model yang berlaku.

Format tabel ablasi:

| ID | Yang diubah | Seed | F1 DS2 rerata (rentang) | AUC | Recall S / V / F | TEST-B / TEST-C | Vonis |
|---|---|---|---|---|---|---|---|

Vonis memakai tiga kata yang konsisten: **dikunci**, **ditolak**, **bukan
sinyal**. Pertukaran yang disengaja (LR 1e-3 dipertahankan: AUC dan recall F
lebih baik di 1e-4, tetapi recall S turun) ditulis dengan pola trade-off BYOM
(P16 varian, 03).

Format tabel delta INT8:

| Metrik | float32 | INT8 | Delta |
|---|---|---|---|

Format tabel sumber daya:

| Besaran | Nilai | Kondisi build | Target |
|---|---|---|---|

Kolom "kondisi build" wajib ada (jebakan: RAM/Flash berubah 26,4% → 33,1%
hanya karena kredensial WiFi, `[MC]`).

### 4.6.3 Jalur Pipeline Edge-to-Cloud Resilien (Tujuan 3)

Pola OFFLINE (skenario per kondisi jaringan, log sebagai bukti) + AFIB
(tabel rekapitulasi).

| Butir | Isi utama | Bukti | Angka kunci |
|---|---|---|---|
| a. Gerbang kalibrasi dan kualitas | fase `calibrating`, kriteria RR masuk, gerbang ayunan | diagram state (placeholder) | beat karangan tanpa elektroda gagal di dua gerbang `[MC]` |
| b. Streaming normal | publish per beat/batch | log + tabel transmisi | |
| c. Putus koneksi dan pemulihan | putus WiFi paksa, backlog PSRAM, flush | log + plot isi bufer | backlog 27.000 beat, 40 B/entri, sekitar 4–7 jam; flush sekitar 24 detik; hilang 0; duplikat 0 `[MC]` |
| d. Latensi | median dan p95, dekomposisi | **tabel 6 target**, **tabel dekomposisi**, plot sebaran | PDSR 100% / 99,2%; median 939 / 1.108 ms; p95 1.404 / 3.304 ms (tidak stabil) `[MC]`; sisi alat 869 ms = 89%, jaringan+cloud sekitar 130 ms, broker 1,1 ms `[MC]` |
| e. Dashboard | widget, status kualitas, histori | tangkapan layar | |

Format tabel 6 target (langsung menjawab tabel rencana pipeline Bab 3):

| Aspek | Metrik | Target | Ulangan 1 | Ulangan 2 | Status |
|---|---|---|---|---|---|

Ekor p95 yang tidak stabil **ditulis**, beserta penyebab terukurnya
(retransmisi TCP karena kontensi WiFi) dan alasan tidak dikejar. Ini pola
BYOM: kelemahan terukur → sumber → alasan diterima.

## 5. Subbab 4.7

### 4.7.1–4.7.3 Ketercapaian per tujuan

Gabungan GDD Tabel 4.5 dan BYOM 4.7.3. **Draf status per 10 Okt 2026**,
verifikasi sebelum dipakai:

| Tujuan | Target (Bab 3) | Hasil | Status | Justifikasi |
|---|---|---|---|---|
| 1. Preprocessing ringan real-time di MCU | setara Python, real-time, sampel tidak hilang | setara (11/11 puncak, probabilitas cocok), beban rata-rata 3%, hilang 0; akuisisi sinyal tubuh tervalidasi | **Tercapai** | jalur komputasi terbukti setara, akuisisi dari tubuh tervalidasi |
| 2. Model INT8 on-device tanpa cloud | recall tinggi*, delta kecil*, < interval antardetak, muat memori, hemat daya* | INT8 22,94 KB, delta recall +0,0108, 26,6 ms/detak, RAM muat; daya belum | **Sebagian** | daya belum diukur; target * harus diberi angka (§3 catatan) |
| 3. Pipeline MQTT + local buffering | 6 target tabel rencana | 6/6 terukur, 2 ulangan, dengan replay | **Tercapai dengan replay** | gerbang penuh dengan sinyal tubuh belum diuji |

Setiap 4.7.x: satu paragraf P16 (klaim → bukti → mekanisme → kaitan tujuan →
batasan), lalu satu kalimat vonis.

### 4.7.4 Perbandingan dengan penelitian terkait

Satu tabel kecil yang menyandingkan **protokol** (split, unit, kelas, metrik)
dan angka, lalu paragraf P9. Wajib ada karena pembimbing pernah membaca AFIB
dengan akurasi 98,04% (07 §3).

### 4.7.5 Keterbatasan dan status proof of concept

Pola AFIB 4.7 d + GDD p.81. Bahan: subjek sehat dan jumlah terbatas,
daya belum, latensi p95 tidak stabil, model biner
saja, recall S rendah (pertukaran yang disengaja). Keamanan transport tidak
dibahas sama sekali (keputusan user), jadi jangan dimunculkan di sini maupun
di Saran, walaupun AFIB menulisnya.

## 6. Gambar Bab 4: sudah ada vs placeholder

Plot data yang **sudah dihasilkan pipeline** dirujuk lewat jalur export.
Yang lain jadi placeholder (05 §Placeholder).

| ID | Isi | Status | Sumber |
|---|---|---|---|
| fig:4-rpeak | R-peak anotasi pada MLII | ada | `model/artifacts/metrics/fase0_100.png`, `fase0_114.png` |
| fig:4-filter | sinyal sebelum/sesudah bandpass | ada | `fase1_100.png`, `fase1_114.png` |
| fig:4-segmen | window per beat | ada (window 256) | `fase1_segment_100.png` via `make plot1seg` |
| fig:4-pantompkins | deteksi Pan-Tompkins | ada (cek masih relevan) | `pantompkins_100.png` |
| fig:4-latih | kurva latih val_auc | ada (18 Sep) | `fase5_training.png` |
| fig:4-cm-fp32 | CM DS2 float32 | ada (18 Sep) | `fase6_confusion_fp32.png` |
| fig:4-cm-int8 | CM DS2 INT8 | ada (18 Sep) | `fase7_confusion_int8.png` |
| fig:4-jitter | residu dan sweep jitter | ada (18 Sep) | `jitter/jitter_residu.png`, `jitter/sweep_jitter_dasar.png` |
| fig:4-rekaman-ok / -gagal | rekaman AD8232 berhasil vs gagal | ada | `akuisisi/akuisisi_20260915-1130.png` + satu rekaman gagal |
| fig:4-dashboard | dashboard ThingsBoard | ada (cek terkini) | `dashboard/preview.png` |
| fig:4-per-pasien | sebaran recall per pasien DS2 | placeholder, skrip belum ada | data `fase6_per_record_fp32.csv` |
| fig:4-ablasi | grafik ablasi | placeholder, skrip belum ada | `scripts/ringkas_ablasi.py` (keluaran tabel) |
| fig:4-latensi | sebaran latensi pipeline | placeholder, skrip belum ada | log HW-6 |
| fig:4-bufer | isi bufer selama putus-sambung | placeholder, skrip belum ada | log HW-6 |
| fig:4-foto-rakitan | foto breadboard/PCB | placeholder (foto user) | — |
| fig:4-elektroda | posisi elektroda Lead II | placeholder (foto user) | — |
| fig:4-alur-isr | ISR → antrean → loop → inferensi | placeholder (diagram user) | `firmware/src/main.cpp`, `ecg_live.cpp` |
| fig:4-state-gerbang | state machine calibrating → running | placeholder (diagram user) | `firmware/src/ecg_mqtt.cpp`, `model/docs/mqtt-walkthrough.md` |

Untuk tiga plot data yang skripnya belum ada: tanyakan dulu ke user sebelum
menulis skrip. Aturan placeholder melarang membuat skrip gambar baru tanpa
diminta.

Pindah gambar ke `laporan/*/gambar/` lewat `scripts/export_artifacts.sh`
(opt-in `--laporan`), jangan salin manual. Saat ini tujuan skrip itu terkunci
ke `laporan/proposal-pa/gambar`. Progres dan buku ditulis di
`laporan/buku-pa` (keputusan user), jadi tujuannya perlu diarahkan ke
`laporan/buku-pa/gambar`. Langkah itu menyalin ke `laporan/`, jadi konfirmasi
dulu saat dikerjakan.
