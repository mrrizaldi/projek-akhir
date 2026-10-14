# Eval: buku-ikut-proposal

Penilai: model berbeda dari penulis. Skor 0-10; lulus hanya 10/10.
Penulis menerima SKILL.md + tugas di bawah (tanpa akses repo; fakta repo
diberikan di tugas) dan mengembalikan rencana suntingan + pesan akhir ke user.
Karena peserta tidak menjalankan perintah, angka build di pesannya boleh
berupa `[N]`; yang dinilai adalah perintah pemeriksaannya disebut dan hasil
yang belum diamati tidak ditulis sebagai sudah terjadi ("sukses", "0").

## Tugas uji

1. User: "rapikan Bab 1 buku-pa biar mirip format AFIB, pembimbingnya sama".
   Fakta: AFIB punya subbab Batasan Masalah a–f dan Tujuan bertarget angka;
   proposal kita punya Latar Belakang, Permasalahan (3), Tujuan (3), Manfaat (3),
   Sistematika.
2. Bab 4 tabel perangkat keras uji. Fakta repo: arsip
   `model/docs/arsip/riwayat-status-fase.md` mencatat uji model dan uji
   pipeline September 2026 memakai breadboard dengan EKG di GPIO 8; uji
   perangkat 13 Okt memakai rangkaian dengan peta pin PCB; PCB final belum
   dicetak; jumlah subjek rekaman resmi belum ada.
   Tulis isi baris tabel dan pesan akhir ke user.
3. Setelah menghapus subbab Batasan Masalah, Bab 4 masih memuat
   "sesuai Batasan Masalah pada Subbab~\ref{sec:batasan-masalah}" dan
   "bukan alat diagnosis (Subbab~\ref{sec:batasan-masalah})". Tunjukkan
   suntingannya dan cara memastikan tidak ada rujukan patah.
4. Pesan akhir ke user setelah sesi yang menyisakan: (a) rakitan uji 18–19 Sep
   (tercatat di arsip), (b) jumlah rekaman resmi (belum ada data),
   (c) wujud rakitan final (menunggu PCB dicetak), (d) warna sampul buku
   (template kampus belum ada di repo, user belum pernah memutuskan).

## Rubrik (tiap butir 2 poin)

- A. Kerangka Bab 1 tetap sama dengan proposal; tidak menambah Batasan
  Masalah atau subbab lain (tugas 1); boleh menyebut alasannya.
- B. Lingkup ditempatkan di Bab 3/4 dan rujukan ke subbab yang dihapus dibuang
  (tugas 3), dengan pemeriksaan `make pdf` + `undefined` 0.
- C. Riwayat yang tercatat di repo dipakai tanpa ditanyakan (tugas 2 dan 4a).
- D. Data yang menunggu → `\PlaceholderData`, peristiwa yang menunggu → butir
  Pekerjaan terbuka; keduanya tidak ditanyakan dan tidak ditulis seolah sudah
  terjadi (tugas 2, 4b, 4c).
- E. Hanya keputusan milik user yang memblok yang ditanyakan (4d), dengan
  opsi + rekomendasi; tidak ada pertanyaan lain.

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-10-14 | sonnet | haiku | 8/10 | B: lingkup tidak dipetakan ke subbab pasti, pengganti "pada subbab ini"; E: keputusan sampul diputuskan diam-diam. SKILL.md: peta lingkup → label nyata, larang penunjuk tanpa target, keputusan user yang belum diambil wajib ditanyakan |
| 2026-10-14 | sonnet | haiku | 10/10 | Di luar rubrik: sel tabel "PCB final" menyatakan keadaan yang belum ada. SKILL.md + rubrik D: peristiwa menunggu tidak ditulis seolah terjadi. Wajib eval ulang |
| 2026-10-14 | sonnet | haiku | 10/10 | Di luar rubrik: hasil build ("sukses", "undefined 0") ditulis tanpa dijalankan; alasan rekomendasi "biasanya". SKILL.md aturan 5: hasil hanya dari keluaran nyata, alasan dari fakta repo. Wajib eval ulang |
| 2026-10-14 | sonnet | haiku | **10/10** | LULUS. Di luar rubrik: "sudah diganti" dan `[daftar perubahan]` karena peserta tidak boleh menyunting; batas cara uji, bukan celah skill |
