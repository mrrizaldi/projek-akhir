---
name: no-code-comments
description: Write and edit code in the PA repo (ESP32 C/C++ firmware, Python model and dashboard scripts, shell, platformio.ini, header generators) with no comments and no docstrings, reusing constant names that already exist in the repo, putting explanations into the right component doc, and verifying with scripts/check_comments.py. Use whenever the user asks to add, change, or fix code in this repo, for example "tambah fitur bip tolak", "ubah ambang jadi 80", "tulis skrip analisis", "edit main.cpp", "buat generator header", "ganti pin buzzer", "add a function to firmware", "write a script in model/scripts", and when writing a prompt for a subagent that will write code in this repo.
---

# No code comments (PA repo layer)

Load the user-scope skill of the same name (`~/.claude/skills/no-code-comments`) first; this repo layer adds only what is specific to the PA repo. The user skill holds the general rules: named literals and indexes, named CLI arguments, grep for names and values before naming, include a header instead of redefining, comment-free generators, a value change shown in the file that owns it, the Makefile `##` exception, and subagent briefs with an absolute `cd`. Below is only what differs here.

## Checker

Run it from the repo root on every file you touched and hand the work over only when it exits 0. Reason: the user skill's checker does not scan C/C++, and the repo checker does.

```bash
cd /home/mrrizaldi/dev/projek-akhir && python3 scripts/check_comments.py <file>...
```

CI runs it for the whole repo through `.github/workflows/checks.yml`. A violation in a file you did not touch is reported, not fixed: editing files outside the task scope is not the remedy.

## Comment forms in this repo

- `platformio.ini` uses `;` and `#` for comments, and both are banned. An option that needs an explanation is explained in `firmware/README.md` §PlatformIO environments.
- Help text a program prints (argparse strings) and Makefile `##` targets are allowed; `__doc__` and docstrings are not.

## Names that already exist in the repo

Shared constants live in the headers of `firmware/include/` (for example `THRESHOLD_SWING` in `gate.h`, `TONE_HZ` in `board.h`), so search first with `grep -rn "THRESHOLD\|BEEP_\|TONE_" firmware/include firmware/src model/config.py` and include the header instead of redefining. The `BEEP_*_MS` constants are local to each file (`display.cpp`, `recorder.cpp`, `gate.cpp`, `main.cpp`), so open the target file and read its constants before naming one; when a constant with the same value or meaning already exists there (for example `SAMPLES_PER_WRITE` in `recorder.cpp`), use it instead of adding a new name, because two names for one value drift apart. Model values (FS, window, thresholds) are in `model/config.py`; use them from there, never a copy. A script in `model/scripts/` reaches `config` the way its sibling scripts do: `sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))` before `from config import ...`, because Python puts the script's own folder on the path, not `model/`. A name that exists with another meaning (`BEEP_REJECT_MS` in `display.cpp` is a beep length, not a gap) is not reused or imitated with a similar name, because the firmware is one namespace.

A literal passed to a driver API is named for its effect, for example `TONE_IDLE` (`board.cpp`) for the buzzer tone value that leaves the pin silent, and `WITHOUT_MISO` for the unused SPI pin, not `0` or `-1`. Reason: the buzzer module is active LOW, so the meaning of a bare number cannot be read from the code.

## Where explanations go

Read the target section first and do not duplicate its content; link to what is already there.

| Code source | Target doc |
|---|---|
| Firmware pitfalls | `firmware/README.md` §Pitfalls (an existing section; not the pin map) |
| One firmware feature (behavior, interfaces, limits) | its page in `docs/features/` (list in `docs/README.md`) |
| Port, golden, TFLM | `model/docs/firmware-walkthrough.md` |
| Model pipeline | the stage walkthrough in `model/docs/` (map in `model/docs/README.md`, for example `features-rr-walkthrough.md`); decisions in `model/CLAUDE.md` |
| `model/scripts/` scripts | `model/README.md` §Scripts |
| `scripts/` scripts | `scripts/README.md` |
| Dashboard | `dashboard/README.md` |

In §Pitfalls, one item goes into one sub-list by subsystem, because an item that spans subsystems is hard to find again. The sub-lists are Device, Acquisition and pipeline, TFLite Micro, Network and clock, and LittleFS (check with `grep -n "^\*\*" firmware/README.md`).

- **Acquisition and pipeline**: loop behavior, ISR, queue, a buzzer that blocks `loop()`.
- **Device**: pin, buzzer, display, LED, INA219 (example: `SPI.begin` must come before `attach_buzzer` because SPI takes GPIO13).

Add a new section only when no sub-list fits.

## Claims in docs

Check every claim you write into a doc against the code first (open the file, grep the line, run it when you can), because repo docs become the reference for the next piece of work. What is not yet measured on the device is written "not verified on a board", and that sentence must not contradict the task's premise.

## Subagent brief

Copy the no-comment rule into the prompt explicitly, and give a self-contained checker command:

```bash
cd /home/mrrizaldi/dev/projek-akhir && python3 scripts/check_comments.py <touched-file>
```

Point to the target doc section from the table above, and mark any claim not yet measured on a board as "not verified on a board" inside the prompt. Run every command in the prompt exactly as written before handing it over.

## Example

The code stays clean, and the pitfall goes into `firmware/README.md` §Pitfalls, Device sub-list:

```cpp
SPI.begin(TFT_SCK, WITHOUT_MISO, TFT_MOSI);
attach_buzzer();
```
