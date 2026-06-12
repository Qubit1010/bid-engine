"""LLM extraction pipeline: document pages -> validated RFPProfile + requirements.

Two passes:
  A) metadata pass over head+tail chunks (title, issuer, sector, budget,
     deadlines, evaluation criteria, Q&A sections, submission instructions)
  B) requirements pass over every chunk (mandatory/optional, category, page)
then merge, dedupe, pydantic-validate, and NER-normalize.
"""
import difflib
import json

from core import config, llm
from extract import ner
from extract.schemas import Requirement, RFPProfile

CHUNK_CHARS = 12_000

METADATA_SYSTEM = """You are an expert bid manager analyzing a tender/RFP/RFQ document.
Extract metadata precisely. Only state what the document supports - never invent values.
Respond with a single JSON object:
{
  "title": str,                    // official tender title
  "issuer": str,                   // issuing organization
  "sector": str,                   // EXACTLY one of: Construction, Education, Energy, Finance, Healthcare, IT Services, Logistics, Telecom
  "summary": str,                  // 2-3 sentence plain-language summary of the scope
  "budget_raw": str,               // budget/estimated cost as written, "" if absent
  "submission_deadline_raw": str,  // proposal submission deadline as written, "" if absent
  "deadlines": [{"label": str, "raw": str, "source_page": int}],   // ALL dated milestones (pre-bid meeting, queries, submission, opening, validity)
  "criteria": [{"name": str, "weight_pct": number|null, "description": str}],  // evaluation criteria with weights if stated
  "qa_items": [{"question": str, "section": str, "source_page": int}],  // questions/sections bidders must answer
  "submission_instructions": str   // format, copies, envelopes, portal, etc.
}"""

REQUIREMENTS_SYSTEM = """You are an expert bid manager extracting COMPLIANCE REQUIREMENTS from a tender/RFP document chunk.
A requirement is anything the bidder MUST or SHOULD provide, prove, or comply with
(eligibility, certifications, experience, financials, technical specs, deliverables, staffing, legal).
Rules:
- Extract each requirement as one self-contained sentence (compress long clauses).
- mandatory=true for MUST/shall/required/eligibility/disqualification clauses; false for should/preferred/desirable.
- category: one of Eligibility, Technical, Financial, Experience, Certification, Legal, Staffing, Delivery, Other.
- source_page: the [PAGE n] marker nearest above the clause.
- Skip boilerplate (definitions, general conditions of contract) unless it imposes a bidder obligation.
Respond with JSON: {"requirements": [{"text": str, "category": str, "mandatory": bool, "source_page": int}]}"""


def build_chunks(pages: list[dict]) -> list[str]:
    chunks, current, size = [], [], 0
    for p in pages:
        block = f"[PAGE {p['page']}]\n{p['text']}"
        current.append(block)
        size += len(block)
        if size >= CHUNK_CHARS:
            chunks.append("\n\n".join(current))
            current, size = [], 0
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def dedupe_requirements(reqs: list[dict]) -> list[dict]:
    kept: list[dict] = []
    for r in reqs:
        text = r.get("text", "").strip()
        if len(text) < 10:
            continue
        is_dup = False
        for k in kept:
            if difflib.SequenceMatcher(None, text.lower(), k["text"].lower()).ratio() > 0.88:
                # keep the stricter flag if duplicated
                k["mandatory"] = k["mandatory"] or bool(r.get("mandatory"))
                is_dup = True
                break
        if not is_dup:
            kept.append({
                "text": text,
                "category": r.get("category", "General"),
                "mandatory": bool(r.get("mandatory")),
                "source_page": r.get("source_page"),
            })
    return kept


def extract_profile(doc: dict) -> tuple[RFPProfile, list[Requirement]]:
    pages = doc["pages"]
    chunks = build_chunks(pages)

    # -- Pass A: metadata from head + tail ----------------------------------
    head = chunks[0]
    tail = chunks[-1] if len(chunks) > 1 else ""
    meta_input = head + ("\n\n[... document continues ...]\n\n" + tail if tail else "")
    meta = llm.complete_json(METADATA_SYSTEM, meta_input[:60_000], bucket="extract-meta")

    # -- Pass B: requirements from every chunk ------------------------------
    all_reqs: list[dict] = []
    for chunk in chunks:
        try:
            out = llm.complete_json(REQUIREMENTS_SYSTEM, chunk, bucket="extract-reqs")
            all_reqs.extend(out.get("requirements", []))
        except (RuntimeError, ValueError, json.JSONDecodeError):
            continue  # a failed chunk should not sink the whole extraction
    deduped = dedupe_requirements(all_reqs)

    # -- NER normalization ----------------------------------------------------
    deadlines = []
    for d in meta.get("deadlines", []) or []:
        deadlines.append({
            "label": d.get("label", ""),
            "raw": d.get("raw", ""),
            "date": ner.normalize_date(d.get("raw", "") or d.get("label", "")),
            "source_page": d.get("source_page"),
        })
    # independent regex scan catches anything the LLM missed
    llm_dates = {d["date"] for d in deadlines if d["date"]}
    for found in ner.scan_deadlines(pages):
        if found["date"] not in llm_dates:
            found["label"] = "[NER scan] " + found["label"]
            deadlines.append(found)

    submission_deadline = ner.normalize_date(meta.get("submission_deadline_raw", ""))
    if not submission_deadline:
        sub = [d for d in deadlines if "submi" in (d["label"] or "").lower()]
        submission_deadline = sub[0]["date"] if sub else None

    profile = RFPProfile(
        title=meta.get("title") or "Untitled RFP",
        issuer=meta.get("issuer", ""),
        sector=meta.get("sector", "IT Services"),
        summary=meta.get("summary", ""),
        budget_raw=meta.get("budget_raw", ""),
        budget_pkr_m=ner.normalize_pkr_millions(meta.get("budget_raw", "")),
        submission_deadline=submission_deadline,
        deadlines=deadlines,
        criteria=meta.get("criteria", []) or [],
        qa_items=meta.get("qa_items", []) or [],
        submission_instructions=meta.get("submission_instructions", ""),
    )

    requirements = []
    for r in deduped:
        try:
            requirements.append(Requirement(**r))
        except ValueError:
            continue
    return profile, requirements
