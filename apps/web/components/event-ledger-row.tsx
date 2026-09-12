"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { entryNo, formatDate, leadTime, timeAgo } from "@/lib/format";
import { getClaims } from "@/lib/mock-data";
import type { Event } from "@/lib/types";
import type { ReasoningBullet } from "@/lib/evidence";
import { StatusBadge } from "./status-badge";
import { EntityChip } from "./entity-chip";
import { ReliabilityPill } from "./reliability-pill";
import { WhyDisclosure } from "./why-disclosure";

export function LedgerRowItem({ event, reasoning }: { event: Event; reasoning: ReasoningBullet[] }) {
  const [showOriginal, setShowOriginal] = useState(false);
  const claims = getClaims(event.id);
  const original = claims.find((c) => c.attribution === "original");
  const sourceOutlet = original?.outlet ?? event.firstReportedBy?.outlet;
  const href = `/event/${event.id}`;
  const lead = event.firstReportedBy;

  const displayHeadline = showOriginal && event.originalHeadline ? event.originalHeadline : event.headline;
  const displaySummary = showOriginal && event.originalSummary ? event.originalSummary : event.summary;

  return (
    <li className="border-b border-rule">
      <div className="grid gap-x-6 gap-y-3 py-6 md:grid-cols-[minmax(0,1fr)_190px]">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink-faint">
            <span>{event.competition} · {event.sport} · Entry № {entryNo(event.id)} ·{" "}</span>
            <span suppressHydrationWarning>Updated {timeAgo(event.updatedAt)}</span>
            {event.isTranslated && (
              <span className="inline-flex items-center gap-1 rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-800 border border-amber-200">
                Translated from {event.originalLanguage?.toUpperCase()}
                <button
                  type="button"
                  onClick={() => setShowOriginal(!showOriginal)}
                  className="ml-1 underline font-semibold hover:text-amber-950 cursor-pointer"
                >
                  {showOriginal ? "Show translation" : "Show original"}
                </button>
              </span>
            )}
          </div>

          <h3 className="mt-2 font-display text-[1.35rem] font-medium leading-snug tracking-tight md:text-2xl">
            <Link
              href={href}
              className="decoration-[1.5px] underline-offset-[5px] hover:underline"
            >
              {displayHeadline}
            </Link>
          </h3>

          <p className="mt-1.5 line-clamp-2 max-w-[65ch] text-[15px] leading-relaxed text-ink-soft">
            {displaySummary}
          </p>

          {/* Mandatory evidence line: source, first-report attribution, original link */}
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[12.5px]">
            {sourceOutlet && (
              <>
                <a
                  href={event.sourceUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 font-semibold transition-colors hover:text-ledger"
                >
                  Source: {sourceOutlet} <ArrowUpRight className="size-3" aria-hidden />
                </a>
                <ReliabilityPill name={sourceOutlet} />
              </>
            )}
            {lead && (
              <span className="text-ink-faint">
                First:{" "}
                <b className="font-semibold text-ink-soft">{lead.outlet}</b>
                {lead.leadTimeMinutes > 0 && <> · {leadTime(lead.leadTimeMinutes)} ahead of next outlet</>}
              </span>
            )}
            <span className="font-mono text-[11.5px] text-ink-faint">
              {event.independentSources} independent {event.independentSources === 1 ? "source" : "sources"}
            </span>
          </div>

          <div className="mt-2.5 flex flex-wrap gap-1.5">
            {event.entities.map((e) => (
              <EntityChip key={e.name} entity={e} />
            ))}
          </div>

          <div className="mt-3.5">
            <WhyDisclosure reasoning={reasoning} />
          </div>
        </div>

        <div className="flex items-center justify-between gap-2 md:flex-col md:items-end md:justify-start md:border-l md:border-rule md:pl-5 md:text-right">
          <StatusBadge status={event.status} />
          <div className="font-mono text-[11px] leading-4 text-ink-faint">
            <div suppressHydrationWarning>{timeAgo(event.updatedAt)}</div>
            <div>{formatDate(event.updatedAt)}</div>
          </div>
        </div>
      </div>
    </li>
  );
}