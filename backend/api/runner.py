"""Pipeline orchestrator: extract -> match -> winprob -> draft, with live
progress persisted per step so the UI can render a stepper while it runs."""
import json
import time
import traceback

from core import config
from db import database
from draft import generator
from extract import pipeline as extract_pipeline
from rag import matcher
from winprob import predict

STEPS = ["extract", "match", "winprob", "draft"]


def _pace(t0: float) -> None:
    """Demo pacing: when LLM responses replay from cache, steps finish in
    milliseconds and the live stepper flashes past. DEMO_MIN_STEP_SECONDS
    (default 0 = off) floors each step's wall time so the audience can follow.
    Documented in the README; it never adds time to genuinely fresh runs."""
    floor = config.DEMO_MIN_STEP_SECONDS
    elapsed = time.time() - t0
    if floor > 0 and elapsed < floor:
        time.sleep(floor - elapsed)


def _flatten_requirement(row: dict) -> dict:
    """DB row -> API shape (evidence JSON holds items + used_cap_ids)."""
    ev = row.get("evidence") or {}
    if isinstance(ev, list):  # legacy shape safety
        ev = {"items": ev, "used": []}
    return {**row, "evidence": ev.get("items", []), "used_cap_ids": ev.get("used", []),
            "mandatory": bool(row.get("mandatory"))}


def get_workspace_detail(ws_id: str) -> dict | None:
    ws = database.get_workspace(ws_id)
    if not ws:
        return None
    ws["requirements"] = [_flatten_requirement(r) for r in database.get_requirements(ws_id)]
    ws["sections"] = database.get_draft_sections(ws_id)
    ws.pop("doc", None)  # page text is heavy; UI doesn't need it
    return ws


def run_pipeline(ws_id: str) -> None:
    ws = database.get_workspace(ws_id)
    if not ws or not ws.get("doc"):
        return
    doc = ws["doc"]
    t_start = time.time()
    try:
        # 1. extract ---------------------------------------------------------
        database.update_fields("workspaces", ws_id, status="extracting")
        database.set_pipeline_step(ws_id, "extract", "running")
        t0 = time.time()
        profile, requirements = extract_pipeline.extract_profile(doc)
        req_rows = database.replace_requirements(ws_id, [r.model_dump() for r in requirements])
        database.update_fields("workspaces", ws_id, profile=profile.model_dump())
        _pace(t0)
        database.set_pipeline_step(ws_id, "extract", "done",
                                   f"{len(req_rows)} requirements, {len(profile.criteria)} criteria",
                                   int((time.time() - t0) * 1000))

        # 2. match -----------------------------------------------------------
        database.update_fields("workspaces", ws_id, status="matching")
        database.set_pipeline_step(ws_id, "match", "running")
        t0 = time.time()
        matched = matcher.match_requirements(req_rows)
        with database.connect() as conn:
            for m in matched:
                conn.execute(
                    "UPDATE requirements SET status=?, confidence=?, rationale=?, evidence=? WHERE id=?",
                    (m["status"], m["confidence"], m["rationale"],
                     json.dumps({"items": m["evidence"], "used": m.get("used_cap_ids", [])}),
                     m["id"]),
                )
        summary = matcher.compliance_summary(matched)
        _pace(t0)
        database.set_pipeline_step(ws_id, "match", "done",
                                   f"{summary['counts']['PASS']} pass / "
                                   f"{summary['counts']['PARTIAL']} partial / "
                                   f"{summary['counts']['GAP']} gaps",
                                   int((time.time() - t0) * 1000))

        # 3. winprob ---------------------------------------------------------
        database.update_fields("workspaces", ws_id, status="scoring")
        database.set_pipeline_step(ws_id, "winprob", "running")
        t0 = time.time()
        winprob = predict.assess_workspace(profile.model_dump(), summary, doc)
        winprob["compliance_summary"] = summary
        database.update_fields("workspaces", ws_id, winprob=winprob)
        _pace(t0)
        database.set_pipeline_step(ws_id, "winprob", "done",
                                   f"P(win) {winprob['probability']:.0%} -> {winprob['decision']['decision']}",
                                   int((time.time() - t0) * 1000))

        # 4. draft -----------------------------------------------------------
        database.update_fields("workspaces", ws_id, status="drafting")
        database.set_pipeline_step(ws_id, "draft", "running")
        t0 = time.time()
        sections = generator.generate_sections(profile.model_dump(), matched, summary, winprob)
        database.replace_draft_sections(ws_id, sections)
        _pace(t0)
        database.set_pipeline_step(ws_id, "draft", "done",
                                   f"{len(sections)} sections drafted",
                                   int((time.time() - t0) * 1000))

        # effort metric -------------------------------------------------------
        elapsed_s = time.time() - t_start
        baseline_h = max(doc["num_pages"] * config.MANUAL_BASELINE_HOURS_PER_PAGE,
                         config.MANUAL_BASELINE_MIN_HOURS)
        database.update_fields("workspaces", ws_id, status="ready", effort={
            "pipeline_seconds": round(elapsed_s, 1),
            "manual_baseline_hours": baseline_h,
            "baseline_basis": f"{config.MANUAL_BASELINE_HOURS_PER_PAGE}h/page review+draft, min {config.MANUAL_BASELINE_MIN_HOURS}h (industry baseline)",
            "reduction_pct": round(100 * (1 - (elapsed_s / 3600) / baseline_h), 1),
        })
    except Exception as e:  # noqa: BLE001 - background task must record failures
        database.update_fields("workspaces", ws_id, status="error",
                               error=f"{e}\n{traceback.format_exc()[-1500:]}")
        for step in STEPS:
            pipeline = (database.get_workspace(ws_id) or {}).get("pipeline") or []
            for entry in pipeline:
                if entry["step"] == step and entry["status"] == "running":
                    database.set_pipeline_step(ws_id, step, "error", str(e)[:200])
