import { RunCard } from "./components/RunCard";
import { runs, fmtNumber, statusVar } from "./lib/runs";

export default function HomePage() {
  const total = runs.length;
  const successes = runs.filter((r) => r.status === "success").length;
  const failures = runs.filter((r) => r.status === "failed").length;
  const successRate = Math.round((successes / total) * 100);
  const best = runs.reduce((m, r) => (r.bestReturn > m ? r.bestReturn : m), -Infinity);
  const avgDuration = Math.round(runs.reduce((s, r) => s + r.durationSec, 0) / total);
  const avgMin = Math.round(avgDuration / 60);

  return (
    <div className="px-6 md:px-10 py-10 flex flex-col gap-10">
      <Hero />

      <section className="grid grid-cols-2 lg:grid-cols-4 border hairline divide-x divide-y lg:divide-y-0 divide-hairline" style={{ background: "var(--surface)" }}>
        <Stat label="runs total" value={String(total)} sub="last 7 days" />
        <Stat label="success rate" value={`${successRate}%`} sub={`${successes} ok · ${failures} failed`} accent />
        <Stat label="best mean_return" value={fmtNumber(best)} sub="h2vq91 · roomba.flat-room.v2" />
        <Stat label="avg duration" value={`${avgMin}m`} sub="per supervised run" />
      </section>

      <Timeline />

      <section className="flex flex-col gap-4">
        <header className="flex items-end justify-between">
          <div>
            <div className="label">004 · Recent runs</div>
            <h2 className="serif text-[34px] leading-none mt-1">All runs</h2>
          </div>
          <div className="flex items-center gap-2">
            <button className="btn-ghost" type="button">All</button>
            <button className="btn-ghost" type="button">Success</button>
            <button className="btn-ghost" type="button">Running</button>
            <button className="btn-ghost" type="button">Failed</button>
          </div>
        </header>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {runs.map((r) => (
            <RunCard key={r.id} run={r} />
          ))}
        </div>
      </section>
    </div>
  );
}

function Hero() {
  return (
    <section className="flex flex-col gap-3">
      <div className="label">001 · Now</div>
      <h1 className="serif text-[64px] md:text-[88px] leading-[0.95] tracking-tight">
        Watch the agent <span className="italic" style={{ color: "var(--accent)" }}>think</span>,
        <br />
        then ship the postmortem.
      </h1>
      <p className="max-w-2xl text-[13px]" style={{ color: "var(--muted-strong)" }}>
        Hermes supervises every PPO run against templated worlds and Webots, writes one row per
        step into the telemetry store, then dispatches a structured report to AgentMail and
        files the lessons into Nia. Click any run below to inspect it.
      </p>
    </section>
  );
}

function Stat({ label, value, sub, accent = false }: { label: string; value: string; sub: string; accent?: boolean }) {
  return (
    <div className="p-5 flex flex-col gap-1">
      <span className="label">{label}</span>
      <span
        className="serif text-[40px] leading-none tabular-nums"
        style={{ color: accent ? "var(--accent)" : "var(--foreground)" }}
      >
        {value}
      </span>
      <span className="text-[10px] tracking-[0.16em] uppercase" style={{ color: "var(--muted)" }}>
        {sub}
      </span>
    </div>
  );
}

function Timeline() {
  // 84 hours back, runs plotted as bars.
  const span = 84;
  const refMs = new Date("2026-04-25T20:00:00Z").getTime();
  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-end justify-between">
        <div>
          <div className="label">003 · Timeline</div>
          <h2 className="serif text-[34px] leading-none mt-1">Runs over time</h2>
        </div>
        <div className="text-[10px] tracking-[0.16em] uppercase" style={{ color: "var(--muted)" }}>
          last {span}h · click any bar
        </div>
      </div>
      <div
        className="relative border hairline px-4 pt-10 pb-6"
        style={{ background: "var(--surface)" }}
      >
        <div
          aria-hidden
          className="absolute left-4 right-4 top-1/2 h-px"
          style={{ background: "var(--line)" }}
        />
        <div className="relative h-24">
          {runs.map((r) => {
            const hoursAgo = (refMs - new Date(r.startedAt).getTime()) / 3_600_000;
            const left = `${100 - (hoursAgo / span) * 100}%`;
            const height = 30 + Math.min(50, (r.bestReturn + 0.2) * 60);
            const color = statusVar(r.status);
            return (
              <a
                key={r.id}
                href={`/runs/${r.shortId}`}
                className="absolute -translate-x-1/2 group"
                style={{ left, bottom: "50%" }}
                title={`${r.shortId} · ${r.template}`}
              >
                <span
                  className="block w-[3px] transition-all group-hover:w-[5px]"
                  style={{ height, background: color, boxShadow: `0 0 16px ${color}` }}
                />
                <span
                  className="absolute left-1/2 -translate-x-1/2 mt-1 text-[9px] tracking-[0.16em] uppercase whitespace-nowrap opacity-0 group-hover:opacity-100"
                  style={{ color: "var(--muted-strong)", top: "100%" }}
                >
                  {r.shortId}
                </span>
              </a>
            );
          })}
        </div>
        <div className="flex justify-between text-[9px] tracking-[0.18em] uppercase mt-2" style={{ color: "var(--muted)" }}>
          <span>−{span}h</span>
          <span>−48h</span>
          <span>−24h</span>
          <span>now</span>
        </div>
      </div>
    </section>
  );
}
