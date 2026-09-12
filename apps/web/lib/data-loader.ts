import type { Claim, Event, ReliabilityScore } from "./types";
import {
  claimsByEvent,
  getAllEvents,
  getClaims,
  getEvent,
  getRelatedEvents,
  getTopic,
  reliabilityByName,
  reliabilityBySlug,
  reliabilityScores,
} from "./mock-data";
import { EVENT_TRANSLATIONS, CLAIM_TRANSLATIONS } from "./mock-data/translations";
import {
  fetchClaimsByEvent,
  fetchClaimsBySource,
  fetchCorrections,
  fetchEventById,
  fetchEvents,
  fetchReliabilityScore,
  fetchReliabilityScores,
} from "./api";

const USE_MOCK_DATA = process.env.NEXT_PUBLIC_USE_MOCK_DATA === "true";

export function localizeEvent(event: Event, lang: string = "en"): Event {
  const norm = lang.toLowerCase();
  if (norm === "en") return event;
  const tr = EVENT_TRANSLATIONS[event.id]?.[norm];
  if (!tr) return event;
  return {
    ...event,
    headline: tr.headline,
    summary: tr.summary,
    statusNote: tr.statusNote ?? event.statusNote,
    isTranslated: true,
  };
}

export function localizeClaim(claim: Claim, lang: string = "en"): Claim {
  const norm = lang.toLowerCase();
  if (norm === "en") return claim;
  const tr = CLAIM_TRANSLATIONS[claim.id]?.[norm];
  if (!tr) return claim;
  return {
    ...claim,
    text: tr.text,
  };
}

export async function loadAllEvents(status?: string, lang: string = "en"): Promise<Event[]> {
  if (USE_MOCK_DATA) {
    const all = getAllEvents().map((e) => localizeEvent(e, lang));
    return status ? all.filter((e) => e.status === status) : all;
  }
  const events = await fetchEvents(status, lang);
  return events.map((e) => localizeEvent(e, lang));
}

export async function loadEvent(id: string, lang: string = "en"): Promise<Event | null> {
  if (USE_MOCK_DATA) {
    const ev = getEvent(id);
    return ev ? localizeEvent(ev, lang) : null;
  }
  const ev = await fetchEventById(id, lang);
  return ev ? localizeEvent(ev, lang) : null;
}

export async function loadClaims(eventId: string, lang: string = "en"): Promise<Claim[]> {
  const rawClaims = USE_MOCK_DATA ? getClaims(eventId) : await fetchClaimsByEvent(eventId);
  return rawClaims.map((c) => localizeClaim(c, lang));
}

export async function loadRelatedEvents(eventId: string): Promise<Event[]> {
  if (USE_MOCK_DATA) {
    return getRelatedEvents(eventId);
  }

  const allEvents = await fetchEvents();
  const current = allEvents.find((e) => e.id === eventId);
  if (!current) return [];

  const currentEntityNames = new Set(current.entities.map((e) => e.name));
  return allEvents
    .filter((e) => e.id !== eventId)
    .filter(
      (e) =>
        e.competition === current.competition ||
        e.entities.some((entity) => currentEntityNames.has(entity.name))
    )
    .slice(0, 3);
}

export async function loadAllReliabilityScores(): Promise<ReliabilityScore[]> {
  if (USE_MOCK_DATA) {
    return reliabilityScores;
  }
  return fetchReliabilityScores();
}

export async function loadReliabilityScore(slug: string): Promise<ReliabilityScore | null> {
  if (USE_MOCK_DATA) {
    return reliabilityBySlug.get(slug) ?? null;
  }
  return fetchReliabilityScore(slug);
}

export async function loadSubjectClaimsAndEvents(subject: string): Promise<{ claim: Claim; event: Event }[]> {
  if (USE_MOCK_DATA) {
    const score = reliabilityBySlug.get(subject);
    const targetName = score?.subjectName ?? subject;
    return Object.entries(claimsByEvent)
      .flatMap(([eid, cs]) =>
        cs
          .filter((c) => c.outlet === targetName || c.reporter === targetName)
          .map((claim) => ({ claim, event: getEvent(eid)! }))
      )
      .filter((r) => r.event)
      .sort((a, b) => b.claim.timestamp.localeCompare(a.claim.timestamp));
  }

  return fetchClaimsBySource(subject);
}

export async function loadCorrections(lang: string = "en"): Promise<{ claim: Claim; event: Event }[]> {
  let raw: { claim: Claim; event: Event }[] = [];

  if (USE_MOCK_DATA) {
    const correctedEvents = getAllEvents().filter(
      (e) => e.status === "corrected" || e.status === "disputed"
    );
    raw = correctedEvents.flatMap((event) => {
      const claims = getClaims(event.id);
      return claims.map((claim) => ({ claim, event }));
    });
  } else {
    const live = await fetchCorrections();
    if (live.length > 0) {
      raw = live;
    } else {
      const correctedEvents = getAllEvents().filter(
        (e) => e.status === "corrected" || e.status === "disputed"
      );
      raw = correctedEvents.flatMap((event) => {
        const claims = getClaims(event.id);
        return claims.map((claim) => ({ claim, event }));
      });
    }
  }

  return raw.map(({ claim, event }) => ({
    claim: localizeClaim(claim, lang),
    event: localizeEvent(event, lang),
  }));
}

export async function loadRumourLifecycle(eventId: string, lang: string = "en") {
  const event = await loadEvent(eventId, lang);
  if (!event) return null;
  const claims = await loadClaims(eventId, lang);

  // Synthesize lifecycle stages
  const stages = [
    {
      stage: "origin" as const,
      title: "First Reported",
      timestamp: event.firstReportedBy ? event.updatedAt : claims[0]?.timestamp ?? event.updatedAt,
      outlet: event.firstReportedBy?.outlet ?? claims[0]?.outlet ?? "Wire report",
      reporter: claims[0]?.reporter ?? undefined,
      text: claims[0]?.text ?? event.summary,
      status: "developing" as const,
    },
    ...claims.slice(1).map((c, i) => ({
      stage: (c.attribution === "conflicting" ? "dispute" : "corroboration") as "dispute" | "corroboration",
      title: c.attribution === "conflicting" ? "Contradiction / Dispute" : `Corroboration #${i + 1}`,
      timestamp: c.timestamp,
      outlet: c.outlet,
      reporter: c.reporter ?? undefined,
      text: c.text,
      status: (c.attribution === "conflicting" ? "disputed" : "well_corroborated") as any,
    })),
    {
      stage: "resolution" as const,
      title: event.status === "confirmed" ? "Official Resolution: Confirmed" : (event.status === "corrected" ? "Resolution: Corrected / Retracted" : "Current Verified State"),
      timestamp: event.updatedAt,
      text: event.statusNote ?? event.summary,
      status: event.status,
    },
  ];

  return { event, claims, stages };
}

export {
  getTopic,
  reliabilityByName,
  reliabilityBySlug,
  reliabilityScores,
};

