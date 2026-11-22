#!/usr/bin/env python3
import base64
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.parse
import zlib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFT_GLOB = "laporan/*/gambar/draf/*.drawio"
FONT = "Times New Roman"
PRINT_WIDTH_PT = 396.85
PRINT_HEIGHT_PT = 0.6 * 671.81
TARGET_PT = 8.0
ERROR_PT = 7.0
DPI = 300
MAX_FILLS = 4

PALETTE = {
    "#FFFFFF", "#1A1A1A", "#555555", "#666666", "#333333", "#9C6500",
    "#DAE8FC", "#6C8EBF",
    "#D5E8D4", "#5E8F45",
    "#E1D5E7", "#9673A6",
    "#FFE6CC", "#B07A00",
    "#FFF2CC",
    "#F8CECC", "#B85450",
    "#F5F5F5",
}
NEUTRAL_FILLS = {"#FFFFFF", "#F5F5F5"}
FREE_VALUES = {"none", "default", "inherit", ""}
FORBIDDEN_EFFECTS = {"shadow": "shadow", "glass": "glass effect", "sketch": "sketch style", "comic": "comic style"}
FORBIDDEN_LABELS = [
    (re.compile(r"\bRM\s?[1-4]\b"), "requirement label RM1..RM4"),
    (re.compile(r"\bHW-\d"), "work label HW-n"),
    (re.compile(r"\bFase\s+[0-9A-G]\b"), "work label Fase n"),
    (re.compile(r"\bTask\s+\d"), "work label Task n"),
    (re.compile(r"\b[TK]-\d"), "work label T-n/K-n"),
    (re.compile(r"\brev\s?\d\b|revisi kedua", re.I), "PCB revision label"),
    (re.compile(r"walkthrough", re.I), "the word walkthrough"),
    (re.compile(r"\bPA_[A-Z]"), "knob name PA_*"),
    (re.compile(r"\b[\w./-]+\.(py|cpp|h|tex|png|csv|ini|md)\b"), "file name"),
    (re.compile(r"\b(model|firmware|laporan|scripts|dashboard|hardware)/"), "repo path"),
]
EM_DASH = "\u2014"
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]")


def luminance(hex6):
    channels = []
    for i in (1, 3, 5):
        c = int(hex6[i:i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def is_hex(value):
    return bool(value) and re.fullmatch(r"#[0-9A-Fa-f]{6}", value) is not None


def parse_style(text):
    style = {}
    for part in (text or "").split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            style[key.strip()] = value.strip()
        elif part.strip():
            style[part.strip()] = ""
    return style


def plain_text(value):
    value = re.sub(r"<br\s*/?>", "\n", value or "", flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return (value.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&amp;", "&").strip())


def load_pages(content):
    root = ET.fromstring(content)
    if root.tag == "mxGraphModel":
        return [("page-1", root)]
    pages = []
    for i, diagram in enumerate(root.iter("diagram")):
        model = diagram.find("mxGraphModel")
        if model is None and (diagram.text or "").strip():
            raw = zlib.decompress(base64.b64decode(diagram.text.strip()), -15).decode("utf-8")
            model = ET.fromstring(urllib.parse.unquote(raw))
        if model is not None:
            pages.append((diagram.get("name") or f"page-{i + 1}", model))
    return pages


def absolute_position(cell, by_id):
    x = y = 0.0
    while cell is not None:
        geometry = cell.find("mxGeometry")
        if geometry is not None and cell.get("vertex") == "1":
            x += float(geometry.get("x", 0))
            y += float(geometry.get("y", 0))
        cell = by_id.get(cell.get("parent"))
    return x, y


def check_page(name, model, revision=False):
    errors, warnings = [], []
    cells = list(model.iter("mxCell"))
    by_id = {c.get("id"): c for c in cells}
    boxes = []
    smallest_font = None
    fills = set()

    for cell in cells:
        style = parse_style(cell.get("style"))
        label = plain_text(cell.get("value"))
        where = f"{name}: cell {cell.get('id')}" + (f" \"{label[:40]}\"" if label else "")

        if cell.get("vertex") == "1":
            geometry = cell.find("mxGeometry")
            parent = by_id.get(cell.get("parent"))
            attached = geometry is not None and geometry.get("relative") == "1" or (parent is not None and parent.get("edge") == "1")
            if geometry is not None and "group" not in style and not attached:
                x, y = absolute_position(cell, by_id)
                boxes.append((x, y, x + float(geometry.get("width", 0)), y + float(geometry.get("height", 0))))
            if not revision and ("image" in style or style.get("shape") == "image"):
                warnings.append(f"{where}: embedded image; only real component photos from gambar/, no clipart or stock icons")
        if cell.get("edge") == "1":
            for point in cell.iter("mxPoint"):
                if point.get("as") is None and point.get("x") is not None:
                    px, py = float(point.get("x", 0)), float(point.get("y", 0))
                    boxes.append((px, py, px, py))

        for key, meaning in FORBIDDEN_EFFECTS.items():
            if style.get(key) == "1":
                errors.append(f"{where}: {meaning} ({key}=1) is not allowed")
        if style.get("gradientColor", "none").lower() not in FREE_VALUES:
            errors.append(f"{where}: gradient (gradientColor) is not allowed")
        if not revision and style.get("curved") == "1":
            errors.append(f"{where}: curved line; use edgeStyle=orthogonalEdgeStyle")
        if not revision and cell.get("edge") == "1" and style.get("edgeStyle") not in ("orthogonalEdgeStyle", "elbowEdgeStyle", "none", None):
            warnings.append(f"{where}: edgeStyle={style.get('edgeStyle')}; house style uses orthogonalEdgeStyle (trees: elbowEdgeStyle)")

        for key in ("fillColor", "strokeColor", "fontColor", "labelBackgroundColor", "swimlaneFillColor"):
            value = style.get(key)
            if not revision and value is not None and value.lower() not in FREE_VALUES and value.upper() not in PALETTE:
                errors.append(f"{where}: {key}={value} is outside the palette (references/house-style.md)")
            if key == "fillColor" and value and value.upper() in PALETTE:
                fills.add(value.upper())

        for match in [] if revision else re.finditer(r"(color|background-color)\s*:\s*(#[0-9A-Fa-f]{6}|rgb\([^)]*\))", cell.get("value") or ""):
            if match.group(2).upper() not in PALETTE:
                errors.append(f"{where}: color {match.group(2)} inside the HTML label is outside the palette")

        fill = style.get("fillColor", "#FFFFFF")
        fill = fill if is_hex(fill) else "#FFFFFF"
        stroke = style.get("strokeColor")
        if not revision and cell.get("vertex") == "1" and is_hex(stroke) and "text" not in style:
            ratio = contrast(stroke, "#FFFFFF")
            if ratio < 3.0:
                errors.append(f"{where}: border {stroke} is {ratio:.2f}:1 against white (< 3:1, WCAG 1.4.11, antislop-human)")

        if label:
            font_color = style.get("fontColor", "#000000")
            if is_hex(font_color):
                ratio = contrast(font_color, fill)
                if ratio < 4.5:
                    errors.append(f"{where}: text {font_color} on {fill} is {ratio:.2f}:1 (< 4.5:1, antislop R-25)")
            if EM_DASH in label:
                errors.append(f"{where}: em dash in a label (antislop R-02); use a comma, colon or parentheses")
            family = style.get("fontFamily")
            if not revision and family != FONT:
                errors.append(f"{where}: fontFamily={family or 'default (Helvetica)'}; must be {FONT}")
            if not revision and re.search(r"(face=|font-family)", cell.get("value") or "", re.I) and FONT not in (cell.get("value") or ""):
                errors.append(f"{where}: another font inside the HTML label; must be {FONT}")
            size = float(style.get("fontSize", 11))
            if not revision and size >= 18:
                warnings.append(f"{where}: {size:g}px text; a title inside the figure? the title belongs in \\caption")
            smallest_font = size if smallest_font is None else min(smallest_font, size)
            if EMOJI.search(label):
                errors.append(f"{where}: emoji or decorative symbol in a label")
            for pattern, meaning in FORBIDDEN_LABELS:
                if pattern.search(label):
                    errors.append(f"{where}: {meaning} must not appear in a report figure")

    if not boxes:
        return errors, warnings, None
    width = max(b[2] for b in boxes) - min(b[0] for b in boxes)
    height = max(b[3] for b in boxes) - min(b[1] for b in boxes)
    scale = min(PRINT_WIDTH_PT / width, PRINT_HEIGHT_PT / height)
    info = {"width": width, "height": height, "scale": scale, "fills": len(fills - NEUTRAL_FILLS)}
    if smallest_font is not None:
        printed = smallest_font * scale
        info["pt"] = printed
        if printed < TARGET_PT:
            (errors if printed < ERROR_PT else warnings).append(
                f"{name}: smallest text {smallest_font:g}px prints at about {printed:.1f} pt (< {TARGET_PT:g} pt) on a "
                f"{width:.0f}x{height:.0f} canvas; enlarge fontSize or narrow the canvas "
                f"(width <= {smallest_font * PRINT_WIDTH_PT / TARGET_PT:.0f} for {smallest_font:g}px)")
    if not revision and info["fills"] > MAX_FILLS:
        errors.append(f"{name}: {info['fills']} fill colors; at most 3 core colors + 1 accent (antislop R-29)")
    return errors, warnings, info


def check_file(path, revision=False):
    try:
        pages = load_pages(Path(path).read_text(encoding="utf-8"))
    except (ET.ParseError, OSError, zlib.error, ValueError) as e:
        return [f"{path}: not readable as draw.io ({e})"], [], []
    errors, warnings, infos = [], [], []
    for name, model in pages:
        e, w, info = check_page(name, model, revision)
        errors += [f"{path}: {x}" for x in e]
        warnings += [f"{path}: {x}" for x in w]
        if info:
            infos.append((name, info))
    return errors, warnings, infos


def extract_png(png, output):
    data = Path(png).read_bytes()
    i = 8
    while i < len(data):
        length = struct.unpack(">I", data[i:i + 4])[0]
        kind = data[i + 4:i + 8]
        body = data[i + 8:i + 8 + length]
        if kind in (b"tEXt", b"zTXt") and body.split(b"\x00", 1)[0] in (b"mxfile", b"mxGraphModel"):
            value = body.split(b"\x00", 1)[1]
            if kind == b"zTXt":
                value = zlib.decompress(value[1:])
            xml = value.decode("utf-8", "replace")
            if not xml.lstrip().startswith("<"):
                xml = urllib.parse.unquote(xml)
            Path(output).write_text(xml, encoding="utf-8")
            print(f"{png} -> {output}")
            return 0
        i += 12 + length
    print(f"{png}: no embedded draw.io XML (the PNG was not exported with 'Include a copy of my diagram')")
    return 1


def drawio_command():
    binary = os.environ.get("DRAWIO_BIN") or shutil.which("drawio") or shutil.which("draw.io")
    if not binary:
        print("draw.io Desktop not found; install it from https://github.com/jgraph/drawio-desktop/releases or set DRAWIO_BIN")
        sys.exit(2)
    prefix = []
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
        prefix = ["xvfb-run", "-a"]
    extra = ["--no-sandbox"] if hasattr(os, "geteuid") and os.geteuid() == 0 else []
    return prefix + [binary] + extra


def export(path, revision=False):
    _, _, infos = check_file(path, revision)
    width = infos[0][1]["width"] if infos else 800
    scale = max(2.0, math.ceil(DPI * (PRINT_WIDTH_PT / 72) / width * 2) / 2)
    stem = os.path.splitext(path)[0]
    base = drawio_command()
    steps = [
        base + ["-x", "-f", "pdf", "--crop", "-e", "-o", stem + ".pdf", path],
        base + ["-x", "-f", "png", "-e", "-b", "8", "-s", f"{scale:g}", "-o", stem + ".png", path],
    ]
    for step in steps:
        result = subprocess.run(step, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout + result.stderr)
            return 1
    print(f"{path} -> {stem}.pdf, {stem}.png (scale {scale:g}, about {DPI} dpi at print width)")
    return 0


def default_targets():
    return sorted(os.path.relpath(p) for p in ROOT.glob(DRAFT_GLOB))


def report(paths, revision):
    total_errors = total_warnings = 0
    for path in paths:
        errors, warnings, infos = check_file(path, revision)
        for x in errors:
            print(f"ERROR  {x}")
        for x in warnings:
            print(f"WARN   {x}")
        for name, info in infos:
            printed = f", smallest text about {info['pt']:.1f} pt" if "pt" in info else ""
            print(f"INFO   {path}: {name}: canvas {info['width']:.0f}x{info['height']:.0f}, print scale {info['scale']:.2f}{printed}, {info['fills']} fill colors")
        total_errors += len(errors)
        total_warnings += len(warnings)
    print(f"\n{len(paths)} files: {total_errors} errors, {total_warnings} warnings")
    return 1 if total_errors else 0


CLEAN_CELL = ('<mxCell id="{id}" value="{label}" vertex="1" parent="1" style="rounded=0;fillColor={fill};'
              'strokeColor={stroke};fontSize=14;fontFamily=Times New Roman;fontColor=#1A1A1A;whiteSpace=wrap;html=1;">'
              '<mxGeometry x="{x}" y="0" width="100" height="40" as="geometry"/></mxCell>')


def sample(cells):
    return '<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + "</root></mxGraphModel>"


def self_test():
    cases = {
        "clean": (sample([
            CLEAN_CELL.format(id="a", label="AD8232", fill="#DAE8FC", stroke="#6C8EBF", x=0),
            CLEAN_CELL.format(id="b", label="ESP32-S3", fill="#D5E8D4", stroke="#5E8F45", x=150),
        ]), 0, []),
        "slop": (sample([
            '<mxCell id="s" value="\U0001F4E1 WiFi \u2014 Fase 5 model/x.py" vertex="1" parent="1" '
            'style="shadow=1;gradientColor=#7EA6E0;fillColor=#FF0000;fontSize=10;">'
            '<mxGeometry x="0" y="0" width="900" height="40" as="geometry"/></mxCell>',
        ]), 1, ["shadow", "gradient", "outside the palette", "fontFamily", "emoji", "em dash", "Fase n", "file name", "prints at"]),
        "five-fills": (sample([
            CLEAN_CELL.format(id=f, label="x", fill=f"#{f}", stroke=s, x=i * 110)
            for i, (f, s) in enumerate([("DAE8FC", "#6C8EBF"), ("D5E8D4", "#5E8F45"), ("E1D5E7", "#9673A6"),
                                        ("FFE6CC", "#B07A00"), ("FFF2CC", "#9C6500")])
        ]), 1, ["R-29"]),
        "weak-border": (sample([
            CLEAN_CELL.format(id="w", label="TP4056", fill="#FFF2CC", stroke="#D6B656", x=0),
        ]), 1, ["WCAG 1.4.11"]),
    }
    failures = 0
    with tempfile.TemporaryDirectory() as folder:
        for name, (xml, expected_code, needles) in cases.items():
            path = Path(folder) / f"{name}.drawio"
            path.write_text(xml, encoding="utf-8")
            errors, _, _ = check_file(str(path))
            code = 1 if errors else 0
            joined = "\n".join(errors)
            missing = [n for n in needles if n not in joined]
            ok = code == expected_code and not missing
            failures += 0 if ok else 1
            print(f"{'ok  ' if ok else 'FAIL'} {name}: exit {code}" + (f", missing {missing}" if missing else ""))
    print(f"self-test: {len(cases) - failures}/{len(cases)} passed")
    return 1 if failures else 0


def main(args):
    if args and args[0] in ("-h", "--help"):
        print("usage: check_figures.py [--revision] [FILE.drawio ...]  |  --extract IMAGE.png OUT.drawio  |  [--revision] --export FILE.drawio ...  |  --self-test")
        print(f"without files: checks {DRAFT_GLOB}")
        return 0
    if args and args[0] == "--self-test":
        return self_test()
    if args and args[0] == "--extract":
        return extract_png(args[1], args[2])
    revision = "--revision" in args
    args = [a for a in args if a != "--revision"]
    if args and args[0] == "--export":
        code = 0
        for path in args[1:]:
            errors, _, _ = check_file(path, revision)
            if errors:
                print(f"{path}: not exported, {len(errors)} errors remain; run check_figures.py {path}")
                code = 1
                continue
            code |= export(path, revision)
        return code
    paths = args or default_targets()
    if not paths:
        print(f"no drafts match {DRAFT_GLOB}")
        return 0
    return report(paths, revision)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
