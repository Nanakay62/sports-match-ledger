import type { Metadata } from "next";
import { AlertOctagon, CheckCircle2, FileCode, Terminal } from "lucide-react";
import { fetchAdminDeadLetters } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { ReplayButton } from "@/components/replay-button";

export const metadata: Metadata = {
  title: "Dead-Letter Queue · Editorial Control Plane",
};

export default async function AdminDeadLettersPage() {
  const deadLetters = await fetchAdminDeadLetters();

  return (
    <div>
      <header className="border-b-2 border-ink pb-6">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-rose-600">
          <AlertOctagon className="size-3.5" />
          <span>Operational Resilience · Handbook §11.5</span>
        </div>
        <h1 className="mt-2 font-display text-3xl font-medium tracking-tight md:text-4xl">
          Dead-Letter Queue
        </h1>
        <p className="mt-2 text-[14.5px] text-ink-soft">
          Exhausted pipeline background jobs routed to the dead-letter pool after exhausting max retries.
          Inspect diagnostic error traces and replay jobs once network or upstream issues are resolved.
        </p>
      </header>

      <section className="mt-8" aria-label="Dead letter jobs">
        <div className="flex items-baseline justify-between border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-ink-faint">
          <span>{deadLetters.length} exhausted jobs</span>
          <span>Max retries: 3 cycles</span>
        </div>

        {deadLetters.length === 0 ? (
          <div className="py-16 text-center text-ink-faint">
            <CheckCircle2 className="mx-auto size-8 text-emerald-600 opacity-60" />
            <p className="mt-2 text-[14px]">Dead-letter queue is clear. No exhausted jobs on record.</p>
          </div>
        ) : (
          <div className="mt-4 space-y-4">
            {deadLetters.map((item) => (
              <div
                key={item.id}
                className="border border-rule bg-paper p-5 transition-shadow hover:shadow-sm"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rule/60 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-rose-100 px-2 py-0.5 font-mono text-[10.5px] font-semibold text-rose-800">
                      EXHAUSTED ({item.attempts} ATTEMPTS)
                    </span>
                    <span className="font-mono text-[11px] text-ink-faint">Lane: {item.lane}</span>
                    <span className="text-ink-faint">·</span>
                    <span className="font-mono text-[11px] text-ink-faint">Job: {item.job_id}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-[11px] text-ink-faint">
                      {formatDate(item.last_failed_at)}
                    </span>
                    <ReplayButton deadLetterId={item.id} isReplayed={item.replayed} />
                  </div>
                </div>

                <div className="mt-3">
                  <div className="rounded border border-rose-200 bg-rose-50/50 p-3 text-[13px] text-rose-950">
                    <div className="flex items-start gap-2">
                      <Terminal className="mt-0.5 size-4 shrink-0 text-rose-600" />
                      <div>
                        <span className="font-semibold font-mono text-[12px]">Diagnostic error: </span>
                        <span className="font-mono text-[12px]">{item.error_message}</span>
                      </div>
                    </div>
                  </div>

                  <details className="mt-3 cursor-pointer text-[12px] text-ink-soft">
                    <summary className="inline-flex items-center gap-1 font-mono text-[11.5px] text-ink-faint hover:text-ink">
                      <FileCode className="size-3" /> View Job Payload
                    </summary>
                    <pre className="mt-2 overflow-x-auto rounded bg-ink/5 p-3 font-mono text-[11px] text-ink">
                      {(() => {
                        try {
                          return JSON.stringify(JSON.parse(item.payload), null, 2);
                        } catch {
                          return item.payload;
                        }
                      })()}
                    </pre>
                  </details>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
