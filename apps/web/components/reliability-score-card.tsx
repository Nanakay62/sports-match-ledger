import Link from "next/link";
import { ArrowUpRight, Info } from "lucide-react";
import { pct, slugify } from "@/lib/format";
import type { ReliabilityScore } from "@/lib/types";
import { TallyMarks } from "./tally-marks";
import { CategoryRecordRow } from "./category-record";

/** Used on the event page's "Sources on record" grid. Never a lone percentage. */
export function ReliabilityScoreCard({ score }: { score: ReliabilityScore }) {
  const href = `/reliability/${slugify(score.subjectName)}`;
  const insufficient = score.sampleSize < 10;

  return (
    <article className="p-4 md:p-5">
      <header className="flex items-baseline justify-between gap-3">
        <Link href={href} className="font-display text-lg font-medium hover:underline">
          {score.subjectName}
        </Link>
        <span className="rounded-[3px] border border-rule px-1.5 py-0.5 font-mono text-[9.5px] uppercase tracking-[0.12em] text-ink-faint">
          {score.subjectType}
        </span>
      </header>

      {insufficient ? (
        <div className="mt-3 rounded-[4px] border border-dashed border-rule-strong bg-paper-deep/50 p-3">
          <p className="flex gap-2 text-[13px] leading-relaxed text-ink-soft">
            <Info className="mt-0.5 size-4 shrink-0 text-ink-faint" aria-hidden />
            <span>
              <strong className="font-semibold text-ink">Insufficient record.</strong> Only{" "}
              {score.sampleSize} resolved claim{score.sampleSize === 1 ? "" : "s"} on file: scores
              publish at 10 or more.{" "}
              <span className="font-mono text-[12px]">
                {score.correctCount} / {score.sampleSize} correct so far.
              </span>
            </span>
          </p>
          <div className="mt-3">
            <TallyMarks items={score.recentResolutions} />
          </div>
        </div>
      ) : (
        <>
          <div className="mt-3 flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <span className="font-mono text-[28px] font-medium leading-none tracking-tight tabular-nums">
              {score.correctCount}
              <span className="text-ink-faint"> / {score.sampleSize}</span>
            </span>
            <span className="text-[12.5px] text-ink-soft">claims correct</span>
            <span className="font-mono text-[11px] text-ink-faint">
              ≈ {pct(score.correctCount, score.sampleSize)}%
            </span>
          </div>
          <div className="mt-3">
            <TallyMarks items={score.recentResolutions} />
          </div>
          <div className="mt-4 border-t border-rule/70 pt-1">
            {score.scoreByCategory.map((c) => (
              <CategoryRecordRow key={c.category} record={c} />
            ))}
          </div>
        </>
      )}

      <Link
        href={href}
        className="mt-3 inline-flex items-center gap-1 text-[12px] font-semibold text-ledger hover:underline"
      >
        Full reliability profile <ArrowUpRight className="size-3" aria-hidden />
      </Link>
    </article>
  );
}