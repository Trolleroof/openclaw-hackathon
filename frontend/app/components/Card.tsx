import type { ReactNode } from "react";

export function Card({
  title,
  hint,
  action,
  children,
  padded = true,
}: {
  title?: string;
  hint?: string;
  action?: ReactNode;
  children: ReactNode;
  padded?: boolean;
}) {
  return (
    <section className="card">
      {(title || action) && (
        <header className="flex items-center justify-between px-5 py-3 border-b hairline">
          <div className="flex items-baseline gap-3">
            <h3 className="text-[14px] font-semibold tracking-tight">{title}</h3>
            {hint && <span className="label">{hint}</span>}
          </div>
          {action}
        </header>
      )}
      <div className={padded ? "p-5" : ""}>{children}</div>
    </section>
  );
}
