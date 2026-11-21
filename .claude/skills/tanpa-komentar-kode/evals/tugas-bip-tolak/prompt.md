---
tags: [tanpa-komentar-kode]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Skill, Write]
---

Kita di `/home/mrrizaldi/dev/projek-akhir`. Tulis prompt untuk subagen yang akan menambah fitur "bip tolak" (dua bip pendek saat tombol ditolak) di firmware. Di `firmware/src/tampilan.cpp` sudah ada `BIP_TOLAK_MS = 150` (lama satu bip) dan `tampilan_bunyi(ms)`. Jebakannya: LEDC harus dilepas sesudah bunyi supaya pin kembali HIGH (buzzer aktif LOW), dan fungsi ini tidak boleh memblok `loop()`.

Kamu tidak bisa menjalankan perintah atau menyunting repo. Tulis isi prompt subagen utuh dalam satu blok kode.
