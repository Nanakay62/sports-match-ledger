# ADR-0001: Monorepo Structure & Tooling Foundation

## Status
Accepted

## Context
Sports News AI is a multi-component system comprising a Next.js web application, a FastAPI backend API, background pipeline workers (two-lane pipeline: speed lane and evidence lane), shared domain packages (AI Gateway, database layer, common math and schemas), infrastructure definitions, and automated CI verification gates. 

A monorepo structure is required to maintain tight synchronization across domain types (TypeScript on the frontend, Python Pydantic models on the backend), ensure consistent CI enforcement, and prevent architecture drift while enforcing strict module boundaries.

## Decision
We organize the repository as a unified monorepo with the following top-level directory layout:

```
SportsJournalist/
├── AGENTS.md                  # Persistent project brief, non-negotiable rules, and current phase
├── apps/
│   ├── web/                   # Next.js 15 + TypeScript ISR frontend
│   └── api/                   # FastAPI + Pydantic v2 API service
├── workers/
│   └── pipeline/              # Two-lane background workers (speed lane & evidence lane)
├── packages/
│   ├── ai/                    # The AI Gateway (sole locus for model routing, ladder, budget)
│   ├── database/              # PostgreSQL + pgvector schemas, Alembic migrations, session
│   └── common/                # Shared scoring math (Wilson lower bound), schemas, validation
├── tests/
│   ├── unit/                  # Deterministic unit tests (scoring math, type invariants)
│   ├── integration/           # Database integration & API route verification
│   └── e2e/                   # End-to-end user journeys & rendering checks
├── docs/
│   └── adr/                   # Architecture Decision Records
├── infra/
│   ├── docker-compose.yml     # Local services: PostgreSQL with pgvector, MLflow
│   └── scripts/               # Database initialization and seeding utilities
└── .github/
    └── workflows/
        └── ci.yml             # 6-gate CI pipeline
```

### Dependency Rules & Pinning
1. All dependencies across TypeScript (`package.json`) and Python (`pyproject.toml` / `requirements.txt`) must be strictly pinned to exact versions (no `^`, `~`, or `latest`).
2. No direct model provider SDK calls (OpenAI, Anthropic, Gemini, etc.) may exist anywhere outside `packages/ai`.
3. Frontend and API share contracts defined through versioned schemas.

## Consequences
- **Positive**: Strict boundaries prevent premature microservices while maintaining modularity; single-command CI validation across all layers; shared domain understanding.
- **Negative**: Monorepo tooling requires unified git workflows and careful CI caching.
