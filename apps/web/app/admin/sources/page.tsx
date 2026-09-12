import type { Metadata } from "next";
import { ArrowUpRight, Check, CheckCircle2, Clock, Globe, Shield } from "lucide-react";
import { fetchAdminSources } from "@/lib/api";

export const metadata: Metadata = {
  title: "Source Registry · Editorial Control Plane",
};

export default async function AdminSourcesPage({
  searchParams,
}: {
  searchParams?: Promise<{ status?: string }>;
}) {
  const params = searchParams ? await searchParams : undefined;
  const filterStatus = params?.status || "";
  const allSources = await fetchAdminSources();

  const sources = filterStatus
    ? allSources.filter((s) => s.status === filterStatus)
    : allSources;

  return (
    <div>
      <header className="border-b-2 border-ink pb-6">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-faint">
          <Shield className="size-3.5 text-ledger" />
          <span>Intake State Machine · Handbook §11</span>
        </div>
        <h1 className="mt-2 font-display text-3xl font-medium tracking-tight md:text-4xl">
          Source Registry
        </h1>
        <p className="mt-2 text-[14.5px] text-ink-soft">
          All ingested RSS/Atom and official feeds must pass both technical connectivity and legal
          rights review before receiving APPROVED polling status.
        </p>
      </header>

      {/* Status Filter Tabs */}
      <div className="mt-6 flex flex-wrap items-center gap-2 border-b border-rule pb-3 font-mono text-[12px]">
        {[
          { label: "All sources", value: "" },
          { label: "Approved (Active)", value: "approved" },
          { label: "Proposed", value: "proposed" },
          { label: "Technical Review", value: "technical_review" },
          { label: "Rights Review", value: "rights_review" },
        ].map((tab) => {
          const isActive = filterStatus === tab.value;
          return (
            <a
              key={tab.value}
              href={`/admin/sources${tab.value ? `?status=${tab.value}` : ""}`}
              className={`rounded px-2.5 py-1 transition-colors ${
                isActive
                  ? "bg-ink font-semibold text-paper"
                  : "border border-rule bg-paper text-ink-soft hover:border-ink hover:text-ink"
              }`}
            >
              {tab.label}
            </a>
          );
        })}
      </div>

      {/* Sources List */}
      <section className="mt-6" aria-label="Registered sources">
        <div className="flex items-baseline justify-between border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-ink-faint">
          <span>{sources.length} sources listed</span>
          <span>Polling interval: 15–60m</span>
        </div>

        <div className="mt-4 divide-y divide-rule border border-rule bg-paper">
          {sources.map((s) => {
            const isApproved = s.status === "approved";
            return (
              <div key={s.id} className="p-4 transition-colors hover:bg-rule/10">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span className="font-display text-base font-semibold">{s.source_name}</span>
                    <span className="rounded border border-rule px-1.5 py-0.5 font-mono text-[10.5px] text-ink-faint">
                      {s.language.toUpperCase()}
                    </span>
                    <span className="rounded bg-rule/50 px-1.5 py-0.5 font-mono text-[10.5px] text-ink-soft">
                      Rank {s.authority_rank}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded px-2 py-0.5 font-mono text-[10.5px] uppercase tracking-wider font-semibold ${
                        isApproved
                          ? "bg-emerald-100 text-emerald-800"
                          : s.status === "rights_review"
                          ? "bg-blue-100 text-blue-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {s.status.replace("_", " ")}
                    </span>
                  </div>
                </div>

                <div className="mt-2 flex flex-wrap items-center gap-x-6 gap-y-1 text-[12.5px] text-ink-faint">
                  <a
                    href={s.feed_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 font-mono text-[11.5px] text-ledger hover:underline"
                  >
                    <Globe className="size-3" /> Feed XML <ArrowUpRight className="size-2.5" />
                  </a>
                  <span>Category: <b className="text-ink-soft">{s.coverage_category}</b></span>
                  <span>Polling: every {s.polling_interval_minutes} min</span>
                  {s.technical_check_passed && (
                    <span className="inline-flex items-center gap-1 text-emerald-700">
                      <Check className="size-3" /> Tech pass
                    </span>
                  )}
                  {s.rights_review_passed && (
                    <span className="inline-flex items-center gap-1 text-emerald-700">
                      <CheckCircle2 className="size-3" /> Rights pass
                    </span>
                  )}
                </div>

                {(s.technical_notes || s.rights_notes) && (
                  <div className="mt-2 rounded bg-rule/30 p-2 text-[12px] text-ink-soft">
                    {s.technical_notes && <div>• <b>Technical note:</b> {s.technical_notes}</div>}
                    {s.rights_notes && <div>• <b>Rights review:</b> {s.rights_notes}</div>}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
