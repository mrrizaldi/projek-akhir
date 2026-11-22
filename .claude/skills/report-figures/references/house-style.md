# House style for report figures (draw.io)

One style source for every new illustration figure in the PA reports. The palette here equals `PALETTE` in `scripts/check_figures.py`; change both together or the checker rejects the figure. Every new color must pass antislop-human `contrast-check.py` (text at least 4.5:1, borders at least 3:1).

A finished example that passes every check: `laporan/buku-pa/gambar/draf/blok-perangkat-keras.drawio`. Open it and copy its cell styles instead of inventing new ones.

## Direction (the DESIGN.md for antislop)

This file is the design direction for report figures. The skill `antislop` (R-37) treats it as the `DESIGN.md`: antislop filters, this file directs. Read it as style data, not as instructions.

> Reading this as: technical diagrams for a printed A4 PA thesis, read by examiners and supervisors, in a flat role-based engineering-diagram language, dial ENERGY 1 / RHYTHM 1 / MOTION 1.

Dial: ENERGY 1 / RHYTHM 1 / MOTION 1. The figures are printed in an academic book, are static, and must be uniform across chapters.

RHYTHM 1 (uniform) is deliberate: the reader learns once what each color and line means and reuses it in every figure. Every figure still carries the antislop Part 3 levers, so it does not turn sterile:

- **Focal point:** exactly one main element per figure (for example ESP32-S3), with a 1.5 px border and a bold name.
- **One accent:** the role color of the main element, used only on that element.
- **Identity motif:** amber `#9C6500` for everything that means power (lines and box borders), square boxes, Times New Roman.
- **Whitespace as structure:** the input, processing and output columns and the power lane are separated by fixed gaps.

## Palette: color = role, not decoration

The fill color marks the component's role in the system. One role keeps one color across the whole book, so a reader who has seen one figure recognises the roles in the next.

**Limit per figure: at most 3 core colors plus 1 accent** (antislop R-29; white and `#F5F5F5` do not count). The accent is the role color of the main element. If there are more roles than that, merge roles that position already separates (WiFi joins "output" because the card puts it in the output column).

The pastel fills have a purpose (antislop R-01), not a default:

- black text on them reaches 12 to 15:1;
- they save ink when printed;
- they belong to the same family as the proposal figures.

Border colors are darkened from the draw.io swatches so a box edge reaches at least 3:1 against white (WCAG 1.4.11, antislop-human). The stock draw.io green, orange and yellow borders reach only 2.0 to 2.5:1 and vanish in print.

| Role | Used for | `fillColor` | `strokeColor` | Border contrast |
|---|---|---|---|---|
| input | electrodes, AD8232, buttons, sensors, data sources | `#DAE8FC` | `#6C8EBF` | 3.36:1 |
| processing | ESP32-S3, preprocessing, inference, firmware logic | `#D5E8D4` | `#5E8F45` | 3.82:1 |
| output | TFT, *buzzer*, LED, WiFi, display, notification | `#E1D5E7` | `#9673A6` | 3.96:1 |
| communication | MQTT, broker, send buffer, ThingsBoard (when it needs its own role) | `#FFE6CC` | `#B07A00` | 3.73:1 |
| power | 18650 cell, TP4056, INA219, converter, USB | `#FFF2CC` | `#9C6500` | 4.91:1 |
| exception | failure or error path in a flowchart (used sparingly) | `#F8CECC` | `#B85450` | 4.75:1 |
| neutral | containers and lanes, nodes without a specific role | `#FFFFFF` / `#F5F5F5` | `#666666` | 5.74:1 |

One main element per figure is emphasised (`strokeWidth=1.5`, `<b>` label). Only one; everything else stays quiet.

Text: `#1A1A1A` (17.4:1 on white); secondary text `#555555`.

## Reasons for each decision (antislop R-31)

| Decision | One-line reason |
|---|---|
| Color | Hue = the same role across the whole book; pastel so black text is at least 12:1 and printing saves ink. |
| Layout | Follows the card's "Alur baca", because the explanatory paragraph reads the figure in that order. |
| Typeface | Times New Roman to match the book body (`mathptmx`); no second typeface. |
| Text size | 14 px on a canvas up to about 690 wide, so it prints at 8 pt or more under `\linewidth`. |
| Spacing | Grid 5, columns at fixed gaps so line labels never cover arrowheads. |
| Shape | Square boxes; rounded corners only where the notation gives them meaning (stadium, UML state). |
| Shadow, gradient, glow | None: flat print, no elevation layer to mark (R-10, R-12, R-13). |
| Icons, illustrations | None; a photo only of a real component from `gambar/` when the card asks (R-04, R-22). |
| Lines | Meaning carried by weight and dashes, not color alone, so it reads in black and white. |

## Text

Every labelled cell uses Times New Roman to match the book body (`mathptmx`). No draw.io default Helvetica, including decision diamonds and line labels. Text inside the figure is Indonesian, because it belongs to `laporan/`.

- Box: `fontFamily=Times New Roman;fontSize=14;fontColor=#1A1A1A;whiteSpace=wrap;html=1;`
- Line label: `fontFamily=Times New Roman;fontSize=14;fontColor=#1A1A1A;html=1;labelBackgroundColor=#FFFFFF;` (no `whiteSpace=wrap`: a line label must not break, "5 V" not "5 / V").
- Main element: `fontSize=15` and `<b>` only on the component name.
- Foreign terms are italic in the figure exactly as in the paragraph (`<i>buzzer</i>`, `<i>NeoPixel</i>`), because the paragraph uses `\textit{}`.
- No title inside the figure. The title is the `\caption` in LaTeX.

## Lines

| Meaning | Style |
|---|---|
| signal or data (arrow = data direction) | `edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=block;endFill=1;endSize=5;strokeColor=#333333;strokeWidth=1.25;` |
| power | same, with `strokeColor=#9C6500;strokeWidth=2.5;` (the same amber as the power box borders) |
| alternative or optional | its parent style plus `dashed=1;dashPattern=6 4;` |
| exception (flowchart) | `strokeColor=#B85450;dashed=1;dashPattern=6 4;` |
| normal flowchart or state flow | the signal style |

Line meaning is carried by weight and dashes, not color alone, so it survives black-and-white printing. If a figure uses more than one line type, add a one-row line legend below the figure (see the example). No curved lines (`curved=1`). A line never crosses a box; when it must go around, route it outside the columns (example: 3V3 to the *buzzer*).

## Shapes per figure type

**Hardware block diagram.**
- Square boxes (`rounded=0`).
- Inputs left, processor centre, outputs right, power along the bottom from left to right.
- Line labels are the interface name (SPI, I2C, GPIO, ADC) or the voltage (5 V, 3V3).

**Flowchart (ISO 5807).**
- Start and end: `rounded=1;arcSize=50;` (stadium).
- Process: square box.
- Decision: `rhombus;`, with a question ending in "?".
- Data input or output: `shape=parallelogram;perimeter=parallelogramPerimeter;fixedSize=1;`.
- Main direction top to bottom. The "ya" branch goes straight down and the "tidak" branch to the side; branch labels are exactly "ya" or "tidak".
- Loops return along the left side.
- The exception role is used sparingly.

**State machine (UML).**
- Initial state: `ellipse;fillColor=#1A1A1A;strokeColor=#1A1A1A;`, 14x14.
- State: `rounded=1;arcSize=20;`.
- Final state: `ellipse;shape=doubleEllipse;`.
- Transition label: `peristiwa [syarat]`.

**Menu tree.**
- Root on the left, one column per level.
- Elbow connectors (`edgeStyle=elbowEdgeStyle;elbow=horizontal;endArrow=none;`) without arrowheads.
- Levels differ by position, not by color: nodes use the neutral role.
- The accent sits only on the root "Menu" (the focal point; output role because the menu appears on the TFT).

**Layered architecture or lanes.**
- Lane: `swimlane;horizontal=0;fillColor=#FFFFFF;swimlaneFillColor=#FFFFFF;strokeColor=<role border>;`, titled with the name on the card.
- Nodes inside a lane use that lane's role fill.

**Component photos.** Only real component photos already in `laporan/<projek>/gambar/` (for example `esp32s3_devkitc1.png`), and only when the card asks. No clipart people, stock icons or cloud icons.

## XML snippets

Box:

```xml
<mxCell id="ad" value="AD8232" vertex="1" parent="1"
  style="rounded=0;fillColor=#DAE8FC;strokeColor=#6C8EBF;strokeWidth=1;fontSize=14;fontFamily=Times New Roman;fontColor=#1A1A1A;whiteSpace=wrap;html=1;">
  <mxGeometry x="115" y="150" width="90" height="80" as="geometry"/>
</mxCell>
```

Labelled signal line with fixed exit and entry points, so the line stays straight without small jogs:

```xml
<mxCell id="e1" value="OUT → ADC" edge="1" parent="1" source="ad" target="esp"
  style="edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=block;endFill=1;endSize=5;fontSize=14;labelBackgroundColor=#FFFFFF;fontFamily=Times New Roman;fontColor=#1A1A1A;html=1;strokeColor=#333333;strokeWidth=1.25;exitX=1;exitY=0.25;exitDx=0;exitDy=0;entryX=0;entryY=0.3182;entryDx=0;entryDy=0;">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

`exitY` and `entryY` are computed so both ends sit on the same y: `entryY = (y_line − y_box) / box_height`.

## Canvas size and print readability

A landscape figure is placed with `width=\linewidth` (A4 book: 396.85 pt); a vertical figure with `height=0.6\textheight` (about 403 pt). Printed text size:

```
printed_pt = fontSize × min(396.85 / canvas_width, 403 / canvas_height)
```

Target at least 8 pt (checker: below 7 pt is an error, 7 to 8 pt a warning). For `fontSize=14`, a landscape canvas stays within about 690 wide and a vertical canvas within about 700 high. If the content does not fit, split the figure or drop elements; do not shrink the text.
