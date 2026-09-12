import type { ClaimResolution } from "@/lib/types";

export function TallyMarks({ items }: { items: ClaimResolution[] }) {
  const groups: ClaimResolution[][] = [];
  for (let i = 0; i < items.length; i += 5) groups.push(items.slice(i, i + 5));
  const correct = items.filter((i) => i.outcome === "correct").length;

  return (
    <div
      className="flex flex-wrap items-end gap-x-5 gap-y-3"
      role="img"
      aria-label={`${correct} correct, ${items.length - correct} incorrect, shown as tally marks`}
    >
      {groups.map((g, gi) => (
        <div key={gi} className="relative flex items-stretch gap-[3px] self-stretch" style={{ height: 18 }}>
          {g.map((it, ii) => (
            <span
              key={ii}
              title={`${it.claim}: ${it.outcome}`}
              className={`w-[2.5px] rounded-[1px] ${it.outcome === "correct" ? "bg-confirmed" : "bg-disputed"}`}
            />
          ))}
          {g.length === 5 && (
            <span
              aria-hidden
              className="absolute -left-1 -right-1 top-1/2 h-[2px] -translate-y-1/2 -rotate-[22deg] rounded bg-ink/70"
            />
          )}
        </div>
      ))}
    </div>
  );
}