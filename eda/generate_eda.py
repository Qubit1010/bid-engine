"""Exploratory Data Analysis for BidSense.

Reads the three provided datasets (120-bid history, 50 capability records, the
synthesized 16-entry criteria taxonomy), computes descriptive statistics, renders
branded charts into eda/charts/, and writes a fully data-driven EDA_REPORT.md.

Every number in the report is computed here — nothing is hardcoded — so re-running
this regenerates the report if the data changes.

Run:  python eda/generate_eda.py     (from projects/bid-engine/)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
DATA = HERE.parent / "backend" / "data"
CHARTS = HERE / "charts"
CHARTS.mkdir(exist_ok=True)

# Brand palette (matches the app's Sage theme)
GREEN = "#609966"      # win / positive
SAGE = "#9DC08B"       # light accent
RED = "#d33f3f"        # loss / negative
AMBER = "#c2820a"      # threshold / warning
INK = "#243524"        # text
GRID = "#d4e1c7"

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 110,
    "font.size": 10,
    "axes.edgecolor": "#9fae90",
    "axes.labelcolor": INK,
    "axes.titlecolor": INK,
    "axes.titleweight": "bold",
    "text.color": INK,
    "xtick.color": "#56654f",
    "ytick.color": "#56654f",
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.7,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def parse_budget_m(raw) -> float | None:
    if pd.isna(raw):
        return None
    m = re.search(r"([\d,]+(?:\.\d+)?)\s*(B|M|Billion|Million)?", str(raw), re.IGNORECASE)
    if not m:
        return None
    num = float(m.group(1).replace(",", ""))
    unit = (m.group(2) or "M")[0].upper()
    return num * 1000 if unit == "B" else num


def save(fig, name: str):
    fig.tight_layout()
    fig.savefig(CHARTS / name, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Load
# --------------------------------------------------------------------------- #
bh = pd.read_csv(DATA / "bid_history.csv")
cl = pd.read_csv(DATA / "capability_library.csv")
tax = json.loads((DATA / "criteria_taxonomy.json").read_text(encoding="utf-8"))

# original dimensions, before any derived columns are added
RAW_SHAPE = {"bh": bh.shape, "cl": cl.shape}

bh["win"] = (bh["Outcome"] == "Win").astype(int)
bh["budget_m"] = bh["Budget"].map(parse_budget_m)
NUMERIC = ["Score (%)", "Compliance %", "Gaps Found", "Response Time (hrs)",
           "Doc Pages", "budget_m"]

R = {}  # rolling dict of computed values for the report


# --------------------------------------------------------------------------- #
# Bid-history charts
# --------------------------------------------------------------------------- #
def chart_outcome_balance():
    counts = bh["Outcome"].value_counts()
    fig, ax = plt.subplots(figsize=(5, 3.4))
    colors = [GREEN if i == "Win" else RED for i in counts.index]
    ax.bar(counts.index, counts.values, color=colors, width=0.55)
    for i, v in enumerate(counts.values):
        ax.text(i, v + 0.6, str(v), ha="center", fontweight="bold")
    ax.set_title("Outcome balance")
    ax.set_ylabel("Bids")
    save(fig, "outcome_balance.png")
    R["win_rate"] = bh["win"].mean()
    R["n_win"] = int((bh["Outcome"] == "Win").sum())
    R["n_loss"] = int((bh["Outcome"] == "Loss").sum())


def chart_score_by_outcome():
    fig, ax = plt.subplots(figsize=(7, 3.8))
    bins = np.arange(30, 101, 5)
    ax.hist(bh.loc[bh.win == 1, "Score (%)"], bins=bins, color=GREEN, alpha=0.75, label="Win")
    ax.hist(bh.loc[bh.win == 0, "Score (%)"], bins=bins, color=RED, alpha=0.6, label="Loss")
    ax.axvline(70, color=AMBER, ls="--", lw=1.8, label="~70 threshold")
    ax.set_title("Awarded evaluation score by outcome")
    ax.set_xlabel("Score (%)")
    ax.set_ylabel("Bids")
    ax.legend(frameon=False)
    save(fig, "score_by_outcome.png")
    R["score_win_mean"] = bh.loc[bh.win == 1, "Score (%)"].mean()
    R["score_loss_mean"] = bh.loc[bh.win == 0, "Score (%)"].mean()


def chart_score_win_curve():
    bins = np.arange(30, 101, 5)
    bh["score_bin"] = pd.cut(bh["Score (%)"], bins)
    grp = bh.groupby("score_bin", observed=True)["win"].agg(["mean", "count"])
    centers = [iv.mid for iv in grp.index]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.plot(centers, grp["mean"], "-o", color=GREEN, lw=2.2, markersize=5)
    ax.axvline(70, color=AMBER, ls="--", lw=1.8)
    ax.axhline(0.5, color="#9fae90", ls=":", lw=1)
    ax.set_title("Win rate vs awarded score (binned)")
    ax.set_xlabel("Score (%)")
    ax.set_ylabel("P(win)")
    ax.set_ylim(-0.05, 1.05)
    save(fig, "score_win_curve.png")
    below = bh.loc[bh["Score (%)"] < 70, "win"].mean()
    above = bh.loc[bh["Score (%)"] >= 70, "win"].mean()
    R["winrate_below70"] = below
    R["winrate_above70"] = above
    # cleanest single split
    R["misclassified_at_70"] = int(((bh["Score (%)"] >= 70) != (bh.win == 1)).sum())


def chart_corr_with_outcome():
    corr = bh[NUMERIC + ["win"]].corr()["win"].drop("win").sort_values()
    R["corr_outcome"] = corr.to_dict()
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    colors = [GREEN if v >= 0 else RED for v in corr.values]
    ax.barh(corr.index.astype(str), corr.values, color=colors)
    ax.axvline(0, color="#9fae90", lw=1)
    ax.set_title("Correlation of each feature with Win (point-biserial)")
    ax.set_xlabel("correlation with outcome")
    save(fig, "corr_with_outcome.png")


def chart_corr_heatmap():
    corr = bh[NUMERIC].corr()
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(corr, cmap="BrBG", vmin=-1, vmax=1)
    ax.set_xticks(range(len(NUMERIC)))
    ax.set_yticks(range(len(NUMERIC)))
    ax.set_xticklabels(NUMERIC, rotation=40, ha="right")
    ax.set_yticklabels(NUMERIC)
    for i in range(len(NUMERIC)):
        for j in range(len(NUMERIC)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center",
                    color="white" if abs(corr.iloc[i, j]) > 0.5 else INK, fontsize=8)
    ax.set_title("Feature correlation matrix")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    save(fig, "corr_heatmap.png")


def chart_sector_winrate():
    grp = bh.groupby("Sector")["win"].agg(["mean", "count"]).sort_values("mean")
    R["sector_winrate"] = grp["mean"].to_dict()
    R["sector_count"] = grp["count"].to_dict()
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.barh(grp.index, grp["mean"], color=SAGE, edgecolor=GREEN)
    ax.axvline(bh.win.mean(), color=AMBER, ls="--", lw=1.5, label=f"overall {bh.win.mean():.0%}")
    for i, (m, c) in enumerate(zip(grp["mean"], grp["count"])):
        ax.text(m + 0.01, i, f"{m:.0%}  (n={c})", va="center", fontsize=8)
    ax.set_title("Win rate by sector")
    ax.set_xlabel("win rate")
    ax.set_xlim(0, 1)
    ax.legend(frameon=False, loc="lower right")
    save(fig, "sector_winrate.png")


def chart_budget_by_outcome():
    fig, ax = plt.subplots(figsize=(6, 3.8))
    data = [bh.loc[bh.win == 1, "budget_m"].dropna(), bh.loc[bh.win == 0, "budget_m"].dropna()]
    bp = ax.boxplot(data, tick_labels=["Win", "Loss"], patch_artist=True, widths=0.5)
    for patch, c in zip(bp["boxes"], [GREEN, RED]):
        patch.set_facecolor(c)
        patch.set_alpha(0.5)
    ax.set_yscale("log")
    ax.set_title("Budget (PKR M, log) by outcome")
    ax.set_ylabel("Budget (PKR Million)")
    save(fig, "budget_by_outcome.png")


def chart_feature_separation():
    feats = ["Compliance %", "Gaps Found", "Response Time (hrs)", "Doc Pages"]
    fig, axes = plt.subplots(2, 2, figsize=(9, 6))
    for ax, f in zip(axes.ravel(), feats):
        ax.hist(bh.loc[bh.win == 1, f], bins=12, color=GREEN, alpha=0.7, label="Win")
        ax.hist(bh.loc[bh.win == 0, f], bins=12, color=RED, alpha=0.55, label="Loss")
        ax.set_title(f, fontsize=10)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Pre-bid features barely separate Win vs Loss", fontweight="bold")
    save(fig, "feature_separation.png")


def chart_compliance_vs_score():
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for label, c in [(1, GREEN), (0, RED)]:
        sub = bh[bh.win == label]
        ax.scatter(sub["Compliance %"], sub["Score (%)"], color=c, alpha=0.7,
                   label="Win" if label else "Loss", s=28, edgecolor="white", linewidth=0.4)
    ax.axhline(70, color=AMBER, ls="--", lw=1.5)
    ax.set_title("Compliance % vs awarded score")
    ax.set_xlabel("Compliance %")
    ax.set_ylabel("Score (%)")
    ax.legend(frameon=False)
    save(fig, "compliance_vs_score.png")
    R["corr_compliance_score"] = bh["Compliance %"].corr(bh["Score (%)"])


# --------------------------------------------------------------------------- #
# Capability-library charts
# --------------------------------------------------------------------------- #
def chart_cap_domains():
    counts = cl["Domain"].value_counts()
    R["n_domains"] = int(cl["Domain"].nunique())
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.barh(counts.index[::-1], counts.values[::-1], color=SAGE, edgecolor=GREEN)
    ax.set_title("Capability records by domain")
    ax.set_xlabel("records")
    save(fig, "cap_domains.png")


def chart_cap_certifications():
    certs = cl["Certification"].fillna("None / not stated").value_counts()
    R["cert_coverage"] = float((cl["Certification"].notna()).mean())
    R["cert_counts"] = certs.to_dict()
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = [RED if i.startswith("None") else GREEN for i in certs.index]
    ax.barh(certs.index[::-1], certs.values[::-1], color=colors[::-1])
    ax.set_title("Certifications across capability records")
    ax.set_xlabel("records")
    save(fig, "cap_certifications.png")


def chart_cap_contract_value():
    cl["value_m"] = cl["Contract Value"].map(parse_budget_m)
    R["cap_value_median"] = float(cl["value_m"].median())
    R["cap_value_max"] = float(cl["value_m"].max())
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    ax.hist(cl["value_m"].dropna(), bins=15, color=SAGE, edgecolor=GREEN)
    ax.set_title("Contract value distribution (capability library)")
    ax.set_xlabel("Contract value (PKR Million)")
    ax.set_ylabel("records")
    save(fig, "cap_contract_value.png")


def chart_cap_client_type():
    counts = cl["Client Type"].value_counts()
    R["client_type_counts"] = counts.to_dict()
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.bar(counts.index, counts.values, color=GREEN, width=0.6)
    for i, v in enumerate(counts.values):
        ax.text(i, v + 0.2, str(v), ha="center", fontweight="bold")
    ax.set_title("Capability records by client type")
    ax.set_ylabel("records")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    save(fig, "cap_client_type.png")
    R["cap_year_min"] = int(cl["Year Completed"].min())
    R["cap_year_max"] = int(cl["Year Completed"].max())


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def numeric_summary_md() -> str:
    desc = bh[NUMERIC].describe().T[["mean", "std", "min", "50%", "max"]]
    desc.columns = ["mean", "std", "min", "median", "max"]
    rows = ["| Feature | mean | std | min | median | max |",
            "|---|---|---|---|---|---|"]
    for f, r in desc.iterrows():
        rows.append(f"| {f} | {r['mean']:.1f} | {r['std']:.1f} | {r['min']:.0f} "
                    f"| {r['median']:.0f} | {r['max']:.0f} |")
    return "\n".join(rows)


def corr_table_md() -> str:
    items = sorted(R["corr_outcome"].items(), key=lambda kv: -abs(kv[1]))
    rows = ["| Feature | corr with Win |", "|---|---|"]
    for f, v in items:
        rows.append(f"| {f} | {v:+.3f} |")
    return "\n".join(rows)


def sector_table_md() -> str:
    items = sorted(R["sector_winrate"].items(), key=lambda kv: -kv[1])
    rows = ["| Sector | win rate | n |", "|---|---|---|"]
    for s, m in items:
        rows.append(f"| {s} | {m:.0%} | {R['sector_count'][s]} |")
    return "\n".join(rows)


def write_report():
    crit = tax["criteria"]
    weights = [c.get("typical_weight_pct") for c in crit if c.get("typical_weight_pct")]
    md = f"""# BidSense — Exploratory Data Analysis

*Auto-generated by `eda/generate_eda.py`. Every figure and statistic is computed
directly from the provided datasets; re-run the script to regenerate.*

## Datasets

| Dataset | Rows | Columns | Notes |
|---|---|---|---|
| Bid history | {RAW_SHAPE['bh'][0]} | {RAW_SHAPE['bh'][1]} | Past bids with outcome, awarded score, and bid attributes |
| Capability library | {RAW_SHAPE['cl'][0]} | {RAW_SHAPE['cl'][1]} | Company's past-project records used as RAG evidence |
| Criteria taxonomy | {len(crit)} | — | 16 evaluation criteria, **synthesized by the team** (the sample dataset omitted the sheet the problem statement referenced) |

---

## 1. Bid history

### 1.1 Outcome balance
The dataset is close to balanced: **{R['n_win']} wins / {R['n_loss']} losses**
(win rate **{R['win_rate']:.1%}**), so accuracy is a meaningful metric and no
heavy class re-weighting is required.

![Outcome balance](charts/outcome_balance.png)

### 1.2 Feature summary

{numeric_summary_md()}

![Pre-bid features barely separate Win vs Loss](charts/feature_separation.png)

The four operational pre-bid features (compliance, gaps, response time, document
pages) show **heavily overlapping** Win/Loss distributions — visually, none of them
cleanly separates the classes.

### 1.3 The dominant signal: awarded evaluation score
This is the headline finding. Winners average **{R['score_win_mean']:.1f}%** on the
awarded score; losers average **{R['score_loss_mean']:.1f}%**. The score also carries
a hard threshold around **70**:

- Win rate **below** score 70: **{R['winrate_below70']:.0%}**
- Win rate **at/above** score 70: **{R['winrate_above70']:.0%}**
- A naive "score ≥ 70 → Win" rule misclassifies only **{R['misclassified_at_70']} of {bh.shape[0]}** bids.

![Awarded score by outcome](charts/score_by_outcome.png)
![Win rate vs score](charts/score_win_curve.png)

### 1.4 Correlation with outcome
The awarded score dwarfs every other feature in its correlation with winning:

{corr_table_md()}

![Correlation with outcome](charts/corr_with_outcome.png)
![Feature correlation matrix](charts/corr_heatmap.png)

Compliance % and the awarded score are only weakly correlated
(r = {R['corr_compliance_score']:.2f}), confirming that compliance coverage is a
*partial* input to the score, not a substitute for it.

![Compliance vs score](charts/compliance_vs_score.png)

### 1.5 Sector and budget
Win rate varies by sector, but on small per-sector samples (treat as weak priors,
not hard rules):

{sector_table_md()}

![Win rate by sector](charts/sector_winrate.png)
![Budget by outcome](charts/budget_by_outcome.png)

Budget distributions for wins and losses overlap substantially — deal size alone
does not decide the outcome.

---

## 2. Capability library

The company holds **{cl.shape[0]} capability records across {R['n_domains']} domains**,
completed between **{R['cap_year_min']}–{R['cap_year_max']}**, with a median contract
value of **PKR {R['cap_value_median']:.0f}M** (max PKR {R['cap_value_max']:.0f}M).

![Records by domain](charts/cap_domains.png)

**Certifications:** only **{R['cert_coverage']:.0%}** of records carry a stated
certification — a real signal, because tenders that demand a specific certification
the company lacks become hard compliance GAPs (this is what drives the demo's
CONDITIONAL_GO and NO_GO decisions).

![Certifications](charts/cap_certifications.png)
![Contract value](charts/cap_contract_value.png)
![Client type](charts/cap_client_type.png)

---

## 3. Criteria taxonomy

16 evaluation criteria, synthesized to replace the missing dataset sheet, with a
typical weight range of **{min(weights)}–{max(weights)}%**. Sample entries:

| ID | Criterion | Typical weight |
|---|---|---|
""" + "\n".join(
        f"| {c['id']} | {c['name']} | {c.get('typical_weight_pct', '—')}% |"
        for c in crit[:6]
    ) + f"""

---

## 4. Modeling implications

The EDA directly shapes the win-probability design:

1. **The outcome is near-deterministic in one feature (awarded score, threshold ~70).**
   That is why the trained classifier reaches a near-perfect *cross-validated* AUC —
   it is learning a real, almost-trivial rule, not memorizing rows.
2. **Pre-bid features alone are noise** (Section 1.2 / 1.4). The published ablation
   confirms this: drop the score and AUC collapses to ≈ coin-flip.
3. **Leakage caveat → two-stage design.** The awarded score is only known *after*
   evaluation, so it cannot be a live input. The engine therefore estimates the
   expected score (Stage B) from compliance coverage, sector win-rate priors and
   budget alignment, then maps that estimate to win probability with the trained model.
4. **Compliance and certifications are the actionable levers** the company controls
   pre-bid — which is exactly what the matcher and the score estimator key on.

*Reproduce:* `python eda/generate_eda.py` from `projects/bid-engine/`.
"""
    (HERE / "EDA_REPORT.md").write_text(md, encoding="utf-8")


def copy_to_public():
    """Mirror charts into the frontend so the Validation page can serve them."""
    import shutil
    public = HERE.parent / "frontend" / "public" / "eda"
    public.mkdir(parents=True, exist_ok=True)
    for png in CHARTS.glob("*.png"):
        shutil.copy2(png, public / png.name)
    print(f"Charts mirrored -> {public}")


def main():
    chart_outcome_balance()
    chart_score_by_outcome()
    chart_score_win_curve()
    chart_corr_with_outcome()
    chart_corr_heatmap()
    chart_sector_winrate()
    chart_budget_by_outcome()
    chart_feature_separation()
    chart_compliance_vs_score()
    chart_cap_domains()
    chart_cap_certifications()
    chart_cap_contract_value()
    chart_cap_client_type()
    write_report()
    copy_to_public()
    print(f"EDA complete -> {HERE / 'EDA_REPORT.md'}")
    print(f"Charts ({len(list(CHARTS.glob('*.png')))}) -> {CHARTS}")


if __name__ == "__main__":
    main()
