import {
  Activity, Check, CheckCheck, MessageCircle, TriangleAlert, Undo2,
  type LucideIcon,
} from "lucide-react";
import type { ClaimAttribution, EventStatus } from "./types";

/** The only six labels that may ever be rendered. Never a percentage. */
export const STATUS_LABEL: Record<EventStatus, string> = {
  confirmed: "Confirmed",
  well_corroborated: "Well corroborated",
  developing: "Developing",
  rumour: "Rumour",
  disputed: "Disputed",
  corrected: "Corrected",
};

export const STATUS_ORDER: EventStatus[] = [
  "confirmed", "well_corroborated", "developing", "rumour", "disputed", "corrected",
];

export const STATUS_STYLE: Record<EventStatus, string> = {
  confirmed: "border-confirmed/60 bg-confirmed/[0.06] text-confirmed",
  well_corroborated: "border-corroborated/60 bg-corroborated/[0.06] text-corroborated",
  developing: "border-developing/60 bg-developing/[0.07] text-developing",
  rumour: "border-dashed border-rumour/70 bg-rumour/[0.05] text-rumour",
  disputed: "border-disputed/60 bg-disputed/[0.06] text-disputed",
  corrected: "border-corrected/60 bg-corrected/[0.06] text-corrected",
};

export const STATUS_ICON: Record<EventStatus, LucideIcon> = {
  confirmed: Check,
  well_corroborated: CheckCheck,
  developing: Activity,
  rumour: MessageCircle,
  disputed: TriangleAlert,
  corrected: Undo2,
};

/** Small colored marker: always paired with a text label wherever used. */
export const STATUS_DOT: Record<EventStatus, string> = {
  confirmed: "bg-confirmed",
  well_corroborated: "bg-corroborated",
  developing: "bg-developing",
  rumour: "bg-rumour",
  disputed: "bg-disputed",
  corrected: "bg-corrected",
};

export const ATTRIBUTION_STYLE: Record<
  ClaimAttribution,
  { label: string; badge: string; marker: string }
> = {
  original:      { label: "Original",      badge: "border-ink/60 bg-ink/[0.05] text-ink",            marker: "bg-ink" },
  corroborating: { label: "Corroborating", badge: "border-confirmed/50 bg-confirmed/[0.05] text-confirmed", marker: "bg-confirmed" },
  conflicting:   { label: "Conflicting",   badge: "border-disputed/50 bg-disputed/[0.05] text-disputed",    marker: "bg-disputed" },
};