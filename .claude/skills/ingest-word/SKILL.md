---
name: ingest-word
description: Menulis balik suntingan user di DOCX laporan PA (output/main.docx milik laporan/buku-pa atau laporan/progres-pa-1, disunting di WordCraft atau Word) ke file .tex repo ini lewat make sync. Pakai saat user selesai menyunting di Word dan meminta perubahannya masuk ke LaTeX, misalnya "ingest", "sync balik", "masukin suntingan Word ke tex", "udah selesai edit di WordCraft, masukin ke tex", "pull my Word edits back into LaTeX", "sync the docx back to tex", "ingest my WordCraft changes", juga saat make sync-dry atau guard wordcraft-cli menolak di buku PA. Lapisan tipis di atas skill user wordcraft-latex-ingest: memberi path, target make, nama cadangan, pemeriksa format, dan binary khusus repo PA. Bukan untuk membuat DOCX baru (make docx saja), menyunting .tex langsung, atau merapikan gaya tulis (skill tulis-tanpa-slop). Tidak melakukan push.
---

# Ingest suntingan Word ke LaTeX (repo PA)

Muat skill user `wordcraft-latex-ingest` lebih dulu; skill ini hanya menambah hal khusus repo PA. Prosedur 0-8, aturan dasar, dan ringkasan dry-run ada di sana. Di bawah ini yang mengganti placeholder-nya.

## Proyek dan perintah

- Proyek: `laporan/buku-pa` atau `laporan/progres-pa-1`. Semua perintah dijalankan dari foldernya (`cd laporan/<projek>`); `<main>` = `main.tex`, `<out>` = `output/`, `<dir>` = `bab/`. Sumber sebenarnya tetap `.tex`, jadi DOCX hanya jalur suntingan.
- Pakai target make dari `laporan/shared/Makefile.inc`, bukan `wordcraft-cli` mentah, karena target itu sudah membawa `--main main.tex` dan lokasi output yang benar:

| Langkah | Perintah |
|---|---|
| Dry-run | `make sync-dry DOCX=output/suntingan-<stempel>.docx` |
| Tulis | `make sync DOCX=output/suntingan-<stempel>.docx` |
| Bangun ulang PDF | `make pdf-bersih` |
| Buat ulang DOCX | `make docx` (sesudah sync, bukan sebelum) |

## Aturan khusus repo PA

- **Nama cadangan `output/suntingan-<YYYYMMDD-HHMM>.docx`.** Skill user memakai `edits-<stempel>`; di repo ini cadangan memakai awalan `suntingan-` supaya cocok dengan kebiasaan folder `output/`.
- **Bukti build dari `make pdf-bersih`, bukan `make pdf` dan bukan `make rebuild`.** `make pdf` memakai berkas bantu lama sehingga Overfull bisa tersembunyi; `make rebuild` memanggil `clean` yang menghapus `output/` termasuk cadangan DOCX. Hitung dengan `grep -cE "undefined|Overfull" output/main.log`; diharapkan `0`.
- **Pemeriksa format langkah 6:**

```bash
python3 ../../scripts/cek_tabel.py bab/*.tex
python3 ../../scripts/cek_slop.py --ringkas bab/<berkas>.tex
```

  `cek_tabel` untuk semua bab, ambil temuan di baris hasil ingest. `cek_slop` untuk tiap `.tex` yang ditulis sync, ambil temuan `galat`. Keluaran `cek_tabel` sesudah perbaikan masuk pesan commit.
- **Aturan rumah ikut daftar format.** Selain daftar umum (titik dua, titik koma, em dash, istilah belum miring), periksa desimal titik (repo ini memakai desimal koma, ribuan titik) dan label internal repo yang tidak boleh tercetak (HW-n, Fase n, path berkas, nama skrip, `PA_*`, "walkthrough"). Kalimat user tetap tidak ditulis ulang; hanya diusulkan perbaikannya.
- **Tabel, rumus, atau gambar baru yang tidak ditulis sync** dibuat di LaTeX mengikuti skill `tabel-pa` dan `laporan/CLAUDE.md`; gambar ilustrasi tetap placeholder, user yang menggambar.
- **Butir `skipped` dan `% KOMENTAR`** ditangani seperti di skill user; sisa komentar dicek dengan `grep -n "% KOMENTAR" bab/*.tex` (diharapkan kosong).
- **Commit hanya `.tex` di `laporan/<projek>/bab/`** lewat `git add` path eksplisit; `output/suntingan-*.docx` diabaikan git. Tanpa push.

## Binary

`wordcraft-cli` di PATH adalah `~/.cargo/bin/wordcraft-cli`, build branch lokal WordCraft `fix/latex-env-scopes-declarations` (perbaikan ukuran kelas, sel tabel, `\parbox`, Daftar Isi). Versi 0.18.1 dicadangkan di `~/.cargo/bin/wordcraft-cli-0.18.1`; pakai itu hanya bila build lokal diduga menjadi sumber perilaku aneh. Target make memakai binary di PATH, jadi tidak perlu `WORDCRAFT=`.
