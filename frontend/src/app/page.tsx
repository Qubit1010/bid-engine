"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FileText, Loader2, Trash2, UploadCloud, ChevronRight, AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";
import { RUNNING_STATUSES, type Workspace } from "@/lib/types";
import { Badge, Button, Card } from "@/components/ui";

function fmtDate(iso: string) {
  try {
    return new Date(iso).toLocaleString("en-GB", {
      day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function HomePage() {
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<Workspace[] | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    try {
      setWorkspaces(await api.listWorkspaces());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load workspaces");
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [load]);

  const handleFile = useCallback(async (file: File) => {
    const ok = /\.(pdf|docx)$/i.test(file.name);
    if (!ok) {
      setError("Only PDF and DOCX files are supported.");
      return;
    }
    setError(null);
    setUploading(true);
    try {
      const name = file.name.replace(/\.(pdf|docx)$/i, "").replace(/[_-]+/g, " ");
      const ws = await api.createWorkspace(file, name);
      await api.runPipeline(ws.id);
      router.push(`/workspace/${ws.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setUploading(false);
    }
  }, [router]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const remove = async (id: string) => {
    await api.deleteWorkspace(id);
    load();
  };

  return (
    <div className="space-y-8">
      <div className="animate-in">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-100">
          Bid Workspaces
        </h1>
        <p className="mt-2 max-w-2xl text-[15px] leading-relaxed text-slate-400">
          Upload an RFP, RFQ or tender document. BidSense extracts requirements, checks
          compliance against your capability library, scores win probability and drafts the response.
        </p>
      </div>

      {/* Dropzone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => !uploading && fileInput.current?.click()}
        className={`group relative flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-14 transition-all duration-200 animate-in active:scale-[0.99] ${
          dragOver
            ? "scale-[1.01] border-accent-500 bg-accent-500/10 shadow-[0_0_44px_-6px_rgba(96,153,102,0.45)_inset]"
            : "border-ink-700 bg-ink-900/40 hover:border-accent-500/50 hover:bg-ink-900 hover:shadow-[0_0_36px_-12px_rgba(96,153,102,0.30)_inset]"
        }`}
      >
        <input
          ref={fileInput}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
            e.target.value = "";
          }}
        />
        {uploading ? (
          <>
            <Loader2 size={32} className="animate-spin text-accent-400" />
            <p className="mt-3 text-sm font-medium text-slate-300">
              Uploading & starting pipeline…
            </p>
          </>
        ) : (
          <>
            <UploadCloud
              size={32}
              className={dragOver ? "text-accent-400" : "text-slate-500 group-hover:text-slate-400"}
            />
            <p className="mt-3 text-sm font-medium text-slate-300">
              Drop an RFP here, or click to browse
            </p>
            <p className="mt-1 text-xs text-slate-500">PDF or DOCX · analysis starts automatically</p>
          </>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {/* Workspace list */}
      {workspaces === null ? (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 size={14} className="animate-spin" /> Loading workspaces…
        </div>
      ) : workspaces.length === 0 ? (
        <Card className="text-center text-sm text-slate-500">
          No workspaces yet. Upload your first RFP above — the demo documents live in{" "}
          <code className="rounded bg-ink-800 px-1.5 py-0.5 font-mono text-[12px] text-slate-400">
            demo-assets/
          </code>
        </Card>
      ) : (
        <div className="space-y-3">
          {workspaces.map((ws, i) => {
            const running = RUNNING_STATUSES.includes(ws.status);
            const decision = ws.winprob?.decision?.decision;
            return (
              <Link
                key={ws.id}
                href={`/workspace/${ws.id}`}
                style={{ animationDelay: `${Math.min(i, 8) * 45}ms` }}
                className="group flex animate-in items-center gap-4 rounded-xl border border-ink-700/60 bg-ink-900 px-5 py-4 shadow-[0_1px_2px_rgba(40,70,40,0.04)] transition-all duration-200 hover:-translate-y-0.5 hover:border-accent-500/50 hover:bg-ink-850 hover:shadow-[0_10px_28px_-14px_rgba(96,153,102,0.45)]"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-ink-800 text-slate-400">
                  <FileText size={18} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-semibold text-slate-100">
                      {ws.name}
                    </span>
                    {running && (
                      <Badge status="running" className="animate-pulse-soft">
                        <Loader2 size={10} className="animate-spin" /> {ws.status}
                      </Badge>
                    )}
                    {ws.status === "error" && <Badge status="error">error</Badge>}
                    {ws.status === "ready" && decision && (
                      <Badge status={decision}>{decision.replace(/_/g, " ")}</Badge>
                    )}
                  </div>
                  <div className="mt-0.5 flex items-center gap-3 text-xs text-slate-500">
                    <span className="truncate">{ws.filename}</span>
                    <span>·</span>
                    <span>{fmtDate(ws.created_at)}</span>
                    {ws.profile?.sector && (
                      <>
                        <span>·</span>
                        <span>{ws.profile.sector}</span>
                      </>
                    )}
                  </div>
                </div>
                {ws.winprob && (
                  <div className="hidden text-right sm:block">
                    <div className="font-mono text-xl font-semibold text-accent-400">
                      {(ws.winprob.probability * 100).toFixed(0)}%
                    </div>
                    <div className="text-[11px] uppercase tracking-wider text-slate-500">
                      P(win)
                    </div>
                  </div>
                )}
                <Button
                  variant="ghost"
                  className="!px-2 opacity-0 transition-opacity group-hover:opacity-100"
                  onClick={() => { }}
                >
                  <span
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      remove(ws.id);
                    }}
                    className="text-slate-500 hover:text-red-400"
                  >
                    <Trash2 size={14} />
                  </span>
                </Button>
                <ChevronRight size={16} className="text-slate-600 group-hover:text-slate-400" />
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
