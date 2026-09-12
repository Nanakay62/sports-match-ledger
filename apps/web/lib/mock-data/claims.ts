import type { Claim } from "@/lib/types";
import { minutesAgo } from "./helpers";

/** Newest first, keyed by event id. */
export const claimsByEvent: Record<string, Claim[]> = {
  "e-001-osei-arsenal": [
    { id: "c-001a", eventId: "e-001-osei-arsenal", outlet: "The Woodwork", reporter: "Tom Whitcombe", text: "CONFIRMED: Arsenal announce Emeka Osei on a five-year deal. €64m fixed fee, payable over the term, plus €6m in add-ons.", timestamp: minutesAgo(90), attribution: "corroborating", language: "en", url: "https://thewoodwork.example/football/osei-announcement" },
    { id: "c-001b", eventId: "e-001-osei-arsenal", outlet: "Floodlight Forum", reporter: null, text: "Paperwork for Osei has been lodged with the league; squad number 27 has been reserved in internal systems.", timestamp: minutesAgo(1400), attribution: "corroborating", language: "en", url: "https://floodlightforum.example/osei-paperwork" },
    { id: "c-001c", eventId: "e-001-osei-arsenal", outlet: "Terrace Wire", reporter: "Dara Keane", text: "Arsenal and Sporting have exchanged final documents. The medical was completed in London this morning.", timestamp: minutesAgo(2300), attribution: "corroborating", language: "en", url: "https://terracewire.example/osei-documents" },
    { id: "c-001d", eventId: "e-001-osei-arsenal", outlet: "Estadio Dispatch", reporter: "Mara Oduya", text: "Sporting confirm the Osei agreement in a filing to the market regulator: €64m fixed, with up to €6m in add-ons.", timestamp: minutesAgo(4304), attribution: "corroborating", language: "es", url: "https://estadiodispatch.example/osei-regulator-filing" },
    { id: "c-001e", eventId: "e-001-osei-arsenal", outlet: "The Woodwork", reporter: "Tom Whitcombe", text: "Emeka Osei has completed his medical with Arsenal and will sign a five-year contract. Announcement expected within 48 hours.", timestamp: minutesAgo(4400), attribution: "original", language: "en", url: "https://thewoodwork.example/football/osei-arsenal-medical" },
  ],
  "e-002-lindqvist-madrid": [
    { id: "c-002a", eventId: "e-002-lindqvist-madrid", outlet: "Terrace Wire", reporter: "Dara Keane", text: "Real Madrid are preparing a €58m bid for Jonas Lindqvist, to be lodged as soon as the release-clause window opens on 1 July.", timestamp: minutesAgo(420), attribution: "corroborating", language: "en", url: "https://terracewire.example/lindqvist-bid" },
    { id: "c-002b", eventId: "e-002-lindqvist-madrid", outlet: "The Woodwork", reporter: "Tom Whitcombe", text: "Madrid have made Lindqvist their priority attacking target. Initial contact with his representatives was made ten days ago.", timestamp: minutesAgo(1500), attribution: "corroborating", language: "en", url: "https://thewoodwork.example/lindqvist-priority" },
    { id: "c-002c", eventId: "e-002-lindqvist-madrid", outlet: "Estadio Dispatch", reporter: "Mara Oduya", text: "Real Madrid have opened talks with Lindqvist's camp over a summer move. The player is receptive to the project.", timestamp: minutesAgo(1560), attribution: "original", language: "es", url: "https://estadiodispatch.example/lindqvist-talks" },
  ],
  "e-003-duarte-chelsea": [
    { id: "c-003a", eventId: "e-003-duarte-chelsea", outlet: "Transfer Window Daily", reporter: null, text: "DONE DEAL: Rafael Duarte has agreed personal terms with Chelsea. The deal is complete.", timestamp: minutesAgo(300), attribution: "conflicting", language: "en", url: "https://transferwindowdaily.example/duarte-done" },
    { id: "c-003b", eventId: "e-003-duarte-chelsea", outlet: "The Woodwork", reporter: "Tom Whitcombe", text: "Chelsea's move for Rafael Duarte is live, but a payment structure with his club is not yet agreed. A Thursday medical slot has been provisionally held.", timestamp: minutesAgo(480), attribution: "corroborating", language: "en", url: "https://thewoodwork.example/duarte-medical-slot" },
    { id: "c-003c", eventId: "e-003-duarte-chelsea", outlet: "Terrace Wire", reporter: "Dara Keane", text: "Chelsea are working on Rafael Duarte and have provisionally held a medical slot for Thursday.", timestamp: minutesAgo(510), attribution: "original", language: "en", url: "https://terracewire.example/duarte-chelsea" },
  ],
  "e-004-mori-bayern": [
    { id: "c-004a", eventId: "e-004-mori-bayern", outlet: "Transfer Window Daily", reporter: null, text: "EXCLUSIVE: Bayern München are preparing a January swoop for Kaito Mori.", timestamp: minutesAgo(4300), attribution: "original", language: "en", url: "https://transferwindowdaily.example/exclusive/mori-bayern" },
  ],
  "e-005-barski-barcelona": [
    { id: "c-005a", eventId: "e-005-barski-barcelona", outlet: "The Woodwork", reporter: "Tom Whitcombe", text: "No terms sheet has been exchanged between Barcelona and Barski's camp. Any talks to date have been informal.", timestamp: minutesAgo(600), attribution: "conflicting", language: "en", url: "https://thewoodwork.example/barski-no-terms" },
    { id: "c-005b", eventId: "e-005-barski-barcelona", outlet: "Estadio Dispatch", reporter: "Mara Oduya", text: "Barcelona sources deny any agreement with Viktor Barski: “there are no terms on the table.”", timestamp: minutesAgo(640), attribution: "conflicting", language: "es", url: "https://estadiodispatch.example/barski-denial" },
    { id: "c-005c", eventId: "e-005-barski-barcelona", outlet: "Floodlight Forum", reporter: null, text: "Barcelona representatives met Barski's agent in Lisbon last week, according to two people present at the meeting.", timestamp: minutesAgo(800), attribution: "corroborating", language: "en", url: "https://floodlightforum.example/barski-lisbon" },
    { id: "c-005d", eventId: "e-005-barski-barcelona", outlet: "Transfer Window Daily", reporter: null, text: "Barcelona have AGREED personal terms with Viktor Barski ahead of a summer swoop.", timestamp: minutesAgo(850), attribution: "original", language: "en", url: "https://transferwindowdaily.example/exclusive/barski-barcelona" },
  ],
  "e-006-cifuentes-westham": [
    { id: "c-006a", eventId: "e-006-cifuentes-westham", outlet: "Estadio Dispatch", reporter: "Mara Oduya", text: "Correction of record: West Ham's move for Andrés Cifuentes has collapsed: a medical issue ended the deal. The player remains at Lyon.", timestamp: minutesAgo(2600), attribution: "conflicting", language: "es", url: "https://estadiodispatch.example/cifuentes-correction" },
    { id: "c-006b", eventId: "e-006-cifuentes-westham", outlet: "Transfer Window Daily", reporter: null, text: "Cifuentes passed his West Ham medical on Monday. Announcement expected Friday.", timestamp: minutesAgo(2900), attribution: "conflicting", language: "en", url: "https://transferwindowdaily.example/cifuentes-medical" },
    { id: "c-006c", eventId: "e-006-cifuentes-westham", outlet: "Terrace Wire", reporter: "Dara Keane", text: "West Ham have completed the signing of Andrés Cifuentes on a four-year deal.", timestamp: minutesAgo(3050), attribution: "original", language: "en", url: "https://terracewire.example/football/cifuentes-done-deal" },
  ],
  "e-007-novak-liverpool": [
    { id: "c-007a", eventId: "e-007-novak-liverpool", outlet: "Floodlight Forum", reporter: null, text: "Talks between Liverpool and Novák's agent have centred on a package worth around £140,000 a week. Nothing has been signed.", timestamp: minutesAgo(3000), attribution: "corroborating", language: "en", url: "https://floodlightforum.example/novak-talks" },
    { id: "c-007b", eventId: "e-007-novak-liverpool", outlet: "Terrace Wire", reporter: "Dara Keane", text: "Novák's representatives were in Liverpool this week to discuss the shape of an extension.", timestamp: minutesAgo(3080), attribution: "corroborating", language: "en", url: "https://terracewire.example/novak-extension" },
    { id: "c-007c", eventId: "e-007-novak-liverpool", outlet: "The Woodwork", reporter: "Tom Whitcombe", text: "Liverpool have opened talks over a new contract for Karel Novák, whose current deal runs to 2026.", timestamp: minutesAgo(3120), attribution: "original", language: "en", url: "https://thewoodwork.example/football/novak-contract-talks" },
  ],
  "e-008-ferraz-city": [
    { id: "c-008a", eventId: "e-008-ferraz-city", outlet: "The Woodwork", reporter: "Tom Whitcombe", text: "Manchester City hold genuine interest in Thiago Ferraz. Personal terms are close but not final, and no club-to-club agreement exists.", timestamp: minutesAgo(900), attribution: "corroborating", language: "en", url: "https://thewoodwork.example/ferraz-city-interest" },
    { id: "c-008b", eventId: "e-008-ferraz-city", outlet: "Estadio Dispatch", reporter: "Mara Oduya", text: "Manchester City have agreed personal terms with Thiago Ferraz. The next step is club-to-club talks with Girona.", timestamp: minutesAgo(940), attribution: "original", language: "es", url: "https://estadiodispatch.example/football/ferraz-city-terms" },
  ],
  "e-009-sy-alnassr": [
    { id: "c-009a", eventId: "e-009-sy-alnassr", outlet: "Transfer Window Daily", reporter: null, text: "Al-Nassr are plotting a world-record €120m move for Amadou Sy.", timestamp: minutesAgo(5800), attribution: "original", language: "en", url: "https://transferwindowdaily.example/exclusive/sy-alnassr" },
  ],
  "e-010-brandt-brighton": [
    { id: "c-010a", eventId: "e-010-brandt-brighton", outlet: "The Woodwork", reporter: "Tom Whitcombe", text: "CONFIRMED: Brighton announce Luca Brandt on a five-year deal after a club-record £26m agreement.", timestamp: minutesAgo(1500), attribution: "corroborating", language: "en", url: "https://thewoodwork.example/football/brandt-brighton-confirmed" },
    { id: "c-010b", eventId: "e-010-brandt-brighton", outlet: "Floodlight Forum", reporter: null, text: "Brandt has been registered with squad number 14. The announcement is set for Tuesday morning.", timestamp: minutesAgo(1560), attribution: "corroborating", language: "en", url: "https://floodlightforum.example/brandt-registration" },
    { id: "c-010c", eventId: "e-010-brandt-brighton", outlet: "Terrace Wire", reporter: "Dara Keane", text: "Brighton have agreed a club-record fee of £26m rising to £30m for Luca Brandt, with a five-year deal drafted.", timestamp: minutesAgo(2600), attribution: "corroborating", language: "en", url: "https://terracewire.example/brandt-fee" },
    { id: "c-010d", eventId: "e-010-brandt-brighton", outlet: "The Woodwork", reporter: "Tom Whitcombe", text: "Brighton have agreed a club-record fee for Luca Brandt and booked his medical for Monday.", timestamp: minutesAgo(2720), attribution: "original", language: "en", url: "https://thewoodwork.example/brandt-medical" },
  ],
  "e-011-sy-newcastle": [
    { id: "c-011a", eventId: "e-011-sy-newcastle", outlet: "The Woodwork", reporter: "Tom Whitcombe", text: "No bid has been received for Amadou Sy. Intermediaries are floating a £45m figure to force movement.", timestamp: minutesAgo(200), attribution: "conflicting", language: "en", url: "https://thewoodwork.example/sy-no-bid" },
    { id: "c-011b", eventId: "e-011-sy-newcastle", outlet: "Transfer Window Daily", reporter: null, text: "Newcastle's £45m bid for Amadou Sy has been SUBMITTED: a decision is expected within days.", timestamp: minutesAgo(260), attribution: "corroborating", language: "en", url: "https://transferwindowdaily.example/sy-bid-submitted" },
    { id: "c-011c", eventId: "e-011-sy-newcastle", outlet: "Terrace Wire", reporter: "Dara Keane", text: "Newcastle have tabled a £45m offer for Amadou Sy as they look to get the deal done early.", timestamp: minutesAgo(310), attribution: "original", language: "en", url: "https://terracewire.example/football/sy-newcastle-bid" },
  ],
};