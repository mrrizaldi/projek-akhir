#!/usr/bin/python3
import fnmatch
import json
import sys
from pathlib import Path

import pcbnew

DIR = Path(__file__).resolve().parent
PCB = DIR / "mainboard.kicad_pcb"
PRO = DIR / "mainboard.kicad_pro"

COURTYARD_GAP_MIN = 1.0
SILK_HEIGHT_MIN = 1.0
TEXT_ALLOWED_ACROSS = {("C4", "ref")}
mm = pcbnew.ToMM


def box(bb, m=0.0):
    return (mm(bb.GetLeft()) - m, mm(bb.GetTop()) - m, mm(bb.GetRight()) + m, mm(bb.GetBottom()) + m)


def intersects(a, c, m=0.1):
    return a[0] < c[2] - m and c[0] < a[2] - m and a[1] < c[3] - m and c[1] < a[3] - m


def celah(a, c):
    dx = max(c[0] - a[2], a[0] - c[2], 0)
    dy = max(c[1] - a[3], a[1] - c[3], 0)
    return (dx * dx + dy * dy) ** 0.5 if dx and dy else max(dx, dy)


def netclass_lookup():
    ns = json.loads(PRO.read_text())["net_settings"]
    track_widths = {c["name"]: c["track_width"] for c in ns["classes"]}
    pola = [(p["pattern"], p["netclass"]) for p in ns["netclass_patterns"]]

    def kelas(net):
        return next((k for p, k in pola if fnmatch.fnmatchcase(net, p)), "Default")

    return track_widths, kelas


def check_track_width(b):
    track_widths, kelas = netclass_lookup()
    temuan = []
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            continue
        k = kelas(t.GetNetname())
        w = mm(t.GetWidth())
        min_width = track_widths[k]
        if w >= min_width - 1e-6:
            continue
        temuan.append(f"{t.GetNetname()} {w:.2f} mm < {k} {min_width} mm")
    return temuan


def courtyard_box(f):
    cy = f.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False, False)
    return box(bb if bb.GetWidth() else f.GetBoundingBox(False, False))


def check_courtyard(b):
    courtyards = {f.GetReference(): courtyard_box(f) for f in b.GetFootprints()}
    ref = sorted(courtyards)
    return [f"{a}-{c} {celah(courtyards[a], courtyards[c]):.2f} mm"
            for i, a in enumerate(ref) for c in ref[i + 1:]
            if celah(courtyards[a], courtyards[c]) < COURTYARD_GAP_MIN]


def text_kind(t):
    if isinstance(t, pcbnew.PCB_FIELD):
        return "ref" if t.IsReference() else "val" if t.IsValue() else "fld"
    return "user"


def header_direction(f):
    xs = [mm(p.GetPosition().x) for p in f.Pads()]
    ys = [mm(p.GetPosition().y) for p in f.Pads()]
    if len(xs) < 2 or f.GetReference().startswith(("SW", "H", "Q")):
        return "-"
    if max(xs) - min(xs) > 1.0 and max(ys) - min(ys) > 1.0:
        return "-"
    return "H" if max(xs) - min(xs) > max(ys) - min(ys) else "V"


def check_text(b):
    edge = box(b.GetBoardEdgesBoundingBox())
    teks, pads, temuan = [], [], []
    for f in b.GetFootprints():
        r, arah = f.GetReference(), header_direction(f)
        for t in list(f.GetFields()) + [g for g in f.GraphicalItems() if isinstance(g, pcbnew.PCB_TEXT)]:
            if not t.IsVisible() or t.GetLayer() not in (pcbnew.F_SilkS, pcbnew.F_Fab):
                continue
            j, k = text_kind(t), box(t.GetBoundingBox())
            teks.append((r, j, t.GetLayer(), k))
            if t.GetLayer() == pcbnew.F_SilkS and mm(t.GetTextHeight()) < SILK_HEIGHT_MIN - 1e-6:
                temuan.append(f"{r} {j}: silk height {mm(t.GetTextHeight()):.2f} mm")
            rotation_deg = round(t.GetDrawRotation().AsDegrees()) % 180
            if j in ("ref", "val") and arah != "-" and (arah == "H") != (rotation_deg == 0) and (r, j) not in TEXT_ALLOWED_ACROSS:
                temuan.append(f"{r} {j}: not aligned with header")
            if not (k[0] >= edge[0] and k[1] >= edge[1] and k[2] <= edge[2] and k[3] <= edge[3]):
                temuan.append(f"{r} {j}: outside board edge")
        pads += [(r, box(p.GetBoundingBox())) for p in f.Pads()]
    for i, a in enumerate(teks):
        for c in teks[i + 1:]:
            one_owns_fab = a[0] == c[0] and a[2] == c[2] == pcbnew.F_Fab and "val" in (a[1], c[1])
            if intersects(a[3], c[3]) and not one_owns_fab:
                temuan.append(f"{a[0]} {a[1]} overlaps {c[0]} {c[1]}")
    temuan += [f"{a[0]} {a[1]} over pad {p[0]}" for a in teks if a[2] == pcbnew.F_SilkS
               for p in pads if intersects(a[3], p[1], 0)]
    vias = [box(v.GetBoundingBox()) for v in b.GetTracks() if v.Type() == pcbnew.PCB_VIA_T]
    for d in b.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.B_SilkS:
            k = box(d.GetBoundingBox())
            nama = d.GetText().splitlines()[0][:20]
            if not (k[0] >= edge[0] and k[1] >= edge[1] and k[2] <= edge[2] and k[3] <= edge[3]):
                temuan.append(f"back text '{nama}': outside board edge")
            temuan += [f"back text '{nama}' over pad {p[0]}" for p in pads if intersects(k, p[1], 0)]
            temuan += [f"back text '{nama}' over via" for v in vias if intersects(k, v, 0)]
    return temuan


def main():
    b = pcbnew.LoadBoard(str(PCB))
    failures = 0
    for nama, check_function in (("track width", check_track_width), ("courtyard gap", check_courtyard), ("text", check_text)):
        temuan = check_function(b)
        print(f"{nama}: {len(temuan)} findings")
        for t in temuan[:20]:
            print(f"  {t}")
        failures += bool(temuan)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
