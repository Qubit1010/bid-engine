"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft, Check, CheckCircle2, Circle, Download, FileText, Loader2,
  RefreshCw, AlertTriangle, Pencil, X,
} from "lucide-react";
import { api } from "@/lib/api";
import {
  RUNNING_STATUSES, type DraftSection, type Requirement, type Workspace,
} from "@/lib/types";
import { Badge, Button, Card, CardTitle, Stat } from "@/components/ui";
import {
  EstimatorBreakdown, ProbabilityGauge, ShapBars,
} from "@/components/winprob-charts";

const STEPS = [
  { key: "extract", label: "Extract requirements" },
  { key: "match", label: "Match capability library" },
  { key: "winprob", label: "Score win probability" },
  { key: "draft", label: "Draft proposal" },
];

const TABS = ["Overview", "Requirements", "Compliance", "Draft", "Win Probability"] as const;
type Tab = (typeof TABS)[number];

export default function WorkspacePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [ws, setWs] = useState<Workspace | null>(null);
  const [tab, setTab] = useState<Tab>("Overview");
  const [error, setError] = useState<string | null>(null);

  const running = ws ? RUNNING_STATUSES.includes(ws.status) : false;

  const load = useCallback(async () => {
    try {
      setWs(await api.getWorkspace(id));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!running && ws?.status !== "uploaded") return;
    const t = setInterval(load, 2500);
    return () => clearInterval(t);
  }, [running, ws?.status, load]);

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
        <AlertTriangle size={16} /> {error}
      </div>
    );
  }
  if (!ws) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Loader2 size={14} className="animate-spin" /> Loading workspace…
      </div>
    );
  }

  const decision = ws.winprob?.decision?.decision;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/" className="mb-2 inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300">
            <ArrowLeft size={12} /> Workspaces
          </Link>
          <h1 className="flex items-center gap-3 text-2xl font-semibold text-slate-100">
            {ws.name}
            {decision && ws.status === "ready" && (
              <Badge status={decision}>{decision.replace(/_/g, " ")}</Badge>
            )}
            {ws.status === "error" && <Badge status="error">pipeline error</Badge>}
          </h1>
          <p className="mt-1 flex items-center gap-2 text-[13px] text-slate-500">
            <FileText size={12} /> {ws.filename}
            {ws.profile?.issuer && <> · {ws.profile.issuer}</>}
          </p>
        </div>
        {ws.status === "ready" && (
          <div className="flex gap-2">
            <a href={`/api/workspaces/${ws.id}/export/compliance.csv`}>
              <Button variant="ghost"><Download size={13} /> Compliance CSV</Button>
            </a>
            <a href={`/api/workspaces/${ws.id}/export/docx`}>
              <Button><Download size={13} /> Proposal DOCX</Button>
            </a>
          </div>
        )}
      </div>

      {/* Pipeline stepper (while running or on error) */}
      {(running || ws.status === "uploaded" || ws.status === "error") && (
        <PipelineStepper ws={ws} />
      )}
      {ws.status === "error" && ws.error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          <AlertTriangle size={16} /> {ws.error}
          <Button variant="ghost" className="ml-auto" onClick={async () => {
            await api.runPipeline(ws.id); load();
          }}>
            <RefreshCw size={13} /> Retry
          </Button>
        </div>
      )}

      {/* Tabs */}
      {ws.status === "ready" && (
        <>
          <div className="flex gap-1 overflow-x-auto border-b border-ink-700/60">
            {TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`-mb-px shrink-0 cursor-pointer rounded-t-md border-b-2 px-4 py-2.5 text-sm font-medium transition-all duration-150 ${
                  tab === t
                    ? "border-accent-500 text-slate-100"
                    : "border-transparent text-slate-500 hover:bg-ink-800/60 hover:text-slate-300"
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          <div key={tab} className="animate-in">
            {tab === "Overview" && <OverviewTab ws={ws} />}
            {tab === "Requirements" && <RequirementsTab ws={ws} onChanged={load} />}
            {tab === "Compliance" && <ComplianceTab ws={ws} />}
            {tab === "Draft" && <DraftTab ws={ws} onChanged={load} />}
            {tab === "Win Probability" && <WinProbTab ws={ws} />}
          </div>
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */

function PipelineStepper({ ws }: { ws: Workspace }) {
  const byKey = new Map((ws.pipeline ?? []).map((p) => [p.step, p]));
  return (
    <Card>
      <CardTitle sub="Live analysis pipeline — each step persisted with timings">
        Pipeline
      </CardTitle>
      <div className="space-y-3">
        {STEPS.map((s) => {
          const p = byKey.get(s.key);
          return (
            <div key={s.key} className="flex items-center gap-3 text-sm">
              {p?.status === "done" ? (
                <CheckCircle2 size={18} className="text-emerald-400" />
              ) : p?.status === "running" ? (
                <Loader2 size={18} className="animate-spin text-accent-400" />
              ) : p?.status === "error" ? (
                <X size={18} className="text-red-400" />
              ) : (
                <Circle size={18} className="text-ink-700" />
              )}
              <span className={p ? "text-slate-200" : "text-slate-600"}>{s.label}</span>
              {p?.detail && <span className="text-xs text-slate-500">— {p.detail}</span>}
              {p?.ms != null && (
                <span className="ml-auto font-mono text-xs text-slate-500">
                  {(p.ms / 1000).toFixed(1)}s
                </span>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function OverviewTab({ ws }: { ws: Workspace }) {
  const p = ws.profile;
  const wp = ws.winprob;
  if (!p) return null;
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {/* Decision banner */}
      {wp && (
        <Card className="lg:col-span-3">
          <div className="flex flex-wrap items-center gap-x-10 gap-y-4">
            <div className="flex items-center gap-5">
              <ProbabilityGauge probability={wp.probability} decision={wp.decision.decision} />
              <div>
                <Badge status={wp.decision.decision} className="!text-sm !px-3 !py-1">
                  {wp.decision.decision.replace(/_/g, " ")}
                </Badge>
                <p className="mt-2 max-w-md text-xs leading-relaxed text-slate-400">
                  {wp.decision.label}
                </p>
              </div>
            </div>
            <div className="ml-auto grid grid-cols-2 gap-x-10 gap-y-4 sm:grid-cols-4">
              <Stat label="Est. score" value={wp.estimator.estimated_score.toFixed(1)} accent />
              <Stat label="Compliance" value={`${wp.compliance_summary.compliance_pct.toFixed(0)}%`} />
              <Stat label="Mandatory gaps" value={wp.compliance_summary.mandatory_gaps.length} />
              {ws.effort && (
                <Stat label="Effort saved" value={`${ws.effort.reduction_pct.toFixed(0)}%`} accent />
              )}
            </div>
          </div>
        </Card>
      )}

      <Card className="lg:col-span-2">
        <CardTitle>RFP Profile</CardTitle>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-4 text-sm">
          <div className="col-span-2">
            <dt className="text-xs text-slate-500">Title</dt>
            <dd className="mt-0.5 text-slate-200">{p.title}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Issuer</dt>
            <dd className="mt-0.5 text-slate-200">{p.issuer || "—"}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Sector</dt>
            <dd className="mt-0.5 text-slate-200">{p.sector || "—"}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Budget</dt>
            <dd className="mt-0.5 font-mono text-slate-200">
              {p.budget_raw || "not stated"}
              {p.budget_pkr_m != null && (
                <span className="ml-2 text-xs text-slate-500">≈ PKR {p.budget_pkr_m}M</span>
              )}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Submission deadline</dt>
            <dd className="mt-0.5 font-mono text-slate-200">{p.submission_deadline ?? "—"}</dd>
          </div>
          <div className="col-span-2">
            <dt className="text-xs text-slate-500">Summary</dt>
            <dd className="mt-0.5 leading-relaxed text-slate-300">{p.summary}</dd>
          </div>
        </dl>
      </Card>

      <div className="space-y-4">
        <Card>
          <CardTitle>Key Deadlines</CardTitle>
          {p.deadlines.length === 0 ? (
            <p className="text-xs text-slate-500">None extracted.</p>
          ) : (
            <ul className="space-y-2 text-xs">
              {p.deadlines.map((d, i) => (
                <li key={i} className="flex justify-between gap-3">
                  <span className="text-slate-400">{d.label}</span>
                  <span className="shrink-0 font-mono text-slate-200">{d.date ?? d.raw}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card>
          <CardTitle>Evaluation Criteria</CardTitle>
          {p.criteria.length === 0 ? (
            <p className="text-xs text-slate-500">None extracted.</p>
          ) : (
            <ul className="space-y-2">
              {p.criteria.map((c, i) => (
                <li key={i} className="text-xs">
                  <div className="flex justify-between gap-3">
                    <span className="text-slate-300">{c.name}</span>
                    {c.weight_pct != null && (
                      <span className="shrink-0 font-mono text-accent-400">{c.weight_pct}%</span>
                    )}
                  </div>
                  {c.weight_pct != null && (
                    <div className="mt-1 h-1 rounded bg-ink-800">
                      <div
                        className="h-1 rounded bg-accent-500/60"
                        style={{ width: `${Math.min(c.weight_pct, 100)}%` }}
                      />
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>
        {ws.effort && (
          <Card>
            <CardTitle>Effort Reduction</CardTitle>
            <div className="space-y-1 text-xs text-slate-400">
              <div className="flex justify-between">
                <span>Pipeline time</span>
                <span className="font-mono text-slate-200">{ws.effort.pipeline_seconds.toFixed(0)}s</span>
              </div>
              <div className="flex justify-between">
                <span>Manual baseline</span>
                <span className="font-mono text-slate-200">{ws.effort.manual_baseline_hours}h</span>
              </div>
              <div className="flex justify-between border-t border-ink-700 pt-1.5">
                <span className="text-slate-300">Reduction</span>
                <span className="font-mono font-semibold text-emerald-400">
                  {ws.effort.reduction_pct.toFixed(1)}%
                </span>
              </div>
              <p className="pt-1 text-[10px] text-slate-600">{ws.effort.baseline_basis}</p>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

function RequirementsTab({ ws, onChanged }: { ws: Workspace; onChanged: () => void }) {
  const [filter, setFilter] = useState<string>("ALL");
  const [open, setOpen] = useState<string | null>(null);
  const reqs = ws.requirements ?? [];
  const shown = filter === "ALL" ? reqs : reqs.filter((r) => r.status === filter);

  const counts: Record<string, number> = { ALL: reqs.length };
  for (const r of reqs) counts[r.status ?? ""] = (counts[r.status ?? ""] ?? 0) + 1;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {["ALL", "PASS", "PARTIAL", "GAP"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-3 py-1 text-xs font-medium ring-1 transition-colors ${
              filter === f
                ? "bg-accent-500/15 text-accent-400 ring-accent-500/40"
                : "bg-ink-900 text-slate-400 ring-ink-700 hover:text-slate-200"
            }`}
          >
            {f} {counts[f] != null && <span className="opacity-60">({counts[f] ?? 0})</span>}
          </button>
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border border-ink-700/60">
        <table className="w-full text-left text-sm">
          <thead className="bg-ink-900 text-[11px] uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-4 py-2.5 font-medium">Requirement</th>
              <th className="px-3 py-2.5 font-medium">Category</th>
              <th className="px-3 py-2.5 font-medium">Page</th>
              <th className="px-3 py-2.5 font-medium">Status</th>
              <th className="px-3 py-2.5 font-medium">Conf.</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-800">
            {shown.map((r) => (
              <RequirementRow
                key={r.id}
                r={r}
                open={open === r.id}
                onToggle={() => setOpen(open === r.id ? null : r.id)}
                onChanged={onChanged}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RequirementRow({ r, open, onToggle, onChanged }: {
  r: Requirement; open: boolean; onToggle: () => void; onChanged: () => void;
}) {
  return (
    <>
      <tr
        onClick={onToggle}
        className="cursor-pointer bg-ink-950/40 transition-colors hover:bg-ink-900"
      >
        <td className="px-4 py-3 text-[13px] leading-snug text-slate-300">
          {r.mandatory && (
            <span className="mr-1.5 rounded bg-red-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-red-400 ring-1 ring-red-500/30">
              M
            </span>
          )}
          {r.text}
        </td>
        <td className="px-3 py-3 text-xs text-slate-500">{r.category}</td>
        <td className="px-3 py-3 font-mono text-xs text-slate-500">
          {r.source_page ?? "—"}
        </td>
        <td className="px-3 py-3">
          {r.status && (
            <Badge status={r.status}>
              {r.status}{r.overridden ? " *" : ""}
            </Badge>
          )}
        </td>
        <td className="px-3 py-3 font-mono text-xs text-slate-500">
          {r.confidence != null ? r.confidence.toFixed(2) : "—"}
        </td>
      </tr>
      {open && (
        <tr className="bg-ink-900/60">
          <td colSpan={5} className="px-4 py-4">
            <div className="space-y-3 text-xs">
              {r.rationale && (
                <p className="leading-relaxed text-slate-400">
                  <span className="font-semibold text-slate-300">Rationale: </span>
                  {r.rationale}
                </p>
              )}
              {r.evidence.length > 0 && (
                <div>
                  <p className="mb-1.5 font-semibold text-slate-300">Retrieved evidence</p>
                  <div className="space-y-1.5">
                    {r.evidence.map((e) => (
                      <div
                        key={e.cap_id}
                        className={`rounded-lg border px-3 py-2 ${
                          r.used_cap_ids.includes(e.cap_id)
                            ? "border-accent-500/40 bg-accent-500/5"
                            : "border-ink-700/60 bg-ink-950/40"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-semibold text-accent-400">{e.cap_id}</span>
                          <span className="text-slate-400">{e.domain}</span>
                          {r.used_cap_ids.includes(e.cap_id) && (
                            <span className="text-[10px] text-accent-400">cited</span>
                          )}
                          <span className="ml-auto font-mono text-slate-600">
                            sim {e.score.toFixed(2)}
                          </span>
                        </div>
                        <p className="mt-1 text-slate-500">
                          {e.summary} · {e.certification} · {e.contract_value} · {e.client_type} · {e.year_completed}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex items-center gap-2 pt-1">
                <span className="text-slate-500">Analyst override:</span>
                {(["PASS", "PARTIAL", "GAP"] as const).map((s) => (
                  <Button
                    key={s}
                    variant="ghost"
                    className={r.status === s ? "!border-accent-500/50" : ""}
                    onClick={async () => {
                      await api.overrideRequirement(r.id, s);
                      onChanged();
                    }}
                  >
                    {s}
                  </Button>
                ))}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function ComplianceTab({ ws }: { ws: Workspace }) {
  const cs = ws.winprob?.compliance_summary;
  const reqs = ws.requirements ?? [];
  if (!cs) return null;
  const pct = cs.compliance_pct;
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-4">
        <Card><Stat label="Coverage" value={`${pct.toFixed(1)}%`} accent /></Card>
        <Card><Stat label="Pass" value={cs.counts.PASS} /></Card>
        <Card><Stat label="Partial" value={cs.counts.PARTIAL} /></Card>
        <Card><Stat label="Gaps" value={cs.counts.GAP} /></Card>
      </div>

      {/* stacked coverage bar */}
      <div className="flex h-3 overflow-hidden rounded-full">
        <div className="bg-emerald-500/80" style={{ width: `${(cs.counts.PASS / cs.total) * 100}%` }} />
        <div className="bg-amber-500/80" style={{ width: `${(cs.counts.PARTIAL / cs.total) * 100}%` }} />
        <div className="bg-red-500/80" style={{ width: `${(cs.counts.GAP / cs.total) * 100}%` }} />
      </div>

      {cs.mandatory_gaps.length > 0 && (
        <Card className="border-red-500/30">
          <CardTitle sub="These block a clean GO — close them or justify a no-bid.">
            Mandatory Gaps — Action Required
          </CardTitle>
          <ul className="space-y-2">
            {cs.mandatory_gaps.map((g, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                <AlertTriangle size={15} className="mt-0.5 shrink-0 text-red-400" />
                {g}
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card>
        <CardTitle sub="Sorted gaps-first so reviewers see risk immediately.">
          Compliance Matrix
        </CardTitle>
        <div className="space-y-1.5">
          {[...reqs]
            .sort((a, b) => {
              const w = { GAP: 0, PARTIAL: 1, PASS: 2 } as Record<string, number>;
              return (w[a.status ?? ""] ?? 3) - (w[b.status ?? ""] ?? 3)
                || Number(b.mandatory) - Number(a.mandatory);
            })
            .map((r) => (
              <div
                key={r.id}
                className="flex items-start gap-3 rounded-lg border border-ink-800 bg-ink-950/40 px-3 py-2 text-[13px]"
              >
                {r.status && <Badge status={r.status} className="mt-0.5 shrink-0">{r.status}</Badge>}
                <span className="leading-snug text-slate-300">
                  {r.mandatory && <span className="mr-1 font-semibold text-red-400">[M]</span>}
                  {r.text}
                </span>
                {r.used_cap_ids.length > 0 && (
                  <span className="ml-auto shrink-0 font-mono text-[11px] text-accent-400/80">
                    {r.used_cap_ids.join(", ")}
                  </span>
                )}
              </div>
            ))}
        </div>
      </Card>
    </div>
  );
}

function DraftTab({ ws, onChanged }: { ws: Workspace; onChanged: () => void }) {
  const sections = ws.sections ?? [];
  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-500">
        Every factual claim cites its evidence record inline —{" "}
        <span className="font-mono text-accent-400">[CAP-xxx]</span> for past projects,{" "}
        <span className="font-mono text-accent-400">[CO-PROFILE]</span> for company facts.
        Approve each section or regenerate with feedback.
      </p>
      {sections.map((s) => (
        <SectionCard key={s.id} s={s} onChanged={onChanged} />
      ))}
    </div>
  );
}

function SectionCard({ s, onChanged }: { s: DraftSection; onChanged: () => void }) {
  const [editing, setEditing] = useState(false);
  const [regenOpen, setRegenOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [text, setText] = useState(s.content);
  const [feedback, setFeedback] = useState("");

  const highlight = (content: string) =>
    content.split(/(\[(?:CAP-\d{3}|CO-PROFILE)\])/g).map((part, i) =>
      /^\[(?:CAP-\d{3}|CO-PROFILE)\]$/.test(part) ? (
        <span key={i} className="rounded bg-accent-500/15 px-1 font-mono text-[11px] font-semibold text-accent-400">
          {part}
        </span>
      ) : (
        <span key={i}>{part}</span>
      ),
    );

  return (
    <Card className={s.status === "approved" ? "border-emerald-500/30" : ""}>
      <div className="mb-3 flex items-center gap-3">
        <h3 className="text-sm font-semibold text-slate-100">{s.idx + 1}. {s.title}</h3>
        <Badge status={s.status}>{s.status}</Badge>
        {s.citations.length > 0 && (
          <span className="font-mono text-[10px] text-slate-600">
            {s.citations.length} citation{s.citations.length > 1 ? "s" : ""}
          </span>
        )}
        <div className="ml-auto flex gap-1.5">
          {!editing && (
            <>
              <Button variant="ghost" disabled={busy} onClick={() => setRegenOpen(!regenOpen)}>
                <RefreshCw size={12} /> Regenerate
              </Button>
              <Button variant="ghost" onClick={() => { setText(s.content); setEditing(true); }}>
                <Pencil size={12} /> Edit
              </Button>
              {s.status !== "approved" && (
                <Button
                  disabled={busy}
                  onClick={async () => {
                    setBusy(true);
                    await api.updateSection(s.id, { status: "approved" });
                    setBusy(false);
                    onChanged();
                  }}
                >
                  <Check size={12} /> Approve
                </Button>
              )}
            </>
          )}
        </div>
      </div>

      {regenOpen && !editing && (
        <div className="mb-3 flex gap-2">
          <input
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Optional feedback, e.g. 'lead with the government experience'"
            className="flex-1 rounded-lg border border-ink-700 bg-ink-950 px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:border-accent-500 focus:outline-none"
          />
          <Button
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await api.regenerateSection(s.id, feedback);
                setRegenOpen(false);
                setFeedback("");
                onChanged();
              } finally {
                setBusy(false);
              }
            }}
          >
            {busy ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
            Run
          </Button>
        </div>
      )}

      {editing ? (
        <div className="space-y-2">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            className="w-full rounded-lg border border-ink-700 bg-ink-950 px-3 py-2 text-[13px] leading-relaxed text-slate-200 focus:border-accent-500 focus:outline-none"
          />
          <div className="flex gap-2">
            <Button
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                await api.updateSection(s.id, { content: text });
                setBusy(false);
                setEditing(false);
                onChanged();
              }}
            >
              <Check size={12} /> Save
            </Button>
            <Button variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
          </div>
        </div>
      ) : (
        <p className="whitespace-pre-wrap text-[13px] leading-relaxed text-slate-300">
          {highlight(s.content)}
        </p>
      )}
    </Card>
  );
}

function WinProbTab({ ws }: { ws: Workspace }) {
  const wp = ws.winprob;
  if (!wp) return null;
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardTitle sub={`Trained ${wp.model} on 120 historical bids · CV AUC ${wp.model_cv_auc?.toFixed(2) ?? "—"}`}>
          Win Probability
        </CardTitle>
        <div className="flex justify-center py-2">
          <ProbabilityGauge probability={wp.probability} decision={wp.decision.decision} />
        </div>
        <p className="text-center text-xs text-slate-500">{wp.decision.label}</p>
      </Card>

      <Card>
        <CardTitle sub="Stage B — heuristic score estimator (the model's key input)">
          Estimated Evaluation Score
        </CardTitle>
        <EstimatorBreakdown
          components={wp.estimator.components}
          estimated={wp.estimator.estimated_score}
        />
      </Card>

      <Card>
        <CardTitle sub="SHAP values from the trained model — why this probability">
          Feature Contributions (SHAP)
        </CardTitle>
        <ShapBars items={wp.shap} />
      </Card>

      <Card>
        <CardTitle sub="Closest historical bids by sector + budget">
          Comparable Past Bids
        </CardTitle>
        <table className="w-full text-left text-xs">
          <thead className="text-[10px] uppercase tracking-wider text-slate-500">
            <tr>
              <th className="pb-2 font-medium">Bid</th>
              <th className="pb-2 font-medium">Sector</th>
              <th className="pb-2 font-medium">Budget</th>
              <th className="pb-2 font-medium">Score</th>
              <th className="pb-2 font-medium">Outcome</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-800">
            {wp.comparables.map((c) => (
              <tr key={c.bid_id}>
                <td className="py-2 font-mono text-slate-400">{c.bid_id}</td>
                <td className="py-2 text-slate-400">{c.sector}</td>
                <td className="py-2 font-mono text-slate-400">{c.budget}</td>
                <td className="py-2 font-mono text-slate-300">{c.score}</td>
                <td className="py-2">
                  <span className={c.outcome === "Win" ? "text-emerald-400" : "text-red-400"}>
                    {c.outcome}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card className="lg:col-span-2">
        <CardTitle sub="Auto-generated from the analysis — editable before circulation">
          GO / NO-GO Decision Memo
        </CardTitle>
        <p className="whitespace-pre-wrap text-[13px] leading-relaxed text-slate-300">
          {wp.memo}
        </p>
      </Card>
    </div>
  );
}
