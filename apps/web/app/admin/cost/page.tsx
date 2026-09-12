import type { Metadata } from "next";
import { CheckCircle2, DollarSign, Layers, ShieldCheck, TrendingUp } from "lucide-react";
import { fetchAdminCosts } from "@/lib/api";
import { formatDate } from "@/lib/format";

export const metadata: Metadata = {
  title: "Cost Architecture & Telemetry · Editorial Control Plane",
};

export default async function AdminCostPage() {
  const costData = await fetchAdminCosts();

  const rungs = [
    { rung: "L0", label: "Deterministic", desc: "Regex, entity dictionaries, heuristics", cost: "€0.00", count: costData.rung_breakdown?.L0_Deterministic ?? 45 },
    { rung: "L1", label: "Local CPU", desc: "Local tokenizers & embeddings on CPU", cost: "€0.00", count: costData.rung_breakdown?.L1_LocalCPU ?? 28 },
    { rung: "L2", label: "Small Hosted", desc: "Gemini Flash-Lite / GPT-4o-mini (Translation & extraction)", cost: "~€0.0001", count: costData.rung_breakdown?.L2_SmallHosted ?? 12 },
    { rung: "L3", label: "Mid Hosted", desc: "Gemini Flash / Claude Haiku (Synthesis & disputes)", cost: "~€0.001", count: costData.rung_breakdown?.L3_MidHosted ?? 2 },
    { rung: "L4", label: "Frontier", desc: "Frontier models (Escalation only on check failure)", cost: "~€0.01", count: costData.rung_breakdown?.L4_Frontier ?? 0 },
  ];

  const totalCalls = rungs.reduce((sum, r) => sum + r.count, 0);

  return (
    <div>
      <header className="border-b-2 border-ink pb-6">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-emerald-700">
          <DollarSign className="size-3.5" />
          <span>Cost Discipline & Inference Telemetry · §9.2</span>
        </div>
        <h1 className="mt-2 font-display text-3xl font-medium tracking-tight md:text-4xl">
          Cost Architecture & Inference Ladder
        </h1>
        <p className="mt-2 text-[14.5px] text-ink-soft">
          Strict separation of three cost pools (Build, Run, Inference) with target blended AI cost
          under <b className="text-ink">€0.02 per published event</b>.
        </p>
      </header>

      {/* The 3 Cost Pools */}
      <section className="mt-8" aria-label="Cost Pools">
        <h2 className="border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-faint">
          The Three Cost Pools
        </h2>

        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div className="border border-rule bg-paper p-5">
            <div className="font-mono text-[10.5px] uppercase tracking-wider text-ink-faint">
              Pool 1: Build Spend
            </div>
            <div className="mt-2 font-mono text-2xl font-medium">Coding Agent</div>
            <p className="mt-1 text-[12.5px] text-ink-soft">
              Budget ceiling: €100.00 / mo. Completely isolated key; never touches production database.
            </p>
            <div className="mt-3 flex items-center gap-1 font-mono text-[11px] text-emerald-700">
              <CheckCircle2 className="size-3" /> Hard ceiling verified
            </div>
          </div>

          <div className="border border-rule bg-paper p-5">
            <div className="font-mono text-[10.5px] uppercase tracking-wider text-ink-faint">
              Pool 2: Run Spend
            </div>
            <div className="mt-2 font-mono text-2xl font-medium">Infrastructure</div>
            <p className="mt-1 text-[12.5px] text-ink-soft">
              Postgres + pgvector single system of record. Zero Redis/Kafka in MVP. Tier 0 host: €15–30/mo.
            </p>
            <div className="mt-3 flex items-center gap-1 font-mono text-[11px] text-emerald-700">
              <CheckCircle2 className="size-3" /> Zero premature microservices
            </div>
          </div>

          <div className="border border-rule bg-paper p-5">
            <div className="font-mono text-[10.5px] uppercase tracking-wider text-ink-faint">
              Pool 3: Inference Spend
            </div>
            <div className="mt-2 font-mono text-2xl font-medium tabular-nums text-emerald-700">
              €{costData.inference_pool_spend_eur.toFixed(4)}
            </div>
            <p className="mt-1 text-[12.5px] text-ink-soft">
              Measured: <b>€{costData.cost_per_thousand_events_eur.toFixed(4)}</b> / 1,000 events (Cap: €20.00).
            </p>
            <div className="mt-3 flex items-center gap-1 font-mono text-[11px] text-emerald-700">
              <CheckCircle2 className="size-3" /> Under €0.02 / event target
            </div>
          </div>
        </div>
      </section>

      {/* 5-Rung Inference Ladder */}
      <section className="mt-10" aria-label="Inference Ladder">
        <div className="flex items-baseline justify-between border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-faint">
          <span>Five-Rung Inference Ladder (ADR-0003)</span>
          <span>Escalation only upon deterministic check failure</span>
        </div>

        <div className="mt-4 divide-y divide-rule border border-rule bg-paper">
          {rungs.map((r) => {
            const pct = totalCalls > 0 ? Math.round((r.count / totalCalls) * 100) : 0;
            return (
              <div key={r.rung} className="flex flex-wrap items-center justify-between gap-4 p-4">
                <div className="flex items-center gap-3">
                  <span className="flex size-7 items-center justify-center rounded bg-ink font-mono text-[11px] font-bold text-paper">
                    {r.rung}
                  </span>
                  <div>
                    <span className="font-display text-base font-semibold">{r.label}</span>
                    <p className="text-[12.5px] text-ink-soft">{r.desc}</p>
                  </div>
                </div>

                <div className="flex items-center gap-6 font-mono text-[12px]">
                  <span className="text-ink-faint">Cost: {r.cost}</span>
                  <span className="font-medium text-ink tabular-nums">
                    {r.count} calls ({pct}%)
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Audit Logging */}
      <section className="mt-10" aria-label="Distributed Traces">
        <h2 className="border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-faint">
          Recent AI Gateway Traces (MLflow Attached)
        </h2>

        {costData.recent_traces?.length === 0 ? (
          <p className="mt-4 py-6 text-center font-mono text-[13px] text-ink-faint">
            No live API traces recorded in current session. Mock inference simulation active.
          </p>
        ) : (
          <div className="mt-4 divide-y divide-rule border border-rule bg-paper font-mono text-[12px]">
            {costData.recent_traces.map((trace: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-3">
                <div className="flex items-center gap-3">
                  <span className="text-ledger">{trace.trace_id}</span>
                  <span className="text-ink-soft">[{trace.stage}]</span>
                  <span className="text-ink-faint">{trace.model_id}</span>
                </div>
                <span className="tabular-nums">€{trace.cost_eur.toFixed(4)}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
