# LeafScout — ML pipeline

Trains the shared MobileNetV3-Small backbone + one linear SVM head per crop
(coffee/cassava/bean), per ARCHITECTURE.md §4-§5. Code lives in
`leafscout_ml/` (tested, importable package); `scripts/` are thin CLI
wrappers over it.

## Setup

```bash
python3.11 -m venv .venv          # TensorFlow needs <=3.13; see root README
./.venv/bin/pip install -r requirements.txt
```

## Datasets

Already downloaded and organized under `raw/<crop>/<source>/<class>/*.jpg`
for all three crops (coffee/BRACOL, cassava/Makerere, bean/iBean) — see
`leafscout_ml/config.py` for the exact class-folder-name mapping each source
expects. To reproduce from scratch:

```bash
./scripts/download_coffee_bracol.sh      # Mendeley, see "Known issues" below
./scripts/recover_bracol_zip.py "<downloaded inner zip>" raw/coffee/_download/recovered
./scripts/reorganize_bracol.py

./scripts/download_cassava_kaggle.sh     # or the dataset mirror used tonight — see below
./scripts/reorganize_cassava.py          # only if you used the competition CSV route

./scripts/download_bean_ibean_kaggle.sh
./scripts/flatten_ibean.py
```

`.env` (gitignored) holds `KAGGLE_API_TOKEN` — `kaggle` CLI 2.x's newer
token-only auth, no `KAGGLE_USERNAME` needed. `source .env` before any
`kaggle` command, or `export $(cat .env)`.

## Running the pipeline

```bash
./.venv/bin/python scripts/run_pipeline.py coffee   # or cassava / bean / all
```

For each crop: builds the manifest, deduplicates (exact MD5 + near-dup
pHash, cluster-safe), splits 70/15/15, extracts MobileNetV3Small embeddings,
trains a `class_weight='balanced'` linear SVM, runs 5-fold CV, evaluates on
the held-out test split (overall + per-source), and writes:
- `artifacts/backbone_mobilenet_v3_small.tflite` — shared across all crops
- `artifacts/<crop>_head.json` — that crop's SVM weights
- `artifacts/model_registry.json` — one row per crop with every metric above

## Results (this run, see artifacts/model_registry.json for the full detail)

| Crop | Train images | 5-fold CV acc. | Balanced acc. | Held-out test acc. |
|---|---|---|---|---|
| Coffee (BRACOL) | 940 | 81.7% ± 2.0% | 76.8% | 79.9% |
| Cassava (Makerere) | 14,977 | 72.0% ± 0.9% | 56.8% | 72.4% |
| Bean (iBean) | 693 | 91.3% ± 1.6% | 91.3% | 91.2% |

Cassava's gap between plain accuracy (72%) and balanced accuracy (57%) is
real, not a bug — the raw data is ~12x class-imbalanced (mosaic disease
dominates); `class_weight='balanced'` already mitigates it, this is the
honest remaining number. This matches the literature baseline cited in
ARCHITECTURE.md §5 (65-71% with a lightweight backbone) — report it as a
disclosed limitation in the submission, not a bug to hide.

## Tests

```bash
./.venv/bin/python -m pytest tests/ -v
```

34 tests, no TensorFlow/network/dataset dependency — pure manifest/dedup/
split/SVM-head/metrics logic on synthetic fixtures (including a reproducible
noise-textured-image fixture for pHash tests — flat-color test images give
pHash no texture to hash on and falsely collapse to near-identical hashes,
a real trap worth knowing about if you extend these tests).

## Known issues / decisions made overnight (2026-10-03→04)

1. **BRACOL's Mendeley-hosted zip has no valid End-Of-Central-Directory
   record.** `unzip` and `zip -FF` both fail on it (the latter hangs for
   several CPU-minutes without ever completing, likely performing a
   byte-by-byte rescan). The actual corruption is upstream at Mendeley — the
   outer wrapper zip's own CRC passes, so nothing was corrupted in transit.
   `scripts/recover_bracol_zip.py` recovers it with a manual linear scan for
   `PK\x03\x04` local-file-header signatures (DEFLATE-compressed entries,
   sizes read straight from each local header, no central directory needed).
   Recovered 1402 of 1747 leaf images (80%) before hitting the truncation
   point; reorganize_bracol.py further excludes the ~62 "mixed/no single
   predominant stress" labeled images, landing at 1342 trainable images.
   **If you re-run this today, try the plain Mendeley download first** — if
   they've since fixed the archive, you won't need the recovery script at
   all; diff the file count against 1747 to check.
2. **Cassava dataset came from a pre-sorted Kaggle mirror**
   (`nirmalsankalana/cassava-leaf-disease-classification`), not the official
   competition download, because the competition's API download requires
   accepting its competition rules on kaggle.com first — a one-click consent
   action on your account, not something to do on your behalf without you
   present. The mirror has the same underlying Makerere/NaCRRI images
   (matching filenames), already sorted into class folders, 21,397 images
   (more than the original competition's 9,430 — looks like it folds in
   multiple competition years/splits). `CGM`/"green mite" is called "Green
   Mottle" in this mirror's folder names — both names refer to the same
   disease; config.py accepts either substring.
3. **TensorFlow doesn't support Python 3.14** (this machine's default
   `python3`) — installed `python@3.11` via Homebrew specifically for
   `model/.venv`, isolated from your system Python.
4. **`tensorflow-metal` (Apple GPU acceleration) is incompatible with the
   TensorFlow version pip installed tonight** (dlopen failure on import) —
   uninstalled it; everything ran on CPU, which was fast enough at this
   dataset scale (biggest extraction, cassava's 21k images, finished in
   single-digit minutes).
