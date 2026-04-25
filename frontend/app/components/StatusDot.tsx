import type { RunStatus } from "../lib/runs";
import { statusLabel, statusVar } from "../lib/runs";

export function StatusDot({ status, withLabel = false }: { status: RunStatus; withLabel?: boolean }) {
  const color = statusVar(status);
  const isRunning = status === "running";
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className={isRunning ? "pulse-dot" : ""}
        style={{
          display: "inline-block",
          width: 7,
          height: 7,
          borderRadius: 999,
          background: color,
        }}
        aria-hidden
      />
      {withLabel && (
        <span className="label" style={{ color }}>{statusLabel(status)}</span>
      )}
    </span>
  );
}
