import Link from "next/link";
import { pct, slugify } from "@/lib/format";
import { reliabilityByName } from "@/lib/mock-data";

/**
 * Compact inline score. ALWAYS a fraction with its sample size, never a lone
 * percentage, and always the "insufficient record" state below 10 resolved claims.
 */
export function ReliabilityPill({ name }: { name: string }) {
  const s = reliabilityByName.get(name);
  if (!s) return null;
  const href = `/reliability/${slugify(s.subjectName)}`;

  if (s.sampleSize < 10) {
    return (
      <Link
        href={href}
        title={`${name}: insufficient record: only ${s.sampleSize} resolved claims on file`}
        className="inline-flex items-center gap-1 whitespace-nowrap rounded-[3px] border border-dashed border-rule-strong bg-paper-deep px-1.5 py-0.5 font-mono text-[10.5px] text-ink-faint hover:text-ink"
      >
        Insufficient record · {s.correctCount}/{s.sampleSize}
      </Link>
    );
  }

  const p = pct(s.correctCount, s.sampleSize);
  const tone =
    p >= 75
      ? "border-confirmed/40 bg-confirmed/[0.06] text-confirmed hover:bg-confirmed/[0.12]"
      : p >= 50
        ? "border-developing/40 bg-developing/[0.07] text-developing hover:bg-developing/[0.14]"
        : "border-disputed/40 bg-disputed/[0.06] text-disputed hover:bg-disputed/[0.12]";

  return (
    <Link
      href={href}
      title={`${name}: ${s.correctCount} of ${s.sampleSize} resolved claims correct`}
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-[3px] border px-1.5 py-0.5 font-mono text-[10.5px] ${tone}`}
    >
      {s.correctCount} / {s.sampleSize}
    </Link>
  );
}