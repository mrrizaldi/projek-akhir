import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import METRICS_DIR
from scripts.analyze_recording import analyze_segment, muat
from scripts.plot_recording import r_peaks

SQI_WINDOW_S = 10
HR_MIN_BPM, HR_MAX_BPM = 40, 180
RR_PAUSE_MAX_S = 3.0
RR_RATIO_MAX = 2.2
TEMPLATE_CORRELATION_THRESHOLD = 0.66
SECONDS_PER_MINUTE = 60
MIN_COMPLEXES = 2
OUTPUT_FOLDER = os.path.join(METRICS_DIR, "kualitas")


def template_correlation(sinyal, r, lebar):
    setengah = lebar // 2
    r = r[(r - setengah >= 0) & (r + setengah < len(sinyal))]
    if len(r) < MIN_COMPLEXES:
        return 0.0
    complexes = np.stack([sinyal[i - setengah:i + setengah] for i in r])
    template = complexes.mean(axis=0)
    return float(np.mean([np.corrcoef(k, template)[0, 1] for k in complexes]))


def window_scores(sinyal, r, fs):
    rr = np.diff(r) / fs
    if len(rr) == 0:
        return {"hr": 0.0, "jeda_maks": 0.0, "rasio": 0.0, "korelasi": 0.0,
                "lolos_aturan": False, "lolos": False}
    hr = SECONDS_PER_MINUTE / rr.mean()
    jeda_maks, rasio = float(rr.max()), float(rr.max() / rr.min())
    lolos_aturan = (HR_MIN_BPM <= hr <= HR_MAX_BPM and jeda_maks <= RR_PAUSE_MAX_S
                    and rasio < RR_RATIO_MAX)
    korelasi = template_correlation(sinyal, r, int(np.median(rr) * fs))
    return {"hr": float(hr), "jeda_maks": jeda_maks, "rasio": rasio, "korelasi": korelasi,
            "lolos_aturan": lolos_aturan,
            "lolos": lolos_aturan and korelasi >= TEMPLATE_CORRELATION_THRESHOLD}


def recording_windows(segmen, fs):
    n = SQI_WINDOW_S * fs
    hasil = []
    for mentah in segmen:
        h = analyze_segment(mentah, fs)
        r = r_peaks(h)
        for mulai in range(0, len(mentah) - n + 1, n):
            inside = r[(r >= mulai) & (r < mulai + n)] - mulai
            hasil.append(window_scores(h["filtered"][mulai:mulai + n], inside, fs))
    return hasil


def main() -> None:
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"{'recording':<28} {'windows':>7} {'rules':>8} {'all':>8} {'correlation med/min':>19}")
    for path in sys.argv[1:]:
        segmen, fs, _ = muat(path)
        hasil = recording_windows(segmen, fs)
        nama = os.path.splitext(os.path.basename(path))[0]
        korelasi = [j["korelasi"] for j in hasil]
        percent_rules = 100 * np.mean([j["lolos_aturan"] for j in hasil])
        percent_pass = 100 * np.mean([j["lolos"] for j in hasil])
        print(f"{nama:<28} {len(hasil):>7} {percent_rules:>7.1f}% {percent_pass:>7.1f}% "
              f"{np.median(korelasi):>8.3f} / {min(korelasi):.3f}")
        with open(os.path.join(OUTPUT_FOLDER, f"jendela10s_{nama}.csv"), "w") as f:
            f.write("jendela,hr_bpm,jeda_rr_maks_s,rasio_rr,korelasi,lolos_aturan,lolos\n")
            for i, j in enumerate(hasil):
                f.write(f"{i},{j['hr']:.1f},{j['jeda_maks']:.3f},{j['rasio']:.3f},"
                        f"{j['korelasi']:.4f},{int(j['lolos_aturan'])},{int(j['lolos'])}\n")


if __name__ == "__main__":
    main()
