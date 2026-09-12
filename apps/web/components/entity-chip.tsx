import Link from "next/link";
import { Shield, User } from "lucide-react";
import { slugify } from "@/lib/format";
import type { EventEntity } from "@/lib/types";

export function EntityChip({ entity }: { entity: EventEntity }) {
  const Icon = entity.type === "club" ? Shield : User;
  return (
    <Link
      href={`/topic/${slugify(entity.name)}`}
      className="inline-flex items-center gap-1.5 rounded-[3px] border border-rule-strong/80 bg-paper px-2 py-[3px] text-[11.5px] text-ink-soft transition-colors hover:border-ink hover:text-ink"
    >
      <Icon className="size-3" aria-hidden />
      <span className="font-medium">{entity.name}</span>
      <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-ink-faint">
        {entity.type}
      </span>
    </Link>
  );
}