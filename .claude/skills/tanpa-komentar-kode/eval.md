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
| 2026-10-13 | sonnet | haiku | 9/10 | B: `luar[:5]` batas pratinjau tanpa nama. Premis tugas 1 dibantah peserta dengan benar. SKILL.md: semua literal numerik (termasuk irisan tampilan) bernama; jangan gandakan isi dokumen |
| 2026-10-13 | sonnet | haiku | 9/10 | D: prompt subagen menetapkan cwd firmware/ lalu memakai path relatif root. SKILL.md: tiap perintah `cd` absolut & diuji persis; jebakan per subsistem; perubahan nilai yang diminta selalu ditunjukkan |
| 2026-10-13 | sonnet | haiku | 8/10 | B: `hasil[0]`/`hasil[1]` tanpa nama, `AMBANG` didefinisikan ulang (regresi); C: bullet blok loop di Perangkat, klaim perilaku kode lain keliru. SKILL.md: daftar periksa akhir yang mengumpulkan semua kegagalan, dokumentasi skrip model/ vs scripts/ ditegaskan |
| 2026-10-13 | sonnet | haiku | **10/10** | LULUS. Daftar periksa akhir menutup regresi. |

## Catatan untuk revisi berikutnya (temuan di luar rubrik, putaran 8)

Revisi SKILL.md berikutnya wajib dieval ulang sampai 10/10.

- Hasil grep masih sempat diringkas "kosong" padahal ada baris (pola `JEDA`).
- Satu nomor baris salah (`perangkat.cpp:22` vs 23).
- Helper yang sudah ada (`tampilan_bunyi`, non-blocking) tidak dipakai ulang;
  kandidat butir daftar periksa: "cek helper yang sudah ada di berkas tujuan
  sebelum menulis fungsi baru".

