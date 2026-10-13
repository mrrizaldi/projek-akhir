import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf

from config import ARTIFACT_DIR, N_RR_FEATURES, THRESHOLD, WIN_LEN

TFLITE = os.path.join(ARTIFACT_DIR, "model_int8.tflite")
HEADER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "firmware", "include", "model_int8.h")


def quant_params() -> dict:
    interp = tf.lite.Interpreter(model_path=TFLITE)
    interp.allocate_tensors()
    masuk = sorted(interp.get_input_details(), key=lambda d: len(d["shape"]))
    rr, morph = masuk[0], masuk[1]
    keluar = interp.get_output_details()[0]
    for nama, d in (("input", morph), ("rr", rr), ("output", keluar)):
        if d["dtype"].__name__ != "int8":
            raise ValueError(f"{nama} bukan int8 ({d['dtype'].__name__}) — cek INT8_IO")
    return {
        "morph": morph["quantization"], "rr": rr["quantization"],
        "out": keluar["quantization"],
    }


def main() -> None:
    if not os.path.exists(TFLITE):
        raise FileNotFoundError(f"{TFLITE} — jalankan `make quantize` dulu")
    blob = open(TFLITE, "rb").read()
    q = quant_params()
    os.makedirs(os.path.dirname(HEADER), exist_ok=True)

    baris = [", ".join(f"0x{b:02x}" for b in blob[i:i + 12])
             for i in range(0, len(blob), 12)]
    isi_array = ",\n  ".join(baris)
    with open(HEADER, "w") as f:
        f.write(f"""#ifndef MODEL_INT8_H
#define MODEL_INT8_H

#define ECG_WIN_LEN {WIN_LEN}
#ifndef ECG_N_RR
#define ECG_N_RR {N_RR_FEATURES}
#endif
#define ECG_THRESHOLD {THRESHOLD}f

#define ECG_IN_MORPH_SCALE {q['morph'][0]:.10f}f
#define ECG_IN_MORPH_ZERO  {q['morph'][1]}
#define ECG_IN_RR_SCALE    {q['rr'][0]:.10f}f
#define ECG_IN_RR_ZERO     {q['rr'][1]}
#define ECG_OUT_SCALE      {q['out'][0]:.10f}f
#define ECG_OUT_ZERO       {q['out'][1]}

const unsigned int model_int8_tflite_len = {len(blob)};
alignas(16) const unsigned char model_int8_tflite[] = {{
  {isi_array}
}};

#endif
""")
    print(f"{HEADER}  {os.path.getsize(HEADER) / 1024:.1f} KB")
    print(f"  morph scale={q['morph'][0]:.8f} zero={q['morph'][1]}")
    print(f"  rr    scale={q['rr'][0]:.8f} zero={q['rr'][1]}")
    print(f"  out   scale={q['out'][0]:.8f} zero={q['out'][1]}  → p = (q - {q['out'][1]}) * scale")


if __name__ == "__main__":
    main()
