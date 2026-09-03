import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  CheckCircle2,
  Database,
  Gauge,
} from "lucide-react";

import { AppShell } from "./components/app-shell";
import { MetricCard } from "./components/metric-card";

const recentOptimizations = [
  {
    query:
      "SELECT * FROM orders WHERE customer_id = ? AND status = ? ORDER BY created_at DESC",
    status: "Recommended",
    expectedGain: "99.78%",
    measuredGain: "99.88%",
    latency: "18.415 → 0.022 ms",
  },
  {
    query:
      "SELECT * FROM products WHERE category_id = ? AND price > ?",
    status: "Review",
    expectedGain: "14.20%",
    measuredGain: "11.84%",
    latency: "7.281 → 6.419 ms",
  },
  {
    query:
      "SELECT * FROM orders WHERE created_at >= ? ORDER BY created_at DESC",
    status: "Rejected",
    expectedGain: "2.41%",
    measuredGain: "-1.12%",
    latency: "4.892 → 4.947 ms",
  },
];

function StatusBadge({
  status,
}: {
  status: string;
}) {
  const styles =
    status === "Recommended"
      ? "bg-[var(--success-soft)] text-[var(--success)]"
      : status === "Review"
        ? "bg-[var(--warning-soft)] text-[var(--warning)]"
        : "bg-[var(--danger-soft)] text-[var(--danger)]";

  return (
    <span
      className={`inline-flex rounded px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.04em] ${styles}`}
    >
      {status}
    </span>
  );
}

export default function Home() {
  return (
    <AppShell>
      <div className="mx-auto max-w-[1440px]">
        <section className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-[24px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
              Overview
            </h1>

            <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
              Database performance and optimization activity.
            </p>
          </div>

          <button className="flex h-9 items-center gap-2 rounded-md bg-[#17191c] px-3.5 text-[12px] font-medium text-white transition-opacity hover:opacity-90">
            Analyze query

            <ArrowRight
              size={14}
              strokeWidth={1.8}
            />
          </button>
        </section>

        <section className="mb-8 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-5 py-5">
          <div className="grid grid-cols-4">
            <MetricCard
              label="Connected database"
              value="shopdb"
              description="PostgreSQL target"
              icon={
                <Database
                  size={16}
                  strokeWidth={1.8}
                />
              }
            />

            <MetricCard
              label="Analyzed queries"
              value="35"
              description="31 latency samples"
              icon={
                <Activity
                  size={16}
                  strokeWidth={1.8}
                />
              }
            />

            <MetricCard
              label="Recommended indexes"
              value="35"
              description="100% successful history"
              icon={
                <CheckCircle2
                  size={16}
                  strokeWidth={1.8}
                />
              }
            />

            <MetricCard
              label="Median measured gain"
              value="99.88%"
              description="Latest optimization"
              icon={
                <Gauge
                  size={16}
                  strokeWidth={1.8}
                />
              }
            />
          </div>
        </section>

        <div className="grid grid-cols-[minmax(0,1fr)_360px] gap-6">
          <section className="overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface)]">
            <div className="flex h-14 items-center justify-between border-b border-[var(--border)] px-4">
              <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                Recent optimizations
              </h2>

              <button className="text-[11px] font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
                View all
              </button>
            </div>

            <div>
              {recentOptimizations.map(
                (item, index) => (
                  <div
                    key={item.query}
                    className={`grid grid-cols-[minmax(0,1fr)_110px_110px_120px] items-center gap-4 px-4 py-4 ${
                      index !==
                      recentOptimizations.length -
                        1
                        ? "border-b border-[var(--border)]"
                        : ""
                    }`}
                  >
                    <div className="min-w-0">
                      <div className="truncate font-mono text-[11px] text-[var(--text-primary)]">
                        {item.query}
                      </div>

                      <div className="mt-2">
                        <StatusBadge
                          status={item.status}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="text-[10px] uppercase tracking-[0.04em] text-[var(--text-muted)]">
                        Expected
                      </div>

                      <div className="mt-1 text-[12px] font-medium text-[var(--text-primary)]">
                        {item.expectedGain}
                      </div>
                    </div>

                    <div>
                      <div className="text-[10px] uppercase tracking-[0.04em] text-[var(--text-muted)]">
                        Measured
                      </div>

                      <div className="mt-1 text-[12px] font-medium text-[var(--text-primary)]">
                        {item.measuredGain}
                      </div>
                    </div>

                    <div>
                      <div className="text-[10px] uppercase tracking-[0.04em] text-[var(--text-muted)]">
                        Latency
                      </div>

                      <div className="mt-1 text-[11px] font-medium text-[var(--text-secondary)]">
                        {item.latency}
                      </div>
                    </div>
                  </div>
                ),
              )}
            </div>
          </section>

          <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)]">
            <div className="border-b border-[var(--border)] px-4 py-4">
              <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                Latest recommendation
              </h2>
            </div>

            <div className="p-4">
              <div className="mb-5 flex items-center justify-between">
                <StatusBadge status="Recommended" />

                <span className="text-[11px] text-[var(--text-muted)]">
                  High priority
                </span>
              </div>

              <div className="mb-5">
                <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.05em] text-[var(--text-muted)]">
                  Index
                </div>

                <div className="rounded-md border border-[var(--border)] bg-[var(--surface-subtle)] p-3 font-mono text-[11px] leading-5 text-[var(--text-primary)]">
                  idx_orders_customer_id_status_created_at
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-md border border-[var(--border)] p-3">
                  <div className="text-[10px] uppercase tracking-[0.04em] text-[var(--text-muted)]">
                    Expected gain
                  </div>

                  <div className="mt-1 text-[18px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
                    99.78%
                  </div>
                </div>

                <div className="rounded-md border border-[var(--border)] p-3">
                  <div className="text-[10px] uppercase tracking-[0.04em] text-[var(--text-muted)]">
                    Measured gain
                  </div>

                  <div className="mt-1 flex items-center gap-1 text-[18px] font-semibold tracking-[-0.03em] text-[var(--success)]">
                    99.88%

                    <ArrowDownRight
                      size={15}
                      strokeWidth={1.8}
                    />
                  </div>
                </div>
              </div>

              <div className="mt-4 border-t border-[var(--border)] pt-4">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[var(--text-muted)]">
                    Confidence
                  </span>

                  <span className="font-medium text-[var(--text-primary)]">
                    93.15%
                  </span>
                </div>

                <div className="mt-3 flex items-center justify-between text-[11px]">
                  <span className="text-[var(--text-muted)]">
                    Prediction error
                  </span>

                  <span className="font-medium text-[var(--text-primary)]">
                    0.10%
                  </span>
                </div>

                <div className="mt-3 flex items-center justify-between text-[11px]">
                  <span className="text-[var(--text-muted)]">
                    Model
                  </span>

                  <span className="font-mono text-[10px] text-[var(--text-secondary)]">
                    v2-final
                  </span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </AppShell>
  );
}