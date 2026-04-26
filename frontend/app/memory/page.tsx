"use client";

import { useEffect, useMemo, useState } from "react";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { fetchHermesLessons, type HermesLesson } from "../lib/hermes";

function fmt(value: number | null | undefined, decimals = 3): string {
  return value !== null && value !== undefined ? value.toFixed(decimals) : "n/a";
}

function pct(value: number | null | undefined): string {
  return value !== null && value !== undefined ? `${(value * 100).toFixed(1)}%` : "n/a";
}

function fmtDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return "n/a";
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s.toString().padStart(2, "0")}s`;
}

function fmtTimestamp(iso: string | null | undefined): string {
  if (!iso) return "n/a";
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
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

function agentmailBadge(deliveryStatus: string | null | undefined) {
  if (!deliveryStatus) return null;
  const color =
    deliveryStatus === "sent"
      ? "var(--status-success)"
      : deliveryStatus === "failed"
      ? "var(--status-failed)"
      : "var(--muted-strong)";
  return (
    <span className="label" style={{ color }}>
      agentmail {deliveryStatus}
    </span>
  );
}

type DerivedLesson = {
  headline: string;
  whatWorked: string;
  whatFailed: string;
  nextRecommendation: string;
  narrative: string;
};

function deriveLesson(lesson: HermesLesson): DerivedLesson {
  const sr = lesson.best_return ?? 0;
  const mr = lesson.mean_return ?? 0;
  const steps = lesson.steps ?? 0;
  const episodes = lesson.episodes ?? 0;
  const cfg = lesson.config ?? {};
  const room = (cfg.room_size as number | undefined) ?? null;
  const dirt = (cfg.dirt_count as number | undefined) ?? null;
  const obstacles = (cfg.obstacle_count as number | undefined) ?? null;
  const sensorMode = (cfg.sensor_mode as string | undefined) ?? null;

  const envDescriptor = [
    room !== null ? `${room}m room` : null,
    dirt !== null ? `${dirt} dirt particles` : null,
    obstacles ? `${obstacles} obstacles` : null,
    sensorMode ? `${sensorMode} sensing` : null,
  ]
    .filter(Boolean)
    .join(", ");

  if (lesson.status === "failed" && lesson.error) {
    return {
      headline: "Run did not complete — investigate before retrying.",
      whatWorked: "n/a — run did not complete",
      whatFailed: `Run errored out: ${lesson.error}`,
      nextRecommendation:
        "Inspect the runs/ directory logs, reproduce locally, and patch the failure before resubmitting the same config.",
      narrative: `Run ${lesson.run_id} on ${lesson.template} (${envDescriptor || "default config"}) crashed before producing a usable policy. The harness reported: \"${lesson.error}\". No metrics were captured, so any prior lessons on this template still apply.`,
    };
  }

  if (sr >= 0.8) {
    return {
      headline: `Strong convergence — success rate ${pct(sr)}, mean reward ${fmt(mr)}.`,
      whatWorked: `Policy converged cleanly on ${lesson.template}. Across ${episodes || "the"} eval episodes the agent solved ${pct(sr)} of starts with mean reward ${fmt(mr)} after ${steps.toLocaleString()} timesteps.`,
      whatFailed: "No critical failures observed. Reward curve and success rate stayed coherent through eval.",
      nextRecommendation: `Lock this config as a known-good baseline and ramp difficulty: try a larger room (e.g. ${room ? room + 2 : "+2m"}), ~25% more dirt, or swap to lidar_local_dirt sensing if currently on oracle.`,
      narrative: `Run ${lesson.run_id} produced a confident policy on ${lesson.template} (${envDescriptor || "default config"}). PPO trained for ${steps.toLocaleString()} timesteps in ${fmtDuration(lesson.duration_sec)}, reaching ${pct(sr)} success and ${fmt(mr)} mean reward over ${episodes || "n/a"} eval episodes. Treat this as a green checkpoint — the next runs should make the environment harder rather than tweak hyperparameters.`,
    };
  }

  if (sr >= 0.5) {
    return {
      headline: `Partial learning — success rate ${pct(sr)}, mean reward ${fmt(mr)}.`,
      whatWorked: `Reward signal moved in the right direction (mean reward ${fmt(mr)}) and the agent solved ${pct(sr)} of evals — the config is learnable but undertrained.`,
      whatFailed: `Policy did not fully converge in ${steps.toLocaleString()} timesteps. Success rate plateaued below the 80% mark.`,
      nextRecommendation: `Re-run with ~50% more total_timesteps, or hold timesteps and tune reward shaping (e.g. nudge dirt_pickup_reward up, time_penalty down). Keep ${envDescriptor || "the same env config"} so results are comparable.`,
      narrative: `Run ${lesson.run_id} on ${lesson.template} (${envDescriptor || "default config"}) showed clear learning signal but stopped short of mastery. After ${steps.toLocaleString()} timesteps and ${fmtDuration(lesson.duration_sec)} of training, evaluation gave ${pct(sr)} success and ${fmt(mr)} mean reward. The config is viable; the next iteration should extend training or refine reward weights before declaring the env solved.`,
    };
  }

  return {
    headline: `Minimal learning — success rate ${pct(sr)}, mean reward ${fmt(mr)}.`,
    whatWorked: `Pipeline ran end-to-end and produced a usable checkpoint at ${lesson.checkpoint_uri || "runs/<id>/model"}, even though the policy itself underperformed.`,
    whatFailed: `Agent struggled to make progress on ${lesson.template}. Only ${pct(sr)} of evals succeeded with mean reward ${fmt(mr)} — likely under-trained, mis-shaped reward, or env too hard for the current setup.`,
    nextRecommendation: `Either (a) increase total_timesteps significantly (2–3×), (b) simplify the env (smaller room or fewer dirt particles), or (c) revisit reward shaping. Avoid stacking changes — change one knob at a time so Nia can attribute the delta.`,
    narrative: `Run ${lesson.run_id} on ${lesson.template} (${envDescriptor || "default config"}) produced a weak policy. Over ${steps.toLocaleString()} timesteps and ${fmtDuration(lesson.duration_sec)} of wall time, the agent only solved ${pct(sr)} of eval episodes with mean reward ${fmt(mr)}. The reward landscape did not move it past the random-baseline threshold, so this configuration should not be reused without changes. Next experimenter should treat this as a negative example: more compute, simpler env, or reshaped reward.`,
  };
}

function summarizeConfig(cfg: Record<string, unknown> | null | undefined): Array<[string, string]> {
  if (!cfg) return [];
  const order = [
    "room_size",
    "dirt_count",
    "obstacle_count",
    "max_steps",
    "total_timesteps",
    "eval_episodes",
    "sensor_mode",
    "layout_mode",
    "lidar_rays",
    "seed",
    "device",
  ];
  const rows: Array<[string, string]> = [];
  for (const key of order) {
    if (cfg[key] !== undefined && cfg[key] !== null) {
      rows.push([key, String(cfg[key])]);
    }
  }
  for (const [k, v] of Object.entries(cfg)) {
    if (!order.includes(k) && v !== null && v !== undefined && typeof v !== "object") {
      rows.push([k, String(v)]);
    }
  }
  return rows;
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

  const derived = useMemo(() => (selected ? deriveLesson(selected) : null), [selected]);
  const configRows = useMemo(() => (selected ? summarizeConfig(selected.config ?? null) : []), [selected]);

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-2">
        <span className="label">Integration · 03</span>
        <h1 className="text-[32px] font-semibold tracking-tight">Nia memory</h1>
        <p className="max-w-3xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
          W&amp;B holds the numbers. Nia holds the narrative — what we tried, what worked, and
          what failed. After every training run, ClawLab posts a structured lesson to Hermes in Slack,
          AgentMail emails the full report, and Hermes indexes the whole bundle (env config, metrics,
          checkpoint URI, derived recommendations) into Nia so the next run starts with the prior context.
        </p>
        <p className="max-w-3xl text-[12px]" style={{ color: "var(--muted-strong)" }}>
          Each lesson below captures: the env_id and full env config, PPO training stats, evaluation
          success rate, AgentMail / Slack delivery state, and a natural-language summary explaining
          what the run actually demonstrated. This is what Nia retrieves on the next planning step.
        </p>
      </header>

      <section className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_520px] gap-6">
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
                {lessons.map((lesson) => {
                  const d = deriveLesson(lesson);
                  return (
                    <div
                      key={lesson.run_id}
                      className="grid grid-cols-[1fr_auto] gap-4 py-4 border-b hairline last:border-b-0"
                    >
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-semibold font-mono text-[13px]">{lesson.run_id}</span>
                          {statusBadge(lesson.status)}
                          {hermesBadge(lesson.hermes_delivery_status)}
                          {agentmailBadge(lesson.delivery_status)}
                        </div>
                        <p className="mt-1 text-[12px] font-mono" style={{ color: "var(--muted-strong)" }}>
                          {lesson.template} · {(lesson.algo || "PPO")} · {lesson.steps?.toLocaleString() ?? "?"} steps · reward {fmt(lesson.mean_return)} · success {pct(lesson.best_return)} · {fmtDuration(lesson.duration_sec)}
                        </p>
                        <p className="mt-2 text-[12px] leading-relaxed" style={{ color: "var(--foreground)" }}>
                          {d.headline}
                        </p>
                        <p className="mt-1 text-[11px]" style={{ color: "var(--muted-strong)" }}>
                          Logged {fmtTimestamp(lesson.created_at)}
                          {lesson.ended_at ? ` · ended ${fmtTimestamp(lesson.ended_at)}` : ""}
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
                  );
                })}
              </div>
            )}
          </Card>
        </div>

        <Card title="Lesson detail" hint="Nia memory entry">
          {!selected || !derived ? (
            <EmptyState
              icon="↗"
              title="Select a lesson"
              body="Pick a row to see the full lesson sent to Hermes — env config, metrics, derived recommendations, and delivery trail."
            />
          ) : (
            <div className="flex flex-col gap-5">
              <div className="flex flex-col gap-1">
                <span className="label">{selected.run_id}</span>
                <h2 className="text-[18px] font-semibold leading-tight">{selected.template}</h2>
                <div className="flex flex-wrap gap-2 mt-1">
                  {statusBadge(selected.status)}
                  {hermesBadge(selected.hermes_delivery_status)}
                  {agentmailBadge(selected.delivery_status)}
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <span className="label">Narrative</span>
                <p className="text-[12.5px] leading-relaxed">{derived.narrative}</p>
                {selected.model_summary && selected.model_summary !== derived.narrative && (
                  <p className="text-[12px] leading-relaxed" style={{ color: "var(--muted-strong)" }}>
                    {selected.model_summary}
                  </p>
                )}
              </div>

              <div>
                <span className="label">Run stats</span>
                <table className="w-full text-[12px] border-collapse mt-2">
                  <tbody>
                    {([
                      ["Algorithm", selected.algo || "PPO"],
                      ["Timesteps", selected.steps?.toLocaleString() ?? "n/a"],
                      ["Eval episodes", selected.episodes?.toLocaleString() ?? "n/a"],
                      ["Mean reward", fmt(selected.mean_return)],
                      ["Success rate", pct(selected.best_return)],
                      ["Duration", fmtDuration(selected.duration_sec)],
                      ["Started", fmtTimestamp(selected.started_at)],
                      ["Ended", fmtTimestamp(selected.ended_at)],
                      ["Checkpoint", selected.checkpoint_uri || "n/a"],
                    ] as [string, string][]).map(([k, v]) => (
                      <tr key={k} className="border-b hairline last:border-b-0">
                        <td className="py-1.5 pr-4 font-medium" style={{ color: "var(--muted-strong)" }}>{k}</td>
                        <td className="py-1.5 font-mono break-all">{v}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {configRows.length > 0 && (
                <div>
                  <span className="label">Env config</span>
                  <table className="w-full text-[12px] border-collapse mt-2">
                    <tbody>
                      {configRows.map(([k, v]) => (
                        <tr key={k} className="border-b hairline last:border-b-0">
                          <td className="py-1.5 pr-4 font-medium font-mono" style={{ color: "var(--muted-strong)" }}>{k}</td>
                          <td className="py-1.5 font-mono">{v}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="flex flex-col gap-3">
                <span className="label">Lesson</span>
                <div className="flex flex-col gap-1">
                  <span className="text-[11px] uppercase tracking-wider" style={{ color: "var(--muted-strong)" }}>What worked</span>
                  <p className="text-[12.5px] leading-relaxed">{derived.whatWorked}</p>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-[11px] uppercase tracking-wider" style={{ color: "var(--muted-strong)" }}>What failed</span>
                  <p className="text-[12.5px] leading-relaxed">{derived.whatFailed}</p>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-[11px] uppercase tracking-wider" style={{ color: "var(--muted-strong)" }}>Next recommendation</span>
                  <p className="text-[12.5px] leading-relaxed">{derived.nextRecommendation}</p>
                </div>
              </div>

              <div>
                <span className="label">Delivery</span>
                <table className="w-full text-[12px] border-collapse mt-2">
                  <tbody>
                    {([
                      ["Hermes (Slack)", selected.hermes_delivery_status],
                      ["AgentMail", selected.delivery_status || "n/a"],
                      ["AgentMail message", selected.agentmail_message_id || "n/a"],
                      ["AgentMail thread", selected.agentmail_thread_id || "n/a"],
                      ["Logged at", fmtTimestamp(selected.created_at)],
                    ] as [string, string][]).map(([k, v]) => (
                      <tr key={k} className="border-b hairline last:border-b-0">
                        <td className="py-1.5 pr-4 font-medium" style={{ color: "var(--muted-strong)" }}>{k}</td>
                        <td className="py-1.5 font-mono break-all">{v}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {selected.artifact_links && Object.keys(selected.artifact_links).length > 0 && (
                <div className="flex flex-col gap-2">
                  <span className="label">Artifacts</span>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(selected.artifact_links).map(([k, v]) => (
                      <a
                        key={k}
                        className="btn-ghost text-[12px]"
                        href={v}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {k} →
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {selected.markdown && (
                <details className="rounded-md border hairline">
                  <summary className="cursor-pointer px-3 py-2 text-[12px] font-medium" style={{ color: "var(--muted-strong)" }}>
                    Full report markdown (as sent to AgentMail / indexed by Nia)
                  </summary>
                  <pre className="px-3 py-2 text-[11.5px] whitespace-pre-wrap font-mono leading-relaxed" style={{ color: "var(--foreground)" }}>{selected.markdown}</pre>
                </details>
              )}

              {selected.hermes_delivery_error && (
                <div className="rounded-md border hairline p-3 text-[12px]" style={{ color: "var(--status-failed)" }}>
                  <span className="font-medium">Hermes delivery error:</span> {selected.hermes_delivery_error}
                </div>
              )}

              {selected.delivery_error && (
                <div className="rounded-md border hairline p-3 text-[12px]" style={{ color: "var(--status-failed)" }}>
                  <span className="font-medium">AgentMail error:</span> {selected.delivery_error}
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
