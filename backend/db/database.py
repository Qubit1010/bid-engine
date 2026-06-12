"""SQLite persistence layer. Per-call connections keep it thread-safe for
FastAPI background tasks without an ORM."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from core import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS workspaces (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  filename TEXT,
  filetype TEXT,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'created',
  pipeline TEXT,
  doc TEXT,
  profile TEXT,
  winprob TEXT,
  effort TEXT,
  error TEXT
);
CREATE TABLE IF NOT EXISTS requirements (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  idx INTEGER NOT NULL,
  text TEXT NOT NULL,
  category TEXT,
  mandatory INTEGER NOT NULL DEFAULT 0,
  source_page INTEGER,
  status TEXT,
  confidence REAL,
  rationale TEXT,
  evidence TEXT,
  overridden INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS draft_sections (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  idx INTEGER NOT NULL,
  title TEXT NOT NULL,
  content TEXT,
  citations TEXT,
  status TEXT NOT NULL DEFAULT 'draft'
);
CREATE TABLE IF NOT EXISTS capabilities (
  cap_id TEXT PRIMARY KEY,
  domain TEXT,
  summary TEXT,
  certification TEXT,
  year_completed INTEGER,
  contract_value TEXT,
  contract_value_m REAL,
  duration_months INTEGER,
  client_type TEXT
);
"""

JSON_COLS = {"pipeline", "doc", "profile", "winprob", "effort", "evidence", "citations"}


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    d = dict(row)
    for col in JSON_COLS:
        if col in d and isinstance(d[col], str) and d[col]:
            try:
                d[col] = json.loads(d[col])
            except json.JSONDecodeError:
                pass
    return d


def update_fields(table: str, row_id: str, **fields: Any) -> None:
    sets, vals = [], []
    for k, v in fields.items():
        if k in JSON_COLS and not isinstance(v, str) and v is not None:
            v = json.dumps(v)
        sets.append(f"{k} = ?")
        vals.append(v)
    vals.append(row_id)
    with connect() as conn:
        conn.execute(f"UPDATE {table} SET {', '.join(sets)} WHERE id = ?", vals)


# -- workspace helpers -------------------------------------------------------

def create_workspace(name: str, filename: str, filetype: str) -> dict:
    ws_id = new_id("ws")
    with connect() as conn:
        conn.execute(
            "INSERT INTO workspaces (id, name, filename, filetype, created_at, status)"
            " VALUES (?, ?, ?, ?, ?, 'created')",
            (ws_id, name, filename, filetype, now_iso()),
        )
    return get_workspace(ws_id)


def get_workspace(ws_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    return row_to_dict(row)


def list_workspaces() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, filename, filetype, created_at, status, pipeline, profile, winprob, effort"
            " FROM workspaces ORDER BY created_at DESC"
        ).fetchall()
    return [row_to_dict(r) for r in rows]


def delete_workspace(ws_id: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM workspaces WHERE id = ?", (ws_id,))


def get_requirements(ws_id: str) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM requirements WHERE workspace_id = ? ORDER BY idx", (ws_id,)
        ).fetchall()
    return [row_to_dict(r) for r in rows]


def replace_requirements(ws_id: str, reqs: list[dict]) -> list[dict]:
    with connect() as conn:
        conn.execute("DELETE FROM requirements WHERE workspace_id = ?", (ws_id,))
        for i, r in enumerate(reqs):
            conn.execute(
                "INSERT INTO requirements (id, workspace_id, idx, text, category, mandatory, source_page)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (new_id("req"), ws_id, i, r["text"], r.get("category"),
                 int(bool(r.get("mandatory"))), r.get("source_page")),
            )
    return get_requirements(ws_id)


def get_draft_sections(ws_id: str) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM draft_sections WHERE workspace_id = ? ORDER BY idx", (ws_id,)
        ).fetchall()
    return [row_to_dict(r) for r in rows]


def get_section(section_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM draft_sections WHERE id = ?", (section_id,)).fetchone()
    return row_to_dict(row)


def get_requirement(req_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM requirements WHERE id = ?", (req_id,)).fetchone()
    return row_to_dict(row)


def replace_draft_sections(ws_id: str, sections: list[dict]) -> list[dict]:
    with connect() as conn:
        conn.execute("DELETE FROM draft_sections WHERE workspace_id = ?", (ws_id,))
        for i, s in enumerate(sections):
            conn.execute(
                "INSERT INTO draft_sections (id, workspace_id, idx, title, content, citations, status)"
                " VALUES (?, ?, ?, ?, ?, ?, 'draft')",
                (new_id("sec"), ws_id, i, s["title"], s.get("content", ""),
                 json.dumps(s.get("citations", []))),
            )
    return get_draft_sections(ws_id)


def get_capabilities() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM capabilities ORDER BY cap_id").fetchall()
    return [dict(r) for r in rows]


def set_pipeline_step(ws_id: str, step: str, status: str, detail: str = "",
                      ms: int | None = None) -> None:
    """Upsert one step in the workspace's pipeline progress array."""
    ws = get_workspace(ws_id)
    pipeline = ws.get("pipeline") or []
    for entry in pipeline:
        if entry["step"] == step:
            entry.update(status=status, detail=detail, ms=ms)
            break
    else:
        pipeline.append({"step": step, "status": status, "detail": detail, "ms": ms})
    update_fields("workspaces", ws_id, pipeline=pipeline)
