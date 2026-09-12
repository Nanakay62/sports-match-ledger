"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { entryNo, leadTime, timeAgo } from "@/lib/format";
import { getClaims } from "@/lib/mock-data";
import type { Event } from "@/lib/types";
import type { ReasoningBullet } from "@/lib/evidence";
import { StatusBadge } from "./status-badge";
import { EntityChip } from "./entity-chip";
import { ReliabilityPill } from "./reliability-pill";
import { WhyDisclosure } from "./why-disclosure";

export function LeadStory({ event, reasoning }: { event: Event; reasoning: ReasoningBullet[] }) {
  const [showOriginal, setShowOriginal] = useState(false);
  const claims = getClaims(event.id);
  const original = claims.find((c) => c.attribution === "original");
  const sourceOutlet = original?.outlet ?? event.firstReportedBy?.outlet;
  const lead = event.firstReportedBy;
  const href = `/event/${event.id}`;

  const displayHeadline = showOriginal && event.originalHeadline ? event.originalHeadline : event.headline;
  const displaySummary = showOriginal && event.originalSummary ? event.originalSummary : event.summary;

  return (
    <article className="border-b-2 border-ink pb-10">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink-faint">
        <span>{event.competition}</span>
        <span aria-hidden>·</span>
        <span>{event.sport}</span>
        <span aria-hidden>·</span>
        <span>Entry № {entryNo(event.id)}</span>
        <span aria-hidden>·</span>
        <span suppressHydrationWarning>Updated {timeAgo(event.updatedAt)}</span>
        {event.isTranslated && (
          <>
            <span aria-hidden>·</span>
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
          </>
        )}
      </div>

      <h2 className="mt-3 font-display text-[1.9rem] font-medium leading-[1.07] tracking-tight md:text-[2.5rem]">
        <Link href={href} className="decoration-[1.5px] underline-offset-[6px] hover:underline">
          {displayHeadline}
        </Link>
      </h2>

      <p className="mt-3 max-w-2xl text-[15.5px] leading-relaxed text-ink-soft">{displaySummary}</p>

      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-[12.5px]">
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
            First: <b className="font-semibold text-ink-soft">{lead.outlet}</b>
            {lead.leadTimeMinutes > 0 && <> · {leadTime(lead.leadTimeMinutes)} ahead of next outlet</>}
          </span>
        )}
        <span className="font-mono text-[11.5px] text-ink-faint">
          {event.independentSources} independent sources
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {event.entities.map((e) => (
          <EntityChip key={e.name} entity={e} />
        ))}
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-4">
        <StatusBadge status={event.status} size="stamp" />
        <WhyDisclosure reasoning={reasoning} />
        <Link
          href={href}
          className="inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-ledger hover:underline"
        >
          Read the full entry <ArrowRight className="size-3.5" aria-hidden />
        </Link>
      </div>
    </article>
  );
}