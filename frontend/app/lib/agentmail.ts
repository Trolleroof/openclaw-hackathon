export type AgentMailMessageSummary = {
  inbox_id: string;
  message_id: string;
  thread_id?: string | null;
  labels: string[];
  timestamp?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  from?: string | null;
  to: string[];
  cc: string[];
  bcc: string[];
  subject?: string | null;
  preview?: string | null;
  size?: number | null;
};

export type AgentMailMessageDetail = AgentMailMessageSummary & {
  text?: string | null;
  html?: string | null;
  extracted_text?: string | null;
  extracted_html?: string | null;
  attachments: Record<string, unknown>[];
  raw: Record<string, unknown>;
};

export type AgentMailMessageList = {
  count: number;
  messages: AgentMailMessageSummary[];
  next_page_token?: string | null;
};

export type AgentMailMockSendResponse = {
  run_id: string;
  delivery_status: string;
  message_id?: string | null;
  thread_id?: string | null;
  error?: string | null;
};

export const HERMES_API_BASE_URL =
  process.env.NEXT_PUBLIC_HERMES_API_BASE_URL ?? "http://127.0.0.1:8000";

async function readJson<T>(response: Response, action: string): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? `: ${body.detail}` : "";
    throw new Error(`${action} failed (${response.status})${detail}`);
  }

  return response.json();
}

export async function fetchAgentMailMessages(limit = 25): Promise<AgentMailMessageList> {
  const response = await fetch(`${HERMES_API_BASE_URL}/api/v1/agentmail/messages?limit=${limit}`, {
    headers: { Accept: "application/json" },
  });

  return readJson<AgentMailMessageList>(response, "Loading AgentMail inbox");
}

export async function fetchAgentMailMessage(messageId: string): Promise<AgentMailMessageDetail> {
  const response = await fetch(
    `${HERMES_API_BASE_URL}/api/v1/agentmail/messages/${encodeURIComponent(messageId)}`,
    { headers: { Accept: "application/json" } },
  );

  return readJson<AgentMailMessageDetail>(response, "Loading AgentMail message");
}

export async function sendMockRunToAgentMail(): Promise<AgentMailMockSendResponse> {
  const response = await fetch(`${HERMES_API_BASE_URL}/api/v1/agentmail/mock-run`, {
    method: "POST",
    headers: { Accept: "application/json" },
  });

  return readJson<AgentMailMockSendResponse>(response, "Sending mock run to AgentMail");
}
