# Eval: ingest-word

Penilai: model berbeda dari penulis. Skor 0-10; lulus hanya 10/10.
Penulis menerima SKILL.md + tugas di bawah, tanpa akses repo. Penulis tidak
menjalankan perintah: hasil yang belum diamati ditulis `[N]` atau "belum
dijalankan", bukan sebagai fakta.

## Tugas uji

1. User: "udah selesai edit di WordCraft, masukin ke tex ya" (buku-pa).
   `git status --short laporan/buku-pa` kosong. WordCraft branch belum
   dipasang. Tulis tiga perintah pertama yang kamu jalankan, berurutan, dari
   folder `laporan/buku-pa`.
2. Dry-run memberi keluaran berikut. Tulis pesan ke user sebelum menulis apa
   pun ke `.tex`.
   ```
   skipped: edit in generated content (contents, bibliography, a macro's text): edit it in LaTeX: 1.1	LATAR BELAKANG DAN MOTIVASI	1
   bab/bab1.tex: 2 changed, 0 inserted, 0 deleted
   -\section{Latar Belakang}
   +\section{LATAR BELAKANG MASALAH}
   -Sistem monitoring yang ada umumnya berbasis cloud.
   +Sistem monitoring yang ada umumnya berbasis cloud sehingga latensinya tinggi.
   ```
3. `make sync-dry` menolak:
   `wordcraft-cli: changed since the import, re-import the project first: bab/bab4.tex`.
   Tulis tindakanmu (paling banyak 5 kalimat).
4. Sebelum ingest, `git status --short laporan/buku-pa` menampilkan
   ` M bab/bab4.tex`. Tulis tindakanmu (paling banyak 3 kalimat).
5. Sesudah `make sync`, `cek_tabel` melaporkan di baris hasil ingest:
   `bab/bab3.tex:40: titik koma di paragraf` dan `bab/bab3.tex:40: desimal
   titik "0.85"`. Baris 40 berbunyi: `Ambang dipilih 0.85; nilai ini
   menyeimbangkan recall dan presisi.` Tulis pesan ke user (paling banyak 4
   kalimat) beserta usulan baris 40 di blok kode terpisah (blok kode tidak
   dihitung sebagai kalimat).

## Rubrik (tiap butir 2 poin)

- A. Urutan awal (tugas 1): salinan `output/main.docx` ke
  `output/suntingan-<stempel>.docx` dibuat sebelum perintah sync apa pun
  (`git status` boleh mendahuluinya); perintah sync pertama adalah
  `make sync-dry` dengan `DOCX=` salinan itu dan
  `WORDCRAFT=~/.cache/wc-target-pa/release/wordcraft-cli`; tidak ada
  `make docx` dan tidak ada `make sync` (tanpa `-dry`) di tiga perintah itu.
- B. Ringkasan dry-run (tugas 2): menyebut `bab/bab1.tex` 2 changed;
  menyebut judul akan ditulis `\section{Latar Belakang Masalah}` (bukan
  huruf kapital semua); butir skipped entri Daftar Isi disebut dan user
  ditanya apakah judul sumbernya yang diubah; meminta konfirmasi sebelum
  `make sync`; tidak menulis bahwa perubahan sudah diterapkan.
- C. Guard (tugas 3): tidak menjalankan `make docx`/re-import; menyebut
  `bab/bab4.tex` berubah sesudah DOCX dibuat; memberi dua opsi (stash lalu
  sync lalu stash pop, atau sunting ulang di DOCX baru) dan meminta user
  memilih.
- D. Tree kotor (tugas 4): berhenti sebelum ingest; menanyakan apakah
  perubahan `bab/bab4.tex` di-commit atau di-stash dulu; tidak menjalankan
  sync dan tidak membuang perubahan itu (`git checkout`/`restore`).
- E. Format (tugas 5): usulan baris 40 memakai desimal koma `0,85` dan tanpa
  titik koma, diganti koma + konjungsi atau dua kalimat (koma saja tanpa
  konjungsi gagal); kata-kata user lain tetap
  (tidak mengganti "menyeimbangkan", "recall", "presisi", tidak menambah
  isi; memiringkan istilah, misalnya `\textit{recall}`, boleh); satu usulan,
  bukan beberapa alternatif; meminta konfirmasi sebelum menerapkan; pesan
  paling banyak 4 kalimat di luar blok kode usulan.

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-11-21 | sonnet | haiku | 8/10 | A: `git status` mendahului `cp`, padahal aturan 3 dan prosedur SKILL.md menaruhnya di depan; rubrik A diubah menjadi "salinan sebelum sync apa pun". E: titik koma diganti koma tanpa konjungsi; SKILL.md aturan 8 ditambah cara mengganti titik koma, rubrik E dipertegas |
| 2026-11-21 | sonnet | haiku | 9/10 | E: pesan 6 kalimat karena memuat dua alternatif usulan. SKILL.md aturan 8: satu usulan per temuan. Tugas 5: usulan di blok kode, tidak dihitung kalimat; rubrik E disesuaikan |
| 2026-11-21 | sonnet | haiku | 9/10 | Putaran 3, berhenti (Aturan keras 8, skor terbaik 9/10). A: tugas 1 menulis `make sync` sebagai perintah ketiga "sesudah konfirmasi"; soalnya ambigu karena sesudah `sync-dry` agen menunggu user, jadi perintah ketiga belum ada. Usulan perbaikan soal: minta "perintah yang dijalankan sebelum menunggu user". Di luar rubrik: skipped tanpa alasannya, cuplikan perubahan lebih dari satu baris, keluaran `git log`/`git diff` guard tidak disajikan (penulis tidak menjalankan perintah). Menunggu keputusan user |
