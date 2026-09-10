"""model — Fase 4: arsitektur hybrid dua-cabang. Walkthrough: docs/model-walkthrough.md"""
from tensorflow.keras import Input, Model, layers

from config import (
    WIN_LEN, N_RR_FEATURES, CONV_FILTERS, CONV_KERNELS, POOL_SIZE,
    DENSE_UNITS, DROPOUT_RATE,
)


def build_hybrid_model(dropout_rate: float = DROPOUT_RATE) -> Model:
    morph_in = Input(shape=(WIN_LEN, 1), name="morphology")
    x = morph_in
    for filters, kernel in zip(CONV_FILTERS, CONV_KERNELS):
        x = layers.Conv1D(filters, kernel, activation="relu", padding="same")(x)
        x = layers.MaxPooling1D(POOL_SIZE)(x)
    x = layers.GlobalAveragePooling1D()(x)

    rr_in = Input(shape=(N_RR_FEATURES,), name="rhythm")

    merged = layers.Concatenate()([x, rr_in])
    merged = layers.Dense(DENSE_UNITS, activation="relu")(merged)
    if dropout_rate > 0:
        merged = layers.Dropout(dropout_rate)(merged)
    out = layers.Dense(1, activation="sigmoid", name="arrhythmia")(merged)

    return Model(inputs=[morph_in, rr_in], outputs=out, name="hybrid_ecg")
