#!/usr/bin/env python3
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

DIR = Path(__file__).resolve().parent
SCH = DIR / "mainboard.kicad_sch"
PCB = DIR / "mainboard.kicad_pcb"

PIN_U1 = {
    "41": "ECG_OUT", "40": "ECG_LON", "39": "ECG_LOP",
    "15": "TFT_SCK", "12": "TFT_MOSI", "16": "TFT_RST", "17": "TFT_DC",
    "19": "BUZZ", "4": "BTN1", "5": "BTN2", "6": "BTN3",
    "10": "I2C_SDA", "11": "I2C_SCL",
    "1": "+3V3", "2": "+3V3", "21": "+5V",
    "22": "GND", "23": "GND", "24": "GND", "44": "GND",
}

PIN_LAIN = {
    "J3": ["GND", "+3V3", "ECG_OUT", "ECG_LON", "ECG_LOP", "+3V3"],
    "J2": ["GND", "+3V3", "TFT_SCK", "TFT_MOSI", "TFT_RST", "TFT_DC", "GND", "+3V3"],
    "J9": ["GND", "BUZZ", "+3V3"],
    "SW1": ["BTN1", "GND"], "SW2": ["BTN2", "GND"], "SW3": ["BTN3", "GND"],
    "U2": ["+3V3", "GND", "I2C_SCL", "I2C_SDA", "VBAT_SENSE", "VBAT_OUT"],
    "J4": ["VCHG", "GND"], "J5": ["BAT+", "BAT-"], "J6": ["VBAT_OUT", "GND"], "J8": ["BAT+", "BAT-"],
    "Q1": ["VCHG", "VSYS", "VBAT_SENSE"],
    "R1": ["VCHG", "GND"], "R2": ["VBAT_SENSE", "GND"],
    "D1": ["VSYS", "VCHG"], "D2": ["+5V", "VBOOST"],
    "J10": ["VSYS", "VSW", "GND"],
    "J1": ["VSW", "GND", "VBOOST", "GND"],
    "C1": ["+5V", "GND"], "C2": ["+5V", "GND"],
    "C3": ["+3V3", "GND"], "C4": ["+3V3", "GND"], "C5": ["+3V3", "GND"], "C6": ["+3V3", "GND"],
}

BOLEH_5V = {"U1", "C1", "C2", "D2"}


def netlist(tmp):
    keluar = Path(tmp) / "n.xml"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(keluar), str(SCH)],
                   check=True, capture_output=True)
    pin = {}
    for net in ET.parse(keluar).getroot().iter("net"):
        for node in net.iter("node"):
            pin[(node.get("ref"), node.get("pin"))] = net.get("name").lstrip("/")
    return pin


def harapan():
    hasil = {("U1", p): n for p, n in PIN_U1.items()}
    for ref, nets in PIN_LAIN.items():
        hasil.update({(ref, str(i + 1)): n for i, n in enumerate(nets)})
    return hasil


def laporan(perintah):
    with tempfile.TemporaryDirectory() as tmp:
        lapor = Path(tmp) / "r.rpt"
        subprocess.run(perintah + ["-o", str(lapor)], check=True, capture_output=True)
        return lapor.read_text()


def main():
    gagal = 0
    with tempfile.TemporaryDirectory() as tmp:
        pin = netlist(tmp)
    exp = harapan()
    salah = [(k, v, pin.get(k)) for k, v in sorted(exp.items()) if pin.get(k) != v]
    for (ref, p), v, ada in salah:
        print(f"SALAH {ref}.{p}: harus {v}, tertulis {ada}")
    print(f"netlist: {len(exp) - len(salah)}/{len(exp)} pin sesuai peta")
    gagal += bool(salah)

    bocor = sorted(k for k, v in pin.items() if v == "+5V" and k[0] not in BOLEH_5V and not k[0].startswith("#"))
    print(f"+5V di luar jalur daya: {bocor or 'tidak ada'}")
    gagal += bool(bocor)

    teks = laporan(["kicad-cli", "sch", "erc", "--severity-all", str(SCH)])
    erc = {k: int(v) for k, v in re.findall(r"(Errors|Warnings) (\d+)", teks)}
    print(f"ERC: error {erc.get('Errors')} warning {erc.get('Warnings')}")
    gagal += erc.get("Errors", 1) > 0

    teks = laporan(["kicad-cli", "pcb", "drc", "--severity-error", "--schematic-parity", str(PCB)])
    drc = {v: int(k) for k, v in re.findall(r"Found (\d+) (DRC violations|unconnected pads|Footprint errors)", teks)}
    print(f"DRC error: {drc.get('DRC violations')}, unconnected: {drc.get('unconnected pads')}, "
          f"paritas skematik: {drc.get('Footprint errors')}")
    gagal += any(drc.get(k, 1) for k in ("DRC violations", "unconnected pads", "Footprint errors"))

    print("LULUS" if not gagal else "GAGAL")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
