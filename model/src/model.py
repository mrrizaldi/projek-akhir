import numpy as np
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


def build_deploy_model(trained: Model) -> Model:
    morph_in = Input(shape=(WIN_LEN, 1), name="morphology")
    x = morph_in
    for layer in trained.layers:
        if isinstance(layer, (layers.Conv1D, layers.MaxPooling1D)):
            x = layer.__class__.from_config(layer.get_config())(x)
    langkah, kanal = int(x.shape[1]), int(x.shape[2])
    x = layers.DepthwiseConv1D(kernel_size=langkah, use_bias=False, name="gap_dw")(x)

    rr_in = Input(shape=(1, N_RR_FEATURES), name="rhythm")
    y = layers.Concatenate(axis=-1)([x, rr_in])
    y = layers.Conv1D(DENSE_UNITS, 1, activation="relu", name="dense_1x1")(y)
    y = layers.Conv1D(1, 1, activation="sigmoid", name="arrhythmia")(y)
    deploy = Model([morph_in, rr_in], y, name="hybrid_ecg_deploy")

    conv_lama = [l for l in trained.layers if isinstance(l, layers.Conv1D)]
    conv_baru = [l for l in deploy.layers
                 if isinstance(l, layers.Conv1D) and l.name.startswith("conv")]
    for lama, baru in zip(conv_lama, conv_baru):
        baru.set_weights(lama.get_weights())
    deploy.get_layer("gap_dw").set_weights(
        [np.full((langkah, kanal, 1), 1.0 / langkah, dtype=np.float32)])

    dense = [l for l in trained.layers if isinstance(l, layers.Dense)]
    for l, nama in zip(dense, ("dense_1x1", "arrhythmia")):
        w, b = l.get_weights()
        deploy.get_layer(nama).set_weights([w[np.newaxis, ...], b])
    return deploy
