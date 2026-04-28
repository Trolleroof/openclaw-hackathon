const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ApolloLabsLesson = {
  run_id: string;
  status: string;
  template: string;
  algo?: string | null;
  steps: number | null;
  episodes?: number | null;
  mean_return: number | null;
  best_return: number | null;
  config?: Record<string, unknown> | null;
  artifact_links?: Record<string, string> | null;
  checkpoint_uri?: string | null;
  model_summary?: string | null;
  markdown?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  duration_sec: number | null;
  created_at: string;
  error: string | null;
  hermes_delivery_status: string;
  hermes_delivery_error: string | null;
  delivery_status?: string | null;
  delivery_error?: string | null;
  agentmail_message_id?: string | null;
  agentmail_thread_id?: string | null;
};

export async function fetchApolloLabsLessons(limit = 25): Promise<ApolloLabsLesson[]> {
  const res = await fetch(`${API_BASE}/api/v1/memory/lessons?limit=${limit}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`Failed to load lessons (${res.status})`);
  const data = await res.json();
  return data.lessons as ApolloLabsLesson[];
}
