import csv
import datetime
import io
import os
import re
import statistics
import sys
import time

PORT = os.environ.get("ECG_PORT", "/dev/ttyACM0")
TUJUAN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "artifacts", "metrics", "daya")
NAMA = {0: "timer ISR off", 1: "+ ISR 360 Hz", 2: "+ DSP ecg_live", 3: "+ CNN inference",
        4: "+ UI (TFT, beep, LED)", 5: "+ WiFi/MQTT"}


def baca_sampai(s, akhir, detik):
    isi, batas = [], time.time() + detik
    while time.time() < batas:
        b = s.readline().decode(errors="replace").rstrip()
        if b:
            isi.append(b)
            if akhir in b:
                return isi
    return None


def validasi(baris):
    ring, gagal, lalu = {}, [], None
    for m in sorted({int(r["mode"]) for r in baris}):
        r = [x for x in baris if int(x["mode"]) == m]
        i = [float(x["I_mA"]) for x in r]
        ring[m] = dict(I=statistics.mean(i), sd=statistics.stdev(i) if len(i) > 1 else 0.0,
                       V=statistics.mean(float(x["V"]) for x in r),
                       P=statistics.mean(float(x["P_mW"]) for x in r),
                       vmin=min(float(x["V"]) for x in r),
                       beat=sum(int(x["beat"]) for x in r), lewat=sum(int(x["lewat"]) for x in r),
                       sah=all(x["sah"] == "1" for x in r))
        g = ring[m]
        if g["vmin"] < 1.0:
            gagal.append(f"p{m}: V bus {g['vmin']:.3f} V < 1 V, INA219 not in the supply path")
        if m >= 1 and g["lewat"]:
            gagal.append(f"p{m}: {g['lewat']} samples lost, load not representative")
        if m >= 2 and not g["beat"]:
            gagal.append(f"p{m}: no beats, replay not running")
        if lalu is not None:
            dI, sd = g["I"] - ring[lalu]["I"], max(g["sd"], ring[lalu]["sd"])
            if dI < 0:
                gagal.append(f"p{lalu}->p{m}: current dropped {dI:+.2f} mA (not monotonic)")
            elif dI <= 2 * sd:
                gagal.append(f"p{lalu}->p{m}: difference {dI:+.2f} mA <= 2 x std {sd:.2f}")
        lalu = m
    if len(ring) < 6:
        gagal.append(f"only {len(ring)} of 6 modes (sweep aborted midway)")
    return ring, gagal


def main() -> None:
    try:
        import serial
    except ImportError:
        sys.exit("pyserial is missing. Install with:\n  .venv/bin/pip install -r requirements.txt")

    s = serial.Serial()
    s.port, s.baudrate, s.timeout = PORT, 115200, 0.5
    s.dtr = s.rts = False
    try:
        s.open()
    except Exception as e:
        sys.exit(f"Cannot open {PORT}: {e}\nIs another serial monitor still open?")

    daftar = None
    for _ in range(5):
        time.sleep(1.0)
        s.reset_input_buffer()
        s.write(b"v")
        daftar = baca_sampai(s, "daya: akhir daftar", 3)
        if daftar:
            break
    if not daftar:
        sys.exit("Board did not answer 'v' (old firmware without the standalone sweep?).")
    nomor = sorted(int(g.group(1)) for b in daftar if (g := re.match(r"\s+(\d+)\s+\d+ B", b)))
    print("Files on board: " + (", ".join(f"{n:03d}" for n in nomor) or "(empty)"))
    if not nomor:
        sys.exit("No sweep result yet. Run the Ukur daya menu or serial 'V' first.")
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else nomor[-1]

    s.reset_input_buffer()
    s.write(f"v{n}".encode())
    isi = baca_sampai(s, "---SELESAI---", 10)
    s.close()
    if not isi or "---MULAI---" not in isi:
        sys.exit(f"File {n:03d} could not be read: {isi[-1] if isi else 'no reply'}")
    isi = isi[isi.index("---MULAI---") + 1:-1]

    os.makedirs(TUJUAN, exist_ok=True)
    path = os.path.join(TUJUAN, datetime.datetime.now().strftime("%Y%m%d-%H%M")
                        + f"-board-{n:03d}.csv")
    with open(path, "w") as f:
        f.write("\n".join(isi) + "\n")
    print(f"{len(isi) - 1} windows -> {path}\n")

    ring, gagal = validasi(list(csv.DictReader(io.StringIO("\n".join(isi)))))
    print(f"{'mode':<26}{'I (mA)':>16}{'V':>8}{'P (mW)':>9}{'delta I':>9}{'beat':>6}"
          f"{'missed':>6}  board")
    lalu = None
    for m, r in ring.items():
        d = "" if lalu is None else f"{r['I'] - ring[lalu]['I']:+.2f}"
        print(f"p{m} {NAMA[m]:<23}{r['I']:>9.2f} ± {r['sd']:<4.2f}{r['V']:>8.3f}{r['P']:>9.1f}"
              f"{d:>9}{r['beat']:>6}{r['lewat']:>6}  {'valid' if r['sah'] else 'INVALID'}")
        lalu = m
    print("\nCheck: " + ("PASS" if not gagal else "FAIL (INVALID)\n  " + "\n  ".join(gagal)))
    sys.exit(1 if gagal else 0)


if __name__ == "__main__":
    main()
