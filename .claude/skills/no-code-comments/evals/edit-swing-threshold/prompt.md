---
tags: [no-code-comments]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Skill, Write]
---

Kita di `/home/mrrizaldi/dev/projek-akhir`. Di `firmware/include/gate.h` sudah ada `constexpr int THRESHOLD_SWING = 60;`. Aku punya potongan ini di `firmware/src/signal_check.cpp`:

```c
// Ambang ayunan minimum (count ADC) agar sinyal dianggap tersambung.
static const int THRESHOLD = 60;
/* Dipanggil tiap 1 detik dari loop utama. */
bool signal_ok(int swing)
{
    return swing >= THRESHOLD; // bandingkan dengan ambang
}
// TODO: jadikan konfigurasi NVS
```

Ubah ambangnya jadi 80 dan kembalikan potongan lengkapnya. Sebutkan juga perintah pemeriksa yang kamu jalankan sebelum menyerahkan.

Kamu tidak bisa menjalankan perintah atau menyunting repo. Tulis potongan hasil dalam blok kode, lalu tulis perintah pemeriksa persis seperti akan kamu ketik.
