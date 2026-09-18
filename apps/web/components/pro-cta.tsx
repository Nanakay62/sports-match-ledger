"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

type Status = "idle" | "submitting" | "error";

export function ProCta({ label, planId }: { label: string; planId: "plan_pro_monthly" | "plan_pro_annual" }) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

  async function startCheckout(e: React.FormEvent) {
    e.preventDefault();
    if (!email.includes("@")) {
      setError("Enter a valid email address.");
      return;
    }
    setStatus("submitting");
    setError(null);
    try {
      const resp = await fetch(`${API_BASE_URL}/billing/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_id: planId, email }),
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(body.detail || "Checkout could not be started.");
      }
      const data = await resp.json();
      window.location.href = data.checkout_url;
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  return (
    <form onSubmit={startCheckout} className="space-y-2">
      <label htmlFor={`pro-email-${planId}`} className="sr-only">
        Email address
      </label>
      <input
        id={`pro-email-${planId}`}
        type="email"
        required
        placeholder="you@example.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="w-full border border-rule-strong bg-paper px-3 py-2 text-[13.5px] outline-none focus-visible:ring-1 focus-visible:ring-ink"
      />
      <Button type="submit" disabled={status === "submitting"} className="w-full bg-ink text-paper hover:bg-ledger-deep">
        {status === "submitting" ? "Redirecting to checkout…" : label}
      </Button>
      {error && (
        <p className="border border-dashed border-disputed/60 bg-paper-deep/60 px-3 py-2 text-[12px] leading-relaxed text-disputed">
          {error}
        </p>
      )}
      <p className="text-[11px] leading-relaxed text-ink-faint">
        Handled by Stripe Checkout. The free ledger never changes, whatever you choose here.
      </p>
    </form>
  );
}
