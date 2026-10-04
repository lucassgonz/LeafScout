# LeafScout — Technical Walkthrough (1 minute)

Live demo script for the Technical Walkthrough segment — distinct from `PITCH_SCRIPT.md`
(the narrative video pitch). This is denser and faster: judges in this segment are
scoring against the concept note's actual criteria (§9), so every line below maps to one
of them. Target: ~150 words, ~60 seconds at a brisk, confident pace.

**Before you start:** app open on the Crop screen, 0 observations, airplane mode OFF (so
the sync + GPS moments land). Have the Simulator or phone already unlocked and the app
foregrounded — don't spend demo seconds unlocking.

---

## Script

*(0:00 — on screen: crop selector)*

> "LeafScout — one shared MobileNetV3 backbone, a separate linear SVM head per crop,
> coffee, cassava, bean — the exact datasets this challenge names for agriculture."

*(0:08 — tap "Try a sample photo instead")*

> "Everything from here runs on-device. No server call for the diagnosis itself — that's
> the Small AI constraint: it has to work on a phone a farmer already owns, offline."

*(0:18 — result appears: diagnosis, confidence, recommended action)*

> "Under a second, with a confidence score. Below our threshold, it doesn't guess — it
> tells her to ask a person instead. That's the guardrail: a human always makes the
> final call."

*(0:28 — tap "Listen")*

> "The recommended action is spoken, not just written — accessible without reading."

*(0:33 — point at the GPS pin / pending-sync counter)*

> "It logs with location, saves locally first, and syncs to the cooperative's dashboard
> the moment a connection shows up — never blocking on one."

*(0:42 — switch to the web dashboard tab, already loaded)*

> "And here's that same data live — the extension officer's view, same Supabase project,
> real observations, real model accuracy per crop. Coffee 82%, bean 91%, cassava 72% —
> we report that honestly, it's the published ceiling for a lightweight model on an
> imbalanced dataset, not something we're hiding."

*(0:55 — close)*

> "On-device, offline-first, guardrailed, and honest about what it doesn't know yet."

---

## Why this script, not a longer one

Mapped directly to concept note §9 (judging criteria), so nothing here is decorative:

| Line | Criterion it hits |
|---|---|
| "exact datasets this challenge names" | Data grounding (15%) |
| "runs on-device... has to work offline" | Built solution fidelity (25%) — the core Small AI constraint |
| "doesn't guess... human always makes the final call" | Responsible AI (pass/fail) |
| "spoken, not just written" | §6 — at least one interaction by voice/local language |
| "saves locally first, syncs... never blocking" | Built solution fidelity — offline-first architecture |
| "same data live... extension officer's view" | Development relevance (20%) — closes the loop to the extension system |
| "Coffee 82%... we report that honestly" | Evidence it works (15%) + Responsible AI (disclosing limitations, not just claiming a number) |
| One shared backbone, three heads | Scalability (10%) — implicit in the architecture itself |

**If you're cut off early**, the three lines that must survive no matter what: the
offline/on-device claim, the confidence guardrail, and the honest accuracy numbers. Those
three are worth more judging weight combined than anything else in the script.

**If you have 10 extra seconds**, add after the dashboard beat: *"One shared backbone
means adding a fourth crop is a retrain, not a rebuild."* — directly answers scalability
without needing to be asked.
