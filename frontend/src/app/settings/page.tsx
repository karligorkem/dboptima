"use client";

import {
  BrainCircuit,
  CheckCircle2,
  Database,
  Gauge,
  LoaderCircle,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";
import {
  useEffect,
  useState,
} from "react";

import { AppShell } from "../components/app-shell";
import { MetricCard } from "../components/metric-card";

type SettingsResponse = {
  application: {
    name: string;
    environment: string;
  };

  recommendation_policy: {
    recommended_threshold_percent: number;
    review_threshold_percent: number;
    rejected_below_percent: number;
  };

  benchmark_policy: {
    warmup_runs: number;
    measurement_runs: number;
    decision_metric: string;
    temporary_index: boolean;
    keep_index_after_benchmark: boolean;
  };

  safety: {
    explain_analyze_executes_query: boolean;
    automatic_index_application: boolean;
    benchmark_is_final_authority: boolean;
    ml_ranking_enabled: boolean;
  };

  model: {
    production_version: string;
    feature_schema: string;
    feature_count: number;
  };
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

function BooleanState({
  value,
  positiveWhenTrue = true,
}: {
  value: boolean;
  positiveWhenTrue?: boolean;
}) {
  const positive = positiveWhenTrue
    ? value
    : !value;

  return (
    <span
      className={
        positive
          ? "inline-flex rounded bg-[var(--success-soft)] px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.05em] text-[var(--success)]"
          : "inline-flex rounded bg-[var(--danger-soft)] px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.05em] text-[var(--danger)]"
      }
    >
      {value ? "Enabled" : "Disabled"}
    </span>
  );
}

export default function SettingsPage() {
  const [
    data,
    setData,
  ] = useState<SettingsResponse | null>(
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

    async function loadSettings() {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(
          `${API_BASE_URL}/api/settings`,
        );

        if (!response.ok) {
          throw new Error(
            `Settings request failed (${response.status})`,
          );
        }

        const result: SettingsResponse =
          await response.json();

        if (!cancelled) {
          setData(result);
        }
      } catch (err) {
        if (cancelled) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load settings.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadSettings();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AppShell>
      <div className="mx-auto max-w-[1360px]">

        <section className="mb-7">
          <h1 className="text-[24px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
            Settings
          </h1>

          <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
            Runtime policies, benchmark behavior, and optimization safety controls.
          </p>
        </section>


        {loading && (
          <div className="flex min-h-[500px] items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface)]">
            <div className="flex items-center gap-2 text-[12px] text-[var(--text-secondary)]">
              <LoaderCircle
                size={15}
                className="animate-spin"
              />

              Loading settings
            </div>
          </div>
        )}


        {!loading && error && (
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
                    label="Environment"
                    value={
                      data.application
                        .environment
                    }
                    description={
                      data.application
                        .name
                    }
                    icon={
                      <Database
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />

                  <MetricCard
                    label="Recommended threshold"
                    value={`${data.recommendation_policy.recommended_threshold_percent}%`}
                    description="Measured improvement"
                    icon={
                      <CheckCircle2
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />

                  <MetricCard
                    label="Review threshold"
                    value={`${data.recommendation_policy.review_threshold_percent}%`}
                    description="Minimum review range"
                    icon={
                      <Gauge
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />

                  <MetricCard
                    label="Production model"
                    value={
                      data.model
                        .production_version
                    }
                    description={`${data.model.feature_count} features`}
                    icon={
                      <BrainCircuit
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />

                </div>

              </section>


              <div className="grid grid-cols-2 gap-6">

                <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)]">

                  <div className="border-b border-[var(--border)] px-5 py-4">
                    <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                      Recommendation policy
                    </h2>

                    <p className="mt-1 text-[11px] text-[var(--text-muted)]">
                      Deterministic decision thresholds applied after benchmark validation.
                    </p>
                  </div>


                  <div className="p-5">

                    <div className="flex items-center justify-between border-b border-[var(--border)] py-3">

                      <div>
                        <div className="text-[12px] font-medium text-[var(--text-primary)]">
                          Recommended
                        </div>

                        <div className="mt-1 text-[10px] text-[var(--text-muted)]">
                          Candidate is accepted as a strong optimization.
                        </div>
                      </div>

                      <span className="font-mono text-[12px] font-semibold text-[var(--success)]">
                        ≥{" "}
                        {
                          data
                            .recommendation_policy
                            .recommended_threshold_percent
                        }
                        %
                      </span>

                    </div>


                    <div className="flex items-center justify-between border-b border-[var(--border)] py-3">

                      <div>
                        <div className="text-[12px] font-medium text-[var(--text-primary)]">
                          Review
                        </div>

                        <div className="mt-1 text-[10px] text-[var(--text-muted)]">
                          Candidate requires additional evaluation.
                        </div>
                      </div>

                      <span className="font-mono text-[12px] font-semibold text-[var(--warning)]">
                        ≥{" "}
                        {
                          data
                            .recommendation_policy
                            .review_threshold_percent
                        }
                        %
                      </span>

                    </div>


                    <div className="flex items-center justify-between py-3">

                      <div>
                        <div className="text-[12px] font-medium text-[var(--text-primary)]">
                          Rejected
                        </div>

                        <div className="mt-1 text-[10px] text-[var(--text-muted)]">
                          Improvement is below the review threshold.
                        </div>
                      </div>

                      <span className="font-mono text-[12px] font-semibold text-[var(--danger)]">
                        &lt;{" "}
                        {
                          data
                            .recommendation_policy
                            .rejected_below_percent
                        }
                        %
                      </span>

                    </div>

                  </div>

                </section>


                <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)]">

                  <div className="border-b border-[var(--border)] px-5 py-4">
                    <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                      Benchmark policy
                    </h2>

                    <p className="mt-1 text-[11px] text-[var(--text-muted)]">
                      Execution strategy used to validate candidate indexes.
                    </p>
                  </div>


                  <div className="p-5">

                    <div className="flex items-center justify-between border-b border-[var(--border)] py-3">
                      <span className="text-[11px] text-[var(--text-secondary)]">
                        Warmup runs
                      </span>

                      <span className="font-mono text-[11px] font-medium text-[var(--text-primary)]">
                        {
                          data
                            .benchmark_policy
                            .warmup_runs
                        }
                      </span>
                    </div>


                    <div className="flex items-center justify-between border-b border-[var(--border)] py-3">
                      <span className="text-[11px] text-[var(--text-secondary)]">
                        Measurement runs
                      </span>

                      <span className="font-mono text-[11px] font-medium text-[var(--text-primary)]">
                        {
                          data
                            .benchmark_policy
                            .measurement_runs
                        }
                      </span>
                    </div>


                    <div className="flex items-center justify-between border-b border-[var(--border)] py-3">
                      <span className="text-[11px] text-[var(--text-secondary)]">
                        Decision metric
                      </span>

                      <span className="font-mono text-[11px] font-medium uppercase text-[var(--text-primary)]">
                        {
                          data
                            .benchmark_policy
                            .decision_metric
                        }
                      </span>
                    </div>


                    <div className="flex items-center justify-between border-b border-[var(--border)] py-3">
                      <span className="text-[11px] text-[var(--text-secondary)]">
                        Temporary index
                      </span>

                      <BooleanState
                        value={
                          data
                            .benchmark_policy
                            .temporary_index
                        }
                      />
                    </div>


                    <div className="flex items-center justify-between py-3">
                      <span className="text-[11px] text-[var(--text-secondary)]">
                        Keep index after benchmark
                      </span>

                      <BooleanState
                        value={
                          data
                            .benchmark_policy
                            .keep_index_after_benchmark
                        }
                        positiveWhenTrue={
                          false
                        }
                      />
                    </div>

                  </div>

                </section>


                <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)]">

                  <div className="flex items-center gap-2 border-b border-[var(--border)] px-5 py-4">

                    <ShieldCheck
                      size={15}
                      strokeWidth={1.8}
                      className="text-[var(--text-muted)]"
                    />

                    <div>
                      <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                        Safety controls
                      </h2>

                      <p className="mt-1 text-[11px] text-[var(--text-muted)]">
                        Controls governing automated optimization behavior.
                      </p>
                    </div>

                  </div>


                  <div className="p-5">

                    <div className="flex items-center justify-between border-b border-[var(--border)] py-3">
                      <span className="text-[11px] text-[var(--text-secondary)]">
                        Automatic index application
                      </span>

                      <BooleanState
                        value={
                          data.safety
                            .automatic_index_application
                        }
                        positiveWhenTrue={
                          false
                        }
                      />
                    </div>


                    <div className="flex items-center justify-between border-b border-[var(--border)] py-3">
                      <span className="text-[11px] text-[var(--text-secondary)]">
                        Benchmark is final authority
                      </span>

                      <BooleanState
                        value={
                          data.safety
                            .benchmark_is_final_authority
                        }
                      />
                    </div>


                    <div className="flex items-center justify-between border-b border-[var(--border)] py-3">
                      <span className="text-[11px] text-[var(--text-secondary)]">
                        ML candidate ranking
                      </span>

                      <BooleanState
                        value={
                          data.safety
                            .ml_ranking_enabled
                        }
                      />
                    </div>


                    <div className="flex items-center justify-between py-3">

                      <div>
                        <div className="text-[11px] text-[var(--text-secondary)]">
                          EXPLAIN ANALYZE executes query
                        </div>

                        <div className="mt-1 text-[9px] text-[var(--text-muted)]">
                          Queries must be treated as executable workloads.
                        </div>
                      </div>

                      <BooleanState
                        value={
                          data.safety
                            .explain_analyze_executes_query
                        }
                        positiveWhenTrue={
                          false
                        }
                      />

                    </div>

                  </div>

                </section>


                <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)]">

                  <div className="flex items-center gap-2 border-b border-[var(--border)] px-5 py-4">

                    <LockKeyhole
                      size={15}
                      strokeWidth={1.8}
                      className="text-[var(--text-muted)]"
                    />

                    <div>
                      <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                        Production model
                      </h2>

                      <p className="mt-1 text-[11px] text-[var(--text-muted)]">
                        Model used before benchmark execution.
                      </p>
                    </div>

                  </div>


                  <div className="p-5">

                    <div className="flex items-center justify-between border-b border-[var(--border)] py-3">
                      <span className="text-[11px] text-[var(--text-secondary)]">
                        Version
                      </span>

                      <span className="font-mono text-[11px] font-medium text-[var(--text-primary)]">
                        {
                          data.model
                            .production_version
                        }
                      </span>
                    </div>


                    <div className="flex items-center justify-between border-b border-[var(--border)] py-3">
                      <span className="text-[11px] text-[var(--text-secondary)]">
                        Feature schema
                      </span>

                      <span className="font-mono text-[11px] font-medium text-[var(--text-primary)]">
                        {
                          data.model
                            .feature_schema
                        }
                      </span>
                    </div>


                    <div className="flex items-center justify-between py-3">
                      <span className="text-[11px] text-[var(--text-secondary)]">
                        Feature count
                      </span>

                      <span className="font-mono text-[11px] font-medium text-[var(--text-primary)]">
                        {
                          data.model
                            .feature_count
                        }
                      </span>
                    </div>

                  </div>

                </section>

              </div>
            </>
          )}

      </div>
    </AppShell>
  );
}