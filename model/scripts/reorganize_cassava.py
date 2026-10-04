#!/usr/bin/env python3
"""Turn the Kaggle cassava competition's flat train_images/ + train.csv into
the raw/cassava/cassava/<class_name>/*.jpg layout build_manifest.py expects.

Usage:
    .venv/bin/python scripts/reorganize_cassava.py
"""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = ROOT / "raw" / "cassava" / "cassava" / "_download"
OUT_DIR = ROOT / "raw" / "cassava" / "cassava"

# Kaggle "Cassava Leaf Disease Classification" official label map.
LABEL_MAP = {
    0: "bacterial_blight",
    1: "brown_streak",
    2: "green_mottle",
    3: "mosaic_disease",
    4: "healthy",
}


def main() -> None:
    csv_path = DOWNLOAD_DIR / "train.csv"
    images_dir = DOWNLOAD_DIR / "train_images"
    if not csv_path.exists() or not images_dir.exists():
        raise SystemExit(
            f"Expected {csv_path} and {images_dir} — run "
            "scripts/download_cassava_kaggle.sh first."
        )

    counts = {name: 0 for name in LABEL_MAP.values()}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = int(row["label"])
            class_name = LABEL_MAP[label]
            src = images_dir / row["image_id"]
            if not src.exists():
                continue
            dst_dir = OUT_DIR / class_name
            dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst_dir / src.name)
            counts[class_name] += 1

    print("Reorganized cassava images by class:")
    for name, n in counts.items():
        print(f"  {name}: {n}")
    print(f"\nYou can now remove {DOWNLOAD_DIR} to save disk space if desired.")


if __name__ == "__main__":
    main()
