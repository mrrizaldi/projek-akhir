---
name: ingest-word
description: Menulis balik suntingan user di DOCX laporan PA (output/main.docx buku-pa atau progres-pa-1, disunting di WordCraft atau Word) ke file .tex lewat wordcraft-cli latex-sync. Dipakai saat user selesai menyunting dan meminta perubahannya dimasukkan ke LaTeX, misalnya "ingest", "sync balik", "masukin suntingan Word ke tex", "udah selesai edit di WordCraft, masukin ke tex", "pull my Word edits back into LaTeX", "sync the docx back to tex", "ingest my WordCraft changes". DOCX dicadangkan dulu, dry-run diringkas dan dikonfirmasi user sebelum ditulis, judul dikembalikan ke huruf sumber, bagian yang dilewati sync dipindah manual, format dirapikan hanya sesudah dikonfirmasi tanpa menulis ulang kalimat user, lalu PDF dibangun ulang dan di-commit dengan bukti. Bukan untuk membuat DOCX baru dari LaTeX (make docx saja), menyunting laporan langsung di .tex, atau merapikan gaya tulis paragraf (skill tulis-tanpa-slop). Tidak melakukan push.
---

# Ingest suntingan Word ke LaTeX

Suntingan user di DOCX masuk ke `.tex` dalam satu commit yang hanya berisi
suntingan itu dan bisa di-revert utuh, dengan PDF dan DOCX dibangun ulang.
LaTeX tetap sumber kebenaran; user menyunting bebas di DOCX, lalu
`wordcraft-cli latex-sync` (`make sync`) menulis perubahannya balik.

## Aturan dasar

Tiap aturan ada karena melanggarnya pernah menggagalkan pekerjaan.

- **Cadangkan dulu, jangan pernah menimpa DOCX suntingan.** `make docx` menulis
  ke `output/main.docx`, berkas yang sama yang disunting user (temuan #1).
  Salinan `output/suntingan-<YYYYMMDD-HHMM>.docx` dibuat sebelum perintah sync
  apa pun, semua sync memakai salinan itu (`DOCX=...`), dan `make docx` baru
  dijalankan sesudah sync selesai ditulis.
- **Guard menolak → berhenti, jangan re-import.** Re-import (`make docx`)
  membuang suntingan user (temuan #2). User yang memilih jalan keluarnya
  (langkah 2).
- **Tree `.tex` harus bersih sebelum ingest**, supaya commit ingest hanya
  berisi suntingan user dan bisa di-revert utuh. Ada `.tex` berubah →
  berhenti dan tanyakan: commit dulu atau stash. Perubahan itu tidak dibuang
  (`git checkout`/`git restore` tidak dipakai).
- **Tidak ada `make sync` sebelum user mengonfirmasi ringkasan dry-run.**
  Sesudah `make sync-dry`, skill berhenti dan menunggu (temuan #9).
- **Judul dikembalikan ke huruf sumber.** Sync menulis judul dalam huruf
  kapital tampilan (temuan #3). Setiap `\chapter{...}`/`\section{...}` di diff
  yang menjadi kapital semua ditulis ulang dengan kapitalisasi sumber (huruf
  awal kapital per kata, seperti judul lain di berkas itu), karena gaya judul
  sudah mengapitalkan tampilannya. Perbaikan ini disebut di ringkasan dry-run.
- **Yang dilewati sync dipindah manual**, dan komentar Word dikerjakan lalu
  barisnya dihapus. Tanpa itu suntingan hilang tanpa tanda (temuan #4, #5).
- **Kalimat user tidak ditulis ulang.** Format dirapikan hanya sesudah user
  mengonfirmasi daftar perbaikannya. Pilihan kata, urutan, dan isi kalimat
  tetap. Satu usulan per temuan, bukan beberapa alternatif (temuan #8). Titik
  koma diganti titik (menjadi dua kalimat) atau koma + konjungsi ("dan",
  "sehingga"); koma saja tanpa konjungsi tidak boleh (temuan #7).
- **Bukti diambil dari `make pdf-bersih`, bukan `make pdf`.** `make pdf` memakai
  ulang berkas bantu lama dan bisa menyembunyikan Overfull (temuan #10).
- **Salinan `output/suntingan-*.docx` tidak di-commit** (`output/` diabaikan
  git).

## Rujukan

| Berkas | Baca bila |
|---|---|
| `temuan.md` | sebelum mengubah skill ini, atau bila sebuah aturan dasar terasa tidak perlu |
| `templat/ringkasan.md` | langkah 3: menyusun layar konfirmasi dry-run |
| `referensi/sync.md` | keluaran dry-run memuat `skipped` atau `% KOMENTAR`, atau `wordcraft-cli` berperilaku tidak seperti yang diharapkan |

## Prosedur

`<projek>` = `buku-pa` atau `progres-pa-1`. Semua perintah dari
`laporan/<projek>`.

### 0. Persiapan: tree bersih

```bash
cd laporan/<projek>
git status --short .
```

Diharapkan: tidak ada baris `.tex`. Ada `.tex` berubah → berhenti, sebut
berkasnya, tanyakan apakah di-commit atau di-stash dulu. Jangan menjalankan
sync dan jangan membuang perubahan itu.

### 1. Cadangkan DOCX suntingan

```bash
cp output/main.docx output/suntingan-$(date +%Y%m%d-%H%M).docx
ls output/suntingan-*.docx
```

Diharapkan: salinan baru tercantum. `output/main.docx` tidak ada → berhenti,
tanyakan letak DOCX yang disunting user.

### 2. Dry-run

```bash
make sync-dry DOCX=output/suntingan-<stempel>.docx
```

Diharapkan: baris `bab/<berkas>.tex: N changed, N inserted, N deleted`, diff
`-`/`+` per perubahan, dan baris `skipped: ...` bila ada.

Guard menolak (`changed since the import, re-import the project first:
<berkas>`) → berhenti, jangan menjalankan `make docx`. Sajikan berkas yang
disebut guard beserta riwayatnya sejak DOCX dibuat:

```bash
git log --oneline -5 -- <berkas>
git diff <commit-sebelum-perubahan> -- <berkas>
```

Lalu beri dua opsi dan biarkan user memilih: (a) `git stash` perubahan `.tex`
itu, sync, lalu `git stash pop` dan selesaikan konflik; (b) user menyunting
ulang di DOCX baru.

### 3. Layar konfirmasi

Isi `templat/ringkasan.md` dari keluaran langkah 2 dan sajikan: per berkas
jumlah `changed/inserted/deleted`, cuplikan sebelum → sesudah tiap perubahan
(paling banyak satu baris per perubahan), judul yang akan dikembalikan ke huruf
sumber, daftar `skipped` beserta alasannya dan rencananya
(`referensi/sync.md`), pertanyaan untuk suntingan entri Daftar
Isi/Gambar/Tabel, serta jumlah komentar Word beserta rencana tindakan
tiap komentar.

Tunggu "ya". Koreksi dari user → ubah yang disentuhnya dan sajikan ulang.
Sesudah "ya", lanjut tanpa bertanya lagi sampai langkah 6, kecuali ada langkah
yang gagal. Usulan format di langkah 6 punya konfirmasinya sendiri, karena
temuannya baru ada sesudah sync menulis `.tex`.

### 4. Tulis dan kembalikan judul

```bash
make sync DOCX=output/suntingan-<stempel>.docx
git diff --stat -- bab/
```

Diharapkan: jumlah per berkas sama dengan dry-run. Berbeda atau guard menolak
→ berhenti, kutip keluarannya. Lalu tulis ulang setiap judul kapital semua
dengan kapitalisasi sumber.

### 5. Pindah butir skipped dan kerjakan komentar

Ikuti `referensi/sync.md` §Memindah butir yang dilewati sync dan §Komentar
Word. Tunjukkan diff hasil pemindahan:

```bash
git diff -- bab/
```

### 6. Rapikan format sesudah dikonfirmasi

```bash
python3 ../../scripts/cek_tabel.py bab/*.tex
python3 ../../scripts/cek_slop.py --ringkas bab/<berkas>.tex
```

`cek_tabel` untuk semua bab; ambil temuan yang jatuh di baris hasil ingest.
`cek_slop` untuk tiap `.tex` yang ditulis sync; ambil temuan `galat`.

Sajikan daftar perbaikan format (titik dua, titik koma, em dash di paragraf,
istilah teknis belum miring, desimal titik, label internal, galat
`cek_slop`), satu usulan per temuan. Terapkan sesudah user mengonfirmasi, lalu
jalankan `cek_tabel` lagi. Diharapkan: 0 galat di baris hasil ingest.

### 7. Bangun ulang

```bash
make pdf-bersih
grep -cE "undefined|Overfull" output/main.log
make docx
```

Diharapkan: `grep` mencetak `0`, dan `make docx` mencetak
`DOCX tersimpan di output/main.docx`. Lebih dari 0 → berhenti, kutip baris
`undefined`/`Overfull` dari log (`grep -nE "undefined|Overfull"
output/main.log`), perbaiki, ulangi langkah ini.

### 8. Commit dengan bukti

Commit hanya berkas `.tex` yang berubah (`git add bab/<berkas>.tex ...`).
Pesan commit memuat:

1. ringkasan sync: `changed/inserted/deleted` per berkas;
2. butir skipped yang dipindah;
3. keluaran `cek_tabel` sesudah perbaikan;
4. baris hitungan `undefined`/`Overfull` dari log `make pdf-bersih`.

Tidak di-push.
