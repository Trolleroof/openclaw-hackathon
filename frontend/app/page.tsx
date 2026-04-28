"use client";

import { useEffect, useMemo, useState } from "react";
import { LiveRunCard } from "./components/LiveRunCard";
import { EmptyState } from "./components/EmptyState";
import { fetchLiveRuns, fmtDuration, fmtNumber, liveRunStatus, type LiveRun } from "./lib/runs";

const POLL_MS = 3000;

export default function HomePage() {
  const [runs, setRuns] = useState<LiveRun[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    const tick = async () => {
      try {
        const next = await fetchLiveRuns();
        if (cancelled) return;
        setRuns(next);
        setError(null);
        setLastUpdated(Date.now());
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load runs");
      }
    };

    tick();
    const interval = setInterval(tick, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const stats = useMemo(() => {
    const total = runs.length;
    const finished = runs.filter((r) => liveRunStatus(r.status) !== "running");
    const successes = finished.filter((r) => liveRunStatus(r.status) === "success").length;
    const successRate = finished.length
      ? `${Math.round((successes / finished.length) * 100)}%`
      : "—";
    const returns = runs
      .map((r) => r.metrics?.ppo?.avg_reward)
      .filter((v): v is number => typeof v === "number");
    const bestReturn = returns.length ? fmtNumber(Math.max(...returns)) : "—";
    const durations = runs
      .map((r) => r.duration_sec)
      .filter((v): v is number => typeof v === "number" && v > 0);
    const avgDuration = durations.length
      ? fmtDuration(Math.round(durations.reduce((a, b) => a + b, 0) / durations.length))
      : "—";
    const liveCount = runs.filter((r) => liveRunStatus(r.status) === "running").length;
    return { total, successRate, bestReturn, avgDuration, liveCount };
  }, [runs]);

  return (
    <div className="flex flex-col gap-8">
      <section className="flex items-end justify-between gap-4">
        <div>
          <span className="label">Dashboard</span>
          <h1 className="text-[32px] font-semibold tracking-tight mt-1">Runs</h1>
          <p className="text-[13px] mt-1" style={{ color: "var(--muted-strong)" }}>
            Read-only view of runs from the API. To start training or change data, clone this repository
            and run the stack locally with your own configuration.
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-2 text-[11px]" style={{ color: "var(--muted)" }}>
            <span
              className={stats.liveCount > 0 ? "pulse-dot" : ""}
              style={{
                display: "inline-block",
                width: 7,
                height: 7,
                borderRadius: 999,
                background:
                  stats.liveCount > 0 ? "var(--status-running)" : "var(--muted)",
              }}
            />
            <span className="label">
              {stats.liveCount > 0
                ? `${stats.liveCount} live`
                : lastUpdated
                ? "live"
                : "connecting…"}
            </span>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 md:grid-cols-4 card divide-x divide-y md:divide-y-0 divide-hairline">
        <Stat label="runs" value={stats.total.toString()} />
        <Stat label="success rate" value={stats.successRate} />
        <Stat label="best return" value={stats.bestReturn} />
        <Stat label="avg duration" value={stats.avgDuration} />
      </section>

      {error && runs.length === 0 ? (
        <EmptyState
          icon="!"
          title="Cannot reach Apollo Labs API"
          body={`${error} This console is read-only and only displays data from the configured API.`}
        />
      ) : runs.length === 0 ? (
        <EmptyState
          icon="+"
          title="No runs yet"
          body="There are no runs on this API yet. This site is read-only: clone the repo, configure .env locally, and start training on your machine to populate runs here."
        />
      ) : (
        <section className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {runs.map((r) => (
            <LiveRunCard key={r.run_id} run={r} />
          ))}
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-5 flex flex-col gap-1">
      <span className="label">{label}</span>
      <span className="text-[28px] font-semibold tracking-tight tabular-nums">{value}</span>
    </div>
  );
}
