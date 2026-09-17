import type { Metadata } from "next";
import { AlertTriangle, ArrowUpRight, CheckCircle2, FileText, ShieldAlert } from "lucide-react";
import { fetchAdminQuarantine } from "@/lib/api";
import { formatDate } from "@/lib/format";

export const metadata: Metadata = {
  title: "Quarantine Pool · Editorial Control Plane",
};

export default async function AdminQuarantinePage() {
  const quarantined = await fetchAdminQuarantine();

  return (
    <div>
      <header className="border-b-2 border-ink pb-6">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-amber-700">
          <ShieldAlert className="size-3.5" />
          <span>Ingestion Quality Gate · Handbook §11.4</span>
        </div>
        <h1 className="mt-2 font-display text-3xl font-medium tracking-tight md:text-4xl">
          Quarantine Pool
        </h1>
        <p className="mt-2 text-[14.5px] text-ink-soft">
          Raw payloads and articles diverted prior to ledger entry due to low extraction confidence
          (&lt;0.50), truncated bodies, or paywall boilerplate. Quarantined records never pollute the Accountability Ledger.
        </p>
      </header>

      <section className="mt-8" aria-label="Quarantined documents">
        <div className="flex items-baseline justify-between border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-ink-faint">
          <span>{quarantined.length} documents quarantined</span>
          <span>Quality Threshold: &ge; 0.50</span>
        </div>

        {quarantined.length === 0 ? (
          <div className="py-16 text-center text-ink-faint">
            <CheckCircle2 className="mx-auto size-8 text-emerald-600 opacity-60" />
            <p className="mt-2 text-[14px]">Quarantine pool is clear. Ingestion payloads meet quality standards.</p>
          </div>
        ) : (
          <div className="mt-4 space-y-4">
            {quarantined.map((item) => {
              const confidencePct = Math.round(item.confidence_score * 100);
              const isVeryLow = item.confidence_score < 0.35;

              return (
                <div
                  key={item.id}
                  className="border border-rule bg-paper p-5 transition-shadow hover:shadow-sm"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rule/60 pb-3">
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded px-2 py-0.5 font-mono text-[10.5px] font-semibold ${
                          isVeryLow ? "bg-rose-100 text-rose-800" : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        CONFIDENCE: {confidencePct}%
                      </span>
                      <span className="font-mono text-[11px] text-ink-faint">Doc № {item.id}</span>
                    </div>
                    <span className="font-mono text-[11px] text-ink-faint">
                      {formatDate(item.created_at)}
                    </span>
                  </div>

                  <div className="mt-3">
                    <div className="flex items-center gap-2 text-[14px]">
                      <span className="font-semibold text-ink">{item.source_name}</span>
                      <span className="text-ink-faint">·</span>
                      <a
                        href={item.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 font-mono text-[12px] text-ink-soft hover:text-ink hover:underline"
                      >
                        Source URL <ArrowUpRight className="size-3" />
                      </a>
                    </div>

                    <div className="mt-2.5 rounded border border-amber-200 bg-amber-50/50 p-3 text-[13px] text-amber-900">
                      <div className="flex items-start gap-2">
                        <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" />
                        <div>
                          <span className="font-semibold">Rejection reason: </span>
                          <span>{item.rejection_reason}</span>
                        </div>
                      </div>
                    </div>

                    <details className="mt-3 cursor-pointer text-[12px] text-ink-soft">
                      <summary className="inline-flex items-center gap-1 font-mono text-[11.5px] text-ink-faint hover:text-ink">
                        <FileText className="size-3" /> View Raw Ingest Payload
                      </summary>
                      <pre className="mt-2 overflow-x-auto rounded bg-ink/5 p-3 font-mono text-[11px] text-ink">
                        {(() => {
                          try {
                            return JSON.stringify(JSON.parse(item.raw_payload), null, 2);
                          } catch {
                            return item.raw_payload;
                          }
                        })()}
                      </pre>
                    </details>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
