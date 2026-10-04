from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

# Make `leafscout_ml` importable without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from leafscout_ml.config import CropConfig  # noqa: E402


@pytest.fixture
def toy_crop() -> CropConfig:
    """A minimal 2-source, 2-class crop config, mirroring the real ones' shape."""
    return CropConfig(
        crop_id="toycrop",
        display_name="Toy Crop",
        class_map={
            "sourcea": {"healthy": "healthy", "rust": "rust"},
            "sourceb": {"ok": "healthy", "rusty": "rust", "other_species": None},
        },
        known_gap="test fixture — no real gap",
    )


def _make_image(path: Path, seed: int, size: tuple[int, int] = (48, 48), jitter: int = 0) -> None:
    """A reproducible noise-textured image (flat colors give pHash no texture
    to hash on — nearly all solid-color images collapse to the same pHash)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    base = rng.integers(0, 256, size=(size[1], size[0], 3), dtype=np.uint8)
    if jitter:
        noise = np.random.default_rng(seed + 10_000).integers(
            -jitter, jitter + 1, size=base.shape
        )
        base = np.clip(base.astype(int) + noise, 0, 255).astype(np.uint8)
    Image.fromarray(base, mode="RGB").save(path)


@pytest.fixture
def toy_raw_dir(tmp_path: Path, toy_crop: CropConfig) -> Path:
    """Build a tiny raw/ tree matching toy_crop's class map, with a few exact
    and near-duplicate images planted across sources."""
    raw = tmp_path / "raw"

    # sourcea/healthy: 2 distinct (different seeds -> uncorrelated noise)
    _make_image(raw / "sourcea" / "healthy" / "h1.png", seed=1)
    _make_image(raw / "sourcea" / "healthy" / "h2.png", seed=2)

    # sourcea/rust: 2 distinct images
    _make_image(raw / "sourcea" / "rust" / "r1.png", seed=100)
    _make_image(raw / "sourcea" / "rust" / "r2.png", seed=101)

    # sourceb/ok (-> healthy): one EXACT duplicate of sourcea/healthy/h1.png
    _make_image(raw / "sourceb" / "ok" / "dup_of_h1.png", seed=1)
    _make_image(raw / "sourceb" / "ok" / "h3.png", seed=3)

    # sourceb/rusty (-> rust): a near-duplicate of r1 (small pixel jitter) + one distinct
    _make_image(raw / "sourceb" / "rusty" / "near_r1.png", seed=100, jitter=4)
    _make_image(raw / "sourceb" / "rusty" / "r3.png", seed=102)

    # sourceb/other_species: excluded entirely (class_map maps to None)
    _make_image(raw / "sourceb" / "other_species" / "x1.png", seed=999)

    # An unrecognized folder — build_manifest must skip it, not crash.
    _make_image(raw / "sourcea" / "unexpected_folder" / "u1.png", seed=998)

    return raw


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(42)
