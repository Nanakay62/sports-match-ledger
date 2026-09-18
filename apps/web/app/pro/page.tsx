import type { Metadata } from "next";
import Link from "next/link";
import { Check, Minus } from "lucide-react";
import { ProCta } from "@/components/pro-cta";
import { ManageSubscription } from "@/components/manage-subscription";
import { getDictionary } from "@/lib/i18n";

export const metadata: Metadata = { title: "Upgrade: Pro" };

type CellValue = string | boolean;

const ROWS: { feature: string; free: CellValue; pro: CellValue }[] = [
  { feature: "Current status & evidence for every tracked claim", free: true, pro: true },
  { feature: "Public reliability scores & profiles", free: true, pro: true },
  { feature: "Claim history depth", free: "Most recent entries", pro: "Full audit trail" },
  { feature: "Watchlists", free: "3 stories", pro: "Unlimited" },
  { feature: "Alerts", free: "Daily digest", pro: "Real-time" },
  { feature: "Export (CSV / JSON)", free: false, pro: true },
];

const FAQ = [
  {
    q: "Will a story's status ever move behind the paywall?",
    a: "No: never. The current status of every claim, from Confirmed to Corrected, is free and always will be. Pro only deepens the record behind the status: history, exports, alerts and watchlist limits.",
  },
  {
    q: "How is a claim marked correct or incorrect?",
    a: "Against the recorded outcome: official announcements, league filings, confirmed results. Each resolution is timestamped and attributed, so every score can be audited back to source.",
  },
  {
    q: "What happens when a source gets it wrong?",
    a: "It stays on their record. Entries are amended, never deleted; a Corrected status is permanent, and the full resolution history is part of every profile.",
  },
];

function Cell({ v }: { v: CellValue }) {
  return (
    <div className="flex items-center justify-center px-2 py-3 text-center">
      {v === true ? (
        <Check className="size-4 text-ledger" aria-label="Included" />
      ) : v === false ? (
        <Minus className="size-4 text-ink-faint" aria-label="Not included" />
      ) : (
        <span className="text-[12.5px] text-ink-soft">{v}</span>
      )}
    </div>
  );
}

export default async function ProPage({
  searchParams,
}: {
  searchParams?: Promise<{ lang?: string; checkout?: string }>;
}) {
  const sParams = searchParams ? await searchParams : undefined;
  const lang = sParams?.lang || "en";
  const t = getDictionary(lang);
  const querySuffix = lang !== "en" ? `?lang=${lang}` : "";
  const checkoutState = sParams?.checkout;

  return (
    <main className="mx-auto max-w-4xl px-4 pb-20 md:px-6">
      <p className="pt-10 font-mono text-[10.5px] uppercase tracking-[0.16em] text-ink-faint">{t.navUpgrade}</p>
      <h1 className="mt-2 max-w-2xl font-display text-4xl font-medium leading-[1.08] tracking-tight md:text-5xl">
        {t.proTitle}
      </h1>

      {checkoutState === "success" && (
        <div className="mt-6 border-2 border-confirmed px-5 py-4 text-[14px] text-confirmed">
          Subscription confirmed — thank you. It can take a few seconds for Pro access to activate once Stripe
          confirms payment.
        </div>
      )}
      {checkoutState === "cancelled" && (
        <div className="mt-6 border-2 border-rule-strong px-5 py-4 text-[14px] text-ink-soft">
          Checkout was cancelled. Nothing was charged, and nothing about the free ledger changed.
        </div>
      )}

      <div className="mt-6 border-2 border-ink px-5 py-4 md:px-6">
        <p className="font-display text-[17px] leading-relaxed md:text-lg">
          <span className="font-semibold">{t.proPromiseTitle}</span> {t.proPromiseText}
        </p>
      </div>

      {/* Comparison */}
      <section className="mt-10" aria-label="Free vs Pro">
        <div className="border border-rule-strong">
          <div className="grid grid-cols-[minmax(0,1fr)_110px_110px] border-b-2 border-ink font-mono text-[10.5px] uppercase tracking-[0.12em] text-ink-faint">
            <div className="px-3 py-2.5">What you get</div>
            <div className="py-2.5 text-center">Free</div>
            <div className="bg-ledger/[0.05] py-2.5 text-center font-semibold text-ledger">Pro</div>
          </div>
          {ROWS.map((r) => (
            <div key={r.feature} className="grid grid-cols-[minmax(0,1fr)_110px_110px] items-stretch border-b border-rule last:border-b-0">
              <div className="self-center px-3 py-3 text-[13.5px]">{r.feature}</div>
              <Cell v={r.free} />
              <div className="bg-ledger/[0.04]">
                <Cell v={r.pro} />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="mt-10 grid gap-px border border-ink/80 bg-rule md:grid-cols-2" aria-label="Pricing">
        <div className="bg-paper p-6">
          <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-ink-faint">{t.monthly}</div>
          <div className="mt-2 font-mono text-4xl font-medium tabular-nums">
            £6<span className="text-base text-ink-faint"> {t.perMonth}</span>
          </div>
          <ul className="mt-4 space-y-1.5 text-[13.5px] text-ink-soft">
            {["Everything in Free, forever", "Full audit trail on every claim", "Unlimited watchlists", "Real-time status alerts", "CSV & JSON export"].map((f) => (
              <li key={f} className="flex items-start gap-2">
                <Check className="mt-0.5 size-3.5 shrink-0 text-ledger" aria-hidden /> {f}
              </li>
            ))}
          </ul>
          <div className="mt-5">
            <ProCta label={t.startMonthly} planId="plan_pro_monthly" />
          </div>
        </div>

        <div className="relative bg-paper p-6">
          <span className="absolute right-4 top-4 rotate-2 rounded-[2px] border-2 border-confirmed/70 px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-confirmed">
            Best value
          </span>
          <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-ink-faint">{t.annual}</div>
          <div className="mt-2 font-mono text-4xl font-medium tabular-nums">
            £45<span className="text-base text-ink-faint"> {t.perYear}</span>
          </div>
          <p className="mt-1 font-mono text-[11px] text-ink-faint">≈ £3.75 a month · 4.5 months free (&lt; 8 months billing)</p>
          <ul className="mt-4 space-y-1.5 text-[13.5px] text-ink-soft">
            {["Everything in Monthly", "Priority alerting queue", "Save £27 over monthly billing (37% saving)", "Single invoice for tax/expenses"].map((f) => (
              <li key={f} className="flex items-start gap-2">
                <Check className="mt-0.5 size-3.5 shrink-0 text-ledger" aria-hidden /> {f}
              </li>
            ))}
          </ul>
          <div className="mt-5">
            <ProCta label={t.startAnnual} planId="plan_pro_annual" />
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="mt-14" aria-label="Frequently asked questions">
        <h2 className="font-display text-2xl font-medium">Frequently asked questions</h2>
        <dl className="mt-6 divide-y divide-rule border-y border-rule">
          {FAQ.map((item) => (
            <div key={item.q} className="py-5">
              <dt className="font-display text-base font-medium">{item.q}</dt>
              <dd className="mt-2 text-[14px] leading-relaxed text-ink-soft">{item.a}</dd>
            </div>
          ))}
        </dl>
      </section>

      {/* Manage existing subscription */}
      <section className="mt-14 border border-rule-strong px-5 py-5" aria-label="Manage your subscription">
        <h2 className="font-display text-lg font-medium">Already subscribed?</h2>
        <p className="mt-1 text-[13.5px] text-ink-soft">
          Enter the email you subscribed with to change your plan, update your card, or cancel — handled entirely by
          Stripe, no email to us required.
        </p>
        <div className="mt-4">
          <ManageSubscription />
        </div>
      </section>
    </main>
  );
}