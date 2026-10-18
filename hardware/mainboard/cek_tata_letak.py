#!/usr/bin/python3
import fnmatch
import json
import sys
from pathlib import Path

import pcbnew

DIR = Path(__file__).resolve().parent
PCB = DIR / "mainboard.kicad_pcb"
PRO = DIR / "mainboard.kicad_pro"

JARAK_COURTYARD_MIN = 1.0
TINGGI_SILK_MIN = 1.0
TEKS_BOLEH_MELINTANG = {("C4", "ref")}
mm = pcbnew.ToMM


def kotak(bb, m=0.0):
    return (mm(bb.GetLeft()) - m, mm(bb.GetTop()) - m, mm(bb.GetRight()) + m, mm(bb.GetBottom()) + m)


def iris(a, c, m=0.1):
    return a[0] < c[2] - m and c[0] < a[2] - m and a[1] < c[3] - m and c[1] < a[3] - m


def celah(a, c):
    dx = max(c[0] - a[2], a[0] - c[2], 0)
    dy = max(c[1] - a[3], a[1] - c[3], 0)
    return (dx * dx + dy * dy) ** 0.5 if dx and dy else max(dx, dy)


def kelas_net():
    ns = json.loads(PRO.read_text())["net_settings"]
    lebar = {c["name"]: c["track_width"] for c in ns["classes"]}
    pola = [(p["pattern"], p["netclass"]) for p in ns["netclass_patterns"]]

    def kelas(net):
        return next((k for p, k in pola if fnmatch.fnmatchcase(net, p)), "Default")

    return lebar, kelas


def cek_lebar(b):
    lebar, kelas = kelas_net()
    temuan = []
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            continue
        k = kelas(t.GetNetname())
        w = mm(t.GetWidth())
        batas = lebar[k]
        if w >= batas - 1e-6:
            continue
        temuan.append(f"{t.GetNetname()} {w:.2f} mm < {k} {batas} mm")
    return temuan


def kotak_courtyard(f):
    cy = f.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False, False)
    return kotak(bb if bb.GetWidth() else f.GetBoundingBox(False, False))


def cek_courtyard(b):
    kot = {f.GetReference(): kotak_courtyard(f) for f in b.GetFootprints()}
    ref = sorted(kot)
    return [f"{a}-{c} {celah(kot[a], kot[c]):.2f} mm"
            for i, a in enumerate(ref) for c in ref[i + 1:]
            if celah(kot[a], kot[c]) < JARAK_COURTYARD_MIN]


def jenis_teks(t):
    if isinstance(t, pcbnew.PCB_FIELD):
        return "ref" if t.IsReference() else "val" if t.IsValue() else "fld"
    return "user"


def arah_header(f):
    xs = [mm(p.GetPosition().x) for p in f.Pads()]
    ys = [mm(p.GetPosition().y) for p in f.Pads()]
    if len(xs) < 2 or f.GetReference().startswith(("SW", "H", "Q")):
        return "-"
    if max(xs) - min(xs) > 1.0 and max(ys) - min(ys) > 1.0:
        return "-"
    return "H" if max(xs) - min(xs) > max(ys) - min(ys) else "V"


def cek_teks(b):
    tepi = kotak(b.GetBoardEdgesBoundingBox())
    teks, pads, temuan = [], [], []
    for f in b.GetFootprints():
        r, arah = f.GetReference(), arah_header(f)
        for t in list(f.GetFields()) + [g for g in f.GraphicalItems() if isinstance(g, pcbnew.PCB_TEXT)]:
            if not t.IsVisible() or t.GetLayer() not in (pcbnew.F_SilkS, pcbnew.F_Fab):
                continue
            j, k = jenis_teks(t), kotak(t.GetBoundingBox())
            teks.append((r, j, t.GetLayer(), k))
            if t.GetLayer() == pcbnew.F_SilkS and mm(t.GetTextHeight()) < TINGGI_SILK_MIN - 1e-6:
                temuan.append(f"{r} {j}: tinggi silk {mm(t.GetTextHeight()):.2f} mm")
            sudut = round(t.GetDrawRotation().AsDegrees()) % 180
            if j in ("ref", "val") and arah != "-" and (arah == "H") != (sudut == 0) and (r, j) not in TEKS_BOLEH_MELINTANG:
                temuan.append(f"{r} {j}: tidak searah header")
            if not (k[0] >= tepi[0] and k[1] >= tepi[1] and k[2] <= tepi[2] and k[3] <= tepi[3]):
                temuan.append(f"{r} {j}: keluar tepi papan")
        pads += [(r, kotak(p.GetBoundingBox())) for p in f.Pads()]
    for i, a in enumerate(teks):
        for c in teks[i + 1:]:
            satu_milik_fab = a[0] == c[0] and a[2] == c[2] == pcbnew.F_Fab and "val" in (a[1], c[1])
            if iris(a[3], c[3]) and not satu_milik_fab:
                temuan.append(f"{a[0]} {a[1]} menumpuk {c[0]} {c[1]}")
    temuan += [f"{a[0]} {a[1]} di atas pad {p[0]}" for a in teks if a[2] == pcbnew.F_SilkS
               for p in pads if iris(a[3], p[1], 0)]
    vias = [kotak(v.GetBoundingBox()) for v in b.GetTracks() if v.Type() == pcbnew.PCB_VIA_T]
    for d in b.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.B_SilkS:
            k = kotak(d.GetBoundingBox())
            nama = d.GetText().splitlines()[0][:20]
            if not (k[0] >= tepi[0] and k[1] >= tepi[1] and k[2] <= tepi[2] and k[3] <= tepi[3]):
                temuan.append(f"teks belakang '{nama}': keluar tepi papan")
            temuan += [f"teks belakang '{nama}' di atas pad {p[0]}" for p in pads if iris(k, p[1], 0)]
            temuan += [f"teks belakang '{nama}' di atas via" for v in vias if iris(k, v, 0)]
    return temuan


def main():
    b = pcbnew.LoadBoard(str(PCB))
    gagal = 0
    for nama, fungsi in (("lebar jalur", cek_lebar), ("jarak courtyard", cek_courtyard), ("teks", cek_teks)):
        temuan = fungsi(b)
        print(f"{nama}: {len(temuan)} temuan")
        for t in temuan[:20]:
            print(f"  {t}")
        gagal += bool(temuan)
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
