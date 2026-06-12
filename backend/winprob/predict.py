"""Win-probability inference + SHAP explanation + GO/NO-GO decision memo."""
import json
from datetime import datetime, timezone

import joblib
import numpy as np

from core import config, llm
from winprob import features
from winprob.train import BACKGROUND_PATH, METRICS_PATH, MODEL_PATH

GO_THRESHOLD = 0.55
CONDITIONAL_THRESHOLD = 0.40

_loaded = None


def load_model():
    global _loaded
    if _loaded is None:
        if not MODEL_PATH.exists():
            from winprob.train import train
            train()
        _loaded = joblib.load(MODEL_PATH)
    return _loaded


def shap_explain(model_bundle: dict, x: np.ndarray) -> list[dict]:
    import shap

    model, name = model_bundle["model"], model_bundle["name"]
    background = np.load(BACKGROUND_PATH)

    if name == "xgboost":
        explainer = shap.TreeExplainer(model)
        values = explainer.shap_values(x)[0]
    else:  # logistic regression pipeline: explain in scaled space
        scaler, clf = model.named_steps["scaler"], model.named_steps["clf"]
        explainer = shap.LinearExplainer(clf, scaler.transform(background))
        values = explainer.shap_values(scaler.transform(x))[0]

    out = []
    for fname, val, impact in zip(features.FEATURE_NAMES, x[0], values):
        out.append({
            "feature": fname,
            "value": round(float(val), 3),
            "impact": round(float(impact), 4),
        })
    out.sort(key=lambda d: abs(d["impact"]), reverse=True)
    return out


FEATURE_LABELS = {
    "est_score": "Expected evaluation score (estimated)",
    "log_budget_m": "Bid budget (log PKR millions)",
    "compliance_pct": "Compliance coverage %",
    "gaps_found": "Compliance gaps found",
    "doc_pages": "Tender document pages",
    "response_time_hrs": "Time available to respond (hrs)",
}


def humanize_feature(name: str) -> str:
    if name.startswith("sector_"):
        return f"Sector: {name[7:].replace('_', ' ')}"
    return FEATURE_LABELS.get(name, name)


def comparables(profile: dict, k: int = 5) -> list[dict]:
    """Most similar historical bids (same sector first, then budget distance)."""
    import pandas as pd
    df = pd.read_csv(config.DATA_DIR / "bid_history.csv")
    df["budget_m"] = df["Budget"].map(features.parse_budget_m)
    target_budget = profile.get("budget_pkr_m") or df["budget_m"].median()
    df["same_sector"] = (df["Sector"] == profile.get("sector")).astype(int)
    df["budget_dist"] = (df["budget_m"] - target_budget).abs()
    df = df.sort_values(["same_sector", "budget_dist"], ascending=[False, True]).head(k)
    return [
        {
            "bid_id": r["Bid ID"], "client": r["Client"], "sector": r["Sector"],
            "budget": r["Budget"], "outcome": r["Outcome"], "score": int(r["Score (%)"]),
            "compliance": int(r["Compliance %"]), "gaps": int(r["Gaps Found"]),
        }
        for _, r in df.iterrows()
    ]


def decide(probability: float, mandatory_gaps: list[str]) -> dict:
    if probability >= GO_THRESHOLD and not mandatory_gaps:
        decision, label = "GO", "Pursue this bid"
    elif probability >= CONDITIONAL_THRESHOLD or (probability >= GO_THRESHOLD and mandatory_gaps):
        decision, label = "CONDITIONAL_GO", "Pursue only if gaps can be closed"
    else:
        decision, label = "NO_GO", "Recommend passing on this bid"
    return {"decision": decision, "label": label,
            "thresholds": {"go": GO_THRESHOLD, "conditional": CONDITIONAL_THRESHOLD}}


MEMO_SYSTEM = """You are a bid director writing a crisp GO/NO-GO decision memo (max 180 words).
Use the data given. Structure: 1) Decision + win probability. 2) Top 3 factors driving the
probability (from SHAP impacts, plain language). 3) Mandatory gaps and what closing them takes.
4) One-line recommendation. No fluff, no markdown headers - short paragraphs."""


def decision_memo(profile: dict, probability: float, decision: dict,
                  shap_top: list[dict], mandatory_gaps: list[str],
                  summary: dict) -> str:
    payload = {
        "rfp_title": profile.get("title"),
        "sector": profile.get("sector"),
        "budget": profile.get("budget_raw") or "not stated",
        "win_probability": round(probability, 3),
        "estimated_evaluation_score": summary.get("estimated_score"),
        "decision": decision["decision"],
        "top_factors": [
            {"factor": humanize_feature(s["feature"]), "value": s["value"], "impact": s["impact"]}
            for s in shap_top[:5]
        ],
        "compliance": summary,
        "mandatory_gaps": mandatory_gaps[:6],
    }
    try:
        return llm.complete_text(MEMO_SYSTEM, json.dumps(payload), bucket="memo")
    except RuntimeError:
        top = ", ".join(f"{humanize_feature(s['feature'])} ({s['impact']:+.2f})"
                        for s in shap_top[:3])
        gaps = f" Mandatory gaps: {len(mandatory_gaps)}." if mandatory_gaps else ""
        return (
            f"Decision: {decision['decision']} at {probability:.0%} modeled win probability. "
            f"Key drivers: {top}.{gaps} "
            f"Compliance coverage {summary.get('compliance_pct')}% across {summary.get('total')} requirements."
        )


def assess_workspace(profile: dict, summary: dict, doc: dict) -> dict:
    from winprob import estimator

    bundle = load_model()

    hours = None
    if profile.get("submission_deadline"):
        try:
            dl = datetime.fromisoformat(profile["submission_deadline"]).replace(tzinfo=timezone.utc)
            hours = max((dl - datetime.now(timezone.utc)).total_seconds() / 3600, 0)
        except ValueError:
            hours = None

    est = estimator.estimate_score(profile, summary)
    feats = features.workspace_to_features(profile, summary, doc, hours,
                                           est_score=est["estimated_score"])
    x = features.vectorize(feats)
    probability = float(bundle["model"].predict_proba(x)[0, 1])
    shap_values = shap_explain(bundle, x)
    decision = decide(probability, summary.get("mandatory_gaps", []))
    memo = decision_memo(profile, probability, decision, shap_values,
                         summary.get("mandatory_gaps", []), summary)

    metrics = json.loads(METRICS_PATH.read_text()) if METRICS_PATH.exists() else {}
    return {
        "probability": round(probability, 4),
        "model": bundle["name"],
        "model_cv_auc": metrics.get("candidates", {}).get(bundle["name"], {}).get("cv_auc"),
        "estimator": {k: est[k] for k in ("estimated_score", "components")},
        "features": feats,
        "shap": [{**s, "label": humanize_feature(s["feature"])} for s in shap_values],
        "decision": decision,
        "memo": memo,
        "comparables": comparables(profile),
    }
