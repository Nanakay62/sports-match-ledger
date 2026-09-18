"use client";

import { useState } from "react";
import { useEntitlements } from "@/lib/entitlements";

/**
 * Minimal email-only identity control (Handbook §18.1). Not a login: there is no
 * verification that the visitor owns the email they type, no session, no
 * cross-device sync — see docs/adr/0017 for the known gap. It exists so the
 * browser has something to check entitlements and watchlist limits against.
 */
export function AccountStatus() {
  const { email, isPro, loading, identify, signOut } = useEntitlements();
  const [open, setOpen] = useState(false);
  const [draftEmail, setDraftEmail] = useState("");

  if (email) {
    return (
      <div className="flex items-center gap-2 font-mono text-[10.5px] uppercase tracking-[0.1em] text-ink-faint">
        <span className={isPro ? "font-semibold text-ledger" : ""}>{loading ? "…" : isPro ? "Pro" : "Free"}</span>
        <span className="hidden sm:inline text-ink-faint">·</span>
        <span className="hidden max-w-[140px] truncate sm:inline">{email}</span>
        <button type="button" onClick={signOut} className="underline decoration-dotted hover:text-ink">
          sign out
        </button>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-ink-faint underline decoration-dotted hover:text-ink"
      >
        Identify yourself
      </button>
      {open && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!draftEmail.includes("@")) return;
            identify(draftEmail);
            setOpen(false);
            setDraftEmail("");
          }}
          className="absolute right-0 top-full z-10 mt-2 w-64 border border-rule-strong bg-paper p-3 shadow-sm"
        >
          <label htmlFor="account-email" className="block text-[11px] normal-case text-ink-soft">
            Enter the email you subscribed with (or any email — Free works signed out too).
          </label>
          <input
            id="account-email"
            type="email"
            autoFocus
            value={draftEmail}
            onChange={(e) => setDraftEmail(e.target.value)}
            placeholder="you@example.com"
            className="mt-2 w-full border border-rule-strong bg-paper px-2 py-1.5 text-[12.5px] normal-case outline-none focus-visible:ring-1 focus-visible:ring-ink"
          />
          <button
            type="submit"
            className="mt-2 w-full border border-ink bg-ink px-2 py-1.5 text-[12px] normal-case text-paper hover:bg-ledger-deep"
          >
            Check my status
          </button>
        </form>
      )}
    </div>
  );
}
