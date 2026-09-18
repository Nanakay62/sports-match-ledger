"use client";

// Handbook §18.3/§18.5: "measure the conversion rate of each wall separately."
// Fire-and-forget on purpose — telemetry must never block or break the reading
// experience, so failures are swallowed silently rather than surfaced to the user.

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export type WallId = "watchlist_limit" | "archive_depth" | "reporter_history" | "reporter_index" | "export";
export type WallAction = "shown" | "clicked";

export function trackPaywallEvent(wallId: WallId, action: WallAction, opts?: { email?: string | null; context?: string }) {
  if (typeof window === "undefined") return;
  try {
    fetch(`${API_BASE_URL}/billing/paywall-events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        wall_id: wallId,
        action,
        email: opts?.email ?? null,
        context: opts?.context ?? null,
      }),
      keepalive: true,
    }).catch(() => {});
  } catch {
    // ignore — telemetry is best-effort only
  }
}
