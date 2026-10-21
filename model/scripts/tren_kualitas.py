import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FS, METRICS_DIR
from src.preprocessing import apply_bandpass, design_bandpass_sos, pan_tompkins_detect

AMBANG_AYUN = 60
GAIN_50HZ = 0.342
FREK_JALA_HZ = 50.0
ADC_ATAS, ADC_BAWAH = 4090, 5
RR_MIN_S, RR_MAKS_S, DRR_MAKS_S = 0.300, 1.500, 0.200
RR_TENANG_S = 30
STABIL_S = 600
DETIK_PER_MENIT = 60
SKALA_DETEKTOR = 1000.0
PUNCAK_KE_PUNCAK = 2.0
PERSENTIL_BAWAH = 10
BEAT_PERTAMA_BER_RR = 1
FOLDER_KELUARAN = os.path.join(METRICS_DIR, "kualitas")


def baca_header(path):
    kunci = {}
    for baris in open(path):
        if not baris.startswith("#"):
            break
        if baris.strip() == "# jeda":
            sys.exit(f"{path}: berisi '# jeda', sesi berjeda tidak bisa dinilai per detik")
        for kata in baris.lstrip("# ").split():
            k, _, v = kata.partition("=")
            kunci[k] = v
    return kunci


def muat_sesi(paths):
    potongan = []
    for urutan, path in enumerate(paths):
        kunci = baca_header(path)
        if int(kunci.get("fs", FS)) != FS:
            sys.exit(f"{path}: fs={kunci['fs']}, bukan {FS}")
        if int(kunci.get("lewat", 0)):
            print(f"PERINGATAN {path}: lewat={kunci['lewat']}")
        if urutan and int(kunci.get("celah", -1)) != 0:
            print(f"PERINGATAN {path}: bukan lanjutan tanpa celah (celah={kunci.get('celah')})")
        potongan.append(np.loadtxt(path, comments="#", dtype=np.float64))
    return np.concatenate(potongan)


def nilai_per_detik(mentah):
    n_detik = len(mentah) // FS
    blok = mentah[: n_detik * FS].reshape(n_detik, FS)
    tersaring = apply_bandpass(mentah, design_bandpass_sos())[: n_detik * FS].reshape(n_detik, FS)
    ayun = tersaring.max(axis=1) - tersaring.min(axis=1)
    bin_jala = int(np.argmin(np.abs(np.fft.rfftfreq(FS, 1.0 / FS) - FREK_JALA_HZ)))
    amp50 = PUNCAK_KE_PUNCAK * np.abs(np.fft.rfft(blok, axis=1)[:, bin_jala]) / FS
    hum50 = PUNCAK_KE_PUNCAK * amp50
    ayun_bersih = np.maximum(ayun - GAIN_50HZ * hum50, 0.0)
    clipping = (blok.max(axis=1) >= ADC_ATAS) | (blok.min(axis=1) <= ADC_BAWAH)
    return ayun, hum50, ayun_bersih, clipping


def tenang_per_detik(mentah, n_detik):
    x = (mentah - mentah.mean()) / SKALA_DETEKTOR
    r = pan_tompkins_detect(apply_bandpass(x, design_bandpass_sos()), FS)
    rr = np.diff(r) / FS
    drr = np.abs(np.ediff1d(rr, to_begin=0.0))
    wajar = (rr >= RR_MIN_S) & (rr <= RR_MAKS_S) & (drr <= DRR_MAKS_S)
    detik_beat = r[BEAT_PERTAMA_BER_RR:] // FS
    langgar = np.zeros(n_detik, dtype=bool)
    langgar[detik_beat[~wajar & (detik_beat < n_detik)]] = True
    beat = np.bincount(detik_beat[detik_beat < n_detik], minlength=n_detik)
    tenang = np.zeros(n_detik)
    for t in range(1, n_detik):
        tenang[t] = 0.0 if langgar[t] else tenang[t - 1] + 1.0
    return beat, wajar, detik_beat, tenang


def lulus_pertama(syarat):
    indeks = np.flatnonzero(syarat)
    if not len(indeks):
        return "tidak pernah"
    pertama = indeks.min()
    return f"{pertama} s ({pertama / DETIK_PER_MENIT:.1f} menit)"


def main() -> None:
    paths = sys.argv[1:]
    if not paths:
        sys.exit("pakai: python scripts/tren_kualitas.py <berkas-sesi-1.csv> [<berkas-lanjutan.csv> ...]")
    mentah = muat_sesi(paths)
    ayun, hum50, ayun_bersih, clipping = nilai_per_detik(mentah)
    n_detik = len(ayun)
    beat, wajar, detik_beat, tenang = tenang_per_detik(mentah, n_detik)
    waktu = np.arange(n_detik)

    print(f"sesi {len(paths)} berkas, {n_detik} detik ({n_detik / DETIK_PER_MENIT:.1f} menit)\n")
    print("menit | ayun_bersih median p10 | dengung50 median | detik clipping | beat | RR wajar | tenang maks")
    for m in range(0, n_detik, DETIK_PER_MENIT):
        s = slice(m, m + DETIK_PER_MENIT)
        di_menit = (detik_beat >= m) & (detik_beat < m + DETIK_PER_MENIT)
        persen_wajar = 100.0 * wajar[di_menit].mean() if di_menit.any() else float("nan")
        print(f"{m // DETIK_PER_MENIT:5d} | {np.median(ayun_bersih[s]):11.0f} {np.percentile(ayun_bersih[s], PERSENTIL_BAWAH):4.0f}"
              f" | {np.median(hum50[s]):16.0f} | {clipping[s].sum():14d} | {beat[s].sum():4d}"
              f" | {persen_wajar:7.1f}% | {tenang[s].max():8.0f} s")

    ayun_ok = ayun_bersih >= AMBANG_AYUN
    rr_tenang = tenang >= RR_TENANG_S
    print(f"\nayun_bersih >= {AMBANG_AYUN} pertama        : {lulus_pertama(ayun_ok)}")
    print(f"RR tenang >= {RR_TENANG_S} s pertama          : {lulus_pertama(rr_tenang)}")
    print(f"gerbang tanpa syarat {STABIL_S} s lulus     : {lulus_pertama(ayun_ok & rr_tenang)}")
    print(f"gerbang firmware (dengan {STABIL_S} s) lulus: {lulus_pertama(ayun_ok & rr_tenang & (waktu >= STABIL_S))}")

    os.makedirs(FOLDER_KELUARAN, exist_ok=True)
    nama = os.path.splitext(os.path.basename(paths[0]))[0] + f"-sesi{len(paths)}"
    keluaran = os.path.join(FOLDER_KELUARAN, f"{nama}.csv")
    np.savetxt(keluaran, np.column_stack([waktu, ayun, hum50, ayun_bersih, clipping, beat, tenang]),
               fmt="%d", delimiter=",", header="detik,ayun,dengung50,ayun_bersih,clipping,beat,tenang_s",
               comments="")
    print(f"\n{keluaran}")


if __name__ == "__main__":
    main()
