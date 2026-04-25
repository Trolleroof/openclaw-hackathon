import Link from "next/link";
import type { Run } from "../lib/runs";
import { fmtDuration, fmtNumber, fmtRelative, statusVar } from "../lib/runs";
import { StatusDot } from "./StatusDot";
import { Sparkline } from "./Sparkline";

export function RunCard({ run }: { run: Run }) {
  const accent = statusVar(run.status);
  return (
    <Link
      href={`/runs/${run.shortId}`}
      className="group relative block border hairline transition-colors"
      style={{ background: "var(--surface)" }}
    >
      <span
        aria-hidden
        className="absolute left-0 top-0 bottom-0 w-[2px]"
        style={{ background: accent }}
      />
      <div className="p-5 flex flex-col gap-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <StatusDot status={run.status} />
              <span className="text-[10px] tracking-[0.18em] uppercase" style={{ color: accent }}>
                {run.status === "early_stop" ? "EARLY STOP" : run.status.toUpperCase()}
              </span>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="serif italic text-[24px] leading-none">run</span>
              <span className="text-[18px] tracking-tight" style={{ color: "var(--foreground)" }}>
                {run.shortId}
              </span>
            </div>
            <div className="mt-1 text-[11px]" style={{ color: "var(--muted)" }}>
              {run.template} · seed {run.seed}
            </div>
          </div>
          <div
            className="text-[10px] tracking-[0.18em] uppercase opacity-0 group-hover:opacity-100 transition-opacity"
            style={{ color: "var(--accent)" }}
          >
            open ↗
          </div>
        </div>

        <div className="-mx-1">
          <Sparkline values={run.curve} color={accent} width={320} height={48} />
        </div>

        <dl className="grid grid-cols-3 gap-3">
          <Cell label="mean_return" value={fmtNumber(run.meanReturn)} accent={run.status === "failed" || run.status === "early_stop"} />
          <Cell label="best" value={fmtNumber(run.bestReturn)} />
          <Cell label="steps" value={run.steps.toLocaleString()} />
        </dl>

        <div className="flex items-center justify-between text-[10px] tracking-[0.16em] uppercase" style={{ color: "var(--muted)" }}>
          <span>{fmtRelative(run.startedAt)}</span>
          <span>{fmtDuration(run.durationSec)}</span>
        </div>
      </div>
    </Link>
  );
}

function Cell({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[9px] tracking-[0.18em] uppercase" style={{ color: "var(--muted)" }}>
        {label}
      </span>
      <span
        className="text-[15px] tabular-nums"
        style={{ color: accent ? "var(--status-failed)" : "var(--foreground)" }}
      >
        {value}
      </span>
    </div>
  );
}
