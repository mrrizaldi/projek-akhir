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


def autocorrelation_pulse(x, fs):
    q = sosfilt(butter(2, [5, 15], btype="bandpass", fs=fs, output="sos"), x - x.mean())
    e = q ** 2
    e = e - e.mean()
    ac = np.correlate(e, e, mode="full")[len(e) - 1:]
    ac /= ac[0]
    lo, hi = int(0.4 * fs), int(1.5 * fs)
    lag = lo + int(np.argmax(ac[lo:hi]))

    puncak = [ac[i] for i in range(lo + 1, hi - 1)
              if ac[i] > ac[i - 1] and ac[i] >= ac[i + 1]]
    rival_peaks = sum(1 for v in puncak if v >= 0.8 * ac[lag])
    return float(ac[lag]), 60.0 * fs / lag, rival_peaks


AUTOCORRELATION_WINDOW_S = 30
ADC_UPPER, ADC_LOWER = 4090, 5
CLIPPING_PERCENT_THRESHOLD = 0.1


def compute_clipping(mentah):
    n_clip = int((mentah >= ADC_UPPER).sum() + (mentah <= ADC_LOWER).sum())
    persen = 100.0 * n_clip / len(mentah)
    return n_clip, persen, persen <= CLIPPING_PERCENT_THRESHOLD


def pulse_per_window(x, fs):
    n = int(AUTOCORRELATION_WINDOW_S * fs)
    if len(x) < 2 * n:
        return autocorrelation_pulse(x, fs)
    strength, bpm, rival_peaks = zip(*(autocorrelation_pulse(x[i:i + n], fs)
                               for i in range(0, len(x) - n + 1, n)))
    return float(np.median(strength)), float(np.median(bpm)), int(round(np.median(rival_peaks)))


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
            for token in kata:
                k, _, v = token.partition("=")
                if k == "fs":
                    fs = int(v)
                elif k == "lewat":
                    lewat = int(v)
            continue
        segmen[-1].append(int(baris))
    return [np.asarray(v, dtype=np.float32) for v in segmen if v], fs, lewat


def band_energy(x, fs, a, b):
    sp = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    fr = np.fft.rfftfreq(len(x), 1 / fs)
    return float(sp[(fr >= a) & (fr < b)].sum())


def analyze_segment(mentah, fs):
    x = (mentah - mentah.mean()) / 1000.0
    filtered = apply_bandpass(x, design_bandpass_sos())
    r = pan_tompkins_detect(filtered, fs)
    return {
        "n": len(mentah), "x": x, "filtered": filtered, "r": r,
        "rr": np.diff(r) / fs if len(r) > 2 else np.array([]),
        "pita": [band_energy(x, fs, a, b) for a, b in
                 ((0.5, 40), (49, 51), (60, fs / 2), (0.01, 0.5))],
        "ac": pulse_per_window(x, fs) if len(x) > int(1.5 * fs) + 1 else None,
    }


def combine(analyses, fs):
    awal = np.cumsum([0] + [h["n"] for h in analyses])
    r = np.concatenate([h["r"] + a for h, a in zip(analyses, awal)]).astype(int)
    rr = np.concatenate([h["rr"] for h in analyses])
    ecg_band, hum, hf, drift = np.sum([h["pita"] for h in analyses], axis=0)
    ac = [(h["n"], h["ac"]) for h in analyses if h["ac"] is not None]
    if len(ac) == 1:
        strength, bpm_ac, rival_peaks = ac[0][1]
    elif ac:
        class_weights = np.array([n for n, _ in ac], dtype=float)
        strength, bpm_ac, rival_peaks = (np.average([a[i] for _, a in ac], weights=class_weights)
                                 for i in range(3))
        rival_peaks = int(round(rival_peaks))
    else:
        strength, bpm_ac, rival_peaks = 0.0, 0.0, 0
    return r, rr, (ecg_band, hum, hf, drift), (float(strength), float(bpm_ac), rival_peaks), awal


def main() -> None:
    path = sys.argv[1]
    nama = sys.argv[2] if len(sys.argv) > 2 else "device"
    judul = sys.argv[3] if len(sys.argv) > 3 else nama
    segmen, fs, lewat = muat(path)
    mentah = np.concatenate(segmen)
    n = len(mentah)

    clip, percent_clip, clip_ok = compute_clipping(mentah)
    analyses = [analyze_segment(m, fs) for m in segmen]
    x = np.concatenate([h["x"] for h in analyses])
    filtered = np.concatenate([h["filtered"] for h in analyses])
    r, rr, (ecg_band, hum, hf, drift), (strength, bpm_ac, rival_peaks), awal = combine(analyses, fs)
    bpm = 60 / rr if len(rr) else np.array([])
    plausible_fraction = float(((bpm >= 30) & (bpm <= 200)).mean()) if len(bpm) else 0.0

    print(f"{nama}: {n} samples = {n / fs:.1f} seconds @ {fs} Hz"
          + (f", {lewat} samples missed" if lewat is not None else "")
          + (f", {len(segmen)} segments (split by pauses)" if len(segmen) > 1 else ""))
    if len(segmen) > 1:
        for i, h in enumerate(analyses, 1):
            ac = ((f"autocorrelation {h['ac'][0]:.2f} @ {h['ac'][1]:.0f} bpm"
                   f", {h['ac'][2]} equal peaks")
                  if h["ac"] else "autocorrelation - (segment < 1.5 seconds)")
            print(f"  segment {i:<3} {h['n'] / fs:6.1f} seconds  R-peak {len(h['r']):4d}"
                  f"   RR {len(h['rr']):4d}   {ac}")
    print(f"  ADC          {int(mentah.min())}..{int(mentah.max())}   "
          f"clipping {clip} samples ({percent_clip:.3f}%, threshold {CLIPPING_PERCENT_THRESHOLD}%) "
          f"{'OK' if clip_ok else '← BROKEN'}")
    print(f"  50Hz hum     {100 * hum / ecg_band:6.1f}% of ECG band   "
          f"{'OK' if hum / ecg_band < 0.15 else 'TOO LARGE'}")
    print(f"  noise >60Hz  {100 * hf / ecg_band:6.1f}% of ECG band   "
          f"{'OK' if hf / ecg_band < 0.5 else 'TOO LARGE'}")
    print(f"  drift <0.5Hz {100 * drift / ecg_band:6.1f}% of ECG band")
    if strength <= 0.25:
        vonis = "NO clear pulse"
    elif rival_peaks > 2:
        vonis = f"FALSE: {rival_peaks} equal peaks (periodic interference, not a pulse)"
    else:
        vonis = "pulse PRESENT"
    windowed = any(h["n"] >= 2 * AUTOCORRELATION_WINDOW_S * fs for h in analyses)
    method_note = f" (median per {AUTOCORRELATION_WINDOW_S} s)" if windowed else ""
    print(f"  pulse        autocorrelation {strength:.2f} @ {bpm_ac:.0f} bpm{method_note}   {vonis}")
    print(f"  R-peak       {len(r)} in {n / fs:.1f} seconds")
    if len(bpm):
        print(f"  BPM          mean {bpm.mean():.0f}  min {bpm.min():.0f}  max {bpm.max():.0f}"
              f"   plausible {100 * plausible_fraction:.0f}%"
              f"   {'OK' if plausible_fraction > 0.9 else 'INCONSISTENT'}")

    acquisition_dir = os.path.join(METRICS_DIR, "akuisisi")
    os.makedirs(acquisition_dir, exist_ok=True)
    out = os.path.join(acquisition_dir, f"akuisisi_{nama}.png")
    t = np.arange(n) / fs
    shown = slice(0, min(n, int(6 * fs)))
    boundaries = awal[1:-1] / fs
    fig, ax = plt.subplots(3 + (len(segmen) > 1), 1,
                           figsize=(13, 8 + 2.7 * (len(segmen) > 1)))
    ax[0].plot(t[shown], mentah[shown], lw=0.7)
    ax[0].set_title(f"{judul} — ADC mentah (6 detik pertama)")
    ax[0].set_ylabel("counts")
    ax[1].plot(t[shown], filtered[shown], lw=0.7, color="tab:green")
    for pos in r[r < shown.stop]:
        ax[1].axvline(pos / fs, color="red", alpha=0.4, lw=0.8)
    ax[1].set_title("setelah bandpass 0,5-40 Hz kausal + R-peak Pan-Tompkins")
    for b in boundaries[boundaries < shown.stop / fs]:
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
        for b in boundaries:
            ax[3].axvline(b, color="black", ls="--", lw=1)
        ax[3].set_title(f"seluruh rekaman setelah bandpass, {len(segmen)} segmen "
                        "(garis putus-putus = jeda)")
        ax[3].set_xlabel("detik (waktu gabungan, jeda tidak dihitung)")
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f"\n{out}")


if __name__ == "__main__":
    main()
