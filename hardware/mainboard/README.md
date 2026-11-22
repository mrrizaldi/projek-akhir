# Mainboard (PCB rev2)

KiCad project for the device's main board: ESP32-S3-DevKitC-1 N16R8, AD8232,
1.47" ST7789 TFT, INA219, passive buzzer module, three buttons, and an 18650
battery supply path (TP4056 + MT3608 boost) with an on-off switch. All modules
are mounted through 2.54 mm headers. Two-layer board, 110 × 103 mm.

Status: schematic and layout are complete, and the automatic checks pass (see
**Checks**). Not yet fabricated, and the items in **Not yet verified** must be
checked on the physical modules before the Gerbers are sent.

## Files

| File | Contents |
|---|---|
| `mainboard.kicad_pro`, `.kicad_sch`, `.kicad_pcb` | KiCad 9.0.2 project |
| `lib/PA.kicad_sym`, `lib/PA.pretty/` | ESP32-S3-DevKitC-1 symbol and footprint (project library, referenced through `${KIPRJMOD}`) |
| `cek_board.py` | netlist, ERC, DRC, and schematic–PCB parity checks; calls `cek_tata_letak.py` |
| `cek_tata_letak.py` | pcbnew checks (`/usr/bin/python3`): trace width per netclass, courtyard spacing ≥ 1 mm, front and back text |
| `tata_letak.py` | layout tool (`/usr/bin/python3`): locked positions, manual routing, cleanup after autoroute, solid GND pads, zone pour, text placer, engraving |

The files are made with KiCad 9.0.2 and can be opened in KiCad 10. The reverse
does not work: KiCad 10 files (for example the rev2 schematic authored with
KiCad 10.0.6) are rejected by KiCad 9 with the message `Failed to load schematic`.

## Pin map

Same as `firmware/include/board.h`. The U1 pad numbers follow the official
Espressif footprint: pads 1–22 are the left column from the top (3V3 … GND),
pads 23–44 are the right column from the bottom (GND … GND). The physical
order of both columns has been matched 44/44 against the official
ESP32-S3-DevKitC-1 pinout drawing.

| Function | GPIO | U1 pad | Net | Destination |
|---|---|---|---|---|
| EKG OUT / LO− / LO+ | 1 / 2 / 42 | 41 / 40 / 39 | `ECG_OUT` / `ECG_LON` / `ECG_LOP` | J3 pin 3 / 4 / 5 |
| TFT SCK / MOSI | 9 / 8 | 15 / 12 | `TFT_SCK` / `TFT_MOSI` | J2 pin 3 / 4 |
| TFT RES / DC | 10 / 11 | 16 / 17 | `TFT_RST` / `TFT_DC` | J2 pin 5 / 6 |
| Buzzer | 13 | 19 | `BUZZ` | J9 pin 2 |
| Button 1 / 2 / 3 | 4 / 5 / 6 | 4 / 5 / 6 | `BTN1..3` | SW1..3 to GND |
| INA219 SDA / SCL | 17 / 18 | 10 / 11 | `I2C_SDA` / `I2C_SCL` | U2 pin 4 / 3 |
| 3V3 | – | 1, 2 | `+3V3` | all module VCC, AD8232 SDN, TFT BLK |
| 5V | – | 21 | `+5V` | D2 output |
| GND | – | 22, 23, 24, 44 | `GND` | all DevKit GND pins connected |

Module header pin order:

| Ref | Module | Pin 1 → n |
|---|---|---|
| J3 | AD8232 | GND, 3V3, OUT, LO−, LO+, SDN |
| J2 | TFT ST7789 | GND, VCC, SCL, SDA, RES, DC, CS, BLK (CS to GND, BLK to 3V3) |
| U2 | INA219 | VCC, GND, SCL, SDA, VIN−, VIN+ |
| J9 | buzzer A18009 | GND, I/O, VCC |
| J1 | boost MT3608 | VIN+, VIN−, VOUT+, VOUT− |
| J10 | illuminated on-off switch (in the enclosure) | input (VSYS), output to boost (VSW), lamp GND |
| J4 / J5 / J6 | TP4056 | IN+ IN− / B+ B− / OUT+ OUT− |
| J8 | 18650 holder cable (JST PH) | +, − |

GPIOs to avoid when moving pins: 26–37 (flash and octal PSRAM of the N16R8),
0/3/45/46 (strapping), 19/20 (USB). EKG is on GPIO 1 because it is an ADC1
channel; ADC2 cannot be used while WiFi is active. GPIO 12 is free.

## Power supply

```
 J8 baterai ── J5 B+/B− (TP4056) ── J6 OUT+ = VBAT_OUT ── U2 VIN+ ─shunt─ VIN− = VBAT_SENSE
                                                                             │
                     J4 IN+ = VCHG ──┬── gate Q1 (R1 10k ke GND)             D
                                     │                                   Q1 AO3401A
                                     └── D1 SS34 ──► VSYS ◄──────────────── S
                                                      │
                                              J10 saklar on-off
                                                      │ VSW
                                     J1 VIN+ ◄────────┘    J1 VOUT+ = VBOOST ── D2 SS34 ──► +5V ── U1 pin 5V, C1 47 µF, C2 100 nF
```

- Without a charger: the Q1 gate is pulled to GND by R1, Q1 is on, and the
  battery powers the boost.
- With a charger: VCHG 5 V turns Q1 off so the battery only receives charge
  current from the TP4056 and does not power the load. The boost is powered
  from VCHG through D1. The D1 cathode is at VSYS (the boost input), not at
  +5V. If the D1 cathode were at +5V, the Q1 body diode would still conduct
  from the battery to the boost and the cell would drain while charging.
- Switch J10 breaks VSYS before the boost. OFF means the device is fully off,
  also while the charger is plugged in, while battery charging continues
  because the TP4056 is ahead of the switch. The switch lamp is powered from
  VSYS (±3.0–4.6 V).
- R2 1 MΩ (R_Dummy in the rev2 schematic) is kept as is: a ±4 µA load from
  VBAT_SENSE to GND.
- The converter to 5 V is a boost (MT3608). A buck such as the Mini360 needs
  an input ≥ 4.75 V and does not work from a 3.0–4.2 V Li-ion cell.
- +5V only powers power loads (the DevKit 5V pin and its capacitors);
  `cek_board.py` rejects any other pin on the `+5V` net.

## Layout

| Area | Contents | Reason |
|---|---|---|
| Center | U1, USB facing the bottom edge | all used GPIOs are in the left column except EKG |
| Top right | J3 AD8232, C4 | U1 pads 39–41 line up with J3 pins 3–5, EKG traces straight 9 mm |
| Bottom right | battery path, INA219, Q1, D1, D2, TP4056/boost/battery headers | away from the AD8232; the boost module is off the board via a cable |
| Left | TFT, buzzer; buttons SW1–SW3 in a vertical row on the left edge (x 53–57.5, y 57.5–88) | TFT SPI is on the opposite side from the analog trace; buttons are easy to reach from the board edge |
| Above U1 | rule area `antena_devkit` | no copper or vias under the WROOM antenna |
| Bottom | rule area `holder_18650` 80 × 24 mm (x 66–146, y 116.5–140.5) + silkscreen outline | place for the glued wired 18650 holder; battery 65 × 18 mm, holder ±77 × 21 mm, margin 1.5 mm on each side; footprints forbidden, traces and GND pour allowed |

Traces routed manually and locked (`locked`): the three EKG traces (F.Cu), the
AD8232 supply (3V3 from U1 pad 2 through B.Cu to C4/J3 pin 2, SDN to 3V3), I2C
to the INA219 (SDA on F.Cu; SCL goes down through a via to B.Cu at x 118 and
crosses under SDA, because the INA219 pin order SCL–SDA is reversed relative to
the order from the DevKit), 3V3 to the INA219, 3V3 on the left side (U1 pad 2 to
C3), and all power traces (including the Q1 gate branch and R2). The Q1 gate
goes through B.Cu because the SOT-23 pin order (G, D, S clockwise) is opposite
to the direction of the nets around it, and the gate carries no current. The
remaining digital signals are routed by Freerouting 2.3.0. GND is poured on
both layers.

JLCPCB limits for 2-layer 1 oz (the *PCB Capabilities* page): trace/clearance
0.10 mm, trace to PTH hole 0.28 mm (recommendation 0.35 mm), via hole 0.15 /
pad 0.25 mm (holes < 0.3 mm cost more), PTH ring 0.18 mm (recommendation
0.25 mm), silkscreen text height 1.0 mm and line 0.15 mm, copper to edge
0.2 mm. This board's profile is the "technically ideal" profile: widths follow
the current requirement according to IPC-2221 (1 oz, 10 °C temperature rise:
0.3 mm ±1 A, 1.0 mm ±2.4 A), spacing and rings follow the JLCPCB
recommendations.

| Netclass (`mainboard.kicad_pro`) | Nets | Width | Clearance | Via |
|---|---|---|---|---|
| `Default` | digital signals, `+3V3`, GND | 0.3 mm | 0.35 mm | 0.9/0.4 mm |
| `ECG` | `/ECG_*` | 0.4 mm | 0.35 mm | 0.9/0.4 mm |
| `Power` | `/+5V /VBOOST /VSYS /VSW /VCHG /VBAT_OUT /VBAT_SENSE /BAT+ /BAT-` | 1.0 mm | 0.35 mm | 1.2/0.6 mm |

The largest current on the board: the battery/boost trace ±1 A peak (the
MT3608 is limited to 2 A), so 1.0 mm gives margin above the boost limit.
Signals only carry milliamperes; 0.3 mm was chosen because it is three times
the JLCPCB minimum and fits between the DevKit pins without narrowing
(0.3 + 2 × 0.35 = 1.0 mm ≤ gap 1.04 mm).

Component courtyard spacing is at least 1.0 mm. All GND pads use thermal
relief except C2-2, which is connected solid because it only gets one spoke in
the gap between U1 and the +5V trace.

Text: references on the silkscreen (height ≥ 1.0 mm, JLCPCB limit) and values
on Fab, aligned with the header axis and on the opposite side, not stacked and
not over pads. Exception: the C4 reference is horizontal above C4, because the
9 mm gap between U1 and J3 does not fit upright text.

## Differences from the rev2 schematic

The rev2 schematic (`mainboard.kicad_sch`, KiCad 10.0.6, PCB not yet laid out)
is used as the circuit reference. The differences:

| Part | Rev2 | This mainboard | Reason |
|---|---|---|---|
| 3V3 net | label `3.3V` (ESP, AD8232, buzzer) and symbol `+3.3V` (TFT) | a single net `+3V3` | different names in KiCad = two separate nets; the TFT VCC is not connected to the ESP 3V3 |
| Button pull-up | R11–R13 1 kΩ to +5V | removed, `INPUT_PULLUP` | ESP32-S3 GPIO maximum is 3.6 V |
| TFT BLK | not connected | to 3V3 | backlight always on |
| D1 cathode | to +5V | to VSYS | battery does not drain while charging |
| Power switch | none | J10 on VSYS | |
| U1 symbol | ESP32-S3-DEVKITC-1-N8R8 | ESP32-S3-DevKitC-1-N16R8 | the board in use is N16R8 |
| DevKit GND | only the top right GND pin | all four GND pins | |
| Boost header | 2 pins (Input, Output) | 4 pins with GND | the boost module GND gets its own trace |
| Footprint of headers J1–J9 | not yet assigned | PinSocket/PinHeader 2.54 mm, JST PH for the battery | |
| Net names | `SCL`, `OUT`, `buzz`, etc. | prefixed (`I2C_`, `TFT_`, `ECG_`) | identical names merge automatically in KiCad |

Passive footprint sizes follow rev2: R and C 0805 HandSolder, buttons
`SW_PUSH_6mm_H7.3mm`. C1 uses `CP_Radial_D5.0mm_P2.00mm` (same pads as rev2) so
the polarity mark is printed.

## Module circuit rationale

The ESP32-S3 is a 3.3 V device: GPIOs do not tolerate 5 V (limit VDD + 0.3 =
3.6 V). Everything that touches a GPIO is powered from 3V3, including modules
that carry their own transistor.

- **TFT.** All four signal lines (SCL, SDA, RES, DC) are connected directly
  without resistors, because the TFT and ESP32-S3 levels are both 3.3 V. A
  2k2/3k3 divider from a 3.3 V source gives 1.98 V, below the ST7789 VIH of
  0.7 × VDDI = 2.31 V; HIGH is not read. If SCK rings, a 33 Ω series resistor
  near the ESP32-S3 can be inserted. Header J2 has eight pins because the
  module carries CS; CS is tied to GND, so the firmware uses `SPI_MODE3`
  (`firmware/README.md`). BLK to 3V3 (backlight always on); to dim or turn off
  the backlight, BLK can be moved to GPIO 12 and driven with PWM.
- **Buzzer.** The A18009 passive module is active LOW, and its driver
  transistor is presumed PNP (S8550/9012; confirm from the marking on the
  module's transistor body). A PNP only turns off when the base voltage is
  almost equal to its emitter (VCC). With VCC 5 V, I/O HIGH of 3.3 V leaves
  V_EB 1.7 V: the PNP stays on, the buzzer is never silent, and current from 5 V
  flows into the GPIO through the E–B junction. With VCC 3V3, V_EB = 0 when HIGH
  and the buzzer is silent. The sound is slightly quieter than at 5 V; loudness
  is restored by setting `TONE_HZ` to the buzzer resonance. An active module
  (A07009) is sold on the same shop page: the underside of an active buzzer is
  tightly sealed, while a passive buzzer shows a green PCB.
- **Buttons.** No resistors: buttons go to GND and the firmware uses
  `INPUT_PULLUP` (±45 kΩ to 3V3) with 50 ms debounce (`buttons.cpp`). Because
  the button traces are short, this weak pull-up does not easily pick up noise.
  If an external pull-up is still wanted, the top end of the 10 kΩ resistor
  goes to 3V3, not to +5V.
- **AD8232.** J3 pin 1 uses the power symbol `GND`: in KiCad, a local label
  `GND` is not guaranteed to merge with the power symbol. SDN is tied to 3V3
  per the AD8232 datasheet (*"when not using this feature, permanently tie SDN
  to +VS"*); SDN LOW turns the chip off and a floating SDN gives an undefined
  result. The EKG trace from GPIO 1 is on the right side, opposite the TFT SPI
  (GPIO 8/9) on the left side (section **Layout**). GND is poured on both
  layers. SPI noise near the analog trace is immediately visible in the EKG
  signal.

## ESP32-S3-DevKitC-1 footprint

Taken from the official Espressif library (`espressif/kicad-libraries`,
`ESP32-S3-DevKitC.kicad_mod` and symbol `ESP32-S3-DevKitC`). Pad positions are
unchanged: 2 × 22 pins, pitch 2.54 mm, row spacing 22.86 mm. Only the holes and
pads were changed: hole 0.8 mm became 1.0 mm, oval pad 2.0 mm (horizontal) ×
1.5 mm (vertical), ring 0.25 mm per the JLCPCB recommendation. A 0.64 mm square
header pin has a 0.9 mm diagonal so it does not fit a 0.8 mm hole; 1.0 mm is the
same as the KiCad `PinSocket` footprint. A vertical 1.5 mm pad leaves a 1.04 mm
gap between pins in one column, enough for a 0.3 mm trace + 2 × 0.35 mm
clearance. The 3V3 trace to the AD8232 and the I2C trace to the INA219 cross
the pin columns through this gap. The symbol is downgraded from KiCad 10 format
to KiCad 9 format without changing pins.

## Checks

```bash
python3 hardware/mainboard/cek_board.py
```

Expected result:

```
netlist: 87/87 pin sesuai peta
+5V di luar jalur daya: tidak ada
ERC: error 0 warning 0
DRC error: 0, unconnected: 0, paritas skematik: 0
lebar jalur: 0 temuan
jarak courtyard: 0 temuan
teks: 0 temuan
LULUS
```

The script exits with code 1 if a single pin deviates from the map above, if
any trace is thinner than its netclass, if two courtyards are < 1 mm apart, or
if text overlaps, sits over a pad, goes off the edge, or is not aligned with the
header. The pin map in the script (`PIN_U1`, `PIN_LAIN`) must be updated
together with `board.h` whenever a pin is moved.

## Name engraving

Back side silkscreen, mirrored so it reads from below, behind the holder area
(which is footprint-free so its back side has no pads):

| Line | Text | Height | Position |
|---|---|---|---|
| 1 | Muhammad Rafi Rizaldi | 2.5 mm | (106; 125) |
| 2 | 3123600001 | 2.0 mm | (106; 131) |

The text is set in `UKIRAN` and `POSISI_UKIRAN` (`tata_letak.py`).

## Changing the design

Circuit changes:

1. Open `mainboard.kicad_pro` in KiCad 9 or later.
2. Change the schematic. Apply it to the board through a pcbnew script (see the
   user skill `kicad-mcp-pcb`, section *Net names match the schematic*), not
   F8, so that net names stay `/NAMA` (NAMA = the net name).

Re-route the whole board (positions in `POSISI`, manual routes in the `rute_*`
functions in `tata_letak.py`), run from `hardware/mainboard/`:

```bash
/usr/bin/python3 tata_letak.py hapus
/usr/bin/python3 tata_letak.py rute
/usr/bin/python3 tata_letak.py tuang
```

Then autoroute the remaining signals with Freerouting (kicad MCP server:
`open_project`, `autoroute` with `maxPasses` 60), then:

```bash
/usr/bin/python3 tata_letak.py bersih
/usr/bin/python3 tata_letak.py solid
/usr/bin/python3 tata_letak.py teks
/usr/bin/python3 tata_letak.py ukiran
/usr/bin/python3 tata_letak.py tuang
python3 cek_board.py
```

Expected result: the last line of `cek_board.py` is `LULUS` (PASS).
Freerouting can report success while leaving connections; if DRC reports
`unconnected`, add those connections to the `rute_*` functions in
`tata_letak.py` and repeat the whole sequence from `hapus`.

## Not yet verified

1. **Row spacing of the physical DevKit headers.** The footprint uses 22.86 mm
   (official Espressif). Measure the N16R8 board in use, because clones can
   differ.
2. **Pin order of each module** (J2, J3, U2, J9) against the silkscreen of the
   module in hand. The pin order of the 1.47" TFT differs between vendors.
3. **Module mechanical space.** Sizes from sellers differ from each other
   (AD8232 35×22 to 36×33 mm, TFT 19.5×44.5 or 22×38.5 mm, INA219 22×20 mm), and
   the module body outline is not yet drawn on the PCB. If laid toward the
   inside of the board, the TFT body covers C6 and the AD8232 body covers H2.
   SMD components underneath are safe as long as the module is raised above the
   female header. The H2 screw head needs to be checked against the underside of
   the AD8232 module.
4. **Supply path with D1 on VSYS** has not been tested on a breadboard. Measure
   VSYS and +5V with the charger plugged in and unplugged, and confirm the
   battery current ≈ 0 while charging.
5. **Battery connector** uses JST PH 2 mm. Match it to the 18650 holder cable in
   use, and measure the holder: the area on the board is 80 × 24 mm.
6. **Switch lamp voltage J10.** The lamp is powered from VSYS ±3.0–4.6 V. A 12 V
   LED lamp or 220 V neon will not light at this voltage; check the marking on
   the switch body before using the lamp pins.
7. **TP4056 charge current.** The charge current is set by Rprog on the TP4056
   module (default 1 A). Match Rprog to the capacity of the 18650 cell in use.

## Fabrication export

The files for JLCPCB are produced with the settings from the official JLCPCB
guide for KiCad: layers F/B.Cu, F/B.Paste, F/B.Silkscreen, F/B.Mask, Edge.Cuts,
Protel extensions, silkscreen minus mask, vias *tented* (board setting
`(tenting front back)`), zones poured before plotting, Excellon drill in mm
decimal with absolute origin and PTH and NPTH separate plus a drill map.

```bash
hardware/mainboard/ekspor_fab.sh
```

Result: `hardware/mainboard/fab/mainboard-gerber-jlcpcb.zip` (14 files at the zip
root), which is uploaded with the *Add gerber file* button. The `fab/` folder is
not committed because it is regenerated by the command above.

Zip contents checked against the board (Test conditions: 18 Oct 2026):

| What is checked | Gerber/drill | Board |
|---|---|---|
| PTH holes | 101 (0.4 ×3, 0.6 ×2, 0.75 ×2, 0.8 ×2, 1.0 ×80, 1.1 ×12) | same |
| NPTH holes | 4 × 3.2 mm | same |
| Flashes F.Cu / B.Cu | 122 / 101 | 117 pads + 5 vias / 96 THT pads + 5 vias |
| Front mask openings | 121 without vias | 117 pads + 4 screw holes (vias are *tented*) |
| Front / back paste pads | 21 / 0 | 21 SMD pads / 0 |
| Outline | 110.0 × 103.0 mm | same |

The visual appearance of the Gerbers is checked in the JLCPCB preview after
upload and, if *Confirm Production File* is chosen, in the production file sent
by the engineer.

The items in **Not yet verified** are checked before the zip is uploaded.
