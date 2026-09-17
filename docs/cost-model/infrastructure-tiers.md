# Infrastructure Scaling Tiers & Operational Triggers

**Sports News AI — System Architecture**  
**Document Version:** 1.0.0  
**Effective Date:** September 2026  

---

## 1. Architectural Philosophy: The Lean Monolith

Per [`AGENTS.md`](file:///c:/Users/nanak/Desktop/SportsJournalist/AGENTS.md):  
> *"Prefer a simple module to a premature service. No Kubernetes, no Kafka, no microservices, no Redis before it's explicitly forced by a scaling trigger."*

We run a **modular monolith** backed by PostgreSQL + pgvector as the single system of record, including the job queue. Infrastructure upgrades are never speculative; each tier transition is governed by explicit, measurable hardware or latency thresholds.

---

## 2. Five Infrastructure Tiers (Tier 0 to Tier 4)

| Tier | Monthly Run Cost | Traffic SLA | Compute & Architecture | Storage & Queue | Transition Trigger |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 0** | **~€30/month** | 0 – 25k monthly visitors | Single VPS (Hetzner / OVH 4 vCPU, 8GB RAM). Docker Compose running FastAPI, Next.js, and Postgres. | In-process Postgres-backed job queue; local disk storage for traces. | Initial deployment baseline. |
| **Tier 1** | **~€80/month** | 25k – 100k monthly visitors | Dedicated API server (4 vCPU, 8GB); separate background worker container; edge CDN (Cloudflare). | Managed PostgreSQL instance (2 vCPU, 4GB RAM) with automated daily backups. | DB CPU > 60% sustained for 30 minutes, OR Queue P95 age > 2 minutes at peak. |
| **Tier 2** | **~€250/month** | 100k – 500k monthly visitors | 2x API nodes behind regional reverse proxy; dedicated embedding / CPU node for L1 models. | Primary Postgres (write) + Read Replica for public ISR queries; pgvector on primary. | Database read queries saturate connection pool, OR FTS P95 latency > 300ms. |
| **Tier 3** | **~€800/month** | 500k – 2M monthly visitors | Horizontally auto-scaled stateless FastAPI containers; Next.js ISR on multi-region edge nodes. | Managed HA PostgreSQL cluster with automated failover; Redis queue introduced **only** if job backlog exceeds 1,000 concurrent jobs/min. | Job queue age > 10 minutes at peak with max workers, OR API traffic > 10,000 RPM. |
| **Tier 4** | **~€2,500/month** | > 2M monthly visitors & Enterprise API | Multi-region container cluster; dedicated inference GPU nodes (for self-hosted local translation). | Partitioned PostgreSQL tables (historical claims archival); Kafka or durable event streaming **solely** for commercial sub-second push API. | Commercial data partners contractually require < 500ms real-time event streaming. |

---

## 3. Explicit Operational Scaling Triggers

Do not upgrade infrastructure based on intuition or future projections. Upgrade only when one of the following automated triggers fires:

### Trigger 1: Full-Text Search Latency
- **Metric:** `FTS_P95_Latency`
- **Threshold:** `> 300ms` sustained over 1 hour.
- **Action:** Add dedicated trigram GIN indexes; if sustained, route search queries to a read replica before considering external search engines.

### Trigger 2: Job Queue SLA
- **Metric:** `Oldest_Pending_Job_Age`
- **Threshold:** `> 10 minutes` during morning/evening transfer window peaks.
- **Action:** Increase worker concurrency parameter `WORKER_CONCURRENCY` from 4 to 8. If host CPU > 80%, spin up a dedicated worker VPS.

### Trigger 3: Database Load
- **Metric:** `PostgreSQL_CPU_Utilization`
- **Threshold:** `> 70%` sustained over 1 hour.
- **Action:** Move from Tier 0 local Postgres to Tier 1 Managed PostgreSQL (RDS or Hetzner Cloud Managed DB).

### Trigger 4: Webhook & Ingest Volume
- **Metric:** `Incoming_Feed_Documents_Per_Minute`
- **Threshold:** `> 250 documents/min`.
- **Action:** Enable per-domain rate limit queuing in `workers/pipeline/feed_poller.py` and enforce publisher batching.

### Trigger 5: Origin Saturation with High Cache Hit Rate
- **Metric:** `NextJS_Origin_CPU` with `Edge_Cache_Hit_Rate > 85%`
- **Threshold:** Origin server saturated despite high cache efficiency.
- **Action:** Increase Next.js ISR `revalidate` periods from 60s to 300s for non-breaking event views.

---

## 4. Cost Discipline Checklists

- [x] Three cost pools tracked separately (Build, Run, Inference) in [`apps/web/app/admin/cost/page.tsx`](file:///apps/web/app/admin/cost).
- [x] Target blended AI cost per published event: `< €0.02`.
- [x] Total infrastructure + inference cost target at 100k visitors: `< €250/month`.
