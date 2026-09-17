import type { Claim, Event, ReliabilityScore } from "./types";
import { getAllEvents, getClaims, getEvent, reliabilityBySlug, reliabilityScores } from "./mock-data";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function mapApiEvent(raw: any): Event {
  return {
    id: raw.id,
    headline: raw.headline,
    status: raw.status,
    independentSources: raw.independent_sources ?? raw.independentSources ?? 1,
    sport: raw.sport,
    competition: raw.competition,
    updatedAt: raw.updated_at ?? raw.updatedAt ?? new Date().toISOString(),
    summary: raw.summary,
    firstReportedBy: raw.first_reported_by
      ? {
          outlet: raw.first_reported_by.outlet,
          leadTimeMinutes:
            raw.first_reported_by.lead_time_minutes ??
            raw.first_reported_by.leadTimeMinutes ??
            0,
        }
      : raw.firstReportedBy ?? null,
    entities: raw.entities ?? [],
    sourceUrl: raw.source_url ?? raw.sourceUrl ?? "",
    statusNote: raw.status_note ?? raw.statusNote,
    language: raw.language ?? "en",
    originalLanguage: raw.original_language ?? raw.originalLanguage,
    originalHeadline: raw.original_headline ?? raw.originalHeadline,
    originalSummary: raw.original_summary ?? raw.originalSummary,
    isTranslated: raw.is_translated ?? raw.isTranslated ?? false,
    availableTranslations: raw.available_translations ?? raw.availableTranslations ?? [],
  };
}

export function mapApiClaim(raw: any): Claim {
  return {
    id: raw.id,
    eventId: raw.event_id ?? raw.eventId,
    outlet: raw.outlet,
    reporter: raw.reporter ?? null,
    text: raw.text,
    timestamp: raw.timestamp ?? new Date().toISOString(),
    attribution: raw.attribution,
    language: raw.language ?? "en",
    url: raw.url,
  };
}

export function mapApiReliabilityScore(raw: any): ReliabilityScore {
  return {
    subjectName: raw.subject_name ?? raw.subjectName,
    subjectType: raw.subject_type ?? raw.subjectType ?? "outlet",
    sampleSize: raw.sample_size ?? raw.sampleSize ?? 0,
    correctCount: raw.correct_count ?? raw.correctCount ?? 0,
    scoreByCategory: (raw.score_by_category ?? raw.scoreByCategory ?? []).map((c: any) => ({
      category: c.category,
      correct: c.correct,
      total: c.total,
    })),
    recentResolutions: (raw.recent_resolutions ?? raw.recentResolutions ?? []).map((r: any) => ({
      claim: r.claim,
      outcome: r.outcome,
    })),
    affiliation: raw.affiliation,
    beat: raw.beat,
  };
}

export async function fetchEvents(status?: string, lang: string = "en"): Promise<Event[]> {
  try {
    const url = new URL(`${API_BASE_URL}/events`);
    if (status) {
      url.searchParams.set("status", status);
    }
    if (lang) {
      url.searchParams.set("lang", lang);
    }
    const res = await fetch(url.toString(), {
      next: { revalidate: 0 },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data.map(mapApiEvent);
      }
    }
  } catch {
    // Graceful fallback to verified local fixtures if API is offline
  }
  const fallback = getAllEvents();
  return status ? fallback.filter((e) => e.status === status) : fallback;
}

export async function fetchEventById(id: string, lang: string = "en"): Promise<Event | null> {
  try {
    const url = new URL(`${API_BASE_URL}/events/${id}`);
    if (lang) {
      url.searchParams.set("lang", lang);
    }
    const res = await fetch(url.toString(), {
      next: { revalidate: 0 },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const raw = await res.json();
      return mapApiEvent(raw);
    }
  } catch {
    // Graceful fallback to verified local fixtures if API is offline
  }
  return getEvent(id) ?? null;
}

export async function fetchClaimsByEvent(eventId: string): Promise<Claim[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/claims/by-event/${eventId}`, {
      next: { revalidate: 0 },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data.map(mapApiClaim);
      }
    }
  } catch {
    // Graceful fallback to verified local fixtures if API is offline
  }
  return getClaims(eventId);
}

export async function fetchReliabilityScores(): Promise<ReliabilityScore[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/reliability`, {
      next: { revalidate: 0 },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data.map(mapApiReliabilityScore);
      }
    }
  } catch {
    // Graceful fallback to verified local fixtures if API is offline
  }
  return reliabilityScores;
}

export async function fetchReliabilityScore(slug: string): Promise<ReliabilityScore | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/reliability/${slug}`, {
      next: { revalidate: 0 },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const raw = await res.json();
      return mapApiReliabilityScore(raw);
    }
  } catch {
    // Graceful fallback to verified local fixtures if API is offline
  }
  return reliabilityBySlug.get(slug) ?? null;
}

export async function fetchClaimsBySource(subjectSlug: string): Promise<{ claim: Claim; event: Event }[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/claims/by-source/${subjectSlug}`, {
      next: { revalidate: 0 },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data)) {
        return data.map((item: any) => ({
          claim: mapApiClaim(item.claim),
          event: mapApiEvent(item.event),
        }));
      }
    }
  } catch {
    // Graceful fallback to verified local fixtures if API is offline
  }
  return [];
}

export async function fetchCorrections(): Promise<{ claim: Claim; event: Event }[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/claims/corrections`, {
      next: { revalidate: 0 },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data)) {
        return data.map((item: any) => ({
          claim: mapApiClaim(item.claim),
          event: mapApiEvent(item.event),
        }));
      }
    }
  } catch {
    // Fallback
  }
  return [];
}

const ADMIN_API_KEY = process.env.ADMIN_API_KEY || "dev-admin-ledger-secret-key";

export async function fetchAdminOverview(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/overview`, {
      next: { revalidate: 0 },
      headers: { "X-Admin-Key": ADMIN_API_KEY },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback default
  }
  return {
    total_events: 5,
    total_claims: 12,
    total_sources: 15,
    pending_source_reviews: 2,
    pending_human_reviews: 3,
    quarantined_documents: 2,
    dead_letter_jobs: 2,
    total_inference_spend_eur: 0.0035,
    cost_per_thousand_events_eur: 0.70,
  };
}

export async function fetchAdminReviewQueue(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/review-queue`, {
      next: { revalidate: 0 },
      headers: { "X-Admin-Key": ADMIN_API_KEY },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback
  }
  return [];
}

export async function fetchAdminCosts(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/costs`, {
      next: { revalidate: 0 },
      headers: { "X-Admin-Key": ADMIN_API_KEY },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback
  }
  return {
    build_pool_budget_eur: 100.0,
    run_pool_budget_eur: 50.0,
    inference_pool_spend_eur: 0.0035,
    cost_per_thousand_events_eur: 0.70,
    target_cost_per_event_eur: 0.02,
    rung_breakdown: {
      L0_Deterministic: 45,
      L1_LocalCPU: 28,
      L2_SmallHosted: 12,
      L3_MidHosted: 2,
      L4_Frontier: 0,
    },
    recent_traces: [],
  };
}

export async function fetchAdminSources(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/sources/registry`, {
      next: { revalidate: 0 },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback
  }
  return [];
}

export async function fetchAdminEntities(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/entities`, {
      next: { revalidate: 0 },
      headers: { "X-Admin-Key": ADMIN_API_KEY },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback
  }
  return [];
}

export async function fetchAdminDeadLetters(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/dead-letters`, {
      next: { revalidate: 0 },
      headers: { "X-Admin-Key": ADMIN_API_KEY },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback
  }
  return [];
}

export async function replayDeadLetterJob(deadLetterId: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/dead-letters/${deadLetterId}/replay`, {
      method: "POST",
      headers: { "X-Admin-Key": ADMIN_API_KEY },
    });
    return await res.json();
  } catch {
    return { status: "error" };
  }
}

export async function fetchAdminQuarantine(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/quarantine`, {
      next: { revalidate: 0 },
      headers: { "X-Admin-Key": ADMIN_API_KEY },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback
  }
  return [];
}

export async function pauseAdminSource(registryId: string, reason: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/sources/${registryId}/pause`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Key": ADMIN_API_KEY,
      },
      body: JSON.stringify({ reason }),
    });
    return await res.json();
  } catch {
    return { status: "error" };
  }
}

export async function resumeAdminSource(registryId: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/sources/${registryId}/resume`, {
      method: "POST",
      headers: { "X-Admin-Key": ADMIN_API_KEY },
    });
    return await res.json();
  } catch {
    return { status: "error" };
  }
}

export async function blockAdminSource(registryId: string, reason: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/sources/${registryId}/block`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Key": ADMIN_API_KEY,
      },
      body: JSON.stringify({ reason }),
    });
    return await res.json();
  } catch {
    return { status: "error" };
  }
}

export async function resolveAdminReviewItem(
  claimId: string,
  action: "confirm" | "dispute" | "correct",
  notes?: string
): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/review-queue/${claimId}/resolve`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Key": ADMIN_API_KEY,
      },
      body: JSON.stringify({ action, notes }),
    });
    return await res.json();
  } catch {
    return { status: "error" };
  }
}

export async function fetchAdminEvaluationLogs(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/evaluation-logs`, {
      next: { revalidate: 0 },
      headers: { "X-Admin-Key": ADMIN_API_KEY },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback
  }
  return [];
}

export interface AdminClusterSummary {
  event_id: string;
  headline: string;
  status: string;
  sport: string;
  competition: string;
  first_reported_outlet: string | null;
  claims_count: number;
  evidence_count: number;
  disputed_by_event_id: string | null;
  dispute_status: string | null;
  entities: { name: string; type: string }[];
  created_at: string;
  updated_at: string;
}

export interface AdminEvidenceItem {
  id: string;
  outlet_name: string;
  reporter: string | null;
  attribution_type: string;
  similarity_to_root: number;
  published_at: string | null;
  source_url: string;
}

export interface AdminClaimClusterItem {
  id: string;
  claim_text: string;
  predicate: string | null;
  subject_id: string | null;
  object_id: string | null;
  evidence_span: string | null;
  resolvable: boolean;
  resolution_class: string;
  outlet: string;
  reporter: string | null;
  attribution: string;
  attribution_type: string;
  language: string;
  timestamp: string | null;
  evidence_count: number;
  evidence: AdminEvidenceItem[];
}

export interface AdminClusterDetail {
  event_id: string;
  headline: string;
  summary: string;
  status: string;
  sport: string;
  competition: string;
  first_reported_outlet: string | null;
  disputed_by_event_id: string | null;
  dispute_status: string | null;
  dispute_target: {
    event_id: string;
    headline: string;
    status: string;
    dispute_status: string | null;
  } | null;
  entities: { name: string; type: string }[];
  created_at: string;
  updated_at: string;
  claims: AdminClaimClusterItem[];
}

export async function fetchAdminClusters(): Promise<AdminClusterSummary[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/clusters`, {
      next: { revalidate: 0 },
      headers: { "X-Admin-Key": ADMIN_API_KEY },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback
  }
  return [];
}

export async function fetchAdminClusterDetail(eventId: string): Promise<AdminClusterDetail | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/admin/clusters/${eventId}`, {
      next: { revalidate: 0 },
      headers: { "X-Admin-Key": ADMIN_API_KEY },
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fallback
  }
  return null;
}



