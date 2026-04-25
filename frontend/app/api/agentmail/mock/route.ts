import { NextResponse } from "next/server";
import { buildMockAgentMailPayload } from "../../../lib/agentmail";
import { getRun } from "../../../lib/runs";

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as { runId?: string } | null;
  const run = getRun(body?.runId ?? "h2vq91");

  if (!run) {
    return NextResponse.json({ error: "Run not found" }, { status: 404 });
  }

  const payload = buildMockAgentMailPayload(run);

  return NextResponse.json({
    ok: true,
    mocked: true,
    provider: "agentmail",
    sentAt: new Date().toISOString(),
    payload,
  });
}
