import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Info } from "lucide-react";
import { TallyMarks } from "@/components/tally-marks";
import { CategoryRecordRow } from "@/components/category-record";
import { SubjectClaimHistory } from "@/components/subject-claim-history";
import {
  loadReliabilityScore,
  loadSubjectClaimsAndEvents,
  localizeClaim,
  localizeEvent,
  reliabilityByName,
} from "@/lib/data-loader";
import { pct, slugify } from "@/lib/format";
import { getDictionary } from "@/lib/i18n";
import type { Claim, Event } from "@/lib/types";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ subject: string }>;
}): Promise<Metadata> {
  const { subject } = await params;
  const score = await loadReliabilityScore(subject);
  return { title: score ? `${score.subjectName}: reliability` : "Not on record" };
}

export default async function ReliabilityPage({
  params,
  searchParams,
}: {
  params: Promise<{ subject: string }>;
  searchParams?: Promise<{ lang?: string }>;
}) {
  const { subject } = await params;
  const sParams = searchParams ? await searchParams : undefined;
  const lang = sParams?.lang || "en";
  const t = getDictionary(lang);
  const querySuffix = lang !== "en" ? `?lang=${lang}` : "";

  const score = await loadReliabilityScore(subject);
  if (!score) notFound();

  const isOutlet = score.subjectType === "outlet";
  const insufficient = score.sampleSize < 10;
  const p = pct(score.correctCount, score.sampleSize);

  // Every entry in the ledger this subject touched from the database
  const unlocalizedRows: { claim: Claim; event: Event }[] = await loadSubjectClaimsAndEvents(subject);
  const rows = unlocalizedRows.map(({ claim, event }) => ({
    claim: localizeClaim(claim, lang),
    event: localizeEvent(event, lang),
  }));

  return (
    <main className="mx-auto max-w-4xl px-4 pb-20 md:px-6">
      <nav className="pt-6 font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink-faint" aria-label="Breadcrumb">
        <Link href={`/${querySuffix}`} className="hover:text-ink">{t.navLedger}</Link>
        <span className="mx-1.5">/</span>
        <Link href={`/reliability${querySuffix}`} className="hover:text-ink">{t.navReliability}</Link>
        <span className="mx-1.5">/</span>
        <span>{score.subjectName}</span>
      </nav>

      <header className="mt-6">
        <div className="flex flex-wrap items-baseline gap-2">
          <span className="rounded-[3px] border border-rule-strong px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-[0.14em] text-ink-faint">
            {score.subjectType}
          </span>
          {!isOutlet && score.affiliation && (
            <span className="text-[12px] text-ink-faint">
              ·{" "}
              {reliabilityByName.has(score.affiliation) ? (
                <Link
                  href={`/reliability/${slugify(score.affiliation)}${querySuffix}`}
                  className="underline decoration-rule-strong underline-offset-2 hover:text-ink"
                >
                  {score.affiliation}
                </Link>
              ) : (
                score.affiliation
              )}
              {score.beat ? ` (${score.beat})` : ""}
            </span>
          )}
        </div>
        <h1 className="mt-2 font-display text-4xl font-medium tracking-tight">{score.subjectName}</h1>
        <p className="mt-2 max-w-2xl text-[14.5px] leading-relaxed text-ink-soft">
          Every resolved claim published under this {isOutlet ? "masthead" : "byline"}, marked
          against the recorded outcome.
        </p>
      </header>

      {/* Scorecard hero */}
      {insufficient ? (
        <div className="mt-8 border-2 border-dashed border-rule-strong bg-paper-deep/50 p-6">
          <div className="flex gap-3">
            <Info className="mt-1 size-5 shrink-0 text-ink-faint" aria-hidden />
            <div>
              <h2 className="font-display text-xl font-medium">Insufficient record</h2>
              <p className="mt-1.5 max-w-xl text-[14px] leading-relaxed text-ink-soft">
                Only <b className="font-mono">{score.sampleSize}</b> resolved claim
                {score.sampleSize === 1 ? "" : "s"} on file ({rows.length} total claims recorded). Matchday Ledger publishes scores only
                at <b>10+</b> resolved claims, so no rating is shown: the counts below are the
                complete record.
              </p>
              <div className="mt-4 font-mono text-2xl font-medium tabular-nums">
                {score.correctCount} / {score.sampleSize}
                <span className="ml-2 font-sans text-[12px] font-normal text-ink-faint">
                  resolved so far
                </span>
              </div>
              {score.recentResolutions.length > 0 && (
                <div className="mt-3">
                  <TallyMarks items={score.recentResolutions} />
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-8 grid items-center gap-8 border-y-2 border-ink py-6 md:grid-cols-[auto_1fr]">
          <div>
            <div className="font-mono text-[44px] font-medium leading-none tracking-tight tabular-nums">
              {score.correctCount}
              <span className="text-ink-faint"> / {score.sampleSize}</span>
            </div>
            <div className="mt-2 flex items-center gap-2 text-[13px] text-ink-soft">
              <span>claims correct</span>
              <span className="font-mono text-[11px] text-ink-faint">≈ {p}%</span>
            </div>
          </div>
          <div>
            <div className="mb-2.5 text-[10.5px] uppercase tracking-[0.14em] text-ink-faint">
              Last {score.recentResolutions.length} resolutions
            </div>
            <TallyMarks items={score.recentResolutions} />
          </div>
        </div>
      )}

      {/* Record by category */}
      {score.scoreByCategory.length > 0 && (
        <section className="mt-12" aria-label="Record by category">
          <h2 className="border-b-2 border-ink pb-1.5 font-display text-xl font-medium">Record by category</h2>
          <div className="mt-1">
            {score.scoreByCategory.map((c) => (
              <CategoryRecordRow key={c.category} record={c} />
            ))}
          </div>
        </section>
      )}

      {/* Full chronological audit log */}
      <section className="mt-12" aria-label="All claims on record">
        <div className="flex items-baseline justify-between border-b-2 border-ink pb-1.5">
          <h2 className="font-display text-xl font-medium">Claims on record</h2>
          <span className="font-mono text-[11px] text-ink-faint">
            {rows.length} {rows.length === 1 ? "entry" : "entries"} · newest first
          </span>
        </div>

        <SubjectClaimHistory rows={rows} recentResolutions={score.recentResolutions} subjectSlug={subject} querySuffix={querySuffix} />
      </section>
    </main>
  );
}
