import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowUpRight, Radio } from "lucide-react";
import { StatusBadge } from "@/components/status-badge";
import { EntityChip } from "@/components/entity-chip";
import { WhyStatusPanel } from "@/components/why-status-panel";
import { ClaimTimeline } from "@/components/claim-timeline";
import { ReliabilityScoreCard } from "@/components/reliability-score-card";
import { WatchButton } from "@/components/watch-button";
import { ExportButton } from "@/components/export-button";
import { buildStatusReasoning } from "@/lib/evidence";
import { loadClaims, loadEvent, loadRelatedEvents, reliabilityByName } from "@/lib/data-loader";
import { entryNo, formatDate, leadTime, slugify, timeAgo } from "@/lib/format";
import { getDictionary } from "@/lib/i18n";
import type { ReliabilityScore } from "@/lib/types";

export async function generateMetadata({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ lang?: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const sParams = searchParams ? await searchParams : undefined;
  const lang = sParams?.lang || "en";
  const event = await loadEvent(id, lang);
  return { title: event ? event.headline : "Entry not found" };
}

export default async function EventPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ lang?: string }>;
}) {
  const { id } = await params;
  const sParams = searchParams ? await searchParams : undefined;
  const lang = sParams?.lang || "en";
  const t = getDictionary(lang);
  const querySuffix = lang !== "en" ? `?lang=${lang}` : "";

  const event = await loadEvent(id, lang);
  if (!event) notFound();

  const claims = await loadClaims(event.id, lang);
  const reasoning = buildStatusReasoning(event, claims);
  const original = claims.find((c) => c.attribution === "original");
  const sourceOutlet = original?.outlet ?? event.firstReportedBy?.outlet ?? "Unattributed";
  const related = await loadRelatedEvents(event.id);

  const outletNames = [...new Set(claims.map((c) => c.outlet))];
  const reporterNames = [
    ...new Set(
      claims
        .map((c) => c.reporter)
        .filter((r): r is string => !!r && reliabilityByName.has(r)),
    ),
  ];
  const subjects = [...outletNames, ...reporterNames]
    .map((n) => reliabilityByName.get(n))
    .filter((s): s is ReliabilityScore => !!s);

  const first = event.firstReportedBy;

  return (
    <main className="mx-auto max-w-4xl px-4 pb-20 md:px-6">
      <nav className="pt-6 font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink-faint" aria-label="Breadcrumb">
        <Link href={`/${querySuffix}`} className="hover:text-ink">{t.navLedger}</Link>
        <span className="mx-1.5">/</span>
        <span>{event.competition}</span>
        {event.entities[0] && (
          <>
            <span className="mx-1.5">/</span>
            <Link href={`/topic/${slugify(event.entities[0].name)}${querySuffix}`} className="hover:text-ink">
              {event.entities[0].name}
            </Link>
          </>
        )}
      </nav>

      <article>
        <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-3">
          <StatusBadge status={event.status} size="stamp" />
          <div className="font-mono text-[12px] text-ink-faint">
            Entry № {entryNo(event.id)} · Updated <span suppressHydrationWarning>{timeAgo(event.updatedAt)}</span>
          </div>
        </div>

        {event.statusNote && (
          <p className="mt-4 max-w-2xl border-l-2 border-corrected pl-3 text-[13px] leading-relaxed text-ink-soft">
            {event.statusNote}
          </p>
        )}

        {event.isTranslated && (
          <div className="mt-3 flex flex-wrap items-center gap-2 rounded border border-amber-200 bg-amber-50 px-2.5 py-1 font-mono text-[11px] text-amber-800">
            <span>Translated ({lang.toUpperCase()})</span>
            {event.originalHeadline && (
              <span className="text-ink-faint">· Original: "{event.originalHeadline}"</span>
            )}
          </div>
        )}

        <h1 className="mt-4 max-w-3xl font-display text-[2rem] font-medium leading-[1.06] tracking-tight md:text-[2.75rem]">
          {event.headline}
        </h1>
        <p className="mt-4 max-w-2xl text-[16px] leading-relaxed text-ink-soft">{event.summary}</p>

        <div className="mt-5 flex flex-wrap gap-1.5">
          {event.entities.map((e) => (
            <EntityChip key={e.name} entity={e} />
          ))}
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <WatchButton eventId={event.id} querySuffix={querySuffix} />
          <ExportButton eventId={event.id} label="Export CSV" querySuffix={querySuffix} />

          <Link
            href={`/rumour/${event.id}${querySuffix}`}
            className="inline-flex items-center gap-1.5 rounded border border-rule px-2.5 py-1 font-mono text-[11px] text-ink-soft hover:border-ink hover:text-ink"
          >
            <Radio className="size-3 text-ledger" />
            <span>View Rumour Trajectory</span>
          </Link>
        </div>

        {/* Evidence strip: ruled cells, not floating cards */}
        <dl className="mt-8 grid grid-cols-2 gap-px border border-rule bg-rule md:grid-cols-4">
          <div className="bg-paper p-4">
            <dt className="text-[10px] uppercase tracking-[0.14em] text-ink-faint">{t.independentSources}</dt>
            <dd className="mt-1 font-mono text-2xl font-medium tabular-nums">{event.independentSources}</dd>
          </div>
          <div className="bg-paper p-4">
            <dt className="text-[10px] uppercase tracking-[0.14em] text-ink-faint">{t.firstReportedBy}</dt>
            <dd className="mt-1 text-[13.5px] font-medium">
              {first ? (
                <>
                  {first.outlet}
                  {first.leadTimeMinutes > 0 && (
                    <span className="mt-0.5 block font-mono text-[11px] font-normal text-ink-faint">
                      {leadTime(first.leadTimeMinutes)} {t.leadTime}
                    </span>
                  )}
                </>
              ) : (
                <span className="text-[13px] font-normal text-ink-faint">Not on record</span>
              )}
            </dd>
          </div>
          <div className="bg-paper p-4">
            <dt className="text-[10px] uppercase tracking-[0.14em] text-ink-faint">Original source</dt>
            <dd className="mt-1">
              <a
                href={event.sourceUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-[13.5px] font-medium text-ledger hover:underline"
              >
                {sourceOutlet} <ArrowUpRight className="size-3" aria-hidden />
              </a>
              {original && (
                <span className="mt-0.5 block font-mono text-[11px] text-ink-faint">
                  {formatDate(original.timestamp)}
                </span>
              )}
            </dd>
          </div>
          <div className="bg-paper p-4">
            <dt className="text-[10px] uppercase tracking-[0.14em] text-ink-faint">Last updated</dt>
            <dd className="mt-1 font-mono text-lg font-medium">
              <span suppressHydrationWarning>{timeAgo(event.updatedAt)}</span>
            </dd>
          </div>
        </dl>

        <WhyStatusPanel event={event} reasoning={reasoning} />

        <section className="mt-12" aria-label="Claim ledger">
          <div className="flex flex-wrap items-baseline justify-between gap-2 border-b-2 border-ink pb-1.5">
            <h2 className="font-display text-xl font-medium">{t.claimTimeline}</h2>
            <span className="font-mono text-[11px] text-ink-faint">
              {claims.length} {claims.length === 1 ? "entry" : "entries"} · newest first
            </span>
          </div>
          <div className="mt-1">
            <ClaimTimeline claims={claims} eventId={event.id} querySuffix={querySuffix} />
          </div>
        </section>

        <section className="mt-12" aria-label="Sources on record">
          <div className="border-b-2 border-ink pb-1.5">
            <h2 className="font-display text-xl font-medium">Sources on record</h2>
          </div>
          <p className="mt-2 text-[12.5px] text-ink-faint">
            Every desk and byline on this story, scored in public. Fractions are resolved claims
            correct; below 10 resolved claims we show an insufficient-record notice instead of a score.
          </p>
          <div className="mt-4 grid gap-px border border-rule bg-rule md:grid-cols-2">
            {subjects.map((s) => (
              <div key={s.subjectName} className="bg-paper">
                <ReliabilityScoreCard score={s} />
              </div>
            ))}
          </div>
        </section>

        {related.length > 0 && (
          <section className="mt-12" aria-label="Related entries">
            <div className="border-b-2 border-ink pb-1.5">
              <h2 className="font-display text-xl font-medium">{t.relatedEvents}</h2>
            </div>
            <ul className="divide-y divide-rule/70">
              {related.map((r) => (
                <li key={r.id} className="py-3.5">
                  <div className="flex items-center justify-between gap-4">
                    <Link
                      href={`/event/${r.id}${querySuffix}`}
                      className="flex-1 font-display text-[15.5px] font-medium leading-snug hover:underline"
                    >
                      {r.headline}
                    </Link>
                    <StatusBadge status={r.status} />
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-x-3 text-[12px] text-ink-faint">
                    <a
                      href={r.sourceUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-0.5 font-medium text-ledger hover:underline"
                    >
                      Source <ArrowUpRight className="size-3" aria-hidden />
                    </a>
                    {r.firstReportedBy && (
                      <span>
                        First: <b className="text-ink-soft">{r.firstReportedBy.outlet}</b>
                      </span>
                    )}
                    <span>{r.independentSources} sources</span>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}
      </article>
    </main>
  );
}