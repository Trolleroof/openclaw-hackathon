import Link from "next/link";
import { notFound } from "next/navigation";
import { getRun, runs, fmtDuration, fmtNumber, fmtRelative, statusLabel, statusVar } from "../../lib/runs";
import { Card } from "../../components/Card";
import { StatusDot } from "../../components/StatusDot";
import { Sparkline } from "../../components/Sparkline";

export function generateStaticParams() {
  return runs.map((r) => ({ id: r.shortId }));
}

export default async function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const run = getRun(id);
  if (!run) notFound();
  const accent = statusVar(run.status);

  return (
    <div className="px-6 md:px-10 py-10 flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <Link
          href="/"
          className="text-[10px] tracking-[0.18em] uppercase"
          style={{ color: "var(--muted-strong)" }}
        >
          ← All runs
        </Link>
        <div className="flex items-center gap-2">
          <button className="btn-ghost" type="button">Re-run</button>
          <button className="btn-ghost" type="button">Download checkpoint</button>
        </div>
      </div>

      <header className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <StatusDot status={run.status} />
          <span className="text-[10px] tracking-[0.2em] uppercase" style={{ color: accent }}>
            {statusLabel(run.status)}
          </span>
          <span className="text-[10px] tracking-[0.18em] uppercase" style={{ color: "var(--muted)" }}>
            {fmtRelative(run.startedAt)} · {fmtDuration(run.durationSec)}
          </span>
        </div>
        <div className="flex flex-wrap items-baseline gap-x-4 gap-y-2">
          <h1 className="serif text-[68px] leading-none tracking-tight">run</h1>
          <span className="text-[44px] tracking-tight" style={{ color: "var(--foreground)" }}>
            {run.shortId}
          </span>
          <span className="serif italic text-[28px]" style={{ color: "var(--muted-strong)" }}>
            · {run.template}
          </span>
        </div>
        <p className="max-w-3xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
          {run.notes}
        </p>
      </header>

      <section className="grid grid-cols-2 md:grid-cols-4 border hairline divide-x divide-y md:divide-y-0 divide-hairline" style={{ background: "var(--surface)" }}>
        <Metric label="mean_return" value={fmtNumber(run.meanReturn)} accent />
        <Metric label="best_return" value={fmtNumber(run.bestReturn)} />
        <Metric label="steps" value={run.steps.toLocaleString()} />
        <Metric label="episodes" value={run.episodes.toLocaleString()} />
      </section>

      <Card title="Learning curve" code="§ mean_return / step">
        <div className="flex flex-col gap-3">
          <Sparkline values={run.curve} color={accent} width={1200} height={140} />
          <div className="flex justify-between text-[10px] tracking-[0.16em] uppercase" style={{ color: "var(--muted)" }}>
            <span>step 0</span>
            <span>step {run.steps.toLocaleString()}</span>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Config snapshot" code="§ hermes.config.yaml">
          <pre
            className="text-[12px] leading-[1.6] overflow-x-auto"
            style={{ color: "var(--foreground)" }}
          >
{Object.entries(run.config)
  .map(([k, v]) => `${k.padEnd(18, " ")}  ${typeof v === "string" ? v : JSON.stringify(v)}`)
  .join("\n")}
          </pre>
        </Card>

        <Card title="Supervisor log" code="§ stderr tail">
          <div
            className="font-mono text-[12px] leading-[1.7] p-4 border hairline"
            style={{ background: "var(--background)" }}
          >
            {run.logs.map((line, i) => (
              <div key={i} style={{ color: i === run.logs.length - 1 ? "var(--foreground)" : "var(--muted-strong)" }}>
                {line}
              </div>
            ))}
            {run.error && (
              <div className="mt-3 pt-3 border-t hairline" style={{ color: "var(--status-failed)" }}>
                error: {run.error}
              </div>
            )}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card
          title="AgentMail dispatch"
          code="§ 02 · boilerplate"
          action={<button className="btn-ghost" type="button">Re-send</button>}
        >
          <div className="flex flex-col gap-3">
            <Row k="to" v="nikhi@ucsd.edu" />
            <Row k="subject" v={`[RL] run ${run.shortId} ${statusLabel(run.status).toLowerCase()}`} />
            <Row k="sent" v={run.status === "running" ? "— (pending end-of-run)" : fmtRelative(run.startedAt)} />
            <div className="mt-2 p-3 border hairline text-[12px] leading-[1.7]" style={{ background: "var(--background)", color: "var(--muted-strong)" }}>
              <span className="serif italic text-[14px]" style={{ color: "var(--foreground)" }}>Preview —</span>
              <br />
              run {run.shortId} on <em>{run.template}</em> finished with mean_return = {fmtNumber(run.meanReturn)} (best {fmtNumber(run.bestReturn)}). checkpoint at <code>{run.checkpoint}</code>.
            </div>
            <p className="text-[10px] tracking-[0.18em] uppercase" style={{ color: "var(--muted)" }}>
              Stub · wire to AgentMail later
            </p>
          </div>
        </Card>

        <Card
          title="Nia memory"
          code="§ 03 · boilerplate"
          action={<button className="btn-ghost" type="button">Recall</button>}
        >
          <div className="flex flex-col gap-3">
            <Row k="index" v={`hermes.runs / ${run.template}`} />
            <Row k="lessons indexed" v="3" />
            <ul className="flex flex-col gap-2 mt-2">
              {[
                "Higher entropy_coef helps escape early plateaus on flat-room templates.",
                "Collision-reset penalty above 0.4 triggers reward collapse on grid worlds.",
                "500k timesteps is sufficient for v2 templates; v1 plateaus by 400k.",
              ].map((line, i) => (
                <li
                  key={i}
                  className="text-[12px] leading-[1.6] pl-3 border-l"
                  style={{ borderColor: "var(--accent-dim)", color: "var(--muted-strong)" }}
                >
                  <span className="serif italic" style={{ color: "var(--accent)" }}>0{i + 1} · </span>
                  {line}
                </li>
              ))}
            </ul>
            <p className="text-[10px] tracking-[0.18em] uppercase" style={{ color: "var(--muted)" }}>
              Stub · wire to Nia later
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}

function Metric({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="p-5 flex flex-col gap-1">
      <span className="label">{label}</span>
      <span
        className="serif text-[40px] leading-none tabular-nums"
        style={{ color: accent ? "var(--accent)" : "var(--foreground)" }}
      >
        {value}
      </span>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="grid grid-cols-[140px_1fr] gap-4 text-[12px] border-b hairline pb-2">
      <span className="text-[10px] tracking-[0.18em] uppercase" style={{ color: "var(--muted)" }}>{k}</span>
      <span style={{ color: "var(--foreground)" }}>{v}</span>
    </div>
  );
}
