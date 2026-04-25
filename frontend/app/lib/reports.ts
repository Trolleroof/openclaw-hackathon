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

export async function fetchRunReport(runId: string): Promise<RunReport> {
  const response = await fetch(`${HERMES_API_BASE_URL}/api/v1/runs/${runId}/report`, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Report not found (${response.status})`);
  }

  return response.json();
}
