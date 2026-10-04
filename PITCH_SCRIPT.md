# LeafScout — Video Pitch Script (target: 3:30–4:00, cap 5:00)

Format suggestion: screen-recording of the working prototype over a voiceover, cut to a
few slides for the architecture/stats beats. One speaker is enough; split lines between
two teammates if you want visual variety for the judges. Demo crop: **coffee** (it's the
crop in the Annex B scenario itself); mention cassava and bean as the other two
event-suggested crops the same model supports.

---

## 0:00–0:20 — Problem statement

> "Because of LeafScout, a smallholder coffee farmer like Noor will know, in under a
> second and right there on her slope, whether her crop has leaf rust, cercospora, or
> leaf miner — something she would otherwise only find out when the extension officer
> visits, which in her district happens at most twice a year. We know because that
> twice-a-year visit cadence, and the yield drop it causes, is the exact gap the World
> Bank's own agriculture brief names for Noor's coffee harvest this season."

*(On screen: one line of text matching the spoken sentence, then cut to the app.)*

---

## 0:20–1:45 — AI capabilities, why not a simpler tool, guardrails

> "This is a computer vision problem — you can't diagnose a leaf disease from a photo
> with a spreadsheet, a keyword search, or a plain SMS menu. So LeafScout runs one
> shared MobileNetV3 image classifier, quantized down to about one megabyte, directly
> on the phone — plus a linear SVM head trained per crop on top of it. The same
> backbone serves coffee, cassava, and bean; only the small head file changes, so the
> farmer just picks her crop once. No server call, no data plan required for the core
> feature.
>
> We deliberately didn't reach for a general-purpose LLM. An LLM can't look at a leaf,
> and it would need the connectivity we're specifically designing around not needing.
>
> We also built in two guardrails. First, confidence gating: if the model isn't
> confident enough, LeafScout doesn't guess — it tells the farmer to show the leaf to
> the extension officer instead. A confident wrong answer about someone's only harvest
> is worse than no answer. We're especially strict about this for cassava, where the
> published accuracy with a lightweight model is lower than for coffee or bean, and we
> say so rather than hide it. Second, every diagnosis is logged and explainable, never
> acted on automatically — a person always makes the final call."

*(On screen: the crop selector, then the confidence-threshold screen, the "not sure —
ask a person" state.)*

---

## 1:45–3:15 — Tool demo (end-to-end user journey)

> "Here's Noor's actual flow. She opens LeafScout, selects 'Coffee' once — no login, no
> account creation. She points her phone at a leaf and taps capture."

*(Screen recording: crop selector → camera → capture → inference in <1s → result screen.)*

> "In under a second: leaf rust — the actual confidence number will show on screen,
> say whatever the app displays for your photo. She taps to hear the recommended
> action — read out in her own language, because advice she can't understand is advice
> she can't use. The observation — photo, GPS if available, diagnosis, timestamp — is
> saved locally right away."

*(Screen: audio playback icon active; observation saved confirmation.)*

> "She has no signal right now, so nothing is sent anywhere yet — it's queued. Later,
> when she's back near a tower or on Wi-Fi, LeafScout syncs quietly in the background."

*(Screen: sync queue indicator, then a "synced" state once connectivity is simulated.)*

> "On the other end, her cooperative's extension officer sees a dashboard: which
> villages are reporting which disease, on which crop, this week — evidence to
> prioritize the next visit, instead of visiting on a fixed twice-a-year schedule
> regardless of what's actually happening in the field."

*(Screen: simple cooperative-view mockup/dashboard, filterable by crop.)*

*For the technical judges, keep this line in even if you cut time elsewhere:*

> "Tech stack: React Native with a native TFLite binding for on-device inference,
> SQLite for offline-first storage with a store-and-forward sync queue, and Supabase
> on the backend for sync and the cooperative dashboard. We trained on exactly the
> datasets this challenge names for agriculture: BRACOL for coffee, the Makerere
> cassava leaf disease dataset, and iBean for bean — one shared MobileNetV3 backbone,
> one linear SVM head per crop, validated with five-fold cross-validation and
> cross-checked against PlantDoc's real field photos, not just studio images, so our
> reported accuracy reflects the field, not just the lab."

---

## 3:15–3:45 — The challenge/gap being addressed

> "This sits right at the start of Noor's week, not at the end of it. Today, she finds
> out something's wrong with her coffee only when it's visibly bad, or when the officer
> happens to visit. LeafScout moves that moment from 'twice a year, by chance' to 'the
> moment she notices a leaf looks off' — and turns that single photo into a logged,
> shareable piece of evidence the extension system can actually act on, for whichever
> of these three crops she's growing that season."

---

## 3:45–4:15 — Your take: what localizing AI development means

> "For us, localizing AI development didn't mean translating a UI. It meant three
> things: training on the datasets and crops this region actually grows — coffee,
> cassava, bean — not a generic plant dataset, and being upfront when one of them, like
> cassava, is simply a harder problem with less accuracy today. It meant putting the
> output in her language, by voice, not just text. And it meant designing the model to
> say 'I'm not sure' instead of guessing, because a wrong answer that touches someone's
> only harvest is a real cost, not an edge case. That's what we think localizing AI for
> development actually means."

*(On screen: LeafScout logo / team name, closing frame.)*

---

## Production checklist
- [ ] Record screen capture of the full flow in one take if possible (crop select →
      capture → result → audio → offline queue → sync) to keep the demo tight and honest
- [ ] Keep total runtime inside 2:00–5:00 (hard cutoff: no shortlist without the video)
- [ ] Caption the one-sentence problem statement on screen verbatim — judges skim
- [ ] Say the words "confidence," "offline," and "human" out loud at least once each —
      they map directly to the pass/fail "Responsible AI" criterion
- [ ] If time is tight, cut from "Your take," not from the guardrails section — the
      pass/fail criterion is non-negotiable; the closing reflection is not
- [ ] If you only have time to demo one crop end-to-end, demo coffee (it's the Annex B
      scenario crop) and show the cassava/bean heads as a quick cut to the model_registry
      table instead of a full second demo
- [ ] No real leaf on hand? The app has a "Try a sample photo instead" button (a real
      training-set photo per crop) that runs the exact same on-device pipeline — fine to
      use for the recording, it's not a fake/mocked result
