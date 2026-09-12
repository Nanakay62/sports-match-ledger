import type { Claim, Event, EventStatus } from "./types";

export type ReasonKind = "ok" | "warn" | "bad" | "info";

export interface ReasoningBullet {
  kind: ReasonKind;
  text: string;
}

export function buildStatusReasoning(event: Event, claims: Claim[] = []): ReasoningBullet[] {
  const bullets: ReasoningBullet[] = [];
  const status: EventStatus = event.status;
  const numSources = event.independentSources;
  const numClaims = claims.length;

  switch (status) {
    case "confirmed":
      bullets.push({
        kind: "ok",
        text: "**Official confirmation on record:** announced by club principals or verified via regulatory league filings.",
      });
      bullets.push({
        kind: "ok",
        text: `**Corroborated across ${numSources} independent sources** with ${numClaims} aligned claims logged in the ledger.`,
      });
      break;

    case "well_corroborated":
      bullets.push({
        kind: "ok",
        text: `**Multiple independent desks:** ${numSources} independent outlets corroborate active talks and deal framework.`,
      });
      bullets.push({
        kind: "warn",
        text: "**Formal execution pending:** personal terms or club-to-club financial structures remain under negotiation.",
      });
      break;

    case "developing":
      bullets.push({
        kind: "warn",
        text: `**Live negotiations:** ${numSources} desks report concrete activity, but terms remain in flux.`,
      });
      bullets.push({
        kind: "info",
        text: `**${numClaims} claims logged:** desk is monitoring for verification or conflicting briefings.`,
      });
      break;

    case "rumour":
      bullets.push({
        kind: "warn",
        text: "**Single-source claim:** initial report lacks independent corroboration after multi-day monitoring window.",
      });
      bullets.push({
        kind: "info",
        text: "**Ledger holds at Rumour:** status will not escalate without verification from a second independent desk.",
      });
      break;

    case "disputed":
      bullets.push({
        kind: "bad",
        text: "**Direct conflict between sources:** reputable desks report irreconcilable positions or denials.",
      });
      bullets.push({
        kind: "bad",
        text: `**Contested terms:** contradictory claims on record regarding whether bids or terms were ever exchanged.`,
      });
      break;

    case "corrected":
      bullets.push({
        kind: "bad",
        text: `**Prior report superseded:** ${event.statusNote ?? "deal collapsed or initial report proved inaccurate."}`,
      });
      bullets.push({
        kind: "info",
        text: "**Receipts preserved:** original erroneous claims remain permanently recorded on the source's public ledger.",
      });
      break;

    default:
      bullets.push({
        kind: "info",
        text: "**Status pending review:** claims are undergoing attribution verification.",
      });
  }

  return bullets;
}
