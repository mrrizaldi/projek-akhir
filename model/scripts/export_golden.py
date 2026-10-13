import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf

from config import (
    ALIGN_WIN, N_RR_BASE, R_IN_WINDOW, USE_QRSW, USE_RR_RATIO,
)
from config import (
    ARTIFACT_DIR, FS, BANDPASS_LOW, BANDPASS_HIGH, BANDPASS_ORDER,
    GROUP_DELAY_SAMPLES, N_RR_FEATURES, PT_BAND_HIGH, PT_BAND_LOW, PT_BAND_ORDER,
    PT_DETECTOR_OFFSET, PT_MWI_WINDOW_MS, PT_REFINE_WIN, PT_REFRACTORY_MS,
    RR_LOCAL_WINDOW_BEATS, THRESHOLD, WIN_LEN, WIN_POST, WIN_PRE,
)
from src.io_mitdb import load_record
from scipy.signal import butter

from src.preprocessing import (
    apply_bandpass, design_bandpass_sos, pan_tompkins_detect, segment_beats,
    zscore_per_window,
)
from src.features_rr import (
    rakit_fitur_ritme, to_aami_class, to_binary_label,
)
from src.quantize import predict_tflite
from scripts.prep_beats import valid_beat_indices

RECORD = "208"
N_SAMPLES = 2400
RR_FIRST = 2
RR_LAST = 1 if USE_RR_RATIO else 0
QRSW_CARI = 4
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H_PREPROC = os.path.join(ROOT, "firmware", "include", "ecg_preproc.h")
H_GOLDEN = os.path.join(ROOT, "firmware", "test", "golden_ref.h")


def _larik(nama: str, data, per_baris: int = 6, fmt: str = "%.8ef") -> str:
    isi = [fmt % v for v in np.asarray(data).ravel()]
    baris = [", ".join(isi[i:i + per_baris]) for i in range(0, len(isi), per_baris)]
    return f"const float {nama}[{len(isi)}] = {{\n  " + ",\n  ".join(baris) + "\n};\n"


def main() -> None:
    sig, r, sym, fs = load_record(RECORD)
    sos = design_bandpass_sos()

    potongan = sig[:N_SAMPLES]
    filtered_penuh = apply_bandpass(sig, sos)
    filtered = apply_bandpass(potongan, sos)
    assert np.allclose(filtered, filtered_penuh[:N_SAMPLES], atol=1e-6), \
        "filter tidak kausal — vektor uji tidak bisa berdiri sendiri"

    idx = valid_beat_indices(len(sig), r)
    dipakai = [i for i in idx if r[i] - WIN_PRE >= 0 and r[i] + WIN_POST <= N_SAMPLES]
    if not dipakai:
        raise ValueError("tidak ada beat yang muat di potongan")

    windows = zscore_per_window(segment_beats(filtered, r[dipakai]))
    label = [to_binary_label(to_aami_class(sym[i])) for i in dipakai]

    r_potong = np.asarray(r)[dipakai]
    rr = rakit_fitur_ritme(r_potong, windows, np.arange(len(dipakai)))
    rr_bersih = np.nan_to_num(rr, nan=0.0)

    keras = tf.keras.models.load_model(os.path.join(ARTIFACT_DIR, "model_fp32.keras"))
    p_fp32 = keras.predict([windows.reshape(-1, WIN_LEN, 1), rr_bersih], verbose=0).ravel()
    p_int8 = predict_tflite(os.path.join(ARTIFACT_DIR, "model_int8.tflite"),
                            windows.reshape(-1, WIN_LEN, 1), rr_bersih)
    p_fp32[:RR_FIRST] = 0.0
    p_int8[:RR_FIRST] = 0.0
    if RR_LAST:
        p_fp32[-RR_LAST:] = 0.0
        p_int8[-RR_LAST:] = 0.0

    sos_pt = butter(PT_BAND_ORDER, [PT_BAND_LOW, PT_BAND_HIGH],
                    btype="bandpass", fs=FS, output="sos")
    mwi_len = max(1, round(PT_MWI_WINDOW_MS / 1000 * FS))
    refraktori = max(1, round(PT_REFRACTORY_MS / 1000 * FS))
    n_sos_pt = len(sos_pt)
    larik_sos_pt = _larik("ecg_pt_sos", sos_pt, 6)
    r_deteksi = pan_tompkins_detect(filtered, FS)

    os.makedirs(os.path.dirname(H_PREPROC), exist_ok=True)
    os.makedirs(os.path.dirname(H_GOLDEN), exist_ok=True)

    with open(H_PREPROC, "w") as f:
        f.write(f"""#ifndef ECG_PREPROC_H
#define ECG_PREPROC_H

#define ECG_FS {FS}
#define ECG_WIN_PRE {WIN_PRE}
#define ECG_WIN_POST {WIN_POST}
#define ECG_WIN_LEN_ {WIN_LEN}
#define ECG_ZSCORE_EPS 1e-8f
#ifndef ECG_N_RR
#define ECG_N_RR {N_RR_FEATURES}
#endif
#define ECG_RR_LOCAL_WINDOW {RR_LOCAL_WINDOW_BEATS}
#define ECG_N_RR_DASAR {N_RR_BASE}
#define ECG_RR_RATIO {int(USE_RR_RATIO)}
#define ECG_QRSW {int(USE_QRSW)}
#define ECG_R_IN_WINDOW {R_IN_WINDOW}
#define ECG_QRSW_CARI {QRSW_CARI}

#define ECG_PT_MWI_LEN {mwi_len}
#define ECG_PT_REFRACTORY {refraktori}
#define ECG_PT_N_SOS {n_sos_pt}
{larik_sos_pt}
#define ECG_PT_OFFSET {PT_DETECTOR_OFFSET}
#define ECG_PT_REFINE {PT_REFINE_WIN}
#define ECG_GROUP_DELAY {GROUP_DELAY_SAMPLES}

#define ECG_N_SOS {len(sos)}
{_larik("ecg_sos", sos, 6)}
#endif
""")

    n_deteksi = len(r_deteksi)
    isi_deteksi = ", ".join(str(int(v)) for v in r_deteksi)

    with open(H_GOLDEN, "w") as f:
        f.write(f"""#ifndef GOLDEN_REF_H
#define GOLDEN_REF_H

#define GOLDEN_N {N_SAMPLES}
#define GOLDEN_N_BEAT {len(dipakai)}
#define GOLDEN_WIN_LEN {WIN_LEN}
#define GOLDEN_N_RR {N_RR_FEATURES}
#define GOLDEN_THRESHOLD {THRESHOLD}f
#define GOLDEN_RR_FIRST {RR_FIRST}
#define GOLDEN_RR_LAST {RR_LAST}

#define GOLDEN_TOL_FILTER 1e-3f
#define GOLDEN_TOL_ZSCORE 1e-3f
#define GOLDEN_TOL_PROB   2e-2f

{_larik("golden_raw", potongan)}
{_larik("golden_filtered", filtered)}
const int golden_r[GOLDEN_N_BEAT] = {{{", ".join(str(int(r[i])) for i in dipakai)}}};
const char *golden_sym[GOLDEN_N_BEAT] = {{{", ".join(f'"{sym[i]}"' for i in dipakai)}}};
const int golden_label[GOLDEN_N_BEAT] = {{{", ".join(str(v) for v in label)}}};

{_larik("golden_window", windows)}
{_larik("golden_rr", rr_bersih, 3)}
#define GOLDEN_N_DETEKSI {n_deteksi}
const int golden_r_deteksi[GOLDEN_N_DETEKSI] = {{{isi_deteksi}}};

{_larik("golden_prob_fp32", p_fp32, 4)}
{_larik("golden_prob_int8", p_int8, 4)}
#endif
""")

    print(f"Pan-Tompkins atas potongan: {len(r_deteksi)} R-peak -> {list(map(int, r_deteksi))}")
    print(f"record {RECORD}, {N_SAMPLES} sampel, {len(dipakai)} beat: "
          f"{', '.join(sym[i] for i in dipakai)}")
    for n, (i, pf, pi) in enumerate(zip(dipakai, p_fp32, p_int8)):
        print(f"  beat {n}  r={int(r[i]):>5}  {sym[i]}  label={label[n]}  "
              f"fp32 {pf:.4f}  int8 {pi:.4f}")
    for path in (H_PREPROC, H_GOLDEN):
        print(f"{path}  {os.path.getsize(path) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
