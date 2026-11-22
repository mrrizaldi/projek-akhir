---
name: tanpa-komentar-kode
description: Menulis dan menyunting kode di repo PA (firmware C/C++ ESP32, skrip Python model dan dashboard, shell, platformio.ini, generator header) tanpa komentar dan tanpa docstring, memakai nama konstanta yang sudah ada di repo, menaruh penjelasan di dokumen komponen yang tepat, dan memeriksanya dengan scripts/cek_komentar.py. Pakai setiap kali user meminta menambah, mengubah, atau memperbaiki kode di repo ini, misalnya "tambah fitur bip tolak", "ubah ambang jadi 80", "tulis skrip analisis", "edit main.cpp", "buat generator header", "ganti pin buzzer", "add a function to firmware", "write a script in model/scripts", dan saat menulis prompt untuk subagen yang akan menulis kode di repo ini.
---

# Tanpa komentar kode (repo PA)

Muat skill user `no-code-comments` lebih dulu; skill ini hanya menambah hal khusus repo PA. Skill itu memuat aturan umumnya: literal dan indeks bernama, argumen CLI bernama, grep nama dan nilai sebelum menamai, include header alih-alih definisi ulang, generator tanpa komentar, perubahan nilai ditunjukkan di berkasnya, pengecualian `##` di Makefile, dan brief subagen dengan `cd` absolut. Di bawah hanya yang berbeda di repo ini.

## Pemeriksa

Jalankan dari root repo pada berkas yang disentuh, dan serahkan hanya bila keluar 0. Alasannya: pemeriksa skill user tidak memindai C/C++, sedangkan pemeriksa repo memindainya.

```bash
cd /home/mrrizaldi/dev/projek-akhir && python3 scripts/cek_komentar.py <berkas>...
```

CI menjalankannya untuk seluruh repo lewat `.github/workflows/cek.yml`. Pelanggaran di berkas yang tidak kamu sentuh cukup dilaporkan; menyunting berkas di luar lingkup tugas bukan solusinya.

## Bentuk komentar di repo ini

- `platformio.ini` memakai `;` dan `#` untuk komentar, dan keduanya dilarang. Opsi yang butuh penjelasan dijelaskan di `firmware/README.md` §Environment PlatformIO.
- Teks bantuan CLI yang dicetak program (string argparse) dan target `##` di Makefile boleh ada; `__doc__` dan docstring tidak.

## Nama yang sudah ada di repo

Konstanta bersama tinggal di header `firmware/include/` (mis. `THRESHOLD_SWING` di `gate.h`, `TONE_HZ` di `board.h`), jadi cari dulu dengan `grep -rn "AMBANG\|BIP_\|NADA_" firmware/include firmware/src model/config.py` dan include header-nya, jangan definisikan ulang. Konstanta `BIP_*_MS` bersifat lokal per berkas (`display.cpp`, `recorder.cpp`, `gate.cpp`, `main.cpp`), jadi baca prefiks konstanta di berkas tujuan sebelum menamai. Nilai model (FS, window, ambang) ada di `model/config.py`; pakai dari sana, bukan salinan. Nama yang ada dengan arti lain (`BEEP_REJECT_MS` di `display.cpp` adalah lama bip, bukan jeda) jangan dipakai ulang atau ditiru dengan nama mirip, karena firmware satu namespace.

Literal yang dikirim ke API driver diberi nama yang menyebut efeknya, mis. `LEVEL_PIN_DIAM_HIGH` untuk level pin saat buzzer diam, bukan `1` dan bukan nama internal seperti `..._TERBALIK`. Alasannya: buzzer modul aktif LOW, jadi arti angka 1 tidak terbaca dari kodenya.

## Ke dokumen mana penjelasan pergi

Baca bagian tujuan dulu dan jangan menggandakan isinya; rujuk yang sudah ada.

| Sumber kode | Dokumen tujuan |
|---|---|
| Jebakan firmware | `firmware/README.md` §Jebakan (bagian sudah ada; bukan §Pin map) |
| Port, golden, TFLM | `model/docs/firmware-walkthrough.md` (masih aktif, dirujuk `firmware/README.md`) |
| Pipeline model | walkthrough tahapnya di `model/docs/` (peta di `model/docs/README.md`, mis. `features-rr-walkthrough.md`); keputusan di `model/CLAUDE.md` |
| Skrip `model/scripts/` | `model/README.md` §Skrip |
| Skrip `scripts/` | `scripts/README.md` |
| Dashboard | `dashboard/README.md` |

Di §Jebakan firmware, satu butir masuk ke satu sub-daftar sesuai subsistemnya, karena butir yang melintas subsistem sulit ditemukan lagi. Sub-daftar yang ada: Perangkat, Akuisisi dan pipeline, TFLite Micro, Jaringan dan jam, LittleFS (cek dengan `grep -n "^\*\*" firmware/README.md`).

- **Akuisisi dan pipeline**: perilaku loop, ISR, antrean, buzzer yang memblok `loop()`.
- **Perangkat**: pin, buzzer, layar, LED, INA219 (contoh: `SPI.begin` harus sebelum `attach_buzzer` karena SPI merebut GPIO13).

Tambahkan bagian baru hanya bila tidak ada satu pun sub-daftar yang cocok.

## Klaim di dokumen

Setiap klaim yang kamu tulis ke dokumen dicek dulu ke kodenya (buka berkas, grep nomor baris, jalankan bila bisa), karena dokumen repo menjadi acuan kerja berikutnya. Yang belum terukur di perangkat ditulis "belum diverifikasi di board", dan kalimat itu tidak boleh bertentangan dengan premis tugas.

## Brief subagen

Salin aturan tanpa komentar secara eksplisit ke prompt, dan beri perintah pemeriksa yang berdiri sendiri:

```bash
cd /home/mrrizaldi/dev/projek-akhir && python3 scripts/cek_komentar.py <berkas-yang-disentuh>
```

Tunjuk bagian dokumen tujuan dari tabel di atas, dan tandai klaim yang belum terukur di board sebagai "belum diverifikasi di board" di dalam prompt. Uji tiap perintah di prompt persis seperti tertulis sebelum menyerahkannya.

## Contoh

Kode tetap bersih, jebakannya masuk `firmware/README.md` §Jebakan, sub-daftar Perangkat:

```cpp
SPI.begin(TFT_SCK, WITHOUT_MISO, TFT_MOSI);
attach_buzzer();
```
