# Eval: batas-tidak-diam

Penilai: model berbeda dari penulis. Skor 0-10; lulus hanya 10/10.
Penulis menerima SKILL.md + tugas di bawah (tanpa akses repo; fakta repo ada di
tugas, angka build boleh `[N]` karena peserta tidak menjalankan perintah) dan
mengembalikan kode/rencana + pesan ke user.

## Tugas uji (dipersempit 15 Okt 2026, setelah 7 putaran tidak konvergen)

Fakta yang diberikan ke peserta: build/flash `pio run -t upload` dari
`firmware/`; serial 115200: `r` mulai/stop rekam, `j` jeda, `s` status dengan
`sampel hilang <n>` (= `akuisisi_lewat()`), `l` daftar berkas, `d<n>` cetak
berkas, `h<n>` hapus, `y` sumber replay; tarik `make pull N=<n>` dari `model/`;
layar menampilkan `REC mm:ss` dari `n / 360`; LittleFS total 3456 KiB, terpakai
580 KiB; berkas CSV 300 detik ±540 KB; menyimpan 540 KB dengan `f.printf("%u\n")`
per sampel ±4 s (fakta ukur sebelumnya); antrean ISR 256 sampel pada 360 Hz;
`loop()` mengambil satu sampel per iterasi.

1. Tinjau dan perbaiki (bendera `jeda` harus tetap berfungsi):
   ```cpp
   void rekam_sampel(uint16_t s) {
       if (!aktif || n >= REKAM_N) return;
       buf[n++] = s;
   }
   ```
2. Rancang penyimpanan saat batas tercapai, untuk rekaman yang berlanjut ke
   berkas baru, tanpa kehilangan sampel; termasuk pesan ke user untuk pilihan
   yang mengubah pengalamannya.
3. Rencana uji untuk tugas 2: perintah dan angka yang diperiksa.

## Rubrik (tiap butir 2 poin)

- A. Tidak ada data terkumpul yang dibuang, diam-diam maupun dengan pesan,
  kecuali byte yang ditolak tulis karena ruang dan dihitung; perilaku batas
  dipilih (lanjut/berhenti/tolak) dan pilihan yang mengubah pengalaman user
  ditulis sebagai blok opsi lengkap + rekomendasi.
- B. Batas terlihat: serial + layar (+ bip saat sesi berakhir), `aktif = false`
  lebih dulu, dan keadaan layar jujur (REC tidak tampil saat data tidak
  disimpan; indikator saat `hilang`/`belum` > 0).
- C. Aksi di batas tidak memblok: jalur sampel hanya tukar pointer, simpan
  dipecah lintas iterasi hanya saat antrean kosong, buffer kedua; konstanta
  waktu dibandingkan dengan 711 ms.
- D. Uji batas kecil lewat build flag + batas asli di board, tiap uji dengan
  perintah literal, `sampel hilang 0` sebelum/selama/sesudah, dan baris
  harapan pasti (tanpa `≈`, `<`, placeholder).
- E. Teks README lengkap (prosedur, jebakan + angka, flag uji), sumber angka
  disebut, kode tanpa komentar, dan tidak ada hasil yang ditulis teramati
  tanpa dijalankan.

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-10-15 | sonnet | haiku | 9/10 | A: opsi berhenti tanpa simpan buffer penuh, cek ruang sekali di awal sesi, opsi ke user tidak ditulis. SKILL.md: berhenti = simpan dulu, syarat tolak dicek tiap wadah baru, kegagalan tengah sesi & alokasi terlihat, pertanyaan ditulis lengkap, penulis wadah jaga batas sendiri, hitungan "tak tercapai" eksplisit |
| 2026-10-15 | sonnet | haiku | 8/10 | A: jalur gagal membuang wadah terkumpul, 5c diputuskan tanpa opsi; B: helper gagal tidak menulis aktif=false. Di luar rubrik: kapasitas di opsi tanpa cadangan/overhead, open/usedBytes tak diukur. SKILL.md + rubrik A diselaraskan |
| 2026-10-15 | sonnet | haiku | 8/10 | A: gagal open dibuang sebagai pengecualian; D: uji simpan tertunda tanpa angka pasti, uji jeda pakai ≈. Di luar rubrik: hasil uji ditulis teramati tanpa dijalankan. SKILL.md: pengecualian = hanya byte ditolak tulis, semua uji angka pasti, jalur memblok dicocokkan ke akuisisi_lewat, hasil teramati hanya bila dijalankan |
| 2026-10-15 | sonnet | haiku | 8/10 | C: penyelesaian simpan tertunda (paksa, while) di jalur sampel; E: README hanya "perlu diperbarui". Di luar rubrik: ≈ di baris harapan, konversi ganda, timeout tanpa nilai. SKILL.md: kontradiksi aturan 1 vs 4 dihapus (jalur sampel tak pernah menunggu, kehilangan dihitung & tampil), README lengkap, harapan tanpa ≈, konstanta waktu bernilai |
| 2026-10-15 | sonnet | haiku | 7/10 | A: log tanpa blok opsi; B: REC tetap tampil saat sampel hilang; D: harapan "parsial"/"<". Penilai juga salah hitung (4 berkas benar). SKILL.md: opsi untuk batas data rancangan sendiri, REC diganti HILANG, harapan pasti + sumber angka, tabel cek ke-k, opsi tak menghapus data |
| 2026-10-15 | sonnet | haiku | 8/10 | A: tolak hanya satu usulan, gagal close tak terdeteksi; D: hilang tidak di semua uji, `<` di S2, perintah tidak lengkap. SKILL.md: blok opsi tolak, verifikasi ukuran sesudah close, baris harapan tetap + perintah lengkap tiap uji, konstanta waktu dibandingkan angka |
| 2026-10-15 | sonnet | haiku | 7/10 | A: coba ulang habis membuang wadah utuh; B: belum naik tanpa pesan layar, REC tetap tampil; D: sampel hilang 0 tidak di semua uji, placeholder di harapan. Belum direvisi: loop dihentikan untuk keputusan user (7 putaran tidak konvergen) |
| 2026-10-15 | sonnet | haiku | 8/10 | Soal dipersempit (3 tugas). C: hentikan() dari jalur sampel memanggil Serial/layar/bip; D: uji merujuk "sama dengan Uji 1", tanpa baris sebelum, klausa bersyarat. SKILL.md: jalur sampel hanya menandai, uji berdiri sendiri, pesan layar manusiawi, REC = sampel masuk wadah, butir tak dijalankan tetap [ ] |
