import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Database, DollarSign, ShieldAlert, Users } from "lucide-react";
import { fetchAdminOverview } from "@/lib/api";

export const metadata: Metadata = {
  title: "Editorial Control Plane · Overview",
};

export default async function AdminOverviewPage() {
  const stats = await fetchAdminOverview();

  return (
    <div>
      <header className="border-b-2 border-ink pb-6">
        <h1 className="font-display text-3xl font-medium tracking-tight md:text-4xl">
          Control Plane Overview
        </h1>
        <p className="mt-2 text-[14.5px] text-ink-soft">
          Operational telemetry, pipeline status, and editorial governance queues for the
          Accountability Ledger.
        </p>
      </header>

      {/* Primary KPI Grid */}
      <section className="mt-8 grid grid-cols-2 gap-px border border-rule bg-rule md:grid-cols-4" aria-label="System Metrics">
        <div className="bg-paper p-5">
          <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-ink-faint">
            Total Ledger Events
          </div>
          <div className="mt-2 font-mono text-3xl font-medium tabular-nums">{stats.total_events}</div>
          <div className="mt-1 font-mono text-[11px] text-ink-faint">Verified event clusters</div>
        </div>

        <div className="bg-paper p-5">
          <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-ink-faint">
            Total Claims On Record
          </div>
          <div className="mt-2 font-mono text-3xl font-medium tabular-nums">{stats.total_claims}</div>
          <div className="mt-1 font-mono text-[11px] text-ink-faint">Append-only statements</div>
        </div>

        <div className="bg-paper p-5">
          <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-ink-faint">
            Pending Source Reviews
          </div>
          <div className="mt-2 font-mono text-3xl font-medium tabular-nums text-amber-600">
            {stats.pending_source_reviews}
          </div>
          <div className="mt-1 font-mono text-[11px] text-ink-faint">Awaiting technical/rights check</div>
        </div>

        <div className="bg-paper p-5">
          <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-ink-faint">
            Human Review Queue
          </div>
          <div className="mt-2 font-mono text-3xl font-medium tabular-nums text-rose-600">
            {stats.pending_human_reviews}
          </div>
          <div className="mt-1 font-mono text-[11px] text-ink-faint">Disputes & single-source leaks</div>
        </div>
      </section>

      {/* Cost KPIs */}
      <section className="mt-6 grid grid-cols-1 gap-px border border-rule bg-rule md:grid-cols-2" aria-label="Cost Metrics">
        <div className="bg-paper p-5">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-ink-faint">
              Cost Per 1,000 Events
            </span>
            <span className="rounded bg-emerald-100 px-2 py-0.5 font-mono text-[10px] text-emerald-800">
              Within Target
            </span>
          </div>
          <div className="mt-2 font-mono text-3xl font-medium tabular-nums text-emerald-700">
            €{stats.cost_per_thousand_events_eur.toFixed(4)}
          </div>
          <p className="mt-1 text-[12.5px] text-ink-soft">
            Target: &lt; €20.00 per 1,000 events (€0.02/event). Deduplication & L0/L1 rung routing active.
          </p>
        </div>

        <div className="bg-paper p-5">
          <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-ink-faint">
            Inference Spend (Pool 3)
          </div>
          <div className="mt-2 font-mono text-3xl font-medium tabular-nums">
            €{stats.total_inference_spend_eur.toFixed(4)}
          </div>
          <p className="mt-1 text-[12.5px] text-ink-soft">
            Isolated from Build & Run pools. Tracks all L2–L4 model calls via AI Gateway.
          </p>
        </div>
      </section>

      {/* Quick Action Navigation */}
      <section className="mt-10" aria-label="Control modules">
        <h2 className="border-b-2 border-ink pb-2 font-display text-xl font-medium">
          Editorial Modules
        </h2>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <Link
            href="/admin/sources"
            className="group block border border-rule bg-paper p-5 transition-colors hover:border-ink"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="size-4 text-ink-soft" />
                <h3 className="font-display text-lg font-medium group-hover:underline">
                  Source Registry
                </h3>
              </div>
              <ArrowRight className="size-4 text-ink-faint transition-transform group-hover:translate-x-1" />
            </div>
            <p className="mt-2 text-[13px] text-ink-soft">
              Manage the 4-stage intake state machine: PROPOSED → TECHNICAL_REVIEW → RIGHTS_REVIEW → APPROVED.
            </p>
          </Link>

          <Link
            href="/admin/review"
            className="group block border border-rule bg-paper p-5 transition-colors hover:border-ink"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldAlert className="size-4 text-rose-600" />
                <h3 className="font-display text-lg font-medium group-hover:underline">
                  Human Review Queue
                </h3>
              </div>
              <ArrowRight className="size-4 text-ink-faint transition-transform group-hover:translate-x-1" />
            </div>
            <p className="mt-2 text-[13px] text-ink-soft">
              Editorial triage for contested claims, uncorroborated single-source scoops, and conflicting transfer numbers.
            </p>
          </Link>

          <Link
            href="/admin/entities"
            className="group block border border-rule bg-paper p-5 transition-colors hover:border-ink"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="size-4 text-ink-soft" />
                <h3 className="font-display text-lg font-medium group-hover:underline">
                  Entity Corrections & Graph
                </h3>
              </div>
              <ArrowRight className="size-4 text-ink-faint transition-transform group-hover:translate-x-1" />
            </div>
            <p className="mt-2 text-[13px] text-ink-soft">
              Map international bylines, multilingual club names, and player aliases to canonical entities.
            </p>
          </Link>

          <Link
            href="/admin/cost"
            className="group block border border-rule bg-paper p-5 transition-colors hover:border-ink"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <DollarSign className="size-4 text-emerald-600" />
                <h3 className="font-display text-lg font-medium group-hover:underline">
                  Cost & Inference Telemetry
                </h3>
              </div>
              <ArrowRight className="size-4 text-ink-faint transition-transform group-hover:translate-x-1" />
            </div>
            <p className="mt-2 text-[13px] text-ink-soft">
              Inference ladder execution stats, token consumption per stage, and MLflow gateway trace log.
            </p>
          </Link>
        </div>
      </section>
    </div>
  );
}
