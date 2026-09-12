import { events } from "./events";
import { claimsByEvent } from "./claims";
import { reliabilityScores } from "./reliability";
import { slugify } from "../format";
import type { Claim, Event, ReliabilityScore, Topic } from "../types";

export { events } from "./events";
export { claimsByEvent } from "./claims";
export { reliabilityScores } from "./reliability";

export function getAllEvents(): Event[] {
  return events;
}

export function getEvent(id: string): Event | undefined {
  return events.find((e) => e.id === id);
}

export function getClaims(eventId: string): Claim[] {
  return claimsByEvent[eventId] ?? [];
}

export function getRelatedEvents(eventId: string): Event[] {
  const current = getEvent(eventId);
  if (!current) return [];
  const currentEntityNames = new Set(current.entities.map((e) => e.name));

  return events
    .filter((e) => e.id !== eventId)
    .filter(
      (e) =>
        e.competition === current.competition ||
        e.entities.some((entity) => currentEntityNames.has(entity.name))
    )
    .slice(0, 3);
}

export const reliabilityByName = new Map<string, ReliabilityScore>(
  reliabilityScores.map((s) => [s.subjectName, s])
);

export const reliabilityBySlug = new Map<string, ReliabilityScore>(
  reliabilityScores.map((s) => [slugify(s.subjectName), s])
);

export function getTopic(slug: string): Topic | undefined {
  // 1. Search across all entities in events for matching slug
  for (const ev of events) {
    for (const ent of ev.entities) {
      if (slugify(ent.name) === slug) {
        const topicEvents = events.filter((e) =>
          e.entities.some((x) => x.name === ent.name)
        );
        return {
          slug,
          name: ent.name,
          type: ent.type,
          events: topicEvents,
        };
      }
    }
  }

  // 2. Search competition
  for (const ev of events) {
    if (slugify(ev.competition) === slug) {
      const topicEvents = events.filter((e) => slugify(e.competition) === slug);
      return {
        slug,
        name: ev.competition,
        type: "competition",
        events: topicEvents,
      };
    }
  }

  // 3. Search sport
  for (const ev of events) {
    if (slugify(ev.sport) === slug) {
      const topicEvents = events.filter((e) => slugify(e.sport) === slug);
      return {
        slug,
        name: ev.sport,
        type: "sport",
        events: topicEvents,
      };
    }
  }

  return undefined;
}
