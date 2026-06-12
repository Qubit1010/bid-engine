# BidSense — AI-Powered Bid & Proposal Response Engine

**CUST Hackathon 2026 · Problem #1 (TEKROWE)**

Upload an RFP/RFQ/Tender (PDF or DOCX). BidSense extracts every requirement, evaluation criterion, and deadline; checks each requirement against the company's capability library with cited evidence; drafts a structured, citation-grounded proposal; flags compliance gaps; and scores win probability with an explained **GO / CONDITIONAL GO / NO-GO** decision — in seconds instead of days.

> Bid teams spend 60–80% of their time on manual document drudgery, and a single missed mandatory requirement means disqualification. BidSense turns a 2–4 day response into a reviewed first draft in under 5 minutes.

---

## Quick start

```bash
# backend (Python 3.11+)
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --port 8000

# frontend (Node 20+), second terminal
cd frontend
npm install
npm run dev          # http://localhost:3000
```

Or just run `./setup.ps1` (Windows) / `./setup.sh` (macOS/Linux).

**No API keys needed for the demo.** The repo ships with a warmed LLM response cache (`backend/cache/`) covering the three demo RFPs in `demo-assets/`, so a cold clone replays the full pipeline **offline** — upload any of the three documents and the complete run finishes in under a second. Keys (see `backend/.env.example`) are only required to process *new* documents.

On first boot the backend self-seeds: loads the provided 120-bid history + 50-record capability library into SQLite, builds the embedding index, and trains the win-probability model.

## The 3-document demo

| Document (in `demo-assets/`) | Result | Why it matters |
|---|---|---|
| `RFP_Solar_PV_Hospitals.pdf` | **GO** — P(win) 98%, no mandatory gaps | Strong domain match; shows the full happy path with cited draft |
| `RFP_Hospital_HMIS_Implementation.docx` | **CONDITIONAL GO** — P(win) 98% *but* 1 mandatory gap (CMMI L5 required, company holds L3) | The most valuable real-world case: "you'd win this — if you close one gap." Also proves the DOCX ingestion path |
| `RFP_District_Road_Rehabilitation.pdf` | **NO-GO** — P(win) 2%, 4 genuine eligibility gaps (PEC C-A registration, turnover, road experience, ISO 14001) | The system says *no* honestly — it doesn't flatter every bid |

The three outcomes together demonstrate the decision logic is discriminative, not decorative.

## Architecture

```
Next.js 16 + React 19 + Tailwind 4                       (port 3000)
    │  /api/* rewrite proxy
    ▼
FastAPI · Python                                          (port 8000)
    ├─ ingest/    PyMuPDF (PDF) + python-docx (DOCX) → page-mapped text
    ├─ extract/   LLM structured extraction (pydantic-validated JSON):
    │             requirements (mandatory flag + source page), criteria
    │             + weights, deadlines, budget, Q&A sections
    │             + regex NER validators (dates, PKR amounts, percentages)
    ├─ rag/       OpenAI embeddings over the 50-record capability library,
    │             hybrid cosine + keyword retrieval → evidence per requirement
    │             → LLM compliance judge: PASS / PARTIAL / GAP + rationale
    ├─ winprob/   two-stage scorer:
    │             (A) XGBoost trained on the provided 120-bid history
    │             (B) score estimator from compliance %, sector win-rate
    │                 prior, budget alignment, mandatory-gap penalty
    │             + SHAP feature contributions → GO/NO-GO decision memo
    ├─ draft/     section-by-section proposal generation grounded ONLY in
    │             retrieved evidence — every claim cites [CAP-xxx]/[CO-PROFILE];
    │             fabricated citation IDs are rejected by regex contract
    ├─ export/    proposal DOCX + compliance matrix CSV
    └─ core/llm   dual provider (OpenAI primary, Claude fallback) with a
                  disk cache keyed on prompt hash → offline demo replay
    ▼
SQLite (workspaces, requirements, matches, draft sections, decisions)
```

### Required AI components → where they live

| Component | Implementation |
|---|---|
| **LLM** | Structured extraction, compliance judging, draft generation (`extract/`, `rag/matcher.py`, `draft/`) — dual provider with automatic fallback |
| **RAG** | Embedding index over the capability library + hybrid retrieval; every match and draft sentence carries retrieved-evidence citations (`rag/`) |
| **NER** | Regex normalizers for dates (5 formats), PKR amounts (Million/Billion/crore/lakh), percentages — validating/normalizing LLM output (`extract/ner.py`) |
| **Scoring / ranking** | XGBoost win-probability model (5-fold CV on the provided bid history) + SHAP explanations + transparent score estimator (`winprob/`) |

## Problem-statement deliverables → features

| Deliverable | Status | Where |
|---|---|---|
| Ingest RFP/RFQ/Tender in PDF/DOCX | ✅ | Upload dropzone; demo includes both formats |
| Extract requirements, eval criteria, deadlines, Q&A | ✅ | Overview + Requirements tabs, source-page references |
| Per-RFP workspace | ✅ | Each upload gets its own workspace with full pipeline state |
| Match against Company Capability Library | ✅ | RAG over the provided 50-record library, evidence cards per requirement |
| Auto-draft structured proposal response | ✅ | Draft tab — per-section approve / edit / regenerate-with-feedback |
| Flag compliance gaps | ✅ | Compliance tab — gaps-first matrix, mandatory-gap callout |
| Win-probability score | ✅ | Trained model + SHAP breakdown + comparable past bids |
| GO / NO-GO recommendation | ✅ | Three-way decision with generated memo (GO ≥ 0.55 & no mandatory gaps; CONDITIONAL 0.40–0.55 or mandatory gaps; NO-GO below) |
| ≥50% effort reduction evidence | ✅ | Effort card: pipeline wall-clock vs 0.5 h/page (min 16 h) manual baseline → >99% reduction |
| Analyst review / human-in-the-loop | ✅ | Requirement status overrides + draft section approval workflow |
| Export | ✅ | Proposal DOCX (with compliance matrix + inline citations) and compliance CSV |

## Validation (see the in-app `/validation` page)

- **32/32 pytest tests green** (~4.5 s) — parsers, NER normalizers, schema contracts, retrieval sanity, model-quality gate, citation contract. The live test report is served at `GET /api/validation` and rendered in-app.
- **Model honesty:** the dataset's `Score %` field almost perfectly separates Win/Loss (AUC ≈ 1.0 alone). We report this openly on the Validation page, including an **ablation study** (without the score feature, CV AUC collapses to ~0.45) — which is exactly why production use needs the Stage-B score *estimator* for new bids where no evaluation score exists yet.
- **Anti-hallucination:** drafts may only cite real capability IDs; the citation regex rejects fabricated IDs (tested), and the UI highlights every citation against its evidence card.
- **Offline resilience:** the full pipeline replays from the disk cache in ~0.4 s with networking disabled — verified.

## API surface

```
GET    /api/health
GET    /api/workspaces                       list
POST   /api/workspaces                       upload PDF/DOCX → workspace
GET    /api/workspaces/{id}                  full detail incl. live pipeline steps
POST   /api/workspaces/{id}/run              (re)run pipeline
DELETE /api/workspaces/{id}
PATCH  /api/requirements/{id}                analyst status override
PATCH  /api/sections/{id}                    edit / approve draft section
POST   /api/sections/{id}/regenerate         regenerate with feedback
GET    /api/workspaces/{id}/export/docx
GET    /api/workspaces/{id}/export/compliance.csv
GET    /api/validation                       dataset stats, model metrics, test report
```

## Demo pacing note

`DEMO_MIN_STEP_SECONDS` (in `backend/.env`, default `0` = off) floors each pipeline step's wall time so the live stepper stays followable when responses replay from cache. It never slows genuinely fresh runs — it exists purely so an audience can watch the four stages tick by instead of seeing them flash past in 0.4 s. Set it to `1.5` for stage demos. This is presentation pacing, fully disclosed; the real timings are recorded and shown per step.

## Data

`backend/data/` holds the provided datasets converted to CSV: 120-row bid history and 50-record capability library (from `Problem#1_Sample_Datasets (TEKROWE).xlsx`). The evaluation-criteria taxonomy sheet referenced in the problem statement was missing from the provided file, so we synthesized a 15-entry taxonomy (`criteria_taxonomy.json`) across the dataset's sectors.

## Team

Built for CUST Hackathon 2026 by the NexusPoint team.
