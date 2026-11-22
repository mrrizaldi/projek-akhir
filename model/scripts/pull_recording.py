import datetime
import os
import sys
import time

PORT = os.environ.get("ECG_PORT", "/dev/ttyACM0")
BAUD = 115200
TUJUAN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "data", "recordings")


def main() -> None:
    file_number = int(sys.argv[1]) if len(sys.argv) > 1 else None
    try:
        import serial
    except ImportError:
        sys.exit("pyserial is missing. Install with:\n"
                 "  .venv/bin/pip install -r requirements.txt")

    try:
        s = serial.Serial(PORT, BAUD, timeout=2)
    except Exception as e:
        sys.exit(f"Cannot open {PORT}: {e}\n"
                 "Is the board plugged in? Is another serial monitor still open? "
                 "Check with: lsof /dev/ttyACM0")

    time.sleep(1.0)
    s.reset_input_buffer()

    s.write(b"s")
    s.flush()
    time.sleep(0.6)
    status = s.readline().decode(errors="replace").strip()
    print(status or "(no status reply)")

    if "rekam=1" in status:
        print("Board is still recording: stopping and saving first.")
        s.write(b"r")
        s.flush()
        deadline = time.time() + 15
        while time.time() < deadline:
            line = s.readline().decode(errors="replace").rstrip()
            if line:
                print(line)
            if line.startswith("SIMPAN"):
                break

    s.reset_input_buffer()
    s.write(f"d{file_number}\n".encode() if file_number else b"d")
    s.flush()

    lines, started = [], False
    deadline = time.time() + 60
    while time.time() < deadline:
        line = s.readline().decode(errors="replace").rstrip()
        if not line:
            continue
        if "---MULAI---" in line:
            started = True
            continue
        if "---SELESAI---" in line:
            break
        if started:
            lines.append(line)
    s.close()

    if not lines:
        sys.exit("No recording on the board. Press REC to record first.")

    os.makedirs(TUJUAN, exist_ok=True)
    name = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    if file_number:
        name += f"-rekam-{file_number:03d}"
    path = os.path.join(TUJUAN, f"{name}.csv")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n{len(lines)} lines -> {path}")
    print(f"{lines[0]}\n\nContinue with analysis:\n  .venv/bin/python scripts/analyze_recording.py {path} {name}")


if __name__ == "__main__":
    main()
