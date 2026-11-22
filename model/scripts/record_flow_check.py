import glob
import os
import re
import sys
import time

import serial

hasil = []


class Board:
    def __init__(self, port):
        self.s = serial.Serial()
        self.s.port, self.s.baudrate, self.s.timeout = port, 115200, 0.1
        self.s.dtr = self.s.rts = False
        self.s.open()
        deadline = time.time() + 20
        while self.status()["rekam"] is None and time.time() < deadline:
            time.sleep(1.0)

    def kirim(self, perintah, wait_s=1.0, until=None):
        self.s.reset_input_buffer()
        self.s.write(perintah.encode())
        self.s.flush()
        sisa, baris, deadline = b"", [], time.time() + wait_s
        while time.time() < deadline:
            sisa += self.s.read(self.s.in_waiting or 1)
            *lengkap, sisa = sisa.split(b"\n")
            baris += [t for t in (x.decode(errors="replace").rstrip() for x in lengkap) if t]
            if until and ada(baris, until):
                break
        return baris

    def status(self):
        teks = "\n".join(self.kirim("s", 1.0, r"sumber \w+ -?\d+ \| menu"))
        def m(pola):
            return (re.search(pola, teks) or [None, None])[1]
        return {"rekam": m(r"rekam=(\d)"), "n": int(m(r"rekam=\d n=(\d+)") or -1),
                "hilang": int(m(r"sampel hilang (\d+)") or -1), "lewati": m(r"lewati (\d)"),
                "daya": m(r"daya (-?\d)"), "sumber": m(r"sumber (\w+)"),
                "menu": m(r"menu (\d)"), "jeda": m(r"jeda (\d)")}


def ada(baris, pola):
    return any(re.search(pola, b) for b in baris)


def periksa(nama, conditions):
    failed = [k for k, ok in conditions if not ok]
    hasil.append(not failed)
    print(f"{'PASS' if not failed else 'FAIL'}  {nama}")
    for k in failed:
        print(f"         x {k}")


def main():
    port = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ECG_PORT")
            or next(iter(sorted(glob.glob("/dev/ttyACM*"))), None))
    if not port:
        sys.exit("Board not found (/dev/ttyACM*). Pass the port as an argument.")
    b = Board(port)
    st = b.status()
    print(f"port {port}, start: {st}")
    if st["rekam"] != "0" or st["menu"] != "0" or st["daya"] != "-1":
        sys.exit("Prerequisite: not recording, menu closed, normal power mode (check 's').\n"
                 "Usage: record_flow_check.py [port]")
    if st["sumber"] != "adc":
        b.kirim("y\n", 2.0)
    skip_before = b.status()["lewati"]
    lost_during_recording = []
    file_number = None
    try:
        o = b.kirim("r", 1.0) + b.kirim("T2", 1.5)
        st = b.status(); lost_during_recording.append(st["hilang"])
        periksa("a. recording -> T2: menu locked", [
            ("REKAM mulai printed", ada(o, r"^REKAM mulai")),
            ("message 'DITOLAK: menu'", ada(o, r"DITOLAK: menu")),
            ("menu not opened", not ada(o, r"^menu: MENU")),
            ("status menu 0, rekam=1", st["menu"] == "0" and st["rekam"] == "1")])

        o = b.kirim("j", 1.0) + b.kirim("T2", 1.5)
        st = b.status(); lost_during_recording.append(st["hilang"])
        periksa("b. pause -> T2: menu stays locked", [
            ("REKAM jeda printed", ada(o, r"^REKAM jeda")),
            ("message 'DITOLAK: menu'", ada(o, r"DITOLAK: menu")),
            ("status menu 0, jeda 1", st["menu"] == "0" and st["jeda"] == "1")])
        b.kirim("j", 1.0)

        n0 = b.status()["n"]
        conditions = []
        for cmd, pola in [("y", "ganti sumber"), ("V", "tangga daya"), ("p3", "mode daya"),
                          ("k", "lewati kalibrasi"), ("w0\n", "ganti WiFi"),
                          ("b0\n", "ganti broker"), ("m", "WiFi")]:
            o = b.kirim(cmd, 1.2)
            conditions.append((f"{cmd.strip()} -> 'DITOLAK: {pola}'", ada(o, f"DITOLAK: {pola}")))
            conditions.append((f"{cmd.strip()} has no effect", not ada(o, r"^replay |^tangga: mulai|"
                                                                r"^daya: mode|tidak ada, lihat|^wifi (ON|OFF)")))
        st = b.status(); lost_during_recording.append(st["hilang"])
        periksa("c. recording -> y/V/p3/k/w0/b0/m rejected", conditions + [
            ("sumber adc", st["sumber"] == "adc"), ("daya -1", st["daya"] == "-1"),
            ("lewati unchanged", st["lewati"] == skip_before),
            ("rekam=1, jeda 0", st["rekam"] == "1" and st["jeda"] == "0"),
            (f"recording grew ({n0} -> {st['n']})", st["n"] > n0 > 0)])

        b.kirim("j", 1.0); b.kirim("j", 2.0)
        st = b.status(); lost_during_recording.append(st["hilang"])
        o = b.kirim("T3", 20.0, r"^SIMPAN|GAGAL")
        save_item = next((x for x in o if x.startswith("SIMPAN")), "")
        m = re.search(r"/rekam/(\d+)\.csv", save_item)
        file_number = int(m.group(1)) if m else None
        listing = b.kirim("l", 2.0)
        lines = b.kirim(f"d{file_number}\n", 30.0, r"---SELESAI---") if file_number else []
        sampel = [x for x in lines if x.isdigit()]
        hdr = next((x for x in lines if x.startswith("# fs=")), "")
        n_hdr = int((re.search(r" n=(\d+)", hdr) or [0, -1])[1])
        st = b.status()
        periksa("f. pause/resume -> T3 save", [
            (f"SIMPAN to /rekam/NNN.csv: {save_item!r}", file_number is not None),
            ("file listed by 'l'", file_number is not None and ada(listing, rf"^\s+{file_number}\s+\d+ B\s+# fs=")),
            ("file contains '# jeda'", "# jeda" in lines),
            (f"sample count = header n ({len(sampel)} vs {n_hdr})", len(sampel) == n_hdr > 0),
            ("header lewat=0", "lewat=0 " in hdr),
            (f"0 samples lost during recording {lost_during_recording}", all(h == 0 for h in lost_during_recording)),
            ("session closed (rekam=0)", st["rekam"] == "0")])

        o = b.kirim("T2", 1.5); m1 = b.status()["menu"]
        o2 = b.kirim("T3", 1.5); m0 = b.status()["menu"]
        periksa("g. after save: T2 opens menu, T3 leaves", [
            ("menu: MENU", ada(o, r"^menu: MENU")), ("menu 1", m1 == "1"),
            ("menu: tutup", ada(o2, r"^menu: tutup")), ("menu 0", m0 == "0")])

        o = b.kirim("y", 2.0)
        o3 = b.kirim("t3", 1.5); o_r = b.kirim("r", 1.0)
        st = b.status()
        o4 = b.kirim("y", 2.0); akhir = b.status()["sumber"]
        periksa("d. REPLAY 208 -> t3 / r rejected", [
            ("replay ON (golden_raw)", ada(o, r"replay ON \(golden_raw\)")),
            ("t3 -> 'REKAM hanya dari sensor'", ada(o3, r"REKAM hanya dari sensor")),
            ("r -> 'REKAM hanya dari sensor'", ada(o_r, r"REKAM hanya dari sensor")),
            ("rekam=0", st["rekam"] == "0"),
            ("back to ADC (status sumber adc)", akhir == "adc")])

        b.kirim("T2", 1.5)
        o = b.kirim("r", 1.0); st = b.status()
        b.kirim("T3", 1.5); m0 = b.status()["menu"]
        periksa("e. menu open -> r rejected", [
            ("'REKAM ditolak: tutup menu dulu'", ada(o, r"REKAM ditolak: tutup menu dulu")),
            ("rekam=0, menu 1", st["rekam"] == "0" and st["menu"] == "1"),
            ("menu closed again", m0 == "0")])
    finally:
        st = b.status()
        if st["menu"] == "1":
            b.kirim("T3", 1.5)
        if st["rekam"] == "1":
            o = b.kirim("r", 20.0, r"^SIMPAN|GAGAL")
            m = re.search(r"/rekam/(\d+)\.csv", " ".join(o))
            if m and file_number is None:
                file_number = int(m.group(1))
        if file_number:
            b.kirim(f"h{file_number}\n", 1.5)
        if b.status()["sumber"] != "adc":
            b.kirim("y\n", 2.0)
        print(f"end: {b.status()}")
    print(f"{sum(hasil)}/{len(hasil)} scenarios PASS")
    sys.exit(0 if hasil and all(hasil) else 1)


if __name__ == "__main__":
    main()
