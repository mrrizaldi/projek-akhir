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
        batas = time.time() + 20
        while self.status()["rekam"] is None and time.time() < batas:
            time.sleep(1.0)

    def kirim(self, perintah, tunggu=1.0, sampai=None):
        self.s.reset_input_buffer()
        self.s.write(perintah.encode())
        self.s.flush()
        sisa, baris, batas = b"", [], time.time() + tunggu
        while time.time() < batas:
            sisa += self.s.read(self.s.in_waiting or 1)
            *lengkap, sisa = sisa.split(b"\n")
            baris += [t for t in (x.decode(errors="replace").rstrip() for x in lengkap) if t]
            if sampai and ada(baris, sampai):
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


def periksa(nama, syarat):
    gagal = [k for k, ok in syarat if not ok]
    hasil.append(not gagal)
    print(f"{'LULUS' if not gagal else 'GAGAL'}  {nama}")
    for k in gagal:
        print(f"         x {k}")


def main():
    port = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ECG_PORT")
            or next(iter(sorted(glob.glob("/dev/ttyACM*"))), None))
    if not port:
        sys.exit("Board tidak ditemukan (/dev/ttyACM*). Beri port sebagai argumen.")
    b = Board(port)
    st = b.status()
    print(f"port {port}, awal: {st}")
    if st["rekam"] != "0" or st["menu"] != "0" or st["daya"] != "-1":
        sys.exit("Prasyarat: tidak merekam, menu tertutup, mode daya normal (cek 's').\n"
                 "Pakai: uji_alur_rekam.py [port]")
    if st["sumber"] != "adc":
        b.kirim("y\n", 2.0)
    lewati0 = b.status()["lewati"]
    hilang_selama_rekam = []
    nomor = None
    try:
        o = b.kirim("r", 1.0) + b.kirim("T2", 1.5)
        st = b.status(); hilang_selama_rekam.append(st["hilang"])
        periksa("a. merekam -> T2: menu terkunci", [
            ("REKAM mulai", ada(o, r"^REKAM mulai")),
            ("pesan 'DITOLAK: menu'", ada(o, r"DITOLAK: menu")),
            ("menu tidak dibuka", not ada(o, r"^menu: MENU")),
            ("status menu 0, rekam=1", st["menu"] == "0" and st["rekam"] == "1")])

        o = b.kirim("j", 1.0) + b.kirim("T2", 1.5)
        st = b.status(); hilang_selama_rekam.append(st["hilang"])
        periksa("b. jeda -> T2: menu tetap terkunci", [
            ("REKAM jeda", ada(o, r"^REKAM jeda")),
            ("pesan 'DITOLAK: menu'", ada(o, r"DITOLAK: menu")),
            ("status menu 0, jeda 1", st["menu"] == "0" and st["jeda"] == "1")])
        b.kirim("j", 1.0)

        n0 = b.status()["n"]
        syarat = []
        for cmd, pola in [("y", "ganti sumber"), ("V", "tangga daya"), ("p3", "mode daya"),
                          ("k", "lewati kalibrasi"), ("w0\n", "ganti WiFi"),
                          ("b0\n", "ganti broker")]:
            o = b.kirim(cmd, 1.2)
            syarat.append((f"{cmd.strip()} -> 'DITOLAK: {pola}'", ada(o, f"DITOLAK: {pola}")))
            syarat.append((f"{cmd.strip()} tanpa efek", not ada(o, r"^replay |^tangga: mulai|"
                                                                r"^daya: mode|tidak ada, lihat")))
        st = b.status(); hilang_selama_rekam.append(st["hilang"])
        periksa("c. merekam -> y/V/p3/k/w0/b0 ditolak", syarat + [
            ("sumber adc", st["sumber"] == "adc"), ("daya -1", st["daya"] == "-1"),
            ("lewati tidak berubah", st["lewati"] == lewati0),
            ("rekam=1, jeda 0", st["rekam"] == "1" and st["jeda"] == "0"),
            (f"rekaman bertambah ({n0} -> {st['n']})", st["n"] > n0 > 0)])

        b.kirim("j", 1.0); b.kirim("j", 2.0)
        st = b.status(); hilang_selama_rekam.append(st["hilang"])
        o = b.kirim("T3", 20.0, r"^SIMPAN|GAGAL")
        simpan = next((x for x in o if x.startswith("SIMPAN")), "")
        m = re.search(r"/rekam/(\d+)\.csv", simpan)
        nomor = int(m.group(1)) if m else None
        daftar = b.kirim("l", 2.0)
        isi = b.kirim(f"d{nomor}\n", 30.0, r"---SELESAI---") if nomor else []
        sampel = [x for x in isi if x.isdigit()]
        hdr = next((x for x in isi if x.startswith("# fs=")), "")
        n_hdr = int((re.search(r" n=(\d+)", hdr) or [0, -1])[1])
        st = b.status()
        periksa("f. jeda/lanjut -> T3 simpan", [
            (f"SIMPAN ke /rekam/NNN.csv: {simpan!r}", nomor is not None),
            ("berkas ada di 'l'", nomor is not None and ada(daftar, rf"^\s+{nomor}\s+\d+ B\s+# fs=")),
            ("berkas memuat '# jeda'", "# jeda" in isi),
            (f"jumlah sampel = header n ({len(sampel)} vs {n_hdr})", len(sampel) == n_hdr > 0),
            ("header lewat=0", "lewat=0 " in hdr),
            (f"sampel hilang 0 selama rekaman {hilang_selama_rekam}", all(h == 0 for h in hilang_selama_rekam)),
            ("sesi tertutup (rekam=0)", st["rekam"] == "0")])

        o = b.kirim("T2", 1.5); m1 = b.status()["menu"]
        o2 = b.kirim("T3", 1.5); m0 = b.status()["menu"]
        periksa("g. sesudah simpan: T2 buka menu, T3 keluar", [
            ("menu: MENU", ada(o, r"^menu: MENU")), ("menu 1", m1 == "1"),
            ("menu: tutup", ada(o2, r"^menu: tutup")), ("menu 0", m0 == "0")])

        o = b.kirim("y", 2.0)
        o3 = b.kirim("t3", 1.5); o_r = b.kirim("r", 1.0)
        st = b.status()
        o4 = b.kirim("y", 2.0); akhir = b.status()["sumber"]
        periksa("d. REPLAY 208 -> t3 / r ditolak", [
            ("replay ON (golden_raw)", ada(o, r"replay ON \(golden_raw\)")),
            ("t3 -> 'REKAM hanya dari sensor'", ada(o3, r"REKAM hanya dari sensor")),
            ("r -> 'REKAM hanya dari sensor'", ada(o_r, r"REKAM hanya dari sensor")),
            ("rekam=0", st["rekam"] == "0"),
            ("kembali ke ADC (status sumber adc)", akhir == "adc")])

        b.kirim("T2", 1.5)
        o = b.kirim("r", 1.0); st = b.status()
        b.kirim("T3", 1.5); m0 = b.status()["menu"]
        periksa("e. menu terbuka -> r ditolak", [
            ("'REKAM ditolak: tutup menu dulu'", ada(o, r"REKAM ditolak: tutup menu dulu")),
            ("rekam=0, menu 1", st["rekam"] == "0" and st["menu"] == "1"),
            ("menu tertutup lagi", m0 == "0")])
    finally:
        st = b.status()
        if st["menu"] == "1":
            b.kirim("T3", 1.5)
        if st["rekam"] == "1":
            o = b.kirim("r", 20.0, r"^SIMPAN|GAGAL")
            m = re.search(r"/rekam/(\d+)\.csv", " ".join(o))
            if m and nomor is None:
                nomor = int(m.group(1))
        if nomor:
            b.kirim(f"h{nomor}\n", 1.5)
        if b.status()["sumber"] != "adc":
            b.kirim("y\n", 2.0)
        print(f"akhir: {b.status()}")
    print(f"{sum(hasil)}/{len(hasil)} skenario LULUS")
    sys.exit(0 if hasil and all(hasil) else 1)


if __name__ == "__main__":
    main()
