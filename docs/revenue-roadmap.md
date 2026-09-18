# Revenue Architecture & Monetisation Roadmap

**Sports News AI — Business Model**
**Document Version:** 1.0.0

Handbook §2.1 names seven revenue lines and sequences them by earliest viable month. This document is that sequencing, applied to this repository specifically — each line marked against what's actually built versus what's still a plan, so this stays a roadmap rather than a restatement of the handbook.

## The seven lines, sequenced

| # | Line | Who pays | Realistic price | Margin | Earliest month | Status in this repo |
|---|---|---|---|---|---|---|
| 1 | Consumer subscription | Engaged fans | €4.99/mo or €39/yr (this build: £6/mo, £45/yr) | ~92% | Month 5 | **Live.** Stripe Checkout + Billing Portal, persisted entitlements. See `docs/adr/0017`. |
| 2 | Data and claims API | Fantasy apps, trading desks, agencies, media monitors | €99 / 499 / 1,999 per month | ~95% | Month 8 | **Partially built.** `apps/api/app/security/api_keys.py` has three tiers (Anonymous/Developer/Commercial) with rate limits, but no self-serve signup, no invoicing, no usage-based billing wired to Stripe yet. |
| 3 | Newsletter sponsorship | Brands wanting engaged sports readers | €25–60 CPM on a 10k+ list | ~98% | Month 5 | **Not built.** `scripts/generate_newsletter.py` produces the digest; no subscriber list, no sponsorship slot, no ad-sales process. |
| 4 | Display and native advertising | Programmatic demand | €2–6 RPM in EU sports | ~85% | Month 4 | **Not built.** No ad units anywhere in `apps/web`. |
| 5 | Embeddable widgets and white label | Fan sites, club media, podcasts, blogs | Free (backlinks) to €250/mo branded | ~95% | Month 7 | **Built, free tier only.** `apps/web/app/embed/event/` and `apps/web/app/embed/reliability/` render embeddable cards. No branded/paid tier, no white-label billing. |
| 6 | Affiliate and referral | Streaming, ticketing, merchandise, licensed operators | 5–30% of order value | ~99% | Month 6 | **Not built.** No affiliate links anywhere. Handbook explicitly excludes gambling affiliate revenue from the base plan pending jurisdiction-specific legal advice (`docs/editorial-policy/what-not-to-monetise.md`) — that exclusion still applies to any future affiliate work. |
| 7 | Annual data reports and licensing | Media, rights holders, academics | €2,000–15,000 per report or licence | ~90% | Month 12 | **Not built, and not buildable yet.** Depends on a season's worth of resolved claims existing, which depends on real production traffic. |

## What this means for sequencing work

Only line 1 is genuinely revenue-generating today. The next highest-leverage build, per the handbook's own ordering (by margin and by how early it's realistic) and by how much of the groundwork already exists in this codebase, is **line 2** — the API tiering infrastructure already exists; what's missing is self-serve signup and usage-based invoicing, not a new subsystem.

Lines 3, 4, and 6 are lower-effort but need real audience/traffic to be worth anything — building the mechanics before there's a newsletter list or ad inventory to sell against would be premature. Line 7 is structurally blocked on time (a season of resolved claims) rather than on engineering.

## What not to monetise

Unchanged from `docs/editorial-policy/what-not-to-monetise.md` — paid placement in feeds, sponsored "verified" badges, selling reading behaviour, republishing full articles behind a paywall, and betting tips remain permanently off the table regardless of which revenue line is being built.
