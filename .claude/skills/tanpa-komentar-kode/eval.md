# Eval: tanpa-komentar-kode

Penilai: model berbeda dari penulis. Skor 0-10; lulus hanya 10/10.
Penulis menerima SKILL.md + satu tugas di bawah dan mengembalikan kode + nama
dokumen tempat penjelasan ditaruh. Penilai memakai rubrik di bawah.

## Tugas uji

1. C++ ESP32: fungsi `bip_tolak()` yang membunyikan buzzer dua kali 40 ms
   berjarak 60 ms; ada jebakan: LEDC harus dilepas setelah bunyi agar pin
   kembali HIGH (aktif-LOW).
2. Python: fungsi `rr_per_segmen(segmen, fs)` yang menghitung interval RR (detik)
   per segmen tanpa melintasi batas segmen; terima list array sampel indeks R.
3. Menyunting kode yang SUDAH berkomentar: ubah ambang dari 60 menjadi 80 dan
   kembalikan potongan lengkap. Masukan:
   ```c
   // Ambang ayunan minimum (count ADC) agar sinyal dianggap tersambung.
   static const int AMBANG = 60;
   /* Dipanggil tiap 1 detik dari loop utama. */
   bool sinyal_ok(int ayun)
   {
       return ayun >= AMBANG; // bandingkan dengan ambang
   }
   // TODO: jadikan konfigurasi NVS
   ```
4. Generator Python yang menulis header C berisi array `const int16_t X[] = {...}`
   dari list angka.
5. Prompt untuk subagen yang akan menambah fitur "bip tolak" di firmware.

## Rubrik (tiap butir 2 poin)

- A. Tidak ada komentar/docstring sama sekali di kode keluaran (termasuk tugas 3,
  komentar lama ikut dibuang; tugas 4, header yang dihasilkan tanpa komentar).
- B. Maksud terbaca dari nama (konstanta bernama, fungsi kecil) tanpa komentar.
- C. Jebakan/rasional yang perlu (tugas 1) dipindah ke dokumen yang tepat dan
  disebut lokasinya.
- D. Tugas 5: prompt subagen memuat aturan tanpa komentar secara eksplisit +
  perintah `python3 scripts/cek_komentar.py`.
- E. Tidak ada pelanggaran pengecualian (tidak memakai `__doc__` untuk argparse,
  tidak menaruh TODO/penanda bagian).

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-10-13 | sonnet | haiku | 9/10 | B: literal `1` di `ledc_stop` tanpa nama; urutan argv terbalik. SKILL.md diperbaiki (literal API, argv bernama, grep nama yang ada, berkas dok konkret, potongan utuh) |
| 2026-10-13 | sonnet | haiku | 8/10 | B: `BIP_TOLAK_MS` dipakai ulang beda arti, `AMBANG_AYUN` yang ada tidak dipakai; D: path pemeriksa salah dari `firmware/`. SKILL.md: grep nama+nilai, larang pakai ulang beda arti, cek `static`, klaim pustaka diverifikasi, perintah dari root |
| 2026-10-13 | sonnet | haiku | 7/10 | B: nama mirip `LAMA_BIP_TOLAK_MS`, nama literal tidak menyebut efek; C: rujukan berkas:baris & isi test salah; D: syarat cek seluruh repo tak terpenuhi. SKILL.md: grep pola, larang nama mirip/definisi ulang, nama = efek, semua klaim dok dicek, cek berkas yang disentuh |
| 2026-10-13 | sonnet | haiku | 8/10 | B: irisan `[1:, 0]` tanpa nama; C: klaim §Jebakan tidak ada (padahal ada), jebakan ditaruh di Pin map. SKILL.md: indeks bernama, baca prefiks berkas tujuan, §Jebakan sudah ada, prompt subagen tunjuk bagian dok & tandai belum-terverifikasi. Pemeriksa: direktori di luar git didukung |
