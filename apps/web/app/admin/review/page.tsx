import type { Metadata } from "next";
import Link from "next/link";
import { AlertCircle, ArrowUpRight, CheckCircle2, FileQuestion, ShieldAlert } from "lucide-react";
import { fetchAdminReviewQueue } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { ReviewActionButtons } from "@/components/review-actions";

export const metadata: Metadata = {
  title: "Human Review Queue · Editorial Control Plane",
};

export default async function AdminReviewQueuePage() {
  const queue = await fetchAdminReviewQueue();

  return (
    <div>
      <header className="border-b-2 border-ink pb-6">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-rose-600">
          <ShieldAlert className="size-3.5" />
          <span>Editorial Governance · Handbook §14</span>
        </div>
        <h1 className="mt-2 font-display text-3xl font-medium tracking-tight md:text-4xl">
          Human Review Queue
        </h1>
        <p className="mt-2 text-[14.5px] text-ink-soft">
          Mandatory editorial review for disputed claims, allegations, legal filings, and conflicting
          numerical figures before or alongside publication.
        </p>
      </header>

      <section className="mt-8" aria-label="Review items">
        <div className="flex items-baseline justify-between border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-ink-faint">
          <span>{queue.length} items awaiting editorial decision</span>
          <span>Strict audit trail</span>
        </div>

        {queue.length === 0 ? (
          <div className="py-16 text-center text-ink-faint">
            <CheckCircle2 className="mx-auto size-8 text-emerald-600 opacity-60" />
            <p className="mt-2 text-[14px]">Review queue is clear. All active claims pass deterministic thresholds.</p>
          </div>
        ) : (
          <div className="mt-4 space-y-4">
            {queue.map((item) => (
              <div
                key={item.id}
                className="border border-rule bg-paper p-5 transition-shadow hover:shadow-sm"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rule/60 pb-3">
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-2 py-0.5 font-mono text-[10.5px] font-semibold uppercase ${
                        item.priority === "critical"
                          ? "bg-rose-600 text-paper"
                          : item.priority === "high"
                          ? "bg-rose-100 text-rose-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {item.priority}
                    </span>
                    <span className="rounded bg-rule/70 px-2 py-0.5 font-mono text-[10.5px] uppercase tracking-wider text-ink-soft">
                      {item.trigger_category?.replace("_", " ")}
                    </span>
                    <span className="font-mono text-[11px] text-ink-faint">Claim № {item.id}</span>
                  </div>
                  <span className="font-mono text-[11px] text-ink-faint">
                    {formatDate(item.timestamp)}
                  </span>
                </div>

                <div className="mt-3">
                  <div className="font-mono text-[11px] uppercase tracking-wider text-rose-700 font-semibold">
                    Trigger reason: {item.flag_reason}
                  </div>
                  <p className="mt-2 font-display text-lg font-medium leading-snug">
                    "{item.claim_text}"
                  </p>
                </div>

                <div className="mt-3 grid gap-2 rounded border border-rule/70 bg-rule/20 p-3 text-[12.5px] md:grid-cols-2">
                  <div>
                    <span className="text-ink-faint">Attributed source:</span>{" "}
                    <b className="text-ink-soft">{item.reporter ? `${item.reporter} (${item.outlet})` : item.outlet}</b>
                  </div>
                  <div>
                    <span className="text-ink-faint">Parent story:</span>{" "}
                    <Link href={`/event/${item.event_id}`} className="font-medium text-ledger hover:underline">
                      {item.event_headline}
                    </Link>
                  </div>
                </div>

                {/* Editorial Actions */}
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-rule/50 pt-3">
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 font-mono text-[11.5px] text-ledger hover:underline"
                  >
                    Examine original article <ArrowUpRight className="size-3" />
                  </a>

                  <ReviewActionButtons claimId={item.id} initialStatus={item.event_status} />
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
