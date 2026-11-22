---
type: llm
focus: trace
weight: 1
---

Each test has a literal build command with `-DRECORDER_SECONDS=<number>` (not "same as the previous test") before the serial commands. The real 300 second test may use the default build without the flag (`pio run -t upload`) as long as the command is literal.
