"use client";

// Fire-and-forget, matching the pattern in lib/paywall-tracking.ts: a failed
// subscribe call must never block or break the watchlist UI itself.

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function subscribeToAlerts(email: string | null, eventId: string) {
  if (!email) return;
  try {
    fetch(`${API_BASE_URL}/alerts/subscribe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, event_id: eventId }),
      keepalive: true,
    }).catch(() => {});
  } catch {
    // ignore
  }
}

export function unsubscribeFromAlerts(email: string | null, eventId: string) {
  if (!email) return;
  try {
    fetch(`${API_BASE_URL}/alerts/unsubscribe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, event_id: eventId }),
      keepalive: true,
    }).catch(() => {});
  } catch {
    // ignore
  }
}
