"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  BrainCircuit,
  Database,
  Gauge,
  SearchCode,
  Settings,
  TableProperties,
} from "lucide-react";

import { cn } from "../lib/utils";

const navigation = [
  {
    name: "Overview",
    href: "/",
    icon: Gauge,
  },
  {
    name: "Query Analyzer",
    href: "/analyzer",
    icon: SearchCode,
  },
  {
    name: "Recommendations",
    href: "/recommendations",
    icon: TableProperties,
  },
  {
    name: "Benchmarks",
    href: "/benchmarks",
    icon: BarChart3,
  },
  {
    name: "Workload",
    href: "/workload",
    icon: Activity,
  },
  {
    name: "Models",
    href: "/models",
    icon: BrainCircuit,
  },
  {
    name: "Databases",
    href: "/databases",
    icon: Database,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-40 w-[248px] border-r border-[var(--border)] bg-[var(--surface)]">
      <div className="flex h-16 items-center border-b border-[var(--border)] px-5">
        <div className="flex items-center gap-3">
          <div className="flex size-8 items-center justify-center rounded-md border border-[var(--border-strong)] bg-[#17191c] text-[11px] font-semibold tracking-tight text-white">
            DB
          </div>

          <div>
            <div className="text-sm font-semibold tracking-[-0.01em] text-[var(--text-primary)]">
              DBOptima
            </div>

            <div className="text-[11px] text-[var(--text-muted)]">
              Performance Platform
            </div>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100%-64px)] flex-col">
        <nav className="flex-1 px-3 py-4">
          <div className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--text-muted)]">
            Workspace
          </div>

          <div className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;

              const active =
                pathname === item.href ||
                (item.href !== "/" &&
                  pathname.startsWith(item.href));

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex h-9 items-center gap-3 rounded-md px-2.5 text-[13px] font-medium transition-colors",
                    active
                      ? "bg-[var(--surface-subtle)] text-[var(--text-primary)]"
                      : "text-[var(--text-secondary)] hover:bg-[var(--surface-subtle)] hover:text-[var(--text-primary)]",
                  )}
                >
                  <Icon
                    size={16}
                    strokeWidth={1.8}
                  />

                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>
        </nav>

        <div className="border-t border-[var(--border)] p-3">
          <Link
            href="/settings"
            className="flex h-9 items-center gap-3 rounded-md px-2.5 text-[13px] font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-subtle)] hover:text-[var(--text-primary)]"
          >
            <Settings
              size={16}
              strokeWidth={1.8}
            />

            Settings
          </Link>
        </div>
      </div>
    </aside>
  );
}