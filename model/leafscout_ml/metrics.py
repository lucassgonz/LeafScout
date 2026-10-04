"""5-fold CV and per-source accuracy reporting.

Per-source breakdown exists because pooled accuracy can hide a model that
only works on one easy source (e.g. studio-background BRACOL leaves) while
failing on field-condition sources — the generalization gap flagged in
ARCHITECTURE.md §5.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import LinearSVC


def cross_validate_svm(
    X: np.ndarray,
    y: list[str],
    k: int = 5,
    C: float = 1.0,
    seed: int = 42,
) -> dict:
    """Stratified k-fold CV accuracy for a LinearSVC head.

    Returns per-fold accuracy, mean, and std — the format used for
    ``model_registry.accuracy_5fold_mean`` in the Supabase/SQLite schema.
    """
    y = np.asarray(y)
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)

    fold_accuracies = []
    fold_balanced_accuracies = []
    for train_idx, test_idx in skf.split(X, y):
        clf = LinearSVC(C=C, max_iter=10_000, class_weight="balanced")
        clf.fit(X[train_idx], y[train_idx])
        preds = clf.predict(X[test_idx])
        acc = float(np.mean(preds == y[test_idx]))
        fold_accuracies.append(acc)
        # Plain accuracy on an imbalanced crop (cassava: ~12x class skew) can
        # look good just by favoring the majority class — balanced accuracy
        # (average per-class recall) catches that; report both.
        fold_balanced_accuracies.append(float(balanced_accuracy_score(y[test_idx], preds)))

    return {
        "k": k,
        "fold_accuracies": fold_accuracies,
        "mean": float(np.mean(fold_accuracies)),
        "std": float(np.std(fold_accuracies)),
        "fold_balanced_accuracies": fold_balanced_accuracies,
        "balanced_mean": float(np.mean(fold_balanced_accuracies)),
    }


def per_source_accuracy(y_true: list[str], y_pred: list[str], source: list[str]) -> dict[str, float]:
    """Accuracy broken down by originating dataset source.

    A pooled number near 95% with one source at 60% is a materially different
    (and more honest) result than a flat 95% — this is what gets reported in
    the submission per ARCHITECTURE.md §5/§9.
    """
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred)
    source_arr = np.asarray(source)

    result: dict[str, float] = {}
    for src in sorted(set(source)):
        mask = source_arr == src
        if mask.sum() == 0:
            continue
        result[src] = float(np.mean(y_true_arr[mask] == y_pred_arr[mask]))
    return result
