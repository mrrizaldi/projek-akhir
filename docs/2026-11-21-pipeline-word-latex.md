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

Target (keputusan user 21 Nov 2026): PDF dan DOCX dibuka berdampingan berisi
sama per halaman, dengan font, margin, dan ukuran kertas sama. Diperiksa
`make cek-docx` (`scripts/cek_docx.py`, cara pakai di `scripts/README.md`).
Penyuntingan repo `~/dev/wordcraft` diizinkan user, dikerjakan di branch lokal
`fix/latex-env-scopes-declarations` tanpa push (aturan repo itu: `main` hanya
lewat PR, publikasi ditanyakan dulu).

Penyebab yang sudah ditemukan dan diperbaiki:

1. Deklarasi ukuran di dalam lingkungan `center`, `flushleft`, `flushright`,
   `quote`, dan daftar bocor keluar `\end`. `\small` pembungkus `longtable`
   Tabel 3.3 membuat seluruh paragraf sesudahnya 9 pt. Perbaikan di
   `crates/formats/src/latex/parser.rs` `environment()`, commit `f9bea92d`.

Hasil `make cek-docx` buku-pa:

| Ukuran | wordcraft-cli 0.18.1 | branch `f9bea92d` |
|---|---|---|
| Jumlah halaman (PDF 139) | 123 | 144 |
| Selisih awal Bab 1 | −4 | −4 |
| Selisih awal Bab 3 | 0 | 0 |
| Selisih awal Bab 4 | −4 | 0 |
| Selisih awal Bab 5 | −10 | +8 |
| Halaman berawal sama | 6 | 7 |

Penyebab yang tersisa (teramati, belum diperbaiki):

1. Daftar Isi, Daftar Gambar, dan Daftar Tabel. PDF 8 halaman, DOCX 4 halaman.
   Judul PDF "Daftar Isi" (huruf awal kapital), DOCX "DAFTAR ISI". Entri ABSTRAK
   ada di Daftar Isi PDF dan tidak ada di DOCX.
2. Abstrak terpotong di titik lain (halaman 4 dan 6).
3. Bab 4 di DOCX 8 halaman lebih panjang (penempatan tabel dan gambar).
4. Jarak baris badan teks 21 pt di DOCX dan 22 pt di PDF (`\setstretch{1.5}`
   pada 12 pt = 21,75 pt, sedangkan 1,5 baris Word untuk Times New Roman 12 pt
   sekitar 20,7 pt).
5. Ukuran `\small` dan `\footnotesize` di `crates/formats/src/latex/units.rs`
   memakai kelas 10 pt (9 dan 8 pt), padahal kelas 12 pt memakai 10,95 dan
   10 pt.
6. Pemotongan baris berbeda (Knuth-Plass dan pemenggalan LaTeX terhadap
   pemotongan baris WordCraft). Penyebab ini tidak hilang dengan memperbaiki
   butir 1 sampai 5. Isi per halaman yang identik membutuhkan pemutus halaman
   paksa di DOCX pada posisi halaman PDF LaTeX (keputusan desain, menunggu
   user).

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

1. Cara mencapai isi per halaman identik (Fase 2 butir sisa 6).
