# Perilaku `latex-sync` dan pemindahan manual

Perilaku di bawah diamati langsung pada buku-pa, 21 Nov 2026.

## Perilaku sync

| Suntingan user di DOCX | Hasil sync |
|---|---|
| Paragraf, sel tabel, caption | Ditulis ke `.tex`, `\label` di sebelahnya tetap |
| Judul bab/subbab (`\chapter`, `\section`) | Ditulis dalam huruf kapital tampilan (`\section{Latar Belakang}` → `\section{LATAR BELAKANG MASALAH}`) |
| Entri Daftar Isi/Gambar/Tabel, pustaka, teks makro | `skipped: edit in generated content` |
| Paragraf berisi `\makebox`, `\hspace`, `\small`, grup `{...}` | `skipped: commands the sync cannot rewrite` |
| Rumus, gambar, tabel/baris/kolom baru | Tidak ditulis |
| Komentar Word | Baris `% KOMENTAR [nama, tanggal]: ...` di bawah paragrafnya |

Guard: bila ada `.tex` yang berubah sesudah DOCX dibuat, sync menolak dengan
`changed since the import, re-import the project first: <berkas>`.

## Memindah butir yang dilewati sync

Untuk tiap butir `skipped` (temuan #4):

| Jenis butir | Tindakan |
|---|---|
| Suntingan teks makro atau paragraf berkomando | Sunting baris sumbernya di `.tex` |
| Suntingan entri Daftar Isi/Gambar/Tabel | Tanyakan apakah judul atau caption sumbernya yang diubah, karena entri itu dibangkitkan |
| Rumus, gambar, tabel baru | Tulis di LaTeX mengikuti skill `tabel-pa` dan `laporan/CLAUDE.md` |

Tunjukkan diff hasil pemindahan:

```bash
git diff -- bab/
```

## Komentar Word

Tiap `% KOMENTAR` ditampilkan ke user bersama rencana tindakannya (temuan #5).
Sesudah dikerjakan, baris `% KOMENTAR` dan lanjutannya (`%   ...`) dihapus.
Sisa yang belum dikerjakan:

```bash
grep -n "% KOMENTAR" bab/*.tex
```

Diharapkan: tidak ada keluaran.

## Binary WordCraft

Baca bila `wordcraft-cli` berperilaku lain dari tabel di atas.

`~/.cargo/bin/wordcraft-cli` adalah build branch lokal WordCraft
`fix/latex-env-scopes-declarations` (perbaikan ukuran kelas, sel tabel,
`\parbox`, Daftar Isi), dipasang 21 Nov 2026. Versi 0.18.1 dicadangkan di
`~/.cargo/bin/wordcraft-cli-0.18.1`. Target make memakai `wordcraft-cli` di
PATH, tanpa `WORDCRAFT=`.
