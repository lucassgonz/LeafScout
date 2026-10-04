"""Shared MobileNetV3-Small feature extractor (the one backbone every crop head sits on).

TensorFlow is imported lazily inside functions so that the rest of this
package (manifest/dedup/split/svm_head/metrics) stays importable and testable
in environments without TensorFlow installed.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import IMAGE_SIZE


def load_backbone():
    """Return a frozen MobileNetV3-Small, ImageNet weights, GAP-pooled output."""
    import tensorflow as tf

    base = tf.keras.applications.MobileNetV3Small(
        input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3),
        include_top=False,
        pooling="avg",
        weights="imagenet",
        include_preprocessing=True,  # accepts raw 0-255 uint8/float input
    )
    base.trainable = False
    return base


def _load_image_array(path: str) -> np.ndarray:
    from PIL import Image as PILImage

    with PILImage.open(path) as img:
        img = img.convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE))
        return np.asarray(img, dtype=np.float32)


def extract_embeddings(image_paths: list[str], backbone=None, batch_size: int = 32) -> np.ndarray:
    """Run the backbone over a list of image paths, return (N, D) embeddings.

    Loads/resizes with Pillow and predicts over plain in-memory numpy
    batches — simpler and more robust for a few thousand images than a
    tf.data file-reading pipeline, and avoids a tf.data/Keras `.predict()`
    iterator-exhaustion quirk observed with this TF/Keras version when
    feeding a one-shot `Dataset.from_tensor_slices` of file paths directly.
    """
    if backbone is None:
        backbone = load_backbone()

    all_embeddings = []
    for start in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[start : start + batch_size]
        batch = np.stack([_load_image_array(p) for p in batch_paths])
        all_embeddings.append(backbone.predict(batch, verbose=0))

    return np.concatenate(all_embeddings, axis=0) if all_embeddings else np.empty((0,))


def export_backbone_tflite(backbone, out_path: Path, quantize: bool = True) -> Path:
    """Export the shared backbone to a quantized .tflite file."""
    import tensorflow as tf

    converter = tf.lite.TFLiteConverter.from_keras_model(backbone)
    if quantize:
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(tflite_model)
    return out_path
