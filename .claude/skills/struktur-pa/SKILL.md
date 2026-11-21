---
name: struktur-pa
description: Dipakai saat menyusun, mengubah, atau meninjau kerangka laporan PA (laporan/buku-pa, progres-pa-1, proposal-pa) di tingkat bab dan subbab, misalnya "tambah subbab", "pindahin Keterbatasan ke Bab 5", "tulis abstrak", "susun Bab 4 dan Bab 5", "pasang gambar", "bikin placeholder gambar", "cek benang merah", "audit ketercapaian tujuan", "QA sebelum kumpul", atau "check the report structure". Memuat kerangka beku Bab 4-5, aturan 4.6 dan 4.7, benang merah Permasalahan-Tujuan-Hasil-Kesimpulan, register per bab, kartu placeholder gambar, larangan penunjuk bab/subbab, dan daftar periksa sebelum kumpul. Pakai juga bila user meminta mengubah kerangka beku atau menambah 4.8.
---

# Struktur PA

Kerangka resmi Bab 1-3 ada di `laporan/CLAUDE.md` bagian Struktur Resmi Proposal PA, dan Bab 1 buku mengikuti proposal (skill `buku-ikut-proposal`). Paragraf diatur skill `tulis-tanpa-slop` bersama skill user `indonesian-antislop-writing`: muat keduanya saat menulis atau menyunting paragraf. Tabel diatur skill `tabel-pa`. Aturan gaya paragraf bernomor yang sudah dinonaktifkan ada di `.claude/skills-arsip/narasi-pa/SKILL.md`, dan ringkasan yang dibutuhkan di sini ditulis ulang di aturan 2 dan 8.

`laporan/` read-only tanpa konfirmasi user. Bila tidak berwenang menyunting, tulis jawaban sebagai usulan, dan konsisten sebagai usulan di seluruh pesan.

## Aturan

1. **Kerangka Bab 4-5 beku.** Urutannya: 4.1 Parameter Eksperimen, 4.2 Karakteristik Data, 4.3 Tempat Ujicoba, 4.4 Waktu Ujicoba, 4.5 Spesifikasi Peralatan Ujicoba, 4.6 Hasil Eksperimen, 4.7 Analisis Hasil Eksperimen, lalu 5.1 Kesimpulan dan 5.2 Saran. Pertahankan urutan dan judul persis, termasuk "Ujicoba" (bukan "Uji Coba"), karena kerangka ini diturunkan dari panduan proposal D4TI dan pola laporan PA PENS (`laporan/CLAUDE.md` Struktur Resmi Proposal PA).
   - Bab tidak punya paragraf pembuka: judul bab langsung diikuti subbab pertama (2.1 Deskripsi Permasalahan, 3.1 Deskripsi Solusi, 4.1 Parameter Eksperimen, 5.1 Kesimpulan), mengikuti proposal. Diperiksa `cek_tabel.py` (N-PEMBUKA-BAB).
   - Subbab di luar kerangka (misalnya 4.8 Dokumentasi) hanya atas permintaan user, dan permintaan itu dijawab sebagai opsi: sebut bahwa 4.8 di luar kerangka beku, rekomendasikan foto dokumentasi masuk 4.5 atau lampiran, lalu tunggu keputusan user. Memindahkan Keterbatasan ke Bab 5 juga ditolak, karena Bab 5 tidak memuat temuan baru (aturan 6).

2. **4.6 dan 4.7 berurutan seperti tujuan, dinamai menurut isinya.** 4.6.1 sampai 4.6.n mengikuti urutan Tujuan di Bab 1, kronologis di dalamnya, dan butirnya memakai `\subsubsection` (bernomor huruf). 4.7 berisi tabel ketercapaian (Tercapai / Sebagian tercapai / Belum tercapai, kosakata `tabel-pa` aturan 8), satu subbab analisis per jalur yang sama, subbab perbandingan protokol dengan penelitian terkait, lalu subbab Keterbatasan dan Status *Proof of Concept* sebagai penutup Bab 4. Gayanya mengikuti buku AFIB, karena itu keputusan user (selaras `laporan/CLAUDE.md`).
   - Judul subbab dan kalimat menyebut isi tujuannya ("Jalur *Pipeline Edge-to-Cloud* Resilien", "Analisis Jalur *Pipeline Edge-to-Cloud* Resilien"), bukan label bernomor: tanpa "(Tujuan 1)", "Ketercapaian Tujuan 2", "Subbab ini menjawab Tujuan 3", "Tujuan pertama tercapai sebagian". Kolom tabel ketercapaian berisi nama jalur. Diperiksa `cek_tabel.py` (N-TUJUAN).
   - Subbab dan butir langsung ke isi, tanpa pembuka meta seperti "Bab ini ...", "Subbab ini memaparkan ...", atau "Butir ini bertujuan ...", karena pembaca sudah melihat judulnya. Diperiksa `cek_tabel.py` (N-META).
   - Kaitan ke tujuan dinyatakan sekali di pembuka 4.6 ("disusun mengikuti tujuan penelitian") dan di awal 5.1, tanpa `\ref` ke subbab (aturan 11).
   - Tidak ada tabel atau paragraf "perubahan rancangan dari proposal". Bab 3 memuat rancangan akhir, dan alasan berbasis ukur muncul di butir hasilnya (ablasi, uji kesetaraan).

3. **Benang merah utuh dan dapat ditelusuri.** Jalurnya: Permasalahan[i] → Tujuan[i] → 2.1 tantangan[i] → 3.1 fitur[i] → Rencana Pengujian (metrik + target) → 4.1 parameter → 4.6 angka → 4.7 vonis → 5.1 kesimpulan[i] → 5.2 sisa. Jumlah butir Permasalahan sama dengan Tujuan, karena butir tanpa pasangan tidak bisa divonis.
   - Setiap target di Rencana Pengujian muncul di 4.6 sebagai angka dengan metrik yang sama dan diberi vonis di 4.7. Metrik yang berubah dikatakan beserta alasannya.
   - Uji yang direncanakan tetapi tidak dilakukan ditulis eksplisit "belum dilakukan" beserta alasannya, bukan dihilangkan diam-diam.
   - Target tanpa angka ("tinggi", "kecil", "hemat") tidak bisa divonis, termasuk saat hasilnya belum diukur. Tulis statusnya "Belum dapat divonis (target tanpa angka)" di tabel ketercapaian, lalu sebut perlakuannya: beri angka dari rencana, atau tulis "target indikatif" dan bandingkan dengan pembanding yang disebut. "Belum tercapai" hanya untuk target berangka yang diukur dan tidak terpenuhi.
   - Tiap bab punya minimal satu rujukan balik ke tujuan atau permasalahan tanpa nomor dan tanpa penunjuk subbab ("dikaitkan kembali dengan tujuan penelitian").

4. **Register ditentukan bab, bukan jenis dokumen.** Bab 3 tetap register rancangan ("dirancang") bahkan di buku full, dan isinya rancangan akhir sistem yang diuji di Bab 4, tanpa riwayat revisi internal (rev1, rev2, "PCB revisi kedua", siapa yang mendesain). Diperiksa `cek_tabel.py` (N-REVISI). Bab 4-5 ditulis sebagai capaian dengan kondisi uji menempel pada klaim. Buku full tidak memuat frasa progres ("tahap progres ini", "fase berikutnya", "sprint berikutnya", "semester berikutnya") dan tidak menyebut "proposal ini". Hal yang belum terjadi ditulis `\PlaceholderData{...}` atau "belum diukur", tidak pernah dalam bentuk lampau, karena klaim lampau atas hal yang belum diukur adalah klaim palsu.

5. **Sebaran gambar, tabel, dan sitasi.** Bab 1 dan Bab 5 tanpa gambar dan tabel. Bab 2 memuat gambar pinjaman ber-"Sumber", Bab 3 rancangan sendiri, Bab 4 bukti. Sitasi menumpuk di Bab 1-2; di Bab 3-5 sitasi hanya untuk membenarkan metrik, ambang, atau protokol evaluasi. Subbab teori hanya untuk teori yang menopang keputusan rancangan atau evaluasi, bukan alat bantu (IDE, editor).

6. **Bab 5 pendek dan tertutup.** Dua sampai empat halaman, tanpa angka atau temuan baru, tanpa sitasi. 5.1 menutup per tujuan dengan pola klaim lalu bukti angka dari Bab 4. Tulis "seluruh tujuan tercapai" hanya bila tabel ketercapaian 4.7 seluruhnya Tercapai. 5.2 buku full berisi arah di luar lingkup, 5.2 progres berisi pekerjaan tersisa. Hal yang sudah user putuskan tidak dibahas (keamanan transport TLS/MQTTS) tidak muncul di Keterbatasan maupun Saran.

7. **Abstrak buku full adalah abstrak hasil.** Urutannya: masalah dan urgensi, tujuan, perangkat dan metode, angka hasil utama (metrik model, kinerja di perangkat, pipeline), lalu status dan keterbatasan paling banyak dua kalimat. Angka abstrak sama dengan angka Bab 4 dan Bab 5. *Abstract* berbahasa Inggris berisi hal yang sama. Abstrak proposal dan progres boleh berupa rencana tanpa angka.

8. **Setiap gambar dan tabel diapit.** Rujuk dengan nomor sebelum muncul, jelaskan sesudah muncul dengan paragraf yang dibuka temuan atau nomornya, lalu tutup dengan makna terhadap tujuan.
   - Jangan menyebut posisi gambar atau tabel dengan "di atas" atau "di bawah" ("Tabel 4.2 di atas"), karena posisi float berubah; kata itu tetap boleh untuk besaran ("di atas ambang").
   - Bacakan gambar mengikuti alurnya (flowchart per cabang keputusan, arsitektur per zona bernomor, panel (a)/(b) disebut di caption dan di paragraf).
   - Paragraf penjelas yang hanya mengulang caption adalah pelanggaran.

9. **Placeholder gambar.** Jangan membuat diagram atau gambar ilustrasi (tidak ada Mermaid, TikZ, PlantUML, Graphviz, SVG, draw.io, skrip gambar baru, atau gambar AI): user yang menggambar. Pasang placeholder berisi kartu spesifikasi di posisi gambar, dan tulis caption, `\label`, semua `\ref`, paragraf pengantar, dan paragraf penjelas final.
   - Pembacaan gambar di paragraf penjelas hanya menyebut elemen, label, dan alur yang ada di kartu, dengan kata yang sama persis (kartu "gerbang kalibrasi" berarti paragraf "gerbang kalibrasi", bukan "gerbang awal"), supaya paragraf tetap benar saat gambar selesai digambar.
   - Sesudah seluruh pembacaan selesai, tutup paragraf dengan tepat satu kalimat makna yang boleh mengaitkan gambar ke tujuan, tanpa penunjuk subbab (aturan 11). Jangan menyelipkan kalimat fungsi atau alasan ("syarat ini mencegah ...") di tengah pembacaan, dan jangan menambah kalimat makna kedua.
   - Plot data eksperimen dari pipeline repo (confusion matrix, kurva, grafik latensi) bukan ilustrasi. Rujuk berkas yang sudah di-export. Bila belum ada, placeholder menyebut skrip penghasilnya, dan skrip plot baru tidak ditulis tanpa diminta.
   - Label `RM1..RM4` tidak muncul di gambar.
   - Pencarian sisa placeholder: `grep -rn "PLACEHOLDER-GAMBAR" laporan/`.

   Kartu spesifikasi berisi: ID (`fig:{bab}-{slug}`, sama dengan `\label`), lokasi, jenis (arsitektur, flowchart, diagram alir data, state machine, blok diagram, skematik, wiring/pinout, mockup, foto perangkat, tangkapan layar, ilustrasi konsep, plot data), pesan utama satu kalimat, elemen wajib, alur baca, teks di gambar (label persis yang dipakai paragraf), bahan di repo (path sumber kebenaran), ukuran (landscape `width=\linewidth` atau vertikal `height=0.6\textheight`), dan sumber bila pinjaman.

   ```latex
   % PLACEHOLDER-GAMBAR fig:3-arsitektur  (digambar user, bukan Claude)
   % Lokasi     : {subbab tempat gambar}
   % Jenis      : arsitektur sistem, landscape
   % Pesan      : {satu kalimat}
   % Elemen     : {elemen 1}, {elemen 2}, {elemen 3}
   % Alur baca  : {urutan}
   % Teks       : {label persis}
   % Bahan repo : {path}
   % Ukuran     : width=\linewidth (landscape) atau height=0.6\textheight (vertikal)
   \begin{figure}[!ht]
     \centering
     \fbox{\parbox[c][5cm][c]{0.85\linewidth}{\centering\small
       \textbf{[PLACEHOLDER GAMBAR]}\\[3pt]
       {Jenis}: {ringkasan isi satu baris}\\
       Spesifikasi lengkap ada di komentar sumber.}}
     \caption{Desain Arsitektur Sistem}
     \label{fig:3-arsitektur}
   \end{figure}
   ```

   Saat gambar sudah ada, ganti blok `\fbox{...}` dengan `\includegraphics` dan hapus baris komentar `PLACEHOLDER-GAMBAR`. Gambar masuk `laporan/*/gambar/` lewat `scripts/export_artifacts.sh --laporan`, bukan salinan manual.

10. **Pembimbing PA ini sama dengan pembimbing buku AFIB (Mulyawan 2026).** Tiru formatnya: Tujuan bertarget, tabel State of the Art dengan baris terakhir "Penelitian ini", 4.7 ditutup keterbatasan dan status *proof of concept*. Hindari kelemahannya: target tujuan yang tidak diukur dengan metrik yang dijanjikan, *confusion matrix* yang dideskripsikan kira-kira, hanya akurasi, dan klaim seluruh tujuan tercapai tanpa tabel ketercapaian.
    - Jangan menyandingkan F1 *inter-patient* PA ini langsung dengan akurasi AFIB, karena metrik dan protokolnya berbeda.
    - 4.7 memuat tabel protokol evaluasi (pembagian data, unit, kelas, metrik), dan 4.1 memuat alasan accuracy tidak dipakai (kelas Normal mendominasi).
    - Nada "melanjutkan penelitian terdahulu", bukan menjatuhkan.
    - Setiap keunggulan yang diklaim atas AFIB (inferensi di perangkat, evaluasi *inter-patient*, kesetaraan preprocessing, ketahanan putus koneksi, ukuran model) punya angka di Bab 4.

11. **Tanpa penunjuk bab, subbab, dan butir di teks tercetak.** Jangan menulis "sebagaimana diuraikan pada Bab~\ref{..}", "(Subbab~\ref{..})", "pada Bab 3", "dibahas pada butir d", atau "dijelaskan pada sub-bagian berikut". Tulis isinya langsung ("metrik *recall*, *precision*, ...", "di antara modul pengisi baterai dan konverter"), atau buang penunjuknya bila kalimat tetap utuh. Keputusan user, karena proposal tidak memakainya.
    - Tetap boleh: rujukan Tabel, Gambar, dan Persamaan, dan "... pada butir berikut" yang langsung diikuti daftar.
    - Subbab Tujuan di Bab 1 berakhir pada daftar tujuan, tanpa kalimat sesudahnya.
    - Aturan ini berlaku untuk kalimat `.tex` yang dicetak. Pesan, rencana, dan catatan ke user boleh menyebut nomor bab dan subbab.
    - Diperiksa `cek_tabel.py` (N-PENUNJUK).

## Anti-pola yang diperiksa

| Kelompok | Kesalahan yang dicari | Pencegahan |
|---|---|---|
| Sisa versi lama | "proposal ini" di buku, "tiga bab" padahal lima, rujukan ke tabel yang dihapus, teknologi lama di teori, teori dataset yang tidak dipakai | grep dari daftar periksa, hapus elemen bersama semua `\ref`-nya |
| Navigasi | nomor ganda, "Tabel X di atas" padahal muncul sesudahnya, judul subbab tidak cocok isi, salah ketik judul baku | `\label`/`\ref`, pola apit (aturan 8), judul disalin dari aturan 1 |
| Sitasi | nomor manual bergeser, satu nomor dua sumber, blog untuk teori, angka literatur tanpa `\cite` | BibTeX dan `~\cite`, sumber jurnal/prosiding/datasheet/dokumentasi resmi |
| Isi dan logika | manfaat melampaui keterbatasan, angka teks berbeda dari tabel, metrik yang tidak bisa gagal, kata kerja terbalik ("penurunan dari E ke A"), uji rencana hilang di Bab 4 | aturan 3, ambil angka teks dari tabel, baca ulang kalimat angka |
| Gaya | penjelas gambar mengulang caption, paragraf dobel, "uji coba"/"ujicoba" bergantian, desimal campur | aturan 8, `tulis-tanpa-slop`, `laporan/CLAUDE.md` |

## Daftar periksa sebelum kumpul

Jalankan sendiri dan tulis angka dari keluaran nyata. Perintah yang belum dijalankan ditulis "belum dijalankan", karena angka tebakan lebih buruk daripada angka yang kosong.

```bash
cd laporan/buku-pa && make pdf-bersih && grep -cE "undefined|Overfull|multiply defined" output/main.log
grep -rhoE "\\label\{[^}]+\}" bab/ | sort | uniq -d
grep -rniE "proposal ini|tahap progres|sprint berikutnya|fase berikutnya|semester berikutnya" bab/
grep -rn "PLACEHOLDER-GAMBAR\|PlaceholderData" bab/ | wc -l
grep -nE "HW-[0-9]|Fase [0-9A-G]|\.md|\.py|walkthrough|Task [0-9]" bab/*.tex | grep -vE ":[0-9]+:\s*%"
grep -rn "di atas\|di bawah" bab/ | grep -iE "tabel|gambar"
python3 ../../scripts/cek_tabel.py
```

`make pdf-bersih` dipakai karena `make rebuild` menghapus DOCX di `output/`. Hitungan `main.log` harus 0 dan daftar label ganda harus kosong, karena label ganda membuat `\ref` menunjuk nomor yang salah.

Lalu periksa dengan tangan:
- Setiap Tujuan punya angka di 4.6, vonis di 4.7, dan kalimat di 5.1.
- Angka abstrak sama dengan Bab 4 dan Bab 5.
- Manfaat dan Kesimpulan tidak melampaui Keterbatasan.
- Sistematika Penulisan cocok dengan isi bab yang ada.
- Identitas (nama, NRP, NIP, tahun) cocok dengan sumber resmi.

## Daftar periksa akhir

- Kerangka Bab 4-5 sama dengan aturan 1, 4.6 dan 4.7 berurutan seperti tujuan, judul menurut isi, tanpa "Tujuan N" dan tanpa tabel perubahan dari proposal.
- Setiap target Rencana Pengujian punya angka di 4.6 dengan metrik yang sama dan vonis di 4.7, atau ditulis eksplisit belum dilakukan.
- Bab 3 masih rancangan, Bab 4-5 capaian, tanpa frasa progres di buku.
- Bab 1 dan Bab 5 tanpa gambar dan tabel, Bab 5 tanpa angka baru.
- Semua bab tanpa paragraf pembuka (`cek_tabel.py` N-PEMBUKA-BAB 0), tanpa penunjuk bab, subbab, atau butir di teks tercetak (N-PENUNJUK 0), dan Tujuan Bab 1 berakhir pada daftar.
- Setiap gambar baru berupa placeholder dengan kartu lengkap, dan penjelasnya hanya menyebut elemen kartu.
- Perintah daftar periksa sebelum kumpul sudah dijalankan, dengan angka dari keluaran nyata.
- Pesan akhir hanya mengklaim suntingan pada berkas yang benar-benar diubah.
