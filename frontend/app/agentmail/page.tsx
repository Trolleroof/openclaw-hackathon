"use client";

import { useEffect, useState } from "react";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import {
  fetchAgentMailMessage,
  fetchAgentMailMessages,
  HERMES_API_BASE_URL,
  sendMockRunToAgentMail,
  type AgentMailMessageDetail,
  type AgentMailMessageSummary,
} from "../lib/agentmail";

type ParsedReport = {
  title: string;
  summary: string;
  fields: { label: string; value: string }[];
};

const REPORT_FIELD_LABELS: Record<string, string> = {
  status: "Status",
  template: "Template",
  timesteps: "Timesteps",
  episodes: "Episodes",
  "average reward": "Avg reward",
  "mean return": "Mean return",
  "success rate": "Success rate",
  "best return": "Best return",
  checkpoint: "Checkpoint",
  dashboard: "Dashboard",
};

function messageTime(message: AgentMailMessageSummary) {
  const raw = message.timestamp ?? message.created_at ?? message.updated_at;
  if (!raw) return "unknown";

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(raw));
}

function deliveryLabel(message: AgentMailMessageSummary) {
  if (message.labels.includes("success")) return "success delivery";
  if (message.labels.includes("failed")) return "failed delivery";
  if (message.labels.includes("early_stop")) return "stopped delivery";
  return "agentmail delivery";
}

function bodyText(message: AgentMailMessageDetail) {
  return message.extracted_text ?? message.text ?? message.preview ?? "";
}

function cleanValue(value: string) {
  return value.replace(/`/g, "").replace(/\s+/g, " ").trim();
}

function parseReport(message: AgentMailMessageDetail): ParsedReport {
  const text = bodyText(message);
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  const titleLine = lines.find((line) => line.startsWith("#"));
  const fields = lines.reduce<{ label: string; value: string }[]>((items, line) => {
    const match = line.match(/^[-*]\s+([^:]+):\s*(.+)$/);
    if (!match) return items;

    const key = match[1].toLowerCase();
    items.push({
      label: REPORT_FIELD_LABELS[key] ?? match[1],
      value: cleanValue(match[2]),
    });
    return items;
  }, []);
  const summary =
    lines
      .filter((line) => !line.startsWith("#") && !line.match(/^[-*]\s+[^:]+:/))
      .map(cleanValue)
      .join(" ") ||
    message.preview ||
    "No summary was included with this message.";

  return {
    title: cleanValue(titleLine?.replace(/^#+\s*/, "") || message.subject || "AgentMail message"),
    summary,
    fields,
  };
}

function statusClass(message: AgentMailMessageSummary) {
  if (message.labels.includes("failed")) return "agentmail-status-failed";
  if (message.labels.includes("early_stop")) return "agentmail-status-stopped";
  if (message.labels.includes("success")) return "agentmail-status-success";
  return "agentmail-status-neutral";
}

export default function AgentMailPage() {
  const [messages, setMessages] = useState<AgentMailMessageSummary[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<AgentMailMessageDetail | null>(null);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const [isLoadingMessages, setIsLoadingMessages] = useState(true);
  const [isLoadingMessage, setIsLoadingMessage] = useState(false);
  const [isSendingMock, setIsSendingMock] = useState(false);
  const [inboxError, setInboxError] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

  async function loadMessages() {
    setIsLoadingMessages(true);
    setInboxError(null);

    try {
      const data = await fetchAgentMailMessages();
      setMessages(data.messages);
    } catch (err) {
      setInboxError(err instanceof Error ? err.message : "Failed to load AgentMail inbox");
    } finally {
      setIsLoadingMessages(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function loadInitialMessages() {
      setIsLoadingMessages(true);
      setInboxError(null);

      try {
        const data = await fetchAgentMailMessages();
        if (!cancelled) setMessages(data.messages);
      } catch (err) {
        if (!cancelled) {
          setInboxError(err instanceof Error ? err.message : "Failed to load AgentMail inbox");
        }
      } finally {
        if (!cancelled) setIsLoadingMessages(false);
      }
    }

    loadInitialMessages();
    return () => {
      cancelled = true;
    };
  }, []);

  async function sendMockRun() {
    setIsSendingMock(true);
    setSendError(null);

    try {
      const sent = await sendMockRunToAgentMail();
      await loadMessages();
      if (sent.message_id) await openMessage(sent.message_id);
    } catch (err) {
      setSendError(err instanceof Error ? err.message : "Mock run send failed");
    } finally {
      setIsSendingMock(false);
    }
  }

  async function openMessage(messageId: string) {
    setSelectedMessageId(messageId);
    setSelectedMessage(null);
    setIsLoadingMessage(true);
    setDetailError(null);

    try {
      const message = await fetchAgentMailMessage(messageId);
      setSelectedMessage(message);
    } catch (err) {
      setDetailError(err instanceof Error ? err.message : "Failed to load AgentMail message");
    } finally {
      setIsLoadingMessage(false);
    }
  }

  return (
    <div className="agentmail-surface flex flex-col gap-6">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex flex-col gap-1.5">
          <span className="label">Integration · 02</span>
          <h1 className="text-[34px] font-semibold leading-none tracking-tight">AgentMail</h1>
          <p className="max-w-3xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
            Apollo Labs sends run summaries to AgentMail and reads the run inbox back through the AgentMail
            messages API.
          </p>
        </div>
        <div className="rounded-md border hairline px-3 py-2 text-[12px]" style={{ color: "var(--muted-strong)" }}>
          <span className="label mr-2">Source</span>
          {HERMES_API_BASE_URL}
        </div>
      </header>

      <section className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_560px]">
        <div className="flex flex-col gap-6">
          <Card
            title="Inbox"
            hint="AgentMail messages"
            action={
              <div className="flex gap-2">
                <button className="btn-ghost disabled:opacity-60" type="button" onClick={loadMessages}>
                  Refresh
                </button>
                <button
                  className="btn-accent disabled:opacity-60"
                  type="button"
                  onClick={sendMockRun}
                  disabled={isSendingMock}
                >
                  {isSendingMock ? "Sending..." : "Mock run"}
                </button>
              </div>
            }
          >
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <div className="text-[13px] font-medium">{messages.length} messages</div>
                <div className="text-[11px]" style={{ color: "var(--muted-strong)" }}>
                  Latest AgentMail deliveries
                </div>
              </div>
              <span className="channel-pill">live inbox</span>
            </div>

            {sendError && (
              <div className="mb-3 rounded-md border hairline p-3 text-[12px]" style={{ color: "var(--status-failed)" }}>
                {sendError}
              </div>
            )}

            {isLoadingMessages ? (
              <EmptyState icon="..." title="Loading inbox" body="Reading messages from AgentMail." />
            ) : inboxError ? (
              <EmptyState
                icon="!"
                title="AgentMail not connected"
                body={`${inboxError}. Set AGENTMAIL_API_KEY and AGENTMAIL_INBOX_ID in the API .env, then refresh.`}
              />
            ) : messages.length === 0 ? (
              <EmptyState icon="✉" title="No inbox messages" body="Generate a mock run to send the first report." />
            ) : (
              <div className="flex flex-col gap-2">
                {messages.map((message) => (
                  <button
                    key={message.message_id}
                    className={`agentmail-row grid grid-cols-[minmax(0,1fr)_auto] gap-4 rounded-md border hairline p-3 text-left transition ${
                      selectedMessageId === message.message_id ? "agentmail-row-selected" : ""
                    }`}
                    type="button"
                    onClick={() => openMessage(message.message_id)}
                  >
                    <div className="min-w-0">
                      <div className="mb-1 flex flex-wrap items-center gap-2">
                        <span className={`agentmail-status ${statusClass(message)}`} />
                        <span className="truncate text-[15px] font-semibold leading-tight">
                          {message.subject ?? "Untitled message"}
                        </span>
                      </div>
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <span className="label">{messageTime(message)}</span>
                        <span className="label">{deliveryLabel(message)}</span>
                      </div>
                      <p className="line-clamp-2 text-[12px] leading-relaxed" style={{ color: "var(--muted-strong)" }}>
                        {message.preview ?? message.message_id}
                      </p>
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {message.labels.slice(0, 4).map((label) => (
                          <span key={label} className="channel-pill">
                            {label}
                          </span>
                        ))}
                      </div>
                    </div>
                    <span className="agentmail-open-indicator self-center">Open</span>
                  </button>
                ))}
              </div>
            )}
          </Card>
        </div>

        <Card title="Message" hint="AgentMail detail">
          {!selectedMessageId ? (
            <EmptyState icon="↗" title="Open a message" body="Select an inbox row to load the full AgentMail message." />
          ) : isLoadingMessage ? (
            <EmptyState icon="..." title="Loading message" body={selectedMessageId} />
          ) : detailError ? (
            <EmptyState icon="!" title="Message unavailable" body={detailError} />
          ) : selectedMessage ? (
            <MessageDetail message={selectedMessage} />
          ) : null}
        </Card>
      </section>
    </div>
  );
}

function MessageDetail({ message }: { message: AgentMailMessageDetail }) {
  const report = parseReport(message);
  const primaryFields = report.fields.slice(0, 6);
  const secondaryFields = report.fields.slice(6);
  const text = bodyText(message);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-2">
        <span className="label break-all">{message.message_id}</span>
        <h2 className="text-[22px] font-semibold leading-tight">{message.subject ?? report.title}</h2>
        <div className="grid gap-1 text-[12px]" style={{ color: "var(--muted-strong)" }}>
          <p>
            <span className="label mr-2">From</span>
            {message.from ?? "unknown"}
          </p>
          <p>
            <span className="label mr-2">To</span>
            {message.to.join(", ") || "unknown"}
          </p>
        </div>
      </div>

      <article className="agentmail-report">
        <div className="border-b hairline p-5">
          <span className="label">Apollo Labs report</span>
          <h3 className="mt-2 text-[24px] font-semibold leading-tight">{report.title}</h3>
          <p className="mt-3 text-[14px] leading-7" style={{ color: "var(--muted-strong)" }}>
            {report.summary}
          </p>
        </div>

        {primaryFields.length > 0 && (
          <div className="grid grid-cols-1 border-b hairline sm:grid-cols-2">
            {primaryFields.map((field) => (
              <div key={`${field.label}-${field.value}`} className="agentmail-metric border-b hairline p-4 sm:odd:border-r sm:[&:nth-last-child(-n+2)]:border-b-0">
                <div className="label">{field.label}</div>
                <div className="mt-1 break-words text-[15px] font-semibold">{field.value}</div>
              </div>
            ))}
          </div>
        )}

        {secondaryFields.length > 0 && (
          <div className="grid gap-3 p-5">
            {secondaryFields.map((field) => (
              <div key={`${field.label}-${field.value}`} className="grid gap-1">
                <span className="label">{field.label}</span>
                <span className="break-words text-[13px]" style={{ color: "var(--muted-strong)" }}>
                  {field.value}
                </span>
              </div>
            ))}
          </div>
        )}
      </article>

      {text && report.fields.length === 0 && (
        <pre className="max-h-[420px] overflow-auto rounded-md border hairline bg-background p-4 text-[12px] leading-6 whitespace-pre-wrap">
          {text}
        </pre>
      )}

      {message.attachments.length > 0 && (
        <div className="rounded-md border hairline p-3 text-[12px]" style={{ color: "var(--muted-strong)" }}>
          {message.attachments.length} attachment(s)
        </div>
      )}
    </div>
  );
}
