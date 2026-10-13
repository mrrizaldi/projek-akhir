"""Analisis kualitas rekaman EKG dari device.

    python scripts/analyze_recording.py <berkas>.csv [nama]

Masukan: keluaran `dump` firmware (baris '# fs=.. n=.. lewat=..' lalu satu
nilai ADC per baris). Baris '# jeda' memisahkan segmen rekaman yang dijeda.
Menilai dengan ANGKA, bukan dengan melihat grafik: dengung PLN, derau HF,
drift baseline, dan apakah Pan-Tompkins menemukan detak yang konsisten.

Semua hitungan berjalan PER SEGMEN lalu digabung: filter mulai dari nol di
awal tiap segmen (transiennya sama seperti awal rekaman) dan interval RR tidak
pernah melintasi jeda. Berkas tanpa '# jeda' = satu segmen.
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
    """Returns: (daftar segmen float32 tanpa segmen kosong, fs, lewat)."""
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
    """Satu segmen kontinu: filter, energi pita, autokorelasi, R-peak, RR."""
    x = (mentah - mentah.mean()) / 1000.0
    filtered = apply_bandpass(x, design_bandpass_sos())
    r = pan_tompkins_detect(filtered, fs)
    return {
        "n": len(mentah), "x": x, "filtered": filtered, "r": r,
        "rr": np.diff(r) / fs if len(r) > 2 else np.array([]),
        "pita": [pita_energi(x, fs, a, b) for a, b in
                 ((0.5, 40), (49, 51), (60, fs / 2), (0.01, 0.5))],
        # Lag autokorelasi butuh > 1,5 detik sinyal; segmen lebih pendek dilewati.
        "ac": denyut_autokorelasi(x, fs) if len(x) > int(1.5 * fs) + 1 else None,
    }


def gabung(hasil, fs):
    """Gabungkan hasil per segmen. R jadi indeks pada sumbu waktu gabungan;
    RR disambung per segmen sehingga tidak ada RR yang melintasi jeda."""
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
    segmen, fs, lewat = muat(path)
    mentah = np.concatenate(segmen)
    n = len(mentah)

    clip = int((mentah >= 4095).sum() + (mentah <= 0).sum())
    hasil = [analisis_segmen(m, fs) for m in segmen]
    x = np.concatenate([h["x"] for h in hasil])
    filtered = np.concatenate([h["filtered"] for h in hasil])
    r, rr, (ekg, hum, hf, drift), (kuat, bpm_ac, saingan), awal = gabung(hasil, fs)
    bpm = 60 / rr if len(rr) else np.array([])
    # Detak fisiologis 30-200 bpm; di luar itu hampir pasti deteksi palsu.
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
    batas = awal[1:-1] / fs  # awal segmen ke-2 dst. pada sumbu waktu gabungan
    fig, ax = plt.subplots(3 + (len(segmen) > 1), 1,
                           figsize=(13, 8 + 2.7 * (len(segmen) > 1)))
    ax[0].plot(t[tampil], mentah[tampil], lw=0.7)
    ax[0].set_title(f"{nama} — ADC mentah (6 detik pertama)")
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
