# ADR-0002: PostgreSQL + pgvector as Unified System of Record & Job Queue

## Status
Accepted

## Context
A high-integrity sports news platform requires reliable transactional persistence for an append-only ledger, vector similarity search for event deduplication and clustering, and background job queuing for a two-lane processing pipeline (speed lane <90s, evidence lane <6min).

Modern architectures frequently reach prematurely for external distributed systems such as Redis, Kafka, RabbitMQ, or dedicated vector databases (Pinecone, Milvus, Qdrant). Introducing multiple datastores and queue brokers at this early phase increases operational overhead, deployment complexity, failure modes, and local workstation friction.

## Decision
We select **PostgreSQL 16 with the `pgvector` extension** as the single unified system of record for Sports News AI:
1. **Relational System of Record**: All claims, sources, events, entities, and resolutions are stored in relational tables with foreign keys and strict constraints.
2. **Vector Similarity for Clustering**: `pgvector` (`vector` type and HNSW/IVFFlat indexes) performs cosine similarity search directly within Postgres to deduplicate incoming articles and cluster them into events before any LLM inference occurs.
3. **PostgreSQL-Backed Job Queue**: Pipeline tasks (ingestion, speed lane alerts, evidence lane scoring) are managed using a transactional job table utilizing `SELECT ... FOR UPDATE SKIP LOCKED`. This provides atomic, ACID-compliant queue semantics without needing Redis or Kafka.

### Scaling Trigger Rule
No Redis or Kafka will be introduced into the MVP until forced by an explicit scaling trigger: sustained ingestion throughput exceeding PostgreSQL write-buffer limits (> 5,000 incoming articles/minute) or worker coordination latency exceeding SLA limits under load testing.

## Consequences
- **Positive**: Single system to backup, migrate, query, and monitor; unified ACID transactions between job state transitions and ledger updates; zero extra services required on developer workstations beyond Postgres.
- **Negative**: Long-polling or notification triggers must use `pg_notify` or periodic polling; high queue throughput requires periodic vacuuming of the job table.
