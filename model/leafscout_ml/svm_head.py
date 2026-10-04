"""Per-crop linear SVM head trained on frozen MobileNet embeddings.

Exports to a small JSON weight matrix so the phone app can run
``argmax(W @ embedding + b)`` in plain app code — no extra ML runtime needed
beyond the one shared TFLite backbone. See ARCHITECTURE.md §4.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.svm import LinearSVC


def train_svm_head(X: np.ndarray, y: list[str], C: float = 1.0) -> LinearSVC:
    # class_weight='balanced' matters here: cassava's classes are ~12x
    # imbalanced in the raw data (mosaic disease dominates) — an unweighted
    # SVM would just learn to mostly predict the majority class.
    clf = LinearSVC(C=C, max_iter=10_000, class_weight="balanced")
    clf.fit(X, y)
    return clf


def head_to_weights_dict(clf: LinearSVC, class_names: list[str] | None = None) -> dict:
    """Serialize a trained LinearSVC into the JSON shape the app expects.

    ``coef_`` is (n_classes, n_features) for multi-class (or (1, n_features)
    for binary — normalized here to always look multi-class so the app's
    inference code doesn't need a binary special case).
    """
    classes = list(clf.classes_)
    coef = np.asarray(clf.coef_)
    intercept = np.asarray(clf.intercept_)

    if coef.shape[0] == 1 and len(classes) == 2:
        # LinearSVC collapses binary problems to a single decision boundary;
        # expand to one row per class so app-side code is uniform.
        coef = np.vstack([-coef[0], coef[0]])
        intercept = np.array([-intercept[0], intercept[0]])

    return {
        "classes": classes,
        "coef": coef.tolist(),
        "intercept": intercept.tolist(),
        "feature_dim": coef.shape[1],
    }


def save_head_weights(weights: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(weights, indent=2))
    return out_path


def predict_with_weights(embedding: np.ndarray, weights: dict) -> tuple[str, float, dict[str, float]]:
    """Reference implementation of the app-side inference math.

    Used both to sanity-check exported weights against sklearn's own
    ``.predict`` and as the single source of truth the RN app's JS port
    should match (see app/src/ml/svmHead.ts once the app scaffold lands).
    """
    coef = np.asarray(weights["coef"])
    intercept = np.asarray(weights["intercept"])
    classes = weights["classes"]

    scores = coef @ embedding + intercept
    # Softmax over raw SVM decision scores — not a calibrated probability,
    # but a stable, monotonic confidence proxy for the guardrail threshold.
    exp_scores = np.exp(scores - scores.max())
    probs = exp_scores / exp_scores.sum()

    best_idx = int(np.argmax(scores))
    return classes[best_idx], float(probs[best_idx]), dict(zip(classes, probs.tolist()))
