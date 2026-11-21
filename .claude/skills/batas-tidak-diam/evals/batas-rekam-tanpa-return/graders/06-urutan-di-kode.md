---
type: llm
focus: trace
weight: 1
---

Kode yang ditulis menunjukkan urutannya: di jalur batas `aktif = false` (dan penanda kejadian) dahulu, lalu `Serial`, `tampilan_pesan`, atau `tampilan_bunyi` dipanggil dari `loop()` atau `rekam_layani()`, bukan dari `rekam_sampel`. Menyebut ulang aturannya tanpa kode berurutan tidak cukup.
