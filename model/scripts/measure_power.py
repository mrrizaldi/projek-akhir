"""Tangga ukur daya p0..p5 lewat serial, hasil ke artifacts/metrics/daya/<ts>.csv.

    .venv/bin/python scripts/measure_power.py            (dari folder model/)

Rancangan: docs/arsip/2026-09-16-daya-design.md. Firmware mencetak satu baris
`DAYA pN ...` per jendela 10 detik (rata-rata INA219 tiap 100 ms). Skrip ini
menyalakan replay bila belum (beban identik tiap ulangan), menjalankan tiap
mode, membuang jendela pertama (transien ganti mode), lalu merangkum.

Berhenti tanpa menulis CSV bila tegangan bus < 1 V: INA219 tidak berada di
jalur arus alat, dan angka arusnya bukan konsumsi siapa pun.

Opsi: --port /dev/ttyACM0  --blok 6 (jendela 10 s per mode)  --mode 012345
      --paksa (lewati cek catu; hanya untuk menguji jalur, angka tidak sah)
      --keluar DIR
"""
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
POLA = re.compile(r"DAYA p(\d) n=(\d+) I=([-\d.]+) sd=([-\d.]+) mA V=([-\d.]+) "
                  r"P=([-\d.]+) mW beat=(\d+) lewat=(\d+) replay=(\d)")
KOLOM = ["waktu", "mode", "n", "I_mA", "sd_mA", "V", "P_mW", "beat", "lewat", "replay"]
NAMA = {0: "timer ISR mati", 1: "+ ISR 360 Hz", 2: "+ DSP ecg_live", 3: "+ inferensi CNN",
        4: "+ UI (TFT, bip, LED)", 5: "+ WiFi/MQTT"}


def tunggu(s, isi, detik):
    akhir = time.time() + detik
    while time.time() < akhir:
        b = s.readline().decode("utf-8", "replace").rstrip()
        if b:
            print("  " + b)
            if isi in b:
                return b
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=os.environ.get("ECG_PORT", "/dev/ttyACM0"))
    ap.add_argument("--blok", type=int, default=6)
    ap.add_argument("--mode", default="012345")
    ap.add_argument("--paksa", action="store_true")
    ap.add_argument("--keluar", default=os.path.join(MODEL, "artifacts", "metrics", "daya"))
    a = ap.parse_args()

    s = serial.Serial()
    s.port, s.baudrate, s.timeout = a.port, 115200, 0.2
    s.dtr = s.rts = False            # membuka port tanpa ini me-reset board
    s.open()
    # USB JTAG/serial ESP32-S3 tetap bisa reboot saat port dibuka: tunggu boot
    # selesai bila itu terjadi (tanpa reboot, ini cuma jeda 6 detik).
    tunggu(s, "MONITOR ARITMIA SIAP", 6)
    time.sleep(1.0)

    s.write(b"s")
    st = tunggu(s, "replay=", 3)
    if st is None:
        sys.exit("Board tidak menjawab 's'.")
    replay_awal = "replay=1" in st
    if not replay_awal:
        s.write(b"y")
        if not tunggu(s, "replay ON", 3):
            sys.exit("Replay gagal dinyalakan.")

    baris = []
    try:
        for m in map(int, a.mode):
            s.write(f"p{m}".encode())
            if not tunggu(s, f"daya: mode p{m}", 3):
                sys.exit(f"Mode p{m} tidak dikonfirmasi board.")
            dapat = 0
            akhir = time.time() + (a.blok + 3) * 10 + 5
            while dapat <= a.blok and time.time() < akhir:
                b = s.readline().decode("utf-8", "replace").rstrip()
                g = POLA.search(b)
                if not g or int(g.group(1)) != m:
                    continue
                print("  " + b)
                dapat += 1
                if not a.paksa and float(g.group(5)) < 1.0:
                    sys.exit(f"\nTegangan bus {g.group(5)} V: INA219 tidak berada di jalur arus "
                             "alat (VIN- tidak tersambung ke catu yang mengalir).\nTidak ada "
                             "yang ditulis. Rakit jalur ukur sesuai docs/firmware-walkthrough.md "
                             "§5d Prosedur ukur daya, lalu ulangi.")
                if dapat == 1:
                    continue         # jendela pertama: transien ganti mode
                baris.append([datetime.datetime.now().isoformat(timespec="seconds"), m,
                              *g.groups()[1:]])
            if dapat <= a.blok:
                sys.exit(f"Mode p{m}: hanya {dapat} jendela diterima.")
    finally:
        s.write(b"px")               # kembali ke operasi normal
        if not replay_awal:
            time.sleep(0.6)
            s.write(b"y")
        s.close()

    os.makedirs(a.keluar, exist_ok=True)
    berkas = os.path.join(a.keluar, datetime.datetime.now().strftime("%Y%m%d-%H%M") + ".csv")
    with open(berkas, "w", newline="") as f:
        csv.writer(f).writerows([KOLOM] + baris)
    print(f"\nCSV: {berkas}\n")

    ring = {}
    for m in map(int, a.mode):
        r = [x for x in baris if x[1] == m]
        i = [float(x[3]) for x in r]
        ring[m] = dict(I=statistics.mean(i), sd=statistics.stdev(i) if len(i) > 1 else 0.0,
                       V=statistics.mean(float(x[5]) for x in r),
                       P=statistics.mean(float(x[6]) for x in r),
                       beat=sum(int(x[7]) for x in r), lewat=sum(int(x[8]) for x in r))
    print(f"{'mode':<26}{'I (mA)':>16}{'V':>8}{'P (mW)':>9}{'delta I':>9}{'beat':>6}{'lewat':>6}")
    gagal = []
    lalu = None
    for m, r in ring.items():
        d = "" if lalu is None else f"{r['I'] - ring[lalu]['I']:+.2f}"
        print(f"p{m} {NAMA[m]:<23}{r['I']:>9.2f} ± {r['sd']:<4.2f}{r['V']:>8.3f}{r['P']:>9.1f}"
              f"{d:>9}{r['beat']:>6}{r['lewat']:>6}")
        if m >= 1 and r["lewat"]:
            gagal.append(f"p{m}: {r['lewat']} sampel hilang, beban tidak mewakili")
        if m >= 2 and not r["beat"]:
            gagal.append(f"p{m}: tidak ada beat, replay tidak berjalan")
        if lalu is not None:
            dI, sd = r["I"] - ring[lalu]["I"], max(r["sd"], ring[lalu]["sd"])
            if dI < 0:
                gagal.append(f"p{lalu}->p{m}: arus turun {dI:+.2f} mA (tidak monoton)")
            elif dI <= 2 * sd:
                gagal.append(f"p{lalu}->p{m}: selisih {dI:+.2f} mA <= 2 x std {sd:.2f} "
                             "(tahap ini belum terukur)")
        lalu = m
    print("\nCek: " + ("LULUS" if not gagal else "GAGAL\n  " + "\n  ".join(gagal)))
    sys.exit(1 if gagal else 0)


if __name__ == "__main__":
    main()
