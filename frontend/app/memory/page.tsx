import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";

export default function MemoryPage() {
  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1">
        <span className="label">Integration · 03</span>
        <h1 className="text-[32px] font-semibold tracking-tight">Nia memory</h1>
        <p className="max-w-2xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
          W&amp;B holds the numbers. Nia holds the narrative — what we tried, what worked,
          what failed. Not yet connected.
        </p>
      </header>

      <section className="flex items-center gap-3 card px-4 py-3">
        <span style={{ color: "var(--muted)" }}>▸</span>
        <input
          disabled
          placeholder="search lessons · connect Nia to enable"
          className="flex-1 bg-transparent outline-none text-[13px] placeholder:opacity-60"
        />
        <span className="label">stub</span>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <EmptyState
            icon="§"
            title="No lessons indexed"
            body="Hermes will append a short note per run (success/fail + 2–3 bullets) once Nia is connected. Past notes will surface here and feed back into the next world generation."
          />
        </div>

        <div className="flex flex-col gap-6">
          <Card title="Sources" hint="to be indexed">
            <ul className="flex flex-col text-[13px]">
              {["openclaw-hackathon repo", "Webots supervisor docs", "Gymnasium docs", "Run postmortems"].map((s) => (
                <li key={s} className="flex items-center justify-between py-2 border-b hairline last:border-b-0">
                  <span>{s}</span>
                  <span className="label">0</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </section>
    </div>
  );
}
