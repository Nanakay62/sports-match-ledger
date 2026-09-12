import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  CheckCircle,
  Clock,
  FileText,
  Radio,
  ShieldAlert,
} from "lucide-react";
import { StatusBadge } from "@/components/status-badge";
import { EntityChip } from "@/components/entity-chip";
import { loadRumourLifecycle } from "@/lib/data-loader";
import { formatDate, timeAgo } from "@/lib/format";
import { getDictionary } from "@/lib/i18n";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const lifecycle = await loadRumourLifecycle(id);
  return {
    title: lifecycle ? `Rumour Lifecycle: ${lifecycle.event.headline}` : "Rumour not found",
  };
}

export default async function RumourLifecyclePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ lang?: string }>;
}) {
  const { id } = await params;
  const sParams = searchParams ? await searchParams : undefined;
  const lang = sParams?.lang || "en";
  const t = getDictionary(lang);
  const querySuffix = lang !== "en" ? `?lang=${lang}` : "";

  const lifecycle = await loadRumourLifecycle(id, lang);
  if (!lifecycle) notFound();

  const { event, claims, stages } = lifecycle;

  return (
    <main className="mx-auto max-w-4xl px-4 pb-24 pt-6 md:px-6">
      {/* Breadcrumb */}
      <nav
        className="font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink-faint"
        aria-label="Breadcrumb"
      >
        <Link href={`/${querySuffix}`} className="hover:text-ink">
          {t.navLedger}
        </Link>
        <span className="mx-1.5">/</span>
        <Link href={`/event/${event.id}${querySuffix}`} className="hover:text-ink">
          Event {event.id}
        </Link>
        <span className="mx-1.5">/</span>
        <span>{t.lifecycleBreadcrumb}</span>
      </nav>

      <header className="mt-6 border-b-2 border-ink pb-6">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-faint">
          <Radio className="size-3.5 text-ledger" aria-hidden />
          <span>{t.lifecycleEngine}</span>
        </div>
        <h1 className="mt-2 font-display text-3xl font-medium tracking-tight md:text-4xl">
          {event.headline}
        </h1>
        <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-ink-soft">
          {t.lifecycleDesc}
        </p>

        <div className="mt-5 flex flex-wrap items-center gap-4">
          <StatusBadge status={event.status} size="stamp" />
          <span className="font-mono text-[12px] text-ink-faint">
            {event.independentSources} {t.sourcesOnRecord} · {claims.length} {t.claimsOnFile}
          </span>
        </div>

        <div className="mt-4 flex flex-wrap gap-1.5">
          {event.entities.map((e) => (
            <EntityChip key={e.name} entity={e} />
          ))}
        </div>
      </header>

      {/* Trajectory Strip */}
      <section className="mt-10" aria-label="Lifecycle progression">
        <h2 className="border-b border-rule pb-2 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-faint">
          {t.trajectoryMap}
        </h2>

        <div className="relative mt-8 space-y-8 pl-8 before:absolute before:bottom-3 before:left-3.5 before:top-2 before:w-0.5 before:bg-rule-strong">
          {stages.map((stage, idx) => {
            const isResolution = stage.stage === "resolution";
            const isDispute = stage.stage === "dispute";
            const isOrigin = stage.stage === "origin";

            return (
              <div key={idx} className="relative">
                {/* Node dot on trajectory line */}
                <div
                  className={`absolute -left-8 top-1 flex size-7 items-center justify-center rounded-full border-2 bg-paper text-[11px] font-mono font-medium ${
                    isResolution
                      ? "border-confirmed text-confirmed"
                      : isDispute
                      ? "border-disputed text-disputed"
                      : isOrigin
                      ? "border-ink text-ink"
                      : "border-rule-strong text-ink-soft"
                  }`}
                >
                  {idx + 1}
                </div>

                <div className="rounded border border-rule bg-paper p-5 transition-colors hover:border-ink/60">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rule/60 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-ink">
                        {isOrigin
                          ? t.stageOrigin
                          : isDispute
                          ? t.stageDispute
                          : isResolution
                          ? t.stageResolution
                          : `${t.stageCorroboration} #${idx}`}
                      </span>
                      {stage.outlet && (
                        <span className="font-mono text-[11.5px] text-ink-soft">
                          · {stage.reporter ? `${stage.reporter} (${stage.outlet})` : stage.outlet}
                        </span>
                      )}
                    </div>
                    <span className="font-mono text-[11px] text-ink-faint">
                      <span suppressHydrationWarning>{timeAgo(stage.timestamp)}</span> (
                      {formatDate(stage.timestamp)})
                    </span>
                  </div>

                  <p className="mt-3 text-[14.5px] leading-relaxed text-ink-soft">
                    "{stage.text}"
                  </p>

                  <div className="mt-3 flex items-center justify-between font-mono text-[11px] text-ink-faint">
                    <span>
                      State:{" "}
                      <span className="font-medium text-ink capitalize">{stage.status}</span>
                    </span>
                    {isResolution && (
                      <span className="inline-flex items-center gap-1 font-semibold text-confirmed">
                        <CheckCircle className="size-3.5" /> Outcome Verified
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <footer className="mt-12 border-t border-rule pt-6">
        <Link
          href={`/event/${event.id}${querySuffix}`}
          className="inline-flex items-center gap-2 font-mono text-[12px] text-ledger hover:underline"
        >
          <ArrowLeft className="size-3.5" /> Back to full event dossier
        </Link>
      </footer>
    </main>
  );
}
