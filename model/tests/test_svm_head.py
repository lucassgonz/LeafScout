from __future__ import annotations

import numpy as np

from leafscout_ml.svm_head import (
    head_to_weights_dict,
    predict_with_weights,
    save_head_weights,
    train_svm_head,
)


def _make_separable_dataset(rng, n_per_class=40, n_features=8, n_classes=3):
    X, y = [], []
    for c in range(n_classes):
        center = np.zeros(n_features)
        center[c] = 5.0  # well-separated clusters along distinct axes
        pts = rng.normal(loc=center, scale=0.3, size=(n_per_class, n_features))
        X.append(pts)
        y += [f"class{c}"] * n_per_class
    return np.vstack(X), y


def test_train_svm_head_fits_separable_data(rng):
    X, y = _make_separable_dataset(rng)
    clf = train_svm_head(X, y)
    acc = (clf.predict(X) == np.asarray(y)).mean()
    assert acc > 0.95


def test_weights_dict_shape_multiclass(rng):
    X, y = _make_separable_dataset(rng, n_classes=3)
    clf = train_svm_head(X, y)
    weights = head_to_weights_dict(clf)

    assert len(weights["classes"]) == 3
    assert np.array(weights["coef"]).shape == (3, X.shape[1])
    assert len(weights["intercept"]) == 3
    assert weights["feature_dim"] == X.shape[1]


def test_weights_dict_shape_binary_expanded_to_two_rows(rng):
    X, y = _make_separable_dataset(rng, n_classes=2)
    clf = train_svm_head(X, y)
    weights = head_to_weights_dict(clf)

    # LinearSVC collapses binary to 1 row internally — we must expand to 2
    # so the app's inference code never needs a binary special case.
    assert len(weights["classes"]) == 2
    assert np.array(weights["coef"]).shape == (2, X.shape[1])


def test_predict_with_weights_matches_sklearn_predict(rng):
    X, y = _make_separable_dataset(rng, n_classes=3)
    clf = train_svm_head(X, y)
    weights = head_to_weights_dict(clf)

    mismatches = 0
    for i in range(len(X)):
        predicted_class, confidence, _ = predict_with_weights(X[i], weights)
        if predicted_class != clf.predict(X[i : i + 1])[0]:
            mismatches += 1
        assert 0.0 <= confidence <= 1.0

    # The JSON-weights reference implementation must agree with sklearn's own
    # decision_function-based argmax on (almost) every sample.
    assert mismatches / len(X) < 0.02


def test_predict_with_weights_probs_sum_to_one(rng):
    X, y = _make_separable_dataset(rng, n_classes=3)
    clf = train_svm_head(X, y)
    weights = head_to_weights_dict(clf)

    _, _, probs = predict_with_weights(X[0], weights)
    assert abs(sum(probs.values()) - 1.0) < 1e-6


def test_save_head_weights_round_trips(tmp_path, rng):
    import json

    X, y = _make_separable_dataset(rng, n_classes=2)
    clf = train_svm_head(X, y)
    weights = head_to_weights_dict(clf)

    out_path = save_head_weights(weights, tmp_path / "coffee_head.json")
    loaded = json.loads(out_path.read_text())
    assert loaded["classes"] == weights["classes"]
