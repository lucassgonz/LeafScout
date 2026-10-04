# LeafScout — mobile app

React Native app implementing ARCHITECTURE.md's on-device pipeline: pick a
leaf photo → Skia decode/resize → shared MobileNetV3-Small TFLite backbone →
crop-specific linear SVM head (JS port, `src/ml/svmHead.ts`) → confidence-
gated result → saved to local SQLite (offline-first, sync-ready schema).

## Status as of 2026-10-04

**Verified working end-to-end on iOS Simulator (iPhone 17 Pro, iOS 26.5)** —
all three crops (coffee/cassava/bean) correctly load their model head and
produce a classification from a real photo, confidence gating and local
persistence both confirmed. Screenshots in `../docs/screenshots/`.

I could not interact with the Simulator UI directly overnight — the
Claude Code iOS Simulator panel needs a one-time permission grant from you
("Let Claude use it" in the simulator panel), which only you can approve.
I verified everything via the "Try a sample photo instead" button
(classifies a real bundled training-set photo per crop — see
`src/data/samplePhotos.ts`) triggered through a **temporary** auto-run
effect, confirmed via `xcrun simctl io screenshot` (not the gated panel),
then removed that temporary code — the app's actual shipped behavior is the
manual button, nothing auto-runs.

**Not yet done** — real camera capture is untested (Simulator has no
camera; `react-native-image-picker`'s `launchImageLibrary` is wired and
should work on a real device or via the Simulator's seeded Photos library,
but I haven't exercised that path). Try "Pick a leaf photo" on your end
before recording — if anything's off, it's most likely a Photos-library
permission prompt needing a tap.

## Running it

```bash
npm install
cd ios && LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 pod install && cd ..
npx react-native start          # Metro, separate terminal
npx react-native run-ios --simulator "iPhone 17 Pro"
```

Android isn't set up (no Android Studio/SDK on this machine) — the code has
no iOS-only dependencies I'm aware of, but it's untested there.

## Project layout

- `src/ml/model.ts` — loads the shared TFLite backbone once at startup
  (`preloadModel`), runs a photo through it + the selected crop's SVM head
- `src/ml/svmHead.ts` — JS port of `model/leafscout_ml/svm_head.py`'s
  `predict_with_weights`; **must stay numerically identical to the Python
  reference** (both have their own test suite exercising the same math)
- `src/ml/imagePreprocess.ts` — Skia-based decode/resize/pixel-read (224×224
  RGB, no manual normalization — the TFLite model has Keras's own
  preprocessing layer baked in, see `model/leafscout_ml/embeddings.py`)
- `src/db/db.ts` — SQLite `observations` table, offline-first (every save
  works with zero connectivity; `sync_status` column is there for a future
  Supabase sync job, not wired up yet — see root ARCHITECTURE.md §7.2)
- `src/data/diseaseClasses.ts` — per-crop, per-class display copy (English)
  and the `CONFIDENCE_THRESHOLD` guardrail constant
- `src/data/samplePhotos.ts` — bundled demo photos (see Status above)
- `assets/model/` — the trained artifacts, copied from `../model/artifacts/`
  after each `run_pipeline.py` run (not symlinked — if you retrain, re-copy)

## Tests

```bash
npx jest        # 9 tests: svmHead JS<->Python parity + an App smoke test
npx tsc --noEmit
```

Native modules (`react-native-fast-tflite`, `react-native-sqlite-storage`,
`@shopify/react-native-skia`) are hand-mocked in `__mocks__/` — Jest runs in
plain Node, which has no native module registry, so these would otherwise
fail to even import. The SQLite mock keeps a real in-memory array so
insert/list/count logic is still meaningfully exercised, not just stubbed.

## Known rough edges

- `Podfile` has a `post_install` hook forcing every pod's
  `IPHONEOS_DEPLOYMENT_TARGET` up to 15.0 — `TensorFlowLiteC` and
  `react-native-image-picker`'s privacy-manifest pod both shipped targets
  (12.0, 9.0) below what current Xcode's Simulator SDK supports (15.0+);
  without this the build fails with error code 65.
- `metro.config.js` adds `tflite` to `assetExts` so `require('*.tflite')`
  resolves to a loadable asset module.
- Coffee's SVM head depends on the BRACOL archive-recovery workaround — see
  `../model/README.md` "Known issues" #1 before retraining it.
