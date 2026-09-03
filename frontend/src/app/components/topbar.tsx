import {
  ChevronDown,
  Circle,
  Database,
} from "lucide-react";

export function Topbar() {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[var(--border)] bg-[rgba(255,255,255,0.92)] px-6 backdrop-blur">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-[var(--text-muted)]">
          Workspace
        </span>

        <span className="text-[var(--text-muted)]">
          /
        </span>

        <span className="font-medium text-[var(--text-primary)]">
          Production
        </span>
      </div>

      <div className="flex items-center gap-2">
        <button className="flex h-9 items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 text-[12px] font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-subtle)]">
          <Database
            size={14}
            strokeWidth={1.8}
          />

          shopdb

          <ChevronDown
            size={13}
            strokeWidth={1.8}
          />
        </button>

        <div className="flex h-9 items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--surface)] px-3">
          <Circle
            size={7}
            fill="currentColor"
            className="text-[var(--success)]"
          />

          <span className="text-[12px] font-medium text-[var(--text-secondary)]">
            Connected
          </span>
        </div>
      </div>
    </header>
  );
}
