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
  curve: number[]; // sparkline values
  logs: string[];
};

const now = new Date("2026-04-25T20:00:00Z").getTime();
const hour = 3_600_000;

function sparkline(seed: number, len = 32, drift = 0.05): number[] {
  let v = 0.1 + (seed % 7) * 0.02;
  const out: number[] = [];
  for (let i = 0; i < len; i++) {
    const noise = (Math.sin(seed * (i + 1) * 0.37) + Math.cos(seed * (i + 2) * 0.91)) * 0.07;
    v = Math.max(-0.2, Math.min(1.1, v + drift + noise));
    out.push(v);
  }
  return out;
}

function failingCurve(seed: number, len = 32): number[] {
  const c = sparkline(seed, len, 0.02);
  for (let i = Math.floor(len * 0.6); i < len; i++) c[i] = c[i] * 0.4;
  return c;
}

export const runs: Run[] = [
  {
    id: "run_2026-04-25_kw0c8x",
    shortId: "kw0c8x",
    status: "running",
    template: "roomba.flat-room.v3",
    algo: "PPO",
    startedAt: new Date(now - 0.4 * hour).toISOString(),
    durationSec: 1450,
    steps: 184_000,
    meanReturn: 0.61,
    bestReturn: 0.74,
    episodes: 412,
    seed: 7,
    checkpoint: "s3://hermes/ckpt/kw0c8x/step_180k.pt",
    notes: "Higher entropy bonus; testing collision-reset penalty rebalance.",
    config: {
      env: "roomba.flat-room.v3",
      algo: "PPO",
      lr: 3e-4,
      gamma: 0.99,
      gae_lambda: 0.95,
      clip_range: 0.2,
      ent_coef: 0.012,
      n_envs: 16,
      total_timesteps: 500_000,
      seed: 7,
    },
    curve: sparkline(7, 32, 0.03),
    logs: [
      "[20:00:14] supervisor: world generated from template roomba.flat-room.v3",
      "[20:00:15] worker[0..15]: env reset OK",
      "[20:01:02] ppo: step=8192 mean_return=-0.12 entropy=1.41",
      "[20:08:44] ppo: step=65536 mean_return=0.21 entropy=1.18",
      "[20:18:20] ppo: step=131072 mean_return=0.48 entropy=0.97",
      "[20:23:51] ppo: step=180224 mean_return=0.61 entropy=0.88",
    ],
  },
  {
    id: "run_2026-04-25_h2vq91",
    shortId: "h2vq91",
    status: "success",
    template: "roomba.flat-room.v2",
    algo: "PPO",
    startedAt: new Date(now - 6 * hour).toISOString(),
    durationSec: 4380,
    steps: 500_000,
    meanReturn: 0.82,
    bestReturn: 0.91,
    episodes: 1240,
    seed: 3,
    checkpoint: "s3://hermes/ckpt/h2vq91/best.pt",
    notes: "Best policy so far. Reward shaping unchanged from baseline.",
    config: {
      env: "roomba.flat-room.v2",
      algo: "PPO",
      lr: 3e-4,
      gamma: 0.99,
      gae_lambda: 0.95,
      clip_range: 0.2,
      ent_coef: 0.01,
      n_envs: 16,
      total_timesteps: 500_000,
      seed: 3,
    },
    curve: sparkline(3, 32, 0.045),
    logs: [
      "[14:01:00] supervisor: dispatched run h2vq91",
      "[15:13:22] ppo: step=500000 mean_return=0.82 (best=0.91)",
      "[15:14:00] supervisor: agentmail dispatched -> nikhi@ucsd.edu",
      "[15:14:01] nia: indexed run summary (3 lessons)",
    ],
  },
  {
    id: "run_2026-04-25_p83lqf",
    shortId: "p83lqf",
    status: "failed",
    template: "obstacle-grid.4x4",
    algo: "PPO",
    startedAt: new Date(now - 11 * hour).toISOString(),
    durationSec: 612,
    steps: 71_000,
    meanReturn: -0.18,
    bestReturn: 0.04,
    episodes: 188,
    seed: 11,
    checkpoint: "—",
    notes: "Collision penalty too steep; agent froze in starting cell.",
    error: "reward collapse: mean_return < -0.1 for 80 consecutive eval windows",
    config: {
      env: "obstacle-grid.4x4",
      algo: "PPO",
      lr: 5e-4,
      gamma: 0.99,
      gae_lambda: 0.92,
      clip_range: 0.2,
      ent_coef: 0.005,
      n_envs: 8,
      total_timesteps: 500_000,
      seed: 11,
    },
    curve: failingCurve(11, 32),
    logs: [
      "[09:00:00] supervisor: dispatched run p83lqf",
      "[09:08:18] ppo: step=70000 mean_return=-0.18",
      "[09:10:12] supervisor: TERMINATED (reward collapse guard)",
      "[09:10:15] agentmail: dispatched failure report",
    ],
  },
  {
    id: "run_2026-04-24_a44bbe",
    shortId: "a44bbe",
    status: "early_stop",
    template: "roomba.flat-room.v2",
    algo: "PPO",
    startedAt: new Date(now - 26 * hour).toISOString(),
    durationSec: 2810,
    steps: 320_000,
    meanReturn: 0.71,
    bestReturn: 0.78,
    episodes: 802,
    seed: 5,
    checkpoint: "s3://hermes/ckpt/a44bbe/step_300k.pt",
    notes: "Plateaued; stopped on patience=40 eval windows.",
    config: {
      env: "roomba.flat-room.v2",
      algo: "PPO",
      lr: 3e-4,
      gamma: 0.99,
      gae_lambda: 0.95,
      clip_range: 0.2,
      ent_coef: 0.01,
      n_envs: 16,
      total_timesteps: 500_000,
      seed: 5,
    },
    curve: sparkline(5, 32, 0.035),
    logs: [
      "[18:00:00] supervisor: dispatched run a44bbe",
      "[18:46:50] ppo: step=300000 mean_return=0.71",
      "[18:46:51] supervisor: EARLY_STOP (patience exceeded)",
    ],
  },
  {
    id: "run_2026-04-24_zx21r0",
    shortId: "zx21r0",
    status: "success",
    template: "roomba.flat-room.v1",
    algo: "PPO",
    startedAt: new Date(now - 34 * hour).toISOString(),
    durationSec: 3600,
    steps: 400_000,
    meanReturn: 0.76,
    bestReturn: 0.84,
    episodes: 980,
    seed: 1,
    checkpoint: "s3://hermes/ckpt/zx21r0/best.pt",
    notes: "Baseline reproduction. Matches reference within 2%.",
    config: {
      env: "roomba.flat-room.v1",
      algo: "PPO",
      lr: 3e-4,
      gamma: 0.99,
      gae_lambda: 0.95,
      clip_range: 0.2,
      ent_coef: 0.01,
      n_envs: 16,
      total_timesteps: 400_000,
      seed: 1,
    },
    curve: sparkline(1, 32, 0.04),
    logs: [
      "[10:00:00] supervisor: baseline run zx21r0",
      "[11:00:00] ppo: step=400000 mean_return=0.76",
      "[11:00:05] supervisor: SUCCESS",
    ],
  },
  {
    id: "run_2026-04-23_qq04mn",
    shortId: "qq04mn",
    status: "failed",
    template: "obstacle-grid.6x6",
    algo: "PPO",
    startedAt: new Date(now - 50 * hour).toISOString(),
    durationSec: 90,
    steps: 0,
    meanReturn: 0,
    bestReturn: 0,
    episodes: 0,
    seed: 13,
    checkpoint: "—",
    notes: "Webots failed to launch — missing supervisor proto.",
    error: "WebotsLaunchError: supervisor proto 'HermesSpawn' not found in PROTO path",
    config: {
      env: "obstacle-grid.6x6",
      algo: "PPO",
      lr: 3e-4,
      gamma: 0.99,
      gae_lambda: 0.95,
      clip_range: 0.2,
      ent_coef: 0.01,
      n_envs: 8,
      total_timesteps: 500_000,
      seed: 13,
    },
    curve: new Array(32).fill(0),
    logs: [
      "[18:00:00] supervisor: dispatched run qq04mn",
      "[18:00:08] webots: ERR PROTO 'HermesSpawn' not found",
      "[18:00:09] supervisor: ABORTED",
    ],
  },
  {
    id: "run_2026-04-23_t7cm12",
    shortId: "t7cm12",
    status: "success",
    template: "roomba.flat-room.v2",
    algo: "PPO",
    startedAt: new Date(now - 58 * hour).toISOString(),
    durationSec: 4120,
    steps: 500_000,
    meanReturn: 0.79,
    bestReturn: 0.86,
    episodes: 1180,
    seed: 9,
    checkpoint: "s3://hermes/ckpt/t7cm12/best.pt",
    notes: "Slightly under best-of-class h2vq91; same template.",
    config: {
      env: "roomba.flat-room.v2",
      algo: "PPO",
      lr: 3e-4,
      gamma: 0.99,
      gae_lambda: 0.95,
      clip_range: 0.2,
      ent_coef: 0.01,
      n_envs: 16,
      total_timesteps: 500_000,
      seed: 9,
    },
    curve: sparkline(9, 32, 0.04),
    logs: ["[10:00:00] supervisor: dispatched", "[11:08:40] supervisor: SUCCESS"],
  },
  {
    id: "run_2026-04-22_l9mvqe",
    shortId: "l9mvqe",
    status: "early_stop",
    template: "corridor.long.v1",
    algo: "PPO",
    startedAt: new Date(now - 80 * hour).toISOString(),
    durationSec: 1900,
    steps: 220_000,
    meanReturn: 0.34,
    bestReturn: 0.41,
    episodes: 540,
    seed: 17,
    checkpoint: "s3://hermes/ckpt/l9mvqe/step_220k.pt",
    notes: "Long-corridor template under-explores end goal; reward shaping needed.",
    config: {
      env: "corridor.long.v1",
      algo: "PPO",
      lr: 3e-4,
      gamma: 0.995,
      gae_lambda: 0.95,
      clip_range: 0.2,
      ent_coef: 0.02,
      n_envs: 16,
      total_timesteps: 500_000,
      seed: 17,
    },
    curve: sparkline(17, 32, 0.018),
    logs: ["[12:00:00] supervisor: dispatched", "[12:31:40] supervisor: EARLY_STOP"],
  },
];

export function getRun(id: string): Run | undefined {
  return runs.find((r) => r.id === id || r.shortId === id);
}

export function statusLabel(s: RunStatus): string {
  switch (s) {
    case "success": return "SUCCESS";
    case "running": return "RUNNING";
    case "failed": return "FAILED";
    case "early_stop": return "EARLY STOP";
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

export function fmtRelative(iso: string, refMs: number = now): string {
  const diff = (refMs - new Date(iso).getTime()) / 1000;
  if (diff < 60) return `${Math.round(diff)}s ago`;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return `${Math.round(diff / 86400)}d ago`;
}

export function fmtNumber(n: number): string {
  if (Math.abs(n) >= 1000) return n.toLocaleString();
  return n.toFixed(2);
}
