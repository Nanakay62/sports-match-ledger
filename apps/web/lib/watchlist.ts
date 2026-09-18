"use client";

import { useCallback, useEffect, useState } from "react";

// Client-persisted only (localStorage), not synced to the server or across devices.
// This is a deliberate scope decision, not an oversight: a soft, honest paywall
// (Handbook §18.3) needs a real count to gate against, but a full server-side
// watchlist service (a DB model, CRUD API, cross-device sync) is a separate,
// larger product surface than "make the paywall real." Free users get a fully
// working watchlist on this device; it just doesn't follow them to another one.

const STORAGE_KEY = "snai_watchlist_event_ids";
const CHANGE_EVENT = "snai:watchlist-changed";

function readAll(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeAll(ids: string[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
    window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
  } catch {
    // ignore — private window or storage blocked
  }
}

export function getWatchlist(): string[] {
  return readAll();
}

export function addToWatchlist(eventId: string): void {
  const current = readAll();
  if (!current.includes(eventId)) {
    writeAll([...current, eventId]);
  }
}

export function removeFromWatchlist(eventId: string): void {
  writeAll(readAll().filter((id) => id !== eventId));
}

export function useWatchlist() {
  const [ids, setIds] = useState<string[]>([]);

  useEffect(() => {
    setIds(readAll());
    function onChange() {
      setIds(readAll());
    }
    window.addEventListener(CHANGE_EVENT, onChange);
    window.addEventListener("storage", onChange);
    return () => {
      window.removeEventListener(CHANGE_EVENT, onChange);
      window.removeEventListener("storage", onChange);
    };
  }, []);

  const add = useCallback((eventId: string) => {
    addToWatchlist(eventId);
    setIds(readAll());
  }, []);

  const remove = useCallback((eventId: string) => {
    removeFromWatchlist(eventId);
    setIds(readAll());
  }, []);

  const isWatching = useCallback((eventId: string) => ids.includes(eventId), [ids]);

  return { ids, add, remove, isWatching };
}
