<!--
BidSense pitch deck - Gamma outline (6 slides, balanced pitch).

How to import into Gamma:
  1. Gamma > Create new > "Paste in text".
  2. Paste this whole file.
  3. Each "---" divider becomes a new card; each H1 is the slide title.
  4. Let Gamma generate; keep one card per slide (do not let it split).

Copy is judge-facing: no em dashes. Every claim traces to the build
(see pitch/project-proposal.md, references/technical-architecture.md,
eda/EDA_REPORT.md, and the in-app /validation page).
-->

# The bid that gets thrown out on page 3

- Bid teams spend 60 to 80 percent of their time just reading tenders and assembling responses.
- One missed mandatory clause buried in an annex disqualifies the entire bid, after days of work.
- Nobody can quantify win probability before the effort is spent, so firms chase bids they cannot win and skip ones they could.
- A 15 to 80 page RFP takes 2 to 4 working days to reach a first draft.

Visual: a tender document with a red "DISQUALIFIED" stamp.

Speaker notes: Open on the pain and the stakes. This is money and reputation lost on a technicality.

---

# BidSense reads a tender like a senior bid manager

- Upload a tender (PDF or DOCX). Get a complete, auditable bid workspace in minutes, not days.
- Four-stage pipeline: Extract every requirement, Match it to our capability library with cited evidence, Score win probability, Draft a compliant proposal.
- One clear output: a GO, CONDITIONAL GO, or NO-GO decision plus a review-ready draft.
- Live demo: upload to decision to drafted proposal, on screen.

Visual: the four-stage pipeline as a horizontal flow, ending in a GO/NO-GO badge.

Speaker notes: This is the "what it does" slide. Trigger the live demo here.

---

# It says no when it should

- A tool that flatters every bid is useless. BidSense declined a real road tender with four genuine eligibility gaps.
- Explainable win probability from a trained model with SHAP, not a number an LLM made up.
- Anti-hallucination by contract: every sentence in the draft cites a real capability record. Fabricated citations are rejected and unit-tested.
- Intellectual honesty built in: we publish an ablation study inside the app instead of hiding the data's limits.

Visual: split screen, GO on a winnable bid versus NO-GO with the four red gaps listed.

Speaker notes: This is the differentiator slide. Most teams build a chatbot over a text box. We built an auditable decision system.

---

# Real ML, validated in the open

- Trained on the hackathon's own data: a 120-bid history and a 50-record capability library.
- Honest metrics: every score is out-of-fold (cross-validated), so it reflects generalization, not memorization.
- Two-stage win model solves data leakage: the awarded score is only known after evaluation, so we estimate it pre-bid from compliance, sector priors, and budget fit.
- Automated test suite and a live in-app validation page. Judges see evidence, not claims.
- Runs offline from a warmed cache, so it survives venue Wi-Fi and API outages.

Visual: screenshot of the in-app Validation page (score-to-win curve and ablation study).

Speaker notes: This is the proof slide for the technical judges. Point them to /validation live.

---

# A real market, with no local player

- Public procurement is 15 to 20 percent of GDP. Proposal-response software is an established global category (Responsive, Loopio).
- No localized player handles PPRA formats, PKR amounts, and local rules like PEC categories and ISO requirements.
- Beachhead: Pakistani IT-services and construction firms that bid on government and donor-funded tenders every month.
- Cost per processed bid is a few cents of model spend, so margins are software-grade.
- Business model: per-seat SaaS plus per-bid pricing.

Visual: a market funnel from global RFP software down to the Pakistan procurement beachhead.

Speaker notes: This is the Round 2 market-viability slide. Lead with the size, land on the wedge.

---

# Built end to end, and here is where it goes

- Team: Aleem Ul Hassan (Data and ML Integration), Anas Khan (Backend), Umer Khatab (Frontend).
- Today: single-company workspace, three demo verticals, full pipeline working and offline-resilient.
- Next quarter: a capability-library builder that ingests past proposals, a PPRA tender feed, and a win/loss loop that retrains on every closed bid.
- Year one: multi-tenant SaaS with team workflows and pricing intelligence from historical award data.
- The ask: [insert your specific ask, for example pilot partners, mentorship, or the prize].

Visual: a three-step roadmap timeline with the team initials.

Speaker notes: Close on credibility (we built the whole thing) and momentum (clear path forward). End with the ask.
