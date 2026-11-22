---
type: llm
focus: trace
weight: 1
---

The duration of each save chunk and of each attempt (retry attempts included) has a value and a formula and is compared with 711 ms; an I/O duration not yet measured may be written `[N]` as long as it is added to the chunk time and that sum is compared with 711 ms. The retry interval and wait cap only need to be shown not to block (a `millis()`-based schedule in `loop()`); they need not be compared with 711 ms.
