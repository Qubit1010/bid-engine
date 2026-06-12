"""Win-probability stack: estimator behavior, summary math, trained-model quality gate."""
import json

from core import config
from rag.matcher import compliance_summary
from winprob.estimator import budget_alignment, estimate_score, load_stats


def _summary(compliance_pct: float, gaps: list[str]) -> dict:
    return {"compliance_pct": compliance_pct, "mandatory_gaps": gaps,
            "counts": {"PASS": 0, "PARTIAL": 0, "GAP": len(gaps)}, "total": 10}


def test_higher_compliance_raises_estimate():
    profile = {"sector": "Energy", "budget_pkr_m": 300}
    low = estimate_score(profile, _summary(40, []))["estimated_score"]
    high = estimate_score(profile, _summary(90, []))["estimated_score"]
    assert high > low


def test_mandatory_gaps_lower_estimate():
    profile = {"sector": "Energy", "budget_pkr_m": 300}
    clean = estimate_score(profile, _summary(75, []))["estimated_score"]
    gapped = estimate_score(profile, _summary(75, ["g1", "g2", "g3"]))["estimated_score"]
    assert gapped < clean


def test_budget_alignment_peaks_at_won_median():
    stats = load_stats()
    at_median = budget_alignment(stats["won_budget_median_m"], stats)
    far_away = budget_alignment(stats["won_budget_median_m"] * 8, stats)
    assert at_median == 1.0 and far_away < at_median


def test_unknown_budget_is_neutral():
    assert budget_alignment(None, load_stats()) == 0.5


def test_compliance_summary_math():
    matched = [
        {"status": "PASS", "mandatory": True, "text": "a"},
        {"status": "PARTIAL", "mandatory": False, "text": "b"},
        {"status": "GAP", "mandatory": True, "text": "c"},
        {"status": "GAP", "mandatory": False, "text": "d"},
    ]
    s = compliance_summary(matched)
    assert s["total"] == 4
    assert s["counts"] == {"PASS": 1, "PARTIAL": 1, "GAP": 2}
    assert s["compliance_pct"] == 37.5  # (1 + 0.5) / 4
    assert s["mandatory_gaps"] == ["c"]


def test_trained_model_quality_gate():
    metrics = json.loads((config.MODELS_DIR / "metrics.json").read_text())
    selected = metrics["selected_model"]
    assert metrics["candidates"][selected]["cv_auc"] >= 0.90
    assert metrics["n_samples"] == 120


def test_ablation_is_persisted_for_honesty():
    metrics = json.loads((config.MODELS_DIR / "metrics.json").read_text())
    assert "ablation_without_score" in metrics
    assert "score_auc_alone" in metrics
