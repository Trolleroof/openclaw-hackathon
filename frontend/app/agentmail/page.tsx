import { Card } from "../components/Card";
import { runs, fmtRelative, statusLabel } from "../lib/runs";

export default function AgentMailPage() {
  const finished = runs.filter((r) => r.status !== "running");
  return (
    <div className="px-6 md:px-10 py-10 flex flex-col gap-8">
      <header className="flex flex-col gap-2">
        <div className="label">02 · Async human channel</div>
        <h1 className="serif text-[56px] leading-[0.95] tracking-tight">
          AgentMail <span className="italic" style={{ color: "var(--accent)" }}>— outbox</span>
        </h1>
        <p className="max-w-2xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
          When a supervised run exits, Hermes hands the same structured report it already builds
          to AgentMail. One API call, one envelope, one human ping. This view is a placeholder;
          we will wire the actual SDK in Phase 2.
        </p>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 flex flex-col gap-6">
          <Card title="Recent dispatches" code="§ outbox.tail">
            <div className="flex flex-col">
              {finished.map((r) => (
                <div key={r.id} className="grid grid-cols-[80px_1fr_auto] gap-4 py-3 border-b hairline last:border-b-0 items-baseline">
                  <span className="text-[10px] tracking-[0.18em] uppercase" style={{ color: "var(--muted)" }}>
                    {fmtRelative(r.startedAt)}
                  </span>
                  <div className="min-w-0">
                    <div className="text-[13px] truncate">
                      <span style={{ color: "var(--foreground)" }}>[RL] run {r.shortId}</span>{" "}
                      <span style={{ color: "var(--muted-strong)" }}>
                        {statusLabel(r.status).toLowerCase()} · {r.template}
                      </span>
                    </div>
                    <div className="text-[11px]" style={{ color: "var(--muted)" }}>
                      to nikhi@ucsd.edu · mean_return {r.meanReturn.toFixed(2)} · 1 attachment
                    </div>
                  </div>
                  <button className="btn-ghost" type="button">Open</button>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Envelope preview" code="§ latest · h2vq91">
            <div className="border hairline" style={{ background: "var(--background)" }}>
              <div className="px-4 py-3 border-b hairline grid grid-cols-[80px_1fr] gap-4 text-[12px]">
                <span className="label">From</span><span>hermes-bot@openclaw.dev</span>
                <span className="label">To</span><span>nikhi@ucsd.edu</span>
                <span className="label">Subject</span><span style={{ color: "var(--accent)" }}>[RL] run h2vq91 success</span>
              </div>
              <div className="p-5 text-[13px] leading-[1.75]" style={{ color: "var(--muted-strong)" }}>
                <p>
                  <span className="serif italic text-[16px]" style={{ color: "var(--foreground)" }}>
                    Run h2vq91 finished cleanly.
                  </span>{" "}
                  Final mean_return <strong style={{ color: "var(--foreground)" }}>0.82</strong> (best 0.91)
                  on template <em>roomba.flat-room.v2</em>, 500k steps in 1h 13m.
                </p>
                <p className="mt-3">
                  Best policy committed to <code>s3://hermes/ckpt/h2vq91/best.pt</code>.
                  Curves and config snapshot available in the console.
                </p>
                <p className="mt-3" style={{ color: "var(--muted)" }}>
                  — hermes-bot
                </p>
              </div>
            </div>
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <Card title="Settings" code="§ stub">
            <div className="flex flex-col gap-3">
              <Field k="Inbox" v="nikhi@ucsd.edu" />
              <Field k="Trigger" v="on run.exit (success | fail | early_stop)" />
              <Field k="Format" v="markdown + json attachment" />
              <Field k="API key" v="•••••••••• not set" />
              <button className="btn-accent mt-2" type="button">Connect AgentMail</button>
              <p className="text-[10px] tracking-[0.18em] uppercase" style={{ color: "var(--muted)" }}>
                Stub · docs.agentmail.to
              </p>
            </div>
          </Card>

          <Card title="Health" code="§ stub">
            <div className="flex flex-col gap-2 text-[12px]">
              <Row k="last dispatch" v="5h ago" />
              <Row k="queued" v="0" />
              <Row k="failures (24h)" v="0" />
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}

function Field({ k, v }: { k: string; v: string }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="label">{k}</span>
      <span className="px-3 py-2 border hairline text-[12px]" style={{ background: "var(--background)", color: "var(--foreground)" }}>
        {v}
      </span>
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
