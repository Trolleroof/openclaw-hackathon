import Link from "next/link";
import type { Run } from "../lib/runs";
import { fmtDuration, fmtNumber, fmtRelative, statusLabel, statusVar } from "../lib/runs";
import { StatusDot } from "./StatusDot";
import { Sparkline } from "./Sparkline";

export function RunCard({ run }: { run: Run }) {
  const accent = statusVar(run.status);
  return (
    <Link
      href={`/runs/${run.shortId}`}
      className="group card p-5 flex flex-col gap-4 transition-colors hover:border-[var(--line-strong)]"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <StatusDot status={run.status} />
            <span className="label" style={{ color: accent }}>{statusLabel(run.status)}</span>
          </div>
          <div className="mt-2 mono text-[15px] tracking-tight">{run.shortId}</div>
          <div className="mt-1 text-[12px]" style={{ color: "var(--muted)" }}>
            {run.template} · seed {run.seed}
          </div>
        </div>
        <span
          className="text-[12px] opacity-0 group-hover:opacity-100 transition-opacity"
          style={{ color: "var(--accent)" }}
        >
          open →
        </span>
      </div>

      <Sparkline values={run.curve} color={accent} width={320} height={40} />

      <dl className="grid grid-cols-3 gap-3">
        <Cell label="return" value={fmtNumber(run.meanReturn)} />
        <Cell label="best" value={fmtNumber(run.bestReturn)} />
        <Cell label="steps" value={run.steps.toLocaleString()} />
      </dl>

      <div className="flex items-center justify-between text-[11px]" style={{ color: "var(--muted)" }}>
        <span>{fmtRelative(run.startedAt)}</span>
        <span className="mono">{fmtDuration(run.durationSec)}</span>
      </div>
    </Link>
  );
}

function Cell({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="label">{label}</span>
      <span className="mono text-[14px] tabular-nums">{value}</span>
    </div>
  );
}
