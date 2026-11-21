# Temuan ingest-word

Tiap butir pernah menggagalkan satu pekerjaan. Butir 1–5 diamati langsung
pada `wordcraft-cli latex-sync` di buku-pa (21 Nov 2026,
`docs/2026-11-21-pipeline-word-latex.md`); butir 6–9 berasal dari riwayat
`eval.md`; butir 10 dari `laporan/CLAUDE.md` §Build.

1. **`make docx` menimpa DOCX suntingan.** Target itu menulis ke
   `output/main.docx`, berkas yang sama yang disunting user, jadi menjalankannya
   sebelum sync selesai membuang seluruh suntingan. Aturan: DOCX user disalin
   ke `output/suntingan-<YYYYMMDD-HHMM>.docx` sebelum perintah sync apa pun,
   semua sync memakai salinan itu, dan `make docx` baru dijalankan sesudah sync
   selesai ditulis.
2. **Guard hash menolak, dan re-import adalah jalan keluar yang salah.** Bila
   ada `.tex` yang berubah sesudah DOCX dibuat, sync berhenti dengan
   `changed since the import, re-import the project first: <berkas>`. Pesan
   itu menyarankan re-import, padahal re-import (`make docx`) membuang
   suntingan user. Aturan: berhenti, tunjukkan riwayat berkas itu, dan biarkan
   user memilih antara stash lalu sync lalu stash pop, atau menyunting ulang di
   DOCX baru.
3. **Judul ditulis balik dalam huruf kapital tampilan.** Suntingan judul di DOCX
   menjadi `\section{LATAR BELAKANG MASALAH}` dari
   `\section{Latar Belakang}`, karena DOCX menyimpan teks yang sudah
   dikapitalkan gaya judul. Aturan: setiap `\chapter{...}`/`\section{...}`
   yang menjadi kapital semua ditulis ulang dengan kapitalisasi sumber, dan
   perbaikannya disebut di ringkasan dry-run.
4. **Sebagian suntingan tidak pernah sampai ke `.tex`.** Entri Daftar
   Isi/Gambar/Tabel, pustaka, dan teks makro dilaporkan
   `skipped: edit in generated content`; paragraf berkomando (`\makebox`,
   `\hspace`, `\small`, grup `{...}`) dilaporkan
   `skipped: commands the sync cannot rewrite`; rumus, gambar, dan tabel atau
   baris/kolom baru tidak ditulis sama sekali. Tanpa pemindahan manual,
   suntingan itu hilang tanpa tanda. Aturan: tiap butir skipped dipindah ke
   sumbernya dan diff-nya ditunjukkan; suntingan entri daftar ditanyakan ke
   user karena entri itu dibangkitkan dari judul atau caption.
5. **Komentar Word menjadi baris `% KOMENTAR` di bawah paragrafnya.** Baris itu
   tertinggal di `.tex` bila tidak ditindaklanjuti. Aturan: tiap komentar
   ditampilkan bersama rencana tindakannya, dikerjakan, lalu baris
   `% KOMENTAR` dan lanjutannya (`%   ...`) dihapus.
6. **Eval putaran 1 (8/10): `git status` dianggap salah urutan.** Penulis
   menjalankan `git status` sebelum `cp`, padahal pemeriksaan tree bersih
   memang mendahului salinan. Pelajaran: syarat urutan yang benar adalah
   "salinan dibuat sebelum perintah sync apa pun"; `git status` boleh
   mendahuluinya.
7. **Eval putaran 1 (8/10): titik koma diganti koma tanpa konjungsi.** Kalimat
   user menjadi dua klausa yang disambung koma saja. Aturan: titik koma diganti
   titik (menjadi dua kalimat) atau koma + konjungsi ("dan", "sehingga").
8. **Eval putaran 2 (9/10): dua alternatif usulan.** Pesan format memuat dua
   versi baris yang diusulkan dan melewati batas panjang pesan. Aturan: satu
   usulan per temuan.
9. **Eval putaran 3 (9/10): `make sync` ditulis sebelum user menjawab.** Soal
   meminta "tiga perintah pertama", padahal sesudah `make sync-dry` agen
   menunggu konfirmasi sehingga perintah ketiga belum ada; penulis mengisinya
   dengan `make sync` "sesudah konfirmasi". Di luar rubrik: daftar skipped
   tanpa alasannya, cuplikan perubahan lebih dari satu baris, dan keluaran
   `git log`/`git diff` untuk guard tidak disajikan. Pelajaran: prosedur
   berhenti sesudah `make sync-dry`, dan bentuk ringkasan dry-run dibakukan di
   `templat/ringkasan.md`.
10. **`make pdf` menyembunyikan Overfull.** `make pdf` memakai ulang `.aux`,
    `.toc`, `.lof`, dan `.bbl` lama, sehingga Overfull di daftar gambar atau
    tabel bisa tidak muncul di log (21 Nov 2026: progres-pa-1 `make pdf` 0
    Overfull, `make rebuild` 2). Aturan: hitungan `undefined` dan `Overfull`
    untuk bukti diambil dari `make pdf-bersih` (`make rebuild` menghapus `output/` beserta cadangan DOCX).
