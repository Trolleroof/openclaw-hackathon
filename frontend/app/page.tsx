import { RunCard } from "./components/RunCard";
import { EmptyState } from "./components/EmptyState";
import { runs } from "./lib/runs";

export default function HomePage() {
  return (
    <div className="flex flex-col gap-8">
      <section className="flex items-end justify-between gap-4">
        <div>
          <span className="label">Dashboard</span>
          <h1 className="text-[32px] font-semibold tracking-tight mt-1">Runs</h1>
          <p className="text-[13px] mt-1" style={{ color: "var(--muted-strong)" }}>
            Each box is one supervised training run. Click to inspect config, metrics, and logs.
          </p>
        </div>
        <button className="btn-accent" type="button">+ New run</button>
      </section>

      <section className="grid grid-cols-2 md:grid-cols-4 card divide-x divide-y md:divide-y-0 divide-hairline">
        <Stat label="runs" value={runs.length.toString()} />
        <Stat label="success rate" value="—" />
        <Stat label="best return" value="—" />
        <Stat label="avg duration" value="—" />
      </section>

      {runs.length === 0 ? (
        <EmptyState
          icon="+"
          title="No runs yet"
          body="Once Hermes dispatches a training run, it will show up here. Connect the API to start streaming real data."
          action={
            <div className="flex gap-2">
              <button className="btn-accent" type="button">+ New run</button>
              <button className="btn-ghost" type="button">Connect Hermes API</button>
            </div>
          }
        />
      ) : (
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {runs.map((r) => (
            <RunCard key={r.id} run={r} />
          ))}
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-5 flex flex-col gap-1">
      <span className="label">{label}</span>
      <span className="text-[28px] font-semibold tracking-tight tabular-nums">{value}</span>
    </div>
  );
}
