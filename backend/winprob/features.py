"""Shared feature engineering: bid-history rows and live workspaces map into
the same feature space so the trained model scores new bids directly."""
import numpy as np
import pandas as pd

from core import config

NUMERIC_FEATURES = ["est_score", "log_budget_m", "compliance_pct", "gaps_found",
                    "doc_pages", "response_time_hrs"]
SECTOR_FEATURES = [f"sector_{s.replace(' ', '_')}" for s in config.SECTORS]
FEATURE_NAMES = NUMERIC_FEATURES + SECTOR_FEATURES
# ablation set: what the model would see with no evaluation-score estimate
PREBID_FEATURE_NAMES = [f for f in FEATURE_NAMES if f != "est_score"]

# medians from the training data are filled in at train time and reused at predict time
DEFAULTS = {"est_score": 71.0, "log_budget_m": 5.0, "compliance_pct": 70.0,
            "gaps_found": 4.0, "doc_pages": 150.0, "response_time_hrs": 96.0}


def parse_budget_m(raw: str) -> float | None:
    import re
    if not raw:
        return None
    m = re.search(r"([\d,]+(?:\.\d+)?)\s*(B|M)?", str(raw), re.IGNORECASE)
    if not m:
        return None
    num = float(m.group(1).replace(",", ""))
    return num * 1000 if (m.group(2) or "M").upper() == "B" else num


def history_to_frame(csv_path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    out = pd.DataFrame()
    out["est_score"] = df["Score (%)"].astype(float)  # actual evaluation score in history
    out["log_budget_m"] = np.log1p(df["Budget"].map(parse_budget_m))
    out["compliance_pct"] = df["Compliance %"].astype(float)
    out["gaps_found"] = df["Gaps Found"].astype(float)
    out["doc_pages"] = df["Doc Pages"].astype(float)
    out["response_time_hrs"] = df["Response Time (hrs)"].astype(float)
    for s in config.SECTORS:
        out[f"sector_{s.replace(' ', '_')}"] = (df["Sector"] == s).astype(float)
    out["y"] = (df["Outcome"] == "Win").astype(int)
    return out


def workspace_to_features(profile: dict, summary: dict, doc: dict,
                          hours_to_deadline: float | None,
                          est_score: float) -> dict:
    """Build the live-bid feature dict (named, pre-vectorization).

    est_score comes from the Stage-B estimator (winprob/estimator.py); in the
    training history it is the actual awarded evaluation score.
    """
    budget_m = profile.get("budget_pkr_m")
    feats = {
        "est_score": float(est_score),
        "log_budget_m": float(np.log1p(budget_m)) if budget_m else DEFAULTS["log_budget_m"],
        "compliance_pct": float(summary.get("compliance_pct", DEFAULTS["compliance_pct"])),
        "gaps_found": float(summary.get("counts", {}).get("GAP", DEFAULTS["gaps_found"])),
        "doc_pages": float(doc.get("num_pages", DEFAULTS["doc_pages"])),
        "response_time_hrs": float(np.clip(hours_to_deadline, 24, 240))
        if hours_to_deadline else DEFAULTS["response_time_hrs"],
    }
    for s in config.SECTORS:
        feats[f"sector_{s.replace(' ', '_')}"] = 1.0 if profile.get("sector") == s else 0.0
    return feats


def vectorize(feats: dict) -> np.ndarray:
    return np.array([[feats[name] for name in FEATURE_NAMES]], dtype=float)
