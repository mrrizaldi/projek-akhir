# 05 — Gambar, tabel, persamaan, dan aturan placeholder

## 1. Sebaran per bab (dari Daftar Gambar/Tabel)

| Dok | Gambar B1/B2/B3/B4/B5 | Tabel B1/B2/B3/B4/B5 |
|---|---|---|
| AFIB | 0 / 21 / 10 / 12 / 0 | 0 / 2 / 1 (+1 terhapus) / ±9 / 0 |
| ISYARAT | 0 / 2 / 6 / 14 / 0 | 0 / 3 / 0 / 10 / 0 |
| OFFLINE | 0 / 8 / 7 / 9 / 0 | 0 / 2 / 1 / 2 / 0 |
| GDD | 0 / 4 / 2 / 21 / 0 | 0 / 1 / 0 / 5 / 0 |
| CODACY | 0 / 1 / 2 / 20 / 0 | 0 / 1 / 0 / 3 / 0 |
| BYOM | 0 / 0 / 10 / 6 / 0 | 0 / 1 / 0 / 1 / 0 |

Aturan tak tertulis yang dipatuhi 6/6: **Bab 1 dan Bab 5 tanpa gambar dan
tabel.**

## 2. Inventaris jenis gambar

### Bab 2 (umumnya pinjaman, wajib baris "Sumber")

| Jenis | Fungsi | Contoh lokasi |
|---|---|---|
| Ilustrasi konsep dari paper/web | menjelaskan teori (SVM, clean architecture, retry backoff, GDD, McCall) | AFIB p.38; OFFLINE p.27–32; GDD p.19–26 |
| Bukti masalah (statistik, perbandingan sinyal) | menopang 2.1 | AFIB p.30; GDD p.18 |
| Diagram masalah buatan sendiri | menggambarkan alur lama yang bermasalah | OFFLINE Gambar 2.1, 2.3 (p.18, p.22) |
| Foto modul/komponen | memperkenalkan perangkat keras | AFIB p.40–44 (ESP32, AD8232, MAX30102, TFT, MLX90614) |
| Tangkapan layar alat/platform | memperkenalkan perangkat lunak | AFIB p.45–47 (IDE, ThingsBoard, VS Code); CODACY p.21 |
| Contoh data | memperlihatkan dataset | AFIB p.48 (sinyal beranotasi); ISYARAT Tabel 2.3 berisi gambar isyarat |
| Gambar dari penelitian terkait | memperlihatkan sistem pembanding | AFIB 10 gambar di 2.3 (p.51–65) |

### Bab 3 (buatan sendiri, inti rancangan)

| Jenis | Posisi | Contoh lokasi |
|---|---|---|
| Arsitektur tingkat tinggi (zona bernomor, ikon, panah data) | **gambar pertama 3.2** | AFIB p.75; BYOM p.27; ISYARAT p.30 |
| Alur bisnis sebelum vs sesudah sistem | pembuka desain untuk sistem informasi | GDD p.37–38; OFFLINE p.47 (pasangan dari Gambar 2.3) |
| Tech stack / arsitektur komponen | setelah high-level | OFFLINE p.49; BYOM p.28–29 |
| Rancangan perangkat keras / rangkaian | setelah arsitektur | AFIB p.77 |
| Flowchart / diagram alir (simbol ANSI, hitam-putih) | per proses: perangkat, alur data, training, sinkronisasi, retry, konflik | AFIB p.79–81; OFFLINE p.54–60 |
| Diagram alur bernomor (urutan langkah 1..n di panah) | proses lintas komponen | BYOM p.31–33 |
| Use case | fungsional per aktor | AFIB p.85; ISYARAT p.35 |
| Skema basis data (tabel atau ERD) | penyimpanan | AFIB Tabel 3.1 p.87; ISYARAT Gambar 3.5 p.37 |
| Wireframe / mockup | antarmuka | AFIB p.88–91; ISYARAT p.38 |
| Tahapan penelitian | metodologi | ISYARAT p.36 |
| Gambar kode bermasalah | studi kasus refactoring | CODACY p.33 |

### Bab 4 (bukti)

| Jenis | Contoh lokasi |
|---|---|
| Skematik/wiring per sensor | AFIB p.105–108 |
| Tangkapan layar uji (serial monitor + tampilan perangkat, panel a/b) | AFIB p.105–109 |
| Foto prototipe/enclosure | AFIB p.116 |
| Log transmisi / log retry | AFIB p.117; OFFLINE p.92 |
| Tangkapan layar aplikasi, rangkaian multi-panel per skenario | OFFLINE p.86–95; GDD p.54–73; ISYARAT p.53–60 |
| Dashboard (IoT, analitik) | AFIB p.119; OFFLINE p.96–97 |
| Confusion matrix + ROC | AFIB p.120 |
| Grafik kinerja (latensi, bar chart pembanding) | AFIB p.122; BYOM p.53 |
| Persona, design system, iterasi sebelum-sesudah | GDD p.50–52, p.72, p.77–78 |
| Dokumentasi kegiatan (foto wawancara/validasi) | ISYARAT p.89–90, Lampiran |
| Tangkapan layar alat ukur (Codacy, Postman, Swagger) | CODACY p.43–58; BYOM p.48 |

## 3. Inventaris jenis tabel

| Bab | Jenis tabel | Contoh lokasi |
|---|---|---|
| 2 | karakteristik masalah (normal vs kondisi) | AFIB Tabel 2.1 p.29 |
| 2 | masalah → dampak → solusi | OFFLINE Tabel 2.1 p.20 |
| 2 | **pembanding penelitian terkait** (baris akhir penelitian ini) | 6/6 |
| 2 | aplikasi terkait | ISYARAT Tabel 2.2 |
| 3 | struktur basis data (kolom, tipe, keterangan) | AFIB Tabel 3.1 p.87 |
| 3 | metrik yang akan diambil (metrik, deskripsi, sumber data) | OFFLINE Tabel 3.1 p.62–63 |
| 3 | jadwal pelaksanaan | dihapus di buku full AFIB (sisa rujukan rusak) |
| 4 | spesifikasi perangkat keras dan lunak (+ versi) | AFIB p.102–104; OFFLINE p.83–84 |
| 4 | contoh data/fitur | AFIB Tabel 4.1–4.2 p.100–101 |
| 4 | hasil percobaan berulang (no, kondisi, alat, acuan, selisih) | AFIB Tabel 4.3–4.5 p.112–115 |
| 4 | transmisi/rekapitulasi | AFIB Tabel 4.6–4.7 p.117–118 |
| 4 | sebelum vs sesudah | CODACY Tabel 4.1–4.3; ISYARAT Tabel 4.4–4.7 |
| 4 | test case (ID, status, judul, tipe, prasyarat, langkah, expected, actual) | GDD Tabel 4.4 p.74–76 |
| 4 | hasil wawancara kebutuhan (masalah, kebutuhan, implikasi desain) | GDD Tabel 4.3 p.48–49 |
| 4 | **ketercapaian tujuan** (aspek, status, justifikasi) | GDD Tabel 4.5 p.80–81 |
| 4 | ringkasan hasil per fitur (uji 1 vs uji 2) | ISYARAT Tabel 4.10 p.84 |
| 4 | benchmark | BYOM Tabel 4.1 p.52 |

## 4. Konvensi yang terlihat vs aturan kita

| Hal | Korpus | Aturan kita (`laporan/CLAUDE.md`) |
|---|---|---|
| Posisi caption gambar | di bawah gambar (6/6) | di bawah, tebal, rata tengah |
| Posisi caption tabel | di atas (5/6), ISYARAT di bawah | di atas, tebal, rata tengah |
| Baris "Sumber" gambar pinjaman | di atas caption (OFFLINE, ISYARAT) atau di bawah caption (AFIB) atau nomor sitasi di caption (GDD, CODACY) | "Sumber: ..." 10pt rata tengah **di atas** caption |
| Gaya caption | tebal (AFIB, ISYARAT) atau miring (OFFLINE, GDD, CODACY, BYOM) | tebal |
| Penomoran | per bab "Gambar 3.1"; ada spasi liar "Gambar 3. 2" (AFIB, OFFLINE) | per bab, otomatis dari LaTeX |
| Persamaan | "(2.1)" rata kanan, nomor ganda (AFIB (4.1) dan (4.2) dua kali) | "(Persamaan X.Y)" tebal, otomatis |
| Gambar multi-panel | (a)/(b) di caption + dibahas per panel | sama |
| Kode program | dimasukkan sebagai "Gambar" berisi teks kode (CODACY) | hindari kode panjang di badan, ringkas atau pindah ke lampiran |

## 5. Pola "sandwich" (wajib)

Setiap gambar dan tabel dalam korpus yang baik:

1. **Dirujuk sebelum muncul** dengan nomornya ("ditunjukkan pada Gambar 3.1").
2. **Dijelaskan sesudah muncul** dengan paragraf yang dibuka nomornya ("Gambar
   3.1 menunjukkan ..."), membaca isi secara berurutan.
3. **Ditutup maknanya** terhadap tujuan/sistem.

Rincian per jenis ada di [03-pola-paragraf.md](03-pola-paragraf.md) P10–P12.
Kesalahan yang terlihat: paragraf penjelas yang hanya mengulang caption
("Gambar X diatas merupakan gambar dari ..."), dan rujukan "Tabel 4.8 diatas"
padahal tabelnya baru muncul di bawah (AFIB p.121).

---

## Placeholder gambar

### Aturan (berlaku untuk semua kerja Claude di repo ini)

1. **Claude tidak membuat diagram atau gambar ilustrasi sendiri.** Tidak ada
   Mermaid (`.mmd`), TikZ/pgfplots, PlantUML, Graphviz, SVG/draw.io, skrip
   Python untuk menggambar ilustrasi, atau gambar hasil AI. Gambar ilustrasi
   buatan penulis langsung masuk `laporan/*/gambar/`.
2. Sebagai gantinya Claude menaruh **placeholder** di posisi gambar, berisi
   kartu spesifikasi (lihat §Kartu). User yang menggambar.
3. Yang **tetap** ditulis Claude secara final: caption, `\label`, semua
   `\ref` di teks, paragraf pengantar dan paragraf penjelas gambar.
4. Paragraf penjelas hanya boleh menyebut elemen yang ada di kartu
   spesifikasi. Dengan begitu gambar yang kelak dibuat user cocok dengan teks.
5. Label `RM1..RM4` tidak boleh muncul di gambar apa pun (aturan lama).
6. **Plot data eksperimen bukan ilustrasi.** Confusion matrix, kurva,
   histogram, grafik latensi yang dihasilkan pipeline repo (`model/` dan
   `scripts/export_artifacts.sh` → `laporan/*/gambar/`) boleh langsung dirujuk
   bila berkasnya sudah ada. Bila belum ada, pasang placeholder dan sebutkan
   skrip yang seharusnya menghasilkannya. Jangan menulis skrip plot baru tanpa
   diminta.
7. Placeholder harus mudah dicari: `grep -rn "PLACEHOLDER-GAMBAR" laporan/`.

### Kartu spesifikasi gambar

| Field | Isi |
|---|---|
| ID | `fig:{bab}-{slug}` (sama dengan `\label`) |
| Lokasi | Bab/subbab |
| Jenis | arsitektur, flowchart, diagram alir data, sequence, use case, ERD/skema DB, blok diagram, skematik rangkaian, wiring/pinout, mockup/wireframe, foto perangkat, foto dokumentasi, tangkapan layar, ilustrasi konsep, plot data |
| Pesan utama | satu kalimat: apa yang harus ditangkap pembaca |
| Elemen wajib | daftar kotak/aktor/komponen/layar yang harus ada |
| Alur baca | urutan panah, cabang keputusan, nomor langkah |
| Teks di gambar | label persis yang dipakai di paragraf penjelas |
| Bahan di repo | path sumber kebenaran isinya (kode, konfigurasi, docs) |
| Ukuran | landscape `width=\linewidth` atau vertikal `height=0.6\textheight` |
| Sumber | sitasi bila gambar pinjaman (Bab 2) |

### Templat LaTeX

Hanya memakai `\fbox` dan `\parbox` bawaan LaTeX, tidak perlu paket baru dan
tidak menyentuh `shared/preamble.tex`. Ikuti opsi float yang dipakai file di
sekitarnya.

```latex
% PLACEHOLDER-GAMBAR fig:3-arsitektur  (digambar user, bukan Claude)
% Jenis      : arsitektur sistem, landscape
% Pesan      : {satu kalimat}
% Elemen     : {elemen 1}, {elemen 2}, {elemen 3}
% Alur baca  : {urutan}
% Teks       : {label persis}
% Bahan repo : {path}
\begin{figure}[H]
  \centering
  \fbox{\parbox[c][5cm][c]{0.85\linewidth}{\centering\small
    \textbf{[PLACEHOLDER GAMBAR]}\\[3pt]
    {Jenis}: {ringkasan isi satu baris}\\
    Spesifikasi lengkap ada di komentar sumber.}}
  \caption{Desain Arsitektur Sistem}
  \label{fig:3-arsitektur}
\end{figure}
```

Saat gambar sudah ada, user (atau Claude atas permintaan user) mengganti blok
`\fbox{...}` dengan `\includegraphics[...]{gambar/...}` dan menghapus baris
komentar `PLACEHOLDER-GAMBAR`.

### Templat Markdown (untuk draf di luar LaTeX)

```markdown
> **[PLACEHOLDER GAMBAR fig:3-arsitektur]** Arsitektur sistem (landscape).
> Pesan: {satu kalimat}. Elemen: {daftar}. Alur: {urutan}. Bahan: {path}.
```
