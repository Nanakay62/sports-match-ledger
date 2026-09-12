# Matchday Ledger: presentation build

An accountability ledger for transfer reporting: every claim timestamped and
attributed, resolved against the recorded outcome, and every source scored in
public.

## Run

    npm install
    npx shadcn@latest add button   # the only shadcn primitive used
    npm run dev

## Where things live

- `src/lib/types.ts`: all domain types
- `src/lib/mock-data/`: every fixture + all query helpers (`getAllEvents`,
  `getClaims`, `getTopic`, …). Replace this directory with an API layer and
  nothing else changes.
- `src/lib/status.ts`: the six status labels + styling, single source of truth
- `src/lib/evidence.ts`: the "Why this status?" reasoning engine
- `src/components/`: shared UI

## Rules encoded in the UI

- Statuses are exactly: Confirmed | Well corroborated | Developing | Rumour |
  Disputed | Corrected: never percentages, never new labels
- Reliability is always "x / y claims correct"; below 10 resolved claims renders
  the "insufficient record" state instead of a score
- Every entry shows source name, first-report attribution (when known), and a
  link to the original source
- The paywall gates only history depth, export, watchlist limits and real-time
  alerts: never a story's current status

All fixtures are fictional. `.example` source URLs are reserved placeholders.