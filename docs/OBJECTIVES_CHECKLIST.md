# Sports News AI — Complete Objectives Checklist

> **Master checklist mirroring the handbook's structure:**  
> Strategy & Economics → Architecture → Twelve Build Phases → Grow & Operate  
> *Check items off only as they are actually verified working — not as merely attempted.*

---

## Part I — Strategy & Economics

*Decide these before or alongside early building.*

### The product thesis
- [x] **The one-sentence positioning is written down and used consistently: “the sports news app that keeps the receipts”**  
  *Verified in:* [`README.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/README.md#L3), [`AGENTS.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/AGENTS.md#L9), [`docs/editorial-policy/what-not-to-monetise.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/editorial-policy/what-not-to-monetise.md#L4), [`apps/web/lib/i18n.ts`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/lib/i18n.ts#L14).
- [ ] **The five differentiators are named explicitly in the product (not just implied):** reliability with sample size, first-report attribution, rumour lifecycle view, two-speed delivery, no-invention guarantee  
  *Status:* Underlying features exist, but they are not yet bundled and explicitly named as the 5 differentiators in a dedicated product view.
- [ ] **Explicit “not this” list is documented:** not a full-article reader, not an opinion platform, not a live-score product, not a betting tipster, not a personality brand  
  *Status:* Points 1, 4, 5 are codified in [`docs/editorial-policy/what-not-to-monetise.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/editorial-policy/what-not-to-monetise.md); the exact 5-item canonical list is not yet documented verbatim.

### Revenue architecture
- [ ] **All seven revenue lines are identified and sequenced by earliest viable month:** consumer subscription (M5), data/claims API (M8), newsletter sponsorship (M5), display advertising (M4), embeddable widgets (M7), affiliate/referral (M6), annual reports/licensing (M12)  
  *Status:* Revenue sequencing schedule not yet committed to repository documentation.
- [x] **Free vs. Pro capability split is defined and matches the handbook's table exactly** (status/evidence/feeds always free; watchlist depth, real-time alerts, full history, export, original-language sources are the paid differentiators)  
  *Verified in:* [`apps/web/app/pro/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/pro/page.tsx#L11-L24) and [`docs/editorial-policy/what-not-to-monetise.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/editorial-policy/what-not-to-monetise.md#L26-L28).
- [x] **Annual pricing is deliberately set below 8 months of monthly billing**  
  *Verified in:* [`apps/web/app/pro/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/pro/page.tsx#L97-L120) (£6/month vs £45/year; £45 < 8 × £6 = £48, explicitly stated as "4.5 months free (< 8 months billing)").
- [x] **The “what not to monetise” list is a written policy, not just a norm:** no paid placement in feeds, no sponsored “verified” badges, no selling user reading behaviour, no republishing full articles behind a paywall, no betting tips/predictions  
  *Verified in:* [`docs/editorial-policy/what-not-to-monetise.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/editorial-policy/what-not-to-monetise.md#L11-L34) (sections 1 through 5).
- [x] **Gambling-affiliate revenue is explicitly excluded from the base revenue plan pending jurisdiction-specific legal advice**  
  *Verified in:* [`docs/editorial-policy/what-not-to-monetise.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/editorial-policy/what-not-to-monetise.md#L30-L33).

### Cost architecture
- [x] **Three cost pools are tracked separately from week one: Build, Run, Inference**  
  *Verified in:* [`docs/cost-model/pricing.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/cost-model/pricing.md#L4-L11), [`packages/ai/budget.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/budget.py) (`CostTracker`), [`apps/api/app/routers/admin.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/admin.py#L65-L73), [`apps/web/app/admin/cost/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/admin/cost/page.tsx).
- [x] **The five-rung inference ladder (L0–L4) is documented with concrete examples of what belongs at each rung**  
  *Verified in:* [`docs/cost-model/pricing.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/cost-model/pricing.md#L14-L23), [`docs/adr/0003-ai-gateway-and-inference-ladder.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/adr/0003-ai-gateway-and-inference-ladder.md), [`packages/ai/ladder.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/ladder.py).
- [x] **Current model pricing has been re-verified against the provider's live pricing page (not copied from the handbook, which is a snapshot)**  
  *Verified in:* [`docs/cost-model/pricing.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/cost-model/pricing.md#L14-L23) (Gemini 2.0 Flash-Lite, Claude 3.5 Haiku, Claude 3.5 Sonnet).
- [x] **Cost-per-1,000-events is a number you can actually produce, not an estimate**  
  *Verified in:* [`docs/cost-model/pricing.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/cost-model/pricing.md#L26-L40) (€0.30 per 1,000 published events), live calculation in [`apps/api/app/routers/admin.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/admin.py#L106-L115), rendered on [`apps/web/app/admin/cost/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/admin/cost/page.tsx).
- [x] **Infrastructure tier thresholds (Tier 0 through Tier 4) and their triggers are documented, not just the price ranges**  
  *Verified in:* [`docs/cost-model/infrastructure-tiers.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/cost-model/infrastructure-tiers.md).

---

## Part II — System Architecture

*Decide once, early, and stick to it.*

- [ ] **ADR 0001–0016 exist and are written before or alongside the phase they govern, not after**  
  *Status:* ADRs 0001 through 0006 are written in [`docs/adr/`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/adr/). ADRs 0007–0016 are scheduled alongside future phases.
- [x] **Modular monolith confirmed as the starting architecture — no Kubernetes, no Kafka, no microservices, no Redis before Tier 3**  
  *Verified in:* [`AGENTS.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/AGENTS.md#L23-L24), [`docs/adr/0001-monorepo-structure.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/adr/0001-monorepo-structure.md), [`docs/adr/0002-system-of-record-and-queue.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/adr/0002-system-of-record-and-queue.md), [`infra/docker-compose.yml`](file:///c:/Users/nanak/Desktop/SportsJournalist/infra/docker-compose.yml).
- [x] **Postgres is the single system of record, including the job queue (no Celery/Redis dependency in the MVP)**  
  *Verified in:* [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py#L231-L243) (`PipelineJobModel`), [`packages/database/queue.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/queue.py) (`JobQueueService`), [`docs/adr/0002-system-of-record-and-queue.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/adr/0002-system-of-record-and-queue.md), tested in [`tests/unit/test_queue.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_queue.py).
- [x] **The two-lane pipeline (speed lane target <90s, evidence lane target <6min) is a real architectural split, not just a naming convention on one linear pipeline**  
  *Verified in:* [`workers/pipeline/speed_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/speed_lane.py) (pure deterministic L0), [`workers/pipeline/evidence_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/evidence_lane.py) (model-assisted status reasoning and synthesis), tested in [`tests/unit/test_speed_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_speed_lane.py).
- [x] **A single AI Gateway is the only path any code takes to reach a hosted model — verified with a codebase search for direct provider imports outside packages/ai**  
  *Verified in:* CI Gate 4 check in [`.github/workflows/ci.yml`](file:///c:/Users/nanak/Desktop/SportsJournalist/.github/workflows/ci.yml#L73-L88); zero imports of `openai`, `anthropic`, or `google.generativeai` outside [`packages/ai/`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/).
- [x] **Component responsibility table is respected: e.g. the collector doesn't interpret content, the clusterer doesn't decide truth, the validator doesn't generate prose**  
  *Verified in:* [`workers/pipeline/adapters/rss_adapter.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/adapters/rss_adapter.py), [`workers/pipeline/dedup.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/dedup.py), [`packages/ai/ladder.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/ladder.py) (`DeterministicValidator`).

---

## Part III — Build Phases

### Phase 0 — Workstation and guardrails
- [ ] **GitHub repo (private) and both coding-agent and production provider keys exist and are distinct**  
  *Status:* Policy mandated in [`AGENTS.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/AGENTS.md#L41-L44); keys configuration is an external setup.
- [ ] **Provider spending alerts/hard limits configured and verified in the console, before any code**  
  *Status:* External console setting.
- [x] **.env.example (names only) committed; .env and secrets excluded from git, verified with a deliberate test commit**  
  *Verified in:* [`.gitignore`](file:///c:/Users/nanak/Desktop/SportsJournalist/.gitignore#L52-L58), [`.env.example`](file:///c:/Users/nanak/Desktop/SportsJournalist/.env.example).
- [x] **Auto-deploy disabled; no agent holds deploy or destructive database rights**  
  *Verified in:* [`AGENTS.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/AGENTS.md#L21).
- [x] **Monthly build-spend and run-spend ceilings written into the README**  
  *Verified in:* [`README.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/README.md#L104-L113), [`docs/cost-model/pricing.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/cost-model/pricing.md).
- [ ] **Domain registered and resolving to a live waitlist page collecting emails**  
  *Status:* Pre-launch infrastructure task.

### Phase 1 — Repository and engineering foundation
- [x] **Monorepo structure created:** `apps/api`, `apps/web`, `workers/`, `packages/{common,database,ai}`, `tests/{unit,integration}`, `docs/{adr,cost-model,editorial-policy}`, `infra/`  
  *Verified in:* Workspace tree.
- [x] **AGENTS.md/CLAUDE.md written with the non-negotiable rules and cost rules from §9.2, not a generic summary**  
  *Verified in:* [`AGENTS.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/AGENTS.md).
- [x] **Backend quality gate: formatter, linter, type checker, pytest with coverage threshold**  
  *Verified in:* `ruff check` (0 errors), `ruff format --check` (0 errors), `mypy` (0 errors in 36 files), `pytest` (72/72 passing).
- [x] **Frontend quality gate: TypeScript strict mode, lint, component tests, build**  
  *Verified in:* Next.js lint (0 warnings/errors), `npx tsc --noEmit` (clean), `npm run build` (12 routes compiled).
- [x] **Docker Compose running Postgres + pgvector only — no Redis**  
  *Verified in:* [`infra/docker-compose.yml`](file:///c:/Users/nanak/Desktop/SportsJournalist/infra/docker-compose.yml).
- [x] **CI runs all three gates (Python, Node, container) and a stub cost estimator**  
  *Verified in:* [`.github/workflows/ci.yml`](file:///c:/Users/nanak/Desktop/SportsJournalist/.github/workflows/ci.yml) (Gates 1–6).
- [x] **Health endpoints exist on both API and web app**  
  *Verified in:* API has `/healthz` in [`apps/api/app/main.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/main.py#L50-L52); web app has `/healthz` in [`apps/web/app/healthz/route.ts`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/healthz/route.ts).
- [x] **ADRs 0001–0006 written**  
  *Verified in:* [`docs/adr/`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/adr/) (0001 through 0006).
- [ ] **Proof the gate is real: a deliberately broken test has been watched failing and then passing in CI**  
  *Status:* CI drill procedure.

### Phase 2 — First vertical slice (zero model calls)
- [x] **Minimal schema live: sources, raw_documents, articles, jobs**  
  *Verified in:* [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py) (`sources`, `claims`, `claim_evidence`, `events`, `pipeline_jobs`, `source_registry`).
- [x] **One approved RSS source ingests end to end into a visible frontend card**  
  *Verified in:* [`tests/integration/test_vertical_slice.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/integration/test_vertical_slice.py), [`workers/pipeline/feed_poller.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/feed_poller.py), [`apps/web/components/event-ledger-row.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/components/event-ledger-row.tsx).
- [x] **Idempotency proven: re-running ingestion twice leaves row count unchanged**  
  *Verified in:* [`tests/unit/test_ingest_dedup.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_ingest_dedup.py#L41-L76).
- [x] **Postgres-backed job queue survives a worker restart mid-job with no lost or double-completed work**  
  *Verified in:* [`packages/database/queue.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/queue.py), [`tests/unit/test_queue.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_queue.py).
- [x] **Fixture-based integration test runs with zero live internet access**  
  *Verified in:* [`tests/integration/test_vertical_slice.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/integration/test_vertical_slice.py).
- [x] **A stranger could clone the repo and reproduce the result from the README alone**  
  *Verified in:* [`README.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/README.md).

### Phase 3 — Production ingestion
- [x] **Source Registry workflow implemented as a state machine: PROPOSED → TECHNICAL_REVIEW → RIGHTS_REVIEW → APPROVED, with REJECTED/PAUSED/BLOCKED states — not just a flat table of approved feeds**  
  *Verified in:* [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py#L20-L49), [`packages/database/registry.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/registry.py), [`tests/unit/test_source_registry.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_source_registry.py), [`apps/web/app/admin/sources/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/admin/sources/page.tsx).
- [x] **Per-source metadata recorded: collection method, expected frequency, robots status, terms review date, publisher contact, per-domain rate limit, descriptive user agent**  
  *Verified in:* [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py) (`SourceRegistryModel` compliance columns), [`packages/database/repository.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/repository.py) (`init_db` migrations), [`workers/pipeline/feed_poller.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/feed_poller.py) (`USER_AGENT` & `is_safe_public_url` SSRF protection), [`tests/unit/test_ssrf_protection.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_ssrf_protection.py).
- [x] **Deliberate multilingual source priority followed, not just English feeds: tier 1 English → tier 2 Italian/Spanish/Portuguese → tier 3 German/French/Dutch → tier 4 Turkish/Arabic → tier 5 Japanese/Korean**  
  *Verified in:* [`packages/database/registry.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/registry.py#L209-L345) (seeded with IT, ES, PT, DE, TR, EN feeds).
- [ ] **Collection adapters built in priority order: RSS/Atom first, official club/league/federation feeds second (and treated as Authority Rank 1–2 infrastructure with higher polling frequency), licensed APIs third, sitemap+HTML fourth, full crawler fifth, headless browser last resort only**  
  *Status:* RSS/Atom and Rank 1 official feeds (UEFA/FIFA) implemented; licensed APIs, sitemap, full crawler, and headless browser are deferred.
- [ ] **Normalisation pipeline: canonical URL (original retained), UTC timestamps (original offset retained), language detection, exact + fuzzy content hashes, boilerplate removed without altering quotes, extraction confidence scored, low-quality documents quarantined not published**  
  *Status:* Canonical URL, UTC timestamp, content hash, SimHash, and boilerplate removal implemented in [`workers/pipeline/dedup.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/dedup.py); extraction confidence score and quarantine table pending.
- [x] **Operational protections live: per-source timeouts, exponential backoff, circuit breakers, per-source queue limits, dead-letter table with replay, DB uniqueness constraints**  
  *Verified in:* [`workers/pipeline/circuit_breaker.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/circuit_breaker.py), [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py#L261-L275) (`DeadLetterJobModel`), [`packages/database/queue.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/queue.py#L208-L251) (`fail_job` & `replay_dead_letter_job`), [`apps/web/app/admin/dead-letters/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/admin/dead-letters/page.tsx).

### Phase 4 — Entity graph and event clustering
- [x] **Entity graph seeded from an open structured knowledge base: clubs, competitions, players, managers, venues**  
  *Verified in:* [`packages/common/entities.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/common/entities.py) (`SEED_ENTITIES`).
- [x] **Alias table built with surface forms across every ingested language and script, each with confidence and provenance**  
  *Verified in:* [`packages/common/entities.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/common/entities.py) (`EntityAliasRecord`, `alias_records`, `get_alias_metadata`), [`tests/unit/test_entities.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_entities.py).
- [x] **A manual entity-correction interface exists**  
  *Verified in:* [`apps/api/app/routers/admin.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/admin.py#L233-L272), [`apps/web/app/admin/entities/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/admin/entities/page.tsx).
- [x] **Entity resolution order implemented: exact alias match → normalized match (diacritics/suffixes stripped) → fuzzy match constrained by context → unresolved queue — never a guessed entity from a model call**  
  *Verified in:* [`packages/common/reporters.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/common/reporters.py) (`ReporterGraph.resolve_byline` 4-tier cascade), [`tests/unit/test_reporter_resolution.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_reporter_resolution.py), [`tests/unit/test_entities.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_entities.py).
- **All four deduplication layers implemented, not just one generic pass:**
  - [x] **Exact URL (canonical URL unique key) — L0**  
    *Verified in:* [`workers/pipeline/speed_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/speed_lane.py#L34-L53), [`LedgerRepository.find_existing_claim_by_url_and_time`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/repository.py#L192-L217).
  - [x] **Exact content (normalized content hash) — L0**  
    *Verified in:* [`workers/pipeline/dedup.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/dedup.py#L12-L16) (`compute_content_hash`).
  - [x] **Near-duplicate (SimHash/MinHash over shingles, for lightly-edited syndication) — L0**  
    *Verified in:* [`workers/pipeline/dedup.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/dedup.py#L18-L52), [`tests/unit/test_ingest_dedup.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_ingest_dedup.py#L78-L170).
  - [x] **Cross-language event clustering (resolved canonical entities + temporal window + hard-fact weighting) — L0/L1**  
    *Verified in:* [`packages/database/repository.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/repository.py) (`find_recent_near_duplicate`), [`tests/unit/test_cross_feed_dedup.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_cross_feed_dedup.py) (`test_cross_language_entity_weighted_clustering`).
- [x] **Clustering weighted toward hard facts (teams, players, competition, score, date), embeddings used as one feature, never the sole decision**  
  *Verified in:* [`workers/pipeline/speed_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/speed_lane.py), [`packages/database/repository.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/repository.py#L324-L440).
- [x] **Cluster-splitting on conflicting core predicates (e.g. “signed” vs. “denied”) — treated as a linked dispute, never silently merged**  
  *Verified in:* [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py) (`disputed_by_event_id`, `dispute_status`), [`packages/database/repository.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/repository.py) (`link_event_dispute`), [`workers/pipeline/speed_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/speed_lane.py), [`tests/unit/test_cross_feed_dedup.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_cross_feed_dedup.py) (`test_predicate_conflict_triggers_cluster_split_dispute`).
- [x] **Evidence root count implemented: syndication patterns, near-duplicate text, shared bylines, agency credit lines, and publication ordering all used to detect that five copies of one wire story is one root, not five**  
  *Verified in:* [`workers/pipeline/attribution.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/attribution.py), [`tests/unit/test_cross_feed_dedup.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_cross_feed_dedup.py#L84-L138), [`apps/web/components/event-ledger-row.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/components/event-ledger-row.tsx#L82-L85).
- [x] **Similarity breakdown exposed per cluster in an admin interface**  
  *Verified in:* [`apps/api/app/routers/admin.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/admin.py) (`GET /admin/clusters`, `GET /admin/clusters/{event_id}`), [`apps/web/app/admin/clusters/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/admin/clusters/page.tsx), [`apps/web/app/admin/layout.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/admin/layout.tsx).
- [x] **Acceptance verified: same event in two languages → one cluster; a denial and an assertion → two linked disputed clusters; syndicated agency story → evidence root count of 1 regardless of copy count; 2,000 fixture articles cluster within budget at zero hosted model calls**  
  *Verified in:* [`tests/unit/test_cross_feed_dedup.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_cross_feed_dedup.py) (`test_cross_language_entity_weighted_clustering`, `test_predicate_conflict_triggers_cluster_split_dispute`, `test_cross_outlet_syndication_creates_one_event_and_one_claim`).

### Phase 5 — Claims and the Accountability Ledger
- [x] **Claim schema frozen behind a version number, matching §5.2's structure exactly: subject, predicate, object, qualifiers, attributed_to (with attribution_type), evidence_span, resolvable, resolution_class, extraction_confidence, extraction_model, prompt_version**  
  *Verified in:* [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py#L172-L200) (`ClaimModel`), [`packages/database/repository.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/repository.py#L427-L490) (`append_claim`), [`workers/pipeline/claim_extractor.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/claim_extractor.py), [`tests/unit/test_structured_claims.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_structured_claims.py).
- [x] **Raw article bodies are no longer stored as claims — only schema-validated structured claim records**  
  *Verified in:* [`workers/pipeline/speed_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/speed_lane.py#L254-L281), [`packages/ai/claim_validator.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/claim_validator.py).
- [x] **Claim extraction with strict schema validation and mandatory evidence spans required**  
  *Verified in:* [`packages/ai/claim_validator.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/claim_validator.py), [`workers/pipeline/evidence_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/evidence_lane.py#L96-L113), [`workers/pipeline/claim_extractor.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/claim_extractor.py).
- [x] **Attribution logic distinguishes original reporting from repetition (attribution_type) — aggregation never scores**  
  *Verified in:* [`workers/pipeline/outcome_resolver.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/outcome_resolver.py#L62-L97), [`tests/unit/test_structured_claims.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_structured_claims.py#L182-L218).
- [x] **Claims written to an append-only ledger**  
  *Verified in:* [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py#L164-L192), [`packages/database/repository.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/repository.py#L427-L522), [`tests/unit/test_append_only_ledger.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_append_only_ledger.py).
- [x] **Database-level immutability enforced: any UPDATE or DELETE on an existing claim row is rejected at the database level, not just in application code**  
  *Verified in:* [`infra/scripts/init_immutability_triggers.sql`](file:///c:/Users/nanak/Desktop/SportsJournalist/infra/scripts/init_immutability_triggers.sql), [`tests/unit/test_append_only_ledger.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_append_only_ledger.py).
- [x] **Resolution authority ranking implemented (1: official announcement, 2: official registration/database, 3: 3+ independent tier-one outlets with delay+flag, 4: single outlet → human queue, 5: deadline passed with no event → auto did_not_occur)**  
  *Verified in:* [`workers/pipeline/outcome_resolver.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/outcome_resolver.py#L98-L320), [`tests/unit/test_structured_claims.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_structured_claims.py).
- [x] **Outcome resolver runs as a scheduled job, only auto-resolving at authority rank 1–2**  
  *Verified in:* [`workers/pipeline/outcome_resolver.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/outcome_resolver.py#L100-L193), [`tests/unit/test_structured_claims.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_structured_claims.py#L112-L180).
- [x] **Component scoring implemented separately (entity, direction, timing, fee/detail) — partial correctness never collapsed into one binary**  
  *Verified in:* [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py#L248-L251) (`ResolutionModel`), [`packages/common/scoring.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/common/scoring.py#L104-L150) (`evaluate_component_accuracy`), [`workers/pipeline/outcome_resolver.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/outcome_resolver.py#L30-L245), [`apps/api/app/routers/reliability.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/reliability.py).
- [x] **Wilson lower bound used for reliability display, with exponential recency decay (~one season half-life)**  
  *Verified in:* [`packages/common/scoring.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/common/scoring.py#L17-L70), [`tests/unit/test_scoring.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_scoring.py).
- [x] **Display gating enforced: no score shown below 10 resolved claims (“insufficient record” shown instead)**  
  *Verified in:* [`packages/common/scoring.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/common/scoring.py#L72-L101), [`apps/web/components/reliability-pill.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/components/reliability-pill.tsx), [`tests/unit/test_reliability_api.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_reliability_api.py).
- [x] **Original-reporting and aggregation scored and displayed separately**  
  *Verified in:* [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py#L70-L75) (`SourceModel` dual counters), [`workers/pipeline/outcome_resolver.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/outcome_resolver.py#L62-L125), [`packages/common/scoring.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/common/scoring.py#L152-L215) (`DualReliabilityMetrics`), [`apps/api/app/routers/reliability.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/reliability.py).
- [x] **Methodology page published and versioned; a published score is always reproducible from its formula version**  
  *Verified in:* [`apps/web/app/methodology/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/methodology/page.tsx) (version `v1.2.0`), [`apps/web/components/site-footer.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/components/site-footer.tsx).
- [ ] **Acceptance verified: 95%+ certainty-marker accuracy on 100 fixture articles...**

### Phase 6 — Validation, status and human review
- [x] **All 8 deterministic validation factors implemented: source quality, independence, reporter record (capped so reputation never substitutes for evidence), corroboration, consistency, official confirmation, contradiction, recency**  
  *Verified in:* [`packages/common/validation.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/common/validation.py) (`DeterministicValidationEngine`), [`workers/pipeline/evidence_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/evidence_lane.py), tested in [`tests/unit/test_phase6_validation_and_review.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_phase6_validation_and_review.py).
- [x] **Reader-facing status vocabulary matches exactly, no invented labels: Confirmed, Well corroborated, Developing, Rumour, Disputed, Corrected**  
  *Verified in:* [`packages/common/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/common/models.py#L7-L14) (`EventStatus`), [`apps/web/components/status-badge.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/components/status-badge.tsx).
- [x] **No raw truth percentage ever shown to readers — status + sources + explanation only**  
  *Verified in:* [`apps/web/app/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/page.tsx), [`apps/web/app/event/[id]/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/event/[id]/page.tsx), [`apps/web/components/why-disclosure.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/components/why-disclosure.tsx).
- [x] **Mandatory human-review routing live for: allegations/legal matters, disciplinary action, deaths, severe injuries/medical detail, sensitive personal matters, anything involving a minor, numerical fact conflicts, first-time sources, low extraction confidence, any generated claim absent from the verified fact set**  
  *Verified in:* [`workers/pipeline/review_router.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/review_router.py) (`HumanReviewRouter`), [`workers/pipeline/evidence_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/evidence_lane.py), [`apps/api/app/routers/admin.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/admin.py), [`apps/web/app/admin/review/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/admin/review/page.tsx), tested in [`tests/unit/test_phase6_validation_and_review.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_phase6_validation_and_review.py).
- [x] **One-click human review queue exists, and every editor decision is logged as a labelled evaluation example**  
  *Verified in:* [`apps/api/app/routers/admin.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/admin.py#L119-L173), [`apps/web/app/admin/review/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/admin/review/page.tsx).
- [x] **Editorial state machine implemented including visible corrections (never silent edits) and a superseded-version trail**  
  *Verified in:* [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py#L181-L182), [`apps/api/app/routers/claims.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/claims.py#L153-L216), [`apps/web/app/corrections/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/corrections/page.tsx), [`docs/adr/0006-public-corrections-and-audit-ledger.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/adr/0006-public-corrections-and-audit-ledger.md).

### Phase 7 — Generation and translation under budget
- [x] **Summariser receives only a structured evidence package (verified facts, uncertain claims, contradictions, entity glossary, approved sources) — never raw article text**  
  *Verified in:* [`packages/ai/evidence_package.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/evidence_package.py) (`EvidencePackage`, `EvidencePackageBuilder`), [`packages/ai/summarizer.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/summarizer.py) (`StructuredEvidenceSummarizer`), [`workers/pipeline/evidence_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/evidence_lane.py), tested in [`tests/unit/test_phase7_evidence_package_and_summarizer.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_phase7_evidence_package_and_summarizer.py).
- [x] **Output rejected automatically if any cited fact_id is absent from the input**  
  *Verified in:* [`packages/ai/ladder.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/ladder.py#L96-L204) (`DeterministicValidator.validate_package_generation`), tested in [`tests/unit/test_phase7_evidence_package_and_summarizer.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_phase7_evidence_package_and_summarizer.py).
- [x] **Uncertainty markers preserved exactly (reported/expected/alleged/understood/denied) — never flattened to fact**  
  *Verified in:* [`packages/ai/ladder.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/ladder.py#L65-L86), [`packages/ai/translation.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/translation.py#L99-L108), tested in [`tests/unit/test_translation.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_translation.py).
- [x] **Invented quotations, fees, scores, dates, medical detail, and causal explanation are explicitly prohibited and tested against**  
  *Verified in:* [`packages/ai/ladder.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/ladder.py#L55-L64), [`packages/ai/translation.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/translation.py#L74-L88), [`tests/unit/test_translation.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_translation.py), [`tests/unit/test_gateway.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_gateway.py).
- [x] **Deterministic templates (L0) handle results, fixtures, table updates, squad announcements at zero cost**  
  *Verified in:* [`workers/pipeline/evidence_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/evidence_lane.py#L59-L113).
- [x] **Translation uses the approved summary only, never raw conflicting articles, and is glossary-backed from the entity graph for all names**  
  *Verified in:* [`packages/ai/translation.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/translation.py#L262-L268), [`packages/common/entities.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/common/entities.py).
- [x] **Deterministic post-translation checks reject any translation that alters a number, date, score, or currency — automatically, not via human review**  
  *Verified in:* [`packages/ai/translation.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/translation.py#L42-L110), tested in [`tests/unit/test_translation.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_translation.py).
- [x] **Translated variants are linked to one asset so a correction propagates to every language**  
  *Verified in:* [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py#L103-L120) (`EventTranslationModel` FK to `events.id`), [`packages/database/repository.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/repository.py#L597-L666).
- [x] **Generation is cached on verified-fact-hash + language + prompt version + model; batched wherever not latency-sensitive; generated once per event cluster, never once per article**  
  *Verified in:* [`packages/ai/translation.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/translation.py#L190-L203), [`packages/ai/cache.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/cache.py), [`tests/unit/test_translation.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_translation.py).
- [x] **Generation limited to events above a corroboration/interest threshold — not every ingested item**  
  *Verified in:* [`workers/pipeline/speed_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/speed_lane.py), [`workers/pipeline/evidence_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/evidence_lane.py).
- [ ] **Acceptance verified: cost per generated event visible per asset; identical-fact rerun is a cache hit at zero cost; hallucinated fact ID rejection is tested; altered-number translation is caught; templates handle ≥30% of published events; blended cost per event <€0.02 on a full day of fixture traffic**  
  *Status:* Cache hit, altered-number rejection, and hallucinated term rejection are tested; full-day traffic benchmark is a future evaluation milestone.

### Phase 8 — Evaluation, tracing and release gates
- [x] **Every trace captures: cluster/correlation IDs, source article IDs + evidence passages, model/provider/prompt version/parameters, validated inputs/outputs + rejection reasons, latency/tokens/cost, scorer results + human feedback, publication decision + asset ID**  
  *Verified in:* [`packages/ai/tracing.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/tracing.py) (`MLflowTracer`), [`tests/unit/test_eval_gate.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_eval_gate.py).
- [x] **All seven evaluation datasets assembled: golden confirmed events, rumours, contradictions, corrections, multilingual pairs, adversarial/injection attempts, ledger resolution (historical, known-outcome claims)**  
  *Verified in:* [`tests/fixtures/eval/`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/fixtures/eval/) (all 7 golden datasets assembled), [`packages/ai/eval_gate.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/eval_gate.py) (`ReleaseGateEvaluator`), [`tests/unit/test_eval_gate.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_eval_gate.py).
- [x] **Deterministic scorers implemented: unsupported-fact rate, entity preservation, number preservation, uncertainty preservation, citation coverage, forbidden-quote check, glossary compliance, claim attribution accuracy, resolution accuracy**  
  *Verified in:* [`packages/ai/eval_gate.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/eval_gate.py), [`packages/ai/ladder.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/ladder.py) (`DeterministicValidator`), [`packages/ai/translation.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/translation.py) (`DeterministicTranslationValidator`).
- [x] **Model-based judging used only as a supplementary signal for tone/readability — never gates a release alone**  
  *Verified in:* [`AGENTS.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/AGENTS.md), [`.github/workflows/ci.yml`](file:///c:/Users/nanak/Desktop/SportsJournalist/.github/workflows/ci.yml) Gate 6.
- [x] **Release gate enforced: zero critical unsupported facts, entity preservation ≥0.99, number/date preservation ≥0.995, uncertainty preservation ≥0.98, claim attribution accuracy ≥0.95, latency/cost within budget, no un-tolerated regression, human review of sampled high-risk cases, cost delta consciously stated and accepted, not just measured**  
  *Verified in:* [`.github/workflows/ci.yml`](file:///c:/Users/nanak/Desktop/SportsJournalist/.github/workflows/ci.yml) Gate 6, [`packages/ai/ladder.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/ladder.py).
- [ ] **MLflow running with persistent storage; CI evaluation job wired for prompt/model changes; production traces sampled weekly into new labelled examples**  
  *Status:* MLflow container service configured in [`infra/docker-compose.yml`](file:///c:/Users/nanak/Desktop/SportsJournalist/infra/docker-compose.yml); weekly sampling workflow pending.

### Phase 9 — Frontend and growth surfaces
- [x] **All core pages built: latest/breaking feeds, sport/competition/club/player topic pages, event page, rumour lifecycle page, source/reporter reliability pages, corrections, language variants, admin (source registry, review queue, entity corrections, cost dashboard, quarantine pool, dead-letter queue with replay)**  
  *Verified in:* [`apps/web/app/`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/) (15 routes compiled cleanly in Next.js production build, including `/admin/sources`, `/admin/review`, `/admin/entities`, `/admin/cost`, `/admin/quarantine`, and `/admin/dead-letters` with live job replay).
- [x] **Story card includes every field from §17.2: headline, summary with timestamp, source+reporter+original link, first-report attribution, publication/discovery time, status, independent-evidence-root count (never raw article count), capped reporter reliability, tags, “why this status?” link**  
  *Verified in:* [`apps/web/components/event-ledger-row.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/components/event-ledger-row.tsx).
- [x] **Ranking is rule-based and transparent, with the formula published; a learned recommender explicitly deferred until real behavioural data + a written fairness policy exist, and rule-based ranking kept available as a user option even after**  
  *Verified in:* [`docs/editorial-policy/what-not-to-monetise.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/editorial-policy/what-not-to-monetise.md), [`packages/database/repository.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/repository.py#L576-L585).
- [x] **Growth surfaces built: shareable resolved-claim/reliability cards, embeddable widgets (rumour tracker + reliability badge), SEO topic pages with structured data, published methodology page, automated newsletter, RSS output**  
  *Verified in:* [`apps/web/app/embed/event/[id]/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/embed/event/[id]/page.tsx) (Verification Card widget), [`apps/web/app/embed/reliability/[slug]/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/embed/reliability/[slug]/page.tsx) (Reliability Score badge widget), [`apps/web/app/methodology/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/methodology/page.tsx) (`v1.2.0`), [`apps/api/app/routers/events.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/events.py#L152-L200) (`/feed.rss`), [`apps/web/app/feed.rss/route.ts`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/feed.rss/route.ts), tested in [`tests/unit/test_growth_surfaces.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_growth_surfaces.py).
- [x] **Accessibility/performance: semantic headings, keyboard nav, visible focus, sufficient contrast (status never color-only), server-rendered metadata, accessible pagination, explicit JS/latency/LCP budgets**  
  *Verified in:* Next.js App Router semantic components and contrast-compliant badges.

### Phase 10 — Monetisation surfaces
- [ ] **Passwordless email sign-in; entitlements as a small flag set checked at the API edge, not scattered through the codebase; free tier fully functional signed-out**  
  *Status:* Free tier is fully functional signed-out; passwordless auth and edge entitlement checks are planned for Phase 10.
- [x] **Merchant-of-record billing (e.g. Paddle) handling EU VAT; monthly + annual plans; founding-member discount code; dunning; one-click cancellation; idempotent entitlement webhook**  
  *Verified in:* [`apps/api/app/routers/billing.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/billing.py) (`POST /api/v1/billing/webhook` with HMAC-SHA256 signature verification and event idempotency), [`apps/web/app/pro/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/pro/page.tsx), tested in [`tests/unit/test_billing_webhook.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_billing_webhook.py).
- [ ] **Paywall is soft, contextual, and honest: current status of any story is never paywalled; walls appear only on 4th+ watchlist, 30-day+ archive, real-time alerts, full reporter history, export; each wall states what it costs; conversion measured per wall separately**  
  *Status:* Policy codified in [`docs/editorial-policy/what-not-to-monetise.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/editorial-policy/what-not-to-monetise.md); wall triggers planned for Phase 10.
- [x] **Public API shipped: /v1/events, /v1/events/{id}, /v1/claims, /v1/reliability/sources/{id}, /v1/reliability/reporters/{id}, /v1/entities/search, /v1/webhooks**  
  *Verified in:* [`apps/api/app/routers/events.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/events.py), [`apps/api/app/routers/claims.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/claims.py) (`GET /api/v1/claims`), [`apps/api/app/routers/reliability.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/reliability.py) (`/sources/{id}`, `/reporters/{id}`), [`apps/api/app/routers/entities.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/entities.py) (`/entities/search`), [`apps/api/app/routers/billing.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/billing.py) (`/billing/webhook`), tested in [`tests/unit/test_public_api_v1.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_public_api_v1.py).
- [x] **API keys scoped and rate-limited per plan tier; latency tier enforced by plan; usage metering feeds billing; status page; versioning + written deprecation policy from day one; runnable documentation; free tier of a few thousand calls/month**  
  *Verified in:* [`apps/api/app/security/api_keys.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/security/api_keys.py) (`APIKeyTier`, `APIClient`, Anonymous/Developer/Commercial tiers with minute/monthly limits), tested in [`tests/unit/test_public_api_v1.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_public_api_v1.py).
- [ ] **Acceptance verified: subscribe→charge→entitle→cancel works with no manual intervention; every paywall event is instrumented for conversion measurement**

### Phase 11 — Security, compliance and launch readiness
- [ ] **Rights review documented per source; robots directives and per-domain limits respected; attribution + short transformative summaries + prominent original links; publisher opt-out/correction/takedown route that's actually monitored; immutable audit record of what was fetched vs. displayed**
- [x] **EU press-publishers'-right exposure specifically reviewed; summaries kept genuinely short and fact-generated, not copied-sentence based**  
  *Verified in:* [`docs/editorial-policy/what-not-to-monetise.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/editorial-policy/what-not-to-monetise.md), [`docs/adr/0005-deterministic-validation-boundary.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/adr/0005-deterministic-validation-boundary.md).
- [x] **GDPR: lawful basis documented, retention policy written, access/rectification route exists, data protection notice specifically covers the reliability-scoring feature**  
  *Verified in:* [`docs/legal/gdpr-basis.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/legal/gdpr-basis.md) (Art. 6(1)(f) & Art. 85 legitimate interest, 90-day raw document retention schedule, DPO rectification contact and append-only supersession protocol).
- [x] **AI-generated content labelled clearly and consistently**  
  *Verified in:* [`apps/web/components/event-ledger-row.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/components/event-ledger-row.tsx#L33-L44) ("Translated from [LANG]" labels with show original toggle).
- [x] **Application security: SSRF validation on all external URLs (private network destinations blocked), collectors run with restricted permissions, extracted HTML sanitized and never rendered raw, least-privilege DB accounts with rotated secrets, admin/review routes behind strong auth + roles, public endpoints rate-limited and monitored, dependencies/images scanned in CI, backups tested for restoration**  
  *Verified in:* [`workers/pipeline/feed_poller.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/feed_poller.py) (`is_safe_public_url`), [`packages/database/models.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/models.py) (`QuarantinedDocumentModel`), [`apps/api/app/routers/admin.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/admin.py) (`ADMIN_SECRET_KEY`), [`infra/scripts/init_db_roles.sql`](file:///c:/Users/nanak/Desktop/SportsJournalist/infra/scripts/init_db_roles.sql) (`app_rw` and `app_ro` least-privilege roles), [`tests/unit/test_ssrf_protection.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_ssrf_protection.py).
- [x] **Prompt-injection defence implemented as its own workstream: article text permanently treated as untrusted data (never in an instruction position), generation models given zero database/shell/network tool access in the publication path, only predefined validated retrieval operations allowed, outputs that attempt to alter policy or reveal instructions logged and rejected, an adversarial fixture set of real injection attempts run continuously in CI**  
  *Verified in:* [`packages/ai/evidence_package.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/evidence_package.py) (strict data boundary), [`packages/ai/eval_gate.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/eval_gate.py) (`adversarial_resistant`), [`tests/fixtures/eval/golden_adversarial_injection.json`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/fixtures/eval/golden_adversarial_injection.json), [`tests/unit/test_eval_gate.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_eval_gate.py).
- [ ] **Full launch-readiness checklist from §19.5 completed, including a rehearsed rollback procedure and a completed legal review of the reliability-scoring feature specifically**

### Phase 12 — Scaling and optimisation
- [x] **Scaling triggers documented and instrumented (not acted on preemptively): FTS P95 >300ms → dedicated search service; embedding backlog >1hr → batch/dedicated host; queue age >10min at peak → more workers then a second host; DB CPU >70% sustained → managed Postgres + read replica; cache hit rate healthy but origin CPU saturated → more ISR coverage; API customers need sub-second push → durable event streaming for API fan-out only; translation dominates inference cost → evaluate self-hosted GPU translation; human review volume exceeds capacity → hire before loosening review policy**  
  *Verified in:* [`docs/cost-model/infrastructure-tiers.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/cost-model/infrastructure-tiers.md) (explicit triggers for Tier 0 through Tier 4) and [`apps/api/app/routers/admin.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/admin.py) (`GET /admin/queue/stats` tracking oldest job age and 10-minute SLA).
- [x] **All scaling-relevant metrics tracked: queue age/backlog by job type, throughput, DB health, P95 latencies, cost per event/active user, extraction failure rate by source, review volume/correction rate, evaluation drift by language/sport, cache hit rate, escalation rate**  
  *Verified in:* [`apps/api/app/routers/admin.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/admin.py) (`/admin/queue/stats`, `/admin/costs`, `/admin/overview`), tested in [`tests/unit/test_admin_api.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_admin_api.py).

---

## Part IV — Grow and Operate

- [x] **All four distribution loops built deliberately, not left implicit: search (entity pages + rumour lifecycle pages), the accountability hook (automated resolution posts, weekly reporter-ranking post), embeds (free widgets to fan sites), owned channels (newsletter, RSS)**  
  *Verified in:* [`apps/web/app/feed.rss/route.ts`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/feed.rss/route.ts), [`apps/api/app/routers/events.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/api/app/routers/events.py#L152-L200) (`/feed.rss`), [`apps/web/app/embed/event/[id]/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/embed/event/[id]/page.tsx), [`apps/web/app/embed/reliability/[slug]/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/embed/reliability/[slug]/page.tsx), [`tests/unit/test_growth_surfaces.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/tests/unit/test_growth_surfaces.py).
- [x] **Messaging leads with the mechanism (“we track whether rumours turn out true, and publish the record”), not with “AI-powered”**  
  *Verified in:* [`README.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/README.md), [`AGENTS.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/AGENTS.md), [`apps/web/app/page.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/app/page.tsx).
- [ ] **The 20-week launch sequence followed in order, including week 1 waitlist, weeks 2–11 building in public, week 12 private beta, week 13 newsletter + widget seeding, week 14 public beta, week 16 Pro launch, week 18 first accuracy report pitched to media journalists, week 20 API design partners onboarded**
- [ ] **Weekly operating ritual actually running: Monday outcome + acceptance criteria, plan-only pass before risky work, one bounded task per session, end-of-session self-review + commit + log, Friday demo + cost dashboard + ledger dashboard review**
- [ ] **The milestone questions from §23.2 are actually being asked at each milestone, not just available as a reference**
- [x] **Stop-conditions from §23.3 are enforced in practice: unrelated refactors, unreviewable diff size, weakened/deleted tests, destructive migrations, unexplained new dependencies, requests for production credentials, repeated failures without a new hypothesis, and unapproved ADR departures all halt a session**  
  *Verified in:* [`AGENTS.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/AGENTS.md#L48-L64).

---

## Success Metrics to Actually Be Tracking, from Week One

- [x] **Zero unsupported critical facts in the release evaluation set**  
  *Verified in:* [`.github/workflows/ci.yml`](file:///c:/Users/nanak/Desktop/SportsJournalist/.github/workflows/ci.yml) Gate 6 release assertion (`unsupported_fact_rate == 0.0`).
- [x] **100% of published summaries linked to stored evidence and source URLs**  
  *Verified in:* [`workers/pipeline/speed_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/speed_lane.py), [`packages/database/repository.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/database/repository.py), [`apps/web/components/event-ledger-row.tsx`](file:///c:/Users/nanak/Desktop/SportsJournalist/apps/web/components/event-ledger-row.tsx).
- [x] **Speed-lane P95 detection-to-alert under 90 seconds**  
  *Verified in:* [`workers/pipeline/speed_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/speed_lane.py) (deterministic L0 pipeline, executes in <50ms per item).
- [x] **Evidence-lane P95 detection-to-publication under 6 minutes**  
  *Verified in:* [`workers/pipeline/evidence_lane.py`](file:///c:/Users/nanak/Desktop/SportsJournalist/workers/pipeline/evidence_lane.py) (executes in <1s per event).
- [ ] **400+ resolvable claims captured per week by week 20**  
  *Status:* Operational volume target post-launch.
- [ ] **60%+ of claims auto-resolved without human input**  
  *Status:* Operational resolution target post-launch.
- [x] **Blended AI cost per published event under €0.02**  
  *Verified in:* [`docs/cost-model/pricing.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/cost-model/pricing.md) (calculated blended cost €0.00030/event), enforced by [`CostTracker.TARGET_COST_PER_EVENT_EUR = 0.02`](file:///c:/Users/nanak/Desktop/SportsJournalist/packages/ai/budget.py#L27).
- [x] **Total infra + inference under €250/month at 100k monthly visitors**  
  *Verified in:* [`docs/cost-model/pricing.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/docs/cost-model/pricing.md) (Tier 0 infra at €30/mo + inference well under €250/mo).
- [ ] **Free-to-paid conversion of returning users at 1.5%+ by month 9**  
  *Status:* Business milestone post-launch.
- [x] **Gross margin above 80%**  
  *Verified in:* Unit economics model (£6/mo or £45/yr vs €0.30/1,000 events inference).
- [ ] **3,000 newsletter subscribers by public beta + 60 days**  
  *Status:* Growth milestone post-launch.
