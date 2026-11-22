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
MODE_NAMES = {0: "timer ISR off", 1: "+ ISR 360 Hz", 2: "+ DSP ecg_live", 3: "+ CNN inference",
        4: "+ UI (TFT, beep, LED)", 5: "+ WiFi/MQTT"}


def read_until(s, end_marker, seconds):
    lines, deadline = [], time.time() + seconds
    while time.time() < deadline:
        b = s.readline().decode(errors="replace").rstrip()
        if b:
            lines.append(b)
            if end_marker in b:
                return lines
    return None


def validate_rings(rows):
    ring, failures, previous_mode = {}, [], None
    for m in sorted({int(r["mode"]) for r in rows}):
        r = [x for x in rows if int(x["mode"]) == m]
        i = [float(x["I_mA"]) for x in r]
        ring[m] = dict(I=statistics.mean(i), sd=statistics.stdev(i) if len(i) > 1 else 0.0,
                       V=statistics.mean(float(x["V"]) for x in r),
                       P=statistics.mean(float(x["P_mW"]) for x in r),
                       vmin=min(float(x["V"]) for x in r),
                       beat=sum(int(x["beat"]) for x in r), lewat=sum(int(x["lewat"]) for x in r),
                       sah=all(x["sah"] == "1" for x in r))
        g = ring[m]
        if g["vmin"] < 1.0:
            failures.append(f"p{m}: V bus {g['vmin']:.3f} V < 1 V, INA219 not in the supply path")
        if m >= 1 and g["lewat"]:
            failures.append(f"p{m}: {g['lewat']} samples lost, load not representative")
        if m >= 2 and not g["beat"]:
            failures.append(f"p{m}: no beats, replay not running")
        if previous_mode is not None:
            dI, sd = g["I"] - ring[previous_mode]["I"], max(g["sd"], ring[previous_mode]["sd"])
            if dI < 0:
                failures.append(f"p{previous_mode}->p{m}: current dropped {dI:+.2f} mA (not monotonic)")
            elif dI <= 2 * sd:
                failures.append(f"p{previous_mode}->p{m}: difference {dI:+.2f} mA <= 2 x std {sd:.2f}")
        previous_mode = m
    if len(ring) < 6:
        failures.append(f"only {len(ring)} of 6 modes (sweep aborted midway)")
    return ring, failures


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

    listing = None
    for _ in range(5):
        time.sleep(1.0)
        s.reset_input_buffer()
        s.write(b"v")
        listing = read_until(s, "power: end of list", 3)
        if listing:
            break
    if not listing:
        sys.exit("Board did not answer 'v' (old firmware without the standalone sweep?).")
    file_numbers = sorted(int(g.group(1)) for b in listing if (g := re.match(r"\s+(\d+)\s+\d+ B", b)))
    print("Files on board: " + (", ".join(f"{n:03d}" for n in file_numbers) or "(empty)"))
    if not file_numbers:
        sys.exit("No sweep result yet. Run the Ukur daya menu or serial 'V' first.")
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else file_numbers[-1]

    s.reset_input_buffer()
    s.write(f"v{n}".encode())
    lines = read_until(s, "---SELESAI---", 10)
    s.close()
    if not lines or "---MULAI---" not in lines:
        sys.exit(f"File {n:03d} could not be read: {lines[-1] if lines else 'no reply'}")
    lines = lines[lines.index("---MULAI---") + 1:-1]

    os.makedirs(TUJUAN, exist_ok=True)
    path = os.path.join(TUJUAN, datetime.datetime.now().strftime("%Y%m%d-%H%M")
                        + f"-board-{n:03d}.csv")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{len(lines) - 1} windows -> {path}\n")

    ring, failures = validate_rings(list(csv.DictReader(io.StringIO("\n".join(lines)))))
    print(f"{'mode':<26}{'I (mA)':>16}{'V':>8}{'P (mW)':>9}{'delta I':>9}{'beat':>6}"
          f"{'missed':>6}  board")
    previous_mode = None
    for m, r in ring.items():
        d = "" if previous_mode is None else f"{r['I'] - ring[previous_mode]['I']:+.2f}"
        print(f"p{m} {MODE_NAMES[m]:<23}{r['I']:>9.2f} ± {r['sd']:<4.2f}{r['V']:>8.3f}{r['P']:>9.1f}"
              f"{d:>9}{r['beat']:>6}{r['lewat']:>6}  {'valid' if r['sah'] else 'INVALID'}")
        previous_mode = m
    print("\nCheck: " + ("PASS" if not failures else "FAIL (INVALID)\n  " + "\n  ".join(failures)))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
