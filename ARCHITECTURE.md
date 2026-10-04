# LeafScout — Small AI for Development Hackathon (Agriculture Track)

Working name: **LeafScout**. One sentence: an offline-first phone app that looks at a
leaf — coffee, cassava, or bean, the crops this challenge's agriculture datasets cover —
names the disease in the farmer's own language, and tells her what to do next, without a
data connection, a server, or a general-purpose LLM.

Track: Annex B — Agriculture (World Bank × Hack-Nation Small AI Hackathon, Oct 2026).
All product copy, UI strings, and submission materials are in **English**, per the
competition requirement.

**Implementation status (2026-10-04):** the full pipeline below is built and verified
working end-to-end on-device (iOS Simulator) for all three crops — see
`model/README.md` and `app/README.md` for exact results, test commands, and known rough
edges, and `docs/screenshots/` for proof. Two pragmatic MVP substitutions vs. the original
plan, both swappable later without a redesign: (1) `react-native-image-picker` instead of
a live `react-native-vision-camera` frame processor — the Simulator has no camera at all,
and a static-photo flow is more reliable to ship in one weekend; (2) `@shopify/react-native-skia`
for on-device image decode/resize/pixel-read, feeding the same shared TFLite backbone +
per-crop SVM head described in §4. The Supabase sync layer (§7.2) is schema-ready
(`sync_status` column) but not yet wired up — every other part of the "offline core loop"
claim is real and tested, not aspirational.

**Change from the previous draft:** we now build strictly on the datasets the concept
note itself names in Annex B (§B.2) — **BRACOL** (coffee), **Cassava Leaf Disease**
(Makerere), and **iBean** (Makerere) — plus **PlantVillage** and **PlantDoc** as the
common cross-crop baseline/counterweight pair from §7.3. This also lines up the crop with
the Annex B scenario itself: *Noor's coffee yields have slipped*, so coffee/BRACOL is now
the **primary** demo crop, with cassava and bean as the other two event-suggested crops
the same architecture supports.

---

## 1. Problem framing (from Annex B)

> "Noor's coffee yields have dropped this season, and she cannot say why. The nearest
> extension officer visits the sub-county twice a year at best, and at harvest she sells
> her parchment to whichever middleman drives up the valley, at whatever price he names."

The binding constraint the brief names is **not the absence of an algorithm** — it's the
absence of a working farmer registry and of timely, localized advice. We scope LeafScout
to the piece an app can fix this weekend: turn a leaf photo into an immediate, localized,
actionable diagnosis, with a human-in-the-loop fallback when the model isn't sure, for
whichever of the three event-suggested crops the farmer grows.

**Hackathon challenge we answer:** "Design and demonstrate a Small AI solution that helps
Noor make, communicate or act on one better agricultural decision" — specifically
*identifying a crop problem* (disease ID) and *documenting a field observation*
(georeferenced log for the extension officer's next visit).

---

## 2. Why computer vision here, not a simpler tool

A spreadsheet or SMS can't look at a leaf. A keyword-based chatbot can't tell coffee leaf
rust from cercospora, or cassava mosaic from bacterial blight, from a photo. This is
squarely a computer-vision classification problem — exactly where the hackathon brief
says Small AI "can add value" (it cites the Wadhwani cotton pest tool as the model case:
on-device CV, pattern recognition over thousands of examples, runs offline on a basic
smartphone). A general-purpose LLM adds nothing here and would need the connectivity
LeafScout is designed to not need.

---

## 3. System architecture

```
┌─────────────────────────────── PHONE (offline-capable) ───────────────────────────────┐
│                                                                                          │
│  Crop selector (Coffee / Cassava / Bean — set once, changeable anytime)                 │
│        │                                                                                 │
│  Camera (react-native-vision-camera)                                                    │
│        │ frame / captured photo                                                         │
│        ▼                                                                                │
│  On-device inference pipeline                                                           │
│   1. ONE shared MobileNetV3-Small backbone (TFLite, quantized, ~1-2 MB total)            │
│      → 1280-d (or GAP-reduced) embedding — crop-agnostic feature extractor               │
│   2. Crop-specific linear SVM head (weights bundled as JSON, a few KB EACH)              │
│      coffee_head.json | cassava_head.json | bean_head.json — picked by crop selector     │
│      → class probabilities + confidence margin                                           │
│        │                                                                                 │
│        ▼                                                                                 │
│  Guardrail layer                                                                         │
│   - confidence < threshold  →  "Not sure — show to the extension officer"               │
│   - confidence ≥ threshold  →  diagnosis + cached local-language advisory text/audio     │
│        │                                                                                 │
│        ▼                                                                                 │
│  Local SQLite (observations, advisory_log, sync_queue)  ← store-and-forward              │
│        │                                                                                 │
│        │  (only when a signal is available)                                              │
│        ▼                                                                                 │
└────────┼─────────────────────────────────────────────────────────────────────────────── ┘
         ▼
   Supabase (Postgres + Storage)
   - mirrors observations for the cooperative / extension officer dashboard
   - aggregated, anonymized outbreak view, per crop, per village/season
   - model_registry: which backbone + which per-crop head is in the field, with 5-fold accuracy
```

Everything left of the dotted sync line works with **zero connectivity**. One shared
backbone + three small swappable heads means adding a fourth crop later costs a few KB and
a retrain of one head — not a new app or a re-shipped CNN. The right side (Supabase) is a
convenience layer for the extension officer and for model updates — never a dependency for
the core diagnosis flow.

---

## 4. Tech stack

| Layer | Choice | Why |
|---|---|---|
| App shell | **React Native** (not Capacitor/WebView) | Camera-frame ML inference needs native speed; a WebView adds a bridge/rendering tax we can't afford on a basic Android phone. |
| Camera + frame processing | `react-native-vision-camera` + frame processor plugin | Runs the TFLite call per-frame on the native thread (JSI), not through the JS bridge. |
| On-device inference | `react-native-fast-tflite` | JSI-based TFLite binding, no bridge serialization overhead — needed for sub-100ms feedback on a mid/low-end phone. |
| Local storage | SQLite (`expo-sqlite` / `op-sqlite`) | Offline-first; mirrors the `sync_queue` pattern described below. |
| Backend (sync only, optional) | **Supabase** (Postgres, Storage, Auth) | Thin REST/Realtime sync layer and the extension-officer dashboard. |
| Local-language audio | Pre-recorded cached clips per (crop, disease, action) | Reliable offline, no language-model dependency, cheap to produce for the hackathon weekend. |
| Model training | Python, TensorFlow/Keras → TFLite converter (dynamic-range quantization) | Standard, reproducible; one notebook per crop, shared backbone code. |
| SVM head training | scikit-learn, on frozen MobileNet embeddings, one head per crop | Keeps the on-device graph tiny and lets crops be added without re-shipping the CNN. |

### Why one shared MobileNet backbone + three SVM heads is viable

This is not one monolithic model — it's one cheap feature extractor plus three cheap
linear classifiers:

1. **MobileNetV2/V3-Small up to global-average-pooling**, exported once as a quantized
   TFLite model, trained/fine-tuned across all three crops' leaf images pooled together so
   the embedding generalizes across leaf textures. A 2026 mobile-disease-detection
   benchmark across 101 classes/33 crops found **MobileNetV3-Small reaching 94.54%
   accuracy at a 1.18 MB quantized model and ~3.9 ms inference on Android**, the best
   accuracy-per-KB trade-off tested (EfficientNetB0 topped accuracy at 95.25% but is
   larger/slower) ([arXiv:2508.10817](https://arxiv.org/pdf/2508.10817)).
2. **One linear SVM per crop**, each trained on that crop's embeddings only. Decision
   function is `w·x + b` per class — a tiny matrix multiply in plain app code, no extra ML
   runtime. This recipe is the same as "SVMobileNetV2," a MobileNetV2+SVM hybrid that
   reached **98.4% average accuracy with 5-fold cross-validation** on a 10,836-image
   PlantVillage subset ([MDPI AgriEngineering](https://mdpi-res.com/d_attachment/agriengineering/agriengineering-07-00341/article_deploy/agriengineering-07-00341.pdf)).
   Coffee-specific evidence for the same MobileNet-feature + classical-classifier pattern:
   a MobileNetV2-feature-extractor + Gaussian Naive Bayes pipeline on coffee leaves
   reached 93.89%, and a plain ML model trained on **BRACOL itself** reached 98.04%
   ([NORMA eResearch](https://norma.ncirl.ie/7230/)).

**5-fold CV is the right validation choice** given each crop's dataset is in the low
thousands of images — it reduces variance in the accuracy estimate versus a single
train/val split, and matches the methodology of the comparable published studies above.

---

## 5. Literature review — model selection, per crop

| Crop | Model | Reported accuracy | Context | Verdict |
|---|---|---|---|---|
| Any (general) | MobileNetV3-Small, quantized TFLite | **94.54%**, 1.18 MB, ~3.9 ms/inference | 101-class, 33-crop mobile benchmark | **Shared backbone choice** — best size/speed/accuracy trade-off ([arXiv:2508.10817](https://arxiv.org/pdf/2508.10817)) |
| Any (general) | EfficientNetB0 | 95.25% | Same benchmark | Close second, larger footprint — fallback if the phone fleet skews mid/high-end |
| Coffee (BRACOL) | MobileNetV3 (Small/Large) | **99%** across variants | Coffee leaf, 5-class (rust, miner, phoma, cercospora, healthy) | Strong direct evidence MobileNetV3 suits coffee specifically ([journal.unm.ac.id](https://journal.unm.ac.id/index.php/JESSI/article/download/11798/7289/40978)) |
| Coffee (BRACOL) | MobileNetV2 features + Gaussian Naive Bayes | 93.89% | Hybrid feature-extractor + classical classifier | Same architectural pattern as our MobileNet+SVM head — directly supports the approach |
| Coffee (BRACOL) | ML model trained on BRACOL | 98.04% | Coffee leaf | Upper reference point for our coffee head's 5-fold target |
| Coffee (JMuBEN, larger set) | EfficientNetB0 | 99.72% | 58,405-image coffee set, 5-class | Server-side "second opinion" candidate only — too heavy for the phone |
| Cassava (Makerere, 9,430 imgs) | MobileNet | 71.3% | 5-class: healthy, CMD, CBB, CGM, CBSD | **Honest baseline** — cassava is the hardest of the three crops; expect this, not 90%+, and say so in the submission |
| Cassava (Makerere) | MobileNetV2 | 65.6% | Same dataset | Confirms cassava's ceiling is lower with a lightweight backbone — motivates fine-tuning the shared backbone's last layers on cassava specifically, not relying on frozen features alone |
| Bean (3-class: rust/ALS/healthy) | Stacked ensemble EfficientNetB3+InceptionV3 | 99.22% | Bean leaf | Best published bean accuracy; too heavy for on-device — server-side only |
| Bean | Xception / ResNet50 / DenseNet201 / InceptionV3 | 96% / 95% / 94% / 88% | Bean leaf | Reference points; none beat MobileNetV3's mobile trade-off |

**Critical, submission-relevant caveat:** PlantVillage-trained models collapse on real
field photos — ResNet-50 drops from >99% to under 30% on PlantDoc field images; an
EfficientNet-B2 trained on controlled images drops from 99.6% to 66.8% on an external
field set ([arXiv:2511.18989](https://arxiv.org/pdf/2511.18989v1)). **PlantVillage is used
here only as a cross-crop pretraining/sanity-check corpus for the shared backbone, never
as the sole source for any crop's SVM head.** PlantDoc (2,598 real-world, cluttered-
background images across 13 species, including bean) is the counterweight: every head is
spot-checked against PlantDoc's matching species before being called "field-ready," and
whatever gap remains is reported, not hidden — this is scored under "Responsible AI"
(pass/fail) and "Data grounding" (15%).

---

## 6. Datasets — exactly the ones the concept note suggests (Annex B §B.2 + §7.3)

| Dataset | Crop | What it is | License | Role |
|---|---|---|---|---|
| **BRACOL** (Mendeley) | Coffee | 1,747 Arabica coffee leaf images, Brazil, smartphone-captured, 4 biotic stresses + healthy (leaf miner, leaf rust, brown leaf spot/phoma, cercospora) | CC BY 4.0 | **Primary training set for the coffee head** — matches the Annex B scenario crop directly |
| **Cassava Leaf Disease** (Makerere/NaCRRI) | Cassava | 9,430 labeled smartphone images: healthy + CMD, CBB, CGM, CBSD | Open (Makerere AI Lab) | **Primary training set for the cassava head** |
| **iBean** (Makerere/NaCRRI) | Bean | Healthy, bean rust, angular leaf spot | CC0 | **Primary training set for the bean head** — we already have this fused and deduplicated with two extra sources in `bean-disease-dataset/`, kept as a bonus-robustness enrichment, not a replacement |
| **PlantVillage** | Cross-crop | ~54,000 leaf images, controlled/studio background, many species | Open, widely mirrored | Cross-crop backbone pretraining only — **never used alone to validate a head** (see §5 caveat) |
| **PlantDoc** | Cross-crop, field | 2,598 real-field images, 13 species, 27 classes, cluttered backgrounds | Open (research use) | **Field-realism counterweight** — every head's reported accuracy is checked against the matching PlantDoc species/class where available |

**Supporting / "problem is real" evidence datasets** (from the concept note's common
tables, §7.3–7.4, cited once for the submission's problem statement, not for training):
- **FAOSTAT** — coffee/cassava/bean production and yield baselines, for the problem
  statement's numbers
- **WFP food prices** (via HDX) — staple price series, for the harvest-pricing gap in
  Noor's scenario (context only; out of scope for the weekend build itself)
- **CHIRPS** — rainfall, to contextualize disease-favorable conditions in the demo
  narrative (coffee leaf rust and cassava mosaic both correlate with humidity/rainfall
  patterns)
- **LSMS-ISA** (World Bank Microdata Library) — smallholder household panel, optional
  context for "is this problem real at scale"

**Open gap to disclose explicitly in the submission (scored under §7.2 "what your data
does not cover"):** none of the five core datasets include post-harvest defects, so
LeafScout only addresses pre-harvest crop disease identification, not the quality/grading
problem at sale. Cassava's lower baseline accuracy (65–71% with a lightweight backbone) is
also a known, disclosed limitation — not something we claim to have solved this weekend.

---

## 7. Data schema

### 7.1 Local (on-device SQLite — offline-first, store-and-forward)

```sql
CREATE TABLE crops (
  id    TEXT PRIMARY KEY,   -- 'coffee' | 'cassava' | 'bean'
  name_en TEXT NOT NULL
);

CREATE TABLE farmers (
  id              TEXT PRIMARY KEY,       -- local UUID
  phone_hash      TEXT,                   -- hashed, never raw phone number
  language_pref   TEXT NOT NULL,          -- e.g. 'sw', 'en', 'bn', 'pt'
  primary_crop_id TEXT REFERENCES crops(id),
  coop_id         TEXT,
  created_at      TEXT NOT NULL
);

CREATE TABLE disease_classes (
  id                  TEXT PRIMARY KEY,   -- 'coffee_rust', 'cassava_cmd', 'bean_rust', ...
  crop_id             TEXT NOT NULL REFERENCES crops(id),
  name_en             TEXT NOT NULL,
  name_local          TEXT,
  description_en      TEXT,
  recommended_action  TEXT,               -- short actionable text, localized
  audio_clip_asset    TEXT                -- bundled audio file reference
);

CREATE TABLE observations (
  id                  TEXT PRIMARY KEY,
  farmer_id           TEXT REFERENCES farmers(id),
  crop_id              TEXT NOT NULL REFERENCES crops(id),
  photo_path          TEXT NOT NULL,      -- local file path
  captured_at         TEXT NOT NULL,
  gps_lat             REAL,               -- nullable: GPS may be off/unavailable
  gps_lon             REAL,
  model_version        TEXT NOT NULL,     -- FK to model_registry.version
  predicted_class      TEXT REFERENCES disease_classes(id),
  confidence            REAL NOT NULL,
  top3_json             TEXT,             -- [{class, score}, ...] for transparency
  below_threshold       INTEGER NOT NULL, -- 1 = routed to "ask a person"
  human_confirmed_class TEXT,             -- filled in later by extension officer, nullable
  sync_status            TEXT NOT NULL DEFAULT 'pending' -- pending | synced | failed
);

CREATE TABLE advisory_log (
  id              TEXT PRIMARY KEY,
  observation_id  TEXT REFERENCES observations(id),
  delivered_via   TEXT NOT NULL,          -- 'text' | 'audio'
  language        TEXT NOT NULL,
  created_at      TEXT NOT NULL
);

CREATE TABLE model_registry (
  version                TEXT PRIMARY KEY,
  backbone               TEXT NOT NULL,   -- 'mobilenet_v3_small' (shared across crops)
  crop_id                TEXT NOT NULL REFERENCES crops(id),  -- which head this row describes
  head_type               TEXT NOT NULL,  -- 'svm' | 'softmax'
  tflite_asset_hash       TEXT NOT NULL,  -- shared backbone file hash (same across crop rows)
  head_weights_asset_hash TEXT,           -- this crop's head file hash
  trained_on_dataset      TEXT NOT NULL,  -- 'BRACOL' | 'cassava_makerere' | 'ibean(+fusion)'
  accuracy_5fold_mean      REAL,
  accuracy_5fold_by_source_json TEXT,     -- per-source breakdown, see §5 caveat
  plantdoc_spotcheck_accuracy REAL,       -- field-realism counterweight result, nullable
  created_at               TEXT NOT NULL
);

CREATE TABLE sync_queue (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  table_name    TEXT NOT NULL,
  row_id        TEXT NOT NULL,
  operation     TEXT NOT NULL,            -- 'insert' | 'update'
  payload_json  TEXT NOT NULL,
  attempts      INTEGER NOT NULL DEFAULT 0,
  last_attempt_at TEXT,
  status        TEXT NOT NULL DEFAULT 'pending'
);
```

### 7.2 Supabase (sync mirror + extension-officer / cooperative view)

Same `observations` / `farmers` / `disease_classes` / `model_registry` / `crops` shape,
plus:

```sql
CREATE TABLE outbreak_aggregates (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  coop_id       TEXT NOT NULL,
  crop_id       TEXT NOT NULL,
  disease_id    TEXT NOT NULL,
  week_start    DATE NOT NULL,
  observation_count INTEGER NOT NULL,
  avg_confidence     REAL,
  UNIQUE (coop_id, crop_id, disease_id, week_start)
);
```

Populated by a scheduled job (Supabase Edge Function) rolling up synced observations —
the "connecting evidence to an extension-service next step" piece of the challenge: the
cooperative/extension officer sees a disease trending in a village, per crop, *before*
their next scheduled visit.

Photos sync to Supabase Storage only on explicit farmer consent and Wi-Fi/good-signal
condition (never force a large upload over a 3G bundle) — stated plainly in the app's
data-use notice, per the brief's instruction to say "where the data sits, who can read it,
what happens when the phone is lost or shared."

---

## 8. Feature list

**MVP (built and demoed over the hackathon weekend):**
1. Crop selector (Coffee / Cassava / Bean) — picks which SVM head runs
2. Capture/select a leaf photo → on-device classification in under 1 second
3. Confidence-gated result: diagnosis + localized action text/audio, or "not sure — show
   this to your extension officer" when below threshold (human-in-the-loop guardrail)
4. Local-language audio playback of the recommended action (pre-recorded clips, per crop)
5. Offline observation log, georeferenced when GPS is available, queued for sync
6. Background sync to Supabase whenever connectivity appears (store-and-forward)
7. Minimal cooperative/extension-officer web view: recent observations per village **and
   per crop**, flagged low-confidence cases needing a human look

**Stretch goals (explicitly scoped out of the weekend build, named as "what happens
next" in the submission):**
- A fourth/fifth crop added by training one more SVM head on the shared backbone
- Outbreak heatmap (`outbreak_aggregates`) surfaced to extension officers
- Live on-device TTS/STT for languages without pre-recorded clips
- WFP price-reference cache for the harvest-pricing gap in the same persona scenario
- Model update over-the-air via `model_registry`, side-loadable over a weak connection

---

## 9. Judging-criteria alignment (self-check against §9 of the concept note)

- **Built solution fidelity (25%):** on-device, offline core loop; one shared backbone +
  three small heads, side-loadable (~1-2 MB total)
- **Development relevance (20%):** answers B.1's named problem directly, on the crop
  (coffee) the scenario itself names, plus the two other event-suggested crops
- **Data grounding (15%):** uses exactly the datasets the concept note names for this
  sector (BRACOL, Cassava Leaf Disease, iBean, PlantVillage, PlantDoc); explicit per-crop,
  per-source accuracy reporting; explicit disclosure of cassava's lower ceiling and the
  post-harvest-defect gap
- **Evidence it works (15%):** 5-fold CV accuracy per crop, cross-checked against PlantDoc
  field images, not just pooled studio-image numbers
- **Clarity / value proposition for AI (15%):** CV is the only viable tool for "what
  disease is this from a photo" — stated explicitly, with the Wadhwani precedent cited
- **Scalability (10%):** shared backbone + swappable per-crop heads — adding a 4th crop is
  a retrain, not a rebuild
- **Responsible AI (pass/fail):** confidence threshold + human routing, local-language
  requirement met, explicit data-gap disclosure (cassava accuracy, post-harvest scope), no
  raw phone numbers stored

---

## Sources

- [SVMobileNetV2 / MobileNetV2 + SVM, 5-fold CV, PlantVillage](https://mdpi-res.com/d_attachment/agriengineering/agriengineering-07-00341/article_deploy/agriengineering-07-00341.pdf)
- [Mobile-Friendly Deep Learning for Plant Disease Detection: Lightweight CNN Benchmark, 101 classes/33 crops](https://arxiv.org/pdf/2508.10817)
- [BRACOL dataset description, Mendeley](https://data.mendeley.com/datasets/yy2k5y8mxg/1)
- [Coffee leaf disease classification with MobileNetV3, ~99% accuracy](https://journal.unm.ac.id/index.php/JESSI/article/download/11798/7289/40978)
- [MobileNetV2 features + classical ML classifiers on coffee leaves (incl. BRACOL, 98.04%)](https://norma.ncirl.ie/7230/)
- [Cassava Leaf Disease Detection Using Convolutional Neural Networks (Makerere dataset, MobileNet/MobileNetV2 accuracy)](https://researchgate.net/profile/Elliana-Gautama/publication/352580072_Cassava_Leaf_Disease_Detection_Using_Convolutional_Neural_Networks/links/63c948e6d9fb5967c2ecacf4/Cassava-Leaf-Disease-Detection-Using-Convolutional-Neural-Networks.pdf)
- [PlantDoc: A Dataset for Visual Plant Disease Detection](https://arxiv.org/pdf/1911.10317)
- [Stacked CNN ensemble for bean leaf disease detection (EfficientNetB3 + InceptionV3, 99.22%)](https://psau.sa.elsevierpure.com/en/publications/enhanced-detection-of-bean-leaf-diseases-using-a-stacked-cnn-ense/)
- [PlantVillage-to-field generalization gap, accuracy drop study](https://arxiv.org/html/2511.18989v1)
- Wadhwani AI cotton pest tool — cited directly from the hackathon concept note (Annex B), link not independently verified here
