---
name: struktur-pa
description: Wajib dipakai saat menyusun, mengubah, atau meninjau kerangka laporan PA (laporan/buku-pa, progres, proposal) di tingkat bab dan subbab, yaitu menambah atau menghapus section, menulis abstrak, Bab 4 dan Bab 5, memasang gambar atau placeholder gambar, memeriksa benang merah Permasalahan ke Tujuan ke Hasil ke Kesimpulan, dan QA sebelum laporan dikumpulkan. Kerangka beku PENS, register per bab, aturan placeholder gambar, dan anti-pola korpus.
---

# Struktur PA

Asal aturan: bedah enam laporan PA D4 Teknik Informatika PENS (dua buku
full, empat progres 1) pada 10 Okt 2026, kini arsip
`docs/arsip/2026-10-10-pola-laporan-pa/`. Yang dipertahankan di sini hanya
pola yang berlaku untuk laporan PA ini. Angka korpus, contoh halaman, dan
rencana Bab 4 yang sudah dikerjakan tinggal di arsip dan tidak dijadikan
acuan lagi. Kerangka resmi Bab 1–3 ada di `laporan/CLAUDE.md` §Struktur
Resmi Proposal PA. Kerangka Bab 1 buku mengikuti proposal (skill
`buku-ikut-proposal`). Paragraf diatur skill `narasi-pa`, tabel diatur
skill `tabel-pa`.

## Aturan

1. **Kerangka beku Bab 4–5.** 4.1 Parameter Eksperimen, 4.2 Karakteristik
   Data, 4.3 Tempat Ujicoba, 4.4 Waktu Ujicoba, 4.5 Spesifikasi Peralatan
   Ujicoba, 4.6 Hasil Eksperimen, 4.7 Analisis Hasil Eksperimen, lalu 5.1
   Kesimpulan dan 5.2 Saran. Urutan dan judul tidak diubah ("Ujicoba", bukan
   "Uji Coba"). Bab 2, 3, dan 4 dibuka satu paragraf pembuka sebelum subbab
   pertama (Bab 2: masalah dalam ranahnya, teori yang dikupas, penelitian
   terkait untuk menegaskan orisinalitas. Bab 4: objek yang divalidasi,
   daftar aspek sesuai urutan subbab, fokus analisis). Subbab tambahan di
   luar kerangka (mis. 4.8 Dokumentasi) hanya atas permintaan user, dan
   permintaan itu dijawab sebagai opsi, bukan langsung dikerjakan: sebut
   bahwa 4.8 di luar kerangka beku, rekomendasikan foto dokumentasi masuk
   4.5 Spesifikasi Peralatan Ujicoba atau lampiran, lalu tunggu keputusan
   user.

2. **4.6 dan 4.7 berurutan seperti tujuan, dinamai menurut isinya.**
   4.6.1 sampai 4.6.n mengikuti urutan Tujuan di Bab 1, kronologis di
   dalamnya, dan butirnya memakai `\subsubsection` (bernomor huruf). 4.7
   berisi tabel ketercapaian (Tercapai / Sebagian tercapai / Belum
   tercapai, kosakata `tabel-pa` aturan 7), satu subbab analisis per jalur
   yang sama, subbab perbandingan protokol dengan penelitian terkait, lalu
   subbab Keterbatasan dan Status *Proof of Concept* sebagai penutup Bab 4.
   Gaya mengikuti buku AFIB (keputusan user 19 Okt 2026):
   - Judul subbab dan kalimat menyebut **isi** tujuannya ("Jalur
     Preprocessing *Real-Time*", "Analisis Jalur Model TinyML
     *On-Device*"), tidak pernah label bernomor: tanpa "(Tujuan 1)",
     "Ketercapaian Tujuan 2", "Subbab ini menjawab Tujuan 3", "Tujuan
     pertama tercapai sebagian". Kolom tabel ketercapaian berisi nama
     jalur, bukan "Tujuan 1, ...". Diperiksa `cek_tabel.py` (N-TUJUAN).
   - Paragraf pembuka "Bab ini ..." hanya di awal bab. Subbab dan butir
     langsung ke isi, tanpa "Subbab ini memaparkan ..." atau "Butir ini
     bertujuan ..." (skill `narasi-pa` aturan 7, `cek_tabel.py` N-META).
   - Kaitan ke tujuan cukup dinyatakan sekali di pembuka Bab 4 atau 4.6
     ("disusun mengikuti tujuan pada Subbab~\ref{sec:tujuan}") dan di
     pembuka 5.1.
   - Tidak ada tabel atau paragraf "perubahan rancangan dari proposal"
     (proposal lawan realisasi). Bab 3 memuat rancangan akhir, dan alasan
     berbasis ukur muncul wajar di butir hasilnya (ablasi, uji
     kesetaraan).

3. **Benang merah wajib utuh dan dapat ditelusuri.**
   Permasalahan[i] → Tujuan[i] → 2.1 tantangan[i] → 3.1 fitur[i] → Rencana
   Pengujian (metrik + target) → 4.1 parameter → 4.6 angka → 4.7 vonis →
   5.1 kesimpulan[i] → 5.2 sisa. Jumlah butir Permasalahan = Tujuan.
   - Setiap target di Rencana Pengujian muncul di 4.6 sebagai angka dengan
     **metrik yang sama** dan diberi vonis di 4.7. Metrik yang berubah
     dikatakan beserta alasannya.
   - Uji yang direncanakan tetapi tidak dilakukan ditulis eksplisit belum
     dilakukan beserta alasannya, tidak dihilangkan diam-diam.
   - Target tanpa angka ("tinggi", "kecil", "hemat") tidak bisa divonis,
     termasuk saat hasilnya belum diukur. Di tabel ketercapaian statusnya
     ditulis "Belum dapat divonis (target tanpa angka)", lalu perlakuannya
     disebut: beri angka dari rencana, atau tulis "target indikatif" dan
     bandingkan dengan pembanding yang disebut. "Belum tercapai" hanya untuk
     target berangka yang diukur dan tidak terpenuhi.
   - Minimal satu rujukan balik per bab ke tujuan atau permasalahan tanpa
     nomor ("dikaitkan kembali dengan tujuan penelitian pada
     Subbab~\ref{sec:tujuan}").

4. **Register ditentukan bab, bukan jenis dokumen.** Bab 3 tetap register
   rancangan ("dirancang") bahkan di buku full, dan isinya rancangan akhir
   sistem yang diuji di Bab 4, tanpa riwayat revisi internal (rev1, rev2,
   "PCB revisi kedua", siapa yang mendesain). Diperiksa `cek_tabel.py`
   (N-REVISI). Bab 4–5 ditulis sebagai capaian dengan kondisi uji yang
   menempel pada klaim. Buku full tidak memuat frasa progres ("tahap progres
   ini", "fase berikutnya", "sprint berikutnya", "semester berikutnya") dan
   tidak menyebut "proposal ini". Hal yang belum terjadi ditulis
   `\PlaceholderData{...}` atau "belum diukur", tidak pernah dalam bentuk
   lampau.

5. **Sebaran gambar, tabel, dan sitasi.** Bab 1 dan Bab 5 tanpa gambar dan
   tabel. Bab 2 memuat gambar pinjaman ber-"Sumber", Bab 3 rancangan
   sendiri, Bab 4 bukti. Sitasi menumpuk di Bab 1–2. Di Bab 3–5 sitasi
   hanya untuk membenarkan metrik, ambang, atau protokol evaluasi.
   Subbab teori hanya untuk teori yang menopang keputusan rancangan atau
   evaluasi, bukan alat bantu (IDE, editor).

6. **Bab 5 pendek dan tertutup.** Dua sampai empat halaman, tanpa angka
   atau temuan baru, tanpa sitasi. 5.1 menutup per tujuan dengan pola klaim
   lalu bukti angka dari Bab 4. "Seluruh tujuan tercapai" hanya bila tabel
   ketercapaian 4.7 seluruhnya Tercapai. 5.2 buku full berisi arah di luar
   lingkup, 5.2 progres berisi pekerjaan tersisa. Hal yang user putuskan
   tidak dibahas (keamanan transport TLS/MQTTS) tidak muncul di
   Keterbatasan maupun Saran.

7. **Abstrak buku full = abstrak hasil.** Urutan: masalah dan urgensi →
   tujuan → perangkat dan metode → angka hasil utama (metrik model,
   kinerja di perangkat, pipeline) → status dan keterbatasan, paling banyak
   dua kalimat.
   Angka abstrak = angka Bab 4 = angka Bab 5. *Abstract* berbahasa Inggris
   isinya sama. Abstrak proposal dan progres boleh berupa rencana tanpa
   angka.

8. **Setiap gambar dan tabel diapit.** Dirujuk dengan nomor sebelum muncul,
   dijelaskan sesudah muncul oleh paragraf yang dibuka temuan atau
   nomornya, lalu ditutup makna terhadap tujuan. Posisi gambar atau tabel
   tidak disebut dengan "di atas" atau "di bawah" ("Tabel 4.2 di atas");
   kata itu tetap boleh untuk besaran ("di atas ambang"). Pembacaan
   gambar mengikuti alurnya (flowchart per cabang
   keputusan, arsitektur per zona bernomor, panel (a)/(b) disebut di caption
   dan di paragraf). Paragraf penjelas gambar yang hanya mengulang caption
   adalah pelanggaran.

9. **Placeholder gambar.** Claude tidak membuat diagram atau gambar
   ilustrasi (tidak ada Mermaid, TikZ, PlantUML, Graphviz, SVG, draw.io,
   skrip gambar baru, atau gambar AI). Di posisi gambar dipasang placeholder
   berisi kartu spesifikasi, dan user yang menggambar. Caption, `\label`,
   semua `\ref`, paragraf pengantar, dan paragraf penjelas tetap ditulis
   final. Bagian pembacaan gambar di paragraf penjelas hanya menyebut
   elemen, label, dan alur yang ada di kartu, dengan kata yang sama
   persis dengan kartu (kartu "10 RR" → paragraf "10 RR"). Sesudah seluruh
   pembacaan selesai, paragraf ditutup tepat **satu** kalimat makna yang
   boleh mengaitkan gambar ke tujuan atau subbab lain. Kalimat fungsi atau
   alasan ("syarat ini mencegah ...") tidak diselipkan di tengah pembacaan
   dan tidak ditambah sebagai kalimat makna kedua. Plot data
   eksperimen dari pipeline repo (confusion matrix, kurva, grafik latensi)
   bukan ilustrasi. Berkas yang sudah di-export dirujuk langsung. Bila belum
   ada, placeholder menyebut skrip penghasilnya, dan skrip plot baru tidak
   ditulis tanpa diminta. Label `RM1..RM4` tidak boleh muncul di gambar.
   Pencarian: `grep -rn "PLACEHOLDER-GAMBAR" laporan/`.

   Kartu spesifikasi: ID (`fig:{bab}-{slug}` = `\label`), lokasi, jenis
   (arsitektur, flowchart, diagram alir data, state machine, blok diagram,
   skematik, wiring/pinout, mockup, foto perangkat, tangkapan layar,
   ilustrasi konsep, plot data), pesan utama satu kalimat, elemen wajib,
   alur baca, teks di gambar (label persis yang dipakai paragraf), bahan di
   repo (path sumber kebenaran), ukuran (landscape `width=\linewidth` atau
   vertikal `height=0.6\textheight`), sumber bila pinjaman.

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

   Saat gambar sudah ada, blok `\fbox{...}` diganti `\includegraphics` dan
   baris komentar `PLACEHOLDER-GAMBAR` dihapus. Gambar masuk
   `laporan/*/gambar/` lewat `scripts/export_artifacts.sh --laporan`, bukan
   salinan manual.

10. **Khusus PA ini: pembimbing sama dengan buku AFIB (Mulyawan 2026).**
    Format AFIB yang ditiru: Tujuan bertarget, tabel State of the Art
    dengan baris terakhir "Penelitian ini", 4.7 ditutup keterbatasan dan
    status *proof of concept*. Kelemahan AFIB yang dihindari: target tujuan
    yang tidak diukur dengan metrik yang dijanjikan, *confusion matrix*
    yang dideskripsikan kira-kira, hanya akurasi, dan klaim seluruh tujuan
    tercapai tanpa tabel ketercapaian. Angka F1 *inter-patient* PA ini
    tidak boleh disandingkan langsung dengan akurasi AFIB. Bab 4.7 memuat
    tabel protokol evaluasi (pembagian data, unit, kelas, metrik) dan 4.1
    memuat alasan accuracy tidak dipakai (kelas Normal mendominasi). Nada
    "melanjutkan penelitian terdahulu", bukan menjatuhkan. Setiap keunggulan
    yang diklaim atas AFIB (inferensi di perangkat, evaluasi
    *inter-patient*, kesetaraan preprocessing, ketahanan putus koneksi,
    ukuran model) punya angka di Bab 4.

## Anti-pola korpus yang diperiksa

| Kelompok | Kesalahan nyata di korpus | Pencegahan |
|---|---|---|
| Sisa versi lama | "proposal ini" di buku, "tiga bab" padahal lima, rujukan ke tabel yang dihapus, teknologi lama di teori, teori dataset yang tidak dipakai | grep sebelum kumpul (daftar di bawah), hapus elemen bersama semua `\ref`-nya |
| Navigasi | nomor ganda, "Tabel X di atas" padahal muncul sesudahnya, judul subbab tidak cocok isi, salah ketik judul baku | `\label`/`\ref`, pola apit, judul disalin dari aturan 1 |
| Sitasi | nomor manual bergeser, satu nomor dua sumber, blog untuk teori, angka literatur tanpa `\cite` | BibTeX dan `~\cite`, sumber jurnal/prosiding/datasheet/dokumentasi resmi |
| Isi dan logika | manfaat melampaui keterbatasan, angka teks ≠ tabel, metrik yang tidak bisa gagal, kata kerja terbalik ("penurunan dari E ke A"), uji rencana hilang di Bab 4 | aturan 3, angka teks diambil dari tabel, baca ulang kalimat angka |
| Gaya | penjelas gambar mengulang caption, paragraf dobel, "uji coba"/"ujicoba" bergantian, desimal campur | aturan 8, `narasi-pa`, `laporan/CLAUDE.md` |

## Daftar periksa sebelum kumpul

```bash
cd laporan/buku-pa && make pdf && grep -ciE "undefined|multiply defined" output/main.log
grep -rniE "proposal ini|tahap progres|sprint berikutnya|fase berikutnya|semester berikutnya" bab/
grep -rn "PLACEHOLDER-GAMBAR\|PlaceholderData" bab/ | wc -l
grep -nE "HW-[0-9]|Fase [0-9A-G]|\.md|\.py|walkthrough|Task [0-9]" bab/*.tex | grep -vE ":[0-9]+:\s*%"
grep -rn "di atas\|di bawah" bab/ | grep -iE "tabel|gambar"
python3 ../../scripts/cek_tabel.py
```

Lalu periksa dengan tangan: setiap Tujuan punya angka di 4.6, vonis di 4.7,
dan kalimat di 5.1; angka abstrak = Bab 4 = Bab 5; Manfaat dan Kesimpulan
tidak melampaui Keterbatasan; Sistematika Penulisan cocok dengan isi bab
yang ada; identitas (nama, NRP, NIP, tahun) dicek ke sumber resmi.

## Daftar periksa akhir

- [ ] Kerangka Bab 4–5 sama dengan aturan 1, 4.6 dan 4.7 berurutan seperti
      tujuan, judul menurut isi, tanpa "Tujuan N" dan tanpa tabel perubahan
      dari proposal.
- [ ] Setiap target Rencana Pengujian punya angka di 4.6 dengan metrik yang
      sama dan vonis di 4.7, atau ditulis eksplisit belum dilakukan.
- [ ] Bab 3 masih rancangan, Bab 4–5 capaian, tanpa frasa progres di buku.
- [ ] Bab 1 dan Bab 5 tanpa gambar dan tabel, Bab 5 tanpa angka baru.
- [ ] Setiap gambar baru berupa placeholder dengan kartu lengkap, bukan
      gambar buatan Claude, dan penjelasnya hanya menyebut elemen kartu.
- [ ] Perintah pada daftar periksa sebelum kumpul dijalankan, dan angkanya
      ditulis dari keluaran nyata. Yang belum dijalankan ditulis "belum
      dijalankan".
- [ ] Pesan akhir hanya mengklaim suntingan pada berkas yang benar-benar
      diubah. Tanpa wewenang menyunting (`laporan/` read-only), jawaban
      ditulis sebagai usulan, konsisten di seluruh pesan.
