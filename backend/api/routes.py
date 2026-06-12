"""All API routes. Responses follow {ok, data?, error?}."""
import io
import json

from fastapi import APIRouter, BackgroundTasks, Form, UploadFile
from fastapi.responses import StreamingResponse

from api import runner
from core import config
from db import database
from export import docx_writer

router = APIRouter(prefix="/api")


def ok(data) -> dict:
    return {"ok": True, "data": data}


def err(message: str, code: int = 400):
    from fastapi import HTTPException
    raise HTTPException(status_code=code, detail=message)


@router.get("/health")
def health():
    return ok({"service": "bidsense", "status": "up"})


# -- workspaces ---------------------------------------------------------------

@router.get("/workspaces")
def list_workspaces():
    return ok(database.list_workspaces())


@router.post("/workspaces")
async def create_workspace(file: UploadFile, name: str = Form("")):
    from ingest import parser
    suffix = (file.filename or "upload.pdf").lower().rsplit(".", 1)[-1]
    if suffix not in ("pdf", "docx", "doc"):
        err("Only PDF and DOCX documents are supported")

    raw = await file.read()
    dest = config.UPLOADS_DIR / f"{database.new_id('doc')}.{suffix}"
    dest.write_bytes(raw)
    try:
        doc = parser.parse_document(dest)
    except ValueError as e:
        dest.unlink(missing_ok=True)
        err(str(e))

    ws = database.create_workspace(
        name=name or (file.filename or "Untitled RFP"),
        filename=file.filename or dest.name,
        filetype=suffix,
    )
    database.update_fields("workspaces", ws["id"], doc=doc, status="parsed")
    database.set_pipeline_step(ws["id"], "parse", "done",
                               f"{doc['num_pages']} pages, {doc['chars']:,} chars", None)
    return ok(database.get_workspace(ws["id"]) | {"doc": {"num_pages": doc["num_pages"]}})


@router.get("/workspaces/{ws_id}")
def get_workspace(ws_id: str):
    detail = runner.get_workspace_detail(ws_id)
    if not detail:
        err("Workspace not found", 404)
    return ok(detail)


@router.delete("/workspaces/{ws_id}")
def delete_workspace(ws_id: str):
    database.delete_workspace(ws_id)
    return ok({"deleted": ws_id})


@router.post("/workspaces/{ws_id}/run")
def run_workspace(ws_id: str, background: BackgroundTasks):
    ws = database.get_workspace(ws_id)
    if not ws:
        err("Workspace not found", 404)
    if ws["status"] in ("extracting", "matching", "scoring", "drafting"):
        return ok({"status": ws["status"], "note": "pipeline already running"})
    background.add_task(runner.run_pipeline, ws_id)
    database.update_fields("workspaces", ws_id, status="extracting", error=None)
    return ok({"status": "started"})


# -- human-in-the-loop review --------------------------------------------------

@router.patch("/requirements/{req_id}")
def override_requirement(req_id: str, payload: dict):
    req = database.get_requirement(req_id)
    if not req:
        err("Requirement not found", 404)
    fields = {}
    if payload.get("status") in ("PASS", "PARTIAL", "GAP"):
        fields["status"] = payload["status"]
        fields["overridden"] = 1
        fields["rationale"] = payload.get("rationale", "Manually overridden by bid manager.")
    if not fields:
        err("Nothing to update")
    database.update_fields("requirements", req_id, **fields)
    return ok(database.get_requirement(req_id))


@router.patch("/sections/{section_id}")
def update_section(section_id: str, payload: dict):
    section = database.get_section(section_id)
    if not section:
        err("Section not found", 404)
    fields = {}
    if "content" in payload:
        fields["content"] = payload["content"]
    if payload.get("status") in ("draft", "approved"):
        fields["status"] = payload["status"]
    if not fields:
        err("Nothing to update")
    database.update_fields("draft_sections", section_id, **fields)
    return ok(database.get_section(section_id))


@router.post("/sections/{section_id}/regenerate")
def regenerate_section(section_id: str, payload: dict | None = None):
    from draft import generator
    from rag import matcher as matcher_mod

    section = database.get_section(section_id)
    if not section:
        err("Section not found", 404)
    ws = database.get_workspace(section["workspace_id"])
    reqs = [runner._flatten_requirement(r) for r in database.get_requirements(ws["id"])]
    summary = matcher_mod.compliance_summary(
        [{**r, "evidence": r["evidence"]} for r in reqs]
    )
    feedback = (payload or {}).get("feedback", "")
    new = generator.regenerate_section(section["title"], ws.get("profile") or {},
                                       reqs, summary, ws.get("winprob"), feedback)
    database.update_fields("draft_sections", section_id, content=new["content"],
                           citations=new["citations"], status="draft")
    return ok(database.get_section(section_id))


# -- exports -------------------------------------------------------------------

@router.get("/workspaces/{ws_id}/export/docx")
def export_docx(ws_id: str):
    ws = database.get_workspace(ws_id)
    if not ws:
        err("Workspace not found", 404)
    reqs = [runner._flatten_requirement(r) for r in database.get_requirements(ws_id)]
    sections = database.get_draft_sections(ws_id)
    blob = docx_writer.build_proposal_docx(ws, reqs, sections)
    fname = f"proposal_{ws_id}.docx"
    return StreamingResponse(
        io.BytesIO(blob),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/workspaces/{ws_id}/export/compliance.csv")
def export_compliance(ws_id: str):
    ws = database.get_workspace(ws_id)
    if not ws:
        err("Workspace not found", 404)
    reqs = [runner._flatten_requirement(r) for r in database.get_requirements(ws_id)]
    csv_text = docx_writer.build_compliance_csv(reqs)
    return StreamingResponse(
        io.BytesIO(csv_text.encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="compliance_{ws_id}.csv"'},
    )


# -- validation ----------------------------------------------------------------

@router.get("/validation")
def validation():
    from winprob.train import METRICS_PATH

    metrics = json.loads(METRICS_PATH.read_text()) if METRICS_PATH.exists() else None
    test_report_path = config.MODELS_DIR / "test_report.json"
    tests = json.loads(test_report_path.read_text()) if test_report_path.exists() else None
    caps = database.get_capabilities()
    taxonomy = json.loads((config.DATA_DIR / "criteria_taxonomy.json").read_text())
    return ok({
        "model_metrics": metrics,
        "test_report": tests,
        "dataset": {
            "bid_history_rows": metrics.get("n_samples") if metrics else None,
            "capability_records": len(caps),
            "criteria_taxonomy_entries": len(taxonomy.get("criteria", [])),
        },
    })
