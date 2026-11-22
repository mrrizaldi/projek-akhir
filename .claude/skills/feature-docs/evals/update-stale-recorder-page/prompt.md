---
tags: [feature-docs]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Skill, Write]
---

I changed the recorder in the PA firmware. Update `docs/features/recording.md` to match.

You cannot run commands or read the repo beyond what is pasted here. Write the new text of the page sections you change (or a unified diff), the exact commands you would run, and your final report. Write any command output you cannot see as [N].

## What I changed in the code

- The maximum recording length is now 300 seconds (`REKAM_DETIK = 300`), was 180.
- When the buffer reaches `REKAM_N` the recorder now stops and saves instead of overwriting; `rekam_simpan` is called from the stop path.
- Nothing else in the recorder changed. Lines moved, so the old line numbers are wrong.

## grep output I already ran

```
$ grep -n "REKAM_DETIK\|REKAM_N\|void rekam_mulai\|void rekam_simpan\|---MULAI---" firmware/src/rekam.cpp
31:constexpr uint32_t REKAM_DETIK = 300;
32:constexpr size_t REKAM_N = REKAM_DETIK * ECG_FS;
88:void rekam_mulai(void)
140:void rekam_simpan(void)
279:    Serial.println("---MULAI---");
$ sed -n 140,146p firmware/src/rekam.cpp
void rekam_simpan(void)
{
    if (!sedang_rekam) return;
    sedang_rekam = false;
    if (n_sampel == 0) return;
    File f = LittleFS.open(nama_berkas, "w");
    if (!f) { tampilan_pesan("GAGAL SIMPAN", "tekan r ulangi"); return; }
```

## Current page excerpt (`docs/features/recording.md`)

```markdown
## Limits and storage

`firmware/src/rekam.cpp`, started from the menu or serial `r`:

| Item | Details |
|---|---|
| Maximum length (`REKAM_DETIK`, `:24`) | 180 s at `ECG_FS`, buffer `REKAM_N` (`:25`). Since 20 Okt 2026 a full buffer no longer overwrites old samples: the recorder stops and calls `rekam_simpan` (`:131`). |
| Start (`rekam_mulai`, `:80`) | Clears the buffer and the dropped-sample counter, then begins sampling into the buffer. |
| Save (`rekam_simpan`, `:131`) | Writes the file to LittleFS and prints a `SIMPAN` line. The save usually takes about 2 seconds. A failed open shows "GAGAL SIMPAN" (save failed) on the TFT. |

## Serial dump

`rekam_dump` (`firmware/src/rekam.cpp:270`) prints `---MULAI---`, the header and one sample per line so a PC script can capture it.

**Code:** `firmware/include/rekam.h` · `firmware/src/rekam.cpp` · `firmware/src/serial_cmd.cpp`
```
