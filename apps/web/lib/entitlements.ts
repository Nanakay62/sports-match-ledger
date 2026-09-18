"use client";

import { useCallback, useEffect, useState } from "react";
import { clearStoredEmail, getStoredEmail, setStoredEmail } from "./identity";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// These three constants mirror the source of truth in
// packages/database/billing_repository.py (FREE_WATCHLIST_LIMIT,
// FREE_ARCHIVE_WINDOW_DAYS, FREE_REPORTER_INDEX_LIMIT). The watchlist limit itself
// comes back from the entitlements API per-user; the other two are fixed product
// constants with no per-user variation, so they're not worth a round trip.
export const FREE_ARCHIVE_WINDOW_DAYS = 30;
export const FREE_REPORTER_INDEX_LIMIT = 20;

export interface Entitlements {
  email: string | null;
  isPro: boolean;
  watchlistLimit: number;
  hasRealtimeAlerts: boolean;
  hasFullHistory: boolean;
  hasExport: boolean;
  loading: boolean;
}

const FREE_DEFAULTS = {
  isPro: false,
  watchlistLimit: 3,
  hasRealtimeAlerts: false,
  hasFullHistory: false,
  hasExport: false,
};

export function useEntitlements() {
  const [state, setState] = useState<Entitlements>({ email: null, loading: true, ...FREE_DEFAULTS });

  const refresh = useCallback(async (targetEmail: string | null) => {
    if (!targetEmail) {
      setState({ email: null, loading: false, ...FREE_DEFAULTS });
      return;
    }
    setState((prev) => ({ ...prev, email: targetEmail, loading: true }));
    try {
      const resp = await fetch(`${API_BASE_URL}/billing/entitlements/${encodeURIComponent(targetEmail)}`);
      if (!resp.ok) throw new Error(`entitlements lookup failed: ${resp.status}`);
      const data = await resp.json();
      setState({
        email: targetEmail,
        loading: false,
        isPro: Boolean(data.is_pro),
        watchlistLimit: data.watchlist_limit ?? FREE_DEFAULTS.watchlistLimit,
        hasRealtimeAlerts: Boolean(data.has_realtime_alerts),
        hasFullHistory: Boolean(data.has_full_history),
        hasExport: Boolean(data.has_export),
      });
    } catch {
      // API unreachable or the email has no record yet — fail safe to free tier,
      // never fail open into Pro.
      setState({ email: targetEmail, loading: false, ...FREE_DEFAULTS });
    }
  }, []);

  useEffect(() => {
    refresh(getStoredEmail());
    function onIdentityChanged() {
      refresh(getStoredEmail());
    }
    window.addEventListener("snai:identity-changed", onIdentityChanged);
    return () => window.removeEventListener("snai:identity-changed", onIdentityChanged);
  }, [refresh]);

  const identify = useCallback(
    (email: string) => {
      setStoredEmail(email);
      refresh(email);
    },
    [refresh],
  );

  const signOut = useCallback(() => {
    clearStoredEmail();
    setState({ email: null, loading: false, ...FREE_DEFAULTS });
  }, []);

  return { ...state, identify, signOut };
}
