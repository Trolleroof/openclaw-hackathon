"use client";

import Link from "next/link";
import { useState } from "react";
import {
  HERMES_API_BASE_URL,
  fmtDuration,
  fmtNumber,
  fmtRelative,
  liveRunStatus,
  statusLabel,
  statusVar,
  type LiveRun,
} from "../lib/runs";
import { StatusDot } from "./StatusDot";

function shortId(runId: string) {
  return runId.replace(/^run_/, "").slice(0, 8);
}

function template(config: Record<string, unknown>) {
  const env = (config.env_id as string | undefined) ?? "Apollo Labs";
  return env.replace("ApolloLabs/", "");
}

function since(start: string | null, end: string | null, durationSec: number | null) {
  if (durationSec != null) return fmtDuration(Math.max(0, Math.round(durationSec)));
  if (!start) return "—";
  const elapsed = (Date.now() - new Date(start).getTime()) / 1000;
  return fmtDuration(Math.max(0, Math.round(elapsed)));
}

export function LiveRunCard({ run }: { run: LiveRun }) {
  const status = liveRunStatus(run.status);
  const accent = statusVar(status);
  const id = shortId(run.run_id);
  const ppo = run.metrics?.ppo;
  const baseline = run.metrics?.random_baseline;
  const isRunning = status === "running";
  const beatsRandom = run.metrics?.ppo_beats_random;
  const [imgError, setImgError] = useState(false);

  const gifSrc =
    run.gif_url && !imgError
      ? `${HERMES_API_BASE_URL}${run.gif_url}?t=${run.ended_at ?? run.started_at ?? ""}`
      : null;

  const duration = since(run.started_at, run.ended_at, run.duration_sec);
  const seed = (run.config?.seed as number | undefined) ?? "—";
  const totalSteps = (run.config?.total_timesteps as number | undefined) ?? null;
  const evalEpisodes = (run.config?.eval_episodes as number | undefined) ?? null;

  return (
    <Link
      href={`/runs/${run.run_id}`}
      className="group card flex flex-col md:flex-row overflow-hidden transition-colors hover:border-[var(--line-strong)]"
    >
      <div
        className="relative shrink-0 w-full md:w-[260px] aspect-square md:aspect-auto md:h-[260px] flex items-center justify-center overflow-hidden"
        style={{ background: "var(--background)", borderRight: "1px solid var(--line)" }}
      >
        {gifSrc ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={gifSrc}
            alt={`${id} rollout`}
            className="w-full h-full object-contain"
            onError={() => setImgError(true)}
          />
        ) : (
          <RolloutPlaceholder running={isRunning} accent={accent} />
        )}
        <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2 py-1 rounded-full"
          style={{ background: "rgba(0,0,0,0.55)", border: "1px solid var(--line)" }}>
          <StatusDot status={status} />
          <span className="label" style={{ color: accent }}>
            {isRunning ? "LIVE" : statusLabel(status)}
          </span>
        </div>
        {beatsRandom === true && (
          <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded-full label"
            style={{ background: "var(--accent-soft)", color: "var(--accent)", border: "1px solid var(--accent)" }}>
            beats random
          </div>
        )}
      </div>

      <div className="flex-1 p-5 flex flex-col gap-4 min-w-0">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="mono text-[16px] tracking-tight truncate">{id}</div>
            <div className="mt-1 text-[12px] truncate" style={{ color: "var(--muted)" }}>
              {template(run.config)} · seed {String(seed)}
            </div>
          </div>
          <span
            className="text-[12px] opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
            style={{ color: "var(--accent)" }}
          >
            open →
          </span>
        </div>

        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Cell
            label="avg return"
            value={ppo?.avg_reward != null ? fmtNumber(ppo.avg_reward) : "—"}
            accent={accent}
          />
          <Cell
            label="success"
            value={
              ppo?.success_rate != null
                ? `${(ppo.success_rate * 100).toFixed(0)}%`
                : "—"
            }
          />
          <Cell
            label="steps"
            value={totalSteps != null ? totalSteps.toLocaleString() : "—"}
          />
          <Cell
            label="episodes"
            value={
              ppo?.episodes != null
                ? ppo.episodes.toLocaleString()
                : evalEpisodes != null
                ? evalEpisodes.toLocaleString()
                : "—"
            }
          />
        </dl>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <Cell
            label="path length"
            value={ppo?.avg_path_length != null ? fmtNumber(ppo.avg_path_length) : "—"}
            small
          />
          <Cell
            label="remaining dirt"
            value={
              ppo?.avg_remaining_dirt != null
                ? ppo.avg_remaining_dirt.toFixed(2)
                : "—"
            }
            small
          />
          <Cell
            label="vs random"
            value={
              baseline?.random_success_rate != null && ppo?.success_rate != null
                ? `${((ppo.success_rate - baseline.random_success_rate) * 100).toFixed(0)}pp`
                : "—"
            }
            small
          />
        </div>

        <div
          className="flex items-center justify-between text-[11px] pt-2 border-t hairline"
          style={{ color: "var(--muted)" }}
        >
          <span>
            {run.started_at
              ? fmtRelative(run.started_at)
              : run.ended_at
              ? fmtRelative(run.ended_at)
              : "—"}
          </span>
          <span className="mono tabular-nums">{duration}</span>
        </div>

        {run.error && (
          <p className="text-[11px] mono" style={{ color: "var(--status-failed)" }}>
            {run.error}
          </p>
        )}
      </div>
    </Link>
  );
}

function Cell({
  label,
  value,
  accent,
  small = false,
}: {
  label: string;
  value: string;
  accent?: string;
  small?: boolean;
}) {
  return (
    <div className="flex flex-col gap-0.5 min-w-0">
      <span className="label">{label}</span>
      <span
        className={`mono tabular-nums truncate ${small ? "text-[12px]" : "text-[15px]"}`}
        style={accent ? { color: accent } : undefined}
      >
        {value}
      </span>
    </div>
  );
}

function RolloutPlaceholder({ running, accent }: { running: boolean; accent: string }) {
  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <div
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage:
            "linear-gradient(var(--line) 1px, transparent 1px), linear-gradient(90deg, var(--line) 1px, transparent 1px)",
          backgroundSize: "20px 20px",
        }}
      />
      <div className="relative flex flex-col items-center gap-2">
        <div
          className={running ? "pulse-dot" : ""}
          style={{
            width: 14,
            height: 14,
            borderRadius: 999,
            background: accent,
            boxShadow: `0 0 24px ${accent}`,
          }}
        />
        <span className="label" style={{ color: "var(--muted)" }}>
          {running ? "capturing rollout…" : "no rollout yet"}
        </span>
      </div>
    </div>
  );
}
