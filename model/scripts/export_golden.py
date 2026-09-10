"""Fase hardware — vektor uji golden reference: Python → C.

    python scripts/export_golden.py

Menghasilkan DUA header:
    firmware/include/ecg_preproc.h   koefisien SOS + konstanta (produksi)
    firmware/test/golden_ref.h       sinyal mentah + hasil tiap tahap (uji)

Kode C wajib menghasilkan angka yang sama dari sinyal mentah yang sama.
Dibuat SEBELUM kode C ditulis — kalau dibuat sesudah, toleransinya cenderung
disesuaikan supaya lolos, dan itu bukan verifikasi.

Record 208 (DS1), 5 detik pertama: memuat beat N, F, dan V sekaligus.
Filter kausal → memfilter potongan 1800 sampel identik dengan memfilter sinyal
utuh lalu memotongnya (di-assert di sini), jadi vektor ini berdiri sendiri.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf  # noqa: E402

from config import (  # noqa: E402
    ARTIFACT_DIR, FS, BANDPASS_LOW, BANDPASS_HIGH, BANDPASS_ORDER,
    N_RR_FEATURES, THRESHOLD, WIN_LEN, WIN_POST, WIN_PRE,
)
from src.io_mitdb import load_record  # noqa: E402
from src.preprocessing import (  # noqa: E402
    apply_bandpass, design_bandpass_sos, segment_beats, zscore_per_window,
)
from src.features_rr import compute_rr_features, to_aami_class, to_binary_label  # noqa: E402
from src.quantize import predict_tflite  # noqa: E402
from scripts.prep_beats import valid_beat_indices  # noqa: E402

RECORD = "208"
N_SAMPLES = 1800                      # 5 detik @360 Hz
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
    rr = compute_rr_features(r)[dipakai]
    label = [to_binary_label(to_aami_class(sym[i])) for i in dipakai]

    keras = tf.keras.models.load_model(os.path.join(ARTIFACT_DIR, "model_fp32.keras"))
    p_fp32 = keras.predict([windows.reshape(-1, WIN_LEN, 1), rr], verbose=0).ravel()
    p_int8 = predict_tflite(os.path.join(ARTIFACT_DIR, "model_int8.tflite"),
                            windows.reshape(-1, WIN_LEN, 1), rr)

    os.makedirs(os.path.dirname(H_PREPROC), exist_ok=True)
    os.makedirs(os.path.dirname(H_GOLDEN), exist_ok=True)

    with open(H_PREPROC, "w") as f:
        f.write(f"""// GENERATED oleh model/scripts/export_golden.py — JANGAN EDIT TANGAN.
// Koefisien golden reference dari model/src/preprocessing.py.
// Regenerasi: cd model && python scripts/export_golden.py
#ifndef ECG_PREPROC_H
#define ECG_PREPROC_H

#define ECG_FS {FS}
#define ECG_WIN_PRE {WIN_PRE}
#define ECG_WIN_POST {WIN_POST}
#define ECG_WIN_LEN_ {WIN_LEN}
#define ECG_ZSCORE_EPS 1e-8f

// Butterworth bandpass {BANDPASS_LOW}-{BANDPASS_HIGH} Hz orde {BANDPASS_ORDER},
// {len(sos)} second-order section: {{b0, b1, b2, a0, a1, a2}} per baris.
// KAUSAL — jalankan maju saja, jangan pernah maju-mundur (filtfilt).
// Group delay menggeser R-peak +4 sampel; BIARKAN, model dilatih dengan geseran itu.
#define ECG_N_SOS {len(sos)}
{_larik("ecg_sos", sos, 6)}
#endif  // ECG_PREPROC_H
""")

    with open(H_GOLDEN, "w") as f:
        f.write(f"""// GENERATED oleh model/scripts/export_golden.py — JANGAN EDIT TANGAN.
// Golden reference: record {RECORD} (DS1), {N_SAMPLES} sampel pertama ({N_SAMPLES / FS:.0f} detik).
// Kode C harus menghasilkan angka ini dari GOLDEN_RAW, dalam toleransi.
#ifndef GOLDEN_REF_H
#define GOLDEN_REF_H

#define GOLDEN_N {N_SAMPLES}
#define GOLDEN_N_BEAT {len(dipakai)}
#define GOLDEN_WIN_LEN {WIN_LEN}
#define GOLDEN_N_RR {N_RR_FEATURES}
#define GOLDEN_THRESHOLD {THRESHOLD}f

// Toleransi: float32 di C dan di numpy beda urutan operasi, jadi jangan uji
// kesetaraan persis. Yang TIDAK boleh adalah beda sistematis (geseran indeks,
// std populasi vs sampel, koefisien tertukar).
#define GOLDEN_TOL_FILTER 1e-4f
#define GOLDEN_TOL_ZSCORE 1e-3f
#define GOLDEN_TOL_PROB   2e-2f

// Tahap 0 — sinyal mentah kanal MLII (mV), langsung dari .dat
{_larik("golden_raw", potongan)}
// Tahap 1 — setelah bandpass kausal (bandingkan dengan keluaran sosfilt-mu)
{_larik("golden_filtered", filtered)}
// Beat yang diuji: indeks R-peak, simbol asli, label
const int golden_r[GOLDEN_N_BEAT] = {{{", ".join(str(int(r[i])) for i in dipakai)}}};
const char *golden_sym[GOLDEN_N_BEAT] = {{{", ".join(f'"{sym[i]}"' for i in dipakai)}}};
const int golden_label[GOLDEN_N_BEAT] = {{{", ".join(str(v) for v in label)}}};

// Tahap 2 — window ter-z-score, {len(dipakai)} beat x {WIN_LEN} sampel (baris demi baris)
{_larik("golden_window", windows)}
// Tahap 3 — fitur RR per beat: RR_prev, RR_ratio, dRR
{_larik("golden_rr", rr, 3)}
// Tahap 4 — probabilitas keluaran model
{_larik("golden_prob_fp32", p_fp32, 4)}
{_larik("golden_prob_int8", p_int8, 4)}
#endif  // GOLDEN_REF_H
""")

    print(f"record {RECORD}, {N_SAMPLES} sampel, {len(dipakai)} beat: "
          f"{', '.join(sym[i] for i in dipakai)}")
    for n, (i, pf, pi) in enumerate(zip(dipakai, p_fp32, p_int8)):
        print(f"  beat {n}  r={int(r[i]):>5}  {sym[i]}  label={label[n]}  "
              f"fp32 {pf:.4f}  int8 {pi:.4f}")
    for path in (H_PREPROC, H_GOLDEN):
        print(f"{path}  {os.path.getsize(path) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
