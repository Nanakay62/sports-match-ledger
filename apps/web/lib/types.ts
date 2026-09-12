// Core domain types for Matchday Ledger.
// These mirror the fixtures in src/lib/mock-data: swap the fixtures for real
// API payloads and nothing else has to change.

export type EventStatus =
  | "confirmed"
  | "well_corroborated"
  | "developing"
  | "rumour"
  | "disputed"
  | "corrected";

export interface EventFirstReport {
  outlet: string;
  /** Minutes ahead of the next outlet. 0 = sole first report so far. */
  leadTimeMinutes: number;
}

export interface EventEntity {
  type: "player" | "club" | "competition" | "sport";
  name: string;
}

export interface Event {
  id: string;
  headline: string;
  status: EventStatus;
  independentSources: number;
  sport: string;
  competition: string;
  updatedAt: string; // ISO 8601
  summary: string;
  firstReportedBy: EventFirstReport | null;
  entities: EventEntity[];
  /** Link to the original published claim: always rendered in the UI. */
  sourceUrl: string;
  /** Plain-language context for exceptional statuses (e.g. what was corrected). */
  statusNote?: string;
  language?: string;
  originalLanguage?: string;
  originalHeadline?: string;
  originalSummary?: string;
  isTranslated?: boolean;
  availableTranslations?: string[];
}

export type ClaimAttribution = "original" | "corroborating" | "conflicting";

export interface Claim {
  id: string;
  eventId: string;
  outlet: string;
  reporter: string | null;
  text: string;
  timestamp: string; // ISO 8601
  attribution: ClaimAttribution;
  /** Language the claim was first published in; `text` is our translation. */
  language: string;
  /** Link to the original published piece. */
  url: string;
}

export interface CategoryRecord {
  category: string;
  correct: number;
  total: number;
}

export interface ClaimResolution {
  claim: string;
  outcome: "correct" | "incorrect";
}

export interface ReliabilityScore {
  subjectName: string;
  subjectType: "outlet" | "reporter";
  /** Below 10 the UI renders the "insufficient record" state: never a score. */
  sampleSize: number;
  correctCount: number;
  scoreByCategory: CategoryRecord[];
  recentResolutions: ClaimResolution[];
  /** Reporter-only metadata for the profile page. */
  affiliation?: string;
  beat?: string;
}

export interface Topic {
  slug: string;
  name: string;
  type: "player" | "club" | "competition" | "sport";
  events: Event[];
}

export interface RumourStage {
  stage: "origin" | "corroboration" | "dispute" | "resolution";
  title: string;
  timestamp: string;
  outlet?: string;
  reporter?: string;
  text: string;
  status: EventStatus;
}

export interface RumourLifecycle {
  event: Event;
  claims: Claim[];
  stages: RumourStage[];
}

export interface AdminStats {
  totalEvents: number;
  totalClaims: number;
  totalSources: number;
  pendingSourceReviews: number;
  pendingHumanReviews: number;
  totalInferenceSpendEur: number;
  costPerThousandEventsEur: number;
}