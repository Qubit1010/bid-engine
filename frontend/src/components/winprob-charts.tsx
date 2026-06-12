"use client";

import { clsx } from "clsx";
import type { EstimatorComponent, ShapItem } from "@/lib/types";

/** SVG semicircle gauge for P(win). */
export function ProbabilityGauge({ probability, decision }: {
  probability: number;
  decision: "GO" | "CONDITIONAL_GO" | "NO_GO";
}) {
  const pct = Math.max(0, Math.min(1, probability));
  const color =
    decision === "GO" ? "#34d399" : decision === "CONDITIONAL_GO" ? "#fbbf24" : "#f87171";
  // semicircle: r=80, circumference of half-circle = PI * r
  const r = 80;
  const half = Math.PI * r;
  return (
    <div className="flex flex-col items-center">
      <svg width="200" height="118" viewBox="0 0 200 118">
        <path
          d="M 20 110 A 80 80 0 0 1 180 110"
          fill="none"
          stroke="#1e2733"
          strokeWidth="14"
          strokeLinecap="round"
        />
        <path
          d="M 20 110 A 80 80 0 0 1 180 110"
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={`${pct * half} ${half}`}
          style={{ transition: "stroke-dasharray 0.8s ease" }}
        />
        <text x="100" y="92" textAnchor="middle" fill="#f1f5f9"
          fontSize="34" fontWeight="700" fontFamily="var(--font-mono)">
          {(pct * 100).toFixed(0)}%
        </text>
        <text x="100" y="112" textAnchor="middle" fill="#64748b"
          fontSize="11" fontWeight="600" letterSpacing="1.5">
          P(WIN)
        </text>
      </svg>
    </div>
  );
}

/** Horizontal SHAP contribution bars, centered at zero. */
export function ShapBars({ items }: { items: ShapItem[] }) {
  const max = Math.max(...items.map((s) => Math.abs(s.impact)), 1e-6);
  return (
    <div className="space-y-2.5">
      {items.map((s) => {
        const w = (Math.abs(s.impact) / max) * 50; // % of half-width
        const pos = s.impact >= 0;
        return (
          <div key={s.feature} className="flex items-center gap-3 text-xs">
            <div className="w-44 shrink-0 truncate text-right text-slate-400" title={s.label}>
              {s.label}
            </div>
            <div className="relative h-4 flex-1 rounded bg-ink-800">
              <div className="absolute inset-y-0 left-1/2 w-px bg-ink-700" />
              <div
                className={clsx(
                  "absolute inset-y-0.5 rounded-sm",
                  pos ? "bg-emerald-500/70" : "bg-red-500/70",
                )}
                style={pos
                  ? { left: "50%", width: `${w}%` }
                  : { right: "50%", width: `${w}%` }}
              />
            </div>
            <div className={clsx(
              "w-14 shrink-0 font-mono",
              pos ? "text-emerald-400" : "text-red-400",
            )}>
              {pos ? "+" : ""}{s.impact.toFixed(3)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** Stage-B estimator component breakdown (score points). */
export function EstimatorBreakdown({ components, estimated }: {
  components: EstimatorComponent[];
  estimated: number;
}) {
  return (
    <div className="space-y-1.5">
      {components.map((c) => (
        <div key={c.name} className="flex items-baseline justify-between gap-4 text-xs">
          <div>
            <span className="text-slate-300">{c.name}</span>
            <span className="ml-2 text-slate-500">{c.detail}</span>
          </div>
          <span className={clsx(
            "shrink-0 font-mono font-semibold",
            c.points > 0 ? "text-emerald-400" : c.points < 0 ? "text-red-400" : "text-slate-400",
          )}>
            {c.points > 0 ? "+" : ""}{c.points.toFixed(1)}
          </span>
        </div>
      ))}
      <div className="mt-2 flex items-baseline justify-between border-t border-ink-700 pt-2 text-sm">
        <span className="font-medium text-slate-200">Estimated evaluation score</span>
        <span className="font-mono text-lg font-bold text-accent-400">
          {estimated.toFixed(1)} <span className="text-xs font-normal text-slate-500">/ 100</span>
        </span>
      </div>
    </div>
  );
}
