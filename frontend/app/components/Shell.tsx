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
            <span className="text-[15px] font-semibold tracking-tight">Apollo Labs</span>
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

      <div className="mx-auto max-w-6xl px-6 pt-3">
        <p className="text-[12px] rounded-md border hairline px-3 py-2" style={{ color: "var(--muted-strong)" }}>
          <span className="label mr-2">Mode</span>
          Read-only. Training, mock reports, and deletions are not available here—clone the repo and run the API locally to change data.
        </p>
      </div>

      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-6 py-10">{children}</div>
      </main>
    </div>
  );
}
