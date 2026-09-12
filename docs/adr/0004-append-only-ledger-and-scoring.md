# ADR-0004: Append-Only Accountability Ledger & Wilson Score Reliability

## Status
Accepted

## Context
The core product thesis of Sports News AI is: "The sports news app that keeps the receipts." The differentiator is the Accountability Ledger. Standard news aggregators delete or silently update erroneous stories when a transfer rumour collapses or proves false. This hides accountability and incentivizes ungrounded sensationalism.

Furthermore, naive reliability metrics (such as raw percentages like 100% based on 1 claim) are misleading, noisy, and easily manipulated.

## Decision
1. **Strictly Append-Only Storage**:
   - The claims table and evidence records are immutable.
   - `UPDATE` and `DELETE` operations are forbidden on ledger claims and resolutions.
   - Any modification is recorded as a superseding event or an explicit amendment with a status of `corrected` or `disputed`.
2. **Reliability Scoring via Wilson Score Interval (Lower Bound)**:
   - For any outlet or reporter with resolved claims, the public score is computed using the **Wilson score interval lower bound** at a 95% confidence level:
     $$\text{Score} = \frac{\hat{p} + \frac{z^2}{2n} - z \sqrt{\frac{\hat{p}(1-\hat{p}) + \frac{z^2}{4n}}{n}}}{1 + \frac{z^2}{n}}$$
     where $\hat{p} = \frac{\text{correct}}{n}$ and $z = 1.95996$ (for 95% confidence).
   - This statistically penalizes small sample sizes (e.g. 1/1 will score much lower than 34/41).
3. **Recency Decay**:
   - Older resolved claims are weighted with an exponential half-life decay ($\lambda$) to reflect current reporting standards.
4. **Sample Size Threshold (< 10 Resolved Claims)**:
   - If a source has fewer than 10 resolved claims ($n < 10$), the platform renders an **"Insufficient record"** state.
   - No score or rating tier is published; only the raw counts ($x/y$) and recent resolutions are visible as public record.
5. **Resolution Hierarchy**:
   - Auto-resolution occurs only at Rank 1 (official club announcement / league filing) and Rank 2 (direct player/executive statements). Rumours and unverified leaks (Rank 3+) never auto-resolve claims.

## Consequences
- **Positive**: Complete audit trail and tamper-proof receipts; statistically sound, defensible reliability scores that resist small-sample distortion; prevents reputational damage from uncorroborated single hits.
- **Negative**: Requires historical recalculations; ledger storage grows monotonically and requires partitioning at scale.
