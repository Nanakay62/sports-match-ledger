import { notFound } from "next/navigation";
import { Award, ExternalLink, HelpCircle, ShieldCheck } from "lucide-react";
import { fetchReliabilityScore } from "@/lib/api";
import { pct, slugify } from "@/lib/format";

export const dynamic = "force-dynamic";

interface EmbedReliabilityPageProps {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ theme?: string }>;
}

export default async function EmbedReliabilityPage({
  params,
  searchParams,
}: EmbedReliabilityPageProps) {
  const { slug } = await params;
  const { theme } = await searchParams;
  const isDark = theme === "dark";

  const score = await fetchReliabilityScore(slug);
  if (!score) {
    notFound();
  }

  const publicAppUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
  const methodologyUrl = `${publicAppUrl}/methodology`;
  const subjectSlug = slugify(score.subjectName);
  const profileUrl = `${publicAppUrl}/reliability/${subjectSlug}`;

  const hasSufficientRecord = score.sampleSize >= 10;
  const scorePercent = pct(score.correctCount, score.sampleSize);

  return (
    <div
      className={`max-w-sm rounded-md border p-4 shadow-sm font-sans transition-colors ${
        isDark
          ? "border-neutral-800 bg-neutral-900 text-neutral-100"
          : "border-rule bg-paper text-ink"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-rule/50 pb-2">
        <div className="flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
          <ShieldCheck className="size-3.5" />
          <span>Reliability Ledger</span>
        </div>
        <span
          className={`rounded px-1.5 py-0.5 font-mono text-[10px] uppercase ${
            isDark ? "bg-neutral-800 text-neutral-300" : "bg-stone-100 text-ink-soft"
          }`}
        >
          {score.subjectType}
        </span>
      </div>

      {/* Subject Name & Primary Score */}
      <div className="mt-3 flex items-center justify-between gap-2">
        <div>
          <a
            href={profileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="group block"
          >
            <h2
              className={`font-display text-base font-semibold group-hover:underline ${
                isDark ? "text-neutral-100" : "text-ink"
              }`}
            >
              {score.subjectName}
            </h2>
          </a>
          {score.affiliation && (
            <p
              className={`text-[12px] ${
                isDark ? "text-neutral-400" : "text-ink-soft"
              }`}
            >
              {score.affiliation}
            </p>
          )}
        </div>

        <div className="text-right">
          {hasSufficientRecord ? (
            <div>
              <div className="font-display text-2xl font-bold tracking-tight text-emerald-700 dark:text-emerald-400">
                {scorePercent}%
              </div>
              <div
                className={`font-mono text-[9px] uppercase tracking-wider ${
                  isDark ? "text-neutral-400" : "text-ink-faint"
                }`}
              >
                Wilson Lower Bound
              </div>
            </div>
          ) : (
            <div
              className={`rounded border px-2 py-1 text-center font-mono text-[10px] ${
                isDark
                  ? "border-neutral-700 bg-neutral-800 text-neutral-300"
                  : "border-amber-200 bg-amber-50 text-amber-900"
              }`}
            >
              <HelpCircle className="mx-auto size-3 mb-0.5 text-amber-600" />
              <span>Record &lt; 10 claims</span>
            </div>
          )}
        </div>
      </div>

      {/* Breakdown Metrics */}
      <div className="mt-3 grid grid-cols-2 gap-2 border-t border-rule/50 pt-2.5 font-mono text-[11px]">
        <div>
          <span className={isDark ? "text-neutral-400" : "text-ink-faint"}>
            Resolved:{" "}
          </span>
          <strong>
            {score.correctCount}/{score.sampleSize}
          </strong>
        </div>
        <div>
          <span className={isDark ? "text-neutral-400" : "text-ink-faint"}>
            Categories:{" "}
          </span>
          <strong>{score.scoreByCategory.length} beats</strong>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-3 flex items-center justify-between border-t border-rule/50 pt-2 font-mono text-[10px]">
        <a
          href={methodologyUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-ink-soft hover:text-ink dark:text-neutral-400 dark:hover:text-neutral-200"
        >
          <Award className="size-3 text-ink-faint" />
          <span>v1.2.0 Methodology</span>
          <ExternalLink className="size-2.5 opacity-60" />
        </a>
        <span className={isDark ? "text-neutral-500" : "text-ink-faint"}>
          Sports News AI
        </span>
      </div>
    </div>
  );
}
