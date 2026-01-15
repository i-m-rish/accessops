"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

type Status = "PENDING" | "APPROVED" | "REJECTED";
type StatusFilter = Status | "ALL";

type RequestOut = {
  id: string;
  requester_id: string;
  resource: string;
  action: string;
  justification: string | null;
  status: Status;
  decided_by: string | null;
  decided_at: string | null;
  created_at: string;
};

type FastApiError = { detail?: unknown };

function parseFastApiError(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "Request failed";
  const p = payload as FastApiError;
  const d = p.detail;

  if (!d) return "Request failed";
  if (typeof d === "string") return d;

  if (Array.isArray(d)) {
    return d
      .map((x) => {
        if (x && typeof x === "object" && "msg" in (x as Record<string, unknown>)) {
          return String((x as Record<string, unknown>).msg);
        }
        return JSON.stringify(x);
      })
      .join("; ");
  }

  return JSON.stringify(d);
}

async function safeJson(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return { detail: text } as FastApiError;
  }
}

async function httpJson<T>(
  path: string,
  opts: RequestInit & { token?: string } = {}
): Promise<T> {
  const headers = new Headers(opts.headers || {});
  headers.set("Content-Type", "application/json");
  if (opts.token) headers.set("Authorization", `Bearer ${opts.token}`);

  const res = await fetch(`${API}${path}`, { ...opts, headers });
  const data = await safeJson(res);

  if (!res.ok) throw new Error(parseFastApiError(data));
  return data as T;
}

function fmtTs(s: string | null) {
  if (!s) return "-";
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

function shortId(id: string) {
  return id ? `${id.slice(0, 8)}…` : "-";
}

function statusBadge(status: Status) {
  switch (status) {
    case "APPROVED":
      return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/40 dark:bg-emerald-950/50 dark:text-emerald-200";
    case "REJECTED":
      return "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/40 dark:bg-rose-950/50 dark:text-rose-200";
    default:
      return "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/40 dark:text-amber-200";
  }
}

export default function RequestPage() {
  const [token, setToken] = useState<string>("");

  // Form state
  const [resource, setResource] = useState("Jira");
  const [action, setAction] = useState("jira-admin");
  const [justification, setJustification] = useState("Need access for project");

  // Data state
  const [myRequests, setMyRequests] = useState<RequestOut[]>([]);
  const [pendingRequests, setPendingRequests] = useState<RequestOut[]>([]);

  // UI state
  const [loadingMine, setLoadingMine] = useState(false);
  const [loadingPending, setLoadingPending] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [decisionBusyId, setDecisionBusyId] = useState<string>("");

  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");
  const [selected, setSelected] = useState<RequestOut | null>(null);

  const [msg, setMsg] = useState<string>("");
  const [err, setErr] = useState<string>("");

  useEffect(() => {
    const t =
      localStorage.getItem("accessops_token") ||
      localStorage.getItem("token") ||
      "";
    setToken(t);
  }, []);

  const isAuthed = useMemo(() => token.trim().length > 0, [token]);

  const filteredMine = useMemo(() => {
    if (statusFilter === "ALL") return myRequests;
    return myRequests.filter((r) => r.status === statusFilter);
  }, [myRequests, statusFilter]);

  const canSubmit = useMemo(() => {
    return (
      isAuthed &&
      resource.trim().length > 0 &&
      action.trim().length > 0 &&
      !submitting
    );
  }, [isAuthed, resource, action, submitting]);

  const loadMine = useCallback(async () => {
    if (!isAuthed) return;

    setErr("");
    setMsg("");
    setLoadingMine(true);

    try {
      const rows = await httpJson<RequestOut[]>("/requests", {
        method: "GET",
        token,
      });
      setMyRequests(rows);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoadingMine(false);
    }
  }, [isAuthed, token]);

  const loadPending = useCallback(async () => {
    if (!isAuthed) return;

    setErr("");
    setMsg("");
    setLoadingPending(true);

    try {
      const rows = await httpJson<RequestOut[]>("/requests/pending", {
        method: "GET",
        token,
      });
      setPendingRequests(rows);
    } catch (e: unknown) {
      // REQUESTER will likely get 403 here; that's correct.
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoadingPending(false);
    }
  }, [isAuthed, token]);

  const submitRequest = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!isAuthed) {
        setErr("No token present. Login first.");
        return;
      }

      setErr("");
      setMsg("");

      if (!resource.trim() || !action.trim()) {
        setErr("Resource and action are required.");
        return;
      }

      setSubmitting(true);
      try {
        await httpJson<RequestOut>("/requests", {
          method: "POST",
          token,
          body: JSON.stringify({
            resource: resource.trim(),
            action: action.trim(),
            justification: justification.trim() ? justification.trim() : null,
          }),
        });

        setMsg("Request created.");
        await loadMine();
      } catch (e2: unknown) {
        setErr(e2 instanceof Error ? e2.message : String(e2));
      } finally {
        setSubmitting(false);
      }
    },
    [isAuthed, token, resource, action, justification, loadMine]
  );

  const decide = useCallback(
    async (id: string, approve: boolean) => {
      if (!isAuthed) {
        setErr("No token present. Login first.");
        return;
      }

      setErr("");
      setMsg("");
      setDecisionBusyId(id);

      try {
        await httpJson<RequestOut>(
          `/requests/${id}/${approve ? "approve" : "reject"}`,
          { method: "PATCH", token }
        );

        setMsg(`${approve ? "Approved" : "Rejected"} request ${shortId(id)}.`);
        await loadPending();
        await loadMine();
      } catch (e: unknown) {
        setErr(e instanceof Error ? e.message : String(e));
      } finally {
        setDecisionBusyId("");
      }
    },
    [isAuthed, token, loadPending, loadMine]
  );

  useEffect(() => {
    if (!isAuthed) return;
    void loadMine();
  }, [isAuthed, loadMine]);

  return (
    <main className="min-h-screen bg-zinc-50 dark:bg-black px-6 py-10">
      <div className="mx-auto w-full max-w-6xl space-y-6">
        {/* Header */}
        <header className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
                Access Requests
              </h2>
              <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                Governed access workflow: create requests, track status, approve/reject (RBAC).
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Link
                href="/"
                className="rounded-lg border border-zinc-300 dark:border-zinc-700 px-3 py-2 text-sm text-zinc-700 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-900 transition"
              >
                Home
              </Link>
              <Link
                href="/login"
                className="rounded-lg bg-black dark:bg-white px-3 py-2 text-sm font-medium text-white dark:text-black hover:opacity-90 transition"
              >
                Login
              </Link>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
            <span className="rounded-md border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/40 px-2 py-1 font-mono">
              /requests
            </span>
            <span className="rounded-md border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/40 px-2 py-1 font-mono">
              /requests/pending
            </span>
            <span className="rounded-md border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/40 px-2 py-1 font-mono">
              /requests/&lt;id&gt;/approve
            </span>
            <span className="rounded-md border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/40 px-2 py-1 font-mono">
              /requests/&lt;id&gt;/reject
            </span>
          </div>
        </header>

        {/* Auth hint */}
        {!isAuthed ? (
          <div className="rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50 dark:bg-rose-950/40 p-4 text-sm text-rose-800 dark:text-rose-200">
            No token found. Login first. This page reads{" "}
            <span className="font-mono">localStorage[accessops_token]</span> (fallback:{" "}
            <span className="font-mono">localStorage[token]</span>).
          </div>
        ) : (
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-4 text-sm text-zinc-600 dark:text-zinc-300">
            Authenticated: bearer token loaded from localStorage.
          </div>
        )}

        {/* Alerts */}
        {err ? (
          <div className="rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50 dark:bg-rose-950/40 p-4 text-sm text-rose-800 dark:text-rose-200">
            <span className="font-semibold">Error:</span> {err}
          </div>
        ) : null}

        {msg ? (
          <div className="rounded-xl border border-emerald-200 dark:border-emerald-900/40 bg-emerald-50 dark:bg-emerald-950/40 p-4 text-sm text-emerald-800 dark:text-emerald-200">
            <span className="font-semibold">Status:</span> {msg}
          </div>
        ) : null}

        {/* Grid */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Create request */}
          <section className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Create Request
                </h3>
                <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                  For REQUESTER role. Requires bearer token.
                </p>
              </div>
              <button
                type="button"
                disabled={!isAuthed || loadingMine}
                onClick={() => void loadMine()}
                className="rounded-lg border border-zinc-300 dark:border-zinc-700 px-3 py-2 text-sm text-zinc-700 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-900 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {loadingMine ? "Refreshing..." : "Refresh"}
              </button>
            </div>

            <form onSubmit={submitRequest} className="mt-5 space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                  Resource
                </label>
                <input
                  className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-300 dark:focus:ring-zinc-700"
                  value={resource}
                  onChange={(e) => setResource(e.target.value)}
                  placeholder="Jira"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                  Action
                </label>
                <input
                  className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-300 dark:focus:ring-zinc-700"
                  value={action}
                  onChange={(e) => setAction(e.target.value)}
                  placeholder="jira-admin"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                  Justification <span className="text-zinc-400">(optional)</span>
                </label>
                <textarea
                  className="min-h-[88px] w-full resize-y rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-300 dark:focus:ring-zinc-700"
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  placeholder="Why do you need this access?"
                />
              </div>

              <button
                disabled={!canSubmit}
                type="submit"
                className="w-full rounded-lg bg-black dark:bg-white px-4 py-2.5 text-sm font-medium text-white dark:text-black hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {submitting ? "Submitting..." : "Submit Request"}
              </button>

              <div className="text-xs text-zinc-500 dark:text-zinc-400">
                Note: keep <span className="font-mono">resource</span> and{" "}
                <span className="font-mono">action</span> stable—these form the entitlement identity
                in real IGA models.
              </div>
            </form>
          </section>

          {/* Pending Queue */}
          <section className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Pending Queue
                </h3>
                <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                  For APPROVER role. REQUESTER typically receives 403 (correct RBAC).
                </p>
              </div>

              <button
                type="button"
                disabled={!isAuthed || loadingPending}
                onClick={() => void loadPending()}
                className="rounded-lg border border-zinc-300 dark:border-zinc-700 px-3 py-2 text-sm text-zinc-700 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-900 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {loadingPending ? "Refreshing..." : "Refresh"}
              </button>
            </div>

            <div className="mt-5 overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
              <table className="min-w-full text-sm">
                <thead className="bg-zinc-50 dark:bg-zinc-900/40 text-zinc-600 dark:text-zinc-300">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium">ID</th>
                    <th className="px-3 py-2 text-left font-medium">Resource</th>
                    <th className="px-3 py-2 text-left font-medium">Action</th>
                    <th className="px-3 py-2 text-left font-medium">Requester</th>
                    <th className="px-3 py-2 text-left font-medium">Decide</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                  {pendingRequests.length === 0 ? (
                    <tr>
                      <td className="px-3 py-3 text-zinc-500 dark:text-zinc-400" colSpan={5}>
                        No pending requests loaded.
                      </td>
                    </tr>
                  ) : (
                    pendingRequests.map((r) => (
                      <tr key={r.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-900/30">
                        <td className="px-3 py-2 font-mono text-zinc-800 dark:text-zinc-200">
                          {shortId(r.id)}
                        </td>
                        <td className="px-3 py-2 text-zinc-800 dark:text-zinc-200">
                          {r.resource}
                        </td>
                        <td className="px-3 py-2 text-zinc-800 dark:text-zinc-200">
                          {r.action}
                        </td>
                        <td className="px-3 py-2 font-mono text-zinc-600 dark:text-zinc-300">
                          {shortId(r.requester_id)}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex gap-2">
                            <button
                              disabled={decisionBusyId === r.id}
                              onClick={() => void decide(r.id, true)}
                              className="rounded-lg border border-emerald-200 dark:border-emerald-900/40 bg-emerald-50 dark:bg-emerald-950/50 px-3 py-1.5 text-xs font-medium text-emerald-800 dark:text-emerald-200 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition"
                            >
                              {decisionBusyId === r.id ? "..." : "Approve"}
                            </button>
                            <button
                              disabled={decisionBusyId === r.id}
                              onClick={() => void decide(r.id, false)}
                              className="rounded-lg border border-rose-200 dark:border-rose-900/40 bg-rose-50 dark:bg-rose-950/50 px-3 py-1.5 text-xs font-medium text-rose-800 dark:text-rose-200 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition"
                            >
                              {decisionBusyId === r.id ? "..." : "Reject"}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {/* My Requests */}
        <section className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div>
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                My Requests
              </h3>
              <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                Click a row to view full details.
              </p>
            </div>

            <div className="sm:ml-auto flex items-center gap-2">
              <span className="text-sm text-zinc-500 dark:text-zinc-400">Filter</span>
              <select
                className="rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-sm text-zinc-800 dark:text-zinc-200 focus:outline-none focus:ring-2 focus:ring-zinc-300 dark:focus:ring-zinc-700"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              >
                <option value="ALL">ALL</option>
                <option value="PENDING">PENDING</option>
                <option value="APPROVED">APPROVED</option>
                <option value="REJECTED">REJECTED</option>
              </select>

              <button
                type="button"
                disabled={!isAuthed || loadingMine}
                onClick={() => void loadMine()}
                className="rounded-lg border border-zinc-300 dark:border-zinc-700 px-3 py-2 text-sm text-zinc-700 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-900 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {loadingMine ? "Refreshing..." : "Refresh"}
              </button>
            </div>
          </div>

          <div className="mt-5 overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
            <table className="min-w-full text-sm">
              <thead className="bg-zinc-50 dark:bg-zinc-900/40 text-zinc-600 dark:text-zinc-300">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">ID</th>
                  <th className="px-3 py-2 text-left font-medium">Resource</th>
                  <th className="px-3 py-2 text-left font-medium">Action</th>
                  <th className="px-3 py-2 text-left font-medium">Status</th>
                  <th className="px-3 py-2 text-left font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {filteredMine.length === 0 ? (
                  <tr>
                    <td className="px-3 py-3 text-zinc-500 dark:text-zinc-400" colSpan={5}>
                      No requests.
                    </td>
                  </tr>
                ) : (
                  filteredMine.map((r) => (
                    <tr
                      key={r.id}
                      className="cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900/30"
                      onClick={() => setSelected(r)}
                      title="Click to view details"
                    >
                      <td className="px-3 py-2 font-mono text-zinc-800 dark:text-zinc-200">
                        {shortId(r.id)}
                      </td>
                      <td className="px-3 py-2 text-zinc-800 dark:text-zinc-200">
                        {r.resource}
                      </td>
                      <td className="px-3 py-2 text-zinc-800 dark:text-zinc-200">
                        {r.action}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${statusBadge(
                            r.status
                          )}`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-zinc-600 dark:text-zinc-300">
                        {fmtTs(r.created_at)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {selected ? (
            <div className="mt-5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/30 p-4">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                  Selected request {shortId(selected.id)}
                </div>
                <button
                  type="button"
                  onClick={() => setSelected(null)}
                  className="rounded-lg border border-zinc-300 dark:border-zinc-700 px-3 py-1.5 text-xs text-zinc-700 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-900 transition"
                >
                  Close
                </button>
              </div>

              <pre className="mt-3 overflow-x-auto text-xs text-zinc-700 dark:text-zinc-200">
                {JSON.stringify(selected, null, 2)}
              </pre>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}
