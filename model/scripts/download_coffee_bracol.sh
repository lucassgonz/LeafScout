#!/usr/bin/env bash
# BRACOL (Brazilian Arabica Coffee Leaf) — Mendeley, CC BY 4.0, no login required.
# https://data.mendeley.com/datasets/yy2k5y8mxg/1
set -euo pipefail
cd "$(dirname "$0")/.."  # -> model/

OUT="raw/coffee/bracol"
mkdir -p "$OUT"

echo "Downloading BRACOL from Mendeley..."
echo "NOTE: Mendeley datasets are served from a versioned, content-hashed URL that"
echo "changes per release. Open https://data.mendeley.com/datasets/yy2k5y8mxg/1 ,"
echo "click 'Download All' to get the zip, then run:"
echo
echo "  unzip <downloaded>.zip -d raw/coffee/bracol"
echo
echo "Expected resulting structure (rename folders to match if the archive differs):"
echo "  raw/coffee/bracol/healthy/*.jpg"
echo "  raw/coffee/bracol/rust/*.jpg"
echo "  raw/coffee/bracol/miner/*.jpg"
echo "  raw/coffee/bracol/phoma/*.jpg"
echo "  raw/coffee/bracol/cercospora/*.jpg"
echo
echo "(BRACOL's own folder/label names vary by release — check leafscout_ml/config.py's"
echo " CROPS['coffee'].class_map and adjust the substrings there if needed, rather than"
echo " renaming hundreds of files by hand.)"
