# Demo Script

## Pre-flight checklist (do this at 9:30 AM, before judges arrive)

1. `setup.ps1` already run; backend on :8000, frontend on :3000
2. In `backend/.env` set `DEMO_MIN_STEP_SECONDS=1.5` and restart the backend (makes the live stepper followable; cached replays otherwise finish in 0.4s)
3. Delete old workspaces from the home page so the list is clean
4. Pre-run the road RFP once so its NO-GO workspace already sits in the list (you will not demo it live, just point at it)
5. Keep `demo-assets/` open in Explorer: solar PDF and HMIS DOCX ready to drag
6. Browser zoom 110 to 125 percent, dark room friendly
7. If Wi-Fi dies: nothing changes. The cache replays everything offline. Say so out loud, it is a feature.

---

## Round 1: table demo for visiting judges (aim for 4 to 5 minutes)

Rubric: Technical 30, Relevance 20, Innovation 20, Validation 15, Feasibility 15. The script hits them in that order of weight.

**0:00 - Hook (15s)**
"Bid teams spend 60 to 80 percent of their time reading tenders and copy-pasting proposals, and one missed mandatory clause disqualifies the whole bid. BidSense reads the tender like a senior bid manager. Watch."

**0:15 - Live run (60s)** [drag `RFP_Solar_PV_Hospitals.pdf` onto the dropzone]
Narrate the stepper as it ticks: "Four stages. Extraction pulls every requirement with its source page. Matching checks each one against our capability library using RAG. Win probability comes from an XGBoost model trained on the 120-bid history you gave us. Then it drafts the proposal."

**1:15 - Overview tab (40s)**
Point at the GO banner and the 98 percent gauge. "GO, no mandatory gaps. Deadlines, budget, evaluation criteria weights, all extracted. And the effort card: this run took seconds against an industry baseline of two-plus days."

**1:55 - Requirements + Compliance (50s)**
Open one PASS row: "Every status has a rationale and cited evidence from the library, this is not a vibe check." Filter to GAP: "It found one genuine gap and said so. Analysts can override any status, human stays in the loop."

**2:45 - Draft tab (40s)**
"Every sentence cites a real capability record. The system physically cannot cite an ID that does not exist, we test for that. Sections are approve, edit, or regenerate-with-feedback." Click export DOCX if they lean in.

**3:25 - The decision story (45s)** [switch to the workspace list]
"Same engine, three tenders, three different answers." Open the HMIS workspace: "Health IT tender, 98 percent win probability, but CONDITIONAL GO, because it requires CMMI Level 5 and we hold Level 3. That one flag is worth the entire product, it is the difference between winning and being disqualified on page 40." Point at the road tender: "And this one it refused, 2 percent, four eligibility gaps. A tool that flatters every bid is useless."

**4:10 - Validation page (30s)**
"Thirty-two automated tests, green, live from pytest. Model metrics with the confusion matrix, and an ablation study where we are honest about what the dataset's score field does. Judges should not have to take our word for anything."

**4:40 - Close (20s)**
"PDF and DOCX in, cited draft and an explainable GO/NO-GO out, offline-capable, fully tested. Happy to go deeper on any layer: the RAG matcher, the model, or the extraction schema."

### Likely judge questions, prepared answers

- "Is the LLM doing the win probability?" No. Trained XGBoost on the provided history, SHAP per-feature breakdown on screen. The LLM never sees the number.
- "What if the model is wrong on new bids?" The dataset's evaluation score nearly determines the outcome, we show that ablation openly. For new bids we estimate that score from compliance, sector win rate, and budget alignment, all visible in the breakdown panel.
- "Hallucinations?" Drafts can only cite library IDs; a regex contract rejects fabricated ones and it is unit-tested. Gaps are written honestly as gaps.
- "Scanned PDFs?" Text-layer PDFs and DOCX today; OCR is a bolt-on at the ingest layer, the rest of the pipeline is format-agnostic.
- "Why did the demo run so fast?" Responses for the demo docs are disk-cached so the demo works offline; fresh documents take a few minutes of real LLM calls. The per-step timings shown are real.

---

## Round 2: live-streamed pitch, top 15 (5 minutes, 2:30 to 5:00 PM)

Rubric flips to startup mode: Value Prop 40, Market Viability 40, Pitch 20. Lead with money, not architecture. Use `pitch/deck.md` slides.

**0:00 - Problem (45s)** Slide 2. The 60-80 percent figure, the disqualification risk, the wrong-GO cost.
**0:45 - Demo (90s)** Compressed Round 1 flow: upload solar, GO banner, one evidence card, then the HMIS CONDITIONAL GO story. The CMMI flag is the emotional peak, spend time there.
**2:15 - Value prop (45s)** Slide 5. Days to minutes, one avoided disqualification pays for the year, one correct NO-GO saves a bid cycle.
**3:00 - Market (60s)** Slide 6. Procurement share of GDP, no localized player, global category proven by Responsive/Loopio. Beachhead: Pakistani IT and construction bidders.
**4:00 - Model + traction path (40s)** Slides 7 and 9. Seat plus per-bid pricing, capability-library onboarding as the enterprise wedge, pilot partners next.
**4:40 - Close (20s)** Slide 10. "Built end-to-end in 24 hours on your dataset. Imagine what we ship with a quarter. We want TEKROWE as pilot partner number one."

Backup: if the live demo cannot run on stage, screen-record the Round 1 flow in the morning (OBS or Xbox Game Bar, Win+Alt+R) and narrate over the recording. Record it during the 9:30 pre-flight regardless.
