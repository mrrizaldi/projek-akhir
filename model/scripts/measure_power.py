import argparse
import csv
import datetime
import os
import re
import statistics
import sys
import time

import serial

MODEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POWER_LINE_PATTERN = re.compile(r"DAYA p(\d) n=(\d+) I=([-\d.]+) sd=([-\d.]+) mA V=([-\d.]+) "
                  r"P=([-\d.]+) mW beat=(\d+) lewat=(\d+) replay=(\d)")
COLUMNS = ["waktu", "mode", "n", "I_mA", "sd_mA", "V", "P_mW", "beat", "lewat", "replay"]
MODE_NAMES = {0: "timer ISR off", 1: "+ ISR 360 Hz", 2: "+ DSP ecg_live", 3: "+ CNN inference",
        4: "+ UI (TFT, beep, LED)", 5: "+ WiFi/MQTT"}


def tunggu(s, expected_text, detik):
    akhir = time.time() + detik
    while time.time() < akhir:
        b = s.readline().decode("utf-8", "replace").rstrip()
        if b:
            print("  " + b)
            if expected_text in b:
                return b
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=os.environ.get("ECG_PORT", "/dev/ttyACM0"))
    ap.add_argument("--blocks", type=int, default=6)
    ap.add_argument("--mode", default="012345")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--output", default=os.path.join(MODEL, "artifacts", "metrics", "daya"))
    a = ap.parse_args()

    s = serial.Serial()
    s.port, s.baudrate, s.timeout = a.port, 115200, 0.2
    s.dtr = s.rts = False
    s.open()
    tunggu(s, "ARRHYTHMIA MONITOR READY", 6)
    time.sleep(1.0)

    s.write(b"s")
    st = tunggu(s, "replay=", 3)
    if st is None:
        sys.exit("Board did not answer 's'.")
    replay_awal = "replay=1" in st
    if not replay_awal:
        s.write(b"y")
        if not tunggu(s, "replay ON", 3):
            sys.exit("Replay failed to turn on.")

    baris = []
    try:
        for m in map(int, a.mode):
            s.write(f"p{m}".encode())
            if not tunggu(s, f"power: mode p{m}", 3):
                sys.exit(f"Mode p{m} was not confirmed by the board.")
            dapat = 0
            akhir = time.time() + (a.blocks + 3) * 10 + 5
            while dapat <= a.blocks and time.time() < akhir:
                b = s.readline().decode("utf-8", "replace").rstrip()
                g = POWER_LINE_PATTERN.search(b)
                if not g or int(g.group(1)) != m:
                    continue
                print("  " + b)
                dapat += 1
                if not a.force and float(g.group(5)) < 1.0:
                    sys.exit(f"\nBus voltage {g.group(5)} V: INA219 is not in the device current path "
                             "(VIN- is not connected to the flowing supply).\nNothing was "
                             "written. Build the measurement path as in docs/firmware-walkthrough.md "
                             "§5d Prosedur ukur daya, then repeat.")
                if dapat == 1:
                    continue
                baris.append([datetime.datetime.now().isoformat(timespec="seconds"), m,
                              *g.groups()[1:]])
            if dapat <= a.blocks:
                sys.exit(f"Mode p{m}: only {dapat} windows received.")
    finally:
        s.write(b"px")
        if not replay_awal:
            time.sleep(0.6)
            s.write(b"y")
        s.close()

    os.makedirs(a.output, exist_ok=True)
    berkas = os.path.join(a.output, datetime.datetime.now().strftime("%Y%m%d-%H%M") + ".csv")
    with open(berkas, "w", newline="") as f:
        csv.writer(f).writerows([COLUMNS] + baris)
    print(f"\nCSV: {berkas}\n")

    ring = {}
    for m in map(int, a.mode):
        r = [x for x in baris if x[1] == m]
        i = [float(x[3]) for x in r]
        ring[m] = dict(I=statistics.mean(i), sd=statistics.stdev(i) if len(i) > 1 else 0.0,
                       V=statistics.mean(float(x[5]) for x in r),
                       P=statistics.mean(float(x[6]) for x in r),
                       beat=sum(int(x[7]) for x in r), lewat=sum(int(x[8]) for x in r))
    print(f"{'mode':<26}{'I (mA)':>16}{'V':>8}{'P (mW)':>9}{'delta I':>9}{'beat':>6}{'missed':>6}")
    failures = []
    lalu = None
    for m, r in ring.items():
        d = "" if lalu is None else f"{r['I'] - ring[lalu]['I']:+.2f}"
        print(f"p{m} {MODE_NAMES[m]:<23}{r['I']:>9.2f} ± {r['sd']:<4.2f}{r['V']:>8.3f}{r['P']:>9.1f}"
              f"{d:>9}{r['beat']:>6}{r['lewat']:>6}")
        if m >= 1 and r["lewat"]:
            failures.append(f"p{m}: {r['lewat']} samples lost, load not representative")
        if m >= 2 and not r["beat"]:
            failures.append(f"p{m}: no beats, replay not running")
        if lalu is not None:
            dI, sd = r["I"] - ring[lalu]["I"], max(r["sd"], ring[lalu]["sd"])
            if dI < 0:
                failures.append(f"p{lalu}->p{m}: current dropped {dI:+.2f} mA (not monotonic)")
            elif dI <= 2 * sd:
                failures.append(f"p{lalu}->p{m}: difference {dI:+.2f} mA <= 2 x std {sd:.2f} "
                             "(this stage is not yet measurable)")
        lalu = m
    print("\nCheck: " + ("PASS" if not failures else "FAIL\n  " + "\n  ".join(failures)))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
