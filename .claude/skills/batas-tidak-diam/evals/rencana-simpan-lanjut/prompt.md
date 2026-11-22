---
tags: [batas-tidak-diam]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Skill, Write]
---

Repo `/home/mrrizaldi/dev/projek-akhir`, firmware ESP32-S3 di `firmware/`. Fakta: build `pio run -t upload` dari `firmware/`; serial 115200: `r` mulai/stop rekam, `j` jeda, `s` status dengan `sampel hilang <n>` (= `acquisition_missed()`), `l` daftar berkas (rekam hanya dari sensor ADC). Antrean ISR `QUEUE_N = 256` pada 360 Hz, `loop()` mengambil satu sampel per iterasi. Batas rekam `RECORDER_N = 360 * RECORDER_SECONDS` (RECORDER_SECONDS bawaan 300, build flag). LittleFS total 3456 KiB, terpakai 580 KiB; berkas CSV 300 detik sekitar 540 KB; menyimpan 540 KB dengan `f.printf` per sampel memakan sekitar 4 detik.

Rancang penyimpanan saat batas RECORDER_N tercapai, untuk rekaman yang berlanjut ke berkas baru tanpa kehilangan sampel, termasuk pesan ke user untuk pilihan yang mengubah pengalamannya. Tulis juga isi catatan dokumentasi untuk `firmware/README.md` (bagian dan kalimat).

Kamu tidak bisa menjalankan perintah atau menyunting repo. Tulis kode atau rencana dan pesan ke user sebagai teks. Bila butuh nilai dari keluaran yang belum kamu lihat, tulis [N].
