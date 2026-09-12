import { CircleCheck, CircleX, Info, TriangleAlert, type LucideIcon } from "lucide-react";
import type { ReasonKind, ReasoningBullet } from "@/lib/evidence";

/** Renders the **bold** markers produced by the evidence engine. */
export function RichText({ text }: { text: string }) {
  const parts = text.split(/\*\*(.+?)\*\*/g);
  return (
    <span>
      {parts.map((p, i) =>
        i % 2 === 1 ? (
          <strong key={i} className="font-semibold text-ink">
            {p}
          </strong>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </span>
  );
}

const REASON_ICON: Record<ReasonKind, LucideIcon> = {
  ok: CircleCheck,
  warn: TriangleAlert,
  bad: CircleX,
  info: Info,
};
const REASON_COLOR: Record<ReasonKind, string> = {
  ok: "text-confirmed",
  warn: "text-developing",
  bad: "text-disputed",
  info: "text-ink-faint",
};

export function ReasonBullet({ bullet }: { bullet: ReasoningBullet }) {
  const Icon = REASON_ICON[bullet.kind];
  return (
    <li className="flex gap-2.5 text-[14px] leading-relaxed text-ink-soft">
      <Icon className={`mt-[3px] size-4 shrink-0 ${REASON_COLOR[bullet.kind]}`} strokeWidth={2.2} aria-hidden />
      <RichText text={bullet.text} />
    </li>
  );
}