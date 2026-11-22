---
tags: [feature-docs]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Skill, Write]
---

I changed the recorder in the PA firmware. Update `docs/features/recording.md` to match.

You cannot run commands or read the repo beyond what is pasted here. Write the new text of the page sections you change (or a unified diff), the exact commands you would run, and your final report. Write any command output you cannot see as [N].

## What I changed in the code

- The maximum recording length is now 300 seconds (`RECORDER_SECONDS = 300`), was 180.
- When the buffer reaches `RECORDER_N` the recorder now stops and saves instead of overwriting; `recorder_save` is called from the stop path.
- Nothing else in the recorder changed. Lines moved, so the old line numbers are wrong.

## grep output I already ran

```
$ grep -n "RECORDER_SECONDS\|RECORDER_N\|void recorder_start\|void recorder_save\|---MULAI---" firmware/src/recorder.cpp
31:constexpr uint32_t RECORDER_SECONDS = 300;
32:constexpr size_t RECORDER_N = RECORDER_SECONDS * ECG_FS;
88:void recorder_start(void)
140:void recorder_save(void)
279:    Serial.println("---MULAI---");
$ sed -n 140,146p firmware/src/recorder.cpp
void recorder_save(void)
{
    if (!recording) return;
    recording = false;
    if (n_samples == 0) return;
    File f = LittleFS.open(file_path, "w");
    if (!f) { display_message("GAGAL SIMPAN", "tekan r ulangi"); return; }
```

## Current page excerpt (`docs/features/recording.md`)

```markdown
## Limits and storage

`firmware/src/recorder.cpp`, started from the menu or serial `r`:

| Item | Details |
|---|---|
| Maximum length (`RECORDER_SECONDS`, `:24`) | 180 s at `ECG_FS`, buffer `RECORDER_N` (`:25`). Since 20 Okt 2026 a full buffer no longer overwrites old samples: the recorder stops and calls `recorder_save` (`:131`). |
| Start (`recorder_start`, `:80`) | Clears the buffer and the dropped-sample counter, then begins sampling into the buffer. |
| Save (`recorder_save`, `:131`) | Writes the file to LittleFS and prints a `SIMPAN` line. The save usually takes about 2 seconds. A failed open shows "GAGAL SIMPAN" (save failed) on the TFT. |

## Serial dump

`recorder_dump` (`firmware/src/recorder.cpp:270`) prints `---MULAI---`, the header and one sample per line so a PC script can capture it.

**Code:** `firmware/include/recorder.h` · `firmware/src/recorder.cpp` · `firmware/src/serial_cmd.cpp`
```
