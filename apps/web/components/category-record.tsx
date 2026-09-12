import type { CategoryRecord } from "@/lib/types";
import { pct } from "@/lib/format";

export function CategoryRecordRow({ record }: { record: CategoryRecord }) {
  const percentage = pct(record.correct, record.total);

  return (
    <div className="flex items-center justify-between gap-3 border-b border-rule/50 py-2 text-[13px] last:border-b-0">
      <span className="truncate text-ink-soft">{record.category}</span>
      <div className="flex items-center gap-2.5 font-mono text-[11.5px]">
        <span className="tabular-nums font-medium text-ink">
          {record.correct} <span className="text-ink-faint">/ {record.total}</span>
        </span>
        <span className="w-10 text-right text-[10.5px] text-ink-faint">
          {percentage}%
        </span>
      </div>
    </div>
  );
}
