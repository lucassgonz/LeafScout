"""Crop/class configuration shared by every pipeline stage.

Each crop maps one or more raw dataset sources to a single set of final class
names. ``None`` as a target class means "ignore this folder" (e.g. a species
that isn't actually the crop in question, or an "unknown"/background bucket).

Folder matching is case-insensitive substring matching against the raw image's
parent directory name, checked in the order listed — see
``leafscout_ml.manifest.classify_folder``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "raw"
FUSED_DIR = ROOT / "fused"
ARTIFACTS_DIR = ROOT / "artifacts"

IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

# Backbone shared by every crop head — the one piece that is NOT crop-specific.
BACKBONE_NAME = "mobilenet_v3_small"
IMAGE_SIZE = 224

# phash near-duplicate threshold (Hamming distance), same choice as the
# original bean-only fusion scripts this pipeline generalizes.
PHASH_HAMMING_THRESHOLD = 5

SPLIT_RATIOS = {"train": 0.7, "val": 0.15, "test": 0.15}
RANDOM_SEED = 42
CV_FOLDS = 5


@dataclass(frozen=True)
class CropConfig:
    crop_id: str
    display_name: str
    # source_name -> {folder_substring: final_class_name_or_None}
    class_map: dict[str, dict[str, str | None]]
    # one-line note on what this crop's data does NOT cover — scored under
    # "Responsible AI" / "Data grounding" in the concept note.
    known_gap: str = ""


CROPS: dict[str, CropConfig] = {
    "coffee": CropConfig(
        crop_id="coffee",
        display_name="Coffee (Arabica)",
        class_map={
            # BRACOL (Mendeley, CC BY 4.0) — symptom-leaf folders.
            "bracol": {
                "healthy": "healthy",
                "rust": "rust",
                "miner": "leaf_miner",
                "phoma": "phoma",
                "cercospora": "cercospora",
            },
        },
        known_gap=(
            "No post-harvest/berry defect classes; BRACOL leaves were photographed "
            "against a partially controlled white background, not pure field conditions "
            "— cross-checked against PlantDoc where a matching class exists. The "
            "Mendeley-hosted archive had no valid End-Of-Central-Directory record "
            "(recovered via scripts/recover_bracol_zip.py's manual local-header scan); "
            "~20% of the 1747 leaf images were unrecoverable (truncated past that point "
            "in the corrupt archive), and the ~62 images with no single predominant "
            "stress (dataset.csv's mixed-label rows) were excluded from this "
            "single-label classifier. Trained on 1342 of 1747 images as a result."
        ),
    ),
    "cassava": CropConfig(
        crop_id="cassava",
        display_name="Cassava",
        class_map={
            # Makerere/NaCRRI Cassava Leaf Disease dataset, as distributed via the
            # Kaggle "Cassava Leaf Disease Classification" competition. That
            # competition's official label map uses "Green Mottle" (CGM); older,
            # pre-competition releases of the same underlying data sometimes used
            # "Green Mite" for the same class — both substrings are accepted here
            # and normalized to the Kaggle name.
            "cassava": {
                "healthy": "healthy",
                "cmd": "mosaic_disease",
                "mosaic": "mosaic_disease",
                "cbb": "bacterial_blight",
                "bacterial": "bacterial_blight",
                "green_mottle": "green_mottle",
                "cgm": "green_mottle",
                "green_mite": "green_mottle",
                "cbsd": "brown_streak",
                "brown_streak": "brown_streak",
            },
        },
        known_gap=(
            "Published lightweight-model accuracy on this dataset is materially lower "
            "than for coffee or bean (literature: 65-71% with MobileNet/MobileNetV2) — "
            "disclosed explicitly in the app and the submission, not presented as solved."
        ),
    ),
    "bean": CropConfig(
        crop_id="bean",
        display_name="Common bean",
        class_map={
            # iBean (Makerere/NaCRRI, CC0) — the dataset this challenge names.
            "ibean": {
                "healthy": "healthy",
                "angular_leaf_spot": "angular_leaf_spot",
                "bean_rust": "rust",
            },
            # Optional enrichment sources kept from the earlier bean-only fusion
            # (not required by the challenge, included only if raw/bean/tanzania
            # or raw/bean/bangladesh are present — see build_manifest.py).
            "tanzania": {
                "healthy": "healthy",
                "rust": "rust",
                "anthra": "anthracnose",
            },
            "bangladesh": {
                "fresh_leaf": "healthy",
                "rust": "rust",
                "blight": "bacterial_blight",
                "mosaic_virus": "mosaic_common",
                # cowpea classes are a different species (Vigna unguiculata) — excluded.
                "cowpea": None,
            },
        },
        known_gap=(
            "No public image dataset located yet for Bean Golden Mosaic (BGMV, "
            "whitefly-vector) — only Mosaic-Common (BCMV, aphid-vector) is covered."
        ),
    ),
}


def crop_raw_dir(crop_id: str) -> Path:
    return RAW_DIR / crop_id


def crop_fused_dir(crop_id: str) -> Path:
    return FUSED_DIR / crop_id


def all_class_names(crop_id: str) -> list[str]:
    cfg = CROPS[crop_id]
    names: set[str] = set()
    for source_map in cfg.class_map.values():
        for target in source_map.values():
            if target is not None:
                names.add(target)
    return sorted(names)
