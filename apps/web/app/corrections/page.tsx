import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight, CheckCircle2, History, AlertTriangle } from "lucide-react";
import { StatusBadge } from "@/components/status-badge";
import { loadCorrections } from "@/lib/data-loader";
import { formatDate, timeAgo } from "@/lib/format";
import { getDictionary } from "@/lib/i18n";

export const metadata: Metadata = {
  title: "Public Corrections Log · Matchday Ledger",
  description: "Public, append-only record of retracted, amended, and superseded reporting.",
};

export default async function CorrectionsPage({
  searchParams,
}: {
  searchParams?: Promise<{ lang?: string }>;
}) {
  const sParams = searchParams ? await searchParams : undefined;
  const lang = sParams?.lang || "en";
  const t = getDictionary(lang);
  const querySuffix = lang !== "en" ? `?lang=${lang}` : "";

  const corrections = await loadCorrections(lang);

  return (
    <main className="mx-auto max-w-4xl px-4 pb-24 pt-6 md:px-6">
      {/* Breadcrumb */}
      <nav
        className="font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink-faint"
        aria-label="Breadcrumb"
      >
        <Link href={`/${querySuffix}`} className="hover:text-ink">
          {t.navLedger}
        </Link>
        <span className="mx-1.5">/</span>
        <span>Audit</span>
        <span className="mx-1.5">/</span>
        <span>{t.correctionsTitle}</span>
      </nav>

      {/* Header Banner */}
      <header className="mt-6 border-b-2 border-ink pb-6">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-confirmed">
          <CheckCircle2 className="size-4" aria-hidden />
          <span>{t.correctionsBadge}</span>
        </div>
        <h1 className="mt-2 font-display text-4xl font-medium tracking-tight md:text-5xl">
          {t.correctionsTitle}
        </h1>
        <div className="mt-4 border-l-2 border-ink pl-4">
          <p className="font-display text-[16px] leading-relaxed text-ink-soft">
            <span className="font-semibold text-ink">{t.correctionsRuleTitle}</span>{" "}
            {t.correctionsRuleText}
          </p>
        </div>
      </header>

      {/* Table / List of Corrections */}
      <section className="mt-8" aria-label="Corrections log">
        <div className="flex items-baseline justify-between border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-ink-faint">
          <span>
            {corrections.length} {t.correctionsSubheader}
          </span>
          <span>{t.correctionsOrder}</span>
        </div>

        {corrections.length === 0 ? (
          <div className="py-12 text-center text-ink-faint">
            <History className="mx-auto size-8 opacity-40" />
            <p className="mt-2 text-[14px]">{t.correctionsEmpty}</p>
          </div>
        ) : (
          <div className="divide-y divide-rule">
            {corrections.map(({ claim, event }) => (
              <article key={claim.id} className="py-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={event.status} size="stamp" />
                    <span className="font-mono text-[11.5px] text-ink-faint">
                      {t.claimNo} {claim.id}
                    </span>
                  </div>
                  <span className="font-mono text-[11.5px] text-ink-faint">
                    {t.amendedAgo}{" "}
                    <span suppressHydrationWarning>{timeAgo(claim.timestamp)}</span>
                  </span>
                </div>

                <h2 className="mt-3 font-display text-xl font-medium leading-snug">
                  <Link href={`/event/${event.id}${querySuffix}`} className="hover:underline">
                    {event.headline}
                  </Link>
                </h2>

                <div className="mt-4 grid gap-4 rounded border border-rule bg-rule/20 p-4 md:grid-cols-2">
                  <div className="border-l-2 border-rule-strong pl-3">
                    <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-ink-faint">
                      {t.originalDisputedClaim}
                    </div>
                    <p className="mt-1 text-[13.5px] italic text-ink-soft">"{claim.text}"</p>
                    <div className="mt-2 text-[11.5px] text-ink-faint">
                      {t.attributedTo}{" "}
                      <span className="font-medium text-ink">
                        {claim.reporter ? `${claim.reporter} (${claim.outlet})` : claim.outlet}
                      </span>
                    </div>
                  </div>

                  <div className="border-l-2 border-corrected pl-3">
                    <div className="flex items-center gap-1 font-mono text-[10px] uppercase tracking-[0.14em] text-corrected">
                      <AlertTriangle className="size-3.5" aria-hidden />
                      <span>{t.correctionContext}</span>
                    </div>
                    <p className="mt-1 text-[13.5px] text-ink-soft">
                      {event.statusNote || t.claimSupersededNote}
                    </p>
                    <div className="mt-2 text-[11.5px] text-ink-faint">
                      {t.resolutionRecorded} {formatDate(event.updatedAt)}
                    </div>
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap items-center gap-4 text-[12px] text-ink-faint">
                  <Link
                    href={`/event/${event.id}${querySuffix}`}
                    className="font-medium text-ledger hover:underline"
                  >
                    {t.viewEventDossier}
                  </Link>
                  {claim.url && (
                    <a
                      href={claim.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-ink-soft hover:underline"
                    >
                      {t.originalLink} <ArrowUpRight className="size-3" />
                    </a>
                  )}
                  <span>
                    {t.competition} {event.competition}
                  </span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
