# Cross-component documentation

## Features

One page per feature: how it works, its interfaces and limits, with `file:line`
pointers into the code. Rules for writing them: `.claude/skills/feature-docs/SKILL.md`.

| Page | Content |
|---|---|
| [architecture](features/architecture.md) | System overview: one loop plus one timer ISR on the ESP32-S3, the module map, and the model and dashboard sides |
| [acquisition](features/acquisition.md) | 360 Hz timer ISR into the sample queue, lost-tick counting, the three signal sources, board bring-up and pins |
| [signal-pipeline](features/signal-pipeline.md) | Causal bandpass, Pan-Tompkins R detection once per second, z-scored beat window and RR features, matched to Python by the golden reference |
| [classification](features/classification.md) | INT8 TFLite Micro inference per beat and the hand-off of results to MQTT |
| [calibration-gate](features/calibration-gate.md) | Per-second signal quality, electrode contact and the calibration, good and bad phases that decide what is classified and published |
| [display-and-buzzer](features/display-and-buzzer.md) | TFT monitor and menu frame, NeoPixel, and the sample-scheduled beat beep |
| [buttons-and-menu](features/buttons-and-menu.md) | Button events, the monitor button map and the on-device menu tree |
| [recording](features/recording.md) | Raw recording into PSRAM, numbered LittleFS files written after the session, session lock, file format and pulling |
| [network-settings](features/network-settings.md) | WiFi and broker lists from `wifi_secrets.h`, NVS persistence, server setup and troubleshooting |
| [serial-commands](features/serial-commands.md) | Single-letter serial commands, the headless twin of the buttons and menu |
| [mqtt-telemetry](features/mqtt-telemetry.md) | PSRAM backlog ring, the hand-written MQTT client, payload and the ThingsBoard side |
| [power-measurement](features/power-measurement.md) | INA219 on the battery side, the `p0` to `p5` power sweep, validity rules and pulling results |
| [diagnostics](features/diagnostics.md) | Shared `diag_*` device self-tests for the menu and the `test_hw_*` suites, and the PC and board test suites |
| [model-pipeline](features/model-pipeline.md) | Python pipeline from MIT-BIH to the INT8 model and the generated firmware headers |

## Working documents

**Content:** documents that are **still valid and in progress**: work lists,
research whose action has not been decided, and unfinished plans. Documents in
this folder may be updated.
**History:** finished documents are deleted; their history is in git. Old plans
are in the git tag `pra-bersih`; trimmed archive documents can be restored from
the parents of commits `0c87f78` (`docs/arsip/`) and `830bd3e`
(`model/docs/arsip/`) with `git show <commit>^:<path>`.

| Date | Document | Content | Status |
|---|---|---|---|
| 2026-11-01 | [target-gaps](2026-11-01-target-gaps.md) | Gaps against the Chapter 1, Chapter 3 and PRD targets: targets not yet measured, targets with narrow coverage, open firmware findings | Active work list; items struck out when closed |
| 2026-11-01 | [bab4-metrics-crosscheck](2026-11-01-bab4-metrics-crosscheck.md) | Crosscheck of Chapter 4 metrics and measurement methods against standards (AAMI EC57, MLPerf Tiny, IEC 60601, IETF IPPM, ITU-T G.1010/H.810), detailed reports per category in the subfolder | A4 to A8 applied in `progres-pa-1`; A9, B and the pipeline and power items deferred (section 4) |
| 2026-11-21 | [skill-anti-slop](2026-11-21-skill-anti-slop.md) | Candidate external skills for report writing without AI writing patterns, their conflicts with repo rules, and the plan to distil them into `narasi-pa` | progres-pa-1 Chapter 2 to 4 trial done, skill eval 10/10; awaiting user review, remainder in §Remaining work |
| 2026-11-21 | [deferred-work](2026-11-21-deferred-work.md) | Single list of work not yet executed from the Word pipeline, anti-slop, release and skill sessions | In progress |
| 2026-11-21 | [skill-codebase-rework](2026-11-21-skill-codebase-rework.md) | Skill rework (extraction to the user skill repo, skill-creator eval format, CI validator) and cleanup of docs and code | Waves 0 to 4 done; remainder in deferred-work |
| 2026-11-22 | [english-codebase](2026-11-22-english-codebase.md) | Codebase, docs, and skills to English with equivalence-proven renames; per-feature docs via `feature-docs` | Phases 0-3, 5 and the hardware scripts done and on `main`; open: 4.1 English serial log (needs the board), firmware-limits 711 ms rule, Phase 7 cleanup (delete `scripts/renames.py`, maps, glossary and this plan after 4.1) |

## When a working document is finished

1. All its actions are done or rejected by the user, and the results are
   recorded in the valid documents (component README, walkthrough, `CLAUDE.md`,
   or the report).
2. First move the facts that still apply (data locations, recovery steps,
   configuration values) to the component README or walkthrough.
3. Delete the file (with user approval) and its row in the index table.
