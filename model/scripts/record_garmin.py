"""Rekam HR (dan RR kalau ada) dari broadcast BLE Garmin ke CSV.

    .venv/bin/python scripts/record_garmin.py [detik] [nama]

Nyalakan Broadcast Heart Rate di jam dulu. Skrip memindai, menyambung ke
Heart Rate Service (0x180D), dan menyalakan notify pada Heart Rate
Measurement (0x2A37).

Paket pertama langsung memberi vonis: flags bit 4 menandakan ada-tidaknya
field RR. Kalau tidak ada, skrip tetap merekam HR — cukup untuk pembandingan
laju per-jendela, tidak cukup untuk pembandingan interval.

Keluaran: data/recordings/garmin-<tanggal-jam>.csv
    t_host   detik sejak skrip mulai, saat paket TIBA
    hr       bpm dari paket itu
    rr_ms    satu baris per RR (kosong kalau paket tak bawa RR)
"""
import asyncio
import datetime
import os
import sys

HR_MEASUREMENT = "00002a37-0000-1000-8000-00805f9b34fb"
NAMA_DEFAULT = os.environ.get("GARMIN_NAMA", "Forerunner")
TUJUAN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "data", "recordings")


def parse_hrm(data: bytes):
    """Bongkar paket Heart Rate Measurement → (flags, hr, [rr_ms]).

    Tata letaknya bergantung flags, jadi offset tiap field harus dihitung
    berjalan — tidak boleh dihardcode:
      bit0  0 = HR uint8, 1 = HR uint16
      bit3  1 = ada field Energy Expended (uint16) yang harus DILOMPATI
      bit4  1 = sisa paket berisi RR, uint16 masing-masing, satuan 1/1024 s
    """
    f = data[0]
    if f & 0x01:
        hr = int.from_bytes(data[1:3], "little")
        i = 3
    else:
        hr = data[1]
        i = 2
    if f & 0x08:
        i += 2
    rr = []
    if f & 0x10:
        while i + 1 < len(data):
            raw = int.from_bytes(data[i:i + 2], "little")
            rr.append(raw * 1000.0 / 1024.0)   # 1/1024 s, BUKAN ms
            i += 2
    return f, hr, rr


def waktu_detak(t_paket: float, rr_ms: list) -> list:
    """Beri cap waktu absolut untuk tiap RR dalam satu paket.

    TODO(user): ini keputusanmu — lihat catatan di chat.

    Yang diketahui: paket tiba pada t_paket, membawa 0..N interval RR yang
    SUDAH terjadi sebelum itu. Yang tidak diketahui: latensi siar (jam
    mengirim ~1 Hz, detaknya bisa terjadi hingga ~1 s sebelum paket tiba).

    Kembalikan list waktu detak (detik, seskala dengan t_paket), satu per RR.
    """
    raise NotImplementedError("isi waktu_detak()")


async def main() -> None:
    detik = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0
    nama = sys.argv[2] if len(sys.argv) > 2 else NAMA_DEFAULT

    try:
        from bleak import BleakClient, BleakScanner
    except ImportError:
        sys.exit("bleak tidak ada. Pasang dengan:\n"
                 "  .venv/bin/pip install bleak")

    print(f"Memindai '{nama}' (20 detik)... broadcast HR sudah nyala di jam?")
    dev = await BleakScanner.find_device_by_filter(
        lambda d, _: nama.lower() in (d.name or "").lower(), timeout=20.0)
    if dev is None:
        sys.exit(f"'{nama}' tidak ketemu. Broadcast masih nyala? "
                 "Jam tidak sedang tersambung ke HP? (BLE cuma satu koneksi)")
    print(f"Ketemu {dev.name} [{dev.address}] — menyambung...")

    os.makedirs(TUJUAN, exist_ok=True)
    cap = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(TUJUAN, f"garmin-{cap}.csv")

    loop = asyncio.get_running_loop()
    t0 = loop.time()
    vonis, n = [], [0]

    # Ditulis per baris, bukan ditumpuk lalu dibuang ke file di akhir: sesi ini
    # 5 menit dan sering diputus Ctrl-C. Buffer di memori = data hilang.
    fh = open(path, "w")
    fh.write(f"# sumber={dev.name} mulai={cap}\n")
    fh.write("t_host,hr,rr_ms\n")

    def on_notify(_, data: bytearray):
        t = loop.time() - t0
        f, hr, rr = parse_hrm(bytes(data))
        if not vonis:
            vonis.append(bool(f & 0x10))
            print(f"\npaket pertama: {bytes(data).hex(' ')}  flags=0x{f:02X}")
            print("  RR ADA — deret interval bisa dipakai\n" if f & 0x10 else
                  "  RR TIDAK ADA — cuma HR, terbatas ke laju per-jendela\n")
        for v in (rr or [None]):
            fh.write(f"{t:.3f},{hr},{'' if v is None else f'{v:.1f}'}\n")
            n[0] += 1
        fh.flush()
        print(f"\rt={t:6.1f}s  hr={hr:3d}  rr={len(rr)}  total={n[0]}",
              end="", flush=True)

    try:
        async with BleakClient(dev) as c:
            await c.start_notify(HR_MEASUREMENT, on_notify)
            print(f"Merekam {detik:.0f} detik. Ctrl-C untuk berhenti lebih awal.")
            await asyncio.sleep(detik)
            await c.stop_notify(HR_MEASUREMENT)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\ndihentikan")
    finally:
        fh.close()
    if not vonis:
        print("Tidak ada satu paket pun — jam masih menyiarkan? HP masih mencaplok koneksinya?")
    print(f"\n{n[0]} baris -> {path}")


def _self_check() -> None:
    # HR uint8, tanpa RR — persis yang terbaca di nRF tadi
    assert parse_hrm(bytes([0x06, 0x4F])) == (0x06, 79, [])
    # HR uint8 + satu RR 0x0320 = 800/1024 s
    f, hr, rr = parse_hrm(bytes([0x10, 0x3C, 0x20, 0x03]))
    assert (f, hr) == (0x10, 60) and abs(rr[0] - 781.25) < 0.01, rr
    # HR uint16 + energy expended dilompati + dua RR
    f, hr, rr = parse_hrm(bytes([0x19, 0x3C, 0x00, 0xE8, 0x03, 0x20, 0x03, 0x00, 0x04]))
    assert (f, hr) == (0x19, 60) and len(rr) == 2, (hr, rr)
    print("parse_hrm OK")


if __name__ == "__main__":
    if "--check" in sys.argv:
        _self_check()
    else:
        asyncio.run(main())
