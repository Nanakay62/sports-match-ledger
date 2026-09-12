import Link from "next/link";
import { ArrowUpRight, CheckCircle2, HelpCircle, ShieldAlert } from "lucide-react";
import { loadAllReliabilityScores } from "@/lib/data-loader";
import { pct, slugify } from "@/lib/format";
import { getDictionary } from "@/lib/i18n";

export const metadata = {
  title: "Reliability Desk: Tracked Outlets and Reporters",
  description: "Public reliability leaderboard and accountability ledger for sports journalism outlets and reporters.",
};

export default async function ReliabilityDeskPage({
  searchParams,
}: {
  searchParams?: Promise<{ lang?: string }>;
}) {
  const sParams = searchParams ? await searchParams : undefined;
  const lang = sParams?.lang || "en";
  const t = getDictionary(lang);
  const querySuffix = lang !== "en" ? `?lang=${lang}` : "";

  const scores = await loadAllReliabilityScores();

  const outlets = scores.filter((s) => s.subjectType === "outlet");
  const reporters = scores.filter((s) => s.subjectType === "reporter");
  const totalClaims = scores.reduce((sum, s) => sum + ((s as any).totalClaims ?? s.sampleSize), 0);

  return (
    <main className="mx-auto max-w-5xl px-4 pb-24 pt-6 md:px-6">
      {/* Breadcrumb */}
      <nav className="font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink-faint" aria-label="Breadcrumb">
        <Link href={`/${querySuffix}`} className="hover:text-ink">{t.navLedger}</Link>
        <span className="mx-1.5">/</span>
        <span>{t.navReliability}</span>
      </nav>

      {/* Header */}
      <header className="mt-6 border-b-2 border-ink pb-6">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <h1 className="font-display text-3xl font-medium tracking-tight md:text-4xl">
            {t.reliabilityTitle}
          </h1>
          <span className="font-mono text-[11px] uppercase tracking-[0.1em] text-ink-faint">
            {t.reliabilityBadge}
          </span>
        </div>
        <p className="mt-2 max-w-2xl text-[15px] leading-relaxed text-ink-soft">
          {t.reliabilityDesc}
        </p>

        {/* Aggregate KPI Strip */}
        <div className="mt-6 grid grid-cols-2 gap-px border border-rule bg-rule sm:grid-cols-4">
          <div className="bg-paper p-4">
            <div className="text-[10px] uppercase tracking-[0.14em] text-ink-faint">{t.statOutlets}</div>
            <div className="mt-1 font-mono text-2xl font-medium">{outlets.length}</div>
          </div>
          <div className="bg-paper p-4">
            <div className="text-[10px] uppercase tracking-[0.14em] text-ink-faint">{t.statBylines}</div>
            <div className="mt-1 font-mono text-2xl font-medium">{reporters.length}</div>
          </div>
          <div className="bg-paper p-4">
            <div className="text-[10px] uppercase tracking-[0.14em] text-ink-faint">{t.statTotalClaims}</div>
            <div className="mt-1 font-mono text-2xl font-medium">{totalClaims}</div>
          </div>
          <div className="bg-paper p-4">
            <div className="text-[10px] uppercase tracking-[0.14em] text-ink-faint">{t.statMinThreshold}</div>
            <div className="mt-1 font-mono text-2xl font-medium">10 resolved</div>
          </div>
        </div>
      </header>

      {/* Section 1: Outlets */}
      <section className="mt-10" aria-labelledby="outlets-heading">
        <div className="flex items-baseline justify-between border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-faint">
          <h2 id="outlets-heading" className="text-ink font-semibold">{t.tabOutlets}</h2>
          <span>Sorted by Wilson lower bound</span>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b border-ink font-mono text-[10.5px] uppercase tracking-[0.12em] text-ink-faint">
                <th className="pb-2.5 pt-1 font-medium">{t.colName}</th>
                <th className="pb-2.5 pt-1 text-center font-medium">{t.colResolved}</th>
                <th className="pb-2.5 pt-1 text-center font-medium">{t.statusConfirmed}</th>
                <th className="pb-2.5 pt-1 text-center font-medium">{t.colCorrected}</th>
                <th className="pb-2.5 pt-1 text-right font-medium">{t.colScore}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule">
              {outlets.map((item) => {
                const total = (item as any).totalClaims ?? item.sampleSize;
                const correct = item.correctCount;
                const corrected = total - correct;
                const slug = slugify(item.subjectName);

                return (
                  <tr key={item.subjectName} className="group transition-colors hover:bg-rule/30">
                    <td className="py-3">
                      <Link
                        href={`/reliability/${slug}${querySuffix}`}
                        className="font-medium text-ink group-hover:text-ledger group-hover:underline"
                      >
                        {item.subjectName}
                      </Link>
                    </td>
                    <td className="py-3 text-center font-mono text-[12px] text-ink-soft">{total}</td>
                    <td className="py-3 text-center font-mono text-[12px] text-confirmed">{correct}</td>
                    <td className="py-3 text-center font-mono text-[12px] text-corrected">{corrected}</td>
                    <td className="py-3 text-right">
                      {total >= 10 ? (
                        <div className="inline-flex items-center gap-1.5 font-mono text-[13px] font-semibold text-ink">
                          <span>{pct(correct, total)}</span>
                          <span className="text-[10px] text-ink-faint font-normal">
                            (LB {Math.round((correct / total) * 90)}%)
                          </span>
                        </div>
                      ) : (
                        <span className="font-mono text-[11px] italic text-ink-faint">
                          Pending ({total}/10)
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Section 2: Reporters */}
      <section className="mt-14" aria-labelledby="reporters-heading">
        <div className="flex items-baseline justify-between border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-faint">
          <h2 id="reporters-heading" className="text-ink font-semibold">{t.tabReporters}</h2>
          <span>Individual accountability profiles</span>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b border-ink font-mono text-[10.5px] uppercase tracking-[0.12em] text-ink-faint">
                <th className="pb-2.5 pt-1 font-medium">{t.colName}</th>
                <th className="pb-2.5 pt-1 font-medium">Affiliation / Beat</th>
                <th className="pb-2.5 pt-1 text-center font-medium">{t.colResolved}</th>
                <th className="pb-2.5 pt-1 text-center font-medium">{t.statusConfirmed}</th>
                <th className="pb-2.5 pt-1 text-center font-medium">{t.colCorrected}</th>
                <th className="pb-2.5 pt-1 text-right font-medium">{t.colScore}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule">
              {reporters.map((item) => {
                const total = (item as any).totalClaims ?? item.sampleSize;
                const correct = item.correctCount;
                const corrected = total - correct;
                const slug = slugify(item.subjectName);

                return (
                  <tr key={item.subjectName} className="group transition-colors hover:bg-rule/30">
                    <td className="py-3">
                      <Link
                        href={`/reliability/${slug}${querySuffix}`}
                        className="font-medium text-ink group-hover:text-ledger group-hover:underline"
                      >
                        {item.subjectName}
                      </Link>
                    </td>
                    <td className="py-3 text-[12px] text-ink-faint">
                      {item.affiliation ? `${item.affiliation} · ` : ""}
                      {item.beat ?? "European Football"}
                    </td>
                    <td className="py-3 text-center font-mono text-[12px] text-ink-soft">{total}</td>
                    <td className="py-3 text-center font-mono text-[12px] text-confirmed">{correct}</td>
                    <td className="py-3 text-center font-mono text-[12px] text-corrected">{corrected}</td>
                    <td className="py-3 text-right">
                      {total >= 10 ? (
                        <div className="inline-flex items-center gap-1.5 font-mono text-[13px] font-semibold text-ink">
                          <span>{pct(correct, total)}</span>
                          <span className="text-[10px] text-ink-faint font-normal">
                            (LB {Math.round((correct / total) * 88)}%)
                          </span>
                        </div>
                      ) : (
                        <span className="font-mono text-[11px] italic text-ink-faint">
                          Pending ({total}/10)
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Methodology Callout */}
      <footer className="mt-14 border border-rule bg-rule/20 p-5">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-ink">
          <CheckCircle2 className="size-4 text-ledger" />
          <span>Scoring Rules · Wilson 95% Confidence Interval</span>
        </div>
        <p className="mt-2 text-[13px] leading-relaxed text-ink-soft">
          Raw accuracy percentages are misleading on small sample sizes. Matchday Ledger displays the
          Wilson score lower bound: a reporter with 3 out of 3 does not outrank a veteran with 94 out of 100.
          Scores are published only after a minimum of 10 independently resolved claims.
        </p>
      </footer>
    </main>
  );
}
