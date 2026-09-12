import type { Event } from "@/lib/types";
import type { ReasoningBullet } from "@/lib/evidence";
import { timeAgo } from "@/lib/format";
import { ReasonBullet } from "./why-bullet";

export function WhyStatusPanel({ event, reasoning }: { event: Event; reasoning: ReasoningBullet[] }) {
  return (
    <section className="mt-10 border border-ink/70 bg-paper-deep/40 p-5 md:p-6" aria-label="Why this status">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-xl italic">Why this status?</h2>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-ink-faint">
          Assigned by the ledger desk ·{" "}
          <span suppressHydrationWarning>{timeAgo(event.updatedAt)}</span>
        </span>
      </div>
      <ul className="mt-4 space-y-3">
        {reasoning.map((r, i) => (
          <ReasonBullet key={i} bullet={r} />
        ))}
      </ul>
      <p className="mt-5 border-t border-rule pt-3 text-[11.5px] leading-relaxed text-ink-faint">
        Status reflects every claim currently on record. It is never automated and never paywalled:
        only deeper history, exports and alerts are Pro.
      </p>
    </section>
  );
}