#!/usr/bin/python3
import sys
from pathlib import Path

import pcbnew

DIR = Path(__file__).resolve().parent
PCB = str(DIR / "mainboard.kicad_pcb")

W_DAYA, W_EKG, W_SINYAL = 1.0, 0.4, 0.3
VIA_SINYAL, VIA_DAYA = (0.9, 0.4), (1.2, 0.6)
PAD_DEVKIT = (1.5, 2.0)
NET_MANUAL = {"/" + n for n in ["+5V", "VBOOST", "VSYS", "VSW", "VCHG", "VBAT_OUT", "VBAT_SENSE",
                                "BAT+", "BAT-", "ECG_OUT", "ECG_LON", "ECG_LOP"]}
PAD_GND_SOLID = [("C2", "2")]
UKIRAN = ("Muhammad Rafi Rizaldi", "3123600001")
POSISI_UKIRAN = (106.0, 125.0, 131.0)

POSISI = {
    "J1": (125.62, 109.5, 270), "J4": (130.5, 109.5, 90), "J6": (137.7, 109.5, 90),
    "J5": (144.9, 109.5, 90), "J8": (153, 109.5, 0),
    "Q1": (130, 88, 0), "R1": (129.06, 82.7, 90), "R2": (138, 85, 0),
    "D1": (128.62, 100, 0), "D2": (119.5, 104, 0), "C1": (85, 100.8, 180), "C2": (86.3, 95, 90),
    "SW1": (53, 64, 90), "SW2": (53, 76, 90), "SW3": (53, 88, 90), "J2": (62, 46, 90),
}

MM, mm = pcbnew.FromMM, pcbnew.ToMM


def titik(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


class Papan:
    def __init__(self):
        self.b = pcbnew.LoadBoard(PCB)

    def simpan(self):
        pcbnew.SaveBoard(PCB, self.b)

    def fp(self, ref):
        return self.b.FindFootprintByReference(ref)

    def pad(self, ref, nomor):
        p = self.fp(ref).FindPadByNumber(nomor).GetPosition()
        return (mm(p.x), mm(p.y))

    def net(self, nama):
        return self.b.GetNetsByName()[nama]

    def jalur(self, net, lapis, titik_titik, lebar):
        for (x1, y1), (x2, y2) in zip(titik_titik, titik_titik[1:]):
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(titik(x1, y1))
            t.SetEnd(titik(x2, y2))
            t.SetWidth(MM(lebar))
            t.SetLayer(lapis)
            t.SetNet(self.net(net))
            t.SetLocked(True)
            self.b.Add(t)

    def via(self, net, x, y, ukuran):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(titik(x, y))
        v.SetWidth(pcbnew.F_Cu, MM(ukuran[0]))
        v.SetDrill(MM(ukuran[1]))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.net(net))
        v.SetLocked(True)
        self.b.Add(v)


def hapus():
    p = Papan()
    jalur = list(p.b.GetTracks())
    for t in jalur:
        p.b.Delete(t)
    p.simpan()
    print(f"hapus: {len(jalur)} jalur/via")


def tempatkan(p):
    for ref, (x, y, sudut) in POSISI.items():
        f = p.fp(ref)
        f.SetLocked(False)
        f.SetPosition(titik(x, y))
        f.SetOrientationDegrees(sudut)
        f.SetLocked(True)


def rute_analog(p, F, B):
    for nomor, net in (("41", "/ECG_OUT"), ("40", "/ECG_LON"), ("39", "/ECG_LOP")):
        a = p.pad("U1", nomor)
        p.jalur(net, F, [a, (122, a[1])], W_EKG)
    c41, c42 = p.pad("C4", "1"), p.pad("C4", "2")
    p.jalur("/+3V3", F, [c41, (c41[0] + 0.48, 55.08), (122, 55.08)], W_SINYAL)
    p.jalur("/GND", F, [c42, (c42[0] + 0.1, 52.54), (122, 52.54)], W_SINYAL)
    p.jalur("/+3V3", F, [(122, 65.24), (124, 65.24), (124, 55.08), (122, 55.08)], W_SINYAL)
    p.jalur("/+3V3", B, [p.pad("U1", "2"), (91.27, 53.81), (115.0, 53.81), (116.2, 55.01), (116.2, c41[1])], W_SINYAL)
    p.via("/+3V3", 116.2, c41[1], VIA_SINYAL)
    p.jalur("/+3V3", F, [(116.2, c41[1]), c41], W_SINYAL)
    p.jalur("/GND", F, [p.pad("U1", "44"), (115, 50), (117.46, 52.46), c42], W_SINYAL)


def rute_3v3_kiri(p, F):
    c31 = p.pad("C3", "1")
    p.jalur("/+3V3", F, [p.pad("U1", "2"), (87.0, 52.54), (87.0, c31[1]), c31], W_SINYAL)


def pad_devkit(p):
    for q in p.fp("U1").Pads():
        q.SetSize(pcbnew.VECTOR2I(MM(PAD_DEVKIT[0]), MM(PAD_DEVKIT[1])))


def rute_sela_i2c(p, F, B):
    for nomor, net in (("10", "/I2C_SDA"), ("11", "/I2C_SCL")):
        x, y = p.pad("U1", nomor)
        ys = y + 1.27
        p.jalur(net, F, [(x, y), (91.27, ys), (117.0, ys)], W_SINYAL)
    sda, scl = p.pad("U2", "4"), p.pad("U2", "3")
    p.jalur("/I2C_SDA", F, [(117.0, 74.13), (137.51, 74.13), sda], W_SINYAL)
    p.via("/I2C_SCL", 118.0, 76.67, VIA_SINYAL)
    p.jalur("/I2C_SCL", F, [(117.0, 76.67), (118.0, 76.67)], W_SINYAL)
    p.jalur("/I2C_SCL", B, [(118.0, 76.67), (140.0, 76.67), (scl[0] - 2.6, scl[1]), scl], W_SINYAL)
    p.jalur("/+3V3", F, [(124.0, 65.24), (142.0, 65.24), (155.0, 78.24), p.pad("U2", "1")], W_SINYAL)


def rute_daya(p, F, B):
    j61 = p.pad("J6", "1")
    p.jalur("/VBAT_OUT", F, [j61, (j61[0], 104), (j61[0] + 7.3, 96.7), p.pad("U2", "6")], W_DAYA)
    q1, q2, q3 = p.pad("Q1", "1"), p.pad("Q1", "2"), p.pad("Q1", "3")
    p.jalur("/VBAT_SENSE", F, [p.pad("U2", "5"), (146.2, 94.16), (140, 88), q3], W_DAYA)
    r21 = p.pad("R2", "1")
    p.jalur("/VBAT_SENSE", F, [r21, (r21[0], 88)], W_DAYA)
    d11, d12 = p.pad("D1", "1"), p.pad("D1", "2")
    j101, j102, j11 = p.pad("J10", "1"), p.pad("J10", "2"), p.pad("J1", "1")
    p.jalur("/VSYS", F, [q2, (127.57, q2[1]), (d11[0], 88.0), j101], W_DAYA)
    p.jalur("/VSYS", F, [d11, (d11[0], 88.0)], W_DAYA)
    p.jalur("/VSW", F, [j102, (124, j102[1]), (124, 107), (124.62, 107), (j11[0], 108.2), j11], W_DAYA)
    j41 = p.pad("J4", "1")
    p.jalur("/VCHG", F, [j41, (j41[0], d12[1])], W_DAYA)
    r11 = p.pad("R1", "1")
    p.jalur("/VCHG", F, [q1, (q1[0], 85.5), r11], W_DAYA)
    p.via("/VCHG", q1[0], 85.5, VIA_DAYA)
    p.jalur("/VCHG", B, [(q1[0], 85.5), (132.5, 88.94), (132.5, 104)], W_DAYA)
    p.via("/VCHG", 132.5, 104, VIA_DAYA)
    p.jalur("/VCHG", F, [(132.5, 104), (j41[0], 104)], W_DAYA)
    j13, d21, d22 = p.pad("J1", "3"), p.pad("D2", "1"), p.pad("D2", "2")
    p.jalur("/VBOOST", F, [j13, (j13[0], d22[1]), d22], W_DAYA)
    u21, c11, c21 = p.pad("U1", "21"), p.pad("C1", "1"), p.pad("C2", "1")
    p.jalur("/+5V", F, [d21, (d21[0] - 2, 106), (92.5, 106), (92.5, u21[1]), u21, c11], W_DAYA)
    p.jalur("/+5V", F, [c21, (c21[0], u21[1])], W_DAYA)
    j51, j52, j81, j82 = p.pad("J5", "1"), p.pad("J5", "2"), p.pad("J8", "1"), p.pad("J8", "2")
    p.jalur("/BAT+", F, [j51, (j51[0], 112), (j81[0], 112), j81], W_DAYA)
    p.jalur("/BAT-", F, [j52, (j52[0], 107), (j82[0], 107), j82], W_DAYA)
    c12 = p.pad("C1", "2")
    p.jalur("/GND", F, [p.pad("U1", "22"), (c12[0], 103.34), c12], W_SINYAL)


def rute():
    p = Papan()
    tempatkan(p)
    pad_devkit(p)
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    rute_analog(p, F, B)
    rute_3v3_kiri(p, F)
    rute_sela_i2c(p, F, B)
    rute_daya(p, F, B)
    p.simpan()
    for ref in ("SW1", "SW2", "SW3", "R1", "D1", "D2", "J8"):
        print(ref, [(q.GetNumber(), q.GetNetname(), round(mm(q.GetPosition().x), 2), round(mm(q.GetPosition().y), 2))
                    for q in p.fp(ref).Pads()])


def bersih():
    p = Papan()
    buang = [t for t in p.b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T and
             (t.GetLength() == 0 or (t.GetNetname() in NET_MANUAL and not t.IsLocked()))]
    for t in buang:
        p.b.Delete(t)
    p.simpan()
    print(f"bersih: {len(buang)} segmen")


def solid():
    p = Papan()
    for f in p.b.GetFootprints():
        for q in f.Pads():
            sambung = pcbnew.ZONE_CONNECTION_FULL if (f.GetReference(), q.GetNumber()) in PAD_GND_SOLID \
                else pcbnew.ZONE_CONNECTION_INHERITED
            q.SetLocalZoneConnection(sambung)
    p.simpan()
    print(f"solid: {len(PAD_GND_SOLID)} pad solid, sisanya thermal")


def tuang():
    p = Papan()
    pcbnew.ZONE_FILLER(p.b).Fill(p.b.Zones())
    p.simpan()
    print("tuang: selesai")


def kotak(bb, m=0.0):
    return (mm(bb.GetLeft()) - m, mm(bb.GetTop()) - m, mm(bb.GetRight()) + m, mm(bb.GetBottom()) + m)


def iris(a, c):
    return a[0] < c[2] and c[0] < a[2] and a[1] < c[3] and c[1] < a[3]


class PenempatTeks:
    def __init__(self, b):
        self.b = b
        t = kotak(b.GetBoardEdgesBoundingBox())
        self.tepi = (t[0] + 0.6, t[1] + 0.6, t[2] - 0.6, t[3] - 0.6)
        self.halang = []
        self.terpasang = []
        for f in b.GetFootprints():
            self.halang += [(f.GetReference(), "pad", kotak(q.GetBoundingBox(), 0.25)) for q in f.Pads()]
            self.halang += [(f.GetReference(), "silk", kotak(g.GetBoundingBox(), 0.15)) for g in f.GraphicalItems()
                            if g.GetLayer() == pcbnew.F_SilkS and not isinstance(g, pcbnew.PCB_TEXT)]
            self.halang += [(f.GetReference(), "teks", kotak(g.GetBoundingBox(), 0.1)) for g in f.GraphicalItems()
                            if isinstance(g, pcbnew.PCB_TEXT) and g.GetLayer() in (pcbnew.F_SilkS, pcbnew.F_Fab)]
        self.halang += [("papan", "silk", kotak(d.GetBoundingBox(), 0.15)) for d in b.GetDrawings()
                        if d.GetLayer() == pcbnew.F_SilkS]
        self.halang += [("antena", "zona", kotak(z.GetBoundingBox())) for z in b.Zones()
                        if z.GetIsRuleArea() and z.GetZoneName() == "antena_devkit"]

    def bebas(self, t, ref):
        k = kotak(t.GetBoundingBox(), 0.15)
        if not (k[0] >= self.tepi[0] and k[1] >= self.tepi[1] and k[2] <= self.tepi[2] and k[3] <= self.tepi[3]):
            return False
        if any(iris(k, o) for r, jenis, o in self.halang if not (r == ref and jenis == "silk")):
            return False
        return not any(iris(k, o) for o in self.terpasang)

    def atur(self, t, u, sudut, x, y):
        t.SetTextSize(pcbnew.VECTOR2I(MM(u), MM(u)))
        t.SetTextThickness(MM(max(0.1, u * 0.15)))
        t.SetTextAngle(pcbnew.EDA_ANGLE(sudut, pcbnew.DEGREES_T))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        t.SetPosition(titik(x, y))

    def calon(self, f, t, u, sudut, sisi):
        xs = [mm(q.GetPosition().x) for q in f.Pads()]
        ys = [mm(q.GetPosition().y) for q in f.Pads()]
        k = kotak(f.GetBoundingBox(False, False))
        cx, cy = (k[0] + k[2]) / 2, (k[1] + k[3]) / 2
        jarak = u / 2 + 0.35
        baris = [jarak + i * u * 1.3 for i in range(8) if jarak + i * u * 1.3 <= 4.0]
        if sudut == 0:
            dekat = [(cx, k[1] - j) for j in baris]
            jauh = [(cx, k[3] + j) for j in baris]
        else:
            dekat = [(k[0] - j, cy) for j in baris]
            jauh = [(k[2] + j, cy) for j in baris]
        semua = (jauh + dekat) if sisi else (dekat + jauh)
        if f.GetReference().startswith(("Q", "H", "SW")):
            n = len(t.GetShownText(False)) * u * 0.45
            semua += [(k[0] - jarak - n, cy), (k[2] + jarak + n, cy)]
        bentang = max(max(xs) - min(xs), max(ys) - min(ys)) if xs else 0
        batas = max(1.5, bentang / 2)
        geser = [0] + [v * d for d in (0.75, 1.5, 2.25, 3, 4, 5, 6) for v in (1, -1) if d <= batas]
        for x, y in semua:
            for d in geser:
                yield (x + d, y) if sudut == 0 and y != cy else (x, y + d)

    def taruh(self, f, t, ukuran, sisi):
        xs = [mm(q.GetPosition().x) for q in f.Pads()]
        ys = [mm(q.GetPosition().y) for q in f.Pads()]
        bebas_arah = f.GetReference().startswith(("Q", "H", "SW"))
        mendatar = (max(xs) - min(xs)) >= (max(ys) - min(ys))
        utama = 0 if mendatar or bebas_arah else 90
        daftar = [utama] + ([90 - utama] if t.IsReference() else [])
        for sudut in daftar:
            for u in ukuran:
                self.atur(t, u, sudut, 0, 0)
                for x, y in self.calon(f, t, u, sudut, sisi):
                    t.SetPosition(titik(x, y))
                    if self.bebas(t, f.GetReference()):
                        self.terpasang.append(kotak(t.GetBoundingBox(), 0.15))
                        return f"{u} mm {sudut} deg"
        if t.IsValue():
            self.atur(t, 0.6, 0, mm(f.GetPosition().x), mm(f.GetPosition().y))
            return "tengah"
        return None


def teks():
    p = Papan()
    for g in p.fp("U1").GraphicalItems():
        if isinstance(g, pcbnew.PCB_TEXT) and g.GetText() in ("REF**", "${REFERENCE}"):
            g.SetText("${REFERENCE}")
            g.SetPosition(titik(101.43, 108.6))
            g.SetTextAngle(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
    penempat = PenempatTeks(p.b)
    for f in p.b.GetFootprints():
        if f.GetReference() == "U1":
            penempat.terpasang += [kotak(x.GetBoundingBox(), 0.15) for x in (f.Reference(), f.Value()) if x.IsVisible()]
    urut = sorted([f for f in p.b.GetFootprints() if f.GetReference() != "U1"], key=lambda f: -len(f.Pads()))
    hasil = {f.GetReference(): [penempat.taruh(f, f.Reference(), [1.0], 0)] for f in urut}
    for f in urut:
        v = f.Value()
        v.SetLayer(pcbnew.F_Fab)
        v.SetVisible(True)
        if f.GetReference().startswith("H"):
            penempat.atur(v, 0.6, 0, mm(f.GetPosition().x), mm(f.GetPosition().y))
            hasil[f.GetReference()].append("tengah")
        else:
            hasil[f.GetReference()].append(penempat.taruh(f, v, [0.8, 0.6, 0.5, 0.4], 1))
    u1 = p.fp("U1").Value()
    penempat.atur(u1, 0.8, 0, 101.43, 110.4)
    p.simpan()
    gagal = [r for r, h in hasil.items() if None in h]
    for r, h in sorted(hasil.items()):
        print(r, h)
    print(f"teks: gagal {gagal}")


def ukiran():
    p = Papan()
    lama = [d for d in p.b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.B_SilkS
            and d.GetText().splitlines()[0] == UKIRAN[0]]
    if lama:
        print("ukiran: sudah ada, tidak ditambah")
        return
    x, y1, y2 = POSISI_UKIRAN
    for teks_baris, y, u in ((UKIRAN[0], y1, 2.5), (UKIRAN[1], y2, 2.0)):
        t = pcbnew.PCB_TEXT(p.b)
        t.SetText(teks_baris)
        t.SetLayer(pcbnew.B_SilkS)
        t.SetMirrored(True)
        t.SetTextSize(pcbnew.VECTOR2I(MM(u), MM(u)))
        t.SetTextThickness(MM(u * 0.15))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetPosition(titik(x, y))
        p.b.Add(t)
    p.simpan()
    print(f"ukiran: {UKIRAN[0]} / {UKIRAN[1]} di B.SilkS ({x}; {y1}/{y2})")


PERINTAH = {"hapus": hapus, "rute": rute, "bersih": bersih, "solid": solid, "tuang": tuang,
            "teks": teks, "ukiran": ukiran}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in PERINTAH:
        print("pakai: /usr/bin/python3 tata_letak.py {" + "|".join(PERINTAH) + "}")
        sys.exit(2)
    PERINTAH[sys.argv[1]]()
