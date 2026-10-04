#!/usr/bin/env python3
"""Flatten whatever folder layout the Kaggle iBean mirror ships (observed:
Bean_Dataset/<class>/*.jpg directly; some mirrors nest an extra
train/validation/test split level) into raw/bean/ibean/<class>/*.jpg.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = ROOT / "raw" / "bean" / "ibean" / "_download"
OUT_DIR = ROOT / "raw" / "bean" / "ibean"

CLASS_DIR_NAMES = ["healthy", "angular_leaf_spot", "bean_rust"]


def main() -> None:
    if not DOWNLOAD_DIR.exists():
        raise SystemExit(f"{DOWNLOAD_DIR} missing — run scripts/download_bean_ibean_kaggle.sh first.")

    counts = {name: 0 for name in CLASS_DIR_NAMES}
    for class_name in CLASS_DIR_NAMES:
        src_class_dirs = [p for p in DOWNLOAD_DIR.rglob(class_name) if p.is_dir()]
        dst_class_dir = OUT_DIR / class_name
        dst_class_dir.mkdir(parents=True, exist_ok=True)
        for src_class_dir in src_class_dirs:
            # tag with the parent folder name in case of split-level duplicates
            tag = src_class_dir.parent.name
            for img in src_class_dir.glob("*"):
                if img.is_file():
                    dst_name = f"{tag}_{img.name}" if tag != "Bean_Dataset" else img.name
                    shutil.copy2(img, dst_class_dir / dst_name)
                    counts[class_name] += 1

    print("Flattened iBean images by class:")
    for name, n in counts.items():
        print(f"  {name}: {n}")


if __name__ == "__main__":
    main()
