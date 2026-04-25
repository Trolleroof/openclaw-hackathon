"use client";

import { useEffect, useState } from "react";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import {
  fetchAgentMailMessage,
  fetchAgentMailMessages,
  HERMES_API_BASE_URL,
  type AgentMailMessageDetail,
  type AgentMailMessageSummary,
} from "../lib/agentmail";

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

function sourceLabel(message: AgentMailMessageSummary) {
  return message.source === "historical_seed" ? "historical seed" : "live run report";
}

export default function AgentMailPage() {
  const [messages, setMessages] = useState<AgentMailMessageSummary[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<AgentMailMessageDetail | null>(null);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const [isLoadingMessages, setIsLoadingMessages] = useState(true);
  const [isLoadingMessage, setIsLoadingMessage] = useState(false);
  const [inboxError, setInboxError] = useState<string | null>(null);
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
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1">
        <span className="label">Integration · 02</span>
        <h1 className="text-[32px] font-semibold tracking-tight">AgentMail</h1>
        <p className="max-w-2xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
          Hermes keeps a local run mail feed backed by run reports. Historical uploads are seeded
          here, and every future finalized run appears here automatically.
        </p>
      </header>

      <section className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_520px] gap-6">
        <div className="flex flex-col gap-6">
          <Card title="Inbox" hint="AgentMail messages">
            <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="text-[12px]" style={{ color: "var(--muted-strong)" }}>
                {messages.length} Hermes messages from {HERMES_API_BASE_URL}
              </div>
              <button className="btn-ghost disabled:opacity-60" type="button" onClick={loadMessages}>
                Refresh
              </button>
            </div>

            {isLoadingMessages ? (
              <EmptyState icon="..." title="Loading inbox" body="Reading the Hermes run mail feed." />
            ) : inboxError ? (
              <EmptyState
                icon="!"
                title="AgentMail feed unavailable"
                body={inboxError}
              />
            ) : messages.length === 0 ? (
              <EmptyState icon="✉" title="No run messages" body="Once Hermes has seeded or finalized runs, they will appear here." />
            ) : (
              <div className="flex flex-col">
                {messages.map((message) => (
                  <div
                    key={message.message_id}
                    className="grid grid-cols-[1fr_auto] gap-4 py-3 border-b hairline last:border-b-0"
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold">{message.subject ?? "Untitled message"}</span>
                        <span className="label">{deliveryLabel(message)}</span>
                        <span className="label">{sourceLabel(message)}</span>
                        <span className="label">{messageTime(message)}</span>
                      </div>
                      <p className="mt-1 text-[12px] truncate" style={{ color: "var(--muted-strong)" }}>
                        {message.preview ?? message.run_id}
                      </p>
                      <div className="mt-1 flex flex-wrap gap-2">
                        {message.labels.slice(0, 4).map((label) => (
                          <span key={label} className="channel-pill">
                            {label}
                          </span>
                        ))}
                      </div>
                    </div>
                    <button className="btn-ghost self-start" type="button" onClick={() => openMessage(message.message_id)}>
                      Open
                    </button>
                  </div>
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
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1">
                <div className="flex flex-wrap gap-2">
                  <span className="label">{selectedMessage.message_id}</span>
                  <span className="label">{sourceLabel(selectedMessage)}</span>
                  <span className="label">{selectedMessage.run_id}</span>
                </div>
                <h2 className="text-[20px] font-semibold leading-tight">{selectedMessage.subject ?? "Untitled message"}</h2>
                <p className="text-[12px]" style={{ color: "var(--muted-strong)" }}>
                  From {selectedMessage.from ?? "unknown"} to {selectedMessage.to.join(", ") || "unknown"}
                </p>
              </div>

              {(selectedMessage.external_message_id || selectedMessage.external_thread_id) && (
                <div className="rounded-md border hairline p-3 text-[12px]" style={{ color: "var(--muted-strong)" }}>
                  {selectedMessage.external_message_id && <div>External message: {selectedMessage.external_message_id}</div>}
                  {selectedMessage.external_thread_id && <div>External thread: {selectedMessage.external_thread_id}</div>}
                </div>
              )}

              {selectedMessage.html ? (
                <iframe
                  className="min-h-[420px] w-full rounded-md border hairline bg-background"
                  sandbox=""
                  srcDoc={selectedMessage.html}
                  title="AgentMail message HTML"
                />
              ) : (
                <pre className="max-h-[520px] overflow-auto rounded-md border hairline bg-background p-3 text-[12px] whitespace-pre-wrap">
                  {selectedMessage.extracted_text ?? selectedMessage.text ?? selectedMessage.preview ?? "No message body."}
                </pre>
              )}

              {selectedMessage.attachments.length > 0 && (
                <div className="rounded-md border hairline p-3 text-[12px]" style={{ color: "var(--muted-strong)" }}>
                  {selectedMessage.attachments.length} attachment(s)
                </div>
              )}
            </div>
          ) : null}
        </Card>
      </section>
    </div>
  );
}
