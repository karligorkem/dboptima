"use client";

import Link from "next/link";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Database,
  Gauge,
  LoaderCircle,
  ShieldCheck,
} from "lucide-react";
import {
  useEffect,
  useState,
} from "react";

import { AppShell } from "../components/app-shell";
import { MetricCard } from "../components/metric-card";

type RecentOptimization = {
  recommendation_id: number;
  query_id: number;
  query: string;
  type: string;
  sql_command: string;
  reason: string;
  status: string;
  confidence: number | null;
  before_ms: number | null;
  after_ms: number | null;
  improvement_ms: number | null;
  improvement_percent: number | null;
  created_at: string | null;
};

type OverviewResponse = {
  database: {
    id: number;
    name: string;
    host: string;
    port: number;
    database_name: string;
    username: string;
  };

  metrics: {
    analyzed_queries: number;
    total_calls: number;
    latency_sample_count: number;
    total_recommendations: number;
    recommended_count: number;
    review_count: number;
    rejected_count: number;
    average_measured_gain: number;
    median_measured_gain: number;
    average_confidence: number;
  };

  latest_recommendation:
    | RecentOptimization
    | null;

  recent_optimizations:
    RecentOptimization[];
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

const DATABASE_ID = 2;

function formatPercent(
  value: number | null | undefined,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  return `${value.toFixed(2)}%`;
}

function formatConfidence(
  value: number | null | undefined,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  return `${(value * 100).toFixed(2)}%`;
}

function formatMs(
  value: number | null | undefined,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  if (value < 1) {
    return `${value.toFixed(3)} ms`;
  }

  return `${value.toFixed(2)} ms`;
}

function formatNumber(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-US",
  ).format(value);
}

function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  return new Intl.DateTimeFormat(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(date);
}

function StatusBadge({
  status,
}: {
  status: string;
}) {
  const styles =
    status === "RECOMMENDED"
      ? "bg-[var(--success-soft)] text-[var(--success)]"
      : status === "REVIEW"
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
  const [
    overview,
    setOverview,
  ] = useState<OverviewResponse | null>(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  useEffect(() => {
    let cancelled = false;

    async function loadOverview() {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(
          `${API_BASE_URL}/api/overview/${DATABASE_ID}`,
        );

        if (!response.ok) {
          throw new Error(
            `Overview request failed (${response.status})`,
          );
        }

        const data: OverviewResponse =
          await response.json();

        if (!cancelled) {
          setOverview(data);
        }
      } catch (err) {
        if (cancelled) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load overview.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadOverview();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AppShell>
      <div className="mx-auto max-w-[1440px]">
        {loading && (
          <div className="flex min-h-[500px] items-center justify-center">
            <div className="flex items-center gap-2 text-[12px] text-[var(--text-secondary)]">
              <LoaderCircle
                size={15}
                className="animate-spin"
              />

              Loading overview
            </div>
          </div>
        )}

        {!loading && error && (
          <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-5">
            <div className="text-[13px] font-semibold text-[var(--danger)]">
              Overview unavailable
            </div>

            <div className="mt-2 text-[12px] text-[var(--text-secondary)]">
              {error}
            </div>
          </div>
        )}

        {!loading &&
          !error &&
          overview && (
            <>
              <section className="mb-8 flex items-start justify-between">
                <div>
                  <h1 className="text-[24px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
                    Overview
                  </h1>

                  <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
                    Database performance and optimization activity.
                  </p>
                </div>

                <Link
                  href="/analyzer"
                  className="flex h-9 items-center gap-2 rounded-md bg-[#17191c] px-3.5 text-[12px] font-medium text-white transition-opacity hover:opacity-90"
                >
                  Analyze query

                  <ArrowRight
                    size={14}
                    strokeWidth={1.8}
                  />
                </Link>
              </section>

              <section className="mb-8 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-5 py-5">
                <div className="grid grid-cols-4">
                  <MetricCard
                    label="Connected database"
                    value={
                      overview.database
                        .database_name
                    }
                    description={
                      overview.database.name
                    }
                    icon={
                      <Database
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />

                  <MetricCard
                    label="Analyzed queries"
                    value={formatNumber(
                      overview.metrics
                        .analyzed_queries,
                    )}
                    description={`${formatNumber(
                      overview.metrics
                        .latency_sample_count,
                    )} latency samples`}
                    icon={
                      <Activity
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />

                  <MetricCard
                    label="Recommended indexes"
                    value={formatNumber(
                      overview.metrics
                        .recommended_count,
                    )}
                    description={`${formatNumber(
                      overview.metrics
                        .total_recommendations,
                    )} total evaluations`}
                    icon={
                      <CheckCircle2
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />

                  <MetricCard
                    label="Median measured gain"
                    value={formatPercent(
                      overview.metrics
                        .median_measured_gain,
                    )}
                    description={`Average ${formatPercent(
                      overview.metrics
                        .average_measured_gain,
                    )}`}
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

                    <span className="text-[11px] font-medium text-[var(--text-secondary)]">
                      Latest 10
                    </span>
                  </div>

                  <div>
                    {overview
                      .recent_optimizations
                      .map(
                        (
                          item,
                          index,
                        ) => (
                          <div
                            key={
                              item.recommendation_id
                            }
                            className={`grid grid-cols-[minmax(0,1fr)_110px_120px_105px] items-center gap-4 px-4 py-4 ${
                              index !==
                              overview
                                .recent_optimizations
                                .length -
                                1
                                ? "border-b border-[var(--border)]"
                                : ""
                            }`}
                          >
                            <div className="min-w-0">
                              <div className="truncate font-mono text-[11px] text-[var(--text-primary)]">
                                {
                                  item.query
                                }
                              </div>

                              <div className="mt-2 flex items-center gap-2">
                                <StatusBadge
                                  status={
                                    item.status
                                  }
                                />

                                <span className="text-[10px] text-[var(--text-muted)]">
                                  {formatDate(
                                    item.created_at,
                                  )}
                                </span>
                              </div>
                            </div>

                            <div>
                              <div className="text-[10px] uppercase tracking-[0.04em] text-[var(--text-muted)]">
                                Measured
                              </div>

                              <div className="mt-1 text-[12px] font-medium text-[var(--text-primary)]">
                                {formatPercent(
                                  item.improvement_percent,
                                )}
                              </div>
                            </div>

                            <div>
                              <div className="text-[10px] uppercase tracking-[0.04em] text-[var(--text-muted)]">
                                Latency
                              </div>

                              <div className="mt-1 text-[11px] font-medium text-[var(--text-secondary)]">
                                {formatMs(
                                  item.before_ms,
                                )}

                                {" → "}

                                {formatMs(
                                  item.after_ms,
                                )}
                              </div>
                            </div>

                            <div>
                              <div className="text-[10px] uppercase tracking-[0.04em] text-[var(--text-muted)]">
                                Confidence
                              </div>

                              <div className="mt-1 text-[12px] font-medium text-[var(--text-primary)]">
                                {formatConfidence(
                                  item.confidence,
                                )}
                              </div>
                            </div>
                          </div>
                        ),
                      )}
                  </div>
                </section>

                <div className="space-y-6">
                  <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)]">
                    <div className="border-b border-[var(--border)] px-4 py-4">
                      <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                        Recommendation summary
                      </h2>
                    </div>

                    <div className="p-4">
                      <div className="space-y-4">
                        <div className="flex items-center justify-between text-[12px]">
                          <span className="text-[var(--text-secondary)]">
                            Recommended
                          </span>

                          <span className="font-semibold text-[var(--text-primary)]">
                            {
                              overview.metrics
                                .recommended_count
                            }
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-[12px]">
                          <span className="text-[var(--text-secondary)]">
                            Review
                          </span>

                          <span className="font-semibold text-[var(--text-primary)]">
                            {
                              overview.metrics
                                .review_count
                            }
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-[12px]">
                          <span className="text-[var(--text-secondary)]">
                            Rejected
                          </span>

                          <span className="font-semibold text-[var(--text-primary)]">
                            {
                              overview.metrics
                                .rejected_count
                            }
                          </span>
                        </div>
                      </div>

                      <div className="mt-5 border-t border-[var(--border)] pt-4">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-[var(--text-muted)]">
                            Average confidence
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {formatConfidence(
                              overview.metrics
                                .average_confidence,
                            )}
                          </span>
                        </div>

                        <div className="mt-3 flex items-center justify-between text-[11px]">
                          <span className="text-[var(--text-muted)]">
                            Total query calls
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {formatNumber(
                              overview.metrics
                                .total_calls,
                            )}
                          </span>
                        </div>
                      </div>
                    </div>
                  </section>

                  {overview
                    .latest_recommendation && (
                    <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)]">
                      <div className="border-b border-[var(--border)] px-4 py-4">
                        <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                          Latest recommendation
                        </h2>
                      </div>

                      <div className="p-4">
                        <div className="mb-5 flex items-center justify-between">
                          <StatusBadge
                            status={
                              overview
                                .latest_recommendation
                                .status
                            }
                          />

                          <span className="text-[11px] text-[var(--text-muted)]">
                            Recommendation #
                            {
                              overview
                                .latest_recommendation
                                .recommendation_id
                            }
                          </span>
                        </div>

                        <div className="mb-5">
                          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.05em] text-[var(--text-muted)]">
                            Index
                          </div>

                          <div className="rounded-md border border-[var(--border)] bg-[var(--surface-subtle)] p-3 font-mono text-[11px] leading-5 text-[var(--text-primary)] break-words">
                            {
                              overview
                                .latest_recommendation
                                .sql_command
                            }
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                          <div className="rounded-md border border-[var(--border)] p-3">
                            <div className="text-[10px] uppercase tracking-[0.04em] text-[var(--text-muted)]">
                              Measured gain
                            </div>

                            <div className="mt-1 text-[18px] font-semibold tracking-[-0.03em] text-[var(--success)]">
                              {formatPercent(
                                overview
                                  .latest_recommendation
                                  .improvement_percent,
                              )}
                            </div>
                          </div>

                          <div className="rounded-md border border-[var(--border)] p-3">
                            <div className="text-[10px] uppercase tracking-[0.04em] text-[var(--text-muted)]">
                              Confidence
                            </div>

                            <div className="mt-1 text-[18px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
                              {formatConfidence(
                                overview
                                  .latest_recommendation
                                  .confidence,
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="mt-4 border-t border-[var(--border)] pt-4">
                          <div className="flex items-center gap-2 text-[11px] text-[var(--text-secondary)]">
                            <ShieldCheck
                              size={14}
                              strokeWidth={1.8}
                            />

                            Validated by measured PostgreSQL benchmark
                          </div>
                        </div>
                      </div>
                    </section>
                  )}
                </div>
              </div>
            </>
          )}
      </div>
    </AppShell>
  );
}