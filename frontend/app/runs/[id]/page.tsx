import Link from "next/link";
import { notFound } from "next/navigation";
import { getRun, runs, fmtDuration, fmtNumber, fmtRelative, statusLabel, statusVar } from "../../lib/runs";
import { Card } from "../../components/Card";
import { StatusDot } from "../../components/StatusDot";
import { Sparkline } from "../../components/Sparkline";

export function generateStaticParams() {
  return runs.map((r) => ({ id: r.shortId }));
}

export const dynamicParams = true;

export default async function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const run = getRun(id);
  if (!run) notFound();
  const accent = statusVar(run.status);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <Link href="/" className="text-[12px]" style={{ color: "var(--muted-strong)" }}>
          ← All runs
        </Link>
        <div className="flex items-center gap-2">
          <button className="btn-ghost" type="button">Re-run</button>
          <button className="btn-ghost" type="button">Download checkpoint</button>
        </div>
      </div>

      <header className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <StatusDot status={run.status} />
          <span className="label" style={{ color: accent }}>{statusLabel(run.status)}</span>
          <span className="label">· {fmtRelative(run.startedAt)} · {fmtDuration(run.durationSec)}</span>
        </div>
        <div className="flex items-baseline gap-3">
          <h1 className="mono text-[32px] tracking-tight">{run.shortId}</h1>
          <span className="text-[14px]" style={{ color: "var(--muted-strong)" }}>
            {run.template}
          </span>
        </div>
        {run.notes && (
          <p className="max-w-2xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
            {run.notes}
          </p>
        )}
      </header>

      <section className="grid grid-cols-2 md:grid-cols-4 card divide-x divide-y md:divide-y-0 divide-hairline">
        <Metric label="return" value={fmtNumber(run.meanReturn)} />
        <Metric label="best" value={fmtNumber(run.bestReturn)} />
        <Metric label="steps" value={run.steps.toLocaleString()} />
        <Metric label="episodes" value={run.episodes.toLocaleString()} />
      </section>

      <Card title="Learning curve" hint="return / step">
        <Sparkline values={run.curve} color={accent} width={1100} height={120} />
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Config" hint="hermes.config.yaml">
          <pre className="mono text-[12px] leading-[1.7] overflow-x-auto">
{Object.entries(run.config)
  .map(([k, v]) => `${k.padEnd(18, " ")}  ${typeof v === "string" ? v : JSON.stringify(v)}`)
  .join("\n")}
          </pre>
        </Card>

        <Card title="Supervisor log" hint="stderr tail">
          <div
            className="mono text-[12px] leading-[1.7] p-4 rounded-md"
            style={{ background: "var(--background)", border: "1px solid var(--line)" }}
          >
            {run.logs.map((line, i) => (
              <div
                key={i}
                style={{ color: i === run.logs.length - 1 ? "var(--foreground)" : "var(--muted-strong)" }}
              >
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
        <Card title="AgentMail" hint="end-of-run report" action={<button className="btn-ghost" type="button">Re-send</button>}>
          <div className="flex flex-col gap-2 text-[12px]">
            <Row k="to" v="— not connected" />
            <Row k="subject" v={`[RL] run ${run.shortId} ${statusLabel(run.status).toLowerCase()}`} />
            <Row k="sent" v="—" />
            <p className="label mt-2">stub · docs.agentmail.to</p>
          </div>
        </Card>

        <Card title="Nia memory" hint="lessons indexed" action={<button className="btn-ghost" type="button">Recall</button>}>
          <div className="flex flex-col gap-2 text-[12px]">
            <Row k="index" v="— not connected" />
            <Row k="lessons" v="0" />
            <p className="label mt-2">stub · docs.trynia.ai</p>
          </div>
        </Card>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-5 flex flex-col gap-1">
      <span className="label">{label}</span>
      <span className="text-[28px] font-semibold tracking-tight tabular-nums">{value}</span>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="grid grid-cols-[100px_1fr] gap-4 border-b hairline pb-1.5">
      <span className="label">{k}</span>
      <span style={{ color: "var(--foreground)" }}>{v}</span>
    </div>
  );
}
