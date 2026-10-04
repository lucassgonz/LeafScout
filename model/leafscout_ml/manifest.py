"""Scan a crop's raw/<source>/... tree, assign final class names, hash images.

Generalizes the bean-only fusion scripts in ../../bean-disease-dataset/scripts
to work for any crop in ``leafscout_ml.config.CROPS``.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from .config import IMG_EXTENSIONS, CropConfig

try:  # optional at import time so non-image tests don't need Pillow/imagehash
    import imagehash
    from PIL import Image
except ImportError:  # pragma: no cover
    imagehash = None
    Image = None


def classify_folder(source: str, folder_name: str, class_map: dict[str, dict[str, str | None]]) -> str | None:
    """Match a folder name against a source's substring->class map.

    Returns the final class name, ``None`` if the folder is explicitly
    excluded, or raises ``KeyError`` if nothing matches (fail loudly rather
    than silently dropping unexpected classes).
    """
    source_map = class_map.get(source)
    if source_map is None:
        raise KeyError(f"No class map registered for source '{source}'")

    folder_lower = folder_name.lower()
    for substring, target in source_map.items():
        if substring.lower() in folder_lower:
            return target
    raise KeyError(
        f"Folder '{folder_name}' under source '{source}' did not match any known "
        f"class substring. Known substrings: {sorted(source_map)}"
    )


def file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def file_phash(path: Path) -> str | None:
    if imagehash is None or Image is None:
        return None
    try:
        with Image.open(path) as img:
            return str(imagehash.phash(img))
    except Exception:
        return None


def build_manifest(raw_dir: Path, crop: CropConfig, sources: list[str] | None = None) -> pd.DataFrame:
    """Walk ``raw_dir/<source>/**`` for every source in ``crop.class_map``.

    ``sources`` lets callers restrict to the sources actually present on disk
    (e.g. skip optional enrichment sources that weren't downloaded).
    """
    rows = []
    active_sources = sources if sources is not None else list(crop.class_map)

    for source in active_sources:
        source_dir = raw_dir / source
        if not source_dir.exists():
            continue
        for img_path in sorted(source_dir.rglob("*")):
            if not img_path.is_file() or img_path.suffix.lower() not in IMG_EXTENSIONS:
                continue
            folder_name = img_path.parent.name
            try:
                final_class = classify_folder(source, folder_name, crop.class_map)
            except KeyError:
                continue  # unrecognized folder (e.g. a readme asset dir) — skip, don't crash the scan
            if final_class is None:
                continue  # explicitly excluded class (e.g. cowpea)

            rows.append(
                {
                    "path_original": str(img_path),
                    "source": source,
                    "class_original": folder_name,
                    "class_final": final_class,
                    "md5": file_md5(img_path),
                    "phash": file_phash(img_path),
                }
            )

    return pd.DataFrame(
        rows,
        columns=["path_original", "source", "class_original", "class_final", "md5", "phash"],
    )
