"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

type Req = {
  id: string;
  resource: string;
  action: string;
  requester_id: string;
};

type FastApiError = { detail?: unknown };

function getErrorMessage(e: unknown): string {
  if (e instanceof Error) return e.message;
  if (typeof e === "string") return e;
  try {
    return JSON.stringify(e);
  } catch {
    return "Request failed";
  }
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

export default function Approvals() {
  const [mounted, setMounted] = useState(false);
  const [token, setToken] = useState<string>("");

  const [rows, setRows] = useState<Req[]>([]);
  const [err, setErr] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    // Ensure client-only read of localStorage to avoid hydration mismatch
    setMounted(true);
    const t =
      localStorage.getItem("accessops_token") ||
      localStorage.getItem("token") ||
      "";
    setToken(t);
  }, []);

  const isAuthed = token.trim().length > 0;

  const load = useCallback(async () => {
    if (!isAuthed) return;
    setErr("");
    setLoading(true);
    try {
      const r = await fetch(`${API}/requests/pending`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const j = await safeJson(r);
      if (!r.ok) throw new Error(parseFastApiError(j));

      setRows((j as Req[]) || []);
    } catch (e: unknown) {
      setErr(getErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [token, isAuthed]);

  const decide = useCallback(
    async (id: string, approve: boolean) => {
      if (!isAuthed) return;
      setErr("");
      try {
        const r = await fetch(`${API}/requests/${id}/${approve ? "approve" : "reject"}`, {
          method: "PATCH",
          headers: { Authorization: `Bearer ${token}` },
        });

        const j = await safeJson(r);
        if (!r.ok) throw new Error(parseFastApiError(j));

        await load();
      } catch (e: unknown) {
        setErr(getErrorMessage(e));
      }
    },
    [token, isAuthed, load]
  );

  useEffect(() => {
    if (!mounted || !isAuthed) return;
    void load();
  }, [mounted, isAuthed, load]);

  // Stable SSR/initial render: avoid branching on token before mount
  if (!mounted) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold">Approvals</h2>
        <div className="mt-3 text-sm text-zinc-500">Loading…</div>
      </div>
    );
  }

  if (!isAuthed) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold">Approvals</h2>
        <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          Missing token. Login first.
          <div className="mt-2 text-xs text-rose-700">
            Expected localStorage key: <span className="font-mono">accessops_token</span>{" "}
            (fallback: <span className="font-mono">token</span>).
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">Approvals</h2>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-50"
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {err && (
        <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
          {err}
        </div>
      )}

      <div className="mt-4 space-y-2">
        {loading && rows.length === 0 ? (
          <div className="text-sm text-zinc-500">Loading pending requests…</div>
        ) : rows.length === 0 ? (
          <div className="text-sm text-zinc-500">No pending requests.</div>
        ) : (
          rows.map((r) => (
            <div key={r.id} className="flex items-center gap-3 rounded-lg border p-3">
              <div className="flex-1 text-sm">
                <div className="font-medium">{r.resource}</div>
                <div className="text-zinc-500">{r.action}</div>
              </div>
              <button
                className="rounded-lg border px-3 py-1.5 text-sm"
                onClick={() => void decide(r.id, true)}
              >
                Approve
              </button>
              <button
                className="rounded-lg border px-3 py-1.5 text-sm"
                onClick={() => void decide(r.id, false)}
              >
                Reject
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

