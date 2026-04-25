import type { Run } from "./runs";
import { fmtDuration, fmtNumber, statusLabel } from "./runs";

export type MockAgentMailPayload = {
  to: string;
  from: string;
  subject: string;
  runId: string;
  modelSummary: string;
  attachment: {
    filename: string;
    data: {
      status: string;
      template: string;
      algo: string;
      steps: number;
      meanReturn: number;
      bestReturn: number;
      durationSec: number;
      checkpoint: string;
      notes: string;
      error?: string;
    };
  };
};

export function buildMockAgentMailPayload(run: Run): MockAgentMailPayload {
  const status = statusLabel(run.status).toLowerCase();
  const configBits = [
    `lr=${run.config.lr}`,
    `gamma=${run.config.gamma}`,
    `entropy=${run.config.ent_coef}`,
    `seed=${run.seed}`,
  ].join(" · ");

  return {
    to: "nikhi@ucsd.edu",
    from: "hermes-bot@openclaw.dev",
    subject: `[RL] run ${run.shortId} ${status}`,
    runId: run.id,
    modelSummary:
      `${run.algo} on ${run.template} finished ${status} after ${run.steps.toLocaleString()} steps ` +
      `(${fmtDuration(run.durationSec)}). mean_return=${fmtNumber(run.meanReturn)}, ` +
      `best_return=${fmtNumber(run.bestReturn)}. Config: ${configBits}. ` +
      `${run.error ? `Failure signal: ${run.error}` : `Checkpoint: ${run.checkpoint}`}`,
    attachment: {
      filename: `run-${run.shortId}-summary.json`,
      data: {
        status: run.status,
        template: run.template,
        algo: run.algo,
        steps: run.steps,
        meanReturn: run.meanReturn,
        bestReturn: run.bestReturn,
        durationSec: run.durationSec,
        checkpoint: run.checkpoint,
        notes: run.notes,
        error: run.error,
      },
    },
  };
}
