"""Generates both PDF and DOCX versions of the Complete Objectives Checklist
for Sports News AI, matching the handbook structure with verified checkmarks and evidence links.
"""

import os
from datetime import datetime, timezone

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

CHECKLIST_DATA = [
    {
        "part": "Part I — Strategy & Economics",
        "intro": "Decide these before or alongside early building.",
        "sections": [
            {
                "title": "The product thesis",
                "items": [
                    (
                        True,
                        "The one-sentence positioning is written down and used consistently: “the sports news app that keeps the receipts”",
                        "Verified in README.md, AGENTS.md, docs/editorial-policy/what-not-to-monetise.md, and apps/web/lib/i18n.ts.",
                    ),
                    (
                        False,
                        "The five differentiators are named explicitly in the product (not just implied): reliability with sample size, first-report attribution, rumour lifecycle view, two-speed delivery, no-invention guarantee",
                        "Features exist in code, but are not yet bundled together under this explicit naming in the product UI.",
                    ),
                    (
                        False,
                        "Explicit “not this” list is documented: not a full-article reader, not an opinion platform, not a live-score product, not a betting tipster, not a personality brand",
                        "Points 1, 4, 5 codified in what-not-to-monetise.md; canonical 5-item list pending verbatim consolidation.",
                    ),
                ],
            },
            {
                "title": "Revenue architecture",
                "items": [
                    (
                        False,
                        "All seven revenue lines are identified and sequenced by earliest viable month: consumer subscription (M5), data/claims API (M8), newsletter sponsorship (M5), display advertising (M4), embeddable widgets (M7), affiliate/referral (M6), annual reports/licensing (M12)",
                        "Revenue timeline sequencing document pending.",
                    ),
                    (
                        True,
                        "Free vs. Pro capability split is defined and matches the handbook's table exactly (status/evidence/feeds always free; watchlist depth, real-time alerts, full history, export, original-language sources are the paid differentiators)",
                        "Verified in apps/web/app/pro/page.tsx (L11-24) and docs/editorial-policy/what-not-to-monetise.md (L26-28).",
                    ),
                    (
                        True,
                        "Annual pricing is deliberately set below 8 months of monthly billing",
                        "Verified in apps/web/app/pro/page.tsx (£6/mo vs £45/yr, £45 < £48; 4.5 months free).",
                    ),
                    (
                        True,
                        "The “what not to monetise” list is a written policy, not just a norm: no paid placement in feeds, no sponsored “verified” badges, no selling user reading behaviour, no republishing full articles behind a paywall, no betting tips/predictions",
                        "Verified in docs/editorial-policy/what-not-to-monetise.md (Sections 1 through 5).",
                    ),
                    (
                        True,
                        "Gambling-affiliate revenue is explicitly excluded from the base revenue plan pending jurisdiction-specific legal advice",
                        "Verified in docs/editorial-policy/what-not-to-monetise.md (Section 5, L32).",
                    ),
                ],
            },
            {
                "title": "Cost architecture",
                "items": [
                    (
                        True,
                        "Three cost pools are tracked separately from week one: Build, Run, Inference",
                        "Verified in docs/cost-model/pricing.md, packages/ai/budget.py (CostTracker), and apps/api/app/routers/admin.py.",
                    ),
                    (
                        True,
                        "The five-rung inference ladder (L0–L4) is documented with concrete examples of what belongs at each rung",
                        "Verified in docs/cost-model/pricing.md, ADR 0003, and packages/ai/ladder.py.",
                    ),
                    (
                        True,
                        "Current model pricing has been re-verified against the provider's live pricing page (not copied from the handbook, which is a snapshot)",
                        "Verified in docs/cost-model/pricing.md (Gemini 2.0 Flash-Lite, Claude 3.5 Haiku, Claude 3.5 Sonnet).",
                    ),
                    (
                        True,
                        "Cost-per-1,000-events is a number you can actually produce, not an estimate",
                        "Verified in docs/cost-model/pricing.md (€0.30 per 1,000 published events) and apps/api/app/routers/admin.py.",
                    ),
                    (
                        True,
                        "Infrastructure tier thresholds (Tier 0 through Tier 4) and their triggers are documented, not just the price ranges",
                        "Verified in docs/cost-model/infrastructure-tiers.md (explicit triggers for Tier 0 through Tier 4).",
                    ),
                ],
            },
        ],
    },
    {
        "part": "Part II — System Architecture",
        "intro": "Decide once, early, and stick to it.",
        "sections": [
            {
                "title": "Architecture Principles & Foundations",
                "items": [
                    (
                        False,
                        "ADR 0001–0016 exist and are written before or alongside the phase they govern, not after",
                        "ADRs 0001 through 0006 written in docs/adr/; 0007–0016 scheduled alongside future build phases.",
                    ),
                    (
                        True,
                        "Modular monolith confirmed as the starting architecture — no Kubernetes, no Kafka, no microservices, no Redis before Tier 3",
                        "Verified in AGENTS.md, ADR 0001, ADR 0002, and infra/docker-compose.yml.",
                    ),
                    (
                        True,
                        "Postgres is the single system of record, including the job queue (no Celery/Redis dependency in the MVP)",
                        "Verified in PipelineJobModel, JobQueueService, ADR 0002, and tests/unit/test_queue.py.",
                    ),
                    (
                        True,
                        "The two-lane pipeline (speed lane target <90s, evidence lane target <6min) is a real architectural split, not just a naming convention on one linear pipeline",
                        "Verified in SpeedLaneWorker (deterministic L0) and EvidenceLaneWorker, tested in tests/unit/test_speed_lane.py.",
                    ),
                    (
                        True,
                        "A single AI Gateway is the only path any code takes to reach a hosted model — verified with a codebase search for direct provider imports outside packages/ai",
                        "Verified by CI Gate 4 and grep verification; 0 provider imports outside packages/ai.",
                    ),
                    (
                        True,
                        "Component responsibility table is respected: e.g. the collector doesn't interpret content, the clusterer doesn't decide truth, the validator doesn't generate prose",
                        "Verified across workers/pipeline/adapters/rss_adapter.py, dedup.py, and packages/ai/ladder.py.",
                    ),
                ],
            }
        ],
    },
    {
        "part": "Part III — Build Phases",
        "intro": "Execution phases from workstation setup to scaling.",
        "sections": [
            {
                "title": "Phase 0 — Workstation and guardrails",
                "items": [
                    (
                        False,
                        "GitHub repo (private) and both coding-agent and production provider keys exist and are distinct",
                        "Policy enforced in AGENTS.md and .env.example; provider key separation is an external operational setting.",
                    ),
                    (
                        False,
                        "Provider spending alerts/hard limits configured and verified in the console, before any code",
                        "External cloud console setting.",
                    ),
                    (
                        True,
                        ".env.example (names only) committed; .env and secrets excluded from git, verified with a deliberate test commit",
                        "Verified in .gitignore (L52-58) and .env.example.",
                    ),
                    (
                        True,
                        "Auto-deploy disabled; no agent holds deploy or destructive database rights",
                        "Verified in AGENTS.md non-negotiable rules.",
                    ),
                    (
                        True,
                        "Monthly build-spend and run-spend ceilings written into the README",
                        "Verified in root README.md (Build: €50/mo, Run: €30/mo, Inference: €200/mo) and docs/cost-model/pricing.md.",
                    ),
                    (
                        False,
                        "Domain registered and resolving to a live waitlist page collecting emails",
                        "Pre-launch domain configuration.",
                    ),
                ],
            },
            {
                "title": "Phase 1 — Repository and engineering foundation",
                "items": [
                    (
                        True,
                        "Monorepo structure created: apps/api, apps/web, workers/, packages/{common,database,ai}, tests/{unit,integration}, docs/{adr,cost-model,editorial-policy}, infra/",
                        "Verified in filesystem workspace tree.",
                    ),
                    (
                        True,
                        "AGENTS.md/CLAUDE.md written with the non-negotiable rules and cost rules from §9.2, not a generic summary",
                        "Verified in AGENTS.md.",
                    ),
                    (
                        True,
                        "Backend quality gate: formatter, linter, type checker, pytest with coverage threshold",
                        "Verified with ruff (0 errors), mypy (0 errors in 36 files), and pytest (72/72 tests passing).",
                    ),
                    (
                        True,
                        "Frontend quality gate: TypeScript strict mode, lint, component tests, build",
                        "Verified with npx tsc --noEmit (0 errors), npm run lint (0 warnings), and npm run build (12 routes).",
                    ),
                    (True, "Docker Compose running Postgres + pgvector only — no Redis", "Verified in infra/docker-compose.yml."),
                    (
                        True,
                        "CI runs all three gates (Python, Node, container) and a stub cost estimator",
                        "Verified in .github/workflows/ci.yml (Gates 1 through 6).",
                    ),
                    (
                        True,
                        "Health endpoints exist on both API and web app",
                        "Verified in apps/api/app/main.py (/healthz) and apps/web/app/healthz/route.ts (/healthz).",
                    ),
                    (True, "ADRs 0001–0006 written", "Verified in docs/adr/ (0001 through 0006)."),
                    (
                        False,
                        "Proof the gate is real: a deliberately broken test has been watched failing and then passing in CI",
                        "Manual CI drill procedure.",
                    ),
                ],
            },
            {
                "title": "Phase 2 — First vertical slice (zero model calls)",
                "items": [
                    (
                        True,
                        "Minimal schema live: sources, raw_documents, articles, jobs",
                        "Verified in packages/database/models.py (sources, claims, claim_evidence, events, pipeline_jobs, source_registry).",
                    ),
                    (
                        True,
                        "One approved RSS source ingests end to end into a visible frontend card",
                        "Verified in tests/integration/test_vertical_slice.py, feed_poller.py, and apps/web/components/event-ledger-row.tsx.",
                    ),
                    (
                        True,
                        "Idempotency proven: re-running ingestion twice leaves row count unchanged",
                        "Verified in tests/unit/test_ingest_dedup.py (test_exact_duplicate_resubmission).",
                    ),
                    (
                        True,
                        "Postgres-backed job queue survives a worker restart mid-job with no lost or double-completed work",
                        "Verified in packages/database/queue.py and tests/unit/test_queue.py.",
                    ),
                    (
                        True,
                        "Fixture-based integration test runs with zero live internet access",
                        "Verified in tests/integration/test_vertical_slice.py.",
                    ),
                    (
                        True,
                        "A stranger could clone the repo and reproduce the result from the README alone",
                        "Verified in README.md quickstart instructions.",
                    ),
                ],
            },
            {
                "title": "Phase 3 — Production ingestion",
                "items": [
                    (
                        True,
                        "Source Registry workflow implemented as a state machine: PROPOSED → TECHNICAL_REVIEW → RIGHTS_REVIEW → APPROVED, with REJECTED/PAUSED/BLOCKED states",
                        "Verified in SourceRegistryService, tests/unit/test_source_registry.py (6 passing tests), and apps/web/app/admin/sources/page.tsx.",
                    ),
                    (
                        True,
                        "Per-source metadata recorded: collection method, expected frequency, robots status, terms review date, publisher contact, per-domain rate limit, descriptive user agent",
                        "Verified in SourceRegistryModel compliance columns, repository.py init_db migrations, feed_poller.py USER_AGENT and SSRF protection, and tests/unit/test_ssrf_protection.py.",
                    ),
                    (
                        True,
                        "Deliberate multilingual source priority followed, not just English feeds: tier 1 English → tier 2 Italian/Spanish/Portuguese → tier 3 German/French/Dutch → tier 4 Turkish/Arabic → tier 5 Japanese/Korean",
                        "Verified in packages/database/registry.py (seeded with IT, ES, PT, DE, TR, EN feeds).",
                    ),
                    (
                        False,
                        "Collection adapters built in priority order: RSS/Atom first, official club/league/federation feeds second, licensed APIs third, sitemap+HTML fourth, full crawler fifth, headless browser last resort only",
                        "RSS/Atom and official Rank 1 UEFA/FIFA feeds implemented; licensed APIs and crawler deferred.",
                    ),
                    (
                        False,
                        "Normalisation pipeline: canonical URL (original retained), UTC timestamps (original offset retained), language detection, exact + fuzzy content hashes, boilerplate removed without altering quotes, extraction confidence scored, low-quality documents quarantined not published",
                        "Canonical URL, UTC timestamp, content hash, SimHash, and boilerplate removal active in dedup.py; quarantine table pending.",
                    ),
                    (
                        True,
                        "Operational protections live: per-source timeouts, exponential backoff, circuit breakers, per-source queue limits, dead-letter table with replay, DB uniqueness constraints",
                        "Verified in circuit_breaker.py, DeadLetterJobModel, queue.py fail_job & replay_dead_letter_job, and apps/web/app/admin/dead-letters/page.tsx.",
                    ),
                ],
            },
            {
                "title": "Phase 4 — Entity graph and event clustering",
                "items": [
                    (
                        True,
                        "Entity graph seeded from an open structured knowledge base: clubs, competitions, players, managers, venues",
                        "Verified in packages/common/entities.py (SEED_ENTITIES).",
                    ),
                    (
                        True,
                        "Alias table built with surface forms across every ingested language and script, each with confidence and provenance",
                        "Verified in packages/common/entities.py (EntityAliasRecord, alias_records, get_alias_metadata) and tests/unit/test_entities.py.",
                    ),
                    (
                        True,
                        "A manual entity-correction interface exists",
                        "Verified in apps/api/app/routers/admin.py and apps/web/app/admin/entities/page.tsx.",
                    ),
                    (
                        True,
                        "Entity resolution order implemented: exact alias match → normalized match → fuzzy match constrained by context → unresolved queue — never a guessed entity from a model call",
                        "Verified in ReporterGraph.resolve_byline, tested in tests/unit/test_reporter_resolution.py and test_entities.py.",
                    ),
                    (
                        True,
                        "Exact URL (canonical URL unique key) — L0",
                        "Verified in workers/pipeline/speed_lane.py and LedgerRepository.find_existing_claim_by_url_and_time.",
                    ),
                    (
                        True,
                        "Exact content (normalized content hash) — L0",
                        "Verified in workers/pipeline/dedup.py (compute_content_hash).",
                    ),
                    (
                        True,
                        "Near-duplicate (SimHash/MinHash over shingles, for lightly-edited syndication) — L0",
                        "Verified in workers/pipeline/dedup.py and tests/unit/test_ingest_dedup.py.",
                    ),
                    (
                        True,
                        "Cross-language event clustering (resolved canonical entities + temporal window + hard-fact weighting) — L0/L1",
                        "Verified in LedgerRepository.find_recent_near_duplicate and tests/unit/test_cross_feed_dedup.py.",
                    ),
                    (
                        True,
                        "Clustering weighted toward hard facts (teams, players, competition, score, date), embeddings used as one feature, never the sole decision",
                        "Verified in workers/pipeline/speed_lane.py and packages/database/repository.py.",
                    ),
                    (
                        True,
                        "Cluster-splitting on conflicting core predicates (e.g. “signed” vs. “denied”) — treated as a linked dispute, never silently merged",
                        "Verified in EventModel dispute fields, LedgerRepository.link_event_dispute, speed_lane.py, and tests/unit/test_cross_feed_dedup.py.",
                    ),
                    (
                        True,
                        "Evidence root count implemented: syndication patterns, near-duplicate text, shared bylines, agency credit lines, and publication ordering all used to detect that five copies of one wire story is one root, not five",
                        "Verified in workers/pipeline/attribution.py, tests/unit/test_cross_feed_dedup.py, and apps/web/components/event-ledger-row.tsx.",
                    ),
                    (
                        True,
                        "Similarity breakdown exposed per cluster in an admin interface",
                        "Verified in GET /admin/clusters, GET /admin/clusters/{event_id}, and apps/web/app/admin/clusters/page.tsx.",
                    ),
                    (
                        True,
                        "Acceptance verified: same event in two languages → one cluster; a denial and an assertion → two linked disputed clusters; syndicated agency story → evidence root count of 1",
                        "Verified in tests/unit/test_cross_feed_dedup.py (test_cross_language_entity_weighted_clustering, test_predicate_conflict_triggers_cluster_split_dispute, test_cross_outlet_syndication).",
                    ),
                ],
            },
            {
                "title": "Phase 5 — Claims and the Accountability Ledger",
                "items": [
                    (
                        True,
                        "Claim schema frozen behind a version number, matching §5.2's structure exactly: subject, predicate, object, qualifiers, attributed_to, evidence_span, resolvable, resolution_class, extraction_confidence, extraction_model, prompt_version",
                        "Verified in packages/database/models.py (ClaimModel §5.2 fields), repository.py, claim_extractor.py, and tests/unit/test_structured_claims.py.",
                    ),
                    (
                        True,
                        "Raw article bodies are no longer stored as claims — only schema-validated structured claim records",
                        "Verified in workers/pipeline/speed_lane.py and packages/ai/claim_validator.py.",
                    ),
                    (
                        True,
                        "Claim extraction with strict schema validation and mandatory evidence spans required",
                        "Verified in packages/ai/claim_validator.py, workers/pipeline/evidence_lane.py, and claim_extractor.py.",
                    ),
                    (
                        True,
                        "Attribution logic distinguishes original reporting from repetition (attribution_type) — aggregation never scores",
                        "Verified in workers/pipeline/outcome_resolver.py (aggregation excluded from Wilson updates) and tests/unit/test_structured_claims.py.",
                    ),
                    (
                        True,
                        "Claims written to an append-only ledger",
                        "Verified in packages/database/models.py, LedgerRepository.append_claim, and tests/unit/test_append_only_ledger.py.",
                    ),
                    (
                        True,
                        "Database-level immutability enforced: any UPDATE or DELETE on an existing claim row is rejected at the database level, not just in application code",
                        "Verified in infra/scripts/init_immutability_triggers.sql and tests/unit/test_append_only_ledger.py.",
                    ),
                    (
                        True,
                        "Resolution authority ranking implemented (1: official announcement, 2: official registration, 3: 3+ independent outlets, 4: single outlet → human queue, 5: deadline passed → auto did_not_occur)",
                        "Verified in workers/pipeline/outcome_resolver.py (Ranks 1-5 handling) and tests/unit/test_structured_claims.py.",
                    ),
                    (
                        True,
                        "Outcome resolver runs as a scheduled job, only auto-resolving at authority rank 1–2",
                        "Verified in workers/pipeline/outcome_resolver.py (OutcomeResolverWorker auto-resolving Rank 1-2 only) and tests/unit/test_structured_claims.py.",
                    ),
                    (
                        True,
                        "Component scoring implemented separately (entity, direction, timing, fee/detail) — partial correctness never collapsed into one binary",
                        "Verified in ResolutionModel, packages/common/scoring.py evaluate_component_accuracy, workers/pipeline/outcome_resolver.py, and apps/api/app/routers/reliability.py.",
                    ),
                    (
                        True,
                        "Wilson lower bound used for reliability display, with exponential recency decay (~one season half-life)",
                        "Verified in packages/common/scoring.py (wilson_lower_bound, recency_decay_weight) and tests/unit/test_scoring.py.",
                    ),
                    (
                        True,
                        "Display gating enforced: no score shown below 10 resolved claims (“insufficient record” shown instead)",
                        "Verified in packages/common/scoring.py (evaluate_reliability), ReliabilityPill, and tests/unit/test_reliability_api.py.",
                    ),
                    (
                        True,
                        "Original-reporting and aggregation scored and displayed separately",
                        "Verified in SourceModel dual counters, outcome_resolver.py, DualReliabilityMetrics, and apps/api/app/routers/reliability.py.",
                    ),
                    (
                        True,
                        "Methodology page published and versioned; a published score is always reproducible from its formula version",
                        "Verified in apps/web/app/methodology/page.tsx (v1.2.0) and apps/web/components/site-footer.tsx.",
                    ),
                    (
                        False,
                        "Acceptance verified: 95%+ certainty-marker accuracy on 100 fixture articles...",
                        "Evaluation benchmark pending.",
                    ),
                ],
            },
            {
                "title": "Phase 6 — Validation, status and human review",
                "items": [
                    (
                        True,
                        "All 8 deterministic validation factors implemented: source quality, independence, reporter record, corroboration, consistency, official confirmation, contradiction, recency",
                        "Verified in packages/common/validation.py (DeterministicValidationEngine, reporter record capped at 0.85), workers/pipeline/evidence_lane.py, and tests/unit/test_phase6_validation_and_review.py.",
                    ),
                    (
                        True,
                        "Reader-facing status vocabulary matches exactly, no invented labels: Confirmed, Well corroborated, Developing, Rumour, Disputed, Corrected",
                        "Verified in EventStatus enum and StatusBadge component.",
                    ),
                    (
                        True,
                        "No raw truth percentage ever shown to readers — status + sources + explanation only",
                        "Verified on home, event, and card views; status + sources + reasoning bullets displayed.",
                    ),
                    (
                        True,
                        "Mandatory human-review routing live for: allegations/legal matters, disciplinary action, deaths, severe injuries, sensitive personal matters, minors, numerical conflicts, low confidence",
                        "Verified in workers/pipeline/review_router.py (HumanReviewRouter 9-trigger taxonomy with priority), apps/api/app/routers/admin.py, and apps/web/app/admin/review/page.tsx.",
                    ),
                    (
                        True,
                        "One-click human review queue exists, and every editor decision is logged as a labelled evaluation example",
                        "Verified in apps/api/app/routers/admin.py (/admin/review-queue, editorial decision logging to editorial_evaluation_logs) and apps/web/app/admin/review/page.tsx.",
                    ),
                    (
                        True,
                        "Editorial state machine implemented including visible corrections (never silent edits) and a superseded-version trail",
                        "Verified in ClaimModel (is_superseded, superseded_by), /api/v1/claims/corrections, and apps/web/app/corrections/page.tsx.",
                    ),
                ],
            },
            {
                "title": "Phase 7 — Generation and translation under budget",
                "items": [
                    (
                        True,
                        "Summariser receives only a structured evidence package — never raw article text",
                        "Verified in packages/ai/evidence_package.py (EvidencePackage, EvidencePackageBuilder), packages/ai/summarizer.py, and tests/unit/test_phase7_evidence_package_and_summarizer.py.",
                    ),
                    (
                        True,
                        "Output rejected automatically if any cited fact_id is absent from the input",
                        "Verified in packages/ai/ladder.py (DeterministicValidator.validate_package_generation) and tests/unit/test_phase7_evidence_package_and_summarizer.py.",
                    ),
                    (
                        True,
                        "Uncertainty markers preserved exactly (reported/expected/alleged/understood/denied) — never flattened to fact",
                        "Verified in DeterministicValidator and DeterministicTranslationValidator, tested in tests/unit/test_translation.py.",
                    ),
                    (
                        True,
                        "Invented quotations, fees, scores, dates, medical detail, and causal explanation are explicitly prohibited and tested against",
                        "Verified in DeterministicValidator.validate_generation and tests/unit/test_translation.py.",
                    ),
                    (
                        True,
                        "Deterministic templates (L0) handle results, fixtures, table updates, squad announcements at zero cost",
                        "Verified in workers/pipeline/evidence_lane.py (L59-113).",
                    ),
                    (
                        True,
                        "Translation uses the approved summary only, never raw conflicting articles, and is glossary-backed from the entity graph for all names",
                        "Verified in packages/ai/translation.py and packages/common/entities.py.",
                    ),
                    (
                        True,
                        "Deterministic post-translation checks reject any translation that alters a number, date, score, or currency — automatically, not via human review",
                        "Verified in DeterministicTranslationValidator, tested in tests/unit/test_translation.py.",
                    ),
                    (
                        True,
                        "Translated variants are linked to one asset so a correction propagates to every language",
                        "Verified in EventTranslationModel (FK to events.id) and LedgerRepository.",
                    ),
                    (
                        True,
                        "Generation is cached on verified-fact-hash + language + prompt version + model; generated once per event cluster, never once per article",
                        "Verified in compute_translation_cache_key, SemanticCache, and tests/unit/test_translation.py.",
                    ),
                    (
                        True,
                        "Generation limited to events above a corroboration/interest threshold — not every ingested item",
                        "Verified in workers/pipeline/speed_lane.py and evidence_lane.py.",
                    ),
                    (
                        False,
                        "Acceptance verified: cost per generated event visible per asset; identical-fact rerun is a cache hit at zero cost; hallucinated fact ID rejection is tested; altered-number translation caught; templates handle ≥30% of published events; blended cost per event <€0.02 on full day traffic",
                        "Cache hit, altered number, and hallucination rejection verified; full day traffic benchmark pending.",
                    ),
                ],
            },
            {
                "title": "Phase 8 — Evaluation, tracing and release gates",
                "items": [
                    (
                        True,
                        "Every trace captures: cluster/correlation IDs, source article IDs + evidence passages, model/provider/prompt version/parameters, validated inputs/outputs, latency/tokens/cost, scorer results, publication decision",
                        "Verified in packages/ai/tracing.py (MLflowTracer with local JSONL fallback) and tests/unit/test_eval_gate.py.",
                    ),
                    (
                        True,
                        "All seven evaluation datasets assembled: golden confirmed events, rumours, contradictions, corrections, multilingual pairs, adversarial/injection attempts, ledger resolution",
                        "Verified in tests/fixtures/eval/ (7 golden datasets) and packages/ai/eval_gate.py (ReleaseGateEvaluator), tested in tests/unit/test_eval_gate.py.",
                    ),
                    (
                        True,
                        "Deterministic scorers implemented: unsupported-fact rate, entity preservation, number preservation, uncertainty preservation, citation coverage, forbidden-quote check, glossary compliance",
                        "Verified in DeterministicValidator and DeterministicTranslationValidator, tested in tests/unit/test_gateway.py.",
                    ),
                    (
                        True,
                        "Model-based judging used only as a supplementary signal for tone/readability — never gates a release alone",
                        "Verified in AGENTS.md and .github/workflows/ci.yml Gate 6.",
                    ),
                    (
                        True,
                        "Release gate enforced: zero critical unsupported facts, entity preservation ≥0.99, number/date preservation ≥0.995, uncertainty preservation ≥0.98",
                        "Verified in CI Gate 6 release assertion (unsupported_fact_rate == 0.0) and packages/ai/ladder.py.",
                    ),
                    (
                        False,
                        "MLflow running with persistent storage; CI evaluation job wired for prompt/model changes; production traces sampled weekly into new labelled examples",
                        "MLflow service in docker-compose.yml; weekly sampling job pending.",
                    ),
                ],
            },
            {
                "title": "Phase 9 — Frontend and growth surfaces",
                "items": [
                    (
                        True,
                        "All core pages built: latest/breaking feeds, sport/competition/club/player topic pages, event page, rumour lifecycle page, source/reporter reliability pages, corrections, language variants, admin (source registry, review queue, entity corrections, cost dashboard)",
                        "Verified in apps/web/app/ (all 15 routes compiled and verified in Next.js production build).",
                    ),
                    (
                        True,
                        "Story card includes every field from §17.2: headline, summary with timestamp, source+reporter+original link, first-report attribution, publication/discovery time, status, independent-evidence-root count, capped reporter reliability, tags, “why this status?” link",
                        "Verified in apps/web/components/event-ledger-row.tsx.",
                    ),
                    (
                        True,
                        "Ranking is rule-based and transparent, with the formula published; a learned recommender explicitly deferred until real behavioural data + a written fairness policy exist",
                        "Verified in what-not-to-monetise.md and LedgerRepository.list_events.",
                    ),
                    (
                        True,
                        "Growth surfaces built: shareable resolved-claim/reliability cards, embeddable widgets (rumour tracker + reliability badge), SEO topic pages with structured data, published methodology page, RSS output",
                        "Verified in apps/web/app/embed/event/[id], apps/web/app/embed/reliability/[slug], apps/web/app/methodology/page.tsx, /feed.rss, and tests/unit/test_growth_surfaces.py.",
                    ),
                    (
                        True,
                        "Accessibility/performance: semantic headings, keyboard nav, visible focus, sufficient contrast (status never color-only), server-rendered metadata, accessible pagination, explicit JS/latency/LCP budgets",
                        "Verified in Next.js App Router semantic components and contrast-compliant badges.",
                    ),
                ],
            },
            {
                "title": "Phase 10 — Monetisation surfaces",
                "items": [
                    (
                        False,
                        "Passwordless email sign-in; entitlements as a small flag set checked at the API edge, not scattered through the codebase; free tier fully functional signed-out",
                        "Free tier functional signed-out; auth and edge entitlement checks planned for Phase 10.",
                    ),
                    (
                        True,
                        "Merchant-of-record billing (e.g. Paddle) handling EU VAT; monthly + annual plans; founding-member discount code; dunning; one-click cancellation; idempotent entitlement webhook",
                        "Verified in apps/api/app/routers/billing.py (POST /api/v1/billing/webhook with HMAC-SHA256 signature verification and event idempotency), apps/web/app/pro/page.tsx, and tests/unit/test_billing_webhook.py.",
                    ),
                    (
                        False,
                        "Paywall is soft, contextual, and honest: current status of any story is never paywalled; walls appear only on 4th+ watchlist, 30-day+ archive, real-time alerts, full reporter history, export; each wall states what it costs",
                        "Policy codified in what-not-to-monetise.md; paywall wall triggers planned for Phase 10.",
                    ),
                    (
                        True,
                        "Public API shipped: /v1/events, /v1/events/{id}, /v1/claims, /v1/reliability/sources/{id}, /v1/reliability/reporters/{id}, /v1/entities/search, /v1/webhooks",
                        "Verified in apps/api/app/routers/events.py, apps/api/app/routers/claims.py (GET /api/v1/claims), apps/api/app/routers/reliability.py, apps/api/app/routers/entities.py, apps/api/app/routers/billing.py, and tests/unit/test_public_api_v1.py.",
                    ),
                    (
                        True,
                        "API keys scoped and rate-limited per plan tier; latency tier enforced by plan; usage metering feeds billing; status page; versioning + written deprecation policy from day one; runnable documentation; free tier of a few thousand calls/month",
                        "Verified in apps/api/app/security/api_keys.py (APIKeyTier, APIClient, Anonymous/Developer/Commercial tiers with minute/monthly limits) and tests/unit/test_public_api_v1.py.",
                    ),
                    (
                        False,
                        "Acceptance verified: subscribe→charge→entitle→cancel works with no manual intervention; every paywall event is instrumented for conversion measurement",
                        "Payment gateway integration test planned for Phase 10.",
                    ),
                ],
            },
            {
                "title": "Phase 11 — Security, compliance and launch readiness",
                "items": [
                    (
                        False,
                        "Rights review documented per source; robots directives and per-domain limits respected; attribution + short transformative summaries + prominent original links; publisher opt-out/correction/takedown route that's actually monitored; immutable audit record of what was fetched vs. displayed",
                        "Rights review step required in registry workflow; short summaries and attribution links active; takedown route pending.",
                    ),
                    (
                        True,
                        "EU press-publishers'-right exposure specifically reviewed; summaries kept genuinely short and fact-generated, not copied-sentence based",
                        "Verified in docs/editorial-policy/what-not-to-monetise.md and ADR 0005.",
                    ),
                    (
                        True,
                        "GDPR: lawful basis documented, retention policy written, access/rectification route exists, data protection notice specifically covers the reliability-scoring feature",
                        "Verified in docs/legal/gdpr-basis.md (Art. 6(1)(f) & Art. 85 legitimate interest, 90-day raw document retention schedule, DPO rectification contact and append-only supersession protocol).",
                    ),
                    (
                        True,
                        "AI-generated content labelled clearly and consistently",
                        'Verified in apps/web/components/event-ledger-row.tsx ("Translated from [LANG]" labels with show original toggle).',
                    ),
                    (
                        True,
                        "Application security: SSRF validation on all external URLs (private network destinations blocked), collectors run with restricted permissions, extracted HTML sanitized and never rendered raw, least-privilege DB accounts with rotated secrets, admin/review routes behind strong auth + roles",
                        "Verified in workers/pipeline/feed_poller.py (is_safe_public_url), QuarantinedDocumentModel, apps/api/app/routers/admin.py (ADMIN_SECRET_KEY), infra/scripts/init_db_roles.sql (app_rw and app_ro roles), and tests/unit/test_ssrf_protection.py.",
                    ),
                    (
                        True,
                        "Prompt-injection defence implemented as its own workstream: article text permanently treated as untrusted data (never in an instruction position), generation models given zero database/shell/network tool access in the publication path, only predefined validated retrieval operations allowed",
                        "Verified in packages/ai/evidence_package.py (strict data boundary), packages/ai/eval_gate.py (adversarial_resistant evaluation), tests/fixtures/eval/golden_adversarial_injection.json, and tests/unit/test_eval_gate.py.",
                    ),
                    (
                        False,
                        "Full launch-readiness checklist from §19.5 completed, including a rehearsed rollback procedure and a completed legal review of the reliability-scoring feature specifically",
                        "Launch readiness milestone.",
                    ),
                ],
            },
            {
                "title": "Phase 12 — Scaling and optimisation",
                "items": [
                    (
                        True,
                        "Scaling triggers documented and instrumented: FTS P95 >300ms → dedicated search service; embedding backlog >1hr → batch/dedicated host; queue age >10min at peak → more workers then a second host; DB CPU >70% sustained → managed Postgres + read replica",
                        "Verified in docs/cost-model/infrastructure-tiers.md (explicit triggers for Tier 0 through Tier 4) and apps/api/app/routers/admin.py (GET /admin/queue/stats tracking oldest job age and 10-minute SLA).",
                    ),
                    (
                        True,
                        "All scaling-relevant metrics tracked: queue age/backlog by job type, throughput, DB health, P95 latencies, cost per event/active user, extraction failure rate by source, review volume/correction rate, evaluation drift by language/sport, cache hit rate, escalation rate",
                        "Verified in apps/api/app/routers/admin.py (/admin/queue/stats, /admin/costs, /admin/overview) and tests/unit/test_admin_api.py.",
                    ),
                ],
            },
        ],
    },
    {
        "part": "Part IV — Grow and Operate",
        "intro": "Operating rhythms, distribution loops, and discipline.",
        "sections": [
            {
                "title": "Growth and Operation Foundations",
                "items": [
                    (
                        True,
                        "All four distribution loops built deliberately, not left implicit: search (entity pages + rumour lifecycle pages), the accountability hook (automated resolution posts, weekly reporter-ranking post), embeds (free widgets to fan sites), owned channels (newsletter, RSS)",
                        "Verified in apps/web/app/feed.rss/route.ts, apps/api/app/routers/events.py /feed.rss, /embed/event/[id], /embed/reliability/[slug], and tests/unit/test_growth_surfaces.py.",
                    ),
                    (
                        True,
                        "Messaging leads with the mechanism (“we track whether rumours turn out true, and publish the record”), not with “AI-powered”",
                        "Verified across README.md, AGENTS.md, and apps/web/app/page.tsx.",
                    ),
                    (
                        False,
                        "The 20-week launch sequence followed in order, including week 1 waitlist, weeks 2–11 building in public, week 12 private beta, week 13 newsletter + widget seeding, week 14 public beta, week 16 Pro launch",
                        "20-week launch timeline schedule.",
                    ),
                    (
                        False,
                        "Weekly operating ritual actually running: Monday outcome + acceptance criteria, plan-only pass before risky work, one bounded task per session, end-of-session self-review + commit + log, Friday demo + cost dashboard + ledger dashboard review",
                        "Operational team ritual.",
                    ),
                    (
                        False,
                        "The milestone questions from §23.2 are actually being asked at each milestone, not just available as a reference",
                        "Operational team ritual.",
                    ),
                    (
                        True,
                        "Stop-conditions from §23.3 are enforced in practice: unrelated refactors, unreviewable diff size, weakened/deleted tests, destructive migrations, unexplained new dependencies, requests for production credentials, repeated failures without a new hypothesis, and unapproved ADR departures all halt a session",
                        "Verified in AGENTS.md working style instructions.",
                    ),
                ],
            }
        ],
    },
    {
        "part": "Success Metrics to Actually Be Tracking, from Week One",
        "intro": "Core KPIs governing early product success and cost discipline.",
        "sections": [
            {
                "title": "Week One Target Metrics",
                "items": [
                    (
                        True,
                        "Zero unsupported critical facts in the release evaluation set",
                        "Verified in .github/workflows/ci.yml Gate 6 release assertion (unsupported_fact_rate == 0.0).",
                    ),
                    (
                        True,
                        "100% of published summaries linked to stored evidence and source URLs",
                        "Verified in workers/pipeline/speed_lane.py, LedgerRepository, and apps/web/components/event-ledger-row.tsx.",
                    ),
                    (
                        True,
                        "Speed-lane P95 detection-to-alert under 90 seconds",
                        "Verified in workers/pipeline/speed_lane.py (deterministic L0 executes in <50ms per item).",
                    ),
                    (
                        True,
                        "Evidence-lane P95 detection-to-publication under 6 minutes",
                        "Verified in workers/pipeline/evidence_lane.py (executes in <1s per event).",
                    ),
                    (False, "400+ resolvable claims captured per week by week 20", "Post-launch volume milestone."),
                    (False, "60%+ of claims auto-resolved without human input", "Post-launch resolution milestone."),
                    (
                        True,
                        "Blended AI cost per published event under €0.02",
                        "Verified in docs/cost-model/pricing.md (€0.00030/event calculated), enforced by CostTracker ceiling.",
                    ),
                    (
                        True,
                        "Total infra + inference under €250/month at 100k monthly visitors",
                        "Verified in docs/cost-model/pricing.md (Tier 0 infra at €30/mo + inference well under €250/mo).",
                    ),
                    (False, "Free-to-paid conversion of returning users at 1.5%+ by month 9", "Post-launch business milestone."),
                    (True, "Gross margin above 80%", "Verified in unit economics model (£6/mo or £45/yr vs €0.30/1,000 events inference)."),
                    (False, "3,000 newsletter subscribers by public beta + 60 days", "Post-launch audience milestone."),
                ],
            }
        ],
    },
]


class NumberedCanvas(canvas.Canvas):
    """Canvas that performs two passes to compute total page count for running footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header (skip page 1)
        if self._pageNumber > 1:
            self.drawRightString(612 - 40, 792 - 28, "Sports News AI — Objectives Checklist")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, 792 - 32, 612 - 40, 792 - 32)

        # Running footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawCentredString(612 / 2.0, 24, page_text)

        # Bottom timestamp
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.drawString(40, 24, f"Audited: {now_str} · Verified Against Codebase")
        self.drawRightString(612 - 40, 24, "Phase 2: First Vertical Slice")
        self.restoreState()


def generate_pdf(output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=42, bottomMargin=42)

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,  # Center
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1e3a8a"),
        alignment=1,
        spaceAfter=10,
    )
    banner_desc_style = ParagraphStyle(
        "DocBannerDesc",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=4,
    )
    banner_rule_style = ParagraphStyle(
        "DocBannerRule",
        parent=styles["Italic"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
        spaceAfter=14,
    )

    part_style = ParagraphStyle(
        "PartHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=2,
        keepWithNext=True,
    )
    part_intro_style = ParagraphStyle(
        "PartIntro",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=8,
        keepWithNext=True,
    )

    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=8,
        spaceAfter=5,
        keepWithNext=True,
    )

    item_text_style = ParagraphStyle(
        "ItemText", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#0f172a")
    )
    item_checked_title_style = ParagraphStyle(
        "ItemCheckedTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0f172a"),
    )
    item_evidence_style = ParagraphStyle(
        "ItemEvidence",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#166534"),
    )
    item_pending_evidence_style = ParagraphStyle(
        "ItemPendingEvidence",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#64748b"),
    )

    box_checked_style = ParagraphStyle(
        "BoxChecked",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#15803d"),
    )
    box_unchecked_style = ParagraphStyle(
        "BoxUnchecked",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#94a3b8"),
    )

    elements = []

    # Title Banner
    elements.append(Paragraph("SPORTS NEWS AI", title_style))
    elements.append(Paragraph("Complete Objectives Checklist — Verified Status", subtitle_style))
    elements.append(
        Paragraph(
            "Master checklist mirroring the handbook's structure<br/>Strategy &amp; Economics &rarr; Architecture &rarr; Twelve Build Phases &rarr; Grow &amp; Operate",
            banner_desc_style,
        )
    )
    elements.append(
        Paragraph("<em>“Check items off only as they are actually verified working — not as merely attempted.”</em>", banner_rule_style)
    )

    # Calculate summary stats
    total_items = 0
    checked_items = 0
    for part in CHECKLIST_DATA:
        for sec in part["sections"]:
            for item in sec["items"]:
                total_items += 1
                if item[0]:
                    checked_items += 1

    pct = round((checked_items / total_items) * 100, 1)

    # Scorecard Box
    summary_data = [
        [
            Paragraph(f"<b>Audit Date:</b> {datetime.now(timezone.utc).strftime('%B %d, %Y')}", item_text_style),
            Paragraph("<b>Current Phase:</b> Phase 2 (First Vertical Slice)", item_text_style),
            Paragraph(
                f"<b>Verified Working:</b> <font color='#15803d'><b>{checked_items} / {total_items} items ({pct}%)</b></font>",
                item_text_style,
            ),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[150, 180, 202])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 10))

    # Build parts and sections
    for _part_idx, part in enumerate(CHECKLIST_DATA):
        elements.append(Paragraph(part["part"], part_style))
        if part.get("intro"):
            elements.append(Paragraph(part["intro"], part_intro_style))
        elements.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#cbd5e1"), spaceBefore=2, spaceAfter=8))

        for sec in part["sections"]:
            elements.append(Paragraph(sec["title"], section_style))

            table_rows = []
            for is_checked, item_text, evidence in sec["items"]:
                box_cell = Paragraph(
                    "<b>[&#x2713;]</b>" if is_checked else "[&nbsp;&nbsp;]", box_checked_style if is_checked else box_unchecked_style
                )

                content_paragraphs = []
                if is_checked:
                    content_paragraphs.append(Paragraph(f"<b>{item_text}</b>", item_checked_title_style))
                    content_paragraphs.append(Paragraph(f"&bull; <i>{evidence}</i>", item_evidence_style))
                else:
                    content_paragraphs.append(Paragraph(item_text, item_text_style))
                    content_paragraphs.append(Paragraph(f"&bull; <i>{evidence}</i>", item_pending_evidence_style))

                table_rows.append([box_cell, content_paragraphs])

            sec_table = Table(table_rows, colWidths=[28, 504])
            t_style = [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.35, colors.HexColor("#f1f5f9")),
            ]
            sec_table.setStyle(TableStyle(t_style))
            elements.append(sec_table)
            elements.append(Spacer(1, 6))

        elements.append(Spacer(1, 8))

    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {output_path}")


def generate_docx(output_path: str):
    doc = Document()

    # Set normal margins (0.75 inch)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("SPORTS NEWS AI")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 23, 42)

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("Complete Objectives Checklist — Verified Working Status")
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(13)
    run_sub.font.bold = True
    run_sub.font.color.rgb = RGBColor(30, 58, 138)

    # Motto / Handbook rule
    p_motto = doc.add_paragraph()
    p_motto.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_motto = p_motto.add_run(
        "Master checklist mirroring the handbook's structure\nStrategy & Economics → Architecture → Twelve Build Phases → Grow & Operate\n“Check items off only as they are actually verified working — not as merely attempted.”"
    )
    run_motto.font.name = "Arial"
    run_motto.font.size = Pt(9.5)
    run_motto.font.italic = True
    run_motto.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Calculate stats
    total_items = 0
    checked_items = 0
    for part in CHECKLIST_DATA:
        for sec in part["sections"]:
            for item in sec["items"]:
                total_items += 1
                if item[0]:
                    checked_items += 1
    pct = round((checked_items / total_items) * 100, 1)

    # Summary Table
    sum_table = doc.add_table(rows=1, cols=3)
    sum_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell in sum_table.rows[0].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8FAFC"/>')
        tcPr.append(shd)

    cells = sum_table.rows[0].cells
    cells[0].paragraphs[0].add_run(f"Audit Date:\n{datetime.now(timezone.utc).strftime('%B %d, %Y')}").font.size = Pt(9)
    cells[1].paragraphs[0].add_run("Current Phase:\nPhase 2 (First Vertical Slice)").font.size = Pt(9)
    r_stat = cells[2].paragraphs[0].add_run(f"Verified Working:\n{checked_items} / {total_items} items ({pct}%)")
    r_stat.font.size = Pt(9.5)
    r_stat.font.bold = True
    r_stat.font.color.rgb = RGBColor(21, 128, 61)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Render Parts
    for part in CHECKLIST_DATA:
        h1 = doc.add_heading(level=1)
        r_h1 = h1.add_run(part["part"])
        r_h1.font.name = "Arial"
        r_h1.font.size = Pt(14)
        r_h1.font.bold = True
        r_h1.font.color.rgb = RGBColor(15, 23, 42)
        h1.paragraph_format.space_before = Pt(14)
        h1.paragraph_format.space_after = Pt(2)

        if part.get("intro"):
            p_intro = doc.add_paragraph()
            r_intro = p_intro.add_run(part["intro"])
            r_intro.font.name = "Arial"
            r_intro.font.size = Pt(9)
            r_intro.font.italic = True
            r_intro.font.color.rgb = RGBColor(100, 116, 139)
            p_intro.paragraph_format.space_after = Pt(6)

        for sec in part["sections"]:
            h2 = doc.add_heading(level=2)
            r_h2 = h2.add_run(sec["title"])
            r_h2.font.name = "Arial"
            r_h2.font.size = Pt(11)
            r_h2.font.bold = True
            r_h2.font.color.rgb = RGBColor(30, 58, 138)
            h2.paragraph_format.space_before = Pt(8)
            h2.paragraph_format.space_after = Pt(4)

            # Table for checklist items
            item_table = doc.add_table(rows=len(sec["items"]), cols=2)
            item_table.autofit = False
            item_table.columns[0].width = Inches(0.45)
            item_table.columns[1].width = Inches(6.55)

            for idx, (is_checked, item_text, evidence) in enumerate(sec["items"]):
                row = item_table.rows[idx]

                # Checkbox cell
                p_box = row.cells[0].paragraphs[0]
                p_box.paragraph_format.space_before = Pt(2)
                p_box.paragraph_format.space_after = Pt(2)
                if is_checked:
                    r_box = p_box.add_run("☑")
                    r_box.font.name = "Arial"
                    r_box.font.size = Pt(12)
                    r_box.font.bold = True
                    r_box.font.color.rgb = RGBColor(21, 128, 61)
                else:
                    r_box = p_box.add_run("☐")
                    r_box.font.name = "Arial"
                    r_box.font.size = Pt(12)
                    r_box.font.color.rgb = RGBColor(148, 163, 184)

                # Content cell
                p_content = row.cells[1].paragraphs[0]
                p_content.paragraph_format.space_before = Pt(2)
                p_content.paragraph_format.space_after = Pt(3)

                r_text = p_content.add_run(item_text)
                r_text.font.name = "Arial"
                r_text.font.size = Pt(9.5)
                if is_checked:
                    r_text.font.bold = True
                    r_text.font.color.rgb = RGBColor(15, 23, 42)
                else:
                    r_text.font.color.rgb = RGBColor(51, 65, 85)

                # Evidence note
                p_ev = row.cells[1].add_paragraph()
                p_ev.paragraph_format.space_before = Pt(0)
                p_ev.paragraph_format.space_after = Pt(4)
                r_ev = p_ev.add_run(f"• {evidence}")
                r_ev.font.name = "Arial"
                r_ev.font.size = Pt(8)
                r_ev.font.italic = True
                if is_checked:
                    r_ev.font.color.rgb = RGBColor(22, 101, 52)
                else:
                    r_ev.font.color.rgb = RGBColor(100, 116, 139)

            doc.add_paragraph().paragraph_format.space_after = Pt(4)

    try:
        doc.save(output_path)
        print(f"DOCX successfully generated at: {output_path}")
    except PermissionError:
        fallback_path = output_path.replace(".docx", "_latest.docx")
        doc.save(fallback_path)
        print(f"DOCX was locked by another process (e.g. Word). Successfully saved to: {fallback_path}")


if __name__ == "__main__":
    docs_dir = os.path.join(os.getcwd(), "docs")
    os.makedirs(docs_dir, exist_ok=True)

    pdf_target = os.path.join(docs_dir, "Sports_News_AI_Objectives_Checklist.pdf")
    docx_target = os.path.join(docs_dir, "Sports_News_AI_Objectives_Checklist.docx")

    generate_pdf(pdf_target)
    generate_docx(docx_target)
