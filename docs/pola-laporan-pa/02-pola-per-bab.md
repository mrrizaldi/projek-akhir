# 02 — Pola per bab dan hubungan antarbab

## 1. Proporsi dan kepadatan

Halaman per bab (termasuk halaman pengisi):

| Dok | B1 | B2 | B3 | B4 | B5 |
|---|---|---|---|---|---|
| AFIB | 8 | 44 | 24 | 30 | 4 |
| ISYARAT (A5) | 4 | 14 | 12 | 50 | 2 |
| OFFLINE | 6 | 28 | 32 | 24 | 4 |
| GDD | 6 | 18 | 8 | 40 | 4 |
| CODACY | 4 | 18 | 8 | 20 | 2 |
| BYOM | 6 | 10 | 16 | 16 | 2 |

Porsi kata per bab (% dari Bab 1–5):

| Dok | B1 | B2 | B3 | B4 | B5 |
|---|---|---|---|---|---|
| AFIB | 8,4 | **42,5** | 19,3 | 26,3 | 3,5 |
| ISYARAT | 6,2 | 16,6 | 14,9 | **59,1** | 3,1 |
| OFFLINE | 7,3 | 30,4 | **36,4** | 23,0 | 2,9 |
| GDD | 10,2 | 26,4 | 11,9 | **47,9** | 3,6 |
| CODACY | 7,5 | **46,4** | 14,4 | 27,9 | 3,7 |
| BYOM | 12,0 | 26,8 | 25,4 | **32,5** | 3,3 |
| **Rentang** | 6–12 | 17–46 | 12–36 | 23–59 | 3–4 |

Penanda sitasi `[n]` per bab:

| Dok | B1 | B2 | B3 | B4 | B5 |
|---|---|---|---|---|---|
| AFIB | 4 | 55 | 0 | 0 | 0 |
| ISYARAT | gaya penulis-tahun, tak terhitung | | | | |
| OFFLINE | 13 | 83 | 0 | 2 | 0 |
| GDD | 10 | 48 | 0 | 0 | 0 |
| CODACY | 15 | 60 | 0 | 0 | 0 |
| BYOM | 9 | 25 | 0 | **12** | 0 |

Median panjang kalimat (kata) dan median panjang paragraf (kata, perkiraan):

| Dok | kalimat B1/B2/B3/B4/B5 | paragraf B1/B2/B3/B4/B5 |
|---|---|---|
| AFIB | 23/22/20/22/24 | 98/81/60/48/74 |
| ISYARAT | 24/21/18/20/24 | 84/70/58/54/73 |
| OFFLINE | 27/25/21/28/35 | 50/73/60/62/66 |
| GDD | 22/20/20/22/18 | 53/48/69/71/70 |
| CODACY | 23/22/18/22/26 | 64/67/57/44/46 |
| BYOM | 24/24/20/21/22 | 77/76/68/54/– |

Pola yang bisa dipegang:
- Bab 1 pendek (4–8 hal., 6–12% kata) tapi paragrafnya paling panjang.
- Bab 2 adalah bab terpadat sitasi. Di progres, Bab 2 sering bab terbesar.
- Bab 3 kalimatnya paling pendek (prosedural, deskripsi komponen).
- Bab 4 membesar seiring kematangan (progres 23–48%, buku 26–59%).
- Bab 5 nyaris konstan: 2–4 halaman, 3–4% kata, tanpa sitasi.

## 2. Kerangka baku (sintesis korpus + Panduan D4TI)

Panduan D4TI (dirangkum di `laporan/CLAUDE.md`) mengatur Bab 1–3. Bab 4–5
diturunkan dari kesamaan keenam dokumen.

```
BAB 1 PENDAHULUAN
  1.1 Latar Belakang
  1.2 Permasalahan
  [1.x Batasan Masalah]        opsional (hanya AFIB)
  1.3 Tujuan                   dibuka kalimat klaim orisinalitas
  1.4 Manfaat
  1.5 Sistematika Penulisan    satu paragraf per bab, Bab 1–5

BAB 2 KAJIAN PUSTAKA
  (paragraf pembuka bab)       Problem dalam Problem Domain → teori → penelitian terkait
  2.1 Deskripsi Permasalahan
  2.2 Teori Penunjang          2.2.1 ... 2.2.n
  2.3 Penelitian Terkait       2.3.1 ... 2.3.n (judul = judul paper)
      + Tabel pembanding (baris terakhir = penelitian ini) + paragraf pemosisian

BAB 3 DESKRIPSI/DESAIN SISTEM
  (paragraf pembuka bab)       lingkup: model, rancangan, variabel, pengumpulan & analisis data
  3.1 Deskripsi Solusi         fitur unik = orisinalitas
  3.2 Desain Sistem            mulai dari diagram high-level, lalu rinci per komponen
      3.2.x ...
  3.x Rencana Pengujian        metrik + cara ukur + target (penutup Bab 3)

BAB 4 EKSPERIMEN DAN ANALISIS
  (paragraf pembuka bab)
  4.1 Parameter Eksperimen
  4.2 Karakteristik Data
  4.3 Tempat Ujicoba
  4.4 Waktu Ujicoba
  4.5 Spesifikasi Peralatan Ujicoba
  4.6 Hasil Eksperimen         4.6.x per uji/fitur, urut kronologis tahap pengembangan
  4.7 Analisis Hasil Eksperimen
  [4.8 Dokumentasi Penelitian] opsional (ISYARAT)

BAB 5 PENUTUP
  (kalimat pembuka bab)        opsional
  5.1 Kesimpulan
  5.2 Saran
```

Judul Bab 3 bervariasi: "Desain Sistem" (AFIB, CODACY) atau "Deskripsi
Sistem" (ISYARAT, OFFLINE, GDD, BYOM). Ikuti templat prodi saat itu.

## 3. Bab 1 — Pendahuluan

### 3.1 Matriks subbab

| Subbab | AFIB | ISYARAT | OFFLINE | GDD | CODACY | BYOM |
|---|---|---|---|---|---|---|
| Latar belakang | 6 par | 5 par | 6 par | 9 par | 4 par | 5 par |
| Permasalahan | daftar pertanyaan a–d ("Bagaimana / Seberapa ...?") | "Identifikasi Permasalahan", 2 par naratif | 2 par naratif + "dua permasalahan utama" bernomor | 3 masalah berjudul + penjelasan | naratif 3 par | kalimat-problem + 3 masalah berjudul |
| Batasan masalah | ada (a–f) | — (batasan ada di Bab 3) | — | — | — | — |
| Tujuan | butir a–d, **tiap butir bertarget angka** | 1 par | kalimat orisinalitas + 2 tujuan | 1 par | 1 par | kalimat orisinalitas + 3 tujuan, 1:1 dengan masalah |
| Manfaat | per pemangku (tenaga medis / masyarakat / mahasiswa) | 1 par | 5 butir bagi pengguna | 2 par | 3 par | per profil pengguna (3) |
| Sistematika | Bab 1–5 | Bab 1–5 | Bab 1–5 | Bab 1–5 | Bab 1–5 | Bab 1–5 |

### 3.2 Alur latar belakang (dipakai 6/6)

| Langkah | Fungsi | Contoh lokasi |
|---|---|---|
| L1 Konteks | tren teknologi/domain yang sedang berkembang | AFIB p.21 par 1; BYOM p.9 par 1 |
| L2 Urgensi berangka | statistik + sitasi (prevalensi, nilai pasar, persentase kegagalan) | AFIB p.21 (prevalensi, 46,3 juta) ; BYOM p.9 (CAGR 21,5%) ; GDD p.11 (12% proyek gagal) |
| L3 Kondisi eksisting + kekurangan | solusi yang ada dan kelemahannya ("Saat ini ... Namun ...") | AFIB p.21–22 (closed system); BYOM p.9 (monolitik) |
| L4 Gap riset | apa yang belum dijawab penelitian sebelumnya | AFIB p.22 (offline vs real-time); OFFLINE p.12 (cross-platform + ISO) |
| L5 Usulan | "penelitian ini mengusulkan/menghadirkan ..." + komponen + alasan pilih metode | AFIB p.22 (sensor + SVM + alasan SVM) |
| L6 Harapan | kontribusi yang diharapkan, sering memuat judul lengkap dalam tanda kutip | AFIB p.22–23 |

### 3.3 Hubungan internal

- Jumlah butir Permasalahan = jumlah butir Tujuan (OFFLINE 2↔2, BYOM 3↔3, AFIB
  4↔4). Saat tujuan berbentuk satu paragraf (ISYARAT, GDD, CODACY) pemetaan ini
  hilang dan analisis Bab 4 jadi sulit ditautkan.
- Target angka di Tujuan (AFIB: PDSR > 90%, MAE RR < 20 ms, sensitivitas &
  spesifisitas > 80%, latensi < 10 s) dipakai ulang di Rencana Pengujian Bab 3
  dan seharusnya dijawab satu per satu di Bab 4–5 (lihat §8).
- Sistematika Penulisan di progres **sudah** menjabarkan isi Bab 4–5 versi
  realisasi (BYOM p.13, GDD p.15–16). Itu yang membuatnya terbaca sebagai buku.

## 4. Bab 2 — Kajian Pustaka

### 4.1 Matriks

| | AFIB | ISYARAT | OFFLINE | GDD | CODACY | BYOM |
|---|---|---|---|---|---|---|
| Paragraf pembuka bab | ✗ | ✓ | ✗ (tetapi 2.2 dan 2.3 berpembuka) | ✓ 2 par | ✓ | ✓ 2 par (frasa Panduan "Problem ... Problem Domain" dipakai eksplisit, p.15) |
| 2.1 Deskripsi Permasalahan | 6 par + Tabel 2.1 + Gambar 2.1 | 2 par | 7 par + 2 gambar + Tabel 2.1 | 2 par + 1 gambar statistik | 3 isu bernomor + par penutup | 4 par, satu par per tantangan |
| Jumlah teori 2.2 | 15 | 9 (butir bernomor, bukan subbab) | 6 | 8 | 9 | 5 |
| Jumlah penelitian 2.3 | 10 | 3 | 7 | 4 | 4 (+ entri "penelitian ini") | 4 |
| Subbab tambahan | 2.4 State of the Art | 2.4 Aplikasi Terkait, 2.5 Dataset | — | — | — | — |
| Tabel pembanding | 12 baris; No/Judul/Penyakit/Model/Dataset/Sensor/Perbedaan | 3 baris; Penelitian/Metode/Kelebihan/Kekurangan/Perbedaan | 8 baris; Peneliti(Thn)/Domain/Fokus/Kontribusi/Teknik/Kelebihan/Keterbatasan | 5 baris; Judul/Fokus/Metode/Hasil | 5 baris; Judul/Fokus/Metodologi/Hasil | 5 baris; Judul/Fokus/Metode/Hasil |
| Baris terakhir = penelitian ini | ✓ "Proposed System" | (kolom Perbedaan) | ✓ "Penelitian ini (2025)" | ✓ (Hasil "-") | ✓ | ✓ "Penelitian yang Diusulkan" |

### 4.2 Fungsi tiap subbab

- **2.1** memperdalam masalah 1.2 dengan bukti dan sitasi. Pola terbaik: satu
  paragraf per masalah/tantangan, urutan sama dengan 1.2 (BYOM p.15–16:
  "Tantangan pertama ... kedua ... Terakhir"). Sering ditopang satu tabel
  karakteristik/masalah atau satu gambar statistik.
- **2.2** memberi definisi + peran dalam penelitian. Tipologi teori yang muncul:
  (a) konsep domain (AFib, ISO, BISINDO), (b) metode/algoritma (SVM, GDD,
  refactoring, DAG), (c) platform/perangkat (ESP32, sensor, Flutter, Laravel,
  Docker), (d) data (MIT-BIH), (e) kerangka evaluasi (McCall, SUS, metrik
  Codacy), (f) alternatif metode sebagai justifikasi pilihan (AFIB 2.2.15).
  Teori alat bantu (Arduino IDE, VS Code) muncul di AFIB tetapi lemah nilainya.
- **2.3** satu subbab per paper, judul = judul paper (Inggris), lalu tabel
  pembanding, lalu paragraf pemosisian.

### 4.3 Urutan 2.2 yang konsisten

Teori diurutkan dari **payung → inti → pendukung**: konteks besar (IoT,
digitalisasi, edge-cloud) → objek/masalah (AFib, offline-first, BYOM) →
metode inti (SVM, sinkronisasi, DAG) → perangkat/platform → dataset → evaluasi
atau alternatif. Pembaca bergerak dari "mengapa" ke "dengan apa".

## 5. Bab 3 — Deskripsi/Desain Sistem

### 5.1 Matriks

| | AFIB | ISYARAT | OFFLINE | GDD | CODACY | BYOM |
|---|---|---|---|---|---|---|
| Pembuka bab | ✗ | ✓ | ✗ | ✗ | ✓ | ✓ (lingkup gaya Panduan) |
| 3.1 Deskripsi Solusi | butir a–f berjudul | 2 fitur bernomor | 6 solusi bernomor | salah judul ("Deskripsi Permasalahan"), 5 par | contoh masalah (gambar kode) → solusi | "Fitur utama pertama ... Terakhir" naratif |
| Gambar pertama 3.2 | arsitektur high-level | desain sistem | alur proses bisnis dengan sistem (lalu tech stack) | alur lama vs alur baru | alur evaluasi (loop) | high-level |
| Rincian berikutnya | HW, 3 flowchart, ekstraksi fitur (persamaan), model (persamaan), use case, DB, mockup | user flow, web app, server, batasan video, arsitektur NLP, use case, tahapan, DB, wireframe | mekanisme A–E (4 diagram alir + tabel metrik), clean architecture & ISO | — | — | backend, worker, BYOM, sinkron versi, deployment, DAG |
| Penutup bab = rencana uji | 3.3 Rencana Pengujian | 3.9 Validasi dan Verifikasi | 3.3 Uji Coba | 3.3 Skenario Ujicoba | 3.3 Skenario + 3.4 Rancangan Evaluasi | 3.2.8 Rencana Pengujian |

### 5.2 Pola top-down (6/6)

1. Deskripsi solusi berupa **daftar fitur**, tiap fitur = masalah apa yang
   dijawab + bagaimana.
2. **Satu diagram tingkat tinggi** dulu, langsung diikuti penjelasan
   komponen bernomor (a, b, c) yang urutannya sama dengan zona di diagram.
3. Turun ke rincian per komponen/alur, masing-masing dengan diagramnya sendiri.
4. **Ditutup rencana pengujian** dengan metrik, cara ukur, dan target/kriteria
   keberhasilan. Inilah jembatan ke Bab 4.1.

## 6. Bab 4 — Eksperimen dan Analisis

### 6.1 Kerangka beku

| Subbab | AFIB | ISYARAT | OFFLINE | GDD | CODACY | BYOM |
|---|---|---|---|---|---|---|
| Pembuka bab | ✓ | ✓ | ✗ | ✗ | ✓ 2 par | ✓ 3 par |
| 4.1 Parameter | 4 kategori a–d | 3 butir | 5 subbab (lingkup, fungsional, FT, kinerja, ISO) | 4 subbab (+ Keterbatasan Scope) | gambar + 4 metrik | 3 subbab metrik, dibenarkan dengan sitasi |
| 4.2 Karakteristik Data | data latih vs data uji + tabel contoh fitur | teks ↔ gesture | jenis data + struktur entitas | data uji fungsional + artefak desain | kode sumber sebagai data, sebelum/sesudah | 4 jenis data, tiap jenis + alasan pemilihan |
| 4.3 Tempat | rumah + lab (alamat lengkap) | daring dari rumah + komunitas | lingkungan pengembangan lokal | lingkungan lokal | lokal + Codacy cloud | rumah + alasan |
| 4.4 Waktu | rentang + "9 sprint" | rentang + tanggal validasi | Sprint 7–8 + tanggal potong | Sprint 7–8 + fokus per sprint + tanggal potong | Mei–Des 2025 | Sprint 1–4 bertanggal |
| 4.5 Spesifikasi | Tabel HW + Tabel SW (versi) | 1 tabel HW+SW | Tabel HW + Tabel SW | 2 tabel | daftar butir | daftar butir + alasan OS |
| 4.6 Hasil | 7 subbab kronologis | 6 subbab, per fitur | 7 subbab, per skenario | "Proses Desain GDD" per tahap metode | baseline → sesudah → ringkasan → uji fungsional | per komponen + benchmark |
| 4.7 Analisis | per pilar (a–d) + keterbatasan | ringkasan temuan bernomor | per mekanisme + kaitan ISO | lingkup, hasil uji, heuristik, **ketercapaian (tabel)** | hipotesis terbukti | performa, **per masalah**, **per tujuan** |

### 6.2 Urutan isi 4.6

Diurutkan mengikuti **urutan pengembangan nyata** (AFIB p.104 menyatakannya
eksplisit: kronologis dari validasi perangkat keras ke integrasi cloud), atau
mengikuti **urutan metode** (GDD: Research → Modeling → Requirements →
Framework → Refinements), atau **sebelum → sesudah** (CODACY). Pilih satu
sumbu dan pertahankan.

### 6.3 Isi 4.7

Tiga gaya, dari paling lemah ke paling kuat:

1. Ringkasan temuan bernomor (ISYARAT): mudah ditulis, tapi tidak menutup
   tujuan secara eksplisit.
2. Analisis per pilar/mekanisme + paragraf keterbatasan (AFIB, OFFLINE).
3. **Analisis per masalah + evaluasi per tujuan** (BYOM 4.7.2–4.7.3) atau
   **tabel ketercapaian** (GDD Tabel 4.5). Ini yang dipakai untuk PA kita.

## 7. Bab 5 — Penutup

| | AFIB | ISYARAT | OFFLINE | GDD | CODACY | BYOM |
|---|---|---|---|---|---|---|
| Kalimat pembuka bab | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ |
| Bentuk kesimpulan | 4 par naratif | par + butir angka | "Pertama/Kedua/Ketiga" temuan | 3 blok bernomor | 5 par naratif | 4 klaim bernomor tebal + par bukti |
| Saran | 5 bernomor | 5 bernomor berjudul | "Pertama–Keempat" | 3 grup a–c | 4 bernomor + par penutup | 3 bernomor berjudul |

Kesimpulan yang baik mengulang **angka** dari Bab 4 dan **memetakan ke
tujuan**; kesimpulan yang lemah mengulang rencana.

## 8. Benang merah antarbab (traceability)

Rantai yang seharusnya utuh di setiap laporan:

```
1.2 Permasalahan[i] → 1.3 Tujuan[i] → 2.1 Tantangan[i] → 3.1 Fitur solusi[i]
   → 3.x Rencana uji: metrik[i] + target[i] → 4.1 Parameter[i]
   → 4.6 Hasil: angka[i] → 4.7 Analisis/ketercapaian[i] → 5.1 Kesimpulan[i]
   → 5.2 Saran (sisa yang belum tercapai)
```

### 8.1 Contoh rantai utuh: BYOM

| Tahap | Isi |
|---|---|
| 1.2 | 3 masalah berjudul: kinerja terpusat, kekakuan monolitik, alur kerja terfragmentasi (p.10–11) |
| 1.3 | 3 tujuan, masing-masing menyebut masalah yang dijawab (p.11) |
| 2.1 | 3 tantangan dengan urutan sama (p.15–16) |
| 3.1 | 4 fitur solusi, tiap fitur dibuka dengan masalah yang dijawab (p.25–26) |
| 3.2.8 | uji beban: skenario, metrik (FPS, latensi, utilisasi), kriteria keberhasilan (p.38–39) |
| 4.1 | metrik pipeline, model, reliabilitas, dibenarkan dengan literatur (p.41–42) |
| 4.7.2 | analisis per masalah, judul = nama masalah (p.54–55) |
| 4.7.3 | evaluasi per tujuan, "Tujuan 1/2/3" (p.55–56), termasuk catatan uji skala penuh belum dilakukan |
| 5.1 | 4 kesimpulan, masing-masing klaim tebal + bukti (p.57) |
| 5.2 | 3 saran = keterbatasan yang tersisa (p.58) |

Celah kecil: uji beban 9 aliran video di 3.2.8 tidak dilaporkan di Bab 4,
hanya ditutup dengan kalimat "pengujian skala penuh belum dilakukan".

### 8.2 Contoh rantai berlabel status: GDD

3 masalah (p.12–13) → tujuan satu paragraf (p.14) → Tabel 4.5 Ketercapaian
dengan 8 aspek berstatus Tercapai / Sebagian Tercapai / Belum Tercapai + kolom
justifikasi (p.80–81) → 5.1 blok "Batasan Penelitian & Progress" (p.83) → 5.2
roadmap PA2 (p.84–85). Status eksplisit seperti ini adalah ciri progres yang
sehat.

### 8.3 Contoh rantai rencana vs terukur: OFFLINE

Rencana 3.3 memuat enam metrik (TTF, TTR, MTBF, Uptime, Downtime, SSR, p.65–75)
→ 4.1.3 menyatakan hanya SSR dan TTR yang diukur, sisanya "masih tahap
perancangan" (p.78–79) → 4.6.7 melaporkan SSR/TTR secara kualitatif + angka
event analitik (p.96–97) → 5.2 menjadikan sisa metrik sebagai saran (p.102).
Pengakuan selisih rencana vs realisasi ditulis terang.

### 8.4 Contoh rantai yang putus: AFIB (buku full)

| Tujuan (p.25) | Rencana (p.92–95) | Bab 4 | Bab 5 |
|---|---|---|---|
| PDSR > 90% | PDR ≥ 90%, latensi 10–30 s | PDSR 100% dari 19 paket (Tabel 4.7), padahal teks menyebut 10 paket (p.118) | "PDSR 100%" |
| MAE interval RR < 20 ms | toleransi < 20 ms vs EKG referensi | **tidak ada MAE RR**; yang dilaporkan akurasi deteksi BPM vs oksimeter (Tabel 4.5) | klaim "seluruh tujuan tercapai" |
| sensitivitas & spesifisitas > 80% | k-fold + uji real-time | akurasi 98,04% dan AUC "mendekati 1"; sensitivitas/spesifisitas tidak dilaporkan terpisah; confusion matrix dideskripsikan "kurang lebih 4.000" | akurasi 98,04% |
| latensi total < 10 s | latensi transmisi | interval kirim ≈ 1 s dan latensi inferensi 0,78 ms, bukan latensi akuisisi-sampai-tampil | "latensi di bawah satu detik" |

Pelajaran: setiap angka target di Tujuan harus muncul sebagai **angka terukur
dengan metrik yang sama** di Bab 4 dan diberi vonis di 4.7/5.1. Kalau metrik
berubah, katakan dan beri alasan.

### 8.5 Contoh rantai sebelum/sesudah: CODACY

2 masalah (duplikasi, tight coupling) → tujuan → 3.4 rancangan evaluasi 4
metrik Codacy sebelum/sesudah → Tabel 4.1 baseline, Tabel 4.2 sesudah, Tabel
4.3 ringkasan (Grade E → A, Issues 26 → 3, Complexity 55 → 9, Duplication 2 →
0) → 4.7 "hipotesis terbukti" → 5.1 mengulang keempat angka. Rantai rapat,
tetapi lingkup hanya satu modul (diakui di 5.2).

## 9. Rujukan silang antarbab di dalam teks

Penanda yang menjahit bab:

| Arah | Bentuk | Contoh lokasi |
|---|---|---|
| Ke belakang | "sebagaimana dijelaskan pada Bab II", "pada bab sebelumnya", "justifikasi desain sistem (Bab 2)" | CODACY p.36; AFIB p.123 |
| Ke depan | "akan dibahas pada bagian 4.6.2", "Subbab berikutnya akan menguraikan ..." | CODACY p.47; OFFLINE p.21 |
| Ke tujuan | "dikaitkan kembali dengan rumusan masalah awal guna menjawab tujuan" | AFIB p.97 |
| Ke tabel lain | "sebagaimana dirangkum pada Tabel 2.1" di tiap paper terkait | CODACY p.27–29 |

Minimal satu rujukan balik per bab ke Tujuan/Permasalahan membuat rantai pada
§8 terlihat oleh penguji.
