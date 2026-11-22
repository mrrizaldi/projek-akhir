---
name: kicad-pcb
description: PA repo layer for KiCad PCB and schematic work in hardware/mainboard. Use when creating, editing, routing, or checking the PA mainboard PCB, schematic, netlist, DRC, or Gerber, when reading KiCad files a friend sent, or when the user types "bikin PCB", "rute ulang mainboard", "check_board", "layout.py", "tuang zona", "profil JLCPCB", "lebar jalur", "autoroute gagal", "ubah pin PCB", "skematik tidak kebaca KiCad", "re-route the mainboard", "pour zones", "change a PCB pin". Loads the user skill kicad-mcp-pcb first, then adds the file locations, checker scripts, JLCPCB profile, power net list, and footprint notes of the PA board. Not for firmware or the report.
---

# KiCad PCB (PA layer)

Load the user-scope skill `kicad-mcp-pcb` first; this skill adds only what is specific to the PA repo.

## Documents to read before asking the user

Read `hardware/mainboard/README.md` (pin map, header pin order, power supply, layout, netclasses, footprint, the "Not yet verified" list) and `firmware/include/board.h` (the single firmware pin map). Ask the user only about choices neither of them settles, because design decisions belong to the user. The question carries one recommendation that is chosen now; missing data is written as "changes to X if ...", not as a postponed choice, because postponing the choice repeatedly stalls the work. Any fact the answer relies on that nobody has measured (LED forward voltage, module dimensions) is named as going into README §Not yet verified, because an unrecorded assumption is lost after the session.

## Locations

All board files are in `hardware/mainboard/`:

| File | Purpose |
|---|---|
| `mainboard.kicad_pro`, `.kicad_sch`, `.kicad_pcb` | KiCad 9.0.2 project; netclasses are in `.kicad_pro` |
| `layout.py` | layout tool, run with `/usr/bin/python3` from `hardware/mainboard/` |
| `check_board.py` | the checker that decides "done" |
| `check_layout.py` | pcbnew checker (width, courtyard, text), called by `check_board.py` |
| `export_fab.sh` | JLCPCB Gerber zip |

Save every new layout script as a command in `layout.py`, not in the scratchpad, because this board has been re-routed several times and the scratchpad is lost between sessions.

KiCad 10 files from a friend are read as text only. The friend's rev2 schematic (KiCad 10.0.6, empty PCB) is only a circuit reference; its differences from this mainboard are in the README table §Differences from the rev2 schematic.

## `layout.py` commands

The full re-route sequence (README §Changing the design), run from `hardware/mainboard/`: `hapus`, `rute`, `tuang`, then Freerouting through the kicad MCP server (`open_project`, `autoroute`), then `bersih`, `solid`, `teks`, `ukiran`, `tuang`, then `python3 check_board.py`. The order matters because the cleanup, solid pads, text and engraving all change copper that the final pour and DRC must see.

Run `tuang` as its own step right before every `kicad-cli pcb drc`, because `kicad-cli` does not pour zones:

```bash
cd hardware/mainboard
/usr/bin/python3 layout.py tuang
kicad-cli pcb drc --schematic-parity --severity-all -o /tmp/drc.rpt mainboard.kicad_pcb
```

When DRC reports `unconnected`, add the remaining connections to the `rute_*` functions in `layout.py` and repeat the sequence from `hapus` (README §Changing the design), because Freerouting can report success while leaving connections open.

Apply schematic changes to the board with a pcbnew script as the user skill describes ("Net names match the schematic"), not F8 and not `sync_schematic_to_board`, so net names stay `/NAME`.

## Done = `check_board.py` PASSES

```bash
cd hardware/mainboard
/usr/bin/python3 layout.py tuang
cd ../..
python3 hardware/mainboard/check_board.py
```

`tuang` runs first because `check_board.py` calls `kicad-cli pcb drc` (`check_board.py` line 86), and `kicad-cli` does not pour zones, so DRC over empty zones gives a false result.

What it checks: the pin map against the netlist (`PIN_U1` and `PIN_LAIN` in the script), `+5V` touching only `U1`, `C1`, `C2`, `D2` (`BOLEH_5V`), ERC, DRC errors, unconnected, schematic parity, then `check_layout.py` (width per netclass, courtyard at least 1 mm, text). The expected last line is `LULUS` (pass); paste its output into the commit message.

Update `PIN_U1` and `PIN_LAIN` together with `firmware/include/board.h` and the pin map table in the README (§Pin map) whenever a pin moves, because the script exits with code 1 if even one pin deviates from the map. When `check_board.py` or `check_layout.py` changes, add one negative test (a deliberately broken board must fail).

## JLCPCB profile: "technical ideal"

This profile is the user's choice: width from the IPC-2221 current requirement, spacing and ring from JLCPCB recommendations, not JLCPCB minimums. A thicker profile or another fabrication method is asked about first.

| Netclass | Nets | Width | Clearance | Via (pad/hole) |
|---|---|---|---|---|
| `Default` | digital signals, `+3V3`, GND | 0.3 mm | 0.35 mm | 0.9/0.4 mm |
| `ECG` | `/ECG_*` | 0.4 mm | 0.35 mm | 0.9/0.4 mm |
| `Power` | power nets below | 1.0 mm | 0.35 mm | 1.2/0.6 mm |

Power nets (netclass `Power`): `/+5V /VBOOST /VSYS /VSW /VCHG /VBAT_OUT /VBAT_SENSE /BAT+ /BAT-`. Gate branches and stubs on these nets follow 1.0 mm. The Q1 gate branch carries `/VCHG` (J4 IN+), so it is a Power trace at 1.0 mm, because a charger current path routed thin is the failure this rule prevents. `+3V3` (the DevKit regulator output, low current) belongs to `Default`, so 0.3 mm.

PTH ring at least 0.25 mm, courtyard spacing at least 1.0 mm, silkscreen reference at least 1.0 mm. Between two pins in one U1 column (pitch 2.54 mm) a `+3V3` trace needs a gap of 0.3 + 2 x 0.35 = 1.0 mm; an oval U1 pad of 2.0 x 1.5 mm leaves 1.04 mm.

## Footprint notes and unproven items

A change to a footprint pad shape is recorded in `hardware/mainboard/README.md` §ESP32-S3-DevKitC-1 footprint. Dimensions, module pin order, mechanical space, and circuit behavior not yet tested go into §Not yet verified in the same README, with how to check each item.
