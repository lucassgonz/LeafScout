#!/usr/bin/env bash
# Cassava Leaf Disease (Makerere AI Lab / NaCRRI) via Kaggle.
# Requires ~/.kaggle/kaggle.json (kaggle.com/settings -> Create New API Token).
set -euo pipefail
cd "$(dirname "$0")/.."  # -> model/

if [ ! -f "$HOME/.kaggle/kaggle.json" ]; then
  echo "Missing ~/.kaggle/kaggle.json — create an API token at kaggle.com/settings," >&2
  echo "download it, then: mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json" >&2
  exit 1
fi

OUT="raw/cassava/cassava"
mkdir -p "$OUT"

# The 2020/2021 Kaggle "Cassava Leaf Disease Classification" competition dataset
# (Makerere AI Lab + NaCRRI). Competition datasets require you to have accepted
# the competition rules on kaggle.com first (one click, no cost).
./.venv/bin/kaggle competitions download -c cassava-leaf-disease-classification -p "$OUT/_download"
cd "$OUT/_download" && unzip -q -o '*.zip' && cd -

echo "Downloaded to $OUT/_download. This competition ships train_images/ + a"
echo "train.csv label file (integer class ids), NOT one-folder-per-class."
echo "Run scripts/reorganize_cassava.py next to turn it into the"
echo "raw/cassava/cassava/<class_name>/*.jpg layout build_manifest.py expects."
