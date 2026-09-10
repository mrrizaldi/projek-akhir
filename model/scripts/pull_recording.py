"""Tarik rekaman dari board ke data/recordings/<tanggal-jam>.csv.

    make pull                  (atau langsung, lihat catatan interpreter)

CATATAN INTERPRETER: skrip ini butuh `pyserial`, yang TIDAK ada di .venv model
(dan sengaja tidak ditambahkan — lihat gate point dependency di CLAUDE.md).
Jalankan dengan Python milik PlatformIO yang sudah punya pyserial:

    ~/.platformio/penv/bin/python scripts/pull_recording.py

Makanya skrip ini HANYA memakai stdlib + pyserial — tanpa numpy/matplotlib.
Analisis dikerjakan terpisah oleh scripts/analyze_recording.py di .venv model.

Kalau board masih merekam, skrip menghentikan & menyimpannya dulu.
"""
import datetime
import os
import sys
import time

PORT = os.environ.get("ECG_PORT", "/dev/ttyACM0")
BAUD = 115200
TUJUAN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "data", "recordings")


def main() -> None:
    try:
        import serial
    except ImportError:
        sys.exit("pyserial tidak ada. Jalankan dengan:\n"
                 "  ~/.platformio/penv/bin/python scripts/pull_recording.py")

    try:
        s = serial.Serial(PORT, BAUD, timeout=2)
    except Exception as e:                                   # noqa: BLE001
        sys.exit(f"Tidak bisa membuka {PORT}: {e}\n"
                 "Board tercolok? Serial monitor lain masih terbuka? "
                 "Cek dengan: lsof /dev/ttyACM0")

    time.sleep(1.0)
    s.reset_input_buffer()

    s.write(b"s")
    s.flush()
    time.sleep(0.6)
    status = s.readline().decode(errors="replace").strip()
    print(status or "(tidak ada balasan status)")

    if "rekam=1" in status:
        print("Board masih merekam — dihentikan & disimpan dulu.")
        s.write(b"r")
        s.flush()
        batas = time.time() + 15
        while time.time() < batas:
            baris = s.readline().decode(errors="replace").rstrip()
            if baris:
                print(baris)
            if baris.startswith("SIMPAN"):
                break

    s.reset_input_buffer()
    s.write(b"d")
    s.flush()

    isi, mulai = [], False
    batas = time.time() + 60
    while time.time() < batas:
        baris = s.readline().decode(errors="replace").rstrip()
        if not baris:
            continue
        if "---MULAI---" in baris:
            mulai = True
            continue
        if "---SELESAI---" in baris:
            break
        if mulai:
            isi.append(baris)
    s.close()

    if not isi:
        sys.exit("Tidak ada rekaman di board. Tekan REC untuk merekam dulu.")

    os.makedirs(TUJUAN, exist_ok=True)
    nama = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    path = os.path.join(TUJUAN, f"{nama}.csv")
    with open(path, "w") as f:
        f.write("\n".join(isi) + "\n")

    print(f"\n{len(isi)} baris -> {path}")
    print(f"{isi[0]}\n\nLanjut analisis:\n  .venv/bin/python scripts/analyze_recording.py {path} {nama}")


if __name__ == "__main__":
    main()
