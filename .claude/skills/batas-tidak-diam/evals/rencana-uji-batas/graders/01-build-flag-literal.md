---
type: llm
focus: trace
weight: 1
---

Tiap uji memuat perintah build literal dengan `-DREKAM_DETIK=<angka>` (bukan "sama dengan uji sebelumnya") sebelum perintah serial. Uji batas asli 300 detik boleh memakai build tanpa flag (`pio run -t upload` bawaan) asalkan perintahnya literal.
