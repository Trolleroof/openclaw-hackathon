import { Card } from "../components/Card";

const LESSONS = [
  {
    id: "L-024",
    title: "Higher entropy_coef escapes flat-room plateaus",
    source: "run h2vq91 · roomba.flat-room.v2",
    body: "Bumping ent_coef from 0.005 → 0.012 lifted mean_return from 0.61 → 0.82. Confirmed across two seeds.",
    tags: ["ppo", "entropy", "flat-room"],
  },
  {
    id: "L-023",
    title: "Collision-reset penalty above 0.4 triggers reward collapse",
    source: "run p83lqf · obstacle-grid.4x4",
    body: "Agent freezes in start cell when stepping into obstacle costs more than reaching goal. Cap penalty <= 0.3.",
    tags: ["reward-shaping", "obstacle-grid"],
  },
  {
    id: "L-022",
    title: "500k timesteps suffices for v2 templates",
    source: "runs h2vq91, t7cm12",
    body: "Both v2 runs converged before 450k steps. v1 plateaus around 400k. Set total_timesteps accordingly.",
    tags: ["budget", "timesteps"],
  },
  {
    id: "L-021",
    title: "Webots PROTO path must include hermes/protos before launch",
    source: "run qq04mn · obstacle-grid.6x6",
    body: "Missing HermesSpawn proto aborted run in 8s. Add path check to supervisor preflight.",
    tags: ["webots", "infra"],
  },
];

const SOURCES = [
  { name: "openclaw-hackathon repo", count: 41, kind: "code" },
  { name: "Webots supervisor docs", count: 18, kind: "external" },
  { name: "Gymnasium docs", count: 12, kind: "external" },
  { name: "Run postmortems", count: 24, kind: "generated" },
];

export default function MemoryPage() {
  return (
    <div className="px-6 md:px-10 py-10 flex flex-col gap-8">
      <header className="flex flex-col gap-2">
        <div className="label">03 · Organizational memory</div>
        <h1 className="serif text-[56px] leading-[0.95] tracking-tight">
          Nia <span className="italic" style={{ color: "var(--accent)" }}>— lessons indexed</span>
        </h1>
        <p className="max-w-2xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
          W&amp;B holds the numbers. Nia holds the narrative — what we tried, what worked, what
          failed, what the manual says about why. Hermes will query this index before each new
          world or config so the next run is grounded in what already happened.
        </p>
      </header>

      <section className="flex items-center gap-3 border hairline px-4 py-3" style={{ background: "var(--surface)" }}>
        <span style={{ color: "var(--muted)" }}>▸</span>
        <input
          disabled
          placeholder="search lessons · e.g. 'why did obstacle-grid fail last week'"
          className="flex-1 bg-transparent outline-none text-[13px] placeholder:opacity-60"
          style={{ color: "var(--foreground)" }}
        />
        <span className="kbd">/</span>
        <span className="label">stub</span>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex items-end justify-between">
            <h2 className="serif italic text-[24px]">Recent lessons</h2>
            <span className="label">{LESSONS.length} entries</span>
          </div>
          {LESSONS.map((l) => (
            <article key={l.id} className="border hairline p-5 flex flex-col gap-3" style={{ background: "var(--surface)" }}>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-[10px] tracking-[0.18em] uppercase" style={{ color: "var(--accent)" }}>{l.id}</div>
                  <h3 className="serif text-[24px] leading-tight mt-1">{l.title}</h3>
                  <div className="text-[11px] mt-1" style={{ color: "var(--muted)" }}>{l.source}</div>
                </div>
                <button className="btn-ghost" type="button">Open</button>
              </div>
              <p className="text-[13px]" style={{ color: "var(--muted-strong)" }}>{l.body}</p>
              <div className="flex gap-2 flex-wrap">
                {l.tags.map((t) => (
                  <span
                    key={t}
                    className="text-[10px] tracking-[0.16em] uppercase px-2 py-0.5 border hairline"
                    style={{ color: "var(--muted-strong)" }}
                  >
                    #{t}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>

        <div className="flex flex-col gap-6">
          <Card title="Indexed sources" code="§ stub">
            <ul className="flex flex-col">
              {SOURCES.map((s) => (
                <li key={s.name} className="flex items-center justify-between py-2.5 border-b hairline last:border-b-0">
                  <div className="flex flex-col">
                    <span className="text-[13px]" style={{ color: "var(--foreground)" }}>{s.name}</span>
                    <span className="label">{s.kind}</span>
                  </div>
                  <span className="serif text-[22px] tabular-nums" style={{ color: "var(--accent)" }}>{s.count}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card title="Connect Nia" code="§ stub">
            <div className="flex flex-col gap-3">
              <label className="flex flex-col gap-1">
                <span className="label">API key</span>
                <span className="px-3 py-2 border hairline text-[12px]" style={{ background: "var(--background)", color: "var(--muted)" }}>
                  •••••••••• not set
                </span>
              </label>
              <button className="btn-accent" type="button">Authorize Nia</button>
              <p className="text-[10px] tracking-[0.18em] uppercase" style={{ color: "var(--muted)" }}>
                docs.trynia.ai · wire later
              </p>
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}
