---
type: llm
focus: trace
weight: 1
---

The code written shows the order: on the limit path `active = false` (and the event marker) first, then `Serial`, `display_message`, or `display_sound` called from `loop()` or `recorder_service()`, not from `recorder_sample`. Restating the rule without ordered code is not enough.
