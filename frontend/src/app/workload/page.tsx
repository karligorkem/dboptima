"use client";

import {
  Activity,
  ChevronLeft,
  ChevronRight,
  Clock3,
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

type WorkloadSort =
  | "p95"
  | "avg"
  | "calls"
  | "max"
  | "recent";

type RecommendationStatus =
  | "RECOMMENDED"
  | "REVIEW"
  | "REJECTED"
  | null;

type WorkloadItem = {
  query_id: number;
  query_hash: string;
  query: string;

  total_calls: number;
  avg_latency_ms: number | null;
  min_latency_ms: number | null;
  max_latency_ms: number | null;
  p95_latency_ms: number | null;

  first_seen: string | null;
  last_seen: string | null;

  latency_sample_count: number;
  recommendation_count: number;
  recommended_count: number;

  best_measured_gain: number | null;
  latest_status: RecommendationStatus;
  latest_measured_gain: number | null;
  latest_confidence: number | null;
};

type WorkloadResponse = {
  database_id: number;

  metrics: {
    query_count: number;
    total_calls: number;
    average_query_latency_ms: number;
    average_p95_latency_ms: number;
    worst_latency_ms: number;
    last_activity_at: string | null;
  };

  pagination: {
    total: number;
    limit: number;
    offset: number;
  };

  sort: string;

  items: WorkloadItem[];
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
  status: RecommendationStatus,
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

  if (status === "REJECTED") {
    return (
      "bg-[var(--danger-soft)] " +
      "text-[var(--danger)]"
    );
  }

  return (
    "bg-[var(--surface-subtle)] " +
    "text-[var(--text-muted)]"
  );
}

function StatusBadge({
  status,
}: {
  status: RecommendationStatus;
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
      {status ?? "NO DECISION"}
    </span>
  );
}

export default function WorkloadPage() {
  const [
    data,
    setData,
  ] = useState<WorkloadResponse | null>(
    null,
  );

  const [
    sort,
    setSort,
  ] = useState<WorkloadSort>(
    "p95",
  );

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
  ] = useState<WorkloadItem | null>(
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

    async function loadWorkload() {
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

        params.set(
          "sort",
          sort,
        );

        const response =
          await fetch(
            `${API_BASE_URL}/api/workload/${DATABASE_ID}?${params.toString()}`,
          );

        if (!response.ok) {
          throw new Error(
            `Workload request failed (${response.status})`,
          );
        }

        const result:
          WorkloadResponse =
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
            : "Failed to load workload.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadWorkload();

    return () => {
      cancelled = true;
    };
  }, [
    page,
    sort,
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
          item.query_hash
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
              Workload
            </h1>

            <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
              Query activity, latency distribution, and optimization history.
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

              Loading workload
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
                    label="Tracked queries"
                    value={formatNumber(
                      data.metrics
                        .query_count,
                    )}
                    description={`${formatNumber(
                      data.metrics
                        .total_calls,
                    )} total calls`}
                    icon={
                      <Activity
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />


                  <MetricCard
                    label="Average latency"
                    value={formatMs(
                      data.metrics
                        .average_query_latency_ms,
                    )}
                    description="Mean query latency"
                    icon={
                      <Clock3
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />


                  <MetricCard
                    label="Average p95"
                    value={formatMs(
                      data.metrics
                        .average_p95_latency_ms,
                    )}
                    description="Tail latency across queries"
                    icon={
                      <Gauge
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />


                  <MetricCard
                    label="Worst latency"
                    value={formatMs(
                      data.metrics
                        .worst_latency_ms,
                    )}
                    description={
                      data.metrics
                        .last_activity_at
                        ? `Last activity ${formatDate(
                            data.metrics
                              .last_activity_at,
                          )}`
                        : "No activity"
                    }
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
                      [
                        "p95",
                        "Highest p95",
                      ],
                      [
                        "avg",
                        "Highest avg",
                      ],
                      [
                        "calls",
                        "Most calls",
                      ],
                      [
                        "max",
                        "Highest max",
                      ],
                      [
                        "recent",
                        "Most recent",
                      ],
                    ] as const
                  ).map(
                    ([
                      value,
                      label,
                    ]) => (
                      <button
                        key={value}
                        onClick={() => {
                          setSort(
                            value,
                          );
                          setPage(0);
                        }}
                        className={
                          sort === value
                            ? "h-8 rounded-md bg-[#17191c] px-3 text-[11px] font-medium text-white"
                            : "h-8 rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 text-[11px] font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                        }
                      >
                        {label}
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
                        event.target
                          .value,
                      )
                    }
                    placeholder="Search query or hash"
                    className="h-9 w-full rounded-md border border-[var(--border)] bg-[var(--surface)] pl-9 pr-3 text-[11px] text-[var(--text-primary)] outline-none placeholder:text-[var(--text-muted)] focus:border-[#aeb2b8]"
                  />

                </div>

              </section>


              <div className="grid grid-cols-[minmax(0,1fr)_420px] gap-5">

                <section className="overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface)]">

                  <div className="grid grid-cols-[minmax(0,1fr)_90px_105px_105px_105px] gap-4 border-b border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-3 text-[9px] font-semibold uppercase tracking-[0.05em] text-[var(--text-muted)]">

                    <div>
                      Query
                    </div>

                    <div>
                      Calls
                    </div>

                    <div>
                      Avg
                    </div>

                    <div>
                      p95
                    </div>

                    <div>
                      Max
                    </div>

                  </div>


                  {visibleItems.length ===
                  0 ? (
                    <div className="p-8 text-center text-[12px] text-[var(--text-muted)]">
                      No workload queries found.
                    </div>
                  ) : (
                    visibleItems.map(
                      (item) => (
                        <button
                          key={
                            item.query_id
                          }
                          onClick={() =>
                            setSelected(
                              item,
                            )
                          }
                          className={
                            "grid w-full grid-cols-[minmax(0,1fr)_90px_105px_105px_105px] items-center gap-4 border-b border-[var(--border)] px-4 py-4 text-left transition-colors last:border-b-0 " +
                            (
                              selected
                                ?.query_id ===
                              item.query_id
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

                            <div className="mt-1.5 flex items-center gap-2">

                              <StatusBadge
                                status={
                                  item.latest_status
                                }
                              />

                              <span className="text-[10px] text-[var(--text-muted)]">
                                {
                                  item.latency_sample_count
                                }{" "}
                                samples
                              </span>

                            </div>

                          </div>


                          <div className="text-[11px] font-medium text-[var(--text-primary)]">
                            {formatNumber(
                              item.total_calls,
                            )}
                          </div>


                          <div className="text-[11px] font-medium text-[var(--text-primary)]">
                            {formatMs(
                              item.avg_latency_ms,
                            )}
                          </div>


                          <div className="text-[11px] font-medium text-[var(--text-primary)]">
                            {formatMs(
                              item.p95_latency_ms,
                            )}
                          </div>


                          <div className="text-[11px] font-medium text-[var(--text-primary)]">
                            {formatMs(
                              item.max_latency_ms,
                            )}
                          </div>

                        </button>
                      ),
                    )
                  )}


                  <div className="flex items-center justify-between border-t border-[var(--border)] px-4 py-3">

                    <div className="text-[10px] text-[var(--text-muted)]">
                      {data.pagination.total.toLocaleString(
                        "en-US",
                      )}{" "}
                      tracked queries
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
                      Query detail
                    </h2>

                  </div>


                  {!selected ? (
                    <div className="p-6 text-[12px] text-[var(--text-muted)]">
                      Select a query.
                    </div>
                  ) : (
                    <div className="p-4">

                      <div className="flex items-center justify-between">

                        <StatusBadge
                          status={
                            selected.latest_status
                          }
                        />

                        <span className="text-[10px] text-[var(--text-muted)]">
                          Query #
                          {
                            selected.query_id
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
                          Query hash
                        </div>

                        <div className="break-all rounded-md border border-[var(--border)] bg-[var(--surface-subtle)] p-3 font-mono text-[10px] text-[var(--text-secondary)]">
                          {
                            selected.query_hash
                          }
                        </div>

                      </div>


                      <div className="mt-4 grid grid-cols-2 gap-3">

                        <div className="rounded-md border border-[var(--border)] p-3">

                          <div className="text-[9px] uppercase tracking-[0.05em] text-[var(--text-muted)]">
                            Average
                          </div>

                          <div className="mt-1 text-[17px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
                            {formatMs(
                              selected.avg_latency_ms,
                            )}
                          </div>

                        </div>


                        <div className="rounded-md border border-[var(--border)] p-3">

                          <div className="text-[9px] uppercase tracking-[0.05em] text-[var(--text-muted)]">
                            p95
                          </div>

                          <div className="mt-1 text-[17px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
                            {formatMs(
                              selected.p95_latency_ms,
                            )}
                          </div>

                        </div>

                      </div>


                      <div className="mt-3 grid grid-cols-2 gap-3">

                        <div className="rounded-md border border-[var(--border)] p-3">

                          <div className="text-[9px] uppercase tracking-[0.05em] text-[var(--text-muted)]">
                            Minimum
                          </div>

                          <div className="mt-1 text-[15px] font-semibold text-[var(--text-primary)]">
                            {formatMs(
                              selected.min_latency_ms,
                            )}
                          </div>

                        </div>


                        <div className="rounded-md border border-[var(--border)] p-3">

                          <div className="text-[9px] uppercase tracking-[0.05em] text-[var(--text-muted)]">
                            Maximum
                          </div>

                          <div className="mt-1 text-[15px] font-semibold text-[var(--text-primary)]">
                            {formatMs(
                              selected.max_latency_ms,
                            )}
                          </div>

                        </div>

                      </div>


                      <div className="mt-4 border-t border-[var(--border)] pt-4">

                        <div className="flex items-center justify-between text-[11px]">

                          <span className="text-[var(--text-muted)]">
                            Total calls
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {formatNumber(
                              selected.total_calls,
                            )}
                          </span>

                        </div>


                        <div className="mt-3 flex items-center justify-between text-[11px]">

                          <span className="text-[var(--text-muted)]">
                            Latency samples
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {
                              selected.latency_sample_count
                            }
                          </span>

                        </div>


                        <div className="mt-3 flex items-center justify-between text-[11px]">

                          <span className="text-[var(--text-muted)]">
                            Recommendations
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {
                              selected.recommendation_count
                            }
                          </span>

                        </div>


                        <div className="mt-3 flex items-center justify-between text-[11px]">

                          <span className="text-[var(--text-muted)]">
                            Recommended runs
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {
                              selected.recommended_count
                            }
                          </span>

                        </div>

                      </div>


                      <div className="mt-4 border-t border-[var(--border)] pt-4">

                        <div className="flex items-center justify-between text-[11px]">

                          <span className="text-[var(--text-muted)]">
                            Latest measured gain
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {formatPercent(
                              selected.latest_measured_gain,
                            )}
                          </span>

                        </div>


                        <div className="mt-3 flex items-center justify-between text-[11px]">

                          <span className="text-[var(--text-muted)]">
                            Best measured gain
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {formatPercent(
                              selected.best_measured_gain,
                            )}
                          </span>

                        </div>


                        <div className="mt-3 flex items-center justify-between text-[11px]">

                          <span className="text-[var(--text-muted)]">
                            Latest confidence
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {formatConfidence(
                              selected.latest_confidence,
                            )}
                          </span>

                        </div>

                      </div>


                      <div className="mt-4 border-t border-[var(--border)] pt-4">

                        <div className="flex items-center justify-between text-[11px]">

                          <span className="text-[var(--text-muted)]">
                            First seen
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {formatDate(
                              selected.first_seen,
                            )}
                          </span>

                        </div>


                        <div className="mt-3 flex items-center justify-between text-[11px]">

                          <span className="text-[var(--text-muted)]">
                            Last seen
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {formatDate(
                              selected.last_seen,
                            )}
                          </span>

                        </div>

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