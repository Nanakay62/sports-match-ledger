"use client";

import Link from "next/link";
import { pct, slugify } from "@/lib/format";
import { FREE_REPORTER_INDEX_LIMIT, useEntitlements } from "@/lib/entitlements";
import { PaywallWall } from "./paywall-wall";

interface ReporterRow {
  subjectName: string;
  sampleSize: number;
  correctCount: number;
  affiliation?: string;
  beat?: string;
  totalClaims?: number;
}

const LABELS = {
  colName: "Reporter",
  colResolved: "Resolved",
  colConfirmed: "Confirmed",
  colCorrected: "Corrected",
  colScore: "Score",
};

/** Handbook §2.1: reporter-level reliability is "Top 20 only" free, "all tracked reporters" on Pro. */
export function ReportersTable({ reporters, querySuffix = "" }: { reporters: ReporterRow[]; querySuffix?: string }) {
  const { isPro, email, loading } = useEntitlements();

  const visible = isPro || loading ? reporters : reporters.slice(0, FREE_REPORTER_INDEX_LIMIT);
  const hiddenCount = isPro || loading ? 0 : Math.max(0, reporters.length - FREE_REPORTER_INDEX_LIMIT);

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-[13px]">
          <thead>
            <tr className="border-b border-ink font-mono text-[10.5px] uppercase tracking-[0.12em] text-ink-faint">
              <th className="pb-2.5 pt-1 font-medium">{LABELS.colName}</th>
              <th className="pb-2.5 pt-1 font-medium">Affiliation / Beat</th>
              <th className="pb-2.5 pt-1 text-center font-medium">{LABELS.colResolved}</th>
              <th className="pb-2.5 pt-1 text-center font-medium">{LABELS.colConfirmed}</th>
              <th className="pb-2.5 pt-1 text-center font-medium">{LABELS.colCorrected}</th>
              <th className="pb-2.5 pt-1 text-right font-medium">{LABELS.colScore}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-rule">
            {visible.map((item) => {
              const total = item.totalClaims ?? item.sampleSize;
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
                        <span className="text-[10px] font-normal text-ink-faint">(LB {Math.round((correct / total) * 88)}%)</span>
                      </div>
                    ) : (
                      <span className="font-mono text-[11px] italic text-ink-faint">Pending ({total}/10)</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {hiddenCount > 0 && (
        <PaywallWall
          wallId="reporter_index"
          email={email}
          querySuffix={querySuffix}
          title={`${hiddenCount} more tracked ${hiddenCount === 1 ? "reporter" : "reporters"}`}
          description={`The free leaderboard shows the top ${FREE_REPORTER_INDEX_LIMIT} reporters by resolved claim volume. Pro sees every tracked reporter, ranked.`}
        />
      )}
    </div>
  );
}
