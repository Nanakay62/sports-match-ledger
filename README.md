# Sports News AI — The Accountability Ledger

> **The sports news app that keeps the receipts.**

An evidence-grounded, multilingual sports journalism platform. Every substantive transfer rumour, breaking scoop, or match development is recorded with its original outlet, author, and timestamp, matched against authoritative outcomes, and rolled up into a public reliability score per outlet and reporter.

---

## Key Features

- **The Accountability Ledger:** An append-only historical record of sports reporting. Claims are never edited or deleted—only superseded with evidence.
- **Multilingual Entity Graph & Translation Engine:** Automatic translation across English, Italian, Spanish, German, and French, with strict deterministic preservation of transfer fees, numbers, uncertainty levels, and canonical club/player names.
- **Automated RSS Feed Poller:** Built-in ingestion across 15+ major global sports outlets (BBC Sport, The Guardian, Sky Sport Italia, Marca, AS, Mundo Deportivo, Kicker, UEFA, FIFA, Record) at zero API cost.
- **Source & Reporter Reliability Scoring:** Deterministic Bayesian scoring (Wilson score interval lower bound, recency decay, per-category accuracy).
- **Subdomain-Isolated Editorial Admin Desk:** Public readers cannot access `/admin`; editorial staff access the Source Registry, Review Queue, Entity Corrections, and Cost Telemetry via `admin.*` subdomain.
- **AI Gateway & 5-Rung Inference Ladder:** L0 deterministic $\to$ L1 local CPU $\to$ L2 small hosted $\to$ L3 mid hosted $\to$ L4 frontier, escalating only upon deterministic check failures.

---

## Tech Stack

- **Frontend:** Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide Icons.
- **Backend API:** FastAPI, Pydantic v2, SQLAlchemy 2.0.
- **Database:** SQLite (local development) / PostgreSQL with pgvector (production).
- **Package Management & Tooling:** `uv` (Python 3.12), `npm` (Node.js 20+), `pytest`, `ruff`, `mypy`.

---

## Quickstart Guide

### Prerequisites
- Node.js 20+ and npm
- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) (fast Python package manager)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/sports-news-ai.git
cd sports-news-ai
```

### 2. Configure Environment
```bash
cp .env.example .env
```

### 3. Backend Setup (FastAPI)
Install Python dependencies and start the API server on port `8000`:
```bash
# Using uv (recommended)
uv run --with-requirements apps/api/requirements.txt uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```
On initial launch, the database tables and approved source feeds are created automatically.

### 4. Frontend Setup (Next.js)
In a separate terminal, install dependencies and start the web server on port `3000`:
```bash
cd apps/web
npm install
npm run dev
```

### 5. Access the Platform
- **Public Reader Site:** [http://localhost:3000/](http://localhost:3000/)
- **Editorial Admin Desk (Subdomain):** [http://admin.localhost:3000/](http://admin.localhost:3000/) (or [http://localhost:3000/?subdomain=admin](http://localhost:3000/?subdomain=admin))
- **Interactive API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Ingesting Live Sports News

To poll the approved free RSS feeds and populate the ledger with breaking articles:
```bash
uv run --with-requirements apps/api/requirements.txt python -m workers.pipeline.feed_poller
```
To seed pre-computed multilingual translations for active stories:
```bash
uv run --with-requirements apps/api/requirements.txt python scripts/seed_event_translations.py
```

---

## Billing (Stripe, test mode)

Pro subscriptions run through Stripe Checkout and the Stripe Billing Portal. Without
`STRIPE_SECRET_KEY` / `STRIPE_PRICE_ID_MONTHLY` / `STRIPE_PRICE_ID_ANNUAL` set, checkout
returns a clean `503` rather than failing silently — the free ledger is unaffected either way.

To wire it up in a Stripe sandbox account:
1. Create two recurring Prices in test mode (monthly, annual) and copy their `price_...` IDs.
2. Set `STRIPE_SECRET_KEY` (`sk_test_...`), `STRIPE_PRICE_ID_MONTHLY`, `STRIPE_PRICE_ID_ANNUAL` in `.env`.
3. Forward webhooks to your local API with the Stripe CLI and set the printed secret as `STRIPE_WEBHOOK_SECRET`:
   ```bash
   stripe listen --forward-to localhost:8000/api/v1/billing/webhook
   ```
4. Subscribe through `/pro` with a [Stripe test card](https://docs.stripe.com/testing#cards) — entitlements are
   persisted in `customer_entitlements`, keyed by the email entered at checkout (no password, per Handbook §18.1).

See `docs/adr/0017-stripe-billing-and-persisted-entitlements.md` for what is and isn't handled yet (notably: no EU VAT/Stripe Tax, and no accounts system beyond email).

---

## Testing & Quality Gates

The project enforces 6 strict quality gates verified via GitHub Actions (`.github/workflows/ci.yml`):

```bash
# Gate 1: Lint & Format
cd apps/web && npm run lint
uv run --with ruff ruff check .
uv run --with ruff ruff format --check .

# Gate 2: Static Type Checking
cd apps/web && npx tsc --noEmit
uv run --with-requirements apps/api/requirements.txt --with mypy mypy packages apps/api workers

# Gate 5: Automated Unit & Invariant Tests
uv run --with-requirements apps/api/requirements.txt --with httpx pytest
```

---

## Cost Ceilings

The platform strictly isolates three cost pools with monthly spending limits:

| Cost Pool | Description | Monthly Ceiling |
|---|---|---|
| **Build** | Coding agents and local CI development | €50 / month |
| **Run** | Core infrastructure (Postgres + container compute, Tier 0) | €30 / month |
| **Inference** | Hosted production model executions (L2–L4) | €200 / month |

Target blended inference cost is strictly budgeted at **<€0.02 per published event**. Full tier definitions and unit economics are documented in [`docs/cost-model/pricing.md`](docs/cost-model/pricing.md).

---

## Deploying to Production

When hosting publicly:
1. **Frontend (Next.js):** Deploy `apps/web` to Vercel, Railway, or AWS. Set `NEXT_PUBLIC_API_URL` to your production API domain.
2. **Backend (FastAPI):** Deploy with Docker or on Railway / Render / Fly.io. Set `DATABASE_URL` to a PostgreSQL instance.
3. **Admin Subdomain:** Point `admin.yourdomain.com` and `yourdomain.com` to the frontend. The Next.js edge middleware isolates the admin desk automatically.

---

## License

MIT License.
