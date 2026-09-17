"""Analisis kualitas rekaman EKG dari device.

    python scripts/analyze_recording.py <rekaman.csv> [nama]

Masukan: keluaran `dump` firmware (baris '# fs=.. n=.. lewat=..' lalu satu
nilai ADC per baris). Menilai dengan ANGKA, bukan dengan melihat grafik:
dengung PLN, derau HF, drift baseline, dan apakah Pan-Tompkins menemukan
detak yang konsisten.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from config import FS, METRICS_DIR  # noqa: E402
from scipy.signal import butter, sosfilt  # noqa: E402

from src.preprocessing import (  # noqa: E402
    apply_bandpass, design_bandpass_sos, pan_tompkins_detect,
)


def denyut_autokorelasi(x, fs):
    """Ada denyut periodik atau tidak — tanpa mendeteksi puncak sama sekali.

    Pan-Tompkins mudah tertipu dengung 50 Hz: energinya bocor lewat tahap
    kuadrat + integrasi dan terhitung sebagai QRS. Autokorelasi energi pita
    QRS (5-15 Hz) menanyakan hal yang berbeda dan jauh lebih tahan derau:
    'apakah pola ini berulang dengan periode 0,4-1,5 detik?'

    Returns: (kekuatan 0-1, bpm)
    """
    q = sosfilt(butter(2, [5, 15], btype="bandpass", fs=fs, output="sos"), x - x.mean())
    e = q ** 2
    e = e - e.mean()
    ac = np.correlate(e, e, mode="full")[len(e) - 1:]
    ac /= ac[0]
    lo, hi = int(0.4 * fs), int(1.5 * fs)
    lag = lo + int(np.argmax(ac[lo:hi]))

    # Penjaga anti-positif-palsu: denyut memberi SATU puncak dominan; gangguan
    # periodik (dengung 50 Hz & harmoniknya) memberi DERETAN puncak setara
    # berjarak seragam. Hitung puncak lain yang tingginya >= 80% puncak utama.
    puncak = [ac[i] for i in range(lo + 1, hi - 1)
              if ac[i] > ac[i - 1] and ac[i] >= ac[i + 1]]
    saingan = sum(1 for v in puncak if v >= 0.8 * ac[lag])
    return float(ac[lag]), 60.0 * fs / lag, saingan


def muat(path: str):
    fs, lewat = FS, None
    nilai = []
    for baris in open(path):
        baris = baris.strip()
        if not baris:
            continue
        if baris.startswith("#"):
            for bagian in baris.lstrip("# ").split():
                k, _, v = bagian.partition("=")
                if k == "fs":
                    fs = int(v)
                elif k == "lewat":
                    lewat = int(v)
            continue
        nilai.append(int(baris))
    return np.asarray(nilai, dtype=np.float32), fs, lewat


def pita_energi(x, fs, a, b):
    sp = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    fr = np.fft.rfftfreq(len(x), 1 / fs)
    return float(sp[(fr >= a) & (fr < b)].sum())


def main() -> None:
    path = sys.argv[1]
    nama = sys.argv[2] if len(sys.argv) > 2 else "device"
    mentah, fs, lewat = muat(path)
    n = len(mentah)

    clip = int((mentah >= 4095).sum() + (mentah <= 0).sum())
    x = (mentah - mentah.mean()) / 1000.0
    filtered = apply_bandpass(x, design_bandpass_sos())

    ekg = pita_energi(x, fs, 0.5, 40)
    hum = pita_energi(x, fs, 49, 51)
    hf = pita_energi(x, fs, 60, fs / 2)
    drift = pita_energi(x, fs, 0.01, 0.5)

    kuat, bpm_ac, saingan = denyut_autokorelasi(x, fs)
    r = pan_tompkins_detect(filtered, fs)
    rr = np.diff(r) / fs if len(r) > 2 else np.array([])
    bpm = 60 / rr if len(rr) else np.array([])
    # Detak fisiologis 30-200 bpm; di luar itu hampir pasti deteksi palsu.
    masuk_akal = float(((bpm >= 30) & (bpm <= 200)).mean()) if len(bpm) else 0.0

    print(f"{nama}: {n} sampel = {n / fs:.1f} detik @ {fs} Hz"
          + (f", {lewat} sampel terlewat" if lewat is not None else ""))
    print(f"  ADC          {int(mentah.min())}..{int(mentah.max())}   "
          f"clipping {clip} sampel {'← RUSAK' if clip else 'OK'}")
    print(f"  dengung 50Hz {100 * hum / ekg:6.1f}% dari pita EKG   "
          f"{'OK' if hum / ekg < 0.15 else 'TERLALU BESAR'}")
    print(f"  derau >60Hz  {100 * hf / ekg:6.1f}% dari pita EKG   "
          f"{'OK' if hf / ekg < 0.5 else 'TERLALU BESAR'}")
    print(f"  drift <0.5Hz {100 * drift / ekg:6.1f}% dari pita EKG")
    if kuat <= 0.25:
        vonis = "TIDAK ADA denyut jelas"
    elif saingan > 2:
        vonis = f"PALSU — {saingan} puncak setara (gangguan periodik, bukan denyut)"
    else:
        vonis = "ADA denyut"
    print(f"  denyut       autokorelasi {kuat:.2f} @ {bpm_ac:.0f} bpm   {vonis}")
    print(f"  R-peak       {len(r)} dalam {n / fs:.1f} detik")
    if len(bpm):
        print(f"  BPM          mean {bpm.mean():.0f}  min {bpm.min():.0f}  max {bpm.max():.0f}"
              f"   masuk akal {100 * masuk_akal:.0f}%"
              f"   {'OK' if masuk_akal > 0.9 else 'TIDAK KONSISTEN'}")

    akuisisi_dir = os.path.join(METRICS_DIR, "akuisisi")
    os.makedirs(akuisisi_dir, exist_ok=True)
    out = os.path.join(akuisisi_dir, f"akuisisi_{nama}.png")
    t = np.arange(n) / fs
    tampil = slice(0, min(n, int(6 * fs)))
    fig, ax = plt.subplots(3, 1, figsize=(13, 8))
    ax[0].plot(t[tampil], mentah[tampil], lw=0.7)
    ax[0].set_title(f"{nama} — ADC mentah (6 detik pertama)")
    ax[0].set_ylabel("counts")
    ax[1].plot(t[tampil], filtered[tampil], lw=0.7, color="tab:green")
    for pos in r[r < tampil.stop]:
        ax[1].axvline(pos / fs, color="red", alpha=0.4, lw=0.8)
    ax[1].set_title("setelah bandpass 0,5-40 Hz kausal + R-peak Pan-Tompkins")
    sp = np.abs(np.fft.rfft(x * np.hanning(n)))
    fr = np.fft.rfftfreq(n, 1 / fs)
    ax[2].semilogy(fr, sp + 1e-9, lw=0.7)
    ax[2].axvspan(49, 51, color="red", alpha=0.2, label="50 Hz (PLN)")
    ax[2].axvspan(0.5, 40, color="green", alpha=0.1, label="pita EKG")
    ax[2].set_xlim(0, fs / 2)
    ax[2].set_title("spektrum sinyal mentah")
    ax[2].set_xlabel("Hz")
    ax[2].legend()
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f"\n{out}")


if __name__ == "__main__":
    main()
