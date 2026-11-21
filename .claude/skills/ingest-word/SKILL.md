---
name: ingest-word
description: Wajib dipakai saat user selesai menyunting laporan PA di WordCraft atau Word (output/main.docx buku-pa atau progres-pa-1) dan meminta perubahannya dimasukkan ke LaTeX ("ingest", "sync balik", "masukin suntingan Word ke tex"). Suntingan dicadangkan dulu, dry-run diringkas dan dikonfirmasi user sebelum ditulis, bagian yang dilewati sync dipindah manual, format dirapikan hanya sesudah dikonfirmasi, lalu PDF dibangun ulang dan di-commit dengan bukti.
---

# Ingest suntingan Word ke LaTeX

Asal aturan: pipeline 21 Nov 2026 (`docs/2026-11-21-pipeline-word-latex.md`).
LaTeX adalah sumber kebenaran, user menyunting bebas di DOCX, lalu perubahan
ditulis balik oleh `wordcraft-cli latex-sync` (`make sync`). Perilaku sync di
bawah diamati langsung pada buku-pa, 21 Nov 2026.

## Perilaku sync yang harus diingat

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

## Aturan

1. **Cadangkan dulu, jangan pernah menimpa DOCX suntingan.** `make docx`
   menulis ke `output/main.docx`, berkas yang sama yang disunting user. Langkah
   pertama selalu menyalin DOCX user ke `output/suntingan-<YYYYMMDD-HHMM>.docx`
   dan semua sync memakai salinan itu (`make sync-dry DOCX=...`). `make docx`
   baru boleh dijalankan sesudah sync selesai ditulis.
2. **Guard menolak → berhenti, jangan re-import.** Re-import (`make docx`)
   membuang suntingan user. Laporkan berkas yang disebut guard dan
   `git log`/`git diff` berkas itu sejak DOCX dibuat, lalu beri user opsi:
   (a) `git stash` perubahan `.tex` itu, sync, lalu `git stash pop` dan
   selesaikan konflik; (b) user menyunting ulang di DOCX baru. User yang
   memilih.
3. **Tree `.tex` harus bersih.** `git status --short laporan/<projek>` tidak
   boleh menunjukkan `.tex` berubah sebelum ingest, supaya commit ingest hanya
   berisi suntingan user dan bisa di-revert utuh. Ada perubahan → berhenti dan
   tanyakan (commit dulu atau stash).
4. **Dry-run diringkas, konfirmasi sebelum menulis.** Jalankan
   `make sync-dry DOCX=<salinan>`, lalu sajikan ke user per berkas: jumlah
   `changed/inserted/deleted`, cuplikan sebelum → sesudah tiap perubahan
   (paling banyak satu baris per perubahan), daftar `skipped` beserta
   alasannya, dan jumlah komentar Word. Jangan menjalankan `make sync`
   sebelum user mengonfirmasi.
5. **Judul dikembalikan ke huruf sumber.** Setiap baris `\chapter{...}`,
   `\section{...}` di diff yang menjadi huruf kapital semua ditulis ulang
   dengan kapitalisasi sumber (huruf awal kapital per kata, seperti judul lain
   di berkas itu), karena gaya judul sudah mengapitalkan tampilannya. Sebut
   perbaikan ini di ringkasan dry-run.
6. **Yang dilewati sync dipindah manual.** Untuk tiap butir `skipped`:
   suntingan teks makro atau paragraf berkomando → sunting baris sumbernya di
   `.tex`; suntingan entri Daftar Isi/Gambar/Tabel → tanyakan apakah judul
   atau caption sumbernya yang diubah, karena entri itu dibangkitkan; rumus,
   gambar, tabel baru → tulis di LaTeX mengikuti `tabel-pa` dan
   `laporan/CLAUDE.md`. Tunjukkan diff hasil pemindahan.
7. **Komentar Word dikerjakan, lalu barisnya dihapus.** Tiap
   `% KOMENTAR` ditampilkan ke user bersama rencana tindakannya; sesudah
   dikerjakan, baris `% KOMENTAR` dan lanjutannya (`%   ...`) dihapus.
8. **Format dirapikan sesudah dikonfirmasi, kalimat tidak ditulis ulang.**
   Jalankan `python3 ../../scripts/cek_tabel.py bab/*.tex` dari folder projek
   dan ambil temuan yang jatuh di baris hasil ingest. Sajikan daftar
   perbaikan format (titik dua, titik koma, em dash di paragraf, istilah
   teknis belum miring, desimal titik, label internal). Titik koma diganti
   titik (menjadi dua kalimat) atau koma + konjungsi ("dan", "sehingga");
   koma saja tanpa konjungsi tidak boleh. Satu usulan per temuan, bukan
   beberapa alternatif. Terapkan sesudah user
   mengonfirmasi. Pilihan kata, urutan, dan isi kalimat user tidak diubah.
   Pada setiap `.tex` yang ditulis sync, jalankan juga dari folder projek:
   ```bash
   python3 ../../scripts/cek_slop.py --ringkas bab/<berkas>.tex
   ```
   Temuan `galat` diajukan ke user sebagai usulan format, satu usulan per
   temuan; kalimat penulis tidak ditulis ulang tanpa konfirmasi.
9. **Bangun ulang dan commit dengan bukti.** `make pdf` harus 0 `undefined`
   dan 0 `Overfull`; lalu `make docx`. Commit memuat ringkasan sync
   (`changed/inserted/deleted` per berkas), butir skipped yang dipindah,
   keluaran `cek_tabel` sesudah perbaikan, dan baris `undefined`/`Overfull`
   dari log. Salinan `output/suntingan-*.docx` tidak di-commit (`output/`
   diabaikan git).

## Binary WordCraft

`~/.cargo/bin/wordcraft-cli` adalah build branch lokal WordCraft
`fix/latex-env-scopes-declarations` (perbaikan ukuran kelas, sel tabel,
`\parbox`, Daftar Isi), dipasang 21 Nov 2026. Versi 0.18.1 dicadangkan di
`~/.cargo/bin/wordcraft-cli-0.18.1`. Target make memakai `wordcraft-cli` di
PATH, tanpa `WORDCRAFT=`.

## Prosedur

```bash
cd laporan/buku-pa
git status --short .
cp output/main.docx output/suntingan-$(date +%Y%m%d-%H%M).docx
make sync-dry DOCX=output/suntingan-<stempel>.docx
make sync DOCX=output/suntingan-<stempel>.docx
python3 ../../scripts/cek_tabel.py bab/*.tex
make pdf
grep -cE "undefined|Overfull" output/main.log
make docx
```

`make sync` dijalankan hanya sesudah konfirmasi user (aturan 4).
