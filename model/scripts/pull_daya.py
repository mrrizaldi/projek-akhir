"""Tarik hasil tangga daya mandiri (/daya/NNN.csv di board) ke
artifacts/metrics/daya/<tanggal-jam>-board-NNN.csv, lalu ringkas & validasi.

    make pull-daya            (berkas terakhir)    make pull-daya N=3
    .venv/bin/python scripts/pull_daya.py [N]

Tangga dijalankan di board tanpa laptop (menu Ukur daya atau serial 'V').
Kolom = CSV measure_power.py + 'sah' (penilaian board per mode). Validasi di
sini diulang dengan kriteria measure_power.py, jadi dua penilaian bisa dibandingkan.
Port lain: ECG_PORT=/dev/ttyACM1 make pull-daya
"""
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
NAMA = {0: "timer ISR mati", 1: "+ ISR 360 Hz", 2: "+ DSP ecg_live", 3: "+ inferensi CNN",
        4: "+ UI (TFT, bip, LED)", 5: "+ WiFi/MQTT"}


def baca_sampai(s, akhir, detik):
    """Baris serial sampai baris yang memuat `akhir` (inklusif) atau batas waktu."""
    isi, batas = [], time.time() + detik
    while time.time() < batas:
        b = s.readline().decode(errors="replace").rstrip()
        if b:
            isi.append(b)
            if akhir in b:
                return isi
    return None


def validasi(baris):
    """Kriteria measure_power.py atas baris CSV board. Return (ringkasan, gagal)."""
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
            gagal.append(f"p{m}: V bus {g['vmin']:.3f} V < 1 V, INA219 tidak di jalur catu")
        if m >= 1 and g["lewat"]:
            gagal.append(f"p{m}: {g['lewat']} sampel hilang, beban tidak mewakili")
        if m >= 2 and not g["beat"]:
            gagal.append(f"p{m}: tidak ada beat, replay tidak berjalan")
        if lalu is not None:
            dI, sd = g["I"] - ring[lalu]["I"], max(g["sd"], ring[lalu]["sd"])
            if dI < 0:
                gagal.append(f"p{lalu}->p{m}: arus turun {dI:+.2f} mA (tidak monoton)")
            elif dI <= 2 * sd:
                gagal.append(f"p{lalu}->p{m}: selisih {dI:+.2f} mA <= 2 x std {sd:.2f}")
        lalu = m
    if len(ring) < 6:
        gagal.append(f"hanya {len(ring)} dari 6 mode (tangga batal di tengah)")
    return ring, gagal


def main() -> None:
    try:
        import serial
    except ImportError:
        sys.exit("pyserial tidak ada. Pasang dengan:\n  .venv/bin/pip install -r requirements.txt")

    s = serial.Serial()
    s.port, s.baudrate, s.timeout = PORT, 115200, 0.5
    s.dtr = s.rts = False            # membuka port tanpa ini me-reset board
    try:
        s.open()
    except Exception as e:                                   # noqa: BLE001
        sys.exit(f"Tidak bisa membuka {PORT}: {e}\nSerial monitor lain masih terbuka?")

    # USB JTAG/serial S3 kadang tetap me-reboot board saat port dibuka: ulangi
    # 'v' sampai board menjawab (boot sampai loop() +-3 s).
    daftar = None
    for _ in range(5):
        time.sleep(1.0)
        s.reset_input_buffer()
        s.write(b"v")
        daftar = baca_sampai(s, "daya: akhir daftar", 3)
        if daftar:
            break
    if not daftar:
        sys.exit("Board tidak menjawab 'v' (firmware lama tanpa tangga mandiri?).")
    nomor = sorted(int(g.group(1)) for b in daftar if (g := re.match(r"\s+(\d+)\s+\d+ B", b)))
    print("Berkas di board: " + (", ".join(f"{n:03d}" for n in nomor) or "(kosong)"))
    if not nomor:
        sys.exit("Belum ada hasil tangga. Jalankan menu Ukur daya atau serial 'V' dulu.")
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else nomor[-1]

    s.reset_input_buffer()
    s.write(f"v{n}".encode())
    isi = baca_sampai(s, "---SELESAI---", 10)
    s.close()
    if not isi or "---MULAI---" not in isi:
        sys.exit(f"Berkas {n:03d} tidak terbaca: {isi[-1] if isi else 'tidak ada balasan'}")
    isi = isi[isi.index("---MULAI---") + 1:-1]

    os.makedirs(TUJUAN, exist_ok=True)
    path = os.path.join(TUJUAN, datetime.datetime.now().strftime("%Y%m%d-%H%M")
                        + f"-board-{n:03d}.csv")
    with open(path, "w") as f:
        f.write("\n".join(isi) + "\n")
    print(f"{len(isi) - 1} jendela -> {path}\n")

    ring, gagal = validasi(list(csv.DictReader(io.StringIO("\n".join(isi)))))
    print(f"{'mode':<26}{'I (mA)':>16}{'V':>8}{'P (mW)':>9}{'delta I':>9}{'beat':>6}"
          f"{'lewat':>6}  board")
    lalu = None
    for m, r in ring.items():
        d = "" if lalu is None else f"{r['I'] - ring[lalu]['I']:+.2f}"
        print(f"p{m} {NAMA[m]:<23}{r['I']:>9.2f} ± {r['sd']:<4.2f}{r['V']:>8.3f}{r['P']:>9.1f}"
              f"{d:>9}{r['beat']:>6}{r['lewat']:>6}  {'sah' if r['sah'] else 'TIDAK SAH'}")
        lalu = m
    print("\nCek: " + ("LULUS" if not gagal else "GAGAL (TIDAK SAH)\n  " + "\n  ".join(gagal)))
    sys.exit(1 if gagal else 0)


if __name__ == "__main__":
    main()
