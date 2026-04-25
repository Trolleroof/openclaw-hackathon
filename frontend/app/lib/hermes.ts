const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type HermesLesson = {
  run_id: string;
  status: string;
  template: string;
  steps: number | null;
  mean_return: number | null;
  best_return: number | null;
  hermes_delivery_status: string;
  hermes_delivery_error: string | null;
  duration_sec: number | null;
  created_at: string;
  error: string | null;
};

export async function fetchHermesLessons(limit = 25): Promise<HermesLesson[]> {
  const res = await fetch(`${API_BASE}/api/v1/memory/lessons?limit=${limit}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`Failed to load lessons (${res.status})`);
  const data = await res.json();
  return data.lessons as HermesLesson[];
}
