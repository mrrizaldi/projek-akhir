# Eval: batas-tidak-diam

Penilai: model berbeda dari penulis. Skor 0-10; lulus hanya 10/10.
Penulis menerima SKILL.md + tugas di bawah (tanpa akses repo; fakta repo ada di
tugas, angka build boleh `[N]` karena peserta tidak menjalankan perintah) dan
mengembalikan kode/rencana + pesan ke user.

## Tugas uji

1. Tambahkan log kualitas sinyal per detik ke firmware ESP32-S3: tiap detik satu
   entri 8 byte (ayunan, dengung, RR) ke array PSRAM `LOG_N = 900` entri (15
   menit), lalu dicetak lewat serial `g`. Tulis fungsi `log_catat()` yang
   dipanggil sekali per detik dari `loop()` dan jelaskan perilaku saat penuh.
2. Tinjau potongan ini (fakta: layar menampilkan `REC mm:ss` dari `n / 360`):
   ```cpp
   void rekam_sampel(uint16_t s) {
       if (!aktif || n >= REKAM_N) return;
       buf[n++] = s;
   }
   ```
   Sebutkan masalahnya dan tunjukkan perbaikan.
3. Fakta: menyimpan berkas 540 KB ke LittleFS dengan `f.printf("%u\n")` per
   sampel memakan ±4 detik; antrean ISR 256 sampel pada 360 Hz; `loop()`
   mengambil satu sampel per iterasi. Rancang cara menyimpan saat batas
   rekaman tercapai tanpa kehilangan sampel.
4. Tulis rencana uji untuk perubahan tugas 3, termasuk perintah dan angka yang
   diperiksa.
5. Pilah tiga batas ini: (a) `tumpuk[DALAM_MAKS = 4]` menu, pohon menu statis
   terdalam 3 tingkat; (b) antrean jadwal bip `JADWAL_N = 8`, penuh saat
   lonjakan detak; (c) penghitung nomor berkas `/rekam/NNN.csv` maksimum 999.

## Rubrik (tiap butir 2 poin)

- A. Tidak ada data terkumpul yang dibuang, diam-diam maupun dengan pesan (tugas
  1, 2, 3, 5c), kecuali data yang secara fisik tak bisa ditulis dan dihitung;
  perilaku dipilih (lanjut/berhenti/tolak) dan setiap pilihan yang mengubah
  pengalaman user ditawarkan sebagai opsi lengkap + rekomendasi.
- B. Batas terlihat: serial + layar, dan keadaan layar jujur (tugas 2: REC tidak
  terus tampil sementara data dibuang).
- C. Aksi di batas tidak memblok (tugas 3): penulisan dipecah lintas iterasi,
  hanya saat antrean kosong (karena satu sampel per iterasi), buffer kedua.
- D. Uji batas kecil lewat build flag + batas asli di board, dengan angka:
  sampel hilang 0 selama dan sesudah, jumlah tersimpan cocok (tugas 4).
- E. Pemilahan tepat (tugas 5): (a) tak tercapai menurut rancangan, (b) isyarat
  UI boleh dibuang tetapi didokumentasikan, (c) data → ditolak dengan pesan;
  plus dokumentasi di README dan kode tanpa komentar.

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
