import numpy as np
import pytest
from tensorflow import keras

from src.train import BestWeightAverage, make_class_weights


def _single_weight_model():
    return keras.Sequential([keras.layers.Input(shape=(1,)),
                             keras.layers.Dense(1, use_bias=False)])


def _run_epochs(cb, auc_history):
    m = _single_weight_model()
    cb.set_model(m)
    for auc, w in auc_history:
        m.set_weights([np.array([[w]], dtype=np.float32)])
        cb.on_epoch_end(0, {"val_auc": auc})
    cb.on_train_end()
    return float(m.get_weights()[0][0, 0])


def test_weights_inversely_proportional():
    y = np.array([0] * 90 + [1] * 10)
    w = make_class_weights(y)
    assert np.isclose(w[0], 100 / (2 * 90))
    assert np.isclose(w[1], 100 / (2 * 10))
    assert w[1] > w[0]


def test_two_class_contributions_equal():
    y = np.array([0] * 90 + [1] * 10)
    w = make_class_weights(y)
    assert np.isclose(90 * w[0], 10 * w[1])


def test_balanced_means_weight_one():
    w = make_class_weights(np.array([0, 0, 1, 1]))
    assert np.isclose(w[0], 1.0) and np.isclose(w[1], 1.0)


def test_empty_class_errors_not_division_by_zero():
    with pytest.raises(ValueError):
        make_class_weights(np.zeros(10, dtype=int))


def test_weight_average_averages_best_n_not_picking_argmax():
    averaged_weight = _run_epochs(BestWeightAverage("val_auc", 3),
                                [(0.90, 4.0), (0.80, 50.0), (0.92, 3.0),
                                 (0.50, 99.0), (0.91, 5.0)])
    assert np.isclose(averaged_weight, 4.0)


def test_bad_epoch_excluded_from_average():
    averaged_weight = _run_epochs(BestWeightAverage("val_auc", 2),
                                [(0.9, 1.0), (0.1, 1000.0), (0.8, 3.0)])
    assert np.isclose(averaged_weight, 2.0)


def test_n_larger_than_epoch_count_uses_all():
    averaged_weight = _run_epochs(BestWeightAverage("val_auc", 10), [(0.9, 2.0), (0.8, 4.0)])
    assert np.isclose(averaged_weight, 3.0)
