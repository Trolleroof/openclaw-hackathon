"use client";

import { useEffect, useState } from "react";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { createSampleRunReport, fetchRunReports, HERMES_API_BASE_URL, type RunReport } from "../lib/reports";

export default function AgentMailPage() {
  const [isSending, setIsSending] = useState(false);
  const [reports, setReports] = useState<RunReport[]>([]);
  const [isLoadingReports, setIsLoadingReports] = useState(true);
  const [reportsError, setReportsError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadReports() {
      setIsLoadingReports(true);
      setReportsError(null);

      try {
        const data = await fetchRunReports();
        if (!cancelled) setReports(data);
      } catch (err) {
        if (!cancelled) {
          setReportsError(err instanceof Error ? err.message : "Failed to load reports");
        }
      } finally {
        if (!cancelled) setIsLoadingReports(false);
      }
    }

    loadReports();
    return () => {
      cancelled = true;
    };
  }, []);

  async function loadReports() {
    setIsLoadingReports(true);
    setReportsError(null);

    try {
      const data = await fetchRunReports();
      setReports(data);
    } catch (err) {
      setReportsError(err instanceof Error ? err.message : "Failed to load reports");
    } finally {
      setIsLoadingReports(false);
    }
  }

  async function sendSampleSummary() {
    setIsSending(true);
    setError(null);

    try {
      await createSampleRunReport();
      await loadReports();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sample report request failed");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1">
        <span className="label">Integration · 02</span>
        <h1 className="text-[32px] font-semibold tracking-tight">AgentMail</h1>
        <p className="max-w-2xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
          When a supervised run exits, Hermes hands the same structured report it already builds
          to AgentMail. Not yet connected.
        </p>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 flex flex-col gap-6">
          <Card title="Outbox" hint="recent dispatches">
            {isLoadingReports ? (
              <EmptyState
                icon="..."
                title="Loading reports"
                body={`Reading run reports from ${HERMES_API_BASE_URL}.`}
              />
            ) : reportsError ? (
              <EmptyState
                icon="!"
                title="Backend not connected"
                body={`${reportsError}. Start FastAPI with uvicorn app.main:app --reload, then refresh this page.`}
              />
            ) : reports.length === 0 ? (
              <EmptyState
                icon="✉"
                title="No dispatches yet"
                body="Once a run completes, the backend will store the report here and attempt AgentMail delivery."
              />
            ) : (
              <div className="flex flex-col">
                {reports.map((report) => (
                  <div key={report.run_id} className="grid grid-cols-[1fr_auto] gap-4 py-3 border-b hairline last:border-b-0">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">{report.run_id}</span>
                        <span className="label">{report.status}</span>
                        <span className="label">delivery: {report.delivery_status}</span>
                      </div>
                      <p className="mt-1 text-[12px] truncate" style={{ color: "var(--muted-strong)" }}>
                        {report.model_summary}
                      </p>
                      {report.delivery_error && (
                        <p className="mt-1 text-[11px]" style={{ color: "var(--status-failed)" }}>
                          {report.delivery_error}
                        </p>
                      )}
                    </div>
                    {report.artifact_links.dashboard && (
                      <a className="btn-ghost self-start" href={report.artifact_links.dashboard}>
                        Open
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card title="Sample completion" hint="backend test">
            <div className="flex flex-col gap-4">
              <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3 items-end">
                <p className="text-[13px]" style={{ color: "var(--muted-strong)" }}>
                  Posts a completed demo run to FastAPI, generates a stored report, and attempts
                  AgentMail delivery if credentials are configured.
                </p>
                <button
                  className="btn-accent self-end disabled:opacity-60"
                  type="button"
                  onClick={sendSampleSummary}
                  disabled={isSending}
                >
                  {isSending ? "Sending sample..." : "Send sample report"}
                </button>
              </div>

              {error && (
                <div className="rounded-md border hairline p-3 text-[12px]" style={{ color: "var(--status-failed)" }}>
                  {error}
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <Card title="Connection" hint="stub">
            <div className="flex flex-col gap-3">
              <Field k="Inbox" placeholder="you@example.com" />
              <Field k="API key" placeholder="agm_..." />
              <button className="btn-accent mt-1" type="button">Connect AgentMail</button>
              <p className="label">docs.agentmail.to</p>
            </div>
          </Card>

          <Card title="Defaults" hint="stub">
            <div className="flex flex-col gap-2 text-[12px]">
              <Row k="trigger" v="on run.exit" />
              <Row k="format" v="markdown + json" />
              <Row k="retries" v="3" />
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}

function Field({ k, placeholder }: { k: string; placeholder: string }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="label">{k}</span>
      <input
        disabled
        placeholder={placeholder}
        className="px-3 py-2 rounded-md text-[13px] outline-none"
        style={{ background: "var(--background)", border: "1px solid var(--line)", color: "var(--foreground)" }}
      />
    </label>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between border-b hairline pb-1.5">
      <span className="label">{k}</span>
      <span style={{ color: "var(--foreground)" }}>{v}</span>
    </div>
  );
}
