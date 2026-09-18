"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { domainOf, formatDate, formatTime, slugify } from "@/lib/format";
import { reliabilityByName } from "@/lib/mock-data";
import { ATTRIBUTION_STYLE } from "@/lib/status";
import { FREE_ARCHIVE_WINDOW_DAYS, useEntitlements } from "@/lib/entitlements";
import type { Claim } from "@/lib/types";
import { ReliabilityPill } from "./reliability-pill";
import { PaywallWall } from "./paywall-wall";

const LANG_NAMES: Record<string, string> = {
  es: "Spanish",
  it: "Italian",
  fr: "French",
  de: "German",
  pt: "Portuguese",
  nl: "Dutch",
};

function isWithinFreeArchiveWindow(timestamp: string): boolean {
  const ageMs = Date.now() - new Date(timestamp).getTime();
  return ageMs <= FREE_ARCHIVE_WINDOW_DAYS * 24 * 60 * 60 * 1000;
}

export function ClaimTimeline({
  claims,
  eventId,
  querySuffix = "",
}: {
  claims: Claim[];
  eventId: string;
  querySuffix?: string;
}) {
  const { isPro, email, loading } = useEntitlements();

  // Handbook §18.3: the archive-depth wall gates history beyond 30 days, never the
  // current record. Free users see every claim from the last 30 days in full.
  const visible = isPro || loading ? claims : claims.filter((c) => isWithinFreeArchiveWindow(c.timestamp));
  const locked = isPro || loading ? [] : claims.filter((c) => !isWithinFreeArchiveWindow(c.timestamp));

  return (
    <div>
      <ol>
        {visible.map((c) => (
          <TimelineRow key={c.id} claim={c} />
        ))}
      </ol>
      {locked.length > 0 && (
        <PaywallWall
          wallId="archive_depth"
          email={email}
          context={eventId}
          querySuffix={querySuffix}
          title={`Full audit trail: ${locked.length} more ${locked.length === 1 ? "entry" : "entries"}`}
          description={`You're seeing claims from the last ${FREE_ARCHIVE_WINDOW_DAYS} days. The complete, timestamped history of this claim (including superseded reports beyond that window) is a Pro feature.`}
          bullets={["History beyond the recent window", "CSV & JSON export of the claim ledger", "Real-time alerts when this status changes"]}
        />
      )}
    </div>
  );
}

function TimelineRow({ claim: c }: { claim: Claim }) {
  const attr = ATTRIBUTION_STYLE[c.attribution];
  const reporterHasRecord = c.reporter ? reliabilityByName.has(c.reporter) : false;
  return (
    <li className="grid grid-cols-[64px_1fr] gap-4 border-b border-rule/60 py-4 last:border-b-0">
      <div className="pt-0.5 font-mono text-[11px] leading-4 text-ink-faint">
        <div>{formatDate(c.timestamp)}</div>
        <div className="text-ink-soft">{formatTime(c.timestamp)}</div>
      </div>
      <div>
        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[13px]">
          <span className={`inline-block size-[7px] shrink-0 ${attr.marker}`} aria-hidden />
          <Link
            href={`/reliability/${slugify(c.outlet)}`}
            className="font-semibold hover:text-ledger hover:underline"
          >
            {c.outlet}
          </Link>
          <ReliabilityPill name={c.outlet} />
          {c.reporter &&
            (reporterHasRecord ? (
              <Link
                href={`/reliability/${slugify(c.reporter)}`}
                className="text-ink-soft hover:text-ink hover:underline"
              >
                {c.reporter}
              </Link>
            ) : (
              <span className="text-ink-soft">{c.reporter}</span>
            ))}
          <span
            className={`rounded-[3px] border px-1.5 py-px font-mono text-[9.5px] font-semibold uppercase tracking-[0.08em] ${attr.badge}`}
          >
            {attr.label}
          </span>
          {c.language !== "en" && (
            <span
              title={`First published in ${LANG_NAMES[c.language] ?? c.language}`}
              className="rounded-[3px] border border-rule-strong px-1 py-px font-mono text-[9.5px] uppercase text-ink-faint"
            >
              {c.language}
            </span>
          )}
        </div>
        <p className="mt-1.5 text-[14.5px] leading-relaxed">{c.text}</p>
        <a
          href={c.url}
          target="_blank"
          rel="noreferrer"
          className="mt-1.5 inline-flex items-center gap-1 font-mono text-[11px] text-ink-faint hover:text-ledger"
        >
          {domainOf(c.url)} <ArrowUpRight className="size-3" aria-hidden />
        </a>
      </div>
    </li>
  );
}
