"""Shared fixtures + a JSON report plugin so the /validation page can show live results.

Run `pytest` normally; a machine-readable report is always written to
models/test_report.json (read by GET /api/validation).
"""
import json
import sys
import time
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from core import config  # noqa: E402

_results: list[dict] = []
_start = 0.0


def pytest_sessionstart(session):
    global _start
    _start = time.time()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        _results.append({"name": item.nodeid.split("::")[-1], "outcome": rep.outcome})


def pytest_sessionfinish(session, exitstatus):
    passed = sum(1 for r in _results if r["outcome"] == "passed")
    failed = sum(1 for r in _results if r["outcome"] != "passed")
    report = {
        "passed": passed,
        "failed": failed,
        "total": len(_results),
        "duration_s": round(time.time() - _start, 2),
        "cases": _results,
    }
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    (config.MODELS_DIR / "test_report.json").write_text(json.dumps(report, indent=2))
