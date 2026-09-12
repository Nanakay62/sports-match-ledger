import type { ReliabilityScore } from "@/lib/types";

// Category counts always sum exactly to sampleSize / correctCount.

export const reliabilityScores: ReliabilityScore[] = [
  {
    subjectName: "The Woodwork", subjectType: "outlet", sampleSize: 41, correctCount: 34,
    scoreByCategory: [
      { category: "Transfers: England", correct: 16, total: 19 },
      { category: "Transfers: Spain", correct: 7, total: 8 },
      { category: "Transfers: Italy", correct: 4, total: 5 },
      { category: "Managerial", correct: 3, total: 4 },
      { category: "Contracts", correct: 4, total: 5 },
    ],
    recentResolutions: [
      { claim: "Osei to Arsenal, five-year deal: announced three days after first report", outcome: "correct" },
      { claim: "Brandt fee a club record at £26m: confirmed", outcome: "correct" },
      { claim: "Novák contract talks opened: confirmed", outcome: "correct" },
      { claim: "Barski: no terms exchanged: matched the club's position", outcome: "correct" },
      { claim: "Lindqvist release clause set at €52m: clause is €58m", outcome: "incorrect" },
      { claim: "Ferraz terms “final”: close, but not final at check", outcome: "incorrect" },
    ],
  },
  {
    subjectName: "Terrace Wire", subjectType: "outlet", sampleSize: 34, correctCount: 21,
    scoreByCategory: [
      { category: "Transfers: England", correct: 9, total: 14 },
      { category: "Transfers: Spain", correct: 4, total: 6 },
      { category: "Transfers: Italy", correct: 3, total: 5 },
      { category: "Loans", correct: 2, total: 3 },
      { category: "Managerial", correct: 3, total: 6 },
    ],
    recentResolutions: [
      { claim: "Cifuentes “signed on a four-year deal”: deal collapsed", outcome: "incorrect" },
      { claim: "Duarte medical slot held for Thursday: slot existed", outcome: "correct" },
      { claim: "Brighton fee £26m rising to £30m: confirmed", outcome: "correct" },
      { claim: "Newcastle bid of £45m for Sy: no bid received", outcome: "incorrect" },
      { claim: "Novák's agent in Liverpool: confirmed", outcome: "correct" },
      { claim: "Bayern to sign Mori last summer: no move", outcome: "incorrect" },
    ],
  },
  {
    subjectName: "Estadio Dispatch", subjectType: "outlet", sampleSize: 33, correctCount: 27,
    scoreByCategory: [
      { category: "Transfers: Spain", correct: 12, total: 14 },
      { category: "Transfers: South America", correct: 6, total: 7 },
      { category: "Transfers: England", correct: 5, total: 6 },
      { category: "Contracts", correct: 4, total: 6 },
    ],
    recentResolutions: [
      { claim: "Barski denial: “no terms on the table”: held up", outcome: "correct" },
      { claim: "Osei fee €64m fixed in the regulator filing: confirmed", outcome: "correct" },
      { claim: "“Cifuentes remains at Lyon”: confirmed after the collapse", outcome: "correct" },
      { claim: "“Madrid out of the Lindqvist race”: talks since opened", outcome: "incorrect" },
      { claim: "Sy release clause €60m: clause is €45m plus bonuses", outcome: "incorrect" },
    ],
  },
  {
    subjectName: "Transfer Window Daily", subjectType: "outlet", sampleSize: 29, correctCount: 9,
    scoreByCategory: [
      { category: "Transfers: England", correct: 4, total: 12 },
      { category: "Transfers: Europe", correct: 2, total: 8 },
      { category: "Deadline day", correct: 1, total: 4 },
      { category: "Contracts", correct: 2, total: 5 },
    ],
    recentResolutions: [
      { claim: "Duarte to Chelsea “DONE DEAL”: not done", outcome: "incorrect" },
      { claim: "Barski terms “agreed”: denied by the club", outcome: "incorrect" },
      { claim: "Cifuentes medical “passed”: the move collapsed", outcome: "incorrect" },
      { claim: "“Osei to reject Arsenal”: he signed", outcome: "incorrect" },
      { claim: "Al-Nassr interest in Sy: agent confirmed contact", outcome: "correct" },
    ],
  },
  {
    subjectName: "Floodlight Forum", subjectType: "outlet", sampleSize: 4, correctCount: 3,
    scoreByCategory: [
      { category: "Transfers: England", correct: 2, total: 3 },
      { category: "Contracts", correct: 1, total: 1 },
    ],
    recentResolutions: [
      { claim: "Osei paperwork lodged: confirmed by the league", outcome: "correct" },
      { claim: "Lisbon meeting between Barski camp and Barça: corroborated", outcome: "correct" },
      { claim: "Cifuentes announcement “Friday”: never came", outcome: "incorrect" },
      { claim: "Brandt squad number 14: confirmed", outcome: "correct" },
    ],
  },
  {
    subjectName: "Mara Oduya", subjectType: "reporter", sampleSize: 21, correctCount: 19,
    affiliation: "Estadio Dispatch", beat: "Transfers: Spain & South America",
    scoreByCategory: [
      { category: "Transfers: Spain", correct: 11, total: 12 },
      { category: "Transfers: South America", correct: 5, total: 5 },
      { category: "Contracts", correct: 3, total: 4 },
    ],
    recentResolutions: [
      { claim: "Barski denial: held up", outcome: "correct" },
      { claim: "Cifuentes correction: verified against the record", outcome: "correct" },
      { claim: "Osei fee €64m fixed: confirmed", outcome: "correct" },
      { claim: "“Madrid out of Lindqvist race”: talks since opened", outcome: "incorrect" },
    ],
  },
  {
    subjectName: "Tom Whitcombe", subjectType: "reporter", sampleSize: 15, correctCount: 12,
    affiliation: "The Woodwork", beat: "Transfers: England",
    scoreByCategory: [
      { category: "Transfers: England", correct: 7, total: 9 },
      { category: "Loans", correct: 2, total: 2 },
      { category: "Managerial", correct: 3, total: 4 },
    ],
    recentResolutions: [
      { claim: "Osei medical completed: announced within 48h", outcome: "correct" },
      { claim: "Novák talks opened: confirmed", outcome: "correct" },
      { claim: "Barski: no terms exchanged: matched club position", outcome: "correct" },
      { claim: "Duarte payment structure “agreed”: not agreed", outcome: "incorrect" },
    ],
  },
  {
    subjectName: "Lena Vogt", subjectType: "reporter", sampleSize: 12, correctCount: 8,
    affiliation: "Terrace Wire", beat: "Bundesliga",
    scoreByCategory: [
      { category: "Bundesliga", correct: 5, total: 7 },
      { category: "Transfers: Europe", correct: 3, total: 5 },
    ],
    recentResolutions: [
      { claim: "Dahmen to extend at Gladbach: extended", outcome: "correct" },
      { claim: "Mori to Bayern in January: no move", outcome: "incorrect" },
      { claim: "Brandt release clause €22m: clause is €26m", outcome: "incorrect" },
    ],
  },
  {
    subjectName: "Dara Keane", subjectType: "reporter", sampleSize: 8, correctCount: 5,
    affiliation: "Terrace Wire", beat: "Transfers: England",
    scoreByCategory: [
      { category: "Transfers: England", correct: 4, total: 6 },
      { category: "Loans", correct: 1, total: 2 },
    ],
    recentResolutions: [
      { claim: "Cifuentes “signed”: the deal collapsed", outcome: "incorrect" },
      { claim: "Newcastle £45m bid tabled: no bid received", outcome: "incorrect" },
      { claim: "Duarte medical slot held: the slot existed", outcome: "correct" },
      { claim: "Brighton fee £26m + £4m add-ons: confirmed", outcome: "correct" },
    ],
  },
  {
    subjectName: "Sandro Ferri", subjectType: "reporter", sampleSize: 6, correctCount: 4,
    affiliation: "The Woodwork", beat: "Serie A",
    scoreByCategory: [
      { category: "Serie A", correct: 3, total: 4 },
      { category: "Transfers: Europe", correct: 1, total: 2 },
    ],
    recentResolutions: [
      { claim: "Fiorentina option on Barski: taken up", outcome: "correct" },
      { claim: "“Atalanta pre-agreement for Sy”: never signed", outcome: "incorrect" },
    ],
  },
];