# Shadow stub — the installed `tensorflowjs` package unconditionally does
# `import tensorflow_decision_forests` (just to support loading TFDF-exported
# SavedModels, which this project never produces), but that real package's
# pinned `yggdrasil-decision-forests` proto gencode requires a protobuf
# runtime version incompatible with the `tensorflow` version this project
# needs. This empty stub (placed earlier on PYTHONPATH — see
# export_web_model.py) satisfies the import without pulling in the broken
# dependency chain; we never call anything from the real package.
