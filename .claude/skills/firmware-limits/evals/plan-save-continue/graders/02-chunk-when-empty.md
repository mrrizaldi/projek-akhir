---
type: llm
focus: trace
weight: 1
---

Saving is split per chunk in `loop()` and runs only when `acquisition_fill() == 0`.
