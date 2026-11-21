---
tags: [tanpa-komentar-kode]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Skill, Write]
---

Kita di `/home/mrrizaldi/dev/projek-akhir`. Di `firmware/src/rekam.cpp` aku punya potongan ini:

```c
// ukuran blok sekali tulis ke LittleFS
static const int BLOK = 256;
void tulis_blok(File &f, const uint16_t *d, size_t n)
{
    for (size_t i = 0; i < n; i += BLOK) f.write((const uint8_t *)(d + i), min((size_t)BLOK, n - i) * 2);
}
```

Rapikan sesuai aturan repo dan kembalikan potongan lengkapnya. Tulis juga grep yang kamu jalankan sebelum menamai konstanta, dan perintah pemeriksanya.

Kamu tidak bisa menjalankan perintah atau menyunting repo. Tulis potongan hasil dalam blok kode, lalu grep dan perintah pemeriksa persis seperti akan kamu ketik.
