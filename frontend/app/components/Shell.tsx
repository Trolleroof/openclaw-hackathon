"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const NAV: { label: string; href: string }[] = [
  { label: "Runs", href: "/" },
  { label: "AgentMail", href: "/agentmail" },
  { label: "Memory", href: "/memory" },
];

export function Shell({ children }: { children: ReactNode }) {
  const path = usePathname();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b hairline">
        <div className="mx-auto max-w-6xl px-6 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <span
              aria-hidden
              className="inline-block w-2 h-2 rounded-full"
              style={{ background: "var(--accent)" }}
            />
            <span className="text-[15px] font-semibold tracking-tight">Hermes</span>
            <span className="label hidden sm:inline ml-2">RL console</span>
          </Link>

          <nav className="flex items-center gap-1">
            {NAV.map((item) => {
              const active =
                item.href === "/"
                  ? path === "/" || path.startsWith("/runs")
                  : path.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="px-3 py-1.5 text-[13px] rounded-md transition-colors"
                  style={{
                    color: active ? "var(--foreground)" : "var(--muted-strong)",
                    background: active ? "var(--surface-2)" : "transparent",
                  }}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-6 py-10">{children}</div>
      </main>

      <footer className="border-t hairline">
        <div className="mx-auto max-w-6xl px-6 h-10 flex items-center justify-between text-[11px]" style={{ color: "var(--muted)" }}>
          <span>hermes · v0.1.0</span>
          <span>not connected</span>
        </div>
      </footer>
    </div>
  );
}
