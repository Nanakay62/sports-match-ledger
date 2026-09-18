"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { trackPaywallEvent, type WallId } from "@/lib/paywall-tracking";

/**
 * The canonical paywall "wall" — soft, contextual and honest (Handbook §18.3):
 * states plainly what's behind it, links to /pro, and reaffirms that current
 * status stays free. Fires a "shown" event on mount and a "clicked" event on the
 * CTA so every wall's conversion can be measured separately (§18.5).
 */
export function PaywallWall({
  wallId,
  email,
  context,
  title,
  description,
  bullets,
  ctaLabel = "See what Pro adds",
  querySuffix = "",
}: {
  wallId: WallId;
  email?: string | null;
  context?: string;
  title: string;
  description: string;
  bullets?: string[];
  ctaLabel?: string;
  querySuffix?: string;
}) {
  useEffect(() => {
    trackPaywallEvent(wallId, "shown", { email, context });
    // Fire once per mount only — re-tracking on every email/context identity change
    // would double-count the same impression.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="mt-6 rounded-[4px] border border-dashed border-rule-strong bg-paper-deep/60 p-5">
      <div className="flex items-center gap-2 font-display text-lg">
        <Lock className="size-4" aria-hidden /> {title}
      </div>
      <p className="mt-1.5 max-w-xl text-[13.5px] leading-relaxed text-ink-soft">{description}</p>
      {bullets && bullets.length > 0 && (
        <ul className="mt-3 space-y-1.5 text-[13px] text-ink-soft">
          {bullets.map((b) => (
            <li key={b} className="flex items-start gap-2">
              <span className="mt-2 size-1.5 shrink-0 rounded-full bg-ink-faint" aria-hidden />
              {b}
            </li>
          ))}
        </ul>
      )}
      <div className="mt-4">
        <Button
          asChild
          size="sm"
          className="bg-ink text-paper hover:bg-ledger-deep"
          onClick={() => trackPaywallEvent(wallId, "clicked", { email, context })}
        >
          <Link href={`/pro${querySuffix}`}>{ctaLabel}</Link>
        </Button>
      </div>
      <p className="mt-3 text-[11.5px] text-ink-faint">The current status of every story stays free, always.</p>
    </div>
  );
}
