# BidSense Pitch Deck (Round 2: Value Prop 40% / Market Viability 40% / Pitch 20%)

One slide per section. Keep each slide to the bolded line plus 3 bullets max.

---

## Slide 1: Title

**BidSense. Win more bids. Skip the drudgery.**

- AI bid and proposal response engine
- RFP in, reviewed proposal draft + GO/NO-GO decision out, in minutes
- Built on the hackathon's real dataset: 120 historical bids, 50 capability records

---

## Slide 2: The Problem (the pain is quantified)

**Bid teams burn 60 to 80 percent of their time on document drudgery, and one missed mandatory clause means disqualification.**

- A typical 15 to 80 page RFP takes 2 to 4 working days to first draft
- Requirements are scattered across submission rules, eligibility clauses, and annexes; humans miss them
- Companies bid on tenders they cannot win and skip tenders they could have won, because nobody can quantify win probability before committing the team

The cost is not the writing time. It is disqualifications and wrong GO decisions.

---

## Slide 3: The Solution

**Upload the tender. BidSense reads it like a senior bid manager.**

1. Extracts every requirement, evaluation criterion, deadline, and Q&A section, with source pages
2. Checks each requirement against your capability library, with cited evidence, PASS / PARTIAL / GAP
3. Scores win probability with an explained ML model and issues GO / CONDITIONAL GO / NO-GO
4. Drafts the full proposal, every claim cited to a real capability record, then exports to Word

Live demo: three real-style tenders, three different honest answers (GO, CONDITIONAL GO with one closable gap, NO-GO).

---

## Slide 4: Why we win (differentiation)

**Most AI proposal tools are a textbox over ChatGPT. BidSense is an auditable decision system.**

- Anti-hallucination by contract: the draft can only cite real capability IDs, fabricated citations are rejected and tested
- Win probability is a trained model on bid history with SHAP explanations, not an LLM guess, and we publish the ablation study that shows what the model actually learned
- The system says NO. A tool that flatters every bid is worthless; ours declined a road tender with 4 genuine eligibility gaps
- Works offline from a response cache; survives venue Wi-Fi and API outages

---

## Slide 5: Value proposition (the math)

**From 2 to 4 days to under 5 minutes to first reviewed draft.**

- Manual baseline: 0.5 hours per page, minimum 16 hours per response
- BidSense pipeline: minutes per response, then human review only where it matters
- One avoided disqualification pays for a year of the product
- One correct NO-GO saves an entire wasted bid cycle (the average team wins roughly half its bids; the losing half is pure cost)

---

## Slide 6: Market

**Every company that answers tenders is a customer. Start in Pakistan, the playbook is global.**

- Public procurement is typically 15 to 20 percent of GDP; for Pakistan that implies a tender market in the tens of billions of dollars annually (PPRA-regulated plus provincial)
- Thousands of registered government contractors and IT/consulting firms respond to tenders monthly, mostly with Word templates and copy-paste
- Globally, proposal and RFP response software is an established multi-billion dollar category (Responsive, Loopio, Qvidian) growing on the back of AI adoption, with no Pakistan-localized player handling PPRA formats, PKR amounts, and local eligibility rules (PEC categories, FBR, ISO requirements)

Beachhead: Pakistani IT services and construction firms bidding on government and donor-funded tenders.

---

## Slide 7: Business model

**SaaS subscription plus usage, priced against the cost of one bid manager day.**

- Starter: per-seat monthly subscription, capped bids per month
- Growth: per-bid pricing for bursty bidders (construction, EPC)
- Enterprise: capability-library onboarding, private deployment, win-rate analytics
- Cost per processed bid is a few dollars of LLM and embedding spend; gross margin stays software-grade

---

## Slide 8: Validation and what is real today

**This is not a concept deck. The prototype you just saw is end-to-end real.**

- Full pipeline working: ingest, extraction, RAG matching, trained win model, drafting, DOCX/CSV export
- 32 automated tests passing, surfaced live inside the product on the Validation page
- Trained and evaluated on the provided 120-bid history; we report model limits honestly, including the ablation
- Human-in-the-loop by design: analysts override match statuses and approve every section

---

## Slide 9: Roadmap

**Prototype to product in three steps.**

1. Now: single-company workspace, three demo verticals (energy, health IT, construction)
2. Next quarter: capability-library builder (ingest past proposals to auto-build the library), PPRA tender feed integration, win/loss feedback loop retraining the model on each closed bid
3. Year one: multi-tenant SaaS, team workflows, pricing intelligence from historical award data

---

## Slide 10: Ask / Close

**Bid teams should compete on what they can deliver, not on who reads PDFs faster.**

- We built the full system in 24 hours on the provided dataset
- The team: full-stack + AI/ML engineering with agency delivery experience shipping client systems
- We are looking for pilot partners who answer tenders every month, and we would love TEKROWE to be the first
