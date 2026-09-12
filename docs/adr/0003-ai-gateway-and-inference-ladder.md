# ADR-0003: AI Gateway & Five-Rung Inference Ladder

## Status
Accepted

## Context
Model calls represent the variable cost risk and hallucination vector of the platform. Direct, unmanaged calls to LLM APIs scattered across backend code lead to prompt drift, unaccounted expenses, inconsistent error handling, lack of provenance tracing, and impossible unit testing.

Furthermore, a blended AI inference cost target of < EUR 0.02 per published event demands strict deduplication and tiered inference: cheap/deterministic methods must handle the vast majority of processing, escalating to expensive frontier models only when verification checks fail.

## Decision
We mandate that **all model calls must route through `packages/ai` (the AI Gateway)**:
1. **Zero Direct Provider Calls**: Direct imports of OpenAI, Anthropic, Gemini, or any other LLM SDKs are prohibited outside of `packages/ai`.
2. **Five-Rung Inference Ladder**:
   - **L0 (Deterministic)**: Regex, entity dictionaries, heuristics, rule-based extraction ($0 cost, <10ms).
   - **L1 (Local CPU Models)**: Embeddings, local fast models (e.g. fast tokenizer / small ONNX transformer) on CPU ($0 variable API cost).
   - **L2 (Small Hosted Model)**: Lightweight, low-cost API models (e.g., Gemini Flash-Lite / GPT-4o-mini) for standard extraction and translation.
   - **L3 (Mid Hosted Model)**: Capable models (e.g., Gemini Flash / Claude 3.5 Haiku) for nuanced claim synthesis and contradiction analysis.
   - **L4 (Frontier Model)**: Escalation-only model (e.g., Claude 3.5 Sonnet / GPT-4o) invoked exclusively when deterministic release gate checks fail.
3. **Deterministic Verification Boundary**: Model escalation occurs *only* if deterministic checks fail (e.g., unsupported fact check, entity preservation failure, or missing citation).
4. **Telemetry & Budget Discipline**:
   - Every generated asset must record: `model_id`, `prompt_version`, `cost_usd`, and `trace_id`.
   - Hard cost budgets per stage. Deduplication and clustering must precede any L2+ model call.

## Consequences
- **Positive**: Strict cost control meeting the < EUR 0.02 / event target; full auditability via trace IDs; modular swapping of model providers without altering application code.
- **Negative**: Adds gateway abstraction overhead; requires maintaining the multi-rung escalation state machine.
