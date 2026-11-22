#!/usr/bin/python3
import sys
from pathlib import Path

import pcbnew

DIR = Path(__file__).resolve().parent
PCB = str(DIR / "mainboard.kicad_pcb")

W_POWER, W_ECG, W_SIGNAL = 1.0, 0.4, 0.3
VIA_SIGNAL, VIA_POWER = (0.9, 0.4), (1.2, 0.6)
PAD_DEVKIT = (1.5, 2.0)
NET_MANUAL = {"/" + n for n in ["+5V", "VBOOST", "VSYS", "VSW", "VCHG", "VBAT_OUT", "VBAT_SENSE",
                                "BAT+", "BAT-", "ECG_OUT", "ECG_LON", "ECG_LOP"]}
PAD_GND_SOLID = [("C2", "2")]
ENGRAVING = ("Muhammad Rafi Rizaldi", "3123600001")
ENGRAVING_POSITION = (106.0, 125.0, 131.0)

POSITIONS = {
    "J1": (125.62, 109.5, 270), "J4": (130.5, 109.5, 90), "J6": (137.7, 109.5, 90),
    "J5": (144.9, 109.5, 90), "J8": (153, 109.5, 0),
    "Q1": (130, 88, 0), "R1": (129.06, 82.7, 90), "R2": (138, 85, 0),
    "D1": (128.62, 100, 0), "D2": (119.5, 104, 0), "C1": (85, 100.8, 180), "C2": (86.3, 95, 90),
    "SW1": (53, 64, 90), "SW2": (53, 76, 90), "SW3": (53, 88, 90), "J2": (62, 46, 90),
}

MM, mm = pcbnew.FromMM, pcbnew.ToMM


def point(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


class BoardEditor:
    def __init__(self):
        self.b = pcbnew.LoadBoard(PCB)

    def save_item(self):
        pcbnew.SaveBoard(PCB, self.b)

    def fp(self, ref):
        return self.b.FindFootprintByReference(ref)

    def pad(self, ref, pad_number):
        p = self.fp(ref).FindPadByNumber(pad_number).GetPosition()
        return (mm(p.x), mm(p.y))

    def net(self, net_name):
        return self.b.GetNetsByName()[net_name]

    def jalur(self, net, copper_layer, points, width_mm):
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(point(x1, y1))
            t.SetEnd(point(x2, y2))
            t.SetWidth(MM(width_mm))
            t.SetLayer(copper_layer)
            t.SetNet(self.net(net))
            t.SetLocked(True)
            self.b.Add(t)

    def via(self, net, x, y, via_size):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(point(x, y))
        v.SetWidth(pcbnew.F_Cu, MM(via_size[0]))
        v.SetDrill(MM(via_size[1]))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.net(net))
        v.SetLocked(True)
        self.b.Add(v)


def delete_tracks():
    p = BoardEditor()
    jalur = list(p.b.GetTracks())
    for t in jalur:
        p.b.Delete(t)
    p.save_item()
    print(f"delete: {len(jalur)} tracks/vias")


def place_footprints(p):
    for ref, (x, y, rotation_deg) in POSITIONS.items():
        f = p.fp(ref)
        f.SetLocked(False)
        f.SetPosition(point(x, y))
        f.SetOrientationDegrees(rotation_deg)
        f.SetLocked(True)


def route_analog(p, F, B):
    for pad_number, net in (("41", "/ECG_OUT"), ("40", "/ECG_LON"), ("39", "/ECG_LOP")):
        a = p.pad("U1", pad_number)
        p.jalur(net, F, [a, (122, a[1])], W_ECG)
    c41, c42 = p.pad("C4", "1"), p.pad("C4", "2")
    p.jalur("/+3V3", F, [c41, (c41[0] + 0.48, 55.08), (122, 55.08)], W_SIGNAL)
    p.jalur("/GND", F, [c42, (c42[0] + 0.1, 52.54), (122, 52.54)], W_SIGNAL)
    p.jalur("/+3V3", F, [(122, 65.24), (124, 65.24), (124, 55.08), (122, 55.08)], W_SIGNAL)
    p.jalur("/+3V3", B, [p.pad("U1", "2"), (91.27, 53.81), (115.0, 53.81), (116.2, 55.01), (116.2, c41[1])], W_SIGNAL)
    p.via("/+3V3", 116.2, c41[1], VIA_SIGNAL)
    p.jalur("/+3V3", F, [(116.2, c41[1]), c41], W_SIGNAL)
    p.jalur("/GND", F, [p.pad("U1", "44"), (115, 50), (117.46, 52.46), c42], W_SIGNAL)


def route_3v3_left(p, F):
    c31 = p.pad("C3", "1")
    p.jalur("/+3V3", F, [p.pad("U1", "2"), (87.0, 52.54), (87.0, c31[1]), c31], W_SIGNAL)


def pad_devkit(p):
    for q in p.fp("U1").Pads():
        q.SetSize(pcbnew.VECTOR2I(MM(PAD_DEVKIT[0]), MM(PAD_DEVKIT[1])))


def route_i2c_gap(p, F, B):
    for pad_number, net in (("10", "/I2C_SDA"), ("11", "/I2C_SCL")):
        x, y = p.pad("U1", pad_number)
        ys = y + 1.27
        p.jalur(net, F, [(x, y), (91.27, ys), (117.0, ys)], W_SIGNAL)
    sda, scl = p.pad("U2", "4"), p.pad("U2", "3")
    p.jalur("/I2C_SDA", F, [(117.0, 74.13), (137.51, 74.13), sda], W_SIGNAL)
    p.via("/I2C_SCL", 118.0, 76.67, VIA_SIGNAL)
    p.jalur("/I2C_SCL", F, [(117.0, 76.67), (118.0, 76.67)], W_SIGNAL)
    p.jalur("/I2C_SCL", B, [(118.0, 76.67), (140.0, 76.67), (scl[0] - 2.6, scl[1]), scl], W_SIGNAL)
    p.jalur("/+3V3", F, [(124.0, 65.24), (142.0, 65.24), (155.0, 78.24), p.pad("U2", "1")], W_SIGNAL)


def route_power(p, F, B):
    j61 = p.pad("J6", "1")
    p.jalur("/VBAT_OUT", F, [j61, (j61[0], 104), (j61[0] + 7.3, 96.7), p.pad("U2", "6")], W_POWER)
    q1, q2, q3 = p.pad("Q1", "1"), p.pad("Q1", "2"), p.pad("Q1", "3")
    p.jalur("/VBAT_SENSE", F, [p.pad("U2", "5"), (146.2, 94.16), (140, 88), q3], W_POWER)
    r21 = p.pad("R2", "1")
    p.jalur("/VBAT_SENSE", F, [r21, (r21[0], 88)], W_POWER)
    d11, d12 = p.pad("D1", "1"), p.pad("D1", "2")
    j101, j102, j11 = p.pad("J10", "1"), p.pad("J10", "2"), p.pad("J1", "1")
    p.jalur("/VSYS", F, [q2, (127.57, q2[1]), (d11[0], 88.0), j101], W_POWER)
    p.jalur("/VSYS", F, [d11, (d11[0], 88.0)], W_POWER)
    p.jalur("/VSW", F, [j102, (124, j102[1]), (124, 107), (124.62, 107), (j11[0], 108.2), j11], W_POWER)
    j41 = p.pad("J4", "1")
    p.jalur("/VCHG", F, [j41, (j41[0], d12[1])], W_POWER)
    r11 = p.pad("R1", "1")
    p.jalur("/VCHG", F, [q1, (q1[0], 85.5), r11], W_POWER)
    p.via("/VCHG", q1[0], 85.5, VIA_POWER)
    p.jalur("/VCHG", B, [(q1[0], 85.5), (132.5, 88.94), (132.5, 104)], W_POWER)
    p.via("/VCHG", 132.5, 104, VIA_POWER)
    p.jalur("/VCHG", F, [(132.5, 104), (j41[0], 104)], W_POWER)
    j13, d21, d22 = p.pad("J1", "3"), p.pad("D2", "1"), p.pad("D2", "2")
    p.jalur("/VBOOST", F, [j13, (j13[0], d22[1]), d22], W_POWER)
    u21, c11, c21 = p.pad("U1", "21"), p.pad("C1", "1"), p.pad("C2", "1")
    p.jalur("/+5V", F, [d21, (d21[0] - 2, 106), (92.5, 106), (92.5, u21[1]), u21, c11], W_POWER)
    p.jalur("/+5V", F, [c21, (c21[0], u21[1])], W_POWER)
    j51, j52, j81, j82 = p.pad("J5", "1"), p.pad("J5", "2"), p.pad("J8", "1"), p.pad("J8", "2")
    p.jalur("/BAT+", F, [j51, (j51[0], 112), (j81[0], 112), j81], W_POWER)
    p.jalur("/BAT-", F, [j52, (j52[0], 107), (j82[0], 107), j82], W_POWER)
    c12 = p.pad("C1", "2")
    p.jalur("/GND", F, [p.pad("U1", "22"), (c12[0], 103.34), c12], W_SIGNAL)


def route():
    p = BoardEditor()
    place_footprints(p)
    pad_devkit(p)
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    route_analog(p, F, B)
    route_3v3_left(p, F)
    route_i2c_gap(p, F, B)
    route_power(p, F, B)
    p.save_item()
    for ref in ("SW1", "SW2", "SW3", "R1", "D1", "D2", "J8"):
        print(ref, [(q.GetNumber(), q.GetNetname(), round(mm(q.GetPosition().x), 2), round(mm(q.GetPosition().y), 2))
                    for q in p.fp(ref).Pads()])


def bersih():
    p = BoardEditor()
    removable = [t for t in p.b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T and
             (t.GetLength() == 0 or (t.GetNetname() in NET_MANUAL and not t.IsLocked()))]
    for t in removable:
        p.b.Delete(t)
    p.save_item()
    print(f"clean: {len(removable)} segments")


def solid():
    p = BoardEditor()
    for f in p.b.GetFootprints():
        for q in f.Pads():
            zone_connection = pcbnew.ZONE_CONNECTION_FULL if (f.GetReference(), q.GetNumber()) in PAD_GND_SOLID \
                else pcbnew.ZONE_CONNECTION_INHERITED
            q.SetLocalZoneConnection(zone_connection)
    p.save_item()
    print(f"solid: {len(PAD_GND_SOLID)} solid pads, the rest thermal")


def pour():
    p = BoardEditor()
    pcbnew.ZONE_FILLER(p.b).Fill(p.b.Zones())
    p.save_item()
    print("pour: done")


def box(bb, m=0.0):
    return (mm(bb.GetLeft()) - m, mm(bb.GetTop()) - m, mm(bb.GetRight()) + m, mm(bb.GetBottom()) + m)


def intersects(a, c):
    return a[0] < c[2] and c[0] < a[2] and a[1] < c[3] and c[1] < a[3]


class TextPlacer:
    def __init__(self, b):
        self.b = b
        t = box(b.GetBoardEdgesBoundingBox())
        self.edge = (t[0] + 0.6, t[1] + 0.6, t[2] - 0.6, t[3] - 0.6)
        self.obstacles = []
        self.placed = []
        for f in b.GetFootprints():
            self.obstacles += [(f.GetReference(), "pad", box(q.GetBoundingBox(), 0.25)) for q in f.Pads()]
            self.obstacles += [(f.GetReference(), "silk", box(g.GetBoundingBox(), 0.15)) for g in f.GraphicalItems()
                            if g.GetLayer() == pcbnew.F_SilkS and not isinstance(g, pcbnew.PCB_TEXT)]
            self.obstacles += [(f.GetReference(), "teks", box(g.GetBoundingBox(), 0.1)) for g in f.GraphicalItems()
                            if isinstance(g, pcbnew.PCB_TEXT) and g.GetLayer() in (pcbnew.F_SilkS, pcbnew.F_Fab)]
        self.obstacles += [("papan", "silk", box(d.GetBoundingBox(), 0.15)) for d in b.GetDrawings()
                        if d.GetLayer() == pcbnew.F_SilkS]
        self.obstacles += [("antena", "zona", box(z.GetBoundingBox())) for z in b.Zones()
                        if z.GetIsRuleArea() and z.GetZoneName() == "antena_devkit"]

    def is_free(self, t, ref):
        k = box(t.GetBoundingBox(), 0.15)
        if not (k[0] >= self.edge[0] and k[1] >= self.edge[1] and k[2] <= self.edge[2] and k[3] <= self.edge[3]):
            return False
        if any(intersects(k, o) for r, kind, o in self.obstacles if not (r == ref and kind == "silk")):
            return False
        return not any(intersects(k, o) for o in self.placed)

    def configure_text(self, t, u, rotation_deg, x, y):
        t.SetTextSize(pcbnew.VECTOR2I(MM(u), MM(u)))
        t.SetTextThickness(MM(max(0.1, u * 0.15)))
        t.SetTextAngle(pcbnew.EDA_ANGLE(rotation_deg, pcbnew.DEGREES_T))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        t.SetPosition(point(x, y))

    def calon(self, f, t, u, rotation_deg, far_first):
        xs = [mm(q.GetPosition().x) for q in f.Pads()]
        ys = [mm(q.GetPosition().y) for q in f.Pads()]
        k = box(f.GetBoundingBox(False, False))
        cx, cy = (k[0] + k[2]) / 2, (k[1] + k[3]) / 2
        text_offset = u / 2 + 0.35
        row_offsets = [text_offset + i * u * 1.3 for i in range(8) if text_offset + i * u * 1.3 <= 4.0]
        if rotation_deg == 0:
            near = [(cx, k[1] - j) for j in row_offsets]
            far = [(cx, k[3] + j) for j in row_offsets]
        else:
            near = [(k[0] - j, cy) for j in row_offsets]
            far = [(k[2] + j, cy) for j in row_offsets]
        spots = (far + near) if far_first else (near + far)
        if f.GetReference().startswith(("Q", "H", "SW")):
            n = len(t.GetShownText(False)) * u * 0.45
            spots += [(k[0] - text_offset - n, cy), (k[2] + text_offset + n, cy)]
        span = max(max(xs) - min(xs), max(ys) - min(ys)) if xs else 0
        max_shift = max(1.5, span / 2)
        shifts = [0] + [v * d for d in (0.75, 1.5, 2.25, 3, 4, 5, 6) for v in (1, -1) if d <= max_shift]
        for x, y in spots:
            for d in shifts:
                yield (x + d, y) if rotation_deg == 0 and y != cy else (x, y + d)

    def put_text(self, f, t, via_size, far_first):
        xs = [mm(q.GetPosition().x) for q in f.Pads()]
        ys = [mm(q.GetPosition().y) for q in f.Pads()]
        free_orientation = f.GetReference().startswith(("Q", "H", "SW"))
        horizontal = (max(xs) - min(xs)) >= (max(ys) - min(ys))
        primary = 0 if horizontal or free_orientation else 90
        rotations = [primary] + ([90 - primary] if t.IsReference() else [])
        for rotation_deg in rotations:
            for u in via_size:
                self.configure_text(t, u, rotation_deg, 0, 0)
                for x, y in self.calon(f, t, u, rotation_deg, far_first):
                    t.SetPosition(point(x, y))
                    if self.is_free(t, f.GetReference()):
                        self.placed.append(box(t.GetBoundingBox(), 0.15))
                        return f"{u} mm {rotation_deg} deg"
        if t.IsValue():
            self.configure_text(t, 0.6, 0, mm(f.GetPosition().x), mm(f.GetPosition().y))
            return "center"
        return None


def teks():
    p = BoardEditor()
    for g in p.fp("U1").GraphicalItems():
        if isinstance(g, pcbnew.PCB_TEXT) and g.GetText() in ("REF**", "${REFERENCE}"):
            g.SetText("${REFERENCE}")
            g.SetPosition(point(101.43, 108.6))
            g.SetTextAngle(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
    placer = TextPlacer(p.b)
    for f in p.b.GetFootprints():
        if f.GetReference() == "U1":
            placer.placed += [box(x.GetBoundingBox(), 0.15) for x in (f.Reference(), f.Value()) if x.IsVisible()]
    by_pad_count = sorted([f for f in p.b.GetFootprints() if f.GetReference() != "U1"], key=lambda f: -len(f.Pads()))
    placements = {f.GetReference(): [placer.put_text(f, f.Reference(), [1.0], 0)] for f in by_pad_count}
    for f in by_pad_count:
        v = f.Value()
        v.SetLayer(pcbnew.F_Fab)
        v.SetVisible(True)
        if f.GetReference().startswith("H"):
            placer.configure_text(v, 0.6, 0, mm(f.GetPosition().x), mm(f.GetPosition().y))
            placements[f.GetReference()].append("center")
        else:
            placements[f.GetReference()].append(placer.put_text(f, v, [0.8, 0.6, 0.5, 0.4], 1))
    u1 = p.fp("U1").Value()
    placer.configure_text(u1, 0.8, 0, 101.43, 110.4)
    p.save_item()
    failed = [r for r, h in placements.items() if None in h]
    for r, h in sorted(placements.items()):
        print(r, h)
    print(f"text: failed {failed}")


def engrave():
    p = BoardEditor()
    old_texts = [d for d in p.b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.B_SilkS
            and d.GetText().splitlines()[0] == ENGRAVING[0]]
    if old_texts:
        print("engrave: already present, not added")
        return
    x, y1, y2 = ENGRAVING_POSITION
    for text_line, y, u in ((ENGRAVING[0], y1, 2.5), (ENGRAVING[1], y2, 2.0)):
        t = pcbnew.PCB_TEXT(p.b)
        t.SetText(text_line)
        t.SetLayer(pcbnew.B_SilkS)
        t.SetMirrored(True)
        t.SetTextSize(pcbnew.VECTOR2I(MM(u), MM(u)))
        t.SetTextThickness(MM(u * 0.15))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetPosition(point(x, y))
        p.b.Add(t)
    p.save_item()
    print(f"engrave: {ENGRAVING[0]} / {ENGRAVING[1]} on B.SilkS ({x}; {y1}/{y2})")


COMMAND_TABLE = {"delete": delete_tracks, "route": route, "clean": bersih, "solid": solid, "pour": pour,
            "text": teks, "engrave": engrave}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMAND_TABLE:
        print("usage: /usr/bin/python3 layout.py {" + "|".join(COMMAND_TABLE) + "}")
        sys.exit(2)
    COMMAND_TABLE[sys.argv[1]]()
