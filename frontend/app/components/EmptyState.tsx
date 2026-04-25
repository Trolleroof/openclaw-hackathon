import type { ReactNode } from "react";

export function EmptyState({
  title,
  body,
  action,
  icon = "—",
}: {
  title: string;
  body: string;
  action?: ReactNode;
  icon?: string;
}) {
  return (
    <div className="card p-10 flex flex-col items-center text-center gap-3">
      <div
        className="w-10 h-10 rounded-full border hairline flex items-center justify-center mono text-[14px]"
        style={{ color: "var(--muted)" }}
      >
        {icon}
      </div>
      <h3 className="text-[18px] font-semibold tracking-tight">{title}</h3>
      <p className="max-w-md text-[13px]" style={{ color: "var(--muted-strong)" }}>
        {body}
      </p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
