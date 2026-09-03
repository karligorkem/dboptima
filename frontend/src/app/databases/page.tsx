"use client";

import {
  CheckCircle2,
  Database,
  LoaderCircle,
  RefreshCw,
  Server,
  XCircle,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { AppShell } from "../components/app-shell";
import { MetricCard } from "../components/metric-card";

type DatabaseConnection = {
  id: number;
  name: string;
  host: string;
  port: number;
  database_name: string;
  username: string;
  created_at?: string | null;
};

type ConnectionState =
  | "idle"
  | "testing"
  | "connected"
  | "failed";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

function formatDate(
  value?: string | null,
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
  ).format(new Date(value));
}

function normalizeDatabases(
  payload: unknown,
): DatabaseConnection[] {
  if (Array.isArray(payload)) {
    return payload as DatabaseConnection[];
  }

  if (
    payload &&
    typeof payload === "object"
  ) {
    const value =
      payload as Record<
        string,
        unknown
      >;

    if (
      Array.isArray(value.items)
    ) {
      return value.items as DatabaseConnection[];
    }

    if (
      Array.isArray(
        value.databases,
      )
    ) {
      return value.databases as DatabaseConnection[];
    }
  }

  return [];
}

export default function DatabasesPage() {
  const [
    databases,
    setDatabases,
  ] = useState<
    DatabaseConnection[]
  >([]);

  const [
    selected,
    setSelected,
  ] =
    useState<DatabaseConnection | null>(
      null,
    );

  const [
    states,
    setStates,
  ] = useState<
    Record<
      number,
      ConnectionState
    >
  >({});

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );

  const loadDatabases =
    useCallback(async () => {
      try {
        setLoading(true);
        setError(null);

        const response =
          await fetch(
            `${API_BASE_URL}/api/databases`,
          );

        if (!response.ok) {
          throw new Error(
            `Database request failed (${response.status})`,
          );
        }

        const payload =
          await response.json();

        const items =
          normalizeDatabases(
            payload,
          );

        setDatabases(items);

        setSelected(
          (current) =>
            current
              ? items.find(
                  (item) =>
                    item.id ===
                    current.id,
                ) ??
                items[0] ??
                null
              : items[0] ??
                null,
        );
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load database connections.",
        );
      } finally {
        setLoading(false);
      }
    }, []);

  useEffect(() => {
    loadDatabases();
  }, [loadDatabases]);

  async function testConnection(
    databaseId: number,
  ) {
    try {
      setStates(
        (current) => ({
          ...current,
          [databaseId]:
            "testing",
        }),
      );

      const response =
        await fetch(
          `${API_BASE_URL}/api/databases/${databaseId}/test`,
          {
            method: "POST",
          },
        );

      if (!response.ok) {
        throw new Error(
          "Connection test failed.",
        );
      }

      setStates(
        (current) => ({
          ...current,
          [databaseId]:
            "connected",
        }),
      );
    } catch {
      setStates(
        (current) => ({
          ...current,
          [databaseId]:
            "failed",
        }),
      );
    }
  }

  const connectedCount =
    Object.values(
      states,
    ).filter(
      (state) =>
        state === "connected",
    ).length;

  return (
    <AppShell>
      <div className="mx-auto max-w-[1440px]">

        <section className="mb-7 flex items-start justify-between">
          <div>
            <h1 className="text-[24px] font-semibold tracking-[-0.03em] text-[var(--text-primary)]">
              Databases
            </h1>

            <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
              PostgreSQL connections available to the optimization workspace.
            </p>
          </div>

          <button
            onClick={
              loadDatabases
            }
            disabled={loading}
            className="flex h-9 items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 text-[11px] font-medium text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)] disabled:opacity-50"
          >
            <RefreshCw
              size={13}
              strokeWidth={1.8}
            />

            Refresh
          </button>
        </section>


        {loading && (
          <div className="flex min-h-[450px] items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface)]">
            <div className="flex items-center gap-2 text-[12px] text-[var(--text-secondary)]">
              <LoaderCircle
                size={15}
                className="animate-spin"
              />

              Loading database connections
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
          !error && (
            <>
              <section className="mb-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-5 py-5">
                <div className="grid grid-cols-3">
                  <MetricCard
                    label="Configured databases"
                    value={String(
                      databases.length,
                    )}
                    description="Stored target connections"
                    icon={
                      <Database
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />

                  <MetricCard
                    label="Verified connections"
                    value={String(
                      connectedCount,
                    )}
                    description="Tested in this session"
                    icon={
                      <CheckCircle2
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />

                  <MetricCard
                    label="Database engine"
                    value="PostgreSQL"
                    description="Current optimizer target"
                    icon={
                      <Server
                        size={16}
                        strokeWidth={1.8}
                      />
                    }
                  />
                </div>
              </section>


              <div className="grid grid-cols-[minmax(0,1fr)_420px] gap-6">

                <section className="overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface)]">
                  <div className="grid grid-cols-[minmax(0,1fr)_190px_130px_130px] gap-4 border-b border-[var(--border)] bg-[var(--surface-subtle)] px-5 py-3 text-[9px] font-semibold uppercase tracking-[0.05em] text-[var(--text-muted)]">
                    <div>
                      Database
                    </div>

                    <div>
                      Host
                    </div>

                    <div>
                      User
                    </div>

                    <div>
                      Connection
                    </div>
                  </div>


                  {databases.length ===
                  0 ? (
                    <div className="p-8 text-center text-[12px] text-[var(--text-muted)]">
                      No database connections configured.
                    </div>
                  ) : (
                    databases.map(
                      (database) => {
                        const state =
                          states[
                            database.id
                          ] ??
                          "idle";

                        return (
                          <button
                            key={
                              database.id
                            }
                            onClick={() =>
                              setSelected(
                                database,
                              )
                            }
                            className={
                              "grid w-full grid-cols-[minmax(0,1fr)_190px_130px_130px] items-center gap-4 border-b border-[var(--border)] px-5 py-4 text-left transition-colors last:border-b-0 " +
                              (
                                selected
                                  ?.id ===
                                database.id
                                  ? "bg-[var(--surface-subtle)]"
                                  : "hover:bg-[var(--surface-subtle)]"
                              )
                            }
                          >
                            <div className="min-w-0">
                              <div className="text-[12px] font-semibold text-[var(--text-primary)]">
                                {
                                  database.name
                                }
                              </div>

                              <div className="mt-1 font-mono text-[10px] text-[var(--text-muted)]">
                                {
                                  database.database_name
                                }
                              </div>
                            </div>


                            <div className="font-mono text-[10px] text-[var(--text-secondary)]">
                              {
                                database.host
                              }
                              :
                              {
                                database.port
                              }
                            </div>


                            <div className="truncate font-mono text-[10px] text-[var(--text-secondary)]">
                              {
                                database.username
                              }
                            </div>


                            <div>
                              {state ===
                                "testing" && (
                                <span className="flex items-center gap-1.5 text-[10px] text-[var(--text-muted)]">
                                  <LoaderCircle
                                    size={12}
                                    className="animate-spin"
                                  />
                                  Testing
                                </span>
                              )}

                              {state ===
                                "connected" && (
                                <span className="flex items-center gap-1.5 text-[10px] font-medium text-[var(--success)]">
                                  <CheckCircle2
                                    size={12}
                                  />
                                  Connected
                                </span>
                              )}

                              {state ===
                                "failed" && (
                                <span className="flex items-center gap-1.5 text-[10px] font-medium text-[var(--danger)]">
                                  <XCircle
                                    size={12}
                                  />
                                  Failed
                                </span>
                              )}

                              {state ===
                                "idle" && (
                                <span className="text-[10px] text-[var(--text-muted)]">
                                  Not tested
                                </span>
                              )}
                            </div>
                          </button>
                        );
                      },
                    )
                  )}
                </section>


                <aside className="self-start rounded-lg border border-[var(--border)] bg-[var(--surface)]">
                  <div className="border-b border-[var(--border)] px-4 py-4">
                    <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">
                      Connection detail
                    </h2>
                  </div>


                  {!selected ? (
                    <div className="p-6 text-[12px] text-[var(--text-muted)]">
                      Select a database connection.
                    </div>
                  ) : (
                    <div className="p-4">

                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-[15px] font-semibold text-[var(--text-primary)]">
                            {
                              selected.name
                            }
                          </div>

                          <div className="mt-1 font-mono text-[10px] text-[var(--text-muted)]">
                            Connection #
                            {
                              selected.id
                            }
                          </div>
                        </div>

                        <Database
                          size={17}
                          strokeWidth={1.6}
                          className="text-[var(--text-muted)]"
                        />
                      </div>


                      <div className="mt-5 space-y-3 border-t border-[var(--border)] pt-4">

                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-[var(--text-muted)]">
                            Database
                          </span>

                          <span className="font-mono font-medium text-[var(--text-primary)]">
                            {
                              selected.database_name
                            }
                          </span>
                        </div>


                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-[var(--text-muted)]">
                            Host
                          </span>

                          <span className="font-mono font-medium text-[var(--text-primary)]">
                            {
                              selected.host
                            }
                          </span>
                        </div>


                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-[var(--text-muted)]">
                            Port
                          </span>

                          <span className="font-mono font-medium text-[var(--text-primary)]">
                            {
                              selected.port
                            }
                          </span>
                        </div>


                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-[var(--text-muted)]">
                            Username
                          </span>

                          <span className="font-mono font-medium text-[var(--text-primary)]">
                            {
                              selected.username
                            }
                          </span>
                        </div>


                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-[var(--text-muted)]">
                            Created
                          </span>

                          <span className="font-medium text-[var(--text-primary)]">
                            {formatDate(
                              selected.created_at,
                            )}
                          </span>
                        </div>


                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-[var(--text-muted)]">
                            Password
                          </span>

                          <span className="font-mono text-[var(--text-primary)]">
                            ••••••••••••
                          </span>
                        </div>

                      </div>


                      <div className="mt-5 border-t border-[var(--border)] pt-4">

                        <button
                          onClick={() =>
                            testConnection(
                              selected.id,
                            )
                          }
                          disabled={
                            states[
                              selected.id
                            ] ===
                            "testing"
                          }
                          className="flex h-9 w-full items-center justify-center gap-2 rounded-md bg-[#17191c] text-[11px] font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {states[
                            selected.id
                          ] ===
                          "testing" ? (
                            <>
                              <LoaderCircle
                                size={13}
                                className="animate-spin"
                              />

                              Testing connection
                            </>
                          ) : (
                            <>
                              <RefreshCw
                                size={13}
                              />

                              Test connection
                            </>
                          )}
                        </button>

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