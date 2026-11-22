---
type: llm
focus: trace
weight: 1
---

Jalur sampel (`recorder_sample` dan yang dipanggilnya) tidak memanggil Serial, `display_message`, `display_sound`, `LittleFS.open`, atau tulis berkas; itu dijalankan dari `loop()`/`recorder_service()`.
