# Skill repo PA

Skill = `SKILL.md` (aturan) + `eval.md` (tugas uji, rubrik, riwayat skor).
Aturan keras 7–8 di `CLAUDE.md` root: setiap kegagalan yang ditangkap user
menjadi skill hari itu juga, dan setiap skill punya eval yang dinilai model
berbeda, maksimal 3 putaran.

| Skill | Lingkup |
|---|---|
| `struktur-pa` | kerangka bab laporan PA, benang merah, register, placeholder gambar, QA sebelum kumpul |
| `tabel-pa` | tabel LaTeX laporan PA (grid PENS, satu tabel satu pertanyaan, templat A–G) |
| `buku-ikut-proposal` | Bab 1 buku mengikuti proposal pada garis besar, sinkronisasi balik ke proposal |
| `batas-tidak-diam` | firmware: batas tidak membuang data diam-diam, aksi di batas tidak memblok |
| `tanpa-komentar-kode` | kode tanpa komentar/docstring, penjelasan ke dokumen |
| `deck-pa` | deck presentasi PA (PPTX): isi dari buku, angka tidak dikarang, tanpa label internal, ilustrasi = placeholder, render + lihat tiap slide |
| `kicad-pcb-pa` | PCB/skematik KiCad: keputusan desain ditanyakan, format KiCad 9, pad dibaca bukan ditebak, nama net = skematik, `cek_board.py` LULUS |
| `tautan-lokal` | dokumen bertautan ke berkas lokal: HTML bukan PDF, tautan relatif `#page=N`, diklik lewat server lokal sebelum diserahkan, yang belum terbukti disebut |
| `tulis-tanpa-slop` | paragraf laporan tanpa pola tulisan AI: isi, angka, sitasi tetap; frasa klise, struktur formulaik, dan kebiasaan bawaan aturan rumah ("karena itu" sisipan, "yaitu" berderet) ditindak; `cek_slop.py` |
| `ingest-word` | suntingan DOCX ke LaTeX: DOCX dicadangkan, dry-run diringkas dan dikonfirmasi, judul dikembalikan ke huruf sumber, skipped dipindah manual, format dirapikan sesudah dikonfirmasi |

`narasi-pa` nonaktif sejak 21 Nov 2026, disimpan di
`.claude/skills-arsip/narasi-pa/` sebagai rujukan.

Pemeriksa mesin untuk skill laporan: `python3 scripts/cek_tabel.py`
(`scripts/README.md`).

## Menjalankan eval satu skill

Dua agen terpisah per putaran, dari Claude Code (Agent tool) atau sesi
terpisah. Penulis dan penilai harus model yang berbeda (yang dipakai sejauh
ini: penulis `sonnet`, penilai `haiku`).

1. **Penulis** hanya diberi `SKILL.md` (plus `referensi/` bila ada) dan
   bagian "Tugas uji" dari `eval.md`, tanpa rubrik dan tanpa akses repo
   lain. Ia tidak menjalankan perintah dan tidak menyunting repo. Angka
   keluaran perintah ditulis `[N]`, suntingan ditulis sebagai usulan.
   Jawaban ditulis ke satu berkas di scratchpad dengan heading
   `## Tugas 1` sampai `## Tugas n`.
2. **Penilai** diberi `SKILL.md`, `eval.md` utuh (tugas + rubrik), dan
   berkas jawaban. Ia menilai tiap butir rubrik 0/1/2 secara literal,
   mengutip bagian jawaban yang gagal, menghitung sendiri apa yang rubrik
   minta dihitung (kata per kalimat, jumlah angka, sel ≤ 20 kata), dan
   mencatat pelanggaran `SKILL.md` di luar rubrik (maks 3). Keluaran: tabel
   `Butir | Skor | Alasan`, baris `Skor: X/10`, lalu "Di luar rubrik".
3. Skor < 10: perbaiki `SKILL.md` (aturan yang ambigu) atau rubrik/tugas
   (soal yang tidak berjawaban pasti), catat satu baris di "Riwayat skor"
   `eval.md` (tanggal, penulis, penilai, skor, temuan, perubahan), lalu
   putaran berikutnya dengan penulis baru (bukan melanjutkan agen lama).
4. Berhenti pada 10/10, pada putaran ke-3, atau bila skor tidak naik dua
   putaran berturut-turut. Yang belum 10/10 dicatat skor terbaiknya dan
   ditanyakan ke user. Setiap perubahan `SKILL.md` sesudah lulus mewajibkan
   eval ulang.

## Cara menulis skill

Gaya mengikuti skill provenfix (`~/dev/before-after/SKILL.md`).

1. **Description** menyebut apa yang dikerjakan, kapan dipakai (frasa pemicu
   seperti yang diketik user, Indonesia dan Inggris), bukan untuk apa, dan apa
   yang tidak dilakukannya.
2. **Pembuka** satu atau dua kalimat tentang hasil akhir.
3. **`## Aturan dasar`** dibuka "Tiap aturan ada karena melanggarnya pernah
   menggagalkan pekerjaan." Tiap butir diawali frasa tebal, lalu alasan
   singkat yang merujuk `temuan.md` (`temuan #3`).
4. **`## Rujukan`** berupa tabel `| Berkas | Baca bila |`. SKILL.md hanya
   memuat aturan dasar dan prosedur; detail yang berlaku pada kondisi
   tertentu pindah ke `referensi/`.
5. **`## Prosedur`** bernomor mulai 0 (persiapan). Tiap langkah memuat
   perintah persis di blok kode, keluaran yang diharapkan, dan kondisi
   berhenti ("gagal → berhenti, kutip alasannya").
6. **Satu layar konfirmasi** sebelum skill menulis berkas milik user; sesudah
   "ya", lanjut tanpa bertanya lagi kecuali ada langkah yang gagal.
7. **`temuan.md`** daftar bernomor, dibuka "Tiap butir pernah menggagalkan
   satu pekerjaan." Isinya kegagalan nyata: asal skill dan pelajaran dari
   riwayat eval.
8. **`templat/`** untuk keluaran berbentuk tetap (laporan ke user, pesan
   commit).
9. **`eval.md`** tetap (Aturan keras 8).

Isi aturan tidak berubah saat gaya ditulis ulang: setiap aturan lama
dipetakan ke tempat barunya, dan eval dijalankan ulang satu putaran dengan
skor minimal sama dengan skor terbaik sebelumnya.
