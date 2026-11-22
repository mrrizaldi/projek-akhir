---
type: llm
focus: trace
weight: 1
---

The answer states a grep that covers `firmware/src/recorder.cpp` (or `firmware/src`) to find the existing constant, not only `firmware/include`, and uses the result: `SAMPLES_PER_WRITE` replaces `BLOCK` with no new definition.
