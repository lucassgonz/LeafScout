#!/usr/bin/env bash
# iBean (Makerere/NaCRRI), CC0, via Kaggle mirror.
# Requires ~/.kaggle/kaggle.json (kaggle.com/settings -> Create New API Token).
set -euo pipefail
cd "$(dirname "$0")/.."  # -> model/

if [ ! -f "$HOME/.kaggle/kaggle.json" ]; then
  echo "Missing ~/.kaggle/kaggle.json — create an API token at kaggle.com/settings," >&2
  echo "download it, then: mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json" >&2
  exit 1
fi

OUT="raw/bean/ibean"
mkdir -p "$OUT"

# Dataset named in ARCHITECTURE.md / the earlier bean-disease-dataset README:
# https://www.kaggle.com/datasets/therealoise/bean-disease-dataset
./.venv/bin/kaggle datasets download -d therealoise/bean-disease-dataset -p "$OUT/_download"
cd "$OUT/_download" && unzip -q -o '*.zip' && cd -

echo "Downloaded. This Kaggle mirror already ships one-folder-per-class"
echo "(train/validation/test splits with healthy/angular_leaf_spot/bean_rust"
echo "subfolders). Flatten it into raw/bean/ibean/<class>/*.jpg with:"
echo
echo "  python scripts/flatten_ibean.py"
