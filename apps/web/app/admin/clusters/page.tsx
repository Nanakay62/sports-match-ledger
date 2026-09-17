import type { Metadata } from "next";
import { AlertCircle, FileText, Layers, Network, Split, Tag } from "lucide-react";
import { fetchAdminClusters } from "@/lib/api";
import { formatDate } from "@/lib/format";

export const metadata: Metadata = {
  title: "Cluster Inspection · Editorial Control Plane",
};

export default async function AdminClustersPage() {
  const clusters = await fetchAdminClusters();
  const disputedCount = clusters.filter((c) => c.dispute_status === "active" || c.disputed_by_event_id).length;
  const multiEvidenceCount = clusters.filter((c) => c.evidence_count > 1).length;

  return (
    <div>
      <header className="border-b-2 border-ink pb-6">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-emerald-700">
          <Network className="size-3.5" />
          <span>Entity Graph & Deduplication · Handbook §4.3 & §14</span>
        </div>
        <h1 className="mt-2 font-display text-3xl font-medium tracking-tight md:text-4xl">
          Cluster Inspection & Disputation
        </h1>
        <p className="mt-2 text-[14.5px] text-ink-soft">
          Inspect cross-feed deduplication clusters, cross-language entity collapses, and automatic cluster-splits
          triggered by conflicting predicates (e.g. transfer denied vs official signing).
        </p>
      </header>

      {/* Overview Stat Cards */}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="border border-rule bg-paper p-4">
          <div className="font-mono text-[11px] uppercase tracking-wider text-ink-faint">
            Total Event Clusters
          </div>
          <div className="mt-1 font-display text-2xl font-bold text-ink">
            {clusters.length}
          </div>
        </div>
        <div className="border border-rule bg-paper p-4">
          <div className="font-mono text-[11px] uppercase tracking-wider text-ink-faint">
            Active Predicate Disputes
          </div>
          <div className="mt-1 font-display text-2xl font-bold text-rose-600">
            {disputedCount}
          </div>
        </div>
        <div className="border border-rule bg-paper p-4">
          <div className="font-mono text-[11px] uppercase tracking-wider text-ink-faint">
            Multi-Source Corroboration
          </div>
          <div className="mt-1 font-display text-2xl font-bold text-emerald-700">
            {multiEvidenceCount}
          </div>
        </div>
      </div>

      <section className="mt-8" aria-label="Event clusters list">
        <div className="flex items-baseline justify-between border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-ink-faint">
          <span>{clusters.length} clusters on record</span>
          <span>Window: 48h deduplication</span>
        </div>

        {clusters.length === 0 ? (
          <div className="py-16 text-center text-ink-faint">
            <Layers className="mx-auto size-8 text-ink-faint opacity-60" />
            <p className="mt-2 text-[14px]">No event clusters indexed in database.</p>
          </div>
        ) : (
          <div className="mt-4 space-y-4">
            {clusters.map((cluster) => {
              const isDisputed = Boolean(cluster.dispute_status === "active" || cluster.disputed_by_event_id);

              return (
                <div
                  key={cluster.event_id}
                  className={`border bg-paper p-5 transition-shadow hover:shadow-sm ${
                    isDisputed ? "border-rose-300 bg-rose-50/20" : "border-rule"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rule/60 pb-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-[11px] font-semibold text-ink-faint">
                        {cluster.event_id}
                      </span>
                      <span className="text-ink-faint">·</span>
                      <span className="rounded bg-ink/5 px-2 py-0.5 font-mono text-[10.5px] uppercase text-ink">
                        {cluster.sport} / {cluster.competition}
                      </span>
                      {isDisputed ? (
                        <span className="inline-flex items-center gap-1 rounded bg-rose-100 px-2 py-0.5 font-mono text-[10.5px] font-semibold uppercase text-rose-800">
                          <Split className="size-3" />
                          DISPUTED CLUSTER-SPLIT
                        </span>
                      ) : (
                        <span className="rounded bg-stone-100 px-2 py-0.5 font-mono text-[10.5px] font-semibold uppercase text-stone-700">
                          {cluster.status}
                        </span>
                      )}
                    </div>
                    <div className="font-mono text-[11px] text-ink-faint">
                      Updated {formatDate(cluster.updated_at)}
                    </div>
                  </div>

                  <div className="mt-3">
                    <h2 className="font-display text-lg font-semibold text-ink">
                      {cluster.headline}
                    </h2>

                    {isDisputed && cluster.disputed_by_event_id && (
                      <div className="mt-2.5 flex items-center gap-2 rounded border border-rose-200 bg-rose-50 p-2.5 text-[12.5px] text-rose-900">
                        <AlertCircle className="size-4 shrink-0 text-rose-600" />
                        <div>
                          <span className="font-semibold font-mono text-[11.5px]">Contradiction Link: </span>
                          <span>
                            Contradictory predicate detected with event cluster{" "}
                            <span className="font-mono font-bold">{cluster.disputed_by_event_id}</span>.
                            Automatically split into distinct dispute threads per Handbook §14.
                          </span>
                        </div>
                      </div>
                    )}

                    <div className="mt-4 flex flex-wrap items-center gap-4 text-[13px] text-ink-soft">
                      <div className="flex items-center gap-1.5">
                        <FileText className="size-3.5 text-ink-faint" />
                        <span>
                          <strong className="text-ink">{cluster.claims_count}</strong> claims
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Layers className="size-3.5 text-ink-faint" />
                        <span>
                          <strong className="text-ink">{cluster.evidence_count}</strong> corroborating evidence
                        </span>
                      </div>
                      {cluster.first_reported_outlet && (
                        <div className="font-mono text-[11px] text-ink-faint">
                          First reported by: <span className="text-ink">{cluster.first_reported_outlet}</span>
                        </div>
                      )}
                    </div>

                    {cluster.entities && cluster.entities.length > 0 && (
                      <div className="mt-3 flex flex-wrap items-center gap-1.5 pt-2">
                        <Tag className="size-3 text-ink-faint" />
                        {cluster.entities.map((entity, idx) => (
                          <span
                            key={idx}
                            className="rounded border border-rule bg-stone-50 px-2 py-0.5 font-mono text-[10.5px] text-ink-soft"
                          >
                            {entity.name} <span className="text-ink-faint">({entity.type})</span>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
