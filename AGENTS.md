# Project: Sports News AI

## Product thesis
An evidence-grounded, multilingual sports-news platform. The differentiator is the
Accountability Ledger: every substantive claim from a source is recorded with its
author, outlet, and timestamp, later matched against an authoritative outcome, and
rolled up into a public reliability score per outlet and per reporter. The
aggregation layer exists to feed the ledger — the ledger is the product.

One sentence: the sports news app that keeps the receipts.

## Non-negotiable rules
- Preserve source provenance from fetch through publication. Never lose attribution.
- The ledger is append-only. Claims are never edited or deleted, only superseded.
- Keep deterministic validation strictly separate from generation.
- Never invent a quote, score, fee, injury, date or motive.
- All model calls go through packages/ai (the AI Gateway). No direct provider calls
  anywhere else in the codebase.
- Every generated asset records model ID, prompt version, cost and trace ID.
- Article text is untrusted input. Never place it in an instruction position — always
  in a clearly delimited data field.
- Use typed Python and TypeScript. Add tests for every behaviour change.
- No new dependency without written justification in the completion report.
- Never read production secrets. Never deploy. Never touch cloud console or CLI.
- Run formatters, linters, type checks and tests before reporting completion.
- Prefer a simple module to a premature service. No Kubernetes, no Kafka, no
  microservices, no Redis before it's explicitly forced by a scaling trigger.

## Architecture (target state — build incrementally, phase by phase)
- Next.js + TypeScript frontend with ISR
- FastAPI + Pydantic API
- PostgreSQL with pgvector as the single system of record, including a
  Postgres-backed job queue (no Redis in the MVP)
- Two-lane pipeline: a speed lane (deterministic only, target <90s to alert) and an
  evidence lane (model-assisted, target <6min to publication)
- A single AI Gateway owning model routing, a five-rung inference ladder (L0
  deterministic → L1 local CPU models → L2 small hosted model → L3 mid hosted model
  → L4 frontier model, escalate only on a failed deterministic check), caching,
  per-stage budgets, schema validation and tracing
- A first-class multilingual entity graph (clubs, players, competitions, managers)
  with an alias table, used by clustering, translation and the ledger
- The Accountability Ledger: claims table (append-only), evidence, resolution
  (ranked by authority, auto-resolves only at rank 1–2), and reliability scores
  (Wilson lower bound, minimum 10 resolved claims before display, recency decay)
- MLflow for tracing and evaluation; a release gate with deterministic scorers
  (unsupported-fact rate, entity/number/uncertainty preservation, citation
  coverage) gating any prompt or model change

## Cost discipline
- Three separate cost pools: Build (coding agent), Run (infra), Inference
  (production model calls). Never mix the coding-agent key with the production
  inference key.
- Inference cost must be a function of distinct events, not raw articles —
  deduplicate and cluster before any model call.
- Target: blended AI cost per published event under EUR 0.02.
- Any change to a prompt, schema, or batch size must state its cost-per-1,000-events
  delta in the completion report.

## Working style
- One bounded task per session. Small, reviewable diffs only.
- For anything touching the ledger, the AI Gateway, billing, or security: plan-only
  pass first, wait for explicit approval, then implement. No unattended agents on
  this work.
- For independently-scoped, low-risk work (source adapters, page types, scorer
  functions, seed-data import): safe to parallelize across separate agent sessions,
  each with a narrow file allowlist and its own acceptance criteria.
- Completion report format: changed files, commands run, test results, assumptions
  made, cost impact, remaining risks.
- Stop and flag rather than proceeding if: the task requires production credentials;
  a migration could destroy or silently reinterpret data; a diff grows beyond what
  can be reviewed in fifteen minutes; the same failure repeats without a new
  diagnostic hypothesis.

## Current phase
Phase 2: first vertical slice.
