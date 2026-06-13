# BidSense — Workflow & Interface Guide

How BidSense works end to end: how you input a tender, what each pipeline stage does, what every tab shows, and how each metric is calculated. Grounded in the actual code (`backend/rag/matcher.py`, `backend/winprob/`, `frontend/src/app/workspace/[id]/page.tsx`).

---

## How you input

One action: **drag an RFP/tender file (PDF or DOCX) onto the dropzone** on the home page, or click to browse. Analysis starts automatically — no forms, no config. Each upload becomes a **workspace** (one tender = one workspace), which is why the home page lists the three demo bids (Solar, HMIS, Road).

You do **not** input your company info per bid. The company's capability library (50 past-project records) and company profile (certifications held, registrations, financials) are seeded once into the database. The RFP is the only thing that changes per run.

---

## What runs under the hood (the 4-stage pipeline)

When you drop a file, the stepper ticks through four stages, each timed and persisted:

1. **Extract** — parses the document to text + page map, then an LLM pulls a structured RFP profile: title, issuer, sector, budget, deadlines, evaluation criteria + weights, and every requirement (flagged mandatory/optional, with source page). A regex NER pass normalizes dates and PKR amounts.
2. **Match** — each requirement is embedded and retrieved against the capability library (RAG, top-3 evidence). An LLM compliance analyst judges each one **PASS / PARTIAL / GAP** with a one-sentence rationale and the exact evidence IDs it used. This uses the 4-type requirement taxonomy:
   - **A. Procedural / submission-format** → satisfied by commitment in the submission (always PASS).
   - **B. Verifiable bidder attributes** (named certs, registrations, turnover) → judged strictly against the company profile; a cert we don't hold is a GAP.
   - **C. Experience / track record** → PASS when domain matches and thresholds (count, value, recency) are met arithmetically by the records.
   - **D. Forward delivery obligations** → commitments; PASS when our experience makes them credible.
3. **Win probability** — estimates the bid's expected evaluation score, feeds it into the trained XGBoost model → P(win), plus SHAP feature contributions and a GO/NO-GO decision.
4. **Draft** — writes the proposal section by section, every claim citing a real `[CAP-xxx]` or `[CO-PROFILE]` record.

---

## The five workspace tabs

### Overview
The executive summary. The GO/CONDITIONAL/NO-GO banner, the P(win) gauge, and four headline stats: Est. score, Compliance %, Mandatory gaps, Effort saved. Below it: the extracted RFP profile (title, issuer, sector, budget, deadline, summary), key deadlines, evaluation criteria with weight bars, and the effort-reduction card (pipeline seconds vs. the manual 2-4 day baseline). The "should I even read further" screen.

### Requirements
The full extracted requirement list as a filterable table (ALL / PASS / PARTIAL / GAP). Each row shows the requirement text, category, source page, status, and confidence. Click a row to expand: the rationale, the retrieved evidence cards (cited ones highlighted), and **analyst override buttons** — you can manually flip any status; human stays in the loop. The red "M" tag marks mandatory requirements.

### Compliance
The same data reframed as a risk view. Four count cards (Coverage %, Pass, Partial, Gaps), a stacked coverage bar, a **Mandatory Gaps — Action Required** panel (the deal-breakers), and the full compliance matrix sorted gaps-first so reviewers see risk immediately. This is the tab that catches the disqualification-on-page-40 problem.

### Draft
The generated proposal, section by section. Citations are highlighted inline (`[CAP-012]`, `[CO-PROFILE]`). Each section can be **approved, edited inline, or regenerated with feedback** (e.g. "lead with the government experience"). The anti-hallucination guarantee lives here: the draft can only cite IDs that actually exist.

### Win Probability
The explainability tab. Five panels:
- **P(win) gauge** — from the trained model (shows which model + CV AUC).
- **Estimated evaluation score** — the heuristic breakdown feeding the model: baseline + compliance + sector track record + budget alignment + gap penalty (each component visible).
- **SHAP contributions** — why the model produced this number, per feature.
- **Comparable past bids** — the 5 closest historical bids by sector + budget, with outcomes.
- **GO / NO-GO decision memo** — auto-written, editable before circulation.

---

## The metrics, defined

- **P(win)** — XGBoost output, trained on the 120-bid history. The LLM never produces this number.
- **Est. score** — predicted evaluation score (0-100). The key model input, computed from compliance coverage vs. historical mean, sector win rate, budget alignment, minus a mandatory-gap penalty.
- **Compliance %** — `(PASS + 0.5 × PARTIAL) / total requirements`. Partial counts as half credit.
- **Mandatory gaps** — count of mandatory requirements that came back GAP. Even one forces CONDITIONAL_GO at best (the CMMI Level 5 case on the HMIS bid).
- **Decision logic** — GO needs P(win) ≥ 0.55 **and** zero mandatory gaps; CONDITIONAL_GO if P(win) ≥ 0.40 or there are mandatory gaps despite a high score; otherwise NO_GO.

---

## The Validation tab (top nav, not per-workspace)

The **credibility / "don't take our word for it" page**, mapped to the rubric's Validation 15%. It surfaces, live:
- The full pytest suite results (32/32 passing) pulled from the actual test run.
- Model metrics: CV AUC, confusion matrix.
- The **honest ablation** — showing the dataset's score field nearly determines the outcome on its own, disclosed openly rather than hidden.

It exists so judges see evidence the system works, not marketing claims. It's separate from any single bid because it's about the engine itself, not one tender.

---

## One-line mental model

**Document in → reviewed, cited proposal draft + an explainable GO/NO-GO out**, with every status and every probability traceable to its evidence.
