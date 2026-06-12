"""Compliance matcher: requirement -> retrieved evidence -> PASS / PARTIAL / GAP.

LLM judges each batch of requirements against its retrieved evidence; a
deterministic similarity-threshold fallback keeps the pipeline alive offline.
"""
import json
from functools import lru_cache

from core import config, llm
from extract.schemas import MatchResult
from rag.retriever import get_retriever

BATCH_SIZE = 8

MATCH_SYSTEM = """You are a compliance analyst at the bidding company. For each tender requirement,
judge whether OUR COMPANY's evidence satisfies it. Evidence comes in two forms:
1. CAPABILITY RECORDS (CAP-xxx): summary-level past-project records (domain, value, duration, cert, client type, year).
2. COMPANY PROFILE (CO-PROFILE): organization-level facts (registrations, certifications held/not held, financials, staff, HSE).

Judging rules — first classify the requirement's TYPE, then judge:
A. PROCEDURAL / SUBMISSION-FORMAT requirements (bid validity period, sealed envelopes, number of
   copies, addressing, page limits, responding to listed sections, attending pre-bid meetings) and
   EVALUATION RULES the procuring agency applies (scoring thresholds, disqualification clauses):
   these are satisfied BY COMMITMENT in the submission itself — always PASS, rationale
   "Procedural commitment — complied with in the submission", used_cap_ids ["CO-PROFILE"].
B. VERIFIABLE BIDDER ATTRIBUTES (named certifications, statutory registrations, licenses, turnover,
   financial capacity, staff credentials): judge strictly against CO-PROFILE. Certifications must
   match exactly (ISO 9001 != ISO 14001); anything in certifications_not_held or registrations we
   lack is GAP. PASS only if a profile fact explicitly covers it.
C. EXPERIENCE / TRACK-RECORD requirements: capability records are SUMMARY-LEVEL by design — PASS
   when the domain matches and stated thresholds (count, value, recency, client type) are met
   arithmetically by the records; PARTIAL if close but short (e.g., 1 of 2 required projects).
   Do not demand detail the summaries cannot contain.
D. FORWARD DELIVERY OBLIGATIONS the winning bidder will perform (scope of work, installation,
   training, O&M, warranties, liaison/approvals, assigning qualified staff, equipment the bidder
   will procure to a stated spec): these are commitments, not pre-existing attributes. PASS when
   our domain experience or profile makes the commitment credible; PARTIAL when our evidence is
   only adjacent; GAP only if we have no related capability at all.
- GAP is reserved for genuine inability: a named attribute we lack (B) or an obligation with zero
  supporting capability (D). Never GAP a requirement merely because summaries omit fine detail.
Respond with JSON: {"results": [{"req_index": int, "status": "PASS"|"PARTIAL"|"GAP",
"confidence": 0.0-1.0, "rationale": str (one sentence), "used_cap_ids": [str]  // CAP-xxx and/or "CO-PROFILE"
}]}"""


@lru_cache(maxsize=1)
def company_profile_text() -> str:
    profile = json.loads((config.DATA_DIR / "company_profile.json").read_text(encoding="utf-8"))
    return json.dumps(profile["company"], indent=1)


def fallback_status(score: float) -> tuple[str, float]:
    if score >= 0.55:
        return "PASS", round(min(score, 0.95), 2)
    if score >= 0.35:
        return "PARTIAL", round(score, 2)
    return "GAP", round(max(0.2, score), 2)


def match_requirements(requirements: list[dict], top_k: int = 3) -> list[dict]:
    """Each requirement dict needs 'text'; returns dicts with evidence + judgment."""
    retriever = get_retriever()
    enriched = []
    for r in requirements:
        evidence = retriever.retrieve(r["text"], top_k=top_k)
        enriched.append({**r, "evidence": evidence})

    for start in range(0, len(enriched), BATCH_SIZE):
        batch = enriched[start : start + BATCH_SIZE]
        lines = []
        for i, item in enumerate(batch):
            ev_lines = [
                f"  - {e['cap_id']}: {e['domain']} | {e['summary']} | cert: {e['certification']}"
                f" | {e['contract_value']} | {e['client_type']} | {e['year_completed']}"
                f" (similarity {e['score']:.2f})"
                for e in item["evidence"]
            ]
            lines.append(
                f"[{i}] REQUIREMENT ({item.get('category', 'General')}"
                f"{', MANDATORY' if item.get('mandatory') else ''}): {item['text']}\n"
                + "\n".join(ev_lines)
            )
        user = ("COMPANY PROFILE (CO-PROFILE):\n" + company_profile_text()
                + "\n\nPer-requirement retrieved capability evidence:\n\n" + "\n\n".join(lines))

        try:
            out = llm.complete_json(MATCH_SYSTEM, user, bucket="match")
            results = {r["req_index"]: r for r in out.get("results", [])}
        except (RuntimeError, ValueError, json.JSONDecodeError):
            results = {}

        for i, item in enumerate(batch):
            raw = results.get(i)
            if raw:
                try:
                    m = MatchResult(**{k: raw[k] for k in
                                       ("status", "confidence", "rationale", "used_cap_ids")
                                       if k in raw})
                    item["status"] = m.status
                    item["confidence"] = m.confidence
                    item["rationale"] = m.rationale
                    item["used_cap_ids"] = m.used_cap_ids
                    continue
                except ValueError:
                    pass
            # deterministic fallback
            best = item["evidence"][0]["score"] if item["evidence"] else 0.0
            status, conf = fallback_status(best)
            item["status"] = status
            item["confidence"] = conf
            item["rationale"] = "Similarity-threshold fallback judgment (LLM unavailable)."
            item["used_cap_ids"] = [item["evidence"][0]["cap_id"]] if item["evidence"] else []

    return enriched


def compliance_summary(matched: list[dict]) -> dict:
    total = len(matched)
    counts = {"PASS": 0, "PARTIAL": 0, "GAP": 0}
    mandatory_gaps = []
    for m in matched:
        counts[m["status"]] = counts.get(m["status"], 0) + 1
        if m["status"] == "GAP" and m.get("mandatory"):
            mandatory_gaps.append(m["text"])
    compliance_pct = (
        round(100 * (counts["PASS"] + 0.5 * counts["PARTIAL"]) / total, 1) if total else 0.0
    )
    return {
        "total": total,
        "counts": counts,
        "compliance_pct": compliance_pct,
        "mandatory_gaps": mandatory_gaps,
    }
