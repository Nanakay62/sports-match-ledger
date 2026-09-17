import { notFound } from "next/navigation";
import { ExternalLink, Layers, ShieldCheck } from "lucide-react";
import { fetchEventById } from "@/lib/api";
import { StatusBadge } from "@/components/status-badge";
import { formatDate } from "@/lib/format";

export const dynamic = "force-dynamic";

interface EmbedEventPageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ theme?: string }>;
}

export default async function EmbedEventPage({ params, searchParams }: EmbedEventPageProps) {
  const { id } = await params;
  const { theme } = await searchParams;
  const isDark = theme === "dark";

  const event = await fetchEventById(id);
  if (!event) {
    notFound();
  }

  const publicAppUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
  const eventUrl = `${publicAppUrl}/event/${event.id}`;

  return (
    <div
      className={`max-w-md rounded-md border p-4 shadow-sm font-sans transition-colors ${
        isDark
          ? "border-neutral-800 bg-neutral-900 text-neutral-100"
          : "border-rule bg-paper text-ink"
      }`}
    >
      {/* Header with status badge and category */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rule/50 pb-2.5">
        <div className="flex items-center gap-2">
          <StatusBadge status={event.status} size="chip" />
          <span
            className={`font-mono text-[10.5px] uppercase tracking-wider ${
              isDark ? "text-neutral-400" : "text-ink-faint"
            }`}
          >
            {event.sport} / {event.competition}
          </span>
        </div>
        <div
          className={`font-mono text-[10px] ${
            isDark ? "text-neutral-400" : "text-ink-faint"
          }`}
        >
          {formatDate(event.updatedAt)}
        </div>
      </div>

      {/* Headline & Summary */}
      <div className="mt-3">
        <a
          href={eventUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="group block"
        >
          <h2
            className={`font-display text-base font-semibold leading-snug group-hover:underline ${
              isDark ? "text-neutral-100" : "text-ink"
            }`}
          >
            {event.headline}
          </h2>
        </a>
        <p
          className={`mt-1.5 line-clamp-3 text-[13px] leading-relaxed ${
            isDark ? "text-neutral-300" : "text-ink-soft"
          }`}
        >
          {event.summary}
        </p>
      </div>

      {/* Receipts Evidence Pill */}
      <div className="mt-3.5 flex flex-wrap items-center justify-between gap-2 border-t border-rule/50 pt-2.5">
        <div
          className={`flex items-center gap-1.5 font-mono text-[11px] ${
            isDark ? "text-neutral-300" : "text-ink-soft"
          }`}
        >
          <Layers className="size-3 text-emerald-600" />
          <span>
            <strong>{event.independentSources}</strong> independent sources
          </span>
          {event.firstReportedBy && (
            <>
              <span className="opacity-40">·</span>
              <span>1st: {event.firstReportedBy.outlet}</span>
            </>
          )}
        </div>

        <a
          href={eventUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 font-mono text-[10.5px] font-semibold text-emerald-700 hover:text-emerald-800 dark:text-emerald-400"
        >
          <ShieldCheck className="size-3" />
          <span>View Receipts</span>
          <ExternalLink className="size-2.5 opacity-70" />
        </a>
      </div>

      {/* Footer provenance stamp */}
      <div
        className={`mt-2 text-right font-mono text-[9.5px] tracking-tight ${
          isDark ? "text-neutral-500" : "text-ink-faint"
        }`}
      >
        <span>Sports News AI Accountability Ledger</span>
      </div>
    </div>
  );
}
