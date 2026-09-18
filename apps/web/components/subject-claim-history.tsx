"use client";

import Link from "next/link";
import { Check, X } from "lucide-react";
import { StatusBadge } from "@/components/status-badge";
import { timeAgo } from "@/lib/format";
import { FREE_ARCHIVE_WINDOW_DAYS, useEntitlements } from "@/lib/entitlements";
import type { Claim, Event } from "@/lib/types";
import { PaywallWall } from "./paywall-wall";

interface ResolutionRecord {
  claim: string;
  outcome?: string;
}

function isWithinFreeArchiveWindow(timestamp: string): boolean {
  const ageMs = Date.now() - new Date(timestamp).getTime();
  return ageMs <= FREE_ARCHIVE_WINDOW_DAYS * 24 * 60 * 60 * 1000;
}

/** Handbook §18.3: "full reporter history" is a named wall — free sees the last 30
 * days on record for this outlet/reporter, Pro sees the full chronological log.
 */
export function SubjectClaimHistory({
  rows,
  recentResolutions,
  subjectSlug,
  querySuffix = "",
}: {
  rows: { claim: Claim; event: Event }[];
  recentResolutions: ResolutionRecord[];
  subjectSlug: string;
  querySuffix?: string;
}) {
  const { isPro, email, loading } = useEntitlements();

  const visible = isPro || loading ? rows : rows.filter((r) => isWithinFreeArchiveWindow(r.claim.timestamp));
  const hiddenCount = isPro || loading ? 0 : rows.length - visible.length;

  if (rows.length === 0) {
    return <p className="mt-6 text-[13.5px] text-ink-faint">No claims recorded yet for this subject.</p>;
  }

  return (
    <div>
      <div className="divide-y divide-rule">
        {visible.map(({ claim, event }) => {
          const res = recentResolutions.find((r) => r.claim === claim.text);
          const outcome = res?.outcome;

          return (
            <article key={claim.id} className="py-4 text-[13.5px]">
              <div className="flex flex-wrap items-center justify-between gap-2 text-[12px] text-ink-faint">
                <div className="flex items-center gap-2">
                  <StatusBadge status={event.status} size="chip" />
                  <span className="font-mono text-[11px]">Claim № {claim.id}</span>
                </div>
                <span suppressHydrationWarning className="font-mono text-[11px]">
                  {timeAgo(claim.timestamp)}
                </span>
              </div>

              <p className="mt-2 text-ink-soft">&quot;{claim.text}&quot;</p>

              <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[12px]">
                <Link href={`/event/${event.id}${querySuffix}`} className="font-medium text-ledger hover:underline">
                  {event.headline} →
                </Link>
                {outcome && (
                  <span
                    className={`inline-flex items-center gap-1 font-mono text-[11px] uppercase tracking-wider ${
                      outcome === "correct"
                        ? "font-medium text-confirmed"
                        : outcome === "incorrect"
                          ? "font-medium text-disputed"
                          : "text-ink-faint"
                    }`}
                  >
                    {outcome === "correct" ? <Check className="size-3" /> : outcome === "incorrect" ? <X className="size-3" /> : null}
                    Outcome: {outcome}
                  </span>
                )}
              </div>
            </article>
          );
        })}
      </div>
      {hiddenCount > 0 && (
        <PaywallWall
          wallId="reporter_history"
          email={email}
          context={subjectSlug}
          querySuffix={querySuffix}
          title={`Full history: ${hiddenCount} more ${hiddenCount === 1 ? "claim" : "claims"}`}
          description={`You're seeing claims from the last ${FREE_ARCHIVE_WINDOW_DAYS} days. The complete chronological record for this outlet or reporter is a Pro feature.`}
          bullets={["Full claim history beyond the recent window", "CSV & JSON export of this record"]}
        />
      )}
    </div>
  );
}
