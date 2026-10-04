#!/usr/bin/env python3
"""Turn the recovered BRACOL leaf/ images + dataset.csv into the
raw/coffee/bracol/<class_name>/*.jpg layout build_manifest.py expects.

dataset.csv's `predominant_stress` column: 0=healthy, 1=miner, 2=rust,
3=phoma, 4=cercospora, 5=multiple stresses with no single predominant one
(mixed cases are excluded here — a single-label classifier can't honestly
use them, and this matches how the published BRACOL papers describe
"predominant" stress labeling).

Run scripts/recover_bracol_zip.py first if raw/coffee/_download/recovered/
doesn't exist yet (the Mendeley-hosted inner zip has no valid End-Of-Central-
Directory record — see model/README.md "Known issues" — so plain `unzip`
fails on it and this manual recovery is required).
"""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECOVERED_DIR = ROOT / "raw" / "coffee" / "_download" / "recovered" / "coffee-datasets" / "coffee-datasets" / "leaf"
OUT_DIR = ROOT / "raw" / "coffee" / "bracol"

LABEL_MAP = {
    "0": "healthy",
    "1": "leaf_miner",
    "2": "rust",
    "3": "phoma",
    "4": "cercospora",
    # "5" (mixed/no single predominant stress) is intentionally excluded.
}


def main() -> None:
    csv_path = RECOVERED_DIR / "dataset.csv"
    images_dir = RECOVERED_DIR / "images"
    if not csv_path.exists() or not images_dir.exists():
        raise SystemExit(
            f"Expected {csv_path} and {images_dir} — run "
            "scripts/recover_bracol_zip.py first."
        )

    counts = {name: 0 for name in LABEL_MAP.values()}
    missing = 0
    excluded_mixed = 0
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            stress = row["predominant_stress"]
            if stress not in LABEL_MAP:
                excluded_mixed += 1
                continue
            class_name = LABEL_MAP[stress]
            src = images_dir / f"{row['id']}.jpg"
            if not src.exists():
                missing += 1  # lost to the archive truncation — see recover_bracol_zip.py output
                continue
            dst_dir = OUT_DIR / class_name
            dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst_dir / src.name)
            counts[class_name] += 1

    print("Reorganized BRACOL images by class:")
    for name, n in counts.items():
        print(f"  {name}: {n}")
    print(f"\nExcluded (mixed/no single predominant stress): {excluded_mixed}")
    print(f"Missing (lost to archive truncation, see recover_bracol_zip.py): {missing}")


if __name__ == "__main__":
    main()
