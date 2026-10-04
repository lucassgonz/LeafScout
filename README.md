# 🌿 LeafScout

**Offline-first crop disease diagnosis for coffee, cassava, and bean.** Built for the
World Bank × Hack-Nation **Small AI for Development Hackathon** (Agriculture track,
Annex B).

> Because of LeafScout, a smallholder farmer will know in under a second, right in her
> field, whether her crop has a disease. Today she only finds out when the extension
> officer visits, which happens at most twice a year. And when she sells her harvest, she
> finally has an independent price to check it against, instead of taking whatever the
> middleman offers.

A photo of a leaf goes in. A MobileNetV3-Small backbone shared across all three crops,
with a linear SVM head trained for each one, runs **entirely on-device** (no server call,
no data plan needed) and returns a diagnosis, a confidence score, and a current market
price for that crop. The observation is saved locally and synced to a cooperative
dashboard whenever a connection shows up.

| | |
|---|---|
| 📱 **Mobile app** | React Native, on-device TFLite inference (iOS verified, Android APK buildable) — [`app/`](app/) |
| 🧠 **ML pipeline** | Dataset fusion, training, 5-fold cross validation, fully tested — [`model/`](model/) |
| 🌐 **Web app (same AI, in-browser)** | [`web/app.html`](web/app.html): pick a crop, diagnose a leaf, entirely client-side via TensorFlow.js |
| 💰 **Market price reference** | Real WFP price data per crop, so a diagnosis isn't the only thing a farmer walks away with |
| 📊 **Cooperative dashboard** | [`web/index.html`](web/index.html) — extension-officer view, deployable to Vercel |
| 🗄️ **Backend** | Supabase (Postgres + RLS), schema in [`supabase/schema.sql`](supabase/schema.sql) |
| 📐 **Full design doc** | [`ARCHITECTURE.md`](ARCHITECTURE.md) |

**If you're judging this from the web** (`web/` deployed to Vercel): `app.html` is not a
simplified demo — it loads the same MobileNetV3 backbone (converted to TensorFlow.js) and
the same per-crop SVM heads the mobile app ships, and runs the identical math client-side.
The mobile app itself is a separate, fully-built React Native project — see
"Mobile app" below for what's verified there and how to run it.

---

## Results

Trained on the exact datasets the hackathon's Annex B names for this sector — not a
generic plant-disease dataset. One shared MobileNetV3-Small backbone (quantized,
~1.1 MB), one linear SVM head per crop (tens of KB each), 5-fold cross-validated.

| Crop | Dataset | Classes | Train images | 5-fold CV accuracy | Balanced accuracy | Held-out test |
|---|---|---|---|---|---|---|
| ☕ Coffee | [BRACOL](https://data.mendeley.com/datasets/yy2k5y8mxg/1) (Mendeley) | healthy, rust, leaf miner, phoma, cercospora | 940 | **81.7% ± 2.0%** | 76.8% | 79.9% |
| 🌾 Cassava | Makerere/NaCRRI (Kaggle) | healthy, mosaic, brown streak, bacterial blight, green mottle | 14,977 | **72.0% ± 0.9%** | 56.8% | 72.4% |
| 🫘 Bean | iBean, Makerere/NaCRRI (Kaggle) | healthy, rust, angular leaf spot | 693 | **91.3% ± 1.6%** | 91.3% | 91.2% |

Full per-run detail (per-fold accuracy, per-source breakdown, artifact hashes) is in
[`model/artifacts/model_registry.json`](model/artifacts/model_registry.json) and mirrored
live in Supabase's `model_registry` table — the web dashboard reads it directly.

**Cassava's lower, disclosed ceiling:** its raw data is ~12x class-imbalanced (mosaic
disease dominates); `class_weight="balanced"` already mitigates it, and 72%/57% is the
honest number that remains — in line with the published literature baseline for a
lightweight on-device model on this dataset (65–71%, see
[`ARCHITECTURE.md` §5](ARCHITECTURE.md#5-literature-review--model-selection-for-the-on-device-classifier)).
We report it rather than hide it — "what the data does not cover" is a scored item in
this challenge.

---

## What's actually built (not just planned)

Verified end-to-end — screenshots in [`docs/screenshots/`](docs/screenshots/), real data
round-tripped through the live Supabase project, 60+ automated tests:

- **On-device inference**: photo → Skia decode/resize → shared TFLite backbone → crop's
  SVM head (JS port, numerically tested against the Python training code) → confidence-
  gated result. Verified on iOS Simulator for all three crops.
- **Offline-first storage**: every observation saves locally (SQLite) with zero
  connectivity, before anything else happens.
- **Real Supabase sync**: schema applied to the live project, RLS enabled with real
  policies, the app pushes each saved observation opportunistically. Confirmed by
  classifying a photo on-device and querying the live table directly.
- **GPS tagging**: best-effort location capture per observation (optional, never blocks
  diagnosis) — `@react-native-community/geolocation`.
- **Voice output**: on-device text-to-speech reads the recommended action aloud
  (`react-native-tts`) — the "at least one interaction by voice" requirement, with every
  native call defensively guarded (TTS routinely rejects for mundane reasons — missing
  voice data, nothing currently speaking — and must never crash the app).
- **Web app, same AI** (`web/app.html`): the shared MobileNetV3 backbone, converted to
  TensorFlow.js (`model/scripts/export_web_model.py`), plus the same three SVM heads,
  running entirely in-browser — WebGL-accelerated (~1.5s/photo), CPU fallback if WebGL
  isn't available. Verified for all three crops; each diagnosis also syncs to the same
  Supabase `observations` table the mobile app writes to. The photo never leaves the
  browser.
- **Cooperative dashboard** (`web/index.html`): reads the same live Supabase tables —
  recent observations, flagged low-confidence cases, per-crop filtering, and the model
  registry table — zero build step, deployable to Vercel as-is.
- **Guardrails**: below a confidence threshold, the app shows "not sure — ask a person"
  instead of a diagnosis. A person always makes the final call; nothing is automated.
- **Android debug APK**: builds successfully (`cd app/android && ./gradlew assembleDebug`)
  after patching two legacy dependencies off the long-dead `jcenter()` repository (patches
  in `app/patches/`, applied automatically via `postinstall`). Not yet installed/run on a
  device or emulator, only the iOS build has been interactively verified end to end.
- **Market price reference**: the direct answer to the problem the concept note names for
  Noor ("she sells her parchment to whichever middleman drives up the valley, at whatever
  price he names"). Shows the latest retail price and a six month trend for the farmer's
  crop, built from real WFP food price data pulled from HDX, not placeholder numbers.
  Coffee is referenced from Ethiopia (WFP does not track it as a food-security commodity
  in most countries, so Ethiopia, a major producer where it is tracked, is used); bean and
  cassava from Uganda, matching this project's training data. It is a monthly snapshot,
  not a live feed, regenerated with `model/scripts/build_price_reference.py`. Present on
  both the mobile app and the web app.

See [`STATUS.md`](STATUS.md) for the full build log, including real bugs found and fixed
along the way (a corrupt upstream Mendeley archive, recovered with a custom parser; a
non-obvious Postgres RLS behavior where `ON CONFLICT` upserts silently require a SELECT
policy; and two Android libraries whose Gradle config hadn't been touched since `jcenter()`
shut down).

---

## Repository layout

```
LeafScout/
├── app/                      React Native mobile app (iOS verified, Android APK builds)
├── model/                    Python ML pipeline: dataset fusion, training, 34 tests
├── web/                      app.html (diagnose) + index.html (dashboard) — deploy to Vercel
├── supabase/                 Database schema (applied to the live project)
├── docs/                     Screenshots and other supporting material
├── ARCHITECTURE.md           Full system design
```

## Running it

**Mobile app** (iOS, needs Xcode + CocoaPods):
```bash
cd app
npm install
cd ios && pod install && cd ..
npx react-native start        # separate terminal
npx react-native run-ios --simulator "iPhone 17 Pro"
```
Details, known build quirks, and test commands: [`app/README.md`](app/README.md).

**Android** (needs the Android SDK + NDK; no emulator/device testing done here, build
only):
```bash
cd app/android
echo "sdk.dir=$ANDROID_HOME" > local.properties   # point at your SDK install
./gradlew assembleDebug
# APK at app/android/app/build/outputs/apk/debug/app-debug.apk
```

**ML pipeline** (Python 3.11, TensorFlow):
```bash
cd model
python3.11 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m pytest tests/ -v       # 34 tests, no dataset/network needed
./.venv/bin/python scripts/run_pipeline.py all
```
Details: [`model/README.md`](model/README.md).

**Web** (diagnosis app + dashboard) — no build step, open directly or serve statically:
```bash
cd web
python3 -m http.server 8080   # or any static file server
# http://localhost:8080/app.html   — diagnose a leaf
# http://localhost:8080/index.html — cooperative dashboard
```
Regenerating `web/assets/model/backbone/` after retraining: `cd model && ./.venv/bin/python scripts/export_web_model.py`.


## Tech stack

React Native · TensorFlow / TensorFlow Lite / TensorFlow.js · scikit-learn (linear SVM
heads) · `react-native-fast-tflite` · `@shopify/react-native-skia` ·
`@react-native-community/geolocation` · `react-native-tts` · Supabase (Postgres + RLS) ·
vanilla JS + `@supabase/supabase-js` + `@tensorflow/tfjs` for the web app · Python 3.11 +
pytest + Jest for testing.

## License

Built for the Small AI for Development Hackathon (Oct 2026). Dataset licenses: BRACOL
(CC BY 4.0), Makerere/NaCRRI cassava and iBean datasets (see their respective Kaggle
listings).
