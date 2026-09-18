"use client";

// Handbook §18.1: "Passwordless email sign-in is sufficient." This is deliberately
// less than that — there is no verification that the visitor owns the email they
// type in, no session, no cross-device sync. It exists only so the browser can ask
// the API "what does this email's entitlement record say" when checking a paywall.
// See docs/adr/0017-stripe-billing-and-persisted-entitlements.md for the known gap.

const STORAGE_KEY = "snai_identity_email";

export function getStoredEmail(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredEmail(email: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, email.trim().toLowerCase());
    window.dispatchEvent(new CustomEvent("snai:identity-changed"));
  } catch {
    // Private-window/blocked-storage: silently no-op, caller falls back to free tier.
  }
}

export function clearStoredEmail(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(STORAGE_KEY);
    window.dispatchEvent(new CustomEvent("snai:identity-changed"));
  } catch {
    // ignore
  }
}
