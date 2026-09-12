"use client";

import { useMemo, useState } from "react";
import { STATUS_LABEL, STATUS_ORDER } from "@/lib/status";
import type { Event, EventStatus } from "@/lib/types";
import type { ReasoningBullet } from "@/lib/evidence";
import { LedgerRowItem } from "./event-ledger-row";

export interface FeedItem {
  event: Event;
  reasoning: ReasoningBullet[];
}

export function TopicFeed({ items }: { items: FeedItem[] }) {
  const [filter, setFilter] = useState<"all" | EventStatus>("all");

  const counts = useMemo(() => {
    const c = Object.fromEntries(STATUS_ORDER.map((s) => [s, 0])) as Record<EventStatus, number>;
    for (const i of items) c[i.event.status]++;
    return c;
  }, [items]);

  const filtered = filter === "all" ? items : items.filter((i) => i.event.status === filter);

  const btn = (active: boolean) =>
    `rounded-[3px] border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.07em] transition-colors ${
      active
        ? "border-ink bg-ink text-paper"
        : "border-rule-strong text-ink-soft hover:border-ink hover:text-ink"
    }`;

  return (
    <div>
      <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter by status">
        <button type="button" onClick={() => setFilter("all")} className={btn(filter === "all")}>
          All <span className="font-mono opacity-70">{items.length}</span>
        </button>
        {STATUS_ORDER.filter((s) => counts[s] > 0).map((s) => (
          <button key={s} type="button" onClick={() => setFilter(s)} className={btn(filter === s)}>
            {STATUS_LABEL[s]} <span className="font-mono opacity-70">{counts[s]}</span>
          </button>
        ))}
      </div>
      <ol className="mt-2">
        {filtered.map((i) => (
          <LedgerRowItem key={i.event.id} event={i.event} reasoning={i.reasoning} />
        ))}
      </ol>
    </div>
  );
}