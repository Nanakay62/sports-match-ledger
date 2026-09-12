# ADR-0005: Strict Boundary Between Deterministic Validation & Generation

## Status
Accepted

## Context
Generative models are probabilistic systems susceptible to hallucination, sycophancy, omission of critical caveats, and instruction drift. In a journalistic accountability platform, inventing a single quote, fee, medical date, or contract length undermines the integrity of the product.

## Decision
We enforce a strict, impermeable architectural boundary between deterministic validation logic and model generation:
1. **Untrusted Input Boundary**:
   - Article text, social media statements, and source feeds are treated as **untrusted data input**.
   - Untrusted text is never placed into an instruction position in prompts; it is always encapsulated in clearly delimited, structured data blocks (e.g. `<source_article>...</source_article>` or JSON fields).
2. **Independent Deterministic Evaluation Gates**:
   - Every generated output (event summary, status rationale, translation) must pass a suite of deterministic scorers before publication:
     - **Unsupported-Fact Rate (UFR)**: Must be 0%. Any claim asserting a number, name, or date not present in the cited source evidence triggers immediate rejection.
     - **Entity & Number Preservation**: All named entities, financial figures (€, £, $), and contract years must map exactly to source text tokens.
     - **Uncertainty Preservation**: If source text indicates conditional terms ("negotiating", "provisional", "slot held"), the generated output must not convert it into certainty ("done deal", "signed").
     - **Citation Coverage**: Every substantive sentence in a published event must link to a specific claim ID and source URL.
3. **Automated MLflow Release Gate**:
   - Any prompt iteration, model version change, or schema adjustment must run against a golden benchmark dataset and achieve passing deterministic scores in MLflow before deployment.

## Consequences
- **Positive**: Zero invented quotes or numbers; guarantees consistent journalistic attribution; enables reliable continuous deployment of prompt updates.
- **Negative**: Adds latency to the evidence lane; requires maintenance of golden benchmark evaluation test suites.
