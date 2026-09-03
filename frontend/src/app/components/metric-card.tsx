import type { ReactNode } from "react";

type MetricCardProps = {
  label: string;
  value: string;
  description: string;
  icon?: ReactNode;
};

export function MetricCard({
  label,
  value,
  description,
  icon,
}: MetricCardProps) {
  return (
    <div className="border-r border-[var(--border)] px-5 first:pl-0 last:border-r-0">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[12px] font-medium text-[var(--text-secondary)]">
          {label}
        </span>

        {icon ? (
          <span className="text-[var(--text-muted)]">
            {icon}
          </span>
        ) : null}
      </div>

      <div className="text-[28px] font-semibold tracking-[-0.04em] text-[var(--text-primary)]">
        {value}
      </div>

      <div className="mt-1 text-[11px] text-[var(--text-muted)]">
        {description}
      </div>
    </div>
  );
}