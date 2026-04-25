import type { ReactNode } from "react";

export function Card({
  title,
  code,
  action,
  children,
  padded = true,
}: {
  title?: string;
  code?: string;
  action?: ReactNode;
  children: ReactNode;
  padded?: boolean;
}) {
  return (
    <section className="border hairline" style={{ background: "var(--surface)" }}>
      {(title || action) && (
        <header className="flex items-center justify-between px-5 py-3 border-b hairline">
          <div className="flex items-baseline gap-3">
            {code && (
              <span className="text-[10px] tracking-[0.2em]" style={{ color: "var(--muted)" }}>
                {code}
              </span>
            )}
            <h3 className="serif italic text-[20px] leading-none">{title}</h3>
          </div>
          {action}
        </header>
      )}
      <div className={padded ? "p-5" : ""}>{children}</div>
    </section>
  );
}
