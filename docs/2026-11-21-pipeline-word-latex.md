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

Perbaikan di branch WordCraft (opsi A, keputusan user 21 Nov 2026):

| Commit | Perbaikan |
|---|---|
| `f9bea92d` | Deklarasi di dalam lingkungan (`\small` di `center` pembungkus `longtable`) tidak lagi bocor keluar `\end` |
| `b56b69fc` | Ukuran `\small` dan sejenisnya mengikuti kelas 12 pt; kunci baru `[body] baseline_pt`; sel tabel mewarisi ukuran font sekitarnya, tanpa indentasi baris pertama, dengan jarak baris `\setstretch` yang berlaku; kolom `L{3.5cm}` terukur |
| `f2cab4fb` | `\addcontentsline{toc}` menjadi entri Daftar Isi (ABSTRAK, ABSTRACT, DAFTAR ISI); entri daftar memakai jarak baris badan teks |
| `f90eb8af` | `\parbox[c][5cm][c]{...}` menjadi kotak satu sel setinggi 5 cm, bergaris di dalam `\fbox` (placeholder gambar) |
| `3384a6a5` | `\begin{enumerate}[label=\alph*.]` bernomor a. b. c. |

`laporan/wordcraft.toml` memakai `baseline_pt = 21.75` (`\setstretch{1.5}`
pada kelas 12 pt: 1,5 × 14,5 pt).

Hasil `make cek-docx` (WordCraft branch `3384a6a5`):

| Ukuran | buku-pa, 0.18.1 | buku-pa, branch | progres-pa-1, 0.18.1 | progres-pa-1, branch |
|---|---|---|---|---|
| Jumlah halaman | 123 (PDF 139) | 140 (PDF 139) | 111 (PDF 127) | 128 (PDF 127) |
| Selisih awal Bab 1 | −4 | 0 | −6 | 0 |
| Selisih awal Bab 2 | −4 | 0 | −6 | 0 |
| Selisih awal Bab 3 | 0 | 0 | −2 | 0 |
| Selisih awal Bab 4 | −4 | 0 | −6 | 0 |
| Selisih awal Bab 5 | −10 | +2 | −12 | +2 |
| Halaman berawal sama | 6 | 23 | 3 | 26 |

Penyebab yang tersisa:

1. Penempatan float. LaTeX memindahkan tabel dan gambar `[!ht]` ke halaman
   berikutnya dan mengisi sisa halaman dengan teks, sedangkan DOCX meletakkan
   tabel tepat di posisi sumbernya. Selisih di Bab 4 naik turun antara −1 dan
   +2 halaman di sekitar float.
2. Pemotongan baris (Knuth-Plass dan pemenggalan LaTeX terhadap pemotongan
   baris WordCraft). Halaman abstrak terpotong beberapa kata lebih awal, dan
   Daftar Isi DOCX memuat satu entri lebih banyak per halaman.
3. Judul Daftar Isi di PDF tercetak "Daftar Isi" walaupun
   `laporan/shared/preamble.tex` menulis `\renewcommand{\contentsname}{DAFTAR ISI}`.
   Ini perilaku sisi LaTeX (kemungkinan ditimpa babel), bukan konverter.

Butir 1 dan 2 tidak bisa ditutup dengan memperbaiki konverter per bug. Isi per
halaman yang identik membutuhkan pemutus halaman paksa di DOCX pada posisi
halaman PDF (opsi B), keputusan user.

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

1. Opsi B (pemutus halaman paksa dari PDF) untuk sisa pergeseran float dan
   pemotongan baris di Fase 2.
2. Memasang `wordcraft-cli` dari branch ke `~/.cargo/bin` supaya `make docx`
   dan `make sync` memakai perbaikan Fase 2.
