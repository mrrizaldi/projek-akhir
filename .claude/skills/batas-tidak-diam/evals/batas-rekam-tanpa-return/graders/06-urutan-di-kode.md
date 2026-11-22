---
type: llm
focus: trace
weight: 1
---

Kode yang ditulis menunjukkan urutannya: di jalur batas `aktif = false` (dan penanda kejadian) dahulu, lalu `Serial`, `display_message`, atau `display_sound` dipanggil dari `loop()` atau `recorder_service()`, bukan dari `recorder_sample`. Menyebut ulang aturannya tanpa kode berurutan tidak cukup.
