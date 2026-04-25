"use client";

import { useState } from "react";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import type { MockAgentMailPayload } from "../lib/agentmail";
import { runs, statusLabel } from "../lib/runs";

type MockResponse = {
  ok: boolean;
  mocked: boolean;
  provider: string;
  sentAt: string;
  payload: MockAgentMailPayload;
};

export default function AgentMailPage() {
  const finishedRuns = runs.filter((run) => run.status !== "running");
  const [selectedRunId, setSelectedRunId] = useState(finishedRuns[0]?.shortId ?? "");
  const [mockResponse, setMockResponse] = useState<MockResponse | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function sendMockSummary() {
    setIsSending(true);
    setError(null);

    try {
      const response = await fetch("/api/agentmail/mock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ runId: selectedRunId }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error ?? "Mock AgentMail request failed");
      }

      setMockResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Mock AgentMail request failed");
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
            <EmptyState
              icon="✉"
              title="No dispatches yet"
              body="Once a run completes and AgentMail is connected, structured reports will appear here."
            />
          </Card>

          <Card title="Mock API sender" hint="local test">
            <div className="flex flex-col gap-4">
              <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3">
                <label className="flex flex-col gap-1">
                  <span className="label">Run summary</span>
                  <select
                    className="px-3 py-2 rounded-md text-[13px] outline-none"
                    style={{ background: "var(--background)", border: "1px solid var(--line)", color: "var(--foreground)" }}
                    value={selectedRunId}
                    onChange={(event) => setSelectedRunId(event.target.value)}
                  >
                    {finishedRuns.map((run) => (
                      <option key={run.id} value={run.shortId}>
                        {run.shortId} · {statusLabel(run.status).toLowerCase()} · {run.template}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  className="btn-accent self-end disabled:opacity-60"
                  type="button"
                  onClick={sendMockSummary}
                  disabled={isSending || !selectedRunId}
                >
                  {isSending ? "Sending mock..." : "Send mock summary"}
                </button>
              </div>

              {error && (
                <div className="rounded-md border hairline p-3 text-[12px]" style={{ color: "var(--status-failed)" }}>
                  {error}
                </div>
              )}

              {mockResponse && (
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                  <div className="rounded-md border hairline p-4" style={{ background: "var(--background)" }}>
                    <div className="label mb-2">Model summary</div>
                    <p className="text-[13px] leading-[1.7]" style={{ color: "var(--muted-strong)" }}>
                      {mockResponse.payload.modelSummary}
                    </p>
                    <div className="mt-4 grid grid-cols-[84px_1fr] gap-2 text-[11px]">
                      <span className="label">To</span>
                      <span>{mockResponse.payload.to}</span>
                      <span className="label">Subject</span>
                      <span style={{ color: "var(--accent)" }}>{mockResponse.payload.subject}</span>
                      <span className="label">Sent</span>
                      <span>{new Date(mockResponse.sentAt).toLocaleString()}</span>
                    </div>
                  </div>
                  <pre
                    className="rounded-md border hairline p-4 text-[11px] leading-[1.6] overflow-x-auto"
                    style={{ background: "var(--background)", color: "var(--foreground)" }}
                  >
{JSON.stringify(mockResponse.payload, null, 2)}
                  </pre>
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
