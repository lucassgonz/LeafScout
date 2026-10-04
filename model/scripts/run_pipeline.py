#!/usr/bin/env python3
"""End-to-end pipeline for one crop: manifest -> dedup -> split -> embeddings
-> SVM head -> 5-fold CV -> per-source accuracy -> export.

Usage:
    .venv/bin/python scripts/run_pipeline.py coffee
    .venv/bin/python scripts/run_pipeline.py cassava
    .venv/bin/python scripts/run_pipeline.py bean
    .venv/bin/python scripts/run_pipeline.py all   # every crop, shares one backbone export
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from leafscout_ml.config import (  # noqa: E402
    ARTIFACTS_DIR,
    CROPS,
    RAW_DIR,
    crop_fused_dir,
    crop_raw_dir,
)
from leafscout_ml.dedup import dedup  # noqa: E402
from leafscout_ml.manifest import build_manifest  # noqa: E402
from leafscout_ml.metrics import cross_validate_svm, per_source_accuracy  # noqa: E402
from leafscout_ml.split import stratified_split  # noqa: E402
from leafscout_ml.svm_head import head_to_weights_dict, save_head_weights, train_svm_head  # noqa: E402


def run_crop(crop_id: str, backbone) -> dict:
    from leafscout_ml.embeddings import extract_embeddings  # lazy: needs TensorFlow

    cfg = CROPS[crop_id]
    raw_dir = crop_raw_dir(crop_id)
    fused_dir = crop_fused_dir(crop_id)
    fused_dir.mkdir(parents=True, exist_ok=True)

    sources_present = [s for s in cfg.class_map if (raw_dir / s).exists()]
    if not sources_present:
        print(f"[{crop_id}] no raw data found under {raw_dir} — skipping. "
              f"Run the matching scripts/download_*.sh first.")
        return {"crop_id": crop_id, "status": "skipped_no_data"}

    print(f"[{crop_id}] sources present: {sources_present}")
    manifest = build_manifest(raw_dir, cfg, sources=sources_present)
    print(f"[{crop_id}] manifest: {len(manifest)} images, classes={sorted(manifest['class_final'].unique())}")

    deduped, dup_report = dedup(manifest)
    n_dupe_clusters = (deduped.groupby("cluster_id").size() > 1).sum()
    print(f"[{crop_id}] dedup: {n_dupe_clusters} duplicate/near-duplicate clusters found")

    split_df = stratified_split(deduped)
    split_df.to_csv(fused_dir / "manifest_final.csv", index=False)
    dup_report.to_csv(fused_dir / "duplicates_report.csv", index=False)
    print(f"[{crop_id}] split sizes: {split_df['split'].value_counts().to_dict()}")

    # Embeddings for every row once (train+val+test), reused for CV (train)
    # and for the held-out test/per-source evaluation.
    print(f"[{crop_id}] extracting embeddings for {len(split_df)} images...")
    embeddings = extract_embeddings(split_df["path_original"].tolist(), backbone=backbone)
    np.save(fused_dir / "embeddings.npy", embeddings)

    train_mask = split_df["split"] == "train"
    test_mask = split_df["split"] == "test"
    X_train, y_train = embeddings[train_mask.values], split_df.loc[train_mask, "class_final"].tolist()
    X_test, y_test = embeddings[test_mask.values], split_df.loc[test_mask, "class_final"].tolist()
    test_sources = split_df.loc[test_mask, "source"].tolist()

    cv_result = cross_validate_svm(X_train, np.array(y_train), k=5)
    print(
        f"[{crop_id}] 5-fold CV accuracy: {cv_result['mean']:.3f} ± {cv_result['std']:.3f}  "
        f"(balanced: {cv_result['balanced_mean']:.3f})"
    )

    final_head = train_svm_head(X_train, y_train)
    test_preds = final_head.predict(X_test)
    test_accuracy = float(np.mean(np.array(test_preds) == np.array(y_test)))
    source_accuracy = per_source_accuracy(y_test, list(test_preds), test_sources)
    print(f"[{crop_id}] held-out test accuracy: {test_accuracy:.3f}")
    print(f"[{crop_id}] per-source test accuracy: {source_accuracy}")

    weights = head_to_weights_dict(final_head)
    head_path = ARTIFACTS_DIR / f"{crop_id}_head.json"
    save_head_weights(weights, head_path)

    registry_row = {
        "crop_id": crop_id,
        "backbone": "mobilenet_v3_small",
        "head_type": "svm",
        "head_weights_asset": str(head_path.relative_to(ARTIFACTS_DIR.parent)),
        "trained_on_dataset": "+".join(sources_present),
        "n_train": int(train_mask.sum()),
        "n_test": int(test_mask.sum()),
        "accuracy_5fold_mean": cv_result["mean"],
        "accuracy_5fold_std": cv_result["std"],
        "accuracy_5fold_by_fold": cv_result["fold_accuracies"],
        "balanced_accuracy_5fold_mean": cv_result["balanced_mean"],
        "test_accuracy": test_accuracy,
        "test_accuracy_by_source": source_accuracy,
        "known_gap": cfg.known_gap,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return registry_row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("crop", choices=[*CROPS.keys(), "all"])
    args = parser.parse_args()

    from leafscout_ml.embeddings import export_backbone_tflite, load_backbone

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    backbone = load_backbone()

    backbone_path = ARTIFACTS_DIR / "backbone_mobilenet_v3_small.tflite"
    if not backbone_path.exists():
        print("Exporting shared MobileNetV3-Small backbone to TFLite...")
        export_backbone_tflite(backbone, backbone_path)
        print(f"Backbone exported: {backbone_path} ({backbone_path.stat().st_size / 1e6:.2f} MB)")

    crop_ids = list(CROPS.keys()) if args.crop == "all" else [args.crop]
    registry_path = ARTIFACTS_DIR / "model_registry.json"
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else []

    for crop_id in crop_ids:
        result = run_crop(crop_id, backbone)
        registry = [r for r in registry if r.get("crop_id") != crop_id] + [result]

    registry_path.write_text(json.dumps(registry, indent=2))
    print(f"\nWrote {registry_path}")


if __name__ == "__main__":
    main()
