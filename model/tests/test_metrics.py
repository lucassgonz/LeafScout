from __future__ import annotations

import numpy as np

from leafscout_ml.metrics import cross_validate_svm, per_source_accuracy


def _make_separable_dataset(rng, n_per_class=50, n_features=8, n_classes=3):
    X, y = [], []
    for c in range(n_classes):
        center = np.zeros(n_features)
        center[c] = 5.0
        pts = rng.normal(loc=center, scale=0.3, size=(n_per_class, n_features))
        X.append(pts)
        y += [f"class{c}"] * n_per_class
    return np.vstack(X), y


def test_cross_validate_svm_runs_k_folds(rng):
    X, y = _make_separable_dataset(rng)
    result = cross_validate_svm(X, y, k=5)
    assert result["k"] == 5
    assert len(result["fold_accuracies"]) == 5


def test_cross_validate_svm_high_accuracy_on_separable_data(rng):
    X, y = _make_separable_dataset(rng)
    result = cross_validate_svm(X, y, k=5)
    assert result["mean"] > 0.9
    assert all(0.0 <= a <= 1.0 for a in result["fold_accuracies"])


def test_cross_validate_svm_is_deterministic_given_seed(rng):
    X, y = _make_separable_dataset(rng)
    r1 = cross_validate_svm(X, y, k=5, seed=7)
    r2 = cross_validate_svm(X, y, k=5, seed=7)
    assert r1["fold_accuracies"] == r2["fold_accuracies"]


def test_per_source_accuracy_separates_good_and_bad_sources():
    y_true = ["rust"] * 10 + ["healthy"] * 10
    y_pred = ["rust"] * 10 + ["rust"] * 5 + ["healthy"] * 5  # second source is 50% wrong
    source = ["lab"] * 10 + ["field"] * 10

    result = per_source_accuracy(y_true, y_pred, source)
    assert result["lab"] == 1.0
    assert result["field"] == 0.5


def test_per_source_accuracy_covers_every_source():
    y_true = ["a", "b", "a"]
    y_pred = ["a", "b", "b"]
    source = ["s1", "s2", "s3"]
    result = per_source_accuracy(y_true, y_pred, source)
    assert set(result) == {"s1", "s2", "s3"}
