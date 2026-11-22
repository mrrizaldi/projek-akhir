---
type: llm
focus: trace
weight: 1
---

The file-write failure test matches the reported `missed` number against the difference of `acquisition_missed()` between `r` and the `REC stopped` line (before the first `SIMPAN`), and after the retry checks `lewat=0` in every rewritten file header.
