# ADR-0015: VPS and Docker Compose Deployment; Scaling Triggers

## Status
Accepted

## Context
Handbook §3.4 and §7.4 both warn against provisioning for a platform the project doesn't have yet: "do not provision for the platform you hope to have... move up only when a metric forces you to." Without a written tier table, "should we scale now" becomes a judgement call made under the same pressure that produces premature infrastructure everywhere else.

## Decision
`infra/docker-compose.yml` runs the whole Tier 0 stack — Postgres (with pgvector), MLflow (ADR-0012) — as plain Docker Compose services with no orchestration layer, matching AGENTS.md's explicit instruction: "no Kubernetes, no Kafka, no microservices, no Redis before it's explicitly forced by a scaling trigger." `docs/cost-model/infrastructure-tiers.md` defines five tiers (Tier 0 at ~€30/month through Tier 4 at ~€2,500/month) each with an explicit traffic band, a concrete configuration, and a named metric-based trigger for moving up — e.g. "DB CPU > 60% sustained for 30 minutes" or "Queue P95 age > 2 minutes at peak," never a projection or a hunch. This is the broader deployment-tier progression; ADR-0002 already set the narrower, specific trigger for the job queue itself (sustained ingestion above 5,000 articles/minute, or worker coordination latency breaching SLA) and established that Redis is introduced *only* at Tier 3, and only as a cache/rate-limiter, never as the system of record.

## Consequences
- **Positive**: "should we scale" has a written, falsifiable answer — check the metric named in the trigger table, not a discussion. A single operator can stand up the entire Tier 0 stack from `infra/docker-compose.yml` with one command, matching the handbook's "understandable by one person at 2 a.m." design goal (§4.5).
- **Negative**: the tier cost figures in `docs/cost-model/infrastructure-tiers.md` are estimates for planning purposes, not a live pricing feed — they should be re-validated against actual provider pricing at the point a tier transition is actually being considered, the same caveat ADR-0007 makes about inference pricing.
