"use client";

import Link from "next/link";
import { ArrowUpRight, BellRing, FileDown, History, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { domainOf, formatDate, formatTime, slugify } from "@/lib/format";
import { reliabilityByName } from "@/lib/mock-data";
import { ATTRIBUTION_STYLE } from "@/lib/status";
import type { Claim } from "@/lib/types";
import { ReliabilityPill } from "./reliability-pill";

const VISIBLE_FREE = 4;
const LANG_NAMES: Record<string, string> = {
  es: "Spanish", it: "Italian", fr: "French", de: "German", pt: "Portuguese", nl: "Dutch",
};

export function ClaimTimeline({ claims }: { claims: Claim[] }) {
  const visible = claims.slice(0, VISIBLE_FREE);
  const locked = claims.slice(VISIBLE_FREE);
  return (
    <div>
      <ol>
        {visible.map((c) => (
          <TimelineRow key={c.id} claim={c} />
        ))}
      </ol>
      {locked.length > 0 && <LockedNote count={locked.length} />}
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

function LockedNote({ count }: { count: number }) {
  return (
    <div className="mt-6 rounded-[4px] border border-dashed border-rule-strong bg-paper-deep/60 p-5">
      <div className="flex items-center gap-2 font-display text-lg">
        <Lock className="size-4" aria-hidden /> Full audit trail: {count} more{" "}
        {count === 1 ? "entry" : "entries"}
      </div>
      <p className="mt-1.5 max-w-xl text-[13.5px] leading-relaxed text-ink-soft">
        You're seeing the most recent entries. The complete, timestamped history of this claim
        (including superseded reports and the paperwork trail) is a Pro feature.
      </p>
      <ul className="mt-3 space-y-1.5 text-[13px] text-ink-soft">
        <li className="flex items-start gap-2">
          <History className="mt-0.5 size-3.5 shrink-0 text-ink-faint" aria-hidden />
          History beyond the recent window
        </li>
        <li className="flex items-start gap-2">
          <FileDown className="mt-0.5 size-3.5 shrink-0 text-ink-faint" aria-hidden />
          CSV &amp; JSON export of the claim ledger
        </li>
        <li className="flex items-start gap-2">
          <BellRing className="mt-0.5 size-3.5 shrink-0 text-ink-faint" aria-hidden />
          Real-time alerts when this status changes
        </li>
      </ul>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button asChild size="sm" className="bg-ink text-paper hover:bg-ledger-deep">
          <Link href="/pro">See what Pro adds</Link>
        </Button>
        <Button
          asChild
          size="sm"
          variant="outline"
          className="border-rule-strong text-ink-soft hover:text-ink"
          title="Export is a Pro feature"
        >
          <Link href="/pro">
            <FileDown className="size-3.5" aria-hidden /> Export ledger
            <Lock className="size-3 text-ink-faint" aria-hidden />
          </Link>
        </Button>
      </div>
      <p className="mt-3 text-[11.5px] text-ink-faint">
        The current status and every claim above stay free, always.
      </p>
    </div>
  );
}