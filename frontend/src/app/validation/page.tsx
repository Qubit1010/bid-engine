"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, FlaskConical, Loader2, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardTitle, Stat } from "@/components/ui";

interface CandidateMetrics {
  cv_auc: number;
  cv_accuracy: number;
  confusion_matrix: number[][];
}

interface ValidationData {
  model_metrics: {
    n_samples: number;
    win_rate: number;
    features: string[];
    candidates: Record<string, CandidateMetrics>;
    ablation_without_score: Record<string, CandidateMetrics>;
    score_auc_alone: number;
    score_win_curve: { score: number; p_win: number }[];
    selected_model: string;
    selection_rule: string;
    data_insight: string;
    note: string;
  };
  test_report: {
    passed: number;
    failed: number;
    total: number;
    duration_s: number;
    cases: { name: string; outcome: string }[];
  } | null;
  dataset: {
    bid_history_rows: number;
    capability_records: number;
    criteria_taxonomy_entries: number;
  };
}

function ConfusionMatrix({ cm }: { cm: number[][] }) {
  const labels = ["Loss", "Win"];
  return (
    <table className="text-center font-mono text-xs">
      <thead>
        <tr>
          <th className="p-1.5" />
          {labels.map((l) => (
            <th key={l} className="p-1.5 font-medium text-slate-500">pred {l}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {cm.map((row, i) => (
          <tr key={i}>
            <td className="p-1.5 text-right font-medium text-slate-500">true {labels[i]}</td>
            {row.map((v, j) => (
              <td
                key={j}
                className={`min-w-12 rounded p-1.5 ${
                  i === j ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                }`}
              >
                {v}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ScoreWinCurve({ points }: { points: { score: number; p_win: number }[] }) {
  if (points.length === 0) return null;
  const W = 460, H = 180, PAD = 36;
  const xs = points.map((p) => p.score);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const x = (s: number) => PAD + ((s - minX) / (maxX - minX)) * (W - 2 * PAD);
  const y = (p: number) => H - PAD - p * (H - 2 * PAD);
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${x(p.score).toFixed(1)} ${y(p.p_win).toFixed(1)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
      {/* gridlines */}
      {[0, 0.5, 1].map((g) => (
        <g key={g}>
          <line x1={PAD} x2={W - PAD} y1={y(g)} y2={y(g)} stroke="var(--chart-grid)" strokeWidth="1" />
          <text x={PAD - 6} y={y(g) + 3} textAnchor="end" fill="var(--chart-axis)" fontSize="9" fontFamily="var(--font-mono)">
            {(g * 100).toFixed(0)}%
          </text>
        </g>
      ))}
      {[40, 60, 70, 80].filter((s) => s >= minX && s <= maxX).map((s) => (
        <g key={s}>
          <line x1={x(s)} x2={x(s)} y1={PAD / 2} y2={H - PAD} stroke={s === 70 ? "var(--chart-threshold)" : "var(--chart-grid)"} strokeWidth="1" strokeDasharray={s === 70 ? "4 3" : undefined} opacity={s === 70 ? 0.55 : 1} />
          <text x={x(s)} y={H - PAD + 14} textAnchor="middle" fill={s === 70 ? "var(--chart-threshold)" : "var(--chart-axis)"} fontSize="9" fontFamily="var(--font-mono)">
            {s}
          </text>
        </g>
      ))}
      <path d={path} fill="none" stroke="var(--chart-line)" strokeWidth="2.5" strokeLinecap="round" />
      <text x={W - PAD} y={H - PAD + 26} textAnchor="end" fill="var(--chart-axis)" fontSize="9">
        evaluation score →
      </text>
    </svg>
  );
}

export default function ValidationPage() {
  const [data, setData] = useState<ValidationData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.validation()
      .then((d) => setData(d as unknown as ValidationData))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"));
  }, []);

  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!data) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Loader2 size={14} className="animate-spin" /> Loading validation data…
      </div>
    );
  }

  const m = data.model_metrics;
  const candidateNames = Object.keys(m.candidates);

  return (
    <div className="space-y-6">
      <div className="animate-in">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-100">Validation & Reliability</h1>
        <p className="mt-2 max-w-2xl text-[15px] leading-relaxed text-slate-400">
          Evidence, not claims: live model metrics from stratified cross-validation, the honest
          ablation study, and the automated test suite.
        </p>
      </div>

      {/* Dataset stats */}
      <div className="grid gap-4 sm:grid-cols-4">
        <Card><Stat label="Historical bids" value={data.dataset.bid_history_rows} /></Card>
        <Card><Stat label="Capability records" value={data.dataset.capability_records} /></Card>
        <Card><Stat label="Criteria taxonomy" value={data.dataset.criteria_taxonomy_entries} /></Card>
        <Card><Stat label="Historical win rate" value={`${(m.win_rate * 100).toFixed(0)}%`} accent /></Card>
      </div>

      {/* Data insight — the honest EDA finding */}
      <Card className="border-accent-500/30">
        <CardTitle sub="What exploratory analysis of the provided dataset actually shows">
          Key Data Insight
        </CardTitle>
        <p className="text-[13px] leading-relaxed text-slate-300">{m.data_insight}</p>
        <p className="mt-2 text-xs text-slate-500">{m.note}</p>
      </Card>

      {/* Model selection */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle sub={m.selection_rule}>Model Candidates (full features)</CardTitle>
          <div className="space-y-4">
            {candidateNames.map((name) => {
              const c = m.candidates[name];
              const selected = name === m.selected_model;
              return (
                <div
                  key={name}
                  className={`rounded-lg border p-3 ${
                    selected ? "border-accent-500/40 bg-accent-500/5" : "border-ink-700/60"
                  }`}
                >
                  <div className="mb-2 flex items-center gap-2 text-sm">
                    <span className="font-mono font-semibold text-slate-200">{name}</span>
                    {selected && (
                      <span className="rounded-full bg-accent-500/15 px-2 py-0.5 text-[10px] font-semibold text-accent-400 ring-1 ring-accent-500/30">
                        SELECTED
                      </span>
                    )}
                    <span className="ml-auto font-mono text-xs text-slate-400">
                      AUC {c.cv_auc.toFixed(3)} · acc {c.cv_accuracy.toFixed(3)}
                    </span>
                  </div>
                  <ConfusionMatrix cm={c.confusion_matrix} />
                </div>
              );
            })}
          </div>
          <p className="mt-4 border-t border-ink-700/60 pt-3 text-xs leading-relaxed text-slate-500">
            <span className="font-semibold text-slate-400">Why it isn&apos;t overfitting: </span>
            these are <span className="font-medium text-slate-400">out-of-fold</span> metrics — every
            row is scored by a model that never trained on it, so a perfect result reflects
            generalization across folds, not memorization (the linear model reaching {" "}
            {m.candidates["logistic_regression"]?.cv_auc.toFixed(2) ?? "~1.0"} on the same folds
            confirms it). It is near-perfect only because the awarded evaluation score nearly
            determines the outcome (see ablation). A live bid&apos;s score is not known yet — Stage B
            estimates it — so production predictions carry that estimate&apos;s uncertainty and are
            <span className="font-medium text-slate-400"> not 100% confident</span>.
          </p>
        </Card>

        <Card>
          <CardTitle sub="Same models WITHOUT the score estimate — pre-bid features alone are noise. This is why Stage B (score estimation) exists.">
            Ablation Study (honesty check)
          </CardTitle>
          <div className="space-y-4">
            {Object.entries(m.ablation_without_score).map(([name, c]) => (
              <div key={name} className="rounded-lg border border-ink-700/60 p-3">
                <div className="mb-2 flex items-center gap-2 text-sm">
                  <span className="font-mono font-semibold text-slate-200">{name}</span>
                  <span className="ml-auto font-mono text-xs text-red-400">
                    AUC {c.cv_auc.toFixed(3)} · acc {c.cv_accuracy.toFixed(3)}
                  </span>
                </div>
                <ConfusionMatrix cm={c.confusion_matrix} />
              </div>
            ))}
            <p className="text-xs leading-relaxed text-slate-500">
              Evaluation score alone reaches AUC {m.score_auc_alone.toFixed(2)} — the dataset&apos;s
              outcome is effectively deterministic on score. We report this instead of hiding it.
            </p>
          </div>
        </Card>
      </div>

      {/* Score → win curve */}
      <Card>
        <CardTitle sub="Fitted on the 120-bid history — the ~70-point threshold the procuring agencies apply is clearly visible">
          Evaluation Score → Win Probability
        </CardTitle>
        <ScoreWinCurve points={m.score_win_curve} />
      </Card>

      {/* Exploratory data analysis */}
      <Card>
        <CardTitle sub="Branded figures from eda/generate_eda.py — the evidence behind the model design">
          Dataset Exploration (EDA)
        </CardTitle>
        <div className="grid gap-5 sm:grid-cols-2">
          {[
            {
              src: "/eda/sector_winrate.png",
              title: "Win rate by sector",
              caption: "Per-sector win rates across the 120-bid history. Small samples — treat as weak priors, not rules.",
            },
            {
              src: "/eda/corr_heatmap.png",
              title: "Feature correlation matrix",
              caption: "Pairwise correlation of the numeric bid features used by the model.",
            },
            {
              src: "/eda/cap_domains.png",
              title: "Capability records by domain",
              caption: "50 records across 12 domains form the RAG evidence base the matcher searches.",
            },
            {
              src: "/eda/cap_contract_value.png",
              title: "Contract value distribution",
              caption: "Project sizes in the capability library (PKR Million).",
            },
            {
              src: "/eda/cap_client_type.png",
              title: "Records by client type",
              caption: "Government, private and international delivery footprint.",
            },
          ].map((c) => (
            <figure key={c.src} className="space-y-2">
              <div className="overflow-hidden rounded-lg border border-ink-700/70 bg-white">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={c.src} alt={c.title} className="w-full" loading="lazy" />
              </div>
              <figcaption className="text-xs leading-relaxed text-slate-500">
                <span className="font-medium text-slate-400">{c.title}.</span> {c.caption}
              </figcaption>
            </figure>
          ))}
        </div>
      </Card>

      {/* Test suite */}
      <Card>
        <CardTitle sub="pytest results captured at backend startup">
          Automated Test Suite
        </CardTitle>
        {data.test_report ? (
          <div className="space-y-3">
            <div className="flex items-center gap-6">
              <Stat label="Passed" value={data.test_report.passed} accent />
              <Stat label="Failed" value={data.test_report.failed} />
              <Stat label="Duration" value={`${data.test_report.duration_s.toFixed(1)}s`} />
            </div>
            <div className="grid gap-1.5 sm:grid-cols-2">
              {data.test_report.cases.map((c) => (
                <div key={c.name} className="flex items-center gap-2 text-xs">
                  {c.outcome === "passed" ? (
                    <CheckCircle2 size={13} className="shrink-0 text-emerald-400" />
                  ) : (
                    <XCircle size={13} className="shrink-0 text-red-400" />
                  )}
                  <span className="truncate font-mono text-slate-400">{c.name}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <FlaskConical size={15} />
            No test report yet — run <code className="rounded bg-ink-800 px-1.5 py-0.5 font-mono text-xs">pytest --report</code> in the backend.
          </div>
        )}
      </Card>
    </div>
  );
}
