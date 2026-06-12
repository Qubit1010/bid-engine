"""Train the win-probability model on the 120-bid history.

Honest approach for n=120: compare XGBoost vs L2 logistic regression with
stratified 5-fold CV and ship whichever generalizes better. All metrics are
persisted to models/metrics.json and surfaced on the in-app Validation page.
"""
import json

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from core import config
from winprob import features

MODEL_PATH = config.MODELS_DIR / "winprob_model.joblib"
METRICS_PATH = config.MODELS_DIR / "metrics.json"
BACKGROUND_PATH = config.MODELS_DIR / "shap_background.npy"


def build_candidates() -> dict:
    return {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=1.0, max_iter=2000)),
        ]),
        "xgboost": XGBClassifier(
            n_estimators=120, max_depth=3, learning_rate=0.08,
            subsample=0.9, colsample_bytree=0.9, reg_lambda=2.0,
            eval_metric="logloss", random_state=42,
        ),
    }


def evaluate_candidates(X, y, cv) -> tuple[dict, str]:
    results, best_name, best_auc = {}, None, -1.0
    for name, model in build_candidates().items():
        proba = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]
        auc = roc_auc_score(y, proba)
        pred = (proba >= 0.5).astype(int)
        results[name] = {
            "cv_auc": round(float(auc), 4),
            "cv_accuracy": round(float((pred == y).mean()), 4),
            "confusion_matrix": confusion_matrix(y, pred).tolist(),  # [[tn,fp],[fn,tp]] out-of-fold
        }
        if auc > best_auc:
            best_name, best_auc = name, auc
    return results, best_name


def train(csv_path=None) -> dict:
    csv_path = csv_path or (config.DATA_DIR / "bid_history.csv")
    df = features.history_to_frame(csv_path)
    y = df["y"].values
    X_full = df[features.FEATURE_NAMES].values
    X_prebid = df[features.PREBID_FEATURE_NAMES].values

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    report: dict = {"n_samples": int(len(y)), "win_rate": round(float(y.mean()), 3),
                    "features": features.FEATURE_NAMES}

    report["candidates"], best_name = evaluate_candidates(X_full, y, cv)
    report["ablation_without_score"], _ = evaluate_candidates(X_prebid, y, cv)

    # score -> win curve for the validation page (the dataset's real signal)
    score = df["est_score"].values
    report["score_auc_alone"] = round(float(roc_auc_score(y, score)), 4)
    lr = LogisticRegression(max_iter=2000).fit(score.reshape(-1, 1), y)
    grid = np.linspace(30, 100, 36)
    report["score_win_curve"] = [
        {"score": round(float(s), 1),
         "p_win": round(float(lr.predict_proba([[s]])[0, 1]), 4)}
        for s in grid
    ]

    report["selected_model"] = best_name
    report["selection_rule"] = "highest stratified 5-fold cross-validated ROC-AUC"
    report["data_insight"] = (
        "EDA: outcome in the provided history is driven almost entirely by the awarded "
        "evaluation score (threshold ~70); pre-bid features alone are noise (see "
        "ablation_without_score). The engine therefore estimates the live bid's expected "
        "evaluation score from compliance coverage, sector win-rate priors and budget "
        "alignment (Stage B), and the trained model maps that estimate to win probability."
    )
    report["note"] = (
        "n=120 is small; out-of-fold metrics reported to avoid optimistic bias. "
        "Both candidates evaluated with identical folds (random_state=42)."
    )

    final = build_candidates()[best_name]
    final.fit(X_full, y)
    joblib.dump({"model": final, "name": best_name}, MODEL_PATH)

    from winprob import estimator
    estimator.build_stats(csv_path)

    # SHAP background sample (stratified subsample keeps explanations stable)
    rng = np.random.default_rng(42)
    idx = rng.choice(len(X_full), size=min(60, len(X_full)), replace=False)
    np.save(BACKGROUND_PATH, X_full[idx])

    # store medians for live-bid default imputation
    med = df[features.FEATURE_NAMES].median().to_dict()
    report["feature_medians"] = {k: round(float(v), 3) for k, v in med.items()}

    METRICS_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("selected_model", "candidates")}, indent=2))
    return report


if __name__ == "__main__":
    train()
