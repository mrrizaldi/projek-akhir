# CLAUDE.md — Proyek Akhir (monorepo PA)

Panduan untuk Claude Code saat bekerja di repo ini. Baca dulu sebelum aksi.

## Apa ini

Monorepo Proyek Akhir: **monitoring detak jantung kontinu, klasifikasi
aritmia di edge** (ESP32-S3 + TinyML INT8). Komponen per subdir — lihat
`README.md` untuk tabel & alur artefak.

## Aturan kerja (non-negotiable)

1. **Non-destruktif.** Jangan hapus/pindah/rename file yang sudah ada. Semua
   pembuatan file pola "buat jika belum ada", jangan overwrite.
2. **`laporan/` read-only by default.** `.tex`, `.bib`, `bab/`, `gambar/`
   jangan diutak-atik tanpa konfirmasi. Path relatif rapuh. Aturan detail
   (gaya tulis, konvensi tabel/gambar, struktur bab) ada di `laporan/CLAUDE.md`
   — baca itu dulu kalau kerja di `laporan/`.
3. **PRD = `model/PRD_Model_Aritmia_TinyML.pdf`** (PDF, bukan `.md`; baca pakai
   Read `pages=`). Ikuti kontrak fungsi & jebakan di sana; jangan vibe-coding.
4. **Cari dulu di repo sendiri sebelum merancang.** Rencana, skrip, dan
   mekanisme yang dibutuhkan sering SUDAH ada, tinggal dikerjakan atau diperluas.
   Dua contoh nyata (18 Sep 2026): sumber sinyal replay untuk uji tanpa hardware
   sudah tertulis lengkap di `model/docs/2026-09-16-daya-plan.md` Task 4, dan
   rantai penyelarasan R-peak sudah jadi di `scripts/eval_detected_segmentation.py`.
   Merancang ulang dari nol di dua tempat itu = pekerjaan ganda yang sia-sia.

## Bukti mengalahkan kekakuan

Aturan di atas menjaga hal yang sudah terbukti. Aturan ini menjaga supaya yang
terbukti tidak membeku jadi dogma.

- **Golden reference (`firmware/test/golden_ref.h`) itu REGRESSION TEST, bukan
  pagar desain.** Yang dijamin: C dan Python menghitung hal yang sama. Yang
  TIDAK dijamin: parameternya sudah optimal. Kalau ada bukti konkret (paper
  ber-ablasi, atau eksperimen sendiri) bahwa parameter lain lebih baik, ubah
  parameternya lalu **regenerasi** golden (`python scripts/export_golden.py`)
  dan jalankan `pio test -e native`. Regenerasi = prosedur rutin. Menolak
  perubahan "karena nanti golden berubah" = alasan yang salah.
- **Adopsi dari paper hanya kalau papernya mengablasi klaimnya.** Kalau paper
  cuma memakai metode X tanpa pernah membandingkannya, yang kita punya bukan
  bukti melainkan preseden. Boleh ditiru — setelah kita sendiri yang mengablasi.
  Beda ini konkret: Dias 2021 mengablasi jitter (Tabel 3, 6-8, 33 ulangan) tapi
  tidak pernah mengablasi filternya, jadi jitter-nya diadopsi dan filternya
  tidak.
- **Jangan menyalin konstanta empiris paper kalau kita bisa mengukur sendiri.**
  Dias memakai jitter seragam ±18 sampel karena mereka tidak punya detektor.
  Kita punya, dan residunya ternyata berbentuk lain sama sekali (inti tajam ±2,
  ekor berat sampai 54). Menyalin 18 berarti melatih model melawan error yang
  bukan milik kita.
- **Knob eksperimen lewat environment, bukan lewat mengedit nilai final.**
  `config.py` membaca `PA_WIN_PRE`, `PA_WIN_POST`, `PA_HOS`; tanpa env, nilainya
  persis seperti semula. Ablasi jalan tanpa menyentuh gate point. Nilai yang
  MENANG dikunci dengan mengubah bawaannya — dan itu tetap gate point.

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
