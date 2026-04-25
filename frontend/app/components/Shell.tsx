"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const NAV: { label: string; href: string; code: string }[] = [
  { label: "Runs", href: "/", code: "01" },
  { label: "AgentMail", href: "/agentmail", code: "02" },
  { label: "Nia memory", href: "/memory", code: "03" },
];

export function Shell({ children }: { children: ReactNode }) {
  const path = usePathname();
  return (
    <div className="min-h-screen flex flex-col">
      <Header path={path} />
      <div className="flex-1 flex">
        <aside className="hidden md:flex w-56 shrink-0 border-r hairline">
          <nav className="w-full p-6 flex flex-col gap-1">
            <div className="label mb-3">Sections</div>
            {NAV.map((item) => {
              const active =
                item.href === "/"
                  ? path === "/" || path.startsWith("/runs")
                  : path.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="group flex items-center justify-between px-2 py-2 border-l-2 transition-colors"
                  style={{
                    borderColor: active ? "var(--accent)" : "transparent",
                    color: active ? "var(--foreground)" : "var(--muted-strong)",
                  }}
                >
                  <span className="flex items-baseline gap-3">
                    <span
                      className="text-[10px]"
                      style={{ color: active ? "var(--accent)" : "var(--muted)" }}
                    >
                      {item.code}
                    </span>
                    <span className="serif italic text-[18px] leading-none">{item.label}</span>
                  </span>
                  <span
                    className="text-[10px] opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ color: "var(--accent)" }}
                  >
                    →
                  </span>
                </Link>
              );
            })}
            <div className="mt-auto pt-8 text-[10px] leading-relaxed" style={{ color: "var(--muted)" }}>
              <div className="label mb-2">System</div>
              <div>hermes-api · v0.1.0</div>
              <div>region · sfo-2</div>
              <div>uptime · 04d 11h</div>
            </div>
          </nav>
        </aside>
        <main className="flex-1 min-w-0">{children}</main>
      </div>
      <Ticker />
    </div>
  );
}

function Header({ path }: { path: string }) {
  return (
    <header className="px-6 md:px-10 py-6 border-b hairline flex items-end justify-between gap-6">
      <div className="flex items-baseline gap-4">
        <Link href="/" className="flex items-baseline gap-3">
          <span className="serif text-[42px] leading-none tracking-tight">Hermes</span>
          <span className="serif italic text-[18px]" style={{ color: "var(--muted-strong)" }}>
            — a small console for training runs
          </span>
        </Link>
      </div>
      <div className="hidden lg:flex items-center gap-2">
        <button className="btn-ghost" type="button">
          <span style={{ color: "var(--muted)" }}>⌘K</span>
          <span>Search</span>
        </button>
        <button className="btn-accent" type="button">+ New run</button>
      </div>
      <div className="sr-only">{path}</div>
    </header>
  );
}

function Ticker() {
  const items = [
    "run kw0c8x · step 180,224 · mean_return 0.61",
    "agentmail · last dispatch 5h ago · nikhi@ucsd.edu",
    "nia · 24 indexed lessons · 3 new this week",
    "webots · supervisor proto OK · 1 worker pool",
    "telemetry db · 2,481 step rows · latency 12ms",
  ];
  const text = items.join("   ···   ");
  return (
    <div
      className="border-t hairline overflow-hidden whitespace-nowrap text-[10px] tracking-[0.22em] uppercase py-1.5"
      style={{ color: "var(--muted)", background: "var(--surface)" }}
    >
      <div className="ticker inline-block">
        <span className="px-6">{text}</span>
        <span className="px-6">{text}</span>
      </div>
    </div>
  );
}
