# Pipeline sunting di Word, ingest ke LaTeX

Tujuan: LaTeX tetap sumber kebenaran, penulis menyunting bebas di WordCraft
(`output/main.docx`), lalu perubahan di-ingest ke `.tex` lewat skill dengan
konfirmasi, tanpa penanda `% MANUAL` di `.tex`.

## Kondisi awal (diukur 21 Nov 2026, buku-pa)

Alur sudah tersedia di `laporan/shared/Makefile.inc`: `make docx`
(`wordcraft-cli convert`, layout dari `laporan/wordcraft.toml`), `make sync-dry`
(diff tanpa menulis), dan `make sync` (tulis balik paragraf). wordcraft-cli
0.18.1, sumber di `~/dev/wordcraft` (dokumentasi `docs/latex.md`).

Jumlah halaman awal bab, hasil `make pdf` dan `make docx` lalu DOCX dirender
ulang ke PDF lewat `wordcraft-cli convert`:

| Bagian | PDF LaTeX | DOCX | Selisih |
|---|---|---|---|
| Total | 139 | 123 | −16 |
| Bagian depan (sebelum Bab 1) | 14 | 10 | −4 |
| Bab 2 | 24 | 28 | +4 |
| Bab 3 | 36 | 32 | −4 |
| Bab 4 | 48 | 42 | −6 |
| Bab 5 | 6 | 3 | −3 |

Batasan konverter yang tercatat di `~/dev/wordcraft/docs/latex.md` §Limits dan
relevan: pemutusan halaman berbeda dari pdfLaTeX, gambar PDF/SVG/EPS tidak
dirender (jadi `[Picture: nama]`), `\midrule` di badan tabel tidak digambar,
`\ifx` tidak ditangani, `\vspace{\baselineskip}` dihitung 0. `latex-sync` hanya
menulis paragraf. Tabel, gambar, persamaan, judul, dan baris tabel baru
dilaporkan sebagai skipped.

## Fase 1: hapus penanda `% MANUAL`

1. `laporan/wordcraft.toml` `[sync] marker = ""` (dokumentasi WordCraft: string
   kosong = tanpa penanda). `comments` dan `style_warnings` tetap.
2. Hapus §Penanda `% MANUAL` dari `laporan/CLAUDE.md`. Aturan `% KOMENTAR`
   (kerjakan lalu hapus barisnya) dan daftar bagian yang tidak ditulis sync
   dipindah ke skill ingest.
3. Saat ini 0 penanda di `laporan/**/*.tex`, jadi tidak ada pembersihan berkas.

Verifikasi: sunting satu paragraf di DOCX secara headless (`wordcraft-cli run`),
`make sync-dry` menampilkan diff tanpa baris `% MANUAL`.

## Fase 2: fidelity DOCX terhadap PDF

Target (usulan, menunggu keputusan user): ukuran kertas, margin, font, dan gaya
judul identik, halaman awal tiap bab berselisih paling banyak 1 halaman. Sama
persis per baris tidak menjadi target karena mesin pemutus baris dan penempatan
float LaTeX dan Word berbeda.

1. Pemeriksa: target `make cek-docx` di `laporan/shared/Makefile.inc` yang
   mencetak tabel halaman awal bab PDF dan DOCX berdampingan beserta selisihnya
   (pola pengukuran di atas: `wordcraft-cli convert` DOCX ke PDF, `pdftotext`
   per halaman).
2. Telusuri penyebab per bagian, mulai dari selisih terbesar per halaman:
   Bab 5 (6 jadi 3) dan bagian depan (14 jadi 10). Calon yang diperiksa dulu:
   gambar PDF yang tidak dirender, `\clearpage`/`\cleardoublepage` dan
   `odd_page`, spasi vertikal, float tabel.
3. Perbaikan di `laporan/wordcraft.toml` bila penyebabnya konfigurasi. Bila
   penyebabnya konverter, perbaikan di repo `~/dev/wordcraft` (repo terpisah,
   izin user dulu) atau dicatat sebagai keterbatasan.

Verifikasi: `make cek-docx` memenuhi target untuk buku-pa dan progres-pa-1.

## Fase 3: skill `ingest-word`

Berkas `.claude/skills/ingest-word/SKILL.md`. Alur:

1. Cek `git status laporan/`. Ada perubahan `.tex` yang belum di-commit →
   berhenti dan lapor, supaya hasil ingest bisa di-revert utuh.
2. `make sync-dry` → ringkasan per bab ke user: paragraf berubah (sebelum dan
   sesudah singkat), komentar Word, dan daftar skipped (tabel, judul, rumus,
   gambar).
3. Konfirmasi user → `make sync`.
4. Bagian skipped dipindah manual ke LaTeX sesuai `tabel-pa`, `struktur-pa`,
   dan `laporan/CLAUDE.md`. Diff ditunjukkan ke user.
5. Baris `% KOMENTAR` dikerjakan lalu dihapus.
6. `python3 scripts/cek_tabel.py bab/*.tex` → daftar pelanggaran format di
   paragraf hasil ingest (titik dua, titik koma, em dash, istilah belum miring,
   desimal titik, label internal). Konfirmasi user → dirapikan. Isi kalimat
   penulis tidak ditulis ulang, hanya format.
7. `make pdf` (0 undefined, 0 overfull) dan `make docx`, lalu commit dengan
   bukti (keluaran sync, cek_tabel, ringkasan log LaTeX).

Eval (Aturan keras 8, model berbeda, maksimal 3 putaran), soal berjawaban pasti:
sync dijalankan tanpa konfirmasi, tree kotor tidak dihentikan, tabel skipped
tidak dipindah, kalimat penulis ditulis ulang saat merapikan format, komentar
Word dibiarkan.

Verifikasi ujung ke ujung: `make docx`, sunting headless satu paragraf, satu
sel tabel, satu judul, dan satu komentar, jalankan alur skill, periksa diff
`.tex` dan `make pdf`.

## Sesudahnya

Skill penulisan tanpa pola tulisan AI: `docs/2026-11-21-skill-anti-slop.md`.
Skill ingest langkah 6 nantinya ikut memakai pemeriksaan dari sana.

## Keputusan yang menunggu user

1. Target fidelity di Fase 2.
2. Izin menyunting repo `~/dev/wordcraft` bila penyebabnya di konverter.
