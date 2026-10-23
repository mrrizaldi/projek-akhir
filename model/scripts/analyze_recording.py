import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import FS, METRICS_DIR
from scipy.signal import butter, sosfilt

from src.preprocessing import (
    apply_bandpass, design_bandpass_sos, pan_tompkins_detect,
)


def denyut_autokorelasi(x, fs):
    q = sosfilt(butter(2, [5, 15], btype="bandpass", fs=fs, output="sos"), x - x.mean())
    e = q ** 2
    e = e - e.mean()
    ac = np.correlate(e, e, mode="full")[len(e) - 1:]
    ac /= ac[0]
    lo, hi = int(0.4 * fs), int(1.5 * fs)
    lag = lo + int(np.argmax(ac[lo:hi]))

    puncak = [ac[i] for i in range(lo + 1, hi - 1)
              if ac[i] > ac[i - 1] and ac[i] >= ac[i + 1]]
    saingan = sum(1 for v in puncak if v >= 0.8 * ac[lag])
    return float(ac[lag]), 60.0 * fs / lag, saingan


JENDELA_AUTOKORELASI_S = 30
ADC_ATAS, ADC_BAWAH = 4090, 5
AMBANG_CLIPPING_PERSEN = 0.1


def hitung_clipping(mentah):
    n_clip = int((mentah >= ADC_ATAS).sum() + (mentah <= ADC_BAWAH).sum())
    persen = 100.0 * n_clip / len(mentah)
    return n_clip, persen, persen <= AMBANG_CLIPPING_PERSEN


def denyut_per_jendela(x, fs):
    n = int(JENDELA_AUTOKORELASI_S * fs)
    if len(x) < 2 * n:
        return denyut_autokorelasi(x, fs)
    kuat, bpm, saingan = zip(*(denyut_autokorelasi(x[i:i + n], fs)
                               for i in range(0, len(x) - n + 1, n)))
    return float(np.median(kuat)), float(np.median(bpm)), int(round(np.median(saingan)))


def muat(path: str):
    fs, lewat = FS, None
    segmen = [[]]
    for baris in open(path):
        baris = baris.strip()
        if not baris:
            continue
        if baris.startswith("#"):
            kata = baris.lstrip("# ").split()
            if kata and kata[0] == "jeda":
                segmen.append([])
                continue
            for bagian in kata:
                k, _, v = bagian.partition("=")
                if k == "fs":
                    fs = int(v)
                elif k == "lewat":
                    lewat = int(v)
            continue
        segmen[-1].append(int(baris))
    return [np.asarray(v, dtype=np.float32) for v in segmen if v], fs, lewat


def pita_energi(x, fs, a, b):
    sp = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    fr = np.fft.rfftfreq(len(x), 1 / fs)
    return float(sp[(fr >= a) & (fr < b)].sum())


def analisis_segmen(mentah, fs):
    x = (mentah - mentah.mean()) / 1000.0
    filtered = apply_bandpass(x, design_bandpass_sos())
    r = pan_tompkins_detect(filtered, fs)
    return {
        "n": len(mentah), "x": x, "filtered": filtered, "r": r,
        "rr": np.diff(r) / fs if len(r) > 2 else np.array([]),
        "pita": [pita_energi(x, fs, a, b) for a, b in
                 ((0.5, 40), (49, 51), (60, fs / 2), (0.01, 0.5))],
        "ac": denyut_per_jendela(x, fs) if len(x) > int(1.5 * fs) + 1 else None,
    }


def gabung(hasil, fs):
    awal = np.cumsum([0] + [h["n"] for h in hasil])
    r = np.concatenate([h["r"] + a for h, a in zip(hasil, awal)]).astype(int)
    rr = np.concatenate([h["rr"] for h in hasil])
    ekg, hum, hf, drift = np.sum([h["pita"] for h in hasil], axis=0)
    ac = [(h["n"], h["ac"]) for h in hasil if h["ac"] is not None]
    if len(ac) == 1:
        kuat, bpm_ac, saingan = ac[0][1]
    elif ac:
        bobot = np.array([n for n, _ in ac], dtype=float)
        kuat, bpm_ac, saingan = (np.average([a[i] for _, a in ac], weights=bobot)
                                 for i in range(3))
        saingan = int(round(saingan))
    else:
        kuat, bpm_ac, saingan = 0.0, 0.0, 0
    return r, rr, (ekg, hum, hf, drift), (float(kuat), float(bpm_ac), saingan), awal


def main() -> None:
    path = sys.argv[1]
    nama = sys.argv[2] if len(sys.argv) > 2 else "device"
    judul = sys.argv[3] if len(sys.argv) > 3 else nama
    segmen, fs, lewat = muat(path)
    mentah = np.concatenate(segmen)
    n = len(mentah)

    clip, persen_clip, clip_ok = hitung_clipping(mentah)
    hasil = [analisis_segmen(m, fs) for m in segmen]
    x = np.concatenate([h["x"] for h in hasil])
    filtered = np.concatenate([h["filtered"] for h in hasil])
    r, rr, (ekg, hum, hf, drift), (kuat, bpm_ac, saingan), awal = gabung(hasil, fs)
    bpm = 60 / rr if len(rr) else np.array([])
    masuk_akal = float(((bpm >= 30) & (bpm <= 200)).mean()) if len(bpm) else 0.0

    print(f"{nama}: {n} sampel = {n / fs:.1f} detik @ {fs} Hz"
          + (f", {lewat} sampel terlewat" if lewat is not None else "")
          + (f", {len(segmen)} segmen (dipisah jeda)" if len(segmen) > 1 else ""))
    if len(segmen) > 1:
        for i, h in enumerate(hasil, 1):
            ac = ((f"autokorelasi {h['ac'][0]:.2f} @ {h['ac'][1]:.0f} bpm"
                   f", {h['ac'][2]} puncak setara")
                  if h["ac"] else "autokorelasi - (segmen < 1,5 detik)")
            print(f"  segmen {i:<3}  {h['n'] / fs:6.1f} detik   R-peak {len(h['r']):4d}"
                  f"   RR {len(h['rr']):4d}   {ac}")
    print(f"  ADC          {int(mentah.min())}..{int(mentah.max())}   "
          f"clipping {clip} sampel ({persen_clip:.3f}%, ambang {AMBANG_CLIPPING_PERSEN}%) "
          f"{'OK' if clip_ok else '← RUSAK'}")
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
    berjendela = any(h["n"] >= 2 * JENDELA_AUTOKORELASI_S * fs for h in hasil)
    cara = f" (median per {JENDELA_AUTOKORELASI_S} s)" if berjendela else ""
    print(f"  denyut       autokorelasi {kuat:.2f} @ {bpm_ac:.0f} bpm{cara}   {vonis}")
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
    batas = awal[1:-1] / fs
    fig, ax = plt.subplots(3 + (len(segmen) > 1), 1,
                           figsize=(13, 8 + 2.7 * (len(segmen) > 1)))
    ax[0].plot(t[tampil], mentah[tampil], lw=0.7)
    ax[0].set_title(f"{judul} — ADC mentah (6 detik pertama)")
    ax[0].set_ylabel("counts")
    ax[1].plot(t[tampil], filtered[tampil], lw=0.7, color="tab:green")
    for pos in r[r < tampil.stop]:
        ax[1].axvline(pos / fs, color="red", alpha=0.4, lw=0.8)
    ax[1].set_title("setelah bandpass 0,5-40 Hz kausal + R-peak Pan-Tompkins")
    for b in batas[batas < tampil.stop / fs]:
        for a in ax[:2]:
            a.axvline(b, color="black", ls="--", lw=1)
    sp = np.abs(np.fft.rfft(x * np.hanning(n)))
    fr = np.fft.rfftfreq(n, 1 / fs)
    ax[2].semilogy(fr, sp + 1e-9, lw=0.7)
    ax[2].axvspan(49, 51, color="red", alpha=0.2, label="50 Hz (PLN)")
    ax[2].axvspan(0.5, 40, color="green", alpha=0.1, label="pita EKG")
    ax[2].set_xlim(0, fs / 2)
    ax[2].set_title("spektrum sinyal mentah")
    ax[2].set_xlabel("Hz")
    ax[2].legend()
    if len(segmen) > 1:
        ax[3].plot(t, filtered, lw=0.4, color="tab:green")
        for b in batas:
            ax[3].axvline(b, color="black", ls="--", lw=1)
        ax[3].set_title(f"seluruh rekaman setelah bandpass, {len(segmen)} segmen "
                        "(garis putus-putus = jeda)")
        ax[3].set_xlabel("detik (waktu gabungan, jeda tidak dihitung)")
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f"\n{out}")


if __name__ == "__main__":
    main()
