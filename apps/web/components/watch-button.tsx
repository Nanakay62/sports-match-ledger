"use client";

import Link from "next/link";
import { useState } from "react";
import { Bookmark, BookmarkCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

export function WatchButton() {
  const [watching, setWatching] = useState(false);
  return (
    <div className="flex flex-col items-start gap-1.5">
      <Button
        variant={watching ? "default" : "outline"}
        size="sm"
        onClick={() => setWatching((w) => !w)}
        className={
          watching
            ? "border-ledger bg-ledger text-paper hover:bg-ledger-deep"
            : "border-rule-strong text-ink-soft hover:text-ink"
        }
      >
        {watching ? <BookmarkCheck className="size-3.5" aria-hidden /> : <Bookmark className="size-3.5" aria-hidden />}
        {watching ? "On your watchlist" : "Add to watchlist"}
      </Button>
      {watching && (
        <p className="text-[11.5px] text-ink-faint">
          Free watchlists hold 3 ·{" "}
          <Link href="/pro" className="underline hover:text-ink">
            unlimited on Pro
          </Link>
        </p>
      )}
    </div>
  );
}