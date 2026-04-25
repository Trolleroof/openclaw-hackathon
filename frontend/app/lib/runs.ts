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

// No mock data — wire to Hermes API in Phase 2.
export const runs: Run[] = [];

export function getRun(id: string): Run | undefined {
  return runs.find((r) => r.id === id || r.shortId === id);
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
