"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card } from "../../components/Card";
import { fetchRunReport, type RunReport } from "../../lib/reports";
import {
  HERMES_API_BASE_URL,
  fetchLiveRun,
  fmtDuration,
  fmtNumber,
  fmtRelative,
  liveRunStatus,
  statusLabel,
  statusVar,
  type LiveRun,
} from "../../lib/runs";

const POLL_MS = 3000;

export default function RunPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<RunReport | null>(null);
  const [run, setRun] = useState<LiveRun | null>(null);
  const [imgError, setImgError] = useState(false);
  const [pollAttempts, setPollAttempts] = useState(0);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    const tick = async () => {
      try {
        const liveRun = await fetchLiveRun(id);
        if (!cancelled && liveRun) setRun(liveRun);
      } catch {
        // Network blip — keep polling silently.
      }

      try {
        const r = await fetchRunReport(id);
        if (!cancelled) setReport(r);
      } catch {
        // Report not generated yet — fine while a run is still going.
      }

      if (!cancelled) setPollAttempts((n) => n + 1);
    };

    tick();
    const interval = setInterval(tick, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [id]);

  if (!run && !report) {
    const stillSearching = pollAttempts < 4;
    return (
      <div className="flex flex-col gap-4">
        <Link href="/" className="text-[12px]" style={{ color: "var(--muted-strong)" }}>← All runs</Link>
        <div className="flex flex-col gap-2">
          <span className="label">{stillSearching ? "loading run" : "run details unavailable"}</span>
          <p className="mono text-[14px] tracking-tight">{id}</p>
          <p className="text-[12px]" style={{ color: "var(--muted-strong)" }}>
            {stillSearching
              ? "Fetching run details from Hermes…"
              : "This run isn’t available on this dashboard yet. It may still be syncing, or it may have been removed."}
          </p>
          {!stillSearching && (
            <Link
              href="/"
              className="text-[12px] underline"
              style={{ color: "var(--muted-strong)" }}
            >
              View all runs →
            </Link>
          )}
        </div>
      </div>
    );
  }

  const status = run ? liveRunStatus(run.status) : report?.status === "success" ? "success" : report?.status === "failed" ? "failed" : "running";
  const accent = statusVar(status);
  const isRunning = status === "running";

  const runId = run?.run_id ?? report?.run_id ?? id;
  const config = (run?.config ?? report?.config ?? {}) as Record<string, unknown>;
  const template =
    (config.env_id as string | undefined)?.replace("ClawLab/", "") ??
    report?.template ??
    "—";
  const ppo = run?.metrics?.ppo;
  const baseline = run?.metrics?.random_baseline;
  const startedAt =
    run?.started_at ?? report?.started_at ?? run?.ended_at ?? report?.ended_at ?? null;
  const durationSec = run?.duration_sec ?? report?.duration_sec ?? null;
  const meanReturn = ppo?.avg_reward ?? report?.mean_return ?? null;
  const successRate = ppo?.success_rate ?? null;
  const totalSteps =
    (config.total_timesteps as number | undefined) ?? report?.steps ?? null;
  const episodes = ppo?.episodes ?? report?.episodes ?? null;
  const errorMessage = run?.error ?? report?.error ?? null;

  const gifSrc =
    run?.gif_url && !imgError
      ? `${HERMES_API_BASE_URL}${run.gif_url}?t=${run.ended_at ?? run.started_at ?? ""}`
      : null;

  const duration = durationSec != null ? fmtDuration(Math.round(durationSec)) : "—";
  const started = startedAt ? fmtRelative(startedAt) : "—";

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <Link href="/" className="text-[12px]" style={{ color: "var(--muted-strong)" }}>← All runs</Link>
      </div>

      <header className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <span
            className={isRunning ? "pulse-dot" : ""}
            style={{ display: "inline-block", width: 8, height: 8, borderRadius: 999, background: accent }}
          />
          <span className="label" style={{ color: accent }}>
            {isRunning ? "LIVE" : statusLabel(status)}
          </span>
          <span className="label">· {started} · {duration}</span>
        </div>
        <div className="flex items-baseline gap-3">
          <h1 className="mono text-[32px] tracking-tight">{runId}</h1>
          <span className="text-[14px]" style={{ color: "var(--muted-strong)" }}>{template}</span>
        </div>
        {report?.model_summary && (
          <p className="max-w-2xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
            {report.model_summary}
          </p>
        )}
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-6">
        <div
          className="card relative overflow-hidden flex items-center justify-center"
          style={{ aspectRatio: "1 / 1", background: "var(--background)" }}
        >
          {gifSrc ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={gifSrc}
              alt={`${runId} rollout`}
              className="w-full h-full object-contain"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="relative w-full h-full flex items-center justify-center">
              <div
                className="absolute inset-0 opacity-30"
                style={{
                  backgroundImage:
                    "linear-gradient(var(--line) 1px, transparent 1px), linear-gradient(90deg, var(--line) 1px, transparent 1px)",
                  backgroundSize: "24px 24px",
                }}
              />
              <div className="relative flex flex-col items-center gap-2">
                <div
                  className={isRunning ? "pulse-dot" : ""}
                  style={{
                    width: 18,
                    height: 18,
                    borderRadius: 999,
                    background: accent,
                    boxShadow: `0 0 32px ${accent}`,
                  }}
                />
                <span className="label" style={{ color: "var(--muted)" }}>
                  {isRunning ? "capturing rollout…" : "no rollout yet"}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 md:grid-cols-2 card divide-x divide-y md:divide-y-0 divide-hairline">
            <Metric
              label="avg return"
              value={meanReturn != null ? fmtNumber(meanReturn) : "—"}
            />
            <Metric
              label="success rate"
              value={successRate != null ? `${(successRate * 100).toFixed(0)}%` : "—"}
            />
            <Metric
              label="steps"
              value={totalSteps != null ? totalSteps.toLocaleString() : "—"}
            />
            <Metric
              label="episodes"
              value={episodes != null ? episodes.toLocaleString() : "—"}
            />
          </div>

          <div className="card p-5 grid grid-cols-2 gap-3 text-[12px]">
            <Row k="path length" v={ppo?.avg_path_length != null ? fmtNumber(ppo.avg_path_length) : "—"} />
            <Row k="remaining dirt" v={ppo?.avg_remaining_dirt != null ? ppo.avg_remaining_dirt.toFixed(2) : "—"} />
            <Row k="random success" v={baseline?.random_success_rate != null ? `${(baseline.random_success_rate * 100).toFixed(0)}%` : "—"} />
            <Row k="random return" v={baseline?.random_avg_reward != null ? fmtNumber(baseline.random_avg_reward) : "—"} />
            <Row k="beats random" v={run?.metrics?.ppo_beats_random == null ? "—" : run.metrics.ppo_beats_random ? "yes" : "no"} />
            <Row k="duration" v={duration} />
          </div>

          {errorMessage && (
            <div className="card p-4">
              <span className="label" style={{ color: "var(--status-failed)" }}>error</span>
              <p className="mt-1 mono text-[12px]" style={{ color: "var(--status-failed)" }}>
                {errorMessage}
              </p>
            </div>
          )}
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Config" hint={report?.algo ?? "PPO"}>
          <pre className="mono text-[12px] leading-[1.7] overflow-x-auto">
            {Object.entries(config)
              .map(([k, v]) => `${k.padEnd(20, " ")}  ${typeof v === "string" ? v : JSON.stringify(v)}`)
              .join("\n") || "—"}
          </pre>
        </Card>

        {report ? (
          <Card title="AgentMail" hint="end-of-run dispatch">
            <div className="flex flex-col gap-2 text-[12px]">
              <Row k="delivery" v={report.delivery_status} />
              {report.agentmail_message_id && <Row k="message id" v={report.agentmail_message_id} />}
              {report.agentmail_thread_id && <Row k="thread id" v={report.agentmail_thread_id} />}
              {report.delivery_error && (
                <p className="mt-1 text-[11px]" style={{ color: "var(--status-failed)" }}>
                  {report.delivery_error}
                </p>
              )}
              {report.artifact_links.checkpoint && (
                <Row k="checkpoint" v={report.artifact_links.checkpoint} />
              )}
            </div>
          </Card>
        ) : (
          <Card title="AgentMail" hint="end-of-run dispatch">
            <p className="text-[12px]" style={{ color: "var(--muted)" }}>
              Report will be generated and dispatched when the run finishes.
            </p>
          </Card>
        )}
      </div>

      {report?.markdown && (
        <Card title="Report" hint="markdown">
          <pre className="mono text-[12px] leading-[1.7] overflow-x-auto whitespace-pre-wrap">
            {report.markdown}
          </pre>
        </Card>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-5 flex flex-col gap-1">
      <span className="label">{label}</span>
      <span className="text-[28px] font-semibold tracking-tight tabular-nums">{value}</span>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="grid grid-cols-[120px_1fr] gap-4 border-b hairline pb-1.5">
      <span className="label">{k}</span>
      <span style={{ color: "var(--foreground)" }}>{v}</span>
    </div>
  );
}
