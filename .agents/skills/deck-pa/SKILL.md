---
name: deck-pa
description: Wajib dipakai saat membuat, merombak, atau meninjau deck presentasi PA (seminar progres, sidang PA, slide bimbingan) dalam format PPTX. Isi deck diturunkan dari laporan/buku-pa, angka tidak dikarang, label internal repo tidak tampil, gambar ilustrasi berupa placeholder untuk digambar user, dan setiap slide dirender lalu dilihat sebelum diserahkan. Teknis berkas PPTX mengikuti skill pptx (document-skills:pptx).
---

# Deck presentasi PA

Skill ini mengatur ISI deck. Cara menulis berkas `.pptx` (API `pptxgenjs`,
jebakan warna hex, layout, bullet) mengikuti skill `pptx`
(`document-skills:pptx`). Muat keduanya.

## Alat

- `pptxgenjs` 4.0.1 terpasang di prefix user (bukan global sistem). Jalankan
  skrip deck dengan
  `NODE_PATH=~/.local/lib/node_modules node deck.js`. Tanpa `NODE_PATH`,
  `require('pptxgenjs')` gagal. Bila hilang: `npm i -g --prefix ~/.local pptxgenjs`
  (bukan `sudo npm i -g`).
- Render: `deckcraft-cli` (paket .deb DeckCraft) dan `pdftoppm` sudah ada di sistem.
- `scripts/office/validate.py` milik skill `pptx` butuh `defusedxml` yang
  belum terpasang. Memasangnya = dependency baru → tanya user dulu. Tanpa itu,
  bukti berkas sehat = render PDF sukses + semua slide terlihat benar.

## Aturan

1. **Lokasi.** Satu deck satu folder `presentasi/YYYY-MM-DD-<acara>/`
   (contoh `presentasi/2026-11-20-sidang-pa/`): `deck.js` (sumber, di-commit)
   dan `output/` (berisi `.pptx`, `.pdf`, `.png`; folder `presentasi/*/output/`
   di-ignore). `deck.js` adalah kode: tanpa komentar (skill
   `tanpa-komentar-kode`); catatan pembicara ditulis lewat `addNotes`, bukan
   komentar.
2. **Isi diturunkan dari buku.** Sumber tunggal = `laporan/buku-pa/bab/*.tex`.
   Permasalahan dan Tujuan di deck = 3 butir yang sama dengan Bab 1 buku
   (boleh dipadatkan, jumlah dan maknanya tetap). Kesimpulan di deck menjawab
   3 permasalahan itu sesuai Bab 5. Deck tidak memuat klaim yang tidak ada di
   buku.
3. **Angka tidak dikarang.** Setiap angka di slide disalin dari buku (atau
   dari berkas hasil yang dirujuk buku, mis. `model/artifacts/metrics/*.csv`),
   dengan format Indonesia: desimal koma (0,9123), ribuan titik (41.801).
   Angka yang di buku berupa `\PlaceholderData{X}` tampil di slide sebagai
   teks `[PLACEHOLDER DATA: X]` dengan isi X yang sama, bukan angka perkiraan,
   bukan angka uji coba sebelum 13 Okt 2026. Pencarian:
   `grep -rn PlaceholderData laporan/buku-pa/bab`.
4. **Tanpa label internal.** Teks slide dan catatan pembicara yang dibacakan
   tidak memuat: HW-n, Fase n / Fase A–G, Task n, T-n/K-n, path berkas, nama
   skrip, nama env/knob (`PA_*`, env PlatformIO), kata "walkthrough", dan
   label `RM1..RM4`. Nama berkas gambar (mis. `fase7_confusion_int8.png`)
   hanya muncul di `deck.js`, tidak di slide. Lingkup yang sudah diputuskan
   user berlaku: subjek uji anonim (S01, S02, ...), tempat uji laboratorium,
   TLS/keamanan transport tidak dibahas sama sekali.
5. **Gambar.** Plot data hasil pipeline yang sudah di-export ke
   `laporan/buku-pa/gambar/` dipasang langsung dari sana (`addImage`, rasio
   asli dipertahankan). Gambar ilustrasi (arsitektur, blok diagram, flowchart,
   state machine, wiring, foto perangkat, mockup) TIDAK digambar Codex,
   termasuk dengan bentuk dan panah `pptxgenjs` (beberapa `addShape`, garis,
   kotak bersambung). Di posisinya dipasang tepat SATU kotak bergaris putus
   (`addText` dengan `line: { dashType: 'dash' }`, atau satu `addShape`
   persegi) berisi `[PLACEHOLDER GAMBAR] <jenis>: <ringkasan satu baris>`.
   Kartu spesifikasinya (jenis, pesan utama, elemen wajib, alur baca, teks di
   gambar, bahan di repo) ditulis di catatan pembicara slide itu, di bawah
   baris `KARTU GAMBAR (tidak dibacakan)`. Hanya kartu ini yang boleh memuat
   path repo; bagian catatan yang dibacakan tetap tunduk aturan 4. Bila buku
   sudah punya placeholder untuk gambar yang sama, kartunya disalin dari
   komentar `PLACEHOLDER-GAMBAR` di `.tex`.
6. **Satu slide satu pesan.** Judul slide berupa kalimat temuan atau
   pertanyaan slide (mis. "Model INT8 mempertahankan recall aritmia"), bukan
   label ("Hasil"). Badan slide paling banyak 6 butir, tiap butir paling
   banyak 12 kata. Tabel paling banyak 5 baris data × 4 kolom; tabel buku
   yang lebih besar dipangkas ke baris yang menjawab judul slide, sisanya
   disebut "lengkap di buku, Tabel X".
7. **Alur baku.** Judul (nama, NRP, pembimbing) → Latar belakang →
   Permasalahan → Tujuan → Rancangan sistem → Metode pengujian → Hasil (urut
   per tujuan) → Kesimpulan (satu butir per permasalahan) → Saran → penutup.
   Slide di luar alur ini ditambahkan hanya atas permintaan user.
8. **Keputusan milik user ditanyakan sekali.** Templat kampus, warna, dan
   durasi presentasi belum pernah diputuskan di repo. Bila tugas
   membutuhkannya dan user belum menyebutnya, tanyakan sekali dengan opsi +
   rekomendasi sebelum membangun. Jumlah slide tidak ditanyakan terpisah:
   diturunkan dari durasi (kira-kira satu slide per menit) dan disebut di
   pesan sebagai asumsi yang bisa diubah user. Hal yang sudah tercatat di repo atau menunggu data
   resmi tidak ditanyakan (aturan 4 skill `buku-ikut-proposal`).
9. **Verifikasi sendiri sebelum diserahkan.**
   1. `cd presentasi/<folder> && NODE_PATH=~/.local/lib/node_modules node deck.js`
   2. `deckcraft-cli convert output/deck.pptx output/deck.pdf`
   3. `pdftoppm -png -r 60 output/deck.pdf output/slide`
   4. Buka SETIAP `output/slide-*.png` dengan Read dan periksa: teks tidak
      keluar bingkai atau terpotong, tidak ada tumpang tindih, gambar tidak
      gepeng, placeholder terbaca.
   5. `pdftotext output/deck.pdf output/deck.txt`, lalu
      `grep -nE "HW-[0-9]|Fase [0-9A-G]|PA_[A-Z]|walkthrough|RM[1-4]|\.(py|png|csv|tex|js)\b|(model|firmware|laporan|scripts|dashboard)/" output/deck.txt`
      → kosong.
   Laporan akhir ke user menyebut jumlah slide dari keluaran nyata (jumlah
   `slide-*.png`), hasil langkah 4–5, dan yang TIDAK terverifikasi (tampilan font di PowerPoint
   asli, animasi, durasi bicara). Perintah yang tidak dijalankan ditulis
   "belum dijalankan", dan klaim yang bergantung padanya ("deck selesai
   dibangun", "N slide", "label internal bersih") ikut ditulis belum
   terbukti.

## Daftar periksa akhir

- [ ] Permasalahan dan Tujuan 3 butir, sama maknanya dengan Bab 1 buku.
- [ ] Tiap angka ada di buku; `\PlaceholderData` tampil sebagai
      `[PLACEHOLDER DATA: ...]`; format desimal koma.
- [ ] Tidak ada diagram dari `addShape`/panah; ilustrasi = kotak placeholder
      + kartu di catatan pembicara.
- [ ] Judul slide = kalimat temuan; ≤ 6 butir × ≤ 12 kata; tabel ≤ 5 × 4.
- [ ] Semua slide dirender dan dilihat; grep label internal kosong.
- [ ] `deck.js` tanpa komentar; `output/` tidak di-commit.
