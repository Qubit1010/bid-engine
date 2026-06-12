"""Proposal draft generator: evidence-grounded sections with [CAP-xxx] citations.

Anti-hallucination contract: the LLM may only claim what the matched capability
evidence supports; where evidence is missing it must say so explicitly. Every
factual claim cites its capability record inline, so reviewers can trace
every sentence back to the library.
"""
import json
import re

from core import llm

SECTION_PLAN = [
    ("Executive Summary", "exec"),
    ("Understanding of Requirements", "understanding"),
    ("Technical Approach & Methodology", "approach"),
    ("Relevant Experience & Past Performance", "experience"),
    ("Team, Certifications & Quality Assurance", "team"),
    ("Compliance Statement", "compliance"),
    ("Project Plan & Timeline", "plan"),
    ("Value Proposition & Differentiators", "value"),
]

DRAFT_SYSTEM = """You are a senior proposal writer at the bidding company. Write the requested
proposal section in confident, specific, client-facing prose (180-320 words).
HARD RULES:
1. Ground every factual claim about the company in the EVIDENCE records provided
   (CAP-xxx past projects and the CO-PROFILE company fact sheet).
   Cite the record inline like [CAP-012] or [CO-PROFILE] immediately after the claim it supports.
2. NEVER invent projects, clients, certifications, numbers, or capabilities that are
   not in the evidence. If evidence is thin for something the RFP asks, write honestly:
   "Our library does not yet evidence X; we will address this via [partnering/hiring/etc.]".
3. Address the RFP's own requirements and language - mirror the issuer's terminology.
4. Plain professional prose. No bullet spam (max one short list per section), no markdown headers.
Respond with JSON: {"content": str}"""


def _evidence_block(matched: list[dict], statuses: tuple[str, ...]) -> tuple[str, str]:
    """Returns (requirements text, deduped evidence text) filtered to given statuses."""
    reqs, caps_seen, cap_lines = [], set(), []
    for m in matched:
        if m["status"] not in statuses:
            continue
        reqs.append(f"- ({m['status']}{', MANDATORY' if m.get('mandatory') else ''}) {m['text']}")
        for e in m.get("evidence", []):
            if e["cap_id"] in (m.get("used_cap_ids") or []) and e["cap_id"] not in caps_seen:
                caps_seen.add(e["cap_id"])
                cap_lines.append(
                    f"- {e['cap_id']}: {e['domain']} | {e['summary']} | cert: {e['certification']}"
                    f" | value {e['contract_value']} | {e['duration_months']} months"
                    f" | {e['client_type']} | completed {e['year_completed']}"
                )
    return "\n".join(reqs), "\n".join(cap_lines)


def section_inputs(key: str, profile: dict, matched: list[dict],
                   summary: dict, winprob: dict | None) -> dict:
    base = {
        "rfp_title": profile.get("title"),
        "issuer": profile.get("issuer"),
        "sector": profile.get("sector"),
        "rfp_summary": profile.get("summary"),
        "budget": profile.get("budget_raw") or "not stated",
        "submission_deadline": profile.get("submission_deadline"),
        "compliance_summary": summary,
    }
    pass_reqs, pass_caps = _evidence_block(matched, ("PASS", "PARTIAL"))
    gap_reqs, _ = _evidence_block(matched, ("GAP",))

    if key == "exec":
        base["instruction"] = ("Write the executive summary: who we are (from evidence), why we fit "
                               "this tender, our strongest proof points, and our commitment.")
    elif key == "understanding":
        base["instruction"] = ("Demonstrate we understand the issuer's needs and context. Paraphrase "
                               "the scope and what success looks like for them.")
    elif key == "approach":
        base["instruction"] = ("Describe our delivery methodology and how we will meet the technical "
                               "requirements, referencing evidence of having done similar work.")
    elif key == "experience":
        base["instruction"] = ("Present our most relevant past projects as proof of capability. Lead "
                               "with the closest sector/domain matches; include values and durations.")
    elif key == "team":
        base["instruction"] = ("Cover certifications, quality standards and team capability evidenced "
                               "in the library (ISO/CMMI/PMP etc.). Tie each to the RFP's asks.")
    elif key == "compliance":
        base["instruction"] = ("Write the compliance statement: we comply with the listed requirements; "
                               "state coverage honestly, including PARTIAL areas and how we close gaps.")
        base["gap_requirements"] = gap_reqs
    elif key == "plan":
        base["instruction"] = ("Propose a phased project plan and timeline consistent with the deadline "
                               "and typical durations in our evidence (use evidence durations as anchors).")
    else:  # value
        base["instruction"] = ("Why choose us: differentiation grounded in evidence (track record, "
                               "certifications, sector breadth). Confident, not boastful.")
        if winprob:
            base["win_analysis_top_factors"] = [s["label"] for s in winprob.get("shap", [])[:3]]

    base["requirements_addressed"] = pass_reqs[:6000]
    base["company_evidence"] = pass_caps[:6000]
    from rag.matcher import company_profile_text
    base["company_profile (cite as CO-PROFILE)"] = company_profile_text()
    return base


CITATION_RE = re.compile(r"\[(CAP-\d{3}|CO-PROFILE)\]")


def generate_sections(profile: dict, matched: list[dict], summary: dict,
                      winprob: dict | None) -> list[dict]:
    sections = []
    for title, key in SECTION_PLAN:
        payload = section_inputs(key, profile, matched, summary, winprob)
        user = f"SECTION TO WRITE: {title}\n\n" + json.dumps(payload, default=str)
        try:
            out = llm.complete_json(DRAFT_SYSTEM, user, bucket="draft")
            content = out.get("content", "").strip()
        except (RuntimeError, ValueError):
            content = (f"[Draft unavailable offline for '{title}'. "
                       "Re-run with connectivity to generate this section.]")
        sections.append({
            "title": title,
            "content": content,
            "citations": sorted(set(CITATION_RE.findall(content))),
        })
    return sections


def regenerate_section(title: str, profile: dict, matched: list[dict], summary: dict,
                       winprob: dict | None, feedback: str = "") -> dict:
    key = next((k for t, k in SECTION_PLAN if t == title), "exec")
    payload = section_inputs(key, profile, matched, summary, winprob)
    if feedback:
        payload["reviewer_feedback"] = feedback
        payload["instruction"] += " Revise per the reviewer feedback."
    user = f"SECTION TO WRITE: {title}\n\n" + json.dumps(payload, default=str)
    out = llm.complete_json(DRAFT_SYSTEM, user, bucket="draft")
    content = out.get("content", "").strip()
    return {"title": title, "content": content,
            "citations": sorted(set(CITATION_RE.findall(content)))}
