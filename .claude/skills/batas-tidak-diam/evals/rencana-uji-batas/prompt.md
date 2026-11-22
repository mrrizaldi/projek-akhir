---
tags: [batas-tidak-diam]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Skill, Write]
---

Repo `/home/mrrizaldi/dev/projek-akhir`, firmware ESP32-S3 di `firmware/`. Fakta: build `pio run -t upload` dari `firmware/`; serial 115200: `r` mulai/stop rekam, `j` jeda, `s` status dengan `sampel hilang <n>` (= `acquisition_missed()`), `l` daftar berkas (rekam hanya dari sensor ADC). Antrean ISR `QUEUE_N = 256` pada 360 Hz, `loop()` mengambil satu sampel per iterasi. Batas rekam `RECORDER_N = 360 * RECORDER_SECONDS` (RECORDER_SECONDS bawaan 300, build flag). LittleFS total 3456 KiB, terpakai 580 KiB; berkas CSV 300 detik sekitar 540 KB; menyimpan 540 KB dengan `f.printf` per sampel memakan sekitar 4 detik.

Skenario: rekaman berlanjut ke berkas baru tiap RECORDER_SECONDS detik (maksimum 6 bagian). Tulis rencana uji batasnya: perintah dan angka yang diperiksa. Tulis juga uji untuk jalur gagal tulis berkas.

Kamu tidak bisa menjalankan perintah atau menyunting repo. Tulis kode atau rencana dan pesan ke user sebagai teks. Tanda [N] hanya untuk keluaran perintah build yang belum kamu lihat; baris harapan uji ditulis dengan angka pasti.
