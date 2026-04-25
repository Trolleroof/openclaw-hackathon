"use client";

import { useEffect, useState } from "react";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { fetchHermesLessons, type HermesLesson } from "../lib/hermes";

function fmt(value: number | null, decimals = 3): string {
  return value !== null ? value.toFixed(decimals) : "n/a";
}

function statusBadge(status: string) {
  const color =
    status === "success" || status === "completed"
      ? "var(--status-success)"
      : status === "failed"
      ? "var(--status-failed)"
      : "var(--muted-strong)";
  return (
    <span className="label" style={{ color }}>
      {status}
    </span>
  );
}

function hermesBadge(deliveryStatus: string) {
  const color =
    deliveryStatus === "posted"
      ? "var(--status-success)"
      : deliveryStatus === "failed"
      ? "var(--status-failed)"
      : "var(--muted-strong)";
  return (
    <span className="label" style={{ color }}>
      {deliveryStatus === "posted" ? "sent to hermes" : deliveryStatus === "failed" ? "hermes failed" : "hermes skipped"}
    </span>
  );
}

export default function MemoryPage() {
  const [lessons, setLessons] = useState<HermesLesson[]>([]);
  const [selected, setSelected] = useState<HermesLesson | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    fetchHermesLessons()
      .then((data) => { if (!cancelled) setLessons(data); })
      .catch((err) => { if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load lessons"); })
      .finally(() => { if (!cancelled) setIsLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1">
        <span className="label">Integration · 03</span>
        <h1 className="text-[32px] font-semibold tracking-tight">Nia memory</h1>
        <p className="max-w-2xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
          W&amp;B holds the numbers. Nia holds the narrative — what we tried, what worked,
          what failed. ClawLab posts a lesson to Hermes in Slack after each run; Hermes indexes it into Nia.
        </p>
      </header>

      <section className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_440px] gap-6">
        <div className="flex flex-col gap-6">
          <Card title="Lessons" hint="posted to Hermes">
            {isLoading ? (
              <EmptyState icon="..." title="Loading lessons" body="Fetching run lessons from ClawLab." />
            ) : error ? (
              <EmptyState icon="!" title="Could not load lessons" body={error} />
            ) : lessons.length === 0 ? (
              <EmptyState
                icon="§"
                title="No lessons yet"
                body="Complete a training run to generate the first lesson. Set SLACK_WEBHOOK_URL to post it to Hermes."
              />
            ) : (
              <div className="flex flex-col">
                {lessons.map((lesson) => (
                  <div
                    key={lesson.run_id}
                    className="grid grid-cols-[1fr_auto] gap-4 py-3 border-b hairline last:border-b-0"
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold font-mono text-[13px]">{lesson.run_id}</span>
                        {statusBadge(lesson.status)}
                        {hermesBadge(lesson.hermes_delivery_status)}
                      </div>
                      <p className="mt-1 text-[12px]" style={{ color: "var(--muted-strong)" }}>
                        {lesson.template} · reward {fmt(lesson.mean_return)} · success {fmt(lesson.best_return)}
                      </p>
                      {lesson.error && (
                        <p className="mt-1 text-[12px] truncate" style={{ color: "var(--status-failed)" }}>
                          {lesson.error}
                        </p>
                      )}
                    </div>
                    <button
                      className="btn-ghost self-start"
                      type="button"
                      onClick={() => setSelected(selected?.run_id === lesson.run_id ? null : lesson)}
                    >
                      {selected?.run_id === lesson.run_id ? "Close" : "View"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        <Card title="Lesson detail" hint="Nia memory entry">
          {!selected ? (
            <EmptyState icon="↗" title="Select a lesson" body="Pick a row to see the full lesson sent to Hermes." />
          ) : (
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1">
                <span className="label">{selected.run_id}</span>
                <h2 className="text-[18px] font-semibold leading-tight">{selected.template}</h2>
                <div className="flex flex-wrap gap-2 mt-1">
                  {statusBadge(selected.status)}
                  {hermesBadge(selected.hermes_delivery_status)}
                </div>
              </div>

              <table className="w-full text-[12px] border-collapse">
                <tbody>
                  {([
                    ["Timesteps", selected.steps?.toLocaleString() ?? "n/a"],
                    ["Mean reward", fmt(selected.mean_return)],
                    ["Success rate", fmt(selected.best_return)],
                    ["Duration", selected.duration_sec ? `${selected.duration_sec.toFixed(1)}s` : "n/a"],
                    ["Hermes status", selected.hermes_delivery_status],
                  ] as [string, string][]).map(([k, v]) => (
                    <tr key={k} className="border-b hairline last:border-b-0">
                      <td className="py-1.5 pr-4 font-medium" style={{ color: "var(--muted-strong)" }}>{k}</td>
                      <td className="py-1.5 font-mono">{v}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {selected.hermes_delivery_error && (
                <div className="rounded-md border hairline p-3 text-[12px]" style={{ color: "var(--status-failed)" }}>
                  {selected.hermes_delivery_error}
                </div>
              )}

              {selected.error && (
                <div className="rounded-md border hairline p-3 text-[12px]" style={{ color: "var(--status-failed)" }}>
                  <span className="font-medium">Run error:</span> {selected.error}
                </div>
              )}
            </div>
          )}
        </Card>
      </section>
    </div>
  );
}
