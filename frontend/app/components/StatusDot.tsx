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
          width: 8,
          height: 8,
          borderRadius: 999,
          background: color,
          boxShadow: `0 0 12px ${color}`,
        }}
        aria-hidden
      />
      {withLabel && (
        <span className="text-[10px] tracking-[0.18em] uppercase" style={{ color }}>
          {statusLabel(status)}
        </span>
      )}
    </span>
  );
}
