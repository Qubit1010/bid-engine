"""Stage B: estimate the live bid's expected evaluation score (0-100).

EDA on the 120-bid history shows outcome is driven almost entirely by the
evaluation score (threshold ~70); pre-bid features alone are noise (see the
ablation in models/metrics.json). So we estimate the score a live bid would
earn using exactly the heuristics the problem statement names — compliance
coverage, past win rate in similar domains, budget alignment — each component
visible to the bid manager, then feed it to the trained outcome model.
"""
import json

import numpy as np
import pandas as pd

from core import config
from winprob.features import parse_budget_m

STATS_PATH = config.MODELS_DIR / "estimator_stats.json"

# component weights (score points)
W_COMPLIANCE = 0.45      # per percentage point of compliance above/below history mean
COMPLIANCE_CAP = 15.0    # cap the compliance contribution at +/- this many points
SECTOR_SCALE = 30.0      # sector win-rate delta -> score points
BUDGET_SCALE = 8.0       # budget alignment [-0.5, 0.5] -> score points
GAP_PENALTY = 2.5        # per mandatory gap (capped)
GAP_PENALTY_CAP = 15.0


def build_stats(csv_path=None) -> dict:
    csv_path = csv_path or (config.DATA_DIR / "bid_history.csv")
    df = pd.read_csv(csv_path)
    df["budget_m"] = df["Budget"].map(parse_budget_m)
    won = df[df["Outcome"] == "Win"]
    stats = {
        "mean_score": round(float(df["Score (%)"].mean()), 2),
        "mean_compliance": round(float(df["Compliance %"].mean()), 2),
        "overall_win_rate": round(float((df["Outcome"] == "Win").mean()), 4),
        "sector_win_rate": {
            s: round(float((g["Outcome"] == "Win").mean()), 4)
            for s, g in df.groupby("Sector")
        },
        "won_budget_median_m": round(float(won["budget_m"].median()), 1),
        "won_budget_iqr_m": round(float(won["budget_m"].quantile(0.75)
                                        - won["budget_m"].quantile(0.25)), 1),
    }
    STATS_PATH.write_text(json.dumps(stats, indent=2))
    return stats


def load_stats() -> dict:
    if not STATS_PATH.exists():
        return build_stats()
    return json.loads(STATS_PATH.read_text())


def budget_alignment(budget_m: float | None, stats: dict) -> float:
    """1.0 = right at the median of our historically WON bids, decaying with
    IQR-scaled distance. None -> neutral 0.5."""
    if not budget_m:
        return 0.5
    dist = abs(budget_m - stats["won_budget_median_m"]) / max(stats["won_budget_iqr_m"], 1.0)
    return float(np.clip(1.0 - 0.35 * dist, 0.0, 1.0))


def estimate_score(profile: dict, summary: dict) -> dict:
    """Returns estimated evaluation score with a per-component breakdown."""
    stats = load_stats()
    base = stats["mean_score"]

    compliance_pct = float(summary.get("compliance_pct", stats["mean_compliance"]))
    comp_pts = float(np.clip(W_COMPLIANCE * (compliance_pct - stats["mean_compliance"]),
                             -COMPLIANCE_CAP, COMPLIANCE_CAP))

    sector = profile.get("sector", "")
    sector_wr = stats["sector_win_rate"].get(sector, stats["overall_win_rate"])
    sector_pts = SECTOR_SCALE * (sector_wr - stats["overall_win_rate"])

    align = budget_alignment(profile.get("budget_pkr_m"), stats)
    budget_pts = BUDGET_SCALE * (align - 0.5)

    n_mand_gaps = len(summary.get("mandatory_gaps", []))
    gap_pts = -min(GAP_PENALTY * n_mand_gaps, GAP_PENALTY_CAP)

    est = float(np.clip(base + comp_pts + sector_pts + budget_pts + gap_pts, 5, 95))
    return {
        "estimated_score": round(est, 1),
        "components": [
            {"name": "Historical baseline", "points": round(base, 1),
             "detail": f"Mean evaluation score across {120} past bids"},
            {"name": "Compliance coverage", "points": round(comp_pts, 1),
             "detail": f"{compliance_pct:.0f}% coverage vs {stats['mean_compliance']:.0f}% historical mean"},
            {"name": "Sector track record", "points": round(sector_pts, 1),
             "detail": f"{sector or 'Unknown'} win rate {sector_wr:.0%} vs {stats['overall_win_rate']:.0%} overall"},
            {"name": "Budget alignment", "points": round(budget_pts, 1),
             "detail": f"Alignment {align:.0%} with our won-bid budget profile"
                       f" (median PKR {stats['won_budget_median_m']:.0f}M)"},
            {"name": "Mandatory gap penalty", "points": round(gap_pts, 1),
             "detail": f"{n_mand_gaps} mandatory requirement(s) without evidence"},
        ],
        "stats": stats,
    }
