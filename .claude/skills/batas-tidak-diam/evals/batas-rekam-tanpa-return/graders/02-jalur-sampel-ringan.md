---
type: llm
focus: trace
weight: 1
---

Jalur sampel (`recorder_sample` dan yang dipanggilnya) tidak memanggil Serial, `tampilan_pesan`, `tampilan_bunyi`, `LittleFS.open`, atau tulis berkas; itu dijalankan dari `loop()`/`recorder_service()`.
