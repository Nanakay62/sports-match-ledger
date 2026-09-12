# Cost Architecture & Live Model Pricing Model

## Cost Discipline (§9.2)
Sports News AI enforces three strictly isolated cost pools to prevent runaway expenses and ensure production viability:

| Cost Pool | Purpose | Monthly Ceiling / Target | Key Restrictions |
| :--- | :--- | :--- | :--- |
| **Pool 1: Build Spend** | Coding agent & CI evaluation | €100.00 / month | Isolated developer keys; zero production database access. |
| **Pool 2: Run Spend** | Infrastructure (Postgres, hosting, storage) | €30.00 / month (Tier 0) | Single Postgres + pgvector monolith; no Redis or Kafka in MVP. |
| **Pool 3: Inference Spend** | Production model calls via AI Gateway | **&lt; €0.02 per published event** | Deduplicate and cluster before any L2+ model call. |

---

## Current Model Pricing Schedule (Re-verified 2026)

| Model | Provider | Inference Rung | Input / 1M Tokens | Output / 1M Tokens | Role in Pipeline |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Regex / Rule Heuristics** | Internal | **L0 (Deterministic)** | $0.00 | $0.00 | Filtering, entity extraction, exact/fuzzy dedup. |
| **Local CPU Embeddings** | FastTokenizer/ONNX | **L1 (Local CPU)** | $0.00 | $0.00 | Cross-lingual embedding similarity search. |
| **Gemini 2.0 Flash-Lite** | Google | **L2 (Small Hosted)** | $0.075 | $0.30 | High-frequency translation and claim extraction. |
| **Claude 3.5 Haiku** | Anthropic | **L3 (Mid Hosted)** | $0.80 | $4.00 | Claim contradiction synthesis and nuanced dispute notes. |
| **Claude 3.5 Sonnet** | Anthropic | **L4 (Frontier)** | $3.00 | $15.00 | Escalation-only upon deterministic release check failure. |

---

## Blended Cost per 1,000 Published Events

In Sports News AI, model calls are executed **once per event cluster, never per incoming raw article**:

* **Assumptions per 1,000 ingested raw articles:**
  - 1,000 raw articles $\rightarrow$ deduplicated into ~100 distinct event clusters (10:1 ratio via L0 SimHash and L1 vectors).
  - 30% of events handled deterministically at **L0** (results, simple transfers): 30 events $\times$ €0.00 = **€0.00**.
  - 60% of events require **L2** standard extraction/translation (avg. 400 in, 150 out tokens): 60 events $\times$ €0.00012 = **€0.0072**.
  - 9% of events require **L3** complex dispute synthesis (avg. 800 in, 250 out tokens): 9 events $\times$ €0.0016 = **€0.0144**.
  - 1% of events escalate to **L4** frontier evaluation: 1 event $\times$ €0.008 = **€0.0080**.

* **Total Inference Cost per 100 Published Events**: €0.0296.
* **Blended Inference Cost per Published Event**: **€0.00030** (substantially under the €0.02 target ceiling).
* **Cost per 1,000 Published Events**: **€0.30**.
