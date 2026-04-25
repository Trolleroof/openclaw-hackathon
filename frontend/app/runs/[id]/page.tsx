"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card } from "../../components/Card";
import { fetchRunReport, type RunReport } from "../../lib/reports";
import { fmtDuration, fmtNumber, fmtRelative } from "../../lib/runs";

export default function RunPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<RunReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRunReport(id)
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load report"));
  }, [id]);

  if (error) {
    return (
      <div className="flex flex-col gap-4">
        <Link href="/" className="text-[12px]" style={{ color: "var(--muted-strong)" }}>← All runs</Link>
        <p className="text-[13px]" style={{ color: "var(--status-failed)" }}>{error}</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex flex-col gap-4">
        <Link href="/" className="text-[12px]" style={{ color: "var(--muted-strong)" }}>← All runs</Link>
        <p className="text-[13px] label">Loading…</p>
      </div>
    );
  }

  const accent = report.status === "success" ? "var(--status-success)"
    : report.status === "failed" ? "var(--status-failed)"
    : "var(--muted-strong)";

  const duration = report.duration_sec != null ? fmtDuration(report.duration_sec) : "—";
  const started = report.started_at ? fmtRelative(report.started_at) : "—";

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <Link href="/" className="text-[12px]" style={{ color: "var(--muted-strong)" }}>← All runs</Link>
      </div>

      <header className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <span className="label" style={{ color: accent }}>{report.status}</span>
          <span className="label">· {started} · {duration}</span>
        </div>
        <div className="flex items-baseline gap-3">
          <h1 className="mono text-[32px] tracking-tight">{report.run_id}</h1>
          <span className="text-[14px]" style={{ color: "var(--muted-strong)" }}>{report.template}</span>
        </div>
        {report.model_summary && (
          <p className="max-w-2xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
            {report.model_summary}
          </p>
        )}
      </header>

      <section className="grid grid-cols-2 md:grid-cols-4 card divide-x divide-y md:divide-y-0 divide-hairline">
        <Metric label="return" value={report.mean_return != null ? fmtNumber(report.mean_return) : "—"} />
        <Metric label="success rate" value={report.best_return != null ? fmtNumber(report.best_return) : "—"} />
        <Metric label="steps" value={report.steps != null ? report.steps.toLocaleString() : "—"} />
        <Metric label="episodes" value={report.episodes != null ? report.episodes.toLocaleString() : "—"} />
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Config" hint={report.algo}>
          <pre className="mono text-[12px] leading-[1.7] overflow-x-auto">
            {Object.entries(report.config)
              .map(([k, v]) => `${k.padEnd(20, " ")}  ${typeof v === "string" ? v : JSON.stringify(v)}`)
              .join("\n")}
          </pre>
        </Card>

        <Card title="AgentMail" hint="end-of-run dispatch">
          <div className="flex flex-col gap-2 text-[12px]">
            <Row k="delivery" v={report.delivery_status} />
            {report.agentmail_message_id && <Row k="message id" v={report.agentmail_message_id} />}
            {report.agentmail_thread_id && <Row k="thread id" v={report.agentmail_thread_id} />}
            {report.delivery_error && (
              <p className="mt-1 text-[11px]" style={{ color: "var(--status-failed)" }}>
                {report.delivery_error}
              </p>
            )}
            {report.artifact_links.checkpoint && (
              <Row k="checkpoint" v={report.artifact_links.checkpoint} />
            )}
          </div>
        </Card>
      </div>

      {report.markdown && (
        <Card title="Report" hint="markdown">
          <pre className="mono text-[12px] leading-[1.7] overflow-x-auto whitespace-pre-wrap">
            {report.markdown}
          </pre>
        </Card>
      )}
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
    <div className="grid grid-cols-[120px_1fr] gap-4 border-b hairline pb-1.5">
      <span className="label">{k}</span>
      <span style={{ color: "var(--foreground)" }}>{v}</span>
    </div>
  );
}
