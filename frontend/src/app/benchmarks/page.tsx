"use client";

import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Database,
  Gauge,
  LoaderCircle,
  Search,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";

import { AppShell } from "../components/app-shell";
import { MetricCard } from "../components/metric-card";

type BenchmarkStatus =
  | "RECOMMENDED"
  | "REVIEW"
  | "REJECTED";

type BenchmarkItem = {
  benchmark_id: number;
  query_id: number;
  query: string;
  recommendation_type: string;
  sql_command: string;
  status: BenchmarkStatus;
  confidence: number | null;
  before_ms: number | null;
  after_ms: number | null;
  improvement_ms: number | null;
  improvement_percent: number | null;
  reason: string;
  created_at: string | null;
};

type BenchmarkMetrics = {
  total_runs: number;
  measured_runs: number;
  improved_runs: number;
  success_rate: number;

  recommended_runs: number;
  review_runs: number;
  rejected_runs: number;

  average_before_ms: number;
  average_after_ms: number;

  average_gain_percent: number;
  median_gain_percent: number;
  best_gain_percent: number;

  average_confidence: number;
};

type BenchmarksResponse = {
  database_id: number;

  metrics: BenchmarkMetrics;

  pagination: {
    total: number;
    limit: number;
    offset: number;
  };

  items: BenchmarkItem[];
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

const DATABASE_ID = 2;
const PAGE_SIZE = 25;

function formatNumber(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-US",
  ).format(value);
}

function formatPercent(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  return `${value.toFixed(2)}%`;
}

function formatConfidence(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  return `${(value * 100).toFixed(2)}%`;
}

function formatMs(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  if (Math.abs(value) < 1) {
    return `${value.toFixed(3)} ms`;
  }

  return `${value.toFixed(2)} ms`;
}

function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(
    new Date(value),
  );
}

function statusClasses(
  status: BenchmarkStatus,
): string {
  if (status === "RECOMMENDED") {
    return (
      "bg-[var(--success-soft)] " +
      "text-[var(--success)]"
    );
  }

  if (status === "REVIEW") {
    return (
      "bg-[var(--warning-soft)] " +
      "text-[var(--warning)]"
    );
  }

  return (
    "bg-[var(--danger-soft)] " +
    "text-[var(--danger)]"
  );
}

function StatusBadge({
  status,
}: {
  status: BenchmarkStatus;
}) {
  return (
    <span
      className={
        "inline-flex rounded px-2 py-1 " +
        "text-[9px] font-semibold " +
        "tracking-[0.05em] " +
        statusClasses(status)
      }
    >
      {status}
    </span>
  );
}

function GainValue({
  value,
}: {
  value: number | null;
}) {
  if (value === null) {
    return (
      <span className="text-[var(--text-muted)]">
        —
      </span>
    );
  }

  const positive =
    value >= 0;

  return (
    <div
      className={
        "flex items-center gap-1 text-[12px] font-semibold " +
        (
          positive
            ? "text-[var(--success)]"
            : "text-[var(--danger)]"
        )
      }
    >
      {formatPercent(value)}

      {positive ? (
        <ArrowDownRight
          size={13}
          strokeWidth={1.8}
        />
      ) : (
        <ArrowUpRight
          size={13}
          strokeWidth={1.8}
        />
      )}
    </div>
  );
}

export default function BenchmarksPage() {
  const [
    data,
    setData,
  ] = useState<BenchmarksResponse | null>(
    null,
  );

  const [
    status,
    setStatus,
  ] = useState<
    BenchmarkStatus | "ALL"
  >("ALL");

  const [
    page,
    setPage,
  ] = useState(0);

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    selected,
    setSelected,
  ] = useState<BenchmarkItem | null>(
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

    async function loadBenchmarks() {
      try {
        setLoading(true);
        setError(null);

        const params =
          new URLSearchParams();

        params.set(
          "limit",
          String(PAGE_SIZE),
        );

        params.set(
          "offset",
          String(
            page * PAGE_SIZE,
          ),
        );

        if (
          status !== "ALL"
        ) {
          params.set(
            "status",
            status,
          );
        }

        const response =
          await fetch(
            `${API_BASE_URL}/api/benchmarks/${DATABASE_ID}?${params.toString()}`,
          );

        if (!response.ok) {
          throw new Error(
            `Benchmarks request failed (${response.status})`,
          );
        }

        const result:
          BenchmarksResponse =
          await response.json();

        if (!cancelled) {
          setData(result);

          setSelected(
            result.items[0] ??
              null,
          );
        }
      } catch (err) {
        if (cancelled) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load benchmarks.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadBenchmarks();

    return () => {
      cancelled = true;
    };
  }, [
    page,
    status,
  ]);

  const visibleItems =
    useMemo(() => {
      if (!data) {
        return [];
      }

      const term =
        search
          .trim()
          .toLowerCase();

      if (!term) {
        return data.items;
      }

      return data.items.filter(
        (item) =>
          item.query
            .toLowerCase()
            .includes(term) ||
          item.sql_command
            .toLowerCase()
            .includes(term),
      );
    }, [
      data,
      search,
    ]);

  const totalPages =
    data
      ? Math.max(
          1,
          Math.ceil(
            data.pagination
              .total /
              PAGE_SIZE,
          ),
        )
      : 1;

  return (
    <AppShell>
      <div className="mx-auto max-w-[1480px]">

        <section className="mb-7 flex items-start justify-between">

          <div>
            <h1 className="text-[24px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
              Benchmarks
            </h1>

            <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
              Measured before-and-after execution performance for validated optimizations.
            </p>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-[var(--text-secondary)]">
            <Database
              size={14}
              strokeWidth={1.8}
            />

            shopdb
          </div>

        </section>


        {loading && (
          <div className="flex min-h-[500px] items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface)]">

            <div className="flex items-center gap-2 text-[12px] text-[var(--text-secondary)]">
              <LoaderCircle
                size={15}
                className="animate-spin"
              />

              Loading benchmarks
            </div>

          </div>
        )}


        {!loading &&
          error && (
            <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-5 text-[12px] text-[var(--danger)]">
              {error}
            </div>
          )}


        {!loading &&
          !error &&
          data && (
            <>

              <section className="mb-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-5 py-5">

                <div className="grid grid-cols-4">

                  <MetricCard
                    label="Benchmark runs"
                    value={formatNumber(
                      data.metrics
                        .total_runs,
                    )}
                    description={`${formatNumber(
                      data.metrics
                        .measured_runs,
                    )} measured runs`}
                    icon={
                      <Activity
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />


                  <MetricCard
                    label="Success rate"
                    value={formatPercent(
                      data.metrics
                        .success_rate,
                    )}
                    description={`${formatNumber(
                      data.metrics
                        .improved_runs,
                    )} improved runs`}
                    icon={
                      <Gauge
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />


                  <MetricCard
                    label="Median gain"
                    value={formatPercent(
                      data.metrics
                        .median_gain_percent,
                    )}
                    description={`Average ${formatPercent(
                      data.metrics
                        .average_gain_percent,
                    )}`}
                    icon={
                      <ArrowDownRight
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />


                  <MetricCard
                    label="Average latency"
                    value={formatMs(
                      data.metrics
                        .average_after_ms,
                    )}
                    description={`${formatMs(
                      data.metrics
                        .average_before_ms,
                    )} before`}
                    icon={
                      <Database
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />

                </div>

              </section>


              <section className="mb-5 flex items-center justify-between gap-4">

                <div className="flex items-center gap-2">

                  {(
                    [
                      "ALL",
                      "RECOMMENDED",
                      "REVIEW",
                      "REJECTED",
                    ] as const
                  ).map(
                    (item) => (
                      <button
                        key={item}
                        onClick={() => {
                          setStatus(
                            item,
                          );
                          setPage(0);
                        }}
                        className={
                          status === item
                            ? "h-8 rounded-md bg-[#17191c] px-3 text-[11px] font-medium text-white"
                            : "h-8 rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 text-[11px] font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                        }
                      >
                        {item ===
                        "ALL"
                          ? "All"
                          : item}
                      </button>
                    ),
                  )}

                </div>


                <div className="relative w-[320px]">

                  <Search
                    size={14}
                    strokeWidth={1.8}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
                  />

                  <input
                    value={search}
                    onChange={(
                      event,
                    ) =>
                      setSearch(
                        event
                          .target
                          .value,
                      )
                    }
                    placeholder="Search query or index SQL"
                    className="h-9 w-full rounded-md border border-[var(--border)] bg-[var(--surface)] pl-9 pr-3 text-[11px] text-[var(--text-primary)] outline-none placeholder:text-[var(--text-muted)] focus:border-[#aeb2b8]"
                  />

                </div>

              </section>


              <div className="grid grid-cols-[minmax(0,1fr)_420px] gap-5">

                <section className="overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface)]">

                  <div className="grid grid-cols-[minmax(0,1fr)_105px_115px_115px_100px] gap-4 border-b border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-3 text-[9px] font-semibold uppercase tracking-[0.05em] text-[var(--text-muted)]">

                    <div>
                      Query
                    </div>

                    <div>
                      Status
                    </div>

                    <div>
                      Before
                    </div>

                    <div>
                      After
                    </div>

                    <div>
                      Gain
                    </div>

                  </div>


                  {visibleItems.length ===
                  0 ? (
                    <div className="p-8 text-center text-[12px] text-[var(--text-muted)]">
                      No benchmark runs found.
                    </div>
                  ) : (
                    visibleItems.map(
                      (item) => (
                        <button
                          key={
                            item.benchmark_id
                          }
                          onClick={() =>
                            setSelected(
                              item,
                            )
                          }
                          className={
                            "grid w-full grid-cols-[minmax(0,1fr)_105px_115px_115px_100px] items-center gap-4 border-b border-[var(--border)] px-4 py-4 text-left transition-colors last:border-b-0 " +
                            (
                              selected
                                ?.benchmark_id ===
                              item.benchmark_id
                                ? "bg-[var(--surface-subtle)]"
                                : "hover:bg-[var(--surface-subtle)]"
                            )
                          }
                        >

                          <div className="min-w-0">

                            <div className="truncate font-mono text-[11px] text-[var(--text-primary)]">
                              {
                                item.query
                              }
                            </div>

                            <div className="mt-1.5 text-[10px] text-[var(--text-muted)]">
                              Benchmark #
                              {
                                item.benchmark_id
                              }

                              {" · "}

                              {formatDate(
                                item.created_at,
                              )}
                            </div>

                          </div>


                          <div>
                            <StatusBadge
                              status={
                                item.status
                              }
                            />
                          </div>


                          <div className="text-[11px] font-medium text-[var(--text-primary)]">
                            {formatMs(
                              item.before_ms,
                            )}
                          </div>


                          <div className="text-[11px] font-medium text-[var(--text-primary)]">
                            {formatMs(
                              item.after_ms,
                            )}
                          </div>


                          <GainValue
                            value={
                              item.improvement_percent
                            }
                          />

                        </button>
                      ),
                    )
                  )}


                  <div className="flex items-center justify-between border-t border-[var(--border)] px-4 py-3">

                    <div className="text-[10px] text-[var(--text-muted)]">
                      {data.pagination.total.toLocaleString(
                        "en-US",
                      )}{" "}
                      benchmark runs
                    </div>


                    <div className="flex items-center gap-2">

                      <button
                        disabled={
                          page === 0
                        }
                        onClick={() =>
                          setPage(
                            (
                              current,
                            ) =>
                              Math.max(
                                0,
                                current -
                                  1,
                              ),
                          )
                        }
                        className="flex h-8 w-8 items-center justify-center rounded-md border border-[var(--border)] disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        <ChevronLeft
                          size={14}
                        />
                      </button>


                      <span className="min-w-[70px] text-center text-[10px] text-[var(--text-secondary)]">
                        {page + 1} /{" "}
                        {totalPages}
                      </span>


                      <button
                        disabled={
                          page + 1 >=
                          totalPages
                        }
                        onClick={() =>
                          setPage(
                            (
                              current,
                            ) =>
                              current +
                              1,
                          )
                        }
                        className="flex h-8 w-8 items-center justify-center rounded-md border border-[var(--border)] disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        <ChevronRight
                          size={14}
                        />
                      </button>

                    </div>

                  </div>

                </section>


                <aside className="self-start rounded-lg border border-[var(--border)] bg-[var(--surface)]">

                  <div className="border-b border-[var(--border)] px-4 py-4">

                    <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                      Benchmark detail
                    </h2>

                  </div>


                  {!selected ? (
                    <div className="p-6 text-[12px] text-[var(--text-muted)]">
                      Select a benchmark run.
                    </div>
                  ) : (
                    <div className="p-4">

                      <div className="flex items-center justify-between">

                        <StatusBadge
                          status={
                            selected.status
                          }
                        />

                        <span className="text-[10px] text-[var(--text-muted)]">
                          #
                          {
                            selected.benchmark_id
                          }
                        </span>

                      </div>


                      <div className="mt-5">

                        <div className="mb-2 text-[9px] font-semibold uppercase tracking-[0.05em] text-[var(--text-muted)]">
                          Query
                        </div>

                        <div className="break-words rounded-md border border-[var(--border)] bg-[var(--surface-subtle)] p-3 font-mono text-[10px] leading-5 text-[var(--text-primary)]">
                          {
                            selected.query
                          }
                        </div>

                      </div>


                      <div className="mt-4">

                        <div className="mb-2 text-[9px] font-semibold uppercase tracking-[0.05em] text-[var(--text-muted)]">
                          Index SQL
                        </div>

                        <div className="break-words rounded-md border border-[var(--border)] bg-[var(--surface-subtle)] p-3 font-mono text-[10px] leading-5 text-[var(--text-primary)]">
                          {
                            selected.sql_command
                          }
                        </div>

                      </div>


                      <div className="mt-4 grid grid-cols-2 gap-3">

                        <div className="rounded-md border border-[var(--border)] p-3">

                          <div className="text-[9px] uppercase tracking-[0.05em] text-[var(--text-muted)]">
                            Before
                          </div>

                          <div className="mt-1 text-[18px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
                            {formatMs(
                              selected.before_ms,
                            )}
                          </div>

                        </div>


                        <div className="rounded-md border border-[var(--border)] p-3">

                          <div className="text-[9px] uppercase tracking-[0.05em] text-[var(--text-muted)]">
                            After
                          </div>

                          <div className="mt-1 text-[18px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
                            {formatMs(
                              selected.after_ms,
                            )}
                          </div>

                        </div>

                      </div>


                      <div className="mt-3 grid grid-cols-2 gap-3">

                        <div className="rounded-md border border-[var(--border)] p-3">

                          <div className="text-[9px] uppercase tracking-[0.05em] text-[var(--text-muted)]">
                            Gain
                          </div>

                          <div className="mt-1">
                            <GainValue
                              value={
                                selected.improvement_percent
                              }
                            />
                          </div>

                        </div>


                        <div className="rounded-md border border-[var(--border)] p-3">

                          <div className="text-[9px] uppercase tracking-[0.05em] text-[var(--text-muted)]">
                            Confidence
                          </div>

                          <div className="mt-1 text-[18px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
                            {formatConfidence(
                              selected.confidence,
                            )}
                          </div>

                        </div>

                      </div>


                      <div className="mt-4 border-t border-[var(--border)] pt-4">

                        <div className="flex items-center justify-between text-[11px]">

                          <span className="text-[var(--text-muted)]">
                            Improvement
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {formatMs(
                              selected.improvement_ms,
                            )}
                          </span>

                        </div>


                        <div className="mt-3 flex items-center justify-between text-[11px]">

                          <span className="text-[var(--text-muted)]">
                            Recommendation type
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {
                              selected.recommendation_type
                            }
                          </span>

                        </div>


                        <div className="mt-3 flex items-center justify-between text-[11px]">

                          <span className="text-[var(--text-muted)]">
                            Created
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {formatDate(
                              selected.created_at,
                            )}
                          </span>

                        </div>

                      </div>


                      <div className="mt-4 border-t border-[var(--border)] pt-4">

                        <div className="mb-2 text-[9px] font-semibold uppercase tracking-[0.05em] text-[var(--text-muted)]">
                          Evaluation
                        </div>

                        <p className="text-[11px] leading-5 text-[var(--text-secondary)]">
                          {
                            selected.reason
                          }
                        </p>

                      </div>

                    </div>
                  )}

                </aside>

              </div>

            </>
          )}

      </div>
    </AppShell>
  );
}