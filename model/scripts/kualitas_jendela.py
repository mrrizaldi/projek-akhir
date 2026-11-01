import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import METRICS_DIR
from scripts.analyze_recording import analisis_segmen, muat
from scripts.plot_rekaman import puncak_r

JENDELA_SQI_S = 10
HR_MIN_BPM, HR_MAKS_BPM = 40, 180
JEDA_RR_MAKS_S = 3.0
RASIO_RR_MAKS = 2.2
AMBANG_KORELASI_TEMPLATE = 0.66
DETIK_PER_MENIT = 60
MIN_KOMPLEKS = 2
FOLDER_KELUARAN = os.path.join(METRICS_DIR, "kualitas")


def korelasi_template(sinyal, r, lebar):
    setengah = lebar // 2
    r = r[(r - setengah >= 0) & (r + setengah < len(sinyal))]
    if len(r) < MIN_KOMPLEKS:
        return 0.0
    kompleks = np.stack([sinyal[i - setengah:i + setengah] for i in r])
    template = kompleks.mean(axis=0)
    return float(np.mean([np.corrcoef(k, template)[0, 1] for k in kompleks]))


def nilai_jendela(sinyal, r, fs):
    rr = np.diff(r) / fs
    if len(rr) == 0:
        return {"hr": 0.0, "jeda_maks": 0.0, "rasio": 0.0, "korelasi": 0.0,
                "lolos_aturan": False, "lolos": False}
    hr = DETIK_PER_MENIT / rr.mean()
    jeda_maks, rasio = float(rr.max()), float(rr.max() / rr.min())
    lolos_aturan = (HR_MIN_BPM <= hr <= HR_MAKS_BPM and jeda_maks <= JEDA_RR_MAKS_S
                    and rasio < RASIO_RR_MAKS)
    korelasi = korelasi_template(sinyal, r, int(np.median(rr) * fs))
    return {"hr": float(hr), "jeda_maks": jeda_maks, "rasio": rasio, "korelasi": korelasi,
            "lolos_aturan": lolos_aturan,
            "lolos": lolos_aturan and korelasi >= AMBANG_KORELASI_TEMPLATE}


def jendela_rekaman(segmen, fs):
    n = JENDELA_SQI_S * fs
    hasil = []
    for mentah in segmen:
        h = analisis_segmen(mentah, fs)
        r = puncak_r(h)
        for mulai in range(0, len(mentah) - n + 1, n):
            di_dalam = r[(r >= mulai) & (r < mulai + n)] - mulai
            hasil.append(nilai_jendela(h["filtered"][mulai:mulai + n], di_dalam, fs))
    return hasil


def main() -> None:
    os.makedirs(FOLDER_KELUARAN, exist_ok=True)
    print(f"{'rekaman':<28} {'jendela':>7} {'aturan':>8} {'semua':>8} {'korelasi med/min':>17}")
    for path in sys.argv[1:]:
        segmen, fs, _ = muat(path)
        hasil = jendela_rekaman(segmen, fs)
        nama = os.path.splitext(os.path.basename(path))[0]
        korelasi = [j["korelasi"] for j in hasil]
        persen_aturan = 100 * np.mean([j["lolos_aturan"] for j in hasil])
        persen_lolos = 100 * np.mean([j["lolos"] for j in hasil])
        print(f"{nama:<28} {len(hasil):>7} {persen_aturan:>7.1f}% {persen_lolos:>7.1f}% "
              f"{np.median(korelasi):>8.3f} / {min(korelasi):.3f}")
        with open(os.path.join(FOLDER_KELUARAN, f"jendela10s_{nama}.csv"), "w") as f:
            f.write("jendela,hr_bpm,jeda_rr_maks_s,rasio_rr,korelasi,lolos_aturan,lolos\n")
            for i, j in enumerate(hasil):
                f.write(f"{i},{j['hr']:.1f},{j['jeda_maks']:.3f},{j['rasio']:.3f},"
                        f"{j['korelasi']:.4f},{int(j['lolos_aturan'])},{int(j['lolos'])}\n")


if __name__ == "__main__":
    main()
