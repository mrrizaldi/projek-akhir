---
name: tanpa-komentar-kode
description: Wajib dipakai setiap kali menulis atau menyunting kode di repo PA (C/C++ firmware, Python model/dashboard, shell, platformio.ini, generator header). Kode ditulis tanpa komentar dan tanpa docstring; penjelasan masuk dokumen terpisah. Juga dipakai saat memberi prompt ke subagen yang akan menulis kode.
---

# Tanpa komentar kode

Kegagalan yang ditangkap user (13 Okt 2026): kode penuh komentar penjelas,
riwayat, dan rasional, padahal user sudah berkali-kali meminta tidak. Komentar
dianggap spam; penjelasan harus di dokumen tersendiri.

## Aturan

1. Tidak ada komentar di kode: `//`, `/* */`, `#`, `;` (ini), docstring Python.
   Berlaku untuk kode baru DAN baris yang disunting. Jangan menambah komentar
   "penjelas perubahan", "TODO", "catatan", "jebakan", atau tanda bagian.
2. Butuh penjelasan? Ganti nama (variabel, fungsi, konstanta) sampai maksudnya
   terbaca, atau pecah fungsi. Konstanta ajaib → nama bermakna
   (`AMBANG_AYUN`, bukan `60 // ambang ayunan`). Ini termasuk literal yang
   dikirim ke API pihak ketiga: `ledc_stop(mode, kanal, LEVEL_DIAM_HIGH)`,
   bukan `ledc_stop(mode, kanal, 1)`. Nama literal menyebut EFEK yang terjadi
   (`LEVEL_PIN_DIAM_HIGH`), bukan istilah internal (`..._TERBALIK`). Argumen CLI diberi nama lokal sebelum
   dipakai (`nama = sys.argv[1]`, `jalur = sys.argv[2]`), urut sesuai posisinya. Indeks/irisan numerik juga diberi nama
   (`KOLOM_RR_PREV = 0`, `rr = fitur[BARIS_PERTAMA_VALID:, KOLOM_RR_PREV]`)
   atau dipecah jadi fungsi bernama, bukan `[1:, 0]`.
3. Pakai nama yang SUDAH ADA di repo. Sebelum menamai apa pun, grep NAMA dan
   NILAINYA di seluruh `firmware/` dan `model/`
   (`grep -rn "AMBANG\|= 60" firmware/ model/`):
   - ada dengan arti SAMA → pakai nama itu (mis. `AMBANG_AYUN` di `gerbang.h`);
   - nama ada dengan arti LAIN → jangan dipakai ulang, dan jangan memakai nama
     MIRIP (substring/pola sama, mis. `LAMA_BIP_TOLAK_MS` vs `BIP_TOLAK_MS`);
     grep pola (`grep -rn "BIP_\|TOLAK" firmware/`), bukan hanya nama persis,
     dan baca daftar konstanta di BERKAS TUJUAN (semua prefiks yang ada di
     sana, mis. `NADA_`, `BIP_`, `AMBANG`) sebelum menambah nama;
   - konstanta yang sudah ada di header repo tidak didefinisikan ulang di
     potongan kode; include header-nya;
   - jangan menebak lalu menulis "sesuaikan bila beda".
   Sebelum menyuruh memanggil fungsi, cek visibilitasnya (`static` tidak bisa
   dipanggil dari berkas lain).
4. Rasional, jebakan, cara pakai, angka ukur → dokumen, sebut berkas konkret:
   firmware → `firmware/README.md` §Jebakan (bagian `## Jebakan` SUDAH ADA;
   bukan di §Pin map) atau `model/docs/firmware-walkthrough.md`;
   pipeline model → walkthrough tahapnya (peta di `model/docs/README.md`, mis.
   segmentasi/RR → `model/docs/features-rr-walkthrough.md`), keputusan →
   `model/CLAUDE.md`; dashboard → `dashboard/README.md`; skrip →
   `scripts/README.md`. Bila belum ada bagian yang cocok, tambahkan bagian baru
   di berkas itu.
5. Menyunting kode yang sudah berkomentar: buang SEMUA komentarnya (termasuk
   TODO), pindahkan isinya yang bernilai ke dokumen, dan kembalikan potongan
   UTUH, bukan cuplikan.
6. Berkas GENERATED: generatornya tidak boleh menulis komentar.
7. Pengecualian fungsional saja: `##` deskripsi target Makefile (dipakai
   `make help`), teks bantuan CLI yang dicetak program (string argparse, bukan
   `__doc__`), shebang `#!`.
8. Setiap klaim yang ditulis ke dokumen harus dicek sebelum ditulis: rujukan
   `berkas:baris` dan nama bagian (Read/grep, nomor baris aktual), isi test
   yang dirujuk (buka berkas test-nya), dan perilaku pustaka (jalankan, atau
   baca sumber/datasheet terpasang). Yang belum terukur di perangkat ditulis
   "belum diverifikasi di board" dan tidak boleh bertentangan dengan premis.
   Lebih baik tanpa nomor baris daripada nomor baris salah.
9. Saat menyuruh subagen menulis kode, tulis aturan ini eksplisit di prompt,
   dengan perintah pemeriksa yang path-nya benar dari root repo:
   `cd /home/mrrizaldi/dev/projek-akhir && python3 scripts/cek_komentar.py`.

## Pemeriksaan sebelum selesai

Dari root repo, pada berkas yang disentuh (syarat selesai):
```bash
python3 scripts/cek_komentar.py <berkas-yang-disentuh>...
```
Harus keluar 0. Seluruh repo (`python3 scripts/cek_komentar.py` tanpa argumen)
dijalankan CI (`.github/workflows/cek.yml`); pelanggaran di berkas yang tidak
disentuh bukan alasan menyunting berkas di luar lingkup, cukup dilaporkan.
Prompt subagen memakai bentuk berkas-yang-disentuh, bukan seluruh repo, dan
menunjuk bagian dokumen tujuan yang benar (aturan 4); klaim yang belum terukur
di board ditandai "belum diverifikasi di board" juga di dalam prompt.

## Contoh

Salah:
```cpp
// Urutan penting: SPI dulu, baru buzzer, karena SPI.begin merebut GPIO13.
SPI.begin(TFT_SCK, -1, TFT_MOSI);
pasang_buzzer();
```
Benar (kode) + jebakan dicatat di `firmware/README.md` §Jebakan:
```cpp
SPI.begin(TFT_SCK, -1, TFT_MOSI);
pasang_buzzer();
```
