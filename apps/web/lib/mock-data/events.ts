import type { Event } from "@/lib/types";
import { minutesAgo } from "./helpers";

// All outlets, players and deals below are fictional fixtures for this demo.
// .example URLs are reserved placeholders for "link to the original source".

export const events: Event[] = [
  {
    id: "e-001-osei-arsenal",
    headline: "Emeka Osei completes €64m move to Arsenal from Sporting CP",
    status: "confirmed",
    independentSources: 5,
    sport: "Football",
    competition: "Premier League",
    updatedAt: minutesAgo(90),
    summary:
      "Announced by both clubs on Tuesday afternoon; the fee is confirmed in a league filing. A five-year contract runs to 2030, with €6m in add-ons.",
    firstReportedBy: { outlet: "The Woodwork", leadTimeMinutes: 96 },
    entities: [
      { type: "player", name: "Emeka Osei" },
      { type: "club", name: "Arsenal" },
      { type: "club", name: "Sporting CP" },
    ],
    sourceUrl: "https://thewoodwork.example/football/osei-arsenal-confirmed",
  },
  {
    id: "e-002-lindqvist-madrid",
    headline: "Real Madrid open talks for Jonas Lindqvist ahead of release-clause window",
    status: "well_corroborated",
    independentSources: 3,
    sport: "Football",
    competition: "La Liga",
    updatedAt: minutesAgo(420),
    summary:
      "Three desks independently report contact with the striker's camp. A €58m bid is being prepared for when the clause window opens on 1 July; personal terms are not yet agreed.",
    firstReportedBy: { outlet: "Estadio Dispatch", leadTimeMinutes: 60 },
    entities: [
      { type: "player", name: "Jonas Lindqvist" },
      { type: "club", name: "Real Madrid" },
    ],
    sourceUrl: "https://estadiodispatch.example/football/lindqvist-talks",
  },
  {
    id: "e-003-duarte-chelsea",
    headline: "Chelsea hold Thursday medical slot for Rafael Duarte: fee still unresolved",
    status: "developing",
    independentSources: 2,
    sport: "Football",
    competition: "Premier League",
    updatedAt: minutesAgo(300),
    summary:
      "Two outlets report concrete progress and a provisionally booked medical, but the clubs have not settled a payment structure. One tabloid's “done deal” is not corroborated.",
    firstReportedBy: { outlet: "Terrace Wire", leadTimeMinutes: 30 },
    entities: [
      { type: "player", name: "Rafael Duarte" },
      { type: "club", name: "Chelsea" },
    ],
    sourceUrl: "https://terracewire.example/football/duarte-chelsea-live",
  },
  {
    id: "e-004-mori-bayern",
    headline: "Bayern weighing a January move for Kaito Mori",
    status: "rumour",
    independentSources: 1,
    sport: "Football",
    competition: "Bundesliga",
    updatedAt: minutesAgo(4300),
    summary:
      "A single-source exclusive with no independent corroboration after three days. The ledger holds it at Rumour unless a second desk picks it up.",
    firstReportedBy: { outlet: "Transfer Window Daily", leadTimeMinutes: 0 },
    entities: [
      { type: "player", name: "Kaito Mori" },
      { type: "club", name: "Bayern München" },
    ],
    sourceUrl: "https://transferwindowdaily.example/exclusive/mori-bayern",
  },
  {
    id: "e-005-barski-barcelona",
    headline: "Barcelona and Viktor Barski: personal terms “agreed”: or not agreed at all",
    status: "disputed",
    independentSources: 4,
    sport: "Football",
    competition: "La Liga",
    updatedAt: minutesAgo(600),
    summary:
      "One outlet claims terms are agreed; two desks with stronger records report the opposite, and the club denies any offer. Treated as unsettled.",
    firstReportedBy: { outlet: "Transfer Window Daily", leadTimeMinutes: 50 },
    entities: [
      { type: "player", name: "Viktor Barski" },
      { type: "club", name: "Barcelona" },
    ],
    sourceUrl: "https://transferwindowdaily.example/exclusive/barski-barcelona",
  },
  {
    id: "e-006-cifuentes-westham",
    headline: "West Ham “complete” Andrés Cifuentes signing: later corrected: deal collapsed",
    status: "corrected",
    independentSources: 3,
    sport: "Football",
    competition: "Premier League",
    updatedAt: minutesAgo(2600),
    summary:
      "Reported as done on a four-year deal; a medical issue ended it days later. The claim is preserved here, marked Corrected: the ledger never deletes.",
    firstReportedBy: { outlet: "Terrace Wire", leadTimeMinutes: 150 },
    entities: [
      { type: "player", name: "Andrés Cifuentes" },
      { type: "club", name: "West Ham United" },
    ],
    sourceUrl: "https://terracewire.example/football/cifuentes-done-deal",
    statusNote:
      "Corrected two days after first report: the medical flagged an issue and the move collapsed. The player remains at Lyon.",
  },
  {
    id: "e-007-novak-liverpool",
    headline: "Liverpool open contract talks with Karel Novák",
    status: "well_corroborated",
    independentSources: 3,
    sport: "Football",
    competition: "Premier League",
    updatedAt: minutesAgo(3000),
    summary:
      "Three outlets report talks on an extension beyond 2026; a package worth around £140,000 a week has been discussed, with nothing signed.",
    firstReportedBy: { outlet: "The Woodwork", leadTimeMinutes: 40 },
    entities: [
      { type: "player", name: "Karel Novák" },
      { type: "club", name: "Liverpool" },
    ],
    sourceUrl: "https://thewoodwork.example/football/novak-contract-talks",
  },
  {
    id: "e-008-ferraz-city",
    headline: "Manchester City close on personal terms with Thiago Ferraz",
    status: "developing",
    independentSources: 2,
    sport: "Football",
    competition: "Premier League",
    updatedAt: minutesAgo(900),
    summary:
      "Personal terms are close but not final, and no club-to-club agreement exists with Girona. Expect movement either way within the week.",
    firstReportedBy: { outlet: "Estadio Dispatch", leadTimeMinutes: 40 },
    entities: [
      { type: "player", name: "Thiago Ferraz" },
      { type: "club", name: "Manchester City" },
      { type: "club", name: "Girona" },
    ],
    sourceUrl: "https://estadiodispatch.example/football/ferraz-city-terms",
  },
  {
    id: "e-009-sy-alnassr",
    headline: "Al-Nassr prepare a record €120m offer for Amadou Sy",
    status: "rumour",
    independentSources: 1,
    sport: "Football",
    competition: "Saudi Pro League",
    updatedAt: minutesAgo(5800),
    summary:
      "One tabloid exclusive, four days without a second source. The player's camp has not commented.",
    firstReportedBy: { outlet: "Transfer Window Daily", leadTimeMinutes: 0 },
    entities: [
      { type: "player", name: "Amadou Sy" },
      { type: "club", name: "Al-Nassr" },
    ],
    sourceUrl: "https://transferwindowdaily.example/exclusive/sy-alnassr",
  },
  {
    id: "e-010-brandt-brighton",
    headline: "Brighton confirm club-record signing of Luca Brandt",
    status: "confirmed",
    independentSources: 4,
    sport: "Football",
    competition: "Premier League",
    updatedAt: minutesAgo(1500),
    summary:
      "Announced Tuesday: £26m rising to £30m, five years plus a club option of a further year. Squad number 14.",
    firstReportedBy: { outlet: "The Woodwork", leadTimeMinutes: 120 },
    entities: [
      { type: "player", name: "Luca Brandt" },
      { type: "club", name: "Brighton & Hove Albion" },
    ],
    sourceUrl: "https://thewoodwork.example/football/brandt-brighton-confirmed",
  },
  {
    id: "e-011-sy-newcastle",
    headline: "Newcastle “table £45m” for Amadou Sy: but the selling side says no bid arrived",
    status: "disputed",
    independentSources: 3,
    sport: "Football",
    competition: "Premier League",
    updatedAt: minutesAgo(200),
    summary:
      "Two outlets report a submitted bid; the desk with the strongest record reports no bid has been received and the figure is being floated by intermediaries.",
    firstReportedBy: { outlet: "Terrace Wire", leadTimeMinutes: 50 },
    entities: [
      { type: "player", name: "Amadou Sy" },
      { type: "club", name: "Newcastle United" },
    ],
    sourceUrl: "https://terracewire.example/football/sy-newcastle-bid",
  },
];