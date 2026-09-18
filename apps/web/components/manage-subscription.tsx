"use client";

import { useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function ManageSubscription() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  async function openPortal(e: React.FormEvent) {
    e.preventDefault();
    if (!email.includes("@")) {
      setError("Enter a valid email address.");
      return;
    }
    setStatus("submitting");
    setError(null);
    try {
      const resp = await fetch(`${API_BASE_URL}/billing/portal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(resp.status === 404 ? "No subscription found for that email." : body.detail || "Could not open billing portal.");
      }
      const data = await resp.json();
      window.location.href = data.portal_url;
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  return (
    <form onSubmit={openPortal} className="flex flex-col gap-2 sm:flex-row sm:items-center">
      <label htmlFor="manage-sub-email" className="sr-only">
        Email address
      </label>
      <input
        id="manage-sub-email"
        type="email"
        required
        placeholder="you@example.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="min-w-0 flex-1 border border-rule-strong bg-paper px-3 py-2 text-[13.5px] outline-none focus-visible:ring-1 focus-visible:ring-ink"
      />
      <button
        type="submit"
        disabled={status === "submitting"}
        className="shrink-0 border border-ink px-4 py-2 text-[13px] font-medium hover:bg-paper-deep disabled:opacity-50"
      >
        {status === "submitting" ? "Opening…" : "Manage subscription"}
      </button>
      {error && <p className="w-full text-[12px] text-disputed sm:w-auto">{error}</p>}
    </form>
  );
}
