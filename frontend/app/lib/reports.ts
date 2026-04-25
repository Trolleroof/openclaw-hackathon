export type RunReport = {
  run_id: string;
  status: string;
  started_at?: string | null;
  ended_at: string;
  duration_sec?: number | null;
  template: string;
  algo: string;
  config: Record<string, unknown>;
  steps?: number | null;
  episodes?: number | null;
  mean_return?: number | null;
  best_return?: number | null;
  checkpoint_uri?: string | null;
  artifact_links: Record<string, string>;
  error?: string | null;
  model_summary: string;
  markdown: string;
  agentmail_message_id?: string | null;
  agentmail_thread_id?: string | null;
  delivery_status: string;
  delivery_error?: string | null;
  created_at: string;
};

export const HERMES_API_BASE_URL =
  process.env.NEXT_PUBLIC_HERMES_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function fetchRunReports(): Promise<RunReport[]> {
  const response = await fetch(`${HERMES_API_BASE_URL}/api/v1/reports`, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Failed to load reports (${response.status})`);
  }

  return response.json();
}

export async function createSampleRunReport(): Promise<RunReport> {
  const runId = `demo_${Date.now()}`;
  const response = await fetch(`${HERMES_API_BASE_URL}/api/v1/runs/${runId}/complete`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      status: "completed",
      config: {
        total_timesteps: 30000,
        eval_episodes: 10,
        seed: 42,
        room_size: 10,
        max_steps: 200,
        dirt_count: 3,
      },
      metrics: {
        ppo: {
          episodes: 10,
          avg_reward: 38.4,
          success_rate: 0.7,
          avg_steps: 143,
          avg_remaining_dirt: 0.4,
          wall_hits: 12,
        },
      },
      model_path: `runs/${runId}/model/roomba_policy.zip`,
      metrics_path: `runs/${runId}/metrics/combined_metrics.json`,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create sample report (${response.status})`);
  }

  await response.json();
  const reports = await fetchRunReports();
  const created = reports.find((report) => report.run_id === runId);

  if (!created) {
    throw new Error("Sample report was created but could not be reloaded");
  }

  return created;
}
