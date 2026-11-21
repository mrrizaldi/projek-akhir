---
type: llm
focus: trace
weight: 1
---

Durasi tiap potongan simpan dan tiap percobaan (termasuk percobaan coba ulang) punya nilai dan rumus dan dibandingkan dengan 711 ms. Selang coba ulang dan batas tunggu cukup terbukti tidak memblok (jadwal berbasis `millis()` di `loop()`), tidak perlu dibandingkan dengan 711 ms.
