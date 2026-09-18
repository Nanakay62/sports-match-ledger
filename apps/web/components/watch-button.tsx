"use client";

import { useState } from "react";
import Link from "next/link";
import { Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useEntitlements } from "@/lib/entitlements";
import { useWatchlist } from "@/lib/watchlist";
import { trackPaywallEvent } from "@/lib/paywall-tracking";

export function WatchButton({ eventId, querySuffix = "" }: { eventId: string; querySuffix?: string }) {
  const { watchlistLimit, email, loading } = useEntitlements();
  const { ids, add, remove, isWatching } = useWatchlist();
  const [showWall, setShowWall] = useState(false);

  const watching = isWatching(eventId);
  const atLimit = !loading && ids.length >= watchlistLimit && !watching;

  function handleClick() {
    if (watching) {
      remove(eventId);
      return;
    }
    if (atLimit) {
      trackPaywallEvent("watchlist_limit", "shown", { email, context: eventId });
      setShowWall(true);
      return;
    }
    add(eventId);
  }

  return (
    <div className="flex flex-col items-start gap-1.5">
      <Button
        variant={watching ? "default" : "outline"}
        size="sm"
        onClick={handleClick}
        className={watching ? "bg-ink text-paper hover:bg-ledger-deep" : "border-rule-strong text-ink-soft hover:text-ink"}
      >
        {watching ? "On your watchlist" : "Add to watchlist"}
      </Button>
      {!watching && ids.length > 0 && (
        <p className="text-[11.5px] text-ink-faint">
          Watching {ids.length} of {watchlistLimit === 99999 ? "unlimited" : watchlistLimit} free ·{" "}
          <Link href={`/pro${querySuffix}`} className="underline hover:text-ink">
            unlimited on Pro
          </Link>
        </p>
      )}
      {showWall && (
        <div className="mt-1 max-w-xs rounded-[4px] border border-dashed border-rule-strong bg-paper-deep/60 p-3">
          <div className="flex items-center gap-1.5 text-[13px] font-semibold">
            <Lock className="size-3.5" aria-hidden /> Free watchlists hold {watchlistLimit}
          </div>
          <p className="mt-1 text-[12px] leading-relaxed text-ink-soft">
            Remove a story to add this one, or go unlimited on Pro.
          </p>
          <Button
            asChild
            size="sm"
            className="mt-2 bg-ink text-paper hover:bg-ledger-deep"
            onClick={() => trackPaywallEvent("watchlist_limit", "clicked", { email, context: eventId })}
          >
            <Link href={`/pro${querySuffix}`}>See what Pro adds</Link>
          </Button>
        </div>
      )}
    </div>
  );
}
