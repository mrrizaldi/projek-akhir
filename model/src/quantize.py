"""quantize — Fase 7: PTQ INT8 + inferensi tflite. Walkthrough: docs/quantize-walkthrough.md"""
import numpy as np
import tensorflow as tf

from config import INT8_IO, REP_SAMPLES, SEED


def stratified_indices(y, n: int = REP_SAMPLES, seed: int = SEED) -> np.ndarray:
    y = np.asarray(y).astype(int)
    rng = np.random.default_rng(seed)
    idx = []
    for kelas in (0, 1):
        pool = np.flatnonzero(y == kelas)
        if len(pool) == 0:
            raise ValueError(f"kelas {kelas} tidak ada di data kalibrasi (JEBAKAN #4)")
        ambil = max(1, round(n * len(pool) / len(y)))
        idx.append(rng.choice(pool, size=min(ambil, len(pool)), replace=False))
    return np.sort(np.concatenate(idx))


def representative_dataset_gen(X_morph, X_rr, y, n: int = REP_SAMPLES,
                               seed: int = SEED, rr_shape=None):
    """Generator kalibrasi. Yield DICT bernama — list posisional bikin converter
    salah memasangkan tensor pada model dua-input (JEBAKAN #3).

    rr_shape: bentuk per-sampel input ritme; model deploy memakai (1, 3).
    """
    idx = stratified_indices(y, n, seed)
    bentuk = (1,) + tuple(rr_shape) if rr_shape else None

    def gen():
        for i in idx:
            rr = X_rr[i:i + 1].astype(np.float32)
            yield {
                "morphology": X_morph[i:i + 1].astype(np.float32),
                "rhythm": rr.reshape(bentuk) if bentuk else rr,
            }

    return gen


def quantize_int8(model, rep_gen, int8_io: bool = INT8_IO) -> bytes:
    """model: keras Model (pakai build_deploy_model, bukan model latih langsung)."""
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = rep_gen
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    if int8_io:
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
    return converter.convert()


def _quantize(x, detail):
    scale, zero = detail["quantization"]
    if scale == 0:
        return x.astype(detail["dtype"])
    return np.clip(np.round(x / scale) + zero, -128, 127).astype(detail["dtype"])


def _dequantize(q, detail):
    scale, zero = detail["quantization"]
    return (q.astype(np.float32) - zero) * scale if scale else q.astype(np.float32)


def predict_tflite(tflite_path: str, X_morph, X_rr) -> np.ndarray:
    interp = tf.lite.Interpreter(model_path=tflite_path)
    interp.allocate_tensors()
    # Bedakan lewat JUMLAH ELEMEN, bukan jumlah dimensi: di model deploy
    # ritme berbentuk (1,1,3) — sama-sama 3 dimensi dengan morfologi.
    inputs = sorted(interp.get_input_details(), key=lambda d: int(np.prod(d["shape"])))
    rr_in, morph_in = inputs[0], inputs[1]
    out = interp.get_output_details()[0]

    prob = np.empty(len(X_morph), dtype=np.float32)
    for i in range(len(X_morph)):
        interp.set_tensor(morph_in["index"],
                          _quantize(X_morph[i:i + 1].astype(np.float32), morph_in))
        interp.set_tensor(rr_in["index"],
                          _quantize(X_rr[i:i + 1].astype(np.float32), rr_in)
                          .reshape(rr_in["shape"]))
        interp.invoke()
        prob[i] = _dequantize(interp.get_tensor(out["index"]), out).ravel()[0]
    return prob
