---
type: llm
focus: trace
weight: 1
---

The sample path (`recorder_sample` and what it calls) does not call Serial, `display_message`, `display_sound`, `LittleFS.open`, or write a file; those run from `loop()` or `recorder_service()`.
