import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  Calculator,
  ShieldCheck,
  Scale,
  History,
  Split,
  Flag,
  Route,
  Zap,
  XCircle,
} from "lucide-react";

export const metadata = {
  title: "Scoring Methodology & Formula Specification | Sports News AI",
  description:
    "Reproducible statistical specification for the Accountability Ledger: Wilson score lower bounds, sample gating, recency decay, dual attribution, and component scoring.",
};

export default function MethodologyPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <div className="mb-6">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 font-sans text-xs font-medium text-ink-muted hover:text-ink transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to breaking ledger
        </Link>
      </div>

      <header className="mb-10 border-b border-rule pb-8">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="rounded bg-navy-900 px-2.5 py-0.5 font-mono text-[11px] font-medium text-paper">
            Formula Version: v1.2.0
          </span>
          <span className="rounded bg-rule px-2 py-0.5 font-mono text-[11px] text-ink-muted">
            Frozen: September 2026
          </span>
        </div>
        <h1 className="font-serif text-3xl font-bold tracking-tight text-ink sm:text-4xl">
          Accountability Ledger Methodology
        </h1>
        <p className="mt-3 font-sans text-base text-ink-muted leading-relaxed">
          The mathematical and procedural rules governing how sports journalism claims are verified,
          resolved, and synthesized into public reliability records. Every score displayed on Sports News AI
          is deterministically reproducible from the equations below.
        </p>
      </header>

      <div className="space-y-12 font-sans text-ink">
        {/* Core Thesis */}
        <section className="rounded-lg border border-rule bg-paper-deep p-6">
          <div className="flex items-start gap-3">
            <ShieldCheck className="h-6 w-6 text-navy-800 shrink-0 mt-0.5" />
            <div>
              <h2 className="font-serif text-lg font-bold text-ink">The Product Thesis</h2>
              <p className="mt-1 text-sm text-ink-muted leading-relaxed">
                Most platforms rank news by engagement. We track whether claims turn out to be true, and publish the receipts.
                The Accountability Ledger is append-only: claims and resolutions are never deleted or silently edited,
                preserving an immutable audit trail of modern sports reporting.
              </p>
            </div>
          </div>
        </section>

        {/* Five Differentiators */}
        <section className="space-y-4">
          <div className="border-b border-rule pb-2">
            <h2 className="font-serif text-xl font-bold">What Makes This Different</h2>
            <p className="mt-1 text-sm text-ink-muted">
              Five deliberate design choices, not marketing claims — each one is a page or a feature you can go check right now.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="rounded border border-rule p-4">
              <div className="flex items-center gap-2">
                <Calculator className="h-4 w-4 text-accent shrink-0" />
                <span className="font-serif text-sm font-bold">Reliability, measured, not asserted</span>
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">
                Every score on the{" "}
                <Link href="/reliability" className="underline decoration-rule-strong underline-offset-2 hover:text-ink">
                  reliability desk
                </Link>{" "}
                carries its sample size next to it. Below 10 resolved claims, we show &ldquo;insufficient record&rdquo;
                instead of a number — see §2 below.
              </p>
            </div>
            <div className="rounded border border-rule p-4">
              <div className="flex items-center gap-2">
                <Flag className="h-4 w-4 text-accent shrink-0" />
                <span className="font-serif text-sm font-bold">First-report attribution</span>
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">
                We record who broke a story, not who republished it loudest. Event cards credit the outlet that
                reported first and how far ahead of the pack they were — not just whoever&apos;s headline you saw.
              </p>
            </div>
            <div className="rounded border border-rule p-4">
              <div className="flex items-center gap-2">
                <Route className="h-4 w-4 text-accent shrink-0" />
                <span className="font-serif text-sm font-bold">Rumour lifecycle view</span>
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">
                Every transfer saga is one page: every claim, who made it, what corroborated or contradicted it,
                and how it ended. Competitors show you today&apos;s article; we show you the whole arc.
              </p>
            </div>
            <div className="rounded border border-rule p-4">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-accent shrink-0" />
                <span className="font-serif text-sm font-bold">Two-speed delivery</span>
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">
                A speed lane pushes a bare factual alert within seconds of detection — no generated prose. An
                evidence lane follows with a grounded, sourced summary once it&apos;s actually verified.
              </p>
            </div>
          </div>
          <div className="rounded-lg border border-navy-950/20 bg-navy-950 p-5 text-paper">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 shrink-0" />
              <span className="font-serif text-sm font-bold">The no-invention guarantee</span>
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-paper-deep/80">
              Every published sentence traces back to stored evidence, and the interface will show you that evidence.
              In a market saturated with generated slop, verifiable restraint is the fifth differentiator — and the
              one the other four exist to protect.
            </p>
          </div>
        </section>

        {/* What this is / isn't */}
        <section className="space-y-3 rounded-lg border border-dashed border-rule-strong bg-paper p-6">
          <h2 className="font-serif text-lg font-bold">What This Is — and Isn&apos;t</h2>
          <p className="text-sm leading-relaxed text-ink-muted">
            The sports news app that keeps the receipts: we collect reporting from approved sources, group it into
            events, extract the specific claims each outlet makes, and track whether those claims turn out to be true.
          </p>
          <p className="text-xs font-semibold uppercase tracking-wide text-ink-faint">Explicitly not:</p>
          <ul className="grid grid-cols-1 gap-x-6 gap-y-1.5 text-sm text-ink-muted sm:grid-cols-2">
            <li className="flex items-start gap-2">
              <XCircle className="h-3.5 w-3.5 shrink-0 mt-0.5 text-disputed" /> A place to read full articles
            </li>
            <li className="flex items-start gap-2">
              <XCircle className="h-3.5 w-3.5 shrink-0 mt-0.5 text-disputed" /> An opinion or comment platform
            </li>
            <li className="flex items-start gap-2">
              <XCircle className="h-3.5 w-3.5 shrink-0 mt-0.5 text-disputed" /> A live-score product
            </li>
            <li className="flex items-start gap-2">
              <XCircle className="h-3.5 w-3.5 shrink-0 mt-0.5 text-disputed" /> A betting tipster
            </li>
            <li className="flex items-start gap-2">
              <XCircle className="h-3.5 w-3.5 shrink-0 mt-0.5 text-disputed" /> A personality-driven brand
            </li>
          </ul>
        </section>

        {/* 1. Wilson Lower Bound */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 border-b border-rule pb-2">
            <Calculator className="h-5 w-5 text-accent" />
            <h2 className="font-serif text-xl font-bold">1. Primary Metric: Wilson Score Interval Lower Bound</h2>
          </div>
          <p className="text-sm leading-relaxed text-ink-muted">
            Raw percentages (e.g. 2 correct out of 2 = 100%) are fundamentally misleading for evaluating journalists.
            A reporter with 45 correct out of 50 stories has demonstrated far higher reliability than someone who is 2 for 2.
            We compute the <strong>Wilson score interval lower bound</strong> at a 95% confidence level (\(z = 1.95996\)):
          </p>
          <div className="overflow-x-auto rounded bg-paper-deep p-4 font-mono text-xs text-ink border border-rule">
            {`p = correct / total\n`}
            {`z = 1.95996\n`}
            {`denominator = 1 + (z² / n)\n`}
            {`center = p + (z² / (2n))\n`}
            {`spread = z * sqrt((p * (1 - p) / n) + (z² / (4n²)))\n`}
            {`Wilson Lower Bound = (center - spread) / denominator`}
          </div>
          <p className="text-xs text-ink-faint italic">
            This guarantees that a source's score reflects the statistical lower bound of their true accuracy with 95% certainty.
          </p>
        </section>

        {/* 2. Sample Size Gating */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 border-b border-rule pb-2">
            <Scale className="h-5 w-5 text-accent" />
            <h2 className="font-serif text-xl font-bold">2. Display Gating: The 10-Claim Minimum Rule</h2>
          </div>
          <p className="text-sm leading-relaxed text-ink-muted">
            To prevent unfair reputational harm from tiny sample sizes, <strong>no score pill is ever rendered</strong> for an outlet or reporter
            with fewer than <strong>10 resolved claims</strong>.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="rounded border border-dashed border-rule-strong bg-paper p-4">
              <span className="font-mono text-xs font-semibold text-ink-faint">Below 10 Resolved Claims</span>
              <p className="mt-1 font-mono text-xs text-ink">
                &ldquo;Insufficient record · 3/4&rdquo;
              </p>
              <p className="mt-2 text-xs text-ink-muted">
                Displays the raw fraction only. Score color and Wilson lower bound are withheld.
              </p>
            </div>
            <div className="rounded border border-confirmed/30 bg-confirmed/[0.04] p-4">
              <span className="font-mono text-xs font-semibold text-confirmed">10+ Resolved Claims</span>
              <p className="mt-1 font-mono text-xs text-confirmed font-bold">
                &ldquo;68% · 24/31&rdquo;
              </p>
              <p className="mt-2 text-xs text-ink-muted">
                Public reliability pill unlocked, linking directly to the reporter&apos;s itemized dossier.
              </p>
            </div>
          </div>
        </section>

        {/* 3. Dual Reporting Architecture */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 border-b border-rule pb-2">
            <Split className="h-5 w-5 text-accent" />
            <h2 className="font-serif text-xl font-bold">3. Dual Reporting: Original Scoops vs. Wire Aggregation</h2>
          </div>
          <p className="text-sm leading-relaxed text-ink-muted">
            A core failure of modern sports aggregation is outlets repackaging wire reports and claiming credit when they turn out true.
            Under Handbook §5.2 rules:
          </p>
          <ul className="space-y-2 text-sm text-ink-muted">
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-confirmed shrink-0 mt-0.5" />
              <span><strong>Original Reporting (First-Party):</strong> Substantive breaking scoops and investigative claims. These directly determine the primary reputation score.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
              <span><strong>Aggregation & Repetition:</strong> Citing other outlets (&ldquo;according to reports in Spain...&rdquo;). Scored separately under repetition accuracy and <em>excluded from the primary Wilson score</em>.</span>
            </li>
          </ul>
        </section>

        {/* 4. Component Scoring */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 border-b border-rule pb-2">
            <History className="h-5 w-5 text-accent" />
            <h2 className="font-serif text-xl font-bold">4. Component Scoring (Preserving Partial Correctness)</h2>
          </div>
          <p className="text-sm leading-relaxed text-ink-muted">
            Sports journalism is rarely 100% binary. A reporter who identifies the correct target club and player but is off on the fee
            should not be scored the same as someone who fabricated an entire transfer. Resolutions evaluate four discrete components:
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded border border-rule p-3 text-center">
              <span className="font-mono text-xs font-bold text-navy-900">Entity</span>
              <p className="text-[11px] text-ink-muted mt-1">Player & Club accuracy</p>
            </div>
            <div className="rounded border border-rule p-3 text-center">
              <span className="font-mono text-xs font-bold text-navy-900">Direction</span>
              <p className="text-[11px] text-ink-muted mt-1">Signing vs. denial correctness</p>
            </div>
            <div className="rounded border border-rule p-3 text-center">
              <span className="font-mono text-xs font-bold text-navy-900">Timing</span>
              <p className="text-[11px] text-ink-muted mt-1">Window & contract duration</p>
            </div>
            <div className="rounded border border-rule p-3 text-center">
              <span className="font-mono text-xs font-bold text-navy-900">Fee / Detail</span>
              <p className="text-[11px] text-ink-muted mt-1">&plusmn;15% transfer fee precision</p>
            </div>
          </div>
        </section>

        {/* 5. Exponential Recency Decay */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 border-b border-rule pb-2">
            <History className="h-5 w-5 text-accent" />
            <h2 className="font-serif text-xl font-bold">5. Exponential Recency Decay</h2>
          </div>
          <p className="text-sm leading-relaxed text-ink-muted">
            Reporters change beats, lose sources, or improve rigor over time. Past claims are weighted using exponential recency decay
            with a half-life of <strong>90 days</strong> (~one full football season/transfer window):
          </p>
          <div className="overflow-x-auto rounded bg-paper-deep p-4 font-mono text-xs text-ink border border-rule">
            {`weight = 2 ^ (-delta_days / 90.0)`}
          </div>
          <p className="text-xs text-ink-faint">
            A story reported 90 days ago carries half the weight of breaking reporting from today; a story from two seasons ago carries 1/16th weight.
          </p>
        </section>

        {/* Footer Guarantee */}
        <section className="rounded-lg border border-rule bg-navy-950 p-6 text-paper">
          <h3 className="font-serif text-base font-bold text-paper">The No-Invention Guarantee</h3>
          <p className="mt-2 text-xs text-paper-deep/80 leading-relaxed">
            All evaluations rely strictly on Authority Rank 1–2 official announcements (clubs, leagues, federations) or multi-outlet consensus.
            Under no circumstances does an AI model invent or guess the resolution of a claim.
          </p>
        </section>
      </div>
    </div>
  );
}
