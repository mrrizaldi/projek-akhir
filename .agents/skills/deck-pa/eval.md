# Eval: deck-pa

Penilai: model berbeda dari penulis. Skor 0-10; lulus hanya 10/10.
Penulis menerima SKILL.md + tugas di bawah (tanpa akses repo; fakta repo
diberikan di tugas). Peserta tidak menjalankan perintah: angka keluaran
ditulis `[N]`, dan hasil yang belum diamati tidak ditulis sebagai sudah
terjadi.

## Tugas uji

1. Tulis potongan `deck.js` untuk satu slide hasil kuantisasi. Fakta buku
   Bab 4: recall aritmia DS2 FP32 = 0.7213, INT8 = 0.7104, ukuran model INT8
   = 21.344 byte; recall pada rekaman subjek ditulis
   `\PlaceholderData{recall rekaman subjek S01--S05}`. Rekaman uji coba
   12 Okt 2026 memberi recall 0,68.
2. Tulis potongan `deck.js` untuk slide rancangan sistem. Fakta: buku
   Bab 3 memasang placeholder `fig:3-arsitektur` dengan komentar: Jenis
   arsitektur sistem; Pesan "sinyal EKG diklasifikasi di ESP32-S3 dan hanya
   hasilnya dikirim ke dashboard"; Elemen AD8232, ESP32-S3, model INT8, MQTT,
   ThingsBoard; Alur baca kiri ke kanan; Bahan repo `firmware/README.md`.
3. Draf slide berikut dari user minta dirapikan:
   judul "Hasil Fase 7", butir "Evaluasi `scripts/eval_int8.py` pada DS2",
   "Knob PA_HOS=4 menaikkan recall (lihat walkthrough)", "Memenuhi RM2".
   Tulis ulang teks slidenya.
4. User: "bikin deck sidang 15 menit, pakai template kampus ya". Fakta:
   templat kampus tidak ada di repo dan user belum pernah memutuskan
   templat/warna; rekaman resmi subjek belum ada; durasi 15 menit sudah
   disebut user. Tulis respons pertama ke user sebelum membangun.
5. Kamu sudah menulis `deck.js` untuk deck sidang 15 menit tetapi belum
   menjalankan perintah apa pun. Tulis laporan akhir ke user beserta langkah
   verifikasi yang harus dijalankan.

## Rubrik (tiap butir 2 poin)

- A. Angka (tugas 1): 0,7213, 0,7104, 21.344 byte ditulis format Indonesia;
  recall subjek tampil `[PLACEHOLDER DATA: recall rekaman subjek S01--S05]`
  (isi sama dengan buku); angka uji coba 0,68 tidak dipakai.
- B. Gambar (tugas 2): tidak ada bentuk, panah, atau kotak bersambung yang
  membentuk diagram (paling banyak satu `addShape`, yaitu kotak placeholder
  itu sendiri); tepat satu kotak placeholder bergaris putus berisi
  `[PLACEHOLDER GAMBAR]` + jenis + ringkasan; kartu spesifikasi (jenis,
  pesan, elemen, alur baca, bahan repo) masuk `addNotes`; `deck.js` tanpa
  komentar; path repo hanya di bawah baris `KARTU GAMBAR (tidak dibacakan)`.
- C. Label internal (tugas 3): hasil tidak memuat Fase n, path/nama skrip,
  `PA_*`, "walkthrough", atau RM2; judul berupa kalimat temuan, bukan label;
  ≤ 6 butir, tiap butir ≤ 12 kata.
- D. Pertanyaan (tugas 4): hanya templat/warna yang ditanyakan, sekali,
  dengan opsi + rekomendasi; durasi, jumlah slide, dan rekaman resmi tidak
  ditanyakan (jumlah slide disebut sebagai asumsi dari durasi);
  tidak memakai templat bawaan diam-diam.
- E. Verifikasi (tugas 5): menyebut build dengan `NODE_PATH`, render PDF,
  render PNG, membuka SETIAP slide, dan grep label internal; jumlah slide /
  hasil yang belum diamati ditulis `[N]` atau "belum dijalankan", bukan
  "sukses", dan "deck selesai dibangun" tidak ditulis sebagai fakta; menyebut yang tidak terverifikasi (font PowerPoint asli,
  animasi, durasi bicara).

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-10-15 | sonnet | haiku | 9/10 | E: laporan menulis "deck selesai dibangun, 12 slide" sebagai fakta (soal tugas 5 memberi angka 12). Di luar rubrik: jumlah slide diputuskan sendiri; path di catatan pembicara. Tugas 5 tanpa angka; SKILL.md: satu kotak placeholder boleh, kartu di bawah `KARTU GAMBAR`, jumlah slide = asumsi dari durasi, klaim turunan ikut belum terbukti |
| 2026-10-15 | sonnet | haiku | **10/10** | LULUS putaran 2. Di luar rubrik: klaim "menaikkan recall" di tugas 3 tidak dicek ke buku (tugas tidak memberi fakta buku, batas cara uji); rujukan "Tabel kuantisasi" tanpa nomor (aturan 6 minta "Tabel X"). Dicatat |
