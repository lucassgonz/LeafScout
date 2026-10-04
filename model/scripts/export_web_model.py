#!/usr/bin/env python3
"""Export the shared MobileNetV3-Small backbone to TensorFlow.js format, for
the browser-based version of LeafScout (web/app.html) — the same model the
phone app runs (model/artifacts/backbone_mobilenet_v3_small.tflite), just in
a format a browser can load. Keras's `include_preprocessing=True` means this
graph still expects raw 0-255 float RGB input, same as the mobile app's
TFLite model (see leafscout_ml/embeddings.py) — the JS preprocessing code in
web/app.html must NOT re-normalize.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from leafscout_ml.embeddings import load_backbone  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SAVEDMODEL_DIR = ROOT / "artifacts" / "_backbone_savedmodel"
WEB_OUT_DIR = ROOT.parent / "web" / "assets" / "model" / "backbone"
STUBS_DIR = Path(__file__).resolve().parent / "_stubs"


def main() -> None:
    print("Loading Keras MobileNetV3Small backbone...")
    backbone = load_backbone()

    if SAVEDMODEL_DIR.exists():
        shutil.rmtree(SAVEDMODEL_DIR)
    backbone.export(str(SAVEDMODEL_DIR))
    print(f"Saved Keras SavedModel to {SAVEDMODEL_DIR}")

    WEB_OUT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "tensorflowjs.converters.converter",
        "--input_format=tf_saved_model",
        "--output_format=tfjs_graph_model",
        "--signature_name=serving_default",
        "--saved_model_tags=serve",
        str(SAVEDMODEL_DIR),
        str(WEB_OUT_DIR),
    ]
    print("Converting to TF.js graph model:", " ".join(cmd))
    env = {**os.environ, "PYTHONPATH": f"{STUBS_DIR}:{os.environ.get('PYTHONPATH', '')}"}
    subprocess.run(cmd, check=True, env=env)

    shutil.rmtree(SAVEDMODEL_DIR)
    print(f"\nDone. TF.js model files written to {WEB_OUT_DIR}")


if __name__ == "__main__":
    main()
