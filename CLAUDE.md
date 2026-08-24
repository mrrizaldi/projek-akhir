# CLAUDE.md — Proyek Akhir (monorepo PA)

Panduan untuk Claude Code saat bekerja di repo ini. Baca dulu sebelum aksi.

## Apa ini

Monorepo Proyek Akhir: **monitoring detak jantung kontinu, klasifikasi
aritmia di edge** (ESP32-S3 + TinyML INT8). Komponen per subdir — lihat
`README.md` untuk tabel & alur artefak.

## Aturan kerja (non-negotiable)

1. **User menulis logika algoritma sendiri.** File `.py`/`.cpp` di `model/`
   dan `firmware/` sengaja stub. **Jangan implementasikan logika** (preprocessing,
   training, quantize, inferensi) kecuali user minta eksplisit di file itu.
   Tugas default Claude di sini = scaffolding, docs, build glue, review.
2. **Non-destruktif.** Jangan hapus/pindah/rename file yang sudah ada. Semua
   pembuatan file pola "buat jika belum ada", jangan overwrite.
3. **`laporan/` read-only by default.** `.tex`, `.bib`, `bab/`, `gambar/`
   jangan diutak-atik tanpa konfirmasi. Path relatif rapuh. Aturan detail
   (gaya tulis, konvensi tabel/gambar, struktur bab) ada di `laporan/CLAUDE.md`
   — baca itu dulu kalau kerja di `laporan/`.
4. **PRD = `model/PRD_Model_Aritmia_TinyML.pdf`** (PDF, bukan `.md`; baca pakai
   Read `pages=`). Ikuti kontrak fungsi & jebakan di sana; jangan vibe-coding.

## Artefak: produsen → konsumen

- `model/` → `model_int8.h` → `firmware/include/` (GENERATED, jangan edit tangan)
- `model/` & `diagrams/` → figure → `laporan/*/gambar/`
- Sinkron via `scripts/export_artifacts.sh`. **Jangan copy manual.**
- Kebijakan commit: **B1** — figure final + `.h` di-commit; data mentah
  MIT-BIH & `.npz` intermediate di-ignore (`.gitignore`).

## Build

- Laporan:  `cd laporan/<projek> && make pdf` → `output/main.pdf` (gitignored).
  Projek: `proposal-pa` (A4), `buku-pa`, `surat-magang`; `shared/` = preamble +
  `Makefile.inc`. **Ukuran kertas fixed per projek** (`\input ../shared/size-aX`),
  tidak ada `make a4`/`make a5` lagi.
- Model:    `cd model && make train|eval|quantize|export` *(stub)*.
  Python 3.11.9 (`model/.python-version`), venv di `model/.venv`,
  deps di `model/requirements.txt`. Script cek/eksplorasi ad-hoc → `model/scripts/`
  (dijalankan dari folder `model/`).
- Firmware: `cd firmware && pio run` *(stub; verifikasi board id ESP32-S3 N16R8)*

## Diagrams

Label requirement `RM1..RM4` **TIDAK boleh muncul** di diagram apa pun.

## Gate points (berhenti, minta konfirmasi)

- Memindahkan/rename apa pun di `laporan/` → pakai `git mv`, konfirmasi dulu.
- Menambah dependency baru → tanya dulu; utamakan stdlib/yang sudah ada.
- Mengubah nilai final di `model/config.py` (FS, bandpass, window, label map)
  → milik user, konfirmasi dulu.
