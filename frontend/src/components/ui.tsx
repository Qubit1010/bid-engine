"use client";

import { clsx } from "clsx";

export function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={clsx("rounded-xl border border-ink-700/60 bg-ink-900 p-5", className)}>
      {children}
    </div>
  );
}

export function CardTitle({ children, sub }: { children: React.ReactNode; sub?: string }) {
  return (
    <div className="mb-4">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">{children}</h3>
      {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

const STATUS_STYLES: Record<string, string> = {
  PASS: "bg-emerald-500/15 text-emerald-400 ring-emerald-500/30",
  PARTIAL: "bg-amber-500/15 text-amber-400 ring-amber-500/30",
  GAP: "bg-red-500/15 text-red-400 ring-red-500/30",
  GO: "bg-emerald-500/15 text-emerald-400 ring-emerald-500/30",
  CONDITIONAL_GO: "bg-amber-500/15 text-amber-400 ring-amber-500/30",
  NO_GO: "bg-red-500/15 text-red-400 ring-red-500/30",
  approved: "bg-emerald-500/15 text-emerald-400 ring-emerald-500/30",
  draft: "bg-slate-500/15 text-slate-400 ring-slate-500/30",
  ready: "bg-emerald-500/15 text-emerald-400 ring-emerald-500/30",
  error: "bg-red-500/15 text-red-400 ring-red-500/30",
  running: "bg-accent-500/15 text-accent-400 ring-accent-500/30",
};

export function Badge({ status, children, className }: {
  status?: string; children: React.ReactNode; className?: string;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ring-1",
        STATUS_STYLES[status ?? ""] ?? "bg-ink-800 text-slate-300 ring-ink-700",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Button({ onClick, children, variant = "primary", disabled, className }: {
  onClick?: () => void;
  children: React.ReactNode;
  variant?: "primary" | "ghost" | "danger";
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40",
        variant === "primary" && "bg-accent-600 text-white hover:bg-accent-500",
        variant === "ghost" && "border border-ink-700 bg-transparent text-slate-300 hover:bg-ink-800",
        variant === "danger" && "border border-red-500/30 bg-red-500/10 text-red-400 hover:bg-red-500/20",
        className,
      )}
    >
      {children}
    </button>
  );
}

export function Stat({ label, value, accent }: { label: string; value: React.ReactNode; accent?: boolean }) {
  return (
    <div>
      <div className="text-[11px] font-medium uppercase tracking-wider text-slate-500">{label}</div>
      <div className={clsx("mt-0.5 font-mono text-lg font-semibold", accent ? "text-accent-400" : "text-slate-100")}>
        {value}
      </div>
    </div>
  );
}
