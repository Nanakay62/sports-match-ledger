import { cn } from "@/lib/utils";
import { STATUS_ICON, STATUS_LABEL, STATUS_STYLE } from "@/lib/status";
import type { EventStatus } from "@/lib/types";

/**
 * The only way a status is ever rendered: exact plain-language label + icon.
 * Chip = feed rows; Stamp = lead story & event hero (the "rubber stamp").
 */
export function StatusBadge({
  status,
  size = "chip",
  className,
}: {
  status: EventStatus;
  size?: "chip" | "stamp";
  className?: string;
}) {
  const Icon = STATUS_ICON[status];
  const style = STATUS_STYLE[status];
  if (size === "stamp") {
    return (
      <span
        className={cn(
          "stamp-in -rotate-1 inline-flex items-center gap-2 rounded-[2px] border-4 border-double px-4 py-2",
          "font-mono text-[13px] font-semibold uppercase tracking-[0.18em] md:text-sm",
          style,
          className,
        )}
      >
        <Icon className="size-4" strokeWidth={2.4} aria-hidden />
        {STATUS_LABEL[status]}
      </span>
    );
  }
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-[3px] border px-2 py-[3px]",
        "text-[10.5px] font-semibold uppercase tracking-[0.09em]",
        style,
        className,
      )}
    >
      <Icon className="size-3" strokeWidth={2.6} aria-hidden />
      {STATUS_LABEL[status]}
    </span>
  );
}