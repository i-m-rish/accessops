"use client";
import React, { useMemo, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [msg, setMsg] = useState<string>("");
  const [kind, setKind] = useState<"info" | "success" | "error">("info");
  const [loading, setLoading] = useState(false);

  const canSubmit = useMemo(() => {
    return email.trim().length > 0 && password.trim().length > 0 && !loading;
  }, [email, password, loading]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();

    setLoading(true);
    setKind("info");
    setMsg("Logging in...");

    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        const err =
          data?.detail?.[0]?.msg ||
          data?.detail ||
          "Login failed. Please verify your credentials.";
        setKind("error");
        setMsg(String(err));
        return;
      }

      localStorage.setItem("token", data.access_token);
      setKind("success");
      setMsg("Login successful. Token stored in localStorage.");
      setPassword("");
    } catch {
      setKind("error");
      setMsg("Network error. Is the API server running on 127.0.0.1:8000?");
    } finally {
      setLoading(false);
    }
  };

  const badgeClass =
    kind === "success"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/40 dark:bg-emerald-950/50 dark:text-emerald-200"
      : kind === "error"
      ? "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/40 dark:bg-rose-950/50 dark:text-rose-200"
      : "border-zinc-200 bg-zinc-50 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900/40 dark:text-zinc-200";

  return (
    <main className="min-h-screen bg-zinc-50 dark:bg-black flex items-center justify-center px-6">
      <div className="w-full max-w-md rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-sm p-8">
        {/* Header */}
        <div className="mb-7">
          <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
            Login
          </h2>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Sign in to access your governance console.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
              Email
            </label>
            <input
              className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-300 dark:focus:ring-zinc-700"
              placeholder="req@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              inputMode="email"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                Password
              </label>
              <span className="text-xs text-zinc-500 dark:text-zinc-400">
                Minimum 8 chars (register)
              </span>
            </div>
            <input
              className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-300 dark:focus:ring-zinc-700"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          <button
            disabled={!canSubmit}
            className="w-full rounded-lg bg-black dark:bg-white px-4 py-2.5 text-sm font-medium text-white dark:text-black hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>

        {/* Message */}
        {msg ? (
          <div className={`mt-5 rounded-lg border px-3 py-2 text-sm ${badgeClass}`}>
            {msg}
          </div>
        ) : null}

        {/* Footer actions */}
        <div className="mt-6 flex items-center justify-between text-sm">
          <Link
            href="/register"
            className="text-zinc-700 dark:text-zinc-200 hover:underline"
          >
            Create an account
          </Link>
          <Link
            href="/"
            className="text-zinc-500 dark:text-zinc-400 hover:underline"
          >
            Back to home
          </Link>
        </div>

        <div className="mt-6 text-xs text-zinc-400">
          Tip: After login, the bearer token is stored in <span className="font-mono">localStorage</span>.
        </div>
      </div>
    </main>
  );
}

export default Login;
