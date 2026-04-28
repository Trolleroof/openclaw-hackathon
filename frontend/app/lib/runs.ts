export type RunStatus = "success" | "running" | "failed" | "early_stop";

export type Run = {
  id: string;
  shortId: string;
  status: RunStatus;
  template: string;
  algo: string;
  startedAt: string; // ISO
  durationSec: number;
  steps: number;
  meanReturn: number;
  bestReturn: number;
  episodes: number;
  seed: number;
  checkpoint: string;
  notes: string;
  error?: string;
  config: Record<string, string | number | boolean>;
  curve: number[];
  logs: string[];
};

// No mock data — wire to Apollo Labs API in Phase 2.
export const runs: Run[] = [];

export function getRun(id: string): Run | undefined {
  return runs.find((r) => r.id === id || r.shortId === id);
}

export const HERMES_API_BASE_URL =
  process.env.NEXT_PUBLIC_HERMES_API_BASE_URL ?? "http://127.0.0.1:8000";

export type LiveRun = {
  run_id: string;
  status: string;
  started_at: string | null;
  ended_at: string | null;
  duration_sec: number | null;
  config: Record<string, unknown>;
  metrics: {
    ppo?: {
      avg_reward?: number;
      success_rate?: number;
      avg_remaining_dirt?: number;
      avg_path_length?: number;
      episodes?: number;
    };
    random_baseline?: {
      random_avg_reward?: number;
      random_success_rate?: number;
      random_avg_remaining_dirt?: number;
    };
    ppo_beats_random?: boolean;
  } | null;
  model_path: string | null;
  metrics_path: string | null;
  error: string | null;
  has_gif: boolean;
  gif_url: string | null;
};

export async function fetchLiveRuns(): Promise<LiveRun[]> {
  const res = await fetch(`${HERMES_API_BASE_URL}/api/runs`, {
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to load runs (${res.status})`);
  const data = await res.json();
  return (data?.runs ?? []) as LiveRun[];
}

export async function fetchLiveRun(runId: string): Promise<LiveRun | null> {
  const res = await fetch(`${HERMES_API_BASE_URL}/api/runs/${runId}`, {
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Failed to load run (${res.status})`);
  const raw = await res.json();
  return {
    run_id: raw.run_id,
    status: raw.status,
    started_at: raw.started_at ?? null,
    ended_at: raw.ended_at ?? null,
    duration_sec: raw.duration_sec ?? null,
    config: raw.config ?? {},
    metrics: raw.metrics ?? null,
    model_path: raw.model_path ?? null,
    metrics_path: raw.metrics_path ?? null,
    error: raw.error ?? null,
    has_gif: raw.has_gif ?? false,
    gif_url: raw.gif_url ?? null,
  };
}

export function liveRunStatus(s: string): RunStatus {
  if (s === "completed" || s === "success") return "success";
  if (s === "running") return "running";
  if (s === "early_stop") return "early_stop";
  return "failed";
}

export function statusLabel(s: RunStatus): string {
  switch (s) {
    case "success": return "Success";
    case "running": return "Running";
    case "failed": return "Failed";
    case "early_stop": return "Early stop";
  }
}

export function statusVar(s: RunStatus): string {
  switch (s) {
    case "success": return "var(--status-success)";
    case "running": return "var(--status-running)";
    case "failed": return "var(--status-failed)";
    case "early_stop": return "var(--status-stopped)";
  }
}

export function fmtDuration(sec: number): string {
  if (sec < 60) return `${sec}s`;
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  if (m < 60) return `${m}m ${s.toString().padStart(2, "0")}s`;
  const h = Math.floor(m / 60);
  return `${h}h ${(m % 60).toString().padStart(2, "0")}m`;
}

export function fmtRelative(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return `${Math.round(diff)}s ago`;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return `${Math.round(diff / 86400)}d ago`;
}

export function fmtNumber(n: number): string {
  if (Math.abs(n) >= 1000) return n.toLocaleString();
  return n.toFixed(2);
}
