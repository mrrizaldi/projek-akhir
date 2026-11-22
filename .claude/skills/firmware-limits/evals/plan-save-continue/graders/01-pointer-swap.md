---
type: llm
focus: trace
weight: 1
---

The plan shows the pointer-swap design (a second buffer, the sample path only swaps pointers, no copy and no file operation on that path) and names its prerequisite, an IRAM-safe acquisition ISR, with how to measure it; recommending the single-buffer design while that prerequisite is unmet counts as long as the swap design is shown.
