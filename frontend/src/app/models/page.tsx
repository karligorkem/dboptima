"use client";

import {
  Activity,
  CheckCircle2,
  Database,
  Gauge,
  LoaderCircle,
  Layers3,
} from "lucide-react";
import {
  useEffect,
  useState,
} from "react";

import { AppShell } from "../components/app-shell";
import { MetricCard } from "../components/metric-card";

type ProductionModelResponse = {
  status: string;

  model: {
    version: string;
    feature_schema: string;
    feature_count: number;
    features: string[];

    training_samples:
      | number
      | null;

    query_groups:
      | number
      | null;

    artifact_exists: boolean;
    artifact_name: string;
    metadata_name: string;
  };

  metadata: Record<
    string,
    unknown
  >;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

function formatNumber(
  value:
    | number
    | null,
): string {
  if (value === null) {
    return "—";
  }

  return new Intl.NumberFormat(
    "en-US",
  ).format(value);
}

function formatMetadataValue(
  value: unknown,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  if (
    typeof value === "string"
  ) {
    return value;
  }

  if (
    typeof value === "number"
  ) {
    return String(value);
  }

  if (
    typeof value === "boolean"
  ) {
    return value
      ? "true"
      : "false";
  }

  if (
    Array.isArray(value)
  ) {
    return `${value.length} items`;
  }

  return "object";
}

export default function ModelsPage() {
  const [
    data,
    setData,
  ] =
    useState<ProductionModelResponse | null>(
      null,
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );

  useEffect(() => {
    let cancelled = false;

    async function loadModel() {
      try {
        setLoading(true);
        setError(null);

        const response =
          await fetch(
            `${API_BASE_URL}/api/models/production`,
          );

        if (!response.ok) {
          throw new Error(
            `Model request failed (${response.status})`,
          );
        }

        const result:
          ProductionModelResponse =
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
            : "Failed to load model information.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadModel();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AppShell>
      <div className="mx-auto max-w-[1440px]">

        <section className="mb-7 flex items-start justify-between">

          <div>
            <h1 className="text-[24px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
              Models
            </h1>

            <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
              Production model metadata and feature schema.
            </p>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-[var(--text-secondary)]">

            <Database
              size={14}
              strokeWidth={1.8}
            />

            Production

          </div>

        </section>


        {loading && (
          <div className="flex min-h-[500px] items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface)]">

            <div className="flex items-center gap-2 text-[12px] text-[var(--text-secondary)]">

              <LoaderCircle
                size={15}
                className="animate-spin"
              />

              Loading model metadata

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
                    label="Production model"
                    value={
                      data.model
                        .version
                    }
                    description={
                      data.model
                        .feature_schema
                    }
                    icon={
                      <Layers3
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />


                  <MetricCard
                    label="Features"
                    value={String(
                      data.model
                        .feature_count,
                    )}
                    description="Pre-benchmark features"
                    icon={
                      <Gauge
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />


                  <MetricCard
                    label="Training samples"
                    value={formatNumber(
                      data.model
                        .training_samples,
                    )}
                    description={
                      data.model
                        .query_groups !==
                      null
                        ? `${formatNumber(
                            data.model
                              .query_groups,
                          )} query groups`
                        : "Training dataset"
                    }
                    icon={
                      <Activity
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />


                  <MetricCard
                    label="Artifact"
                    value={
                      data.model
                        .artifact_exists
                        ? "Ready"
                        : "Missing"
                    }
                    description={
                      data.model
                        .artifact_name
                    }
                    icon={
                      <CheckCircle2
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />

                </div>

              </section>


              <div className="grid grid-cols-[minmax(0,1fr)_420px] gap-6">

                <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)]">

                  <div className="border-b border-[var(--border)] px-5 py-4">

                    <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                      Feature schema
                    </h2>

                    <p className="mt-1 text-[11px] text-[var(--text-muted)]">
                      Features used by the production ranking model.
                    </p>

                  </div>


                  <div className="grid grid-cols-2 gap-x-8 px-5 py-5">

                    {data.model
                      .features.length ===
                    0 ? (
                      <div className="col-span-2 text-[12px] text-[var(--text-muted)]">
                        No feature metadata available.
                      </div>
                    ) : (
                      data.model
                        .features
                        .map(
                          (
                            feature,
                            index,
                          ) => (
                            <div
                              key={
                                feature
                              }
                              className="flex items-center gap-3 border-b border-[var(--border)] py-3"
                            >

                              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded border border-[var(--border)] bg-[var(--surface-subtle)] font-mono text-[9px] text-[var(--text-muted)]">
                                {String(
                                  index +
                                    1,
                                ).padStart(
                                  2,
                                  "0",
                                )}
                              </div>


                              <div className="font-mono text-[11px] text-[var(--text-primary)]">
                                {
                                  feature
                                }
                              </div>

                            </div>
                          ),
                        )
                    )}

                  </div>

                </section>


                <aside className="self-start rounded-lg border border-[var(--border)] bg-[var(--surface)]">

                  <div className="border-b border-[var(--border)] px-4 py-4">

                    <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                      Production deployment
                    </h2>

                  </div>


                  <div className="p-4">

                    <div className="flex items-center justify-between">

                      <span className="text-[11px] text-[var(--text-muted)]">
                        Status
                      </span>

                      <span className="inline-flex rounded bg-[var(--success-soft)] px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.05em] text-[var(--success)]">
                        {
                          data.status
                        }
                      </span>

                    </div>


                    <div className="mt-4 flex items-center justify-between text-[11px]">

                      <span className="text-[var(--text-muted)]">
                        Model version
                      </span>

                      <span className="font-mono font-medium text-[var(--text-primary)]">
                        {
                          data.model
                            .version
                        }
                      </span>

                    </div>


                    <div className="mt-3 flex items-center justify-between text-[11px]">

                      <span className="text-[var(--text-muted)]">
                        Feature schema
                      </span>

                      <span className="font-mono font-medium text-[var(--text-primary)]">
                        {
                          data.model
                            .feature_schema
                        }
                      </span>

                    </div>


                    <div className="mt-3 flex items-center justify-between text-[11px]">

                      <span className="text-[var(--text-muted)]">
                        Feature count
                      </span>

                      <span className="font-medium text-[var(--text-primary)]">
                        {
                          data.model
                            .feature_count
                        }
                      </span>

                    </div>


                    <div className="mt-3 flex items-center justify-between text-[11px]">

                      <span className="text-[var(--text-muted)]">
                        Training samples
                      </span>

                      <span className="font-medium text-[var(--text-primary)]">
                        {formatNumber(
                          data.model
                            .training_samples,
                        )}
                      </span>

                    </div>


                    <div className="mt-3 flex items-center justify-between text-[11px]">

                      <span className="text-[var(--text-muted)]">
                        Query groups
                      </span>

                      <span className="font-medium text-[var(--text-primary)]">
                        {formatNumber(
                          data.model
                            .query_groups,
                        )}
                      </span>

                    </div>


                    <div className="mt-5 border-t border-[var(--border)] pt-4">

                      <div className="mb-2 text-[9px] font-semibold uppercase tracking-[0.05em] text-[var(--text-muted)]">
                        Model artifact
                      </div>

                      <div className="break-all rounded-md border border-[var(--border)] bg-[var(--surface-subtle)] p-3 font-mono text-[10px] leading-5 text-[var(--text-primary)]">
                        {
                          data.model
                            .artifact_name
                        }
                      </div>

                    </div>


                    <div className="mt-4">

                      <div className="mb-2 text-[9px] font-semibold uppercase tracking-[0.05em] text-[var(--text-muted)]">
                        Metadata file
                      </div>

                      <div className="break-all rounded-md border border-[var(--border)] bg-[var(--surface-subtle)] p-3 font-mono text-[10px] leading-5 text-[var(--text-primary)]">
                        {
                          data.model
                            .metadata_name
                        }
                      </div>

                    </div>

                  </div>

                </aside>

              </div>


              <section className="mt-6 rounded-lg border border-[var(--border)] bg-[var(--surface)]">

                <div className="border-b border-[var(--border)] px-5 py-4">

                  <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                    Metadata
                  </h2>

                  <p className="mt-1 text-[11px] text-[var(--text-muted)]">
                    Raw fields persisted with the production model.
                  </p>

                </div>


                <div className="grid grid-cols-2">

                  {Object.entries(
                    data.metadata,
                  ).map(
                    ([
                      key,
                      value,
                    ]) => (
                      <div
                        key={
                          key
                        }
                        className="flex items-center justify-between gap-6 border-b border-r border-[var(--border)] px-5 py-3 last:border-b-0"
                      >

                        <span className="font-mono text-[10px] text-[var(--text-muted)]">
                          {key}
                        </span>

                        <span className="max-w-[240px] truncate text-right font-mono text-[10px] font-medium text-[var(--text-primary)]">
                          {formatMetadataValue(
                            value,
                          )}
                        </span>

                      </div>
                    ),
                  )}

                </div>

              </section>
            </>
          )}

      </div>
    </AppShell>
  );
}