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
    GROUP_DELAY_SAMPLES, N_RR_FEATURES, PT_BAND_HIGH, PT_BAND_LOW, PT_BAND_ORDER,
    PT_DETECTOR_OFFSET, PT_MWI_WINDOW_MS, PT_REFINE_WIN, PT_REFRACTORY_MS,
    RR_LOCAL_WINDOW_BEATS, THRESHOLD, WIN_LEN, WIN_POST, WIN_PRE,
)
from src.io_mitdb import load_record  # noqa: E402
from scipy.signal import butter  # noqa: E402

from src.preprocessing import (  # noqa: E402
    apply_bandpass, design_bandpass_sos, pan_tompkins_detect, segment_beats,
    zscore_per_window,
)
from src.features_rr import compute_rr_features, to_aami_class, to_binary_label  # noqa: E402
from src.quantize import predict_tflite  # noqa: E402
from scripts.prep_beats import valid_beat_indices  # noqa: E402

RECORD = "208"
N_SAMPLES = 2400                      # 6,7 detik @360 Hz
RR_FIRST = 2                          # beat 0-1 tak punya RR_prev/dRR
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

    # RR dihitung dari daftar R-peak POTONGAN ini saja, bukan record utuh — C
    # cuma punya beat yang ada di sini. Input sama → keluaran harus sama.
    # Konsekuensinya beat 0 & 1 tidak punya RR (NaN); diisi 0 dan tidak diuji.
    rr = compute_rr_features(np.asarray(r)[dipakai])
    rr_bersih = np.nan_to_num(rr, nan=0.0)

    keras = tf.keras.models.load_model(os.path.join(ARTIFACT_DIR, "model_fp32.keras"))
    p_fp32 = keras.predict([windows.reshape(-1, WIN_LEN, 1), rr_bersih], verbose=0).ravel()
    p_int8 = predict_tflite(os.path.join(ARTIFACT_DIR, "model_int8.tflite"),
                            windows.reshape(-1, WIN_LEN, 1), rr_bersih)
    p_fp32[:RR_FIRST] = 0.0
    p_int8[:RR_FIRST] = 0.0

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
// Juga didefinisikan di model_int8.h — dijaga supaya tidak bentrok.
#ifndef ECG_N_RR
#define ECG_N_RR {N_RR_FEATURES}
#endif
#define ECG_RR_LOCAL_WINDOW {RR_LOCAL_WINDOW_BEATS}

// Pan-Tompkins (deteksi R-peak on-device).
#define ECG_PT_MWI_LEN {mwi_len}
#define ECG_PT_REFRACTORY {refraktori}
#define ECG_PT_N_SOS {n_sos_pt}
{larik_sos_pt}
// Penyelarasan R-peak. Urutan WAJIB, salah satu terlewat -> precision jatuh 4x:
//   r - ECG_PT_OFFSET  ->  puncak dlm +-ECG_PT_REFINE  ->  - ECG_GROUP_DELAY
#define ECG_PT_OFFSET {PT_DETECTOR_OFFSET}
#define ECG_PT_REFINE {PT_REFINE_WIN}
#define ECG_GROUP_DELAY {GROUP_DELAY_SAMPLES}

// Butterworth bandpass {BANDPASS_LOW}-{BANDPASS_HIGH} Hz orde {BANDPASS_ORDER},
// {len(sos)} second-order section: {{b0, b1, b2, a0, a1, a2}} per baris.
// KAUSAL — jalankan maju saja, jangan pernah maju-mundur (filtfilt).
// Group delay menggeser R-peak +4 sampel; BIARKAN, model dilatih dengan geseran itu.
#define ECG_N_SOS {len(sos)}
{_larik("ecg_sos", sos, 6)}
#endif  // ECG_PREPROC_H
""")

    n_deteksi = len(r_deteksi)
    isi_deteksi = ", ".join(str(int(v)) for v in r_deteksi)

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
// Beat 0 & 1 tak punya RR_prev/dRR — baris rr & prob-nya 0, jangan diuji.
#define GOLDEN_RR_FIRST {RR_FIRST}

// Toleransi: golden ini float64 (scipy), device float32 (ESP32-S3 punya FPU
// single-precision; double di-emulasi software = lambat). Di filter IIR yang
// rekursif, selisih presisi itu MENUMPUK — terukur ~2e-4 pada amplitudo ~0,4.
// Bukan bug: yang haram adalah beda SISTEMATIS (geseran indeks, koefisien
// tertukar, a0 ikut terbaca). test_pipeline_utuh membuktikan selisih ini tidak
// merambat ke window ter-z-score, yang justru yang dimakan model.
#define GOLDEN_TOL_FILTER 1e-3f
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
{_larik("golden_rr", rr_bersih, 3)}
// Tahap 3b — R-peak hasil Pan-Tompkins atas golden_filtered (indeks MENTAH,
// belum dikompensasi/diselaraskan). Kode C harus menghasilkan deret yang sama.
#define GOLDEN_N_DETEKSI {n_deteksi}
const int golden_r_deteksi[GOLDEN_N_DETEKSI] = {{{isi_deteksi}}};

// Tahap 4 — probabilitas keluaran model
{_larik("golden_prob_fp32", p_fp32, 4)}
{_larik("golden_prob_int8", p_int8, 4)}
#endif  // GOLDEN_REF_H
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
