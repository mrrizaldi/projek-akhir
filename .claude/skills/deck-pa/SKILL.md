---
name: deck-pa
description: Membuat, merombak, atau meninjau deck presentasi Proyek Akhir (PA) dalam format PPTX, misalnya slide seminar progres, sidang PA, atau slide bimbingan. Pakai saat user mengetik "bikin deck sidang", "buat slide seminar progres", "rombak slide PA", "cek deck presentasi", "make the PA slides", atau "review my defense deck". Isi deck diturunkan dari laporan/buku-pa, angka disalin dari buku (tidak dikarang), label internal repo tidak tampil di slide, gambar ilustrasi berupa kotak placeholder untuk digambar user, dan setiap slide dirender lalu dilihat sebelum diserahkan. Teknis berkas PPTX mengikuti skill document-skills:pptx.
---

# Deck presentasi PA

Skill ini mengatur isi deck. Cara menulis berkas `.pptx` (API `pptxgenjs`, jebakan warna hex, layout, bullet) mengikuti skill `document-skills:pptx`; muat keduanya.

## Alat

- `pptxgenjs` terpasang di prefix user, bukan global sistem. Jalankan skrip deck dengan `NODE_PATH=~/.local/lib/node_modules node deck.js`; tanpa `NODE_PATH`, `require('pptxgenjs')` gagal. Bila hilang, pasang dengan `npm i -g --prefix ~/.local pptxgenjs`, bukan `sudo npm i -g`.
- Render memakai `deckcraft-cli` dan `pdftoppm`, keduanya sudah ada di sistem.
- `scripts/office/validate.py` milik skill `pptx` butuh `defusedxml`, yang belum terpasang. Memasangnya berarti dependency baru, jadi tanya user dulu. Tanpa itu, bukti berkas sehat adalah render PDF sukses dan semua slide terlihat benar.

## Lokasi dan berkas

Satu deck satu folder `presentasi/YYYY-MM-DD-<acara>/`, berisi `deck.js` (sumber, di-commit) dan `output/` (`.pptx`, `.pdf`, `.png`; sudah di-ignore lewat `presentasi/*/output/`). Pola ini mengikuti folder yang sudah ada di `presentasi/`.

`deck.js` adalah kode, jadi ditulis tanpa komentar (skill `tanpa-komentar-kode`). Catatan pembicara ditulis lewat `addNotes`, bukan komentar, supaya penjelasan tetap ada tanpa melanggar aturan kode.

## Isi diturunkan dari buku

Sumber tunggal isi deck adalah `laporan/buku-pa/bab/*.tex`, supaya deck dan buku tidak saling bertentangan.

- Permasalahan dan Tujuan di deck sama dengan 3 butir di Bab 1 buku. Boleh dipadatkan, tetapi jumlah dan maknanya tetap.
- Kesimpulan di deck menjawab 3 permasalahan itu sesuai Bab 5, satu butir per permasalahan.
- Deck tidak memuat klaim yang tidak ada di buku, karena penguji membandingkan keduanya.
- Lingkup yang sudah diputuskan user berlaku: subjek uji anonim (S01, S02, ...), tempat uji laboratorium, TLS dan keamanan transport tidak dibahas sama sekali.

## Angka

Salin setiap angka dari buku, atau dari berkas hasil yang dirujuk buku (mis. `model/artifacts/metrics/*.csv`). Angka karangan di depan penguji tidak bisa dipertahankan.

- Format Indonesia: desimal koma (0,9123), ribuan titik (41.801).
- Angka yang di buku berupa `\PlaceholderData{X}` tampil di slide sebagai teks `[PLACEHOLDER DATA: X]` dengan isi X yang sama. Jangan menggantinya dengan angka perkiraan, dan jangan memakai angka uji coba sebelum 13 Okt 2026, karena itu bukan data resmi.
- Daftar placeholder di buku: `grep -rn PlaceholderData laporan/buku-pa/bab`.

## Tanpa label internal

Teks slide dan catatan pembicara yang dibacakan tidak memuat label kerja internal repo, karena penonton tidak mengenalnya: HW-n, Fase n atau Fase A–G, Task n, T-n/K-n, path berkas, nama skrip, nama env atau knob (`PA_*`, env PlatformIO), kata "walkthrough", dan label `RM1..RM4`. Sebut isinya dengan istilah umum.

Nama berkas gambar (mis. `fase7_confusion_int8.png`) hanya muncul di `deck.js`, tidak di slide.

## Gambar

- Plot data hasil pipeline yang sudah di-export ke `laporan/buku-pa/gambar/` dipasang langsung dari sana dengan `addImage`, rasio asli dipertahankan.
- Gambar ilustrasi (arsitektur, blok diagram, flowchart, state machine, wiring, foto perangkat, mockup) tidak digambar Claude, termasuk dengan bentuk dan panah `pptxgenjs` (beberapa `addShape`, garis, kotak bersambung), karena user yang menggambar.
- Di posisi ilustrasi pasang tepat satu kotak bergaris putus (`addText` dengan `line: { dashType: 'dash' }`, atau satu `addShape` persegi) berisi `[PLACEHOLDER GAMBAR] <jenis>: <ringkasan satu baris>`.
- Kartu spesifikasi (jenis, pesan utama, elemen wajib, alur baca, teks di gambar, bahan di repo) ditulis di catatan pembicara slide itu, di bawah baris `KARTU GAMBAR (tidak dibacakan)`. Hanya kartu ini yang boleh memuat path repo; bagian catatan yang dibacakan tetap bebas label internal.
- Bila buku sudah punya placeholder untuk gambar yang sama, salin kartunya dari komentar `PLACEHOLDER-GAMBAR` di `.tex`.

## Struktur slide

- Satu slide satu pesan. Judul berupa kalimat temuan atau pertanyaan (mis. "Model INT8 mempertahankan recall aritmia"), bukan label ("Hasil"), supaya penonton tahu kesimpulan slide sebelum membaca badan.
- Badan slide paling banyak 6 butir, tiap butir paling banyak 12 kata.
- Tabel paling banyak 5 baris data dan 4 kolom. Tabel buku yang lebih besar dipangkas ke baris yang menjawab judul slide, sisanya disebut "lengkap di buku, Tabel X" dengan nomor tabel yang benar.
- Alur baku: Judul (nama, NRP, pembimbing), Latar belakang, Permasalahan, Tujuan, Rancangan sistem, Metode pengujian, Hasil (urut per tujuan), Kesimpulan, Saran, penutup. Slide di luar alur ditambahkan hanya atas permintaan user.

## Keputusan milik user

Templat kampus, warna, dan durasi presentasi belum pernah diputuskan di repo. Bila tugas membutuhkannya dan user belum menyebutnya, tanyakan sekali dengan opsi dan rekomendasi sebelum membangun, dan jangan memakai templat bawaan diam-diam.

Jumlah slide tidak ditanyakan terpisah: turunkan dari durasi (kira-kira satu slide per menit) dan sebut di pesan sebagai asumsi yang bisa diubah user. Hal yang sudah tercatat di repo atau menunggu data resmi tidak ditanyakan, mengikuti skill `buku-ikut-proposal`.

## Verifikasi sebelum diserahkan

Jalankan sendiri, karena user bukan verifikator.

1. `cd presentasi/<folder> && NODE_PATH=~/.local/lib/node_modules node deck.js`
2. `deckcraft-cli convert output/deck.pptx output/deck.pdf`
3. `pdftoppm -png -r 60 output/deck.pdf output/slide`
4. Buka setiap `output/slide-*.png` dengan Read. Periksa teks tidak keluar bingkai atau terpotong, tidak ada tumpang tindih, gambar tidak gepeng, placeholder terbaca.
5. `pdftotext output/deck.pdf output/deck.txt`, lalu
   `grep -nE "HW-[0-9]|Fase [0-9A-G]|PA_[A-Z]|walkthrough|RM[1-4]|\.(py|png|csv|tex|js)\b|(model|firmware|laporan|scripts|dashboard)/" output/deck.txt`
   harus kosong.

Laporan akhir menyebut jumlah slide dari keluaran nyata (jumlah `slide-*.png`), hasil langkah 4 dan 5, serta yang tidak terverifikasi: tampilan font di PowerPoint asli, animasi, durasi bicara. Perintah yang belum dijalankan ditulis "belum dijalankan", dan klaim yang bergantung padanya ("deck selesai dibangun", "N slide", "label internal bersih") ditulis belum terbukti; bila angkanya belum diamati, tulis `[N]`.
