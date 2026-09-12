import Link from "next/link";
import { LeadStory } from "@/components/lead-story";
import { TopicFeed, type FeedItem } from "@/components/topic-feed";
import { buildStatusReasoning } from "@/lib/evidence";
import { loadAllEvents, loadClaims } from "@/lib/data-loader";
import { getDictionary } from "@/lib/i18n";

export default async function HomePage({
  searchParams,
}: {
  searchParams?: Promise<{ lang?: string; status?: string }>;
}) {
  const params = searchParams ? await searchParams : undefined;
  const lang = params?.lang || "en";
  const currentStatus = params?.status || "";
  const t = getDictionary(lang);

  const filterTabs = [
    { label: t.tabAll, value: "" },
    { label: t.tabDeveloping, value: "developing" },
    { label: t.tabConfirmed, value: "confirmed" },
    { label: t.tabRumours, value: "rumour" },
    { label: t.tabDisputed, value: "disputed" },
    { label: t.tabCorrected, value: "corrected" },
  ];

  const allEvents = await loadAllEvents(currentStatus || undefined, lang);
  const leadEvent = allEvents[0];
  const otherEvents = allEvents.slice(1);

  const leadClaims = leadEvent ? await loadClaims(leadEvent.id, lang) : [];
  const leadReasoning = leadEvent ? buildStatusReasoning(leadEvent, leadClaims) : [];

  const feedItems: FeedItem[] = await Promise.all(
    otherEvents.map(async (event) => {
      const claims = await loadClaims(event.id, lang);
      return {
        event,
        reasoning: buildStatusReasoning(event, claims),
      };
    })
  );

  return (
    <main className="mx-auto max-w-6xl px-4 pb-24 pt-6 md:px-6">
      {/* Top Banner / Thesis Statement */}
      <section className="mb-8 border-b border-rule pb-4">
        <div className="flex flex-wrap items-baseline justify-between gap-4">
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-ink-faint">
            {t.thesisBar}
          </p>
          <span className="font-mono text-[11px] text-ink-faint">
            {allEvents.length} {t.storiesTracked}
          </span>
        </div>
      </section>

      {/* Filter Tabs / Fast-lane switcher */}
      <section className="mb-8 overflow-x-auto border-b border-rule pb-2" aria-label="Status filters">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-ink-faint mr-2">
            {t.filterPrefix}
          </span>
          {filterTabs.map((tab) => {
            const isActive = currentStatus === tab.value;
            const queryParams = new URLSearchParams();
            if (lang !== "en") queryParams.set("lang", lang);
            if (tab.value) queryParams.set("status", tab.value);
            const href = `/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;

            return (
              <Link
                key={tab.value}
                href={href}
                className={`rounded-[3px] px-2.5 py-1 font-mono text-[11.5px] transition-colors ${
                  isActive
                    ? "bg-ink font-semibold text-paper"
                    : "border border-rule bg-paper text-ink-soft hover:border-ink hover:text-ink"
                }`}
              >
                {tab.label}
              </Link>
            );
          })}
        </div>
      </section>

      {/* Lead Story */}
      {leadEvent && !currentStatus && (
        <section className="mb-12">
          <LeadStory event={leadEvent} reasoning={leadReasoning} />
        </section>
      )}

      {/* Structured Topic Feed */}
      <section aria-label="Recent reporting">
        <TopicFeed items={currentStatus ? [{ event: leadEvent, reasoning: leadReasoning }, ...feedItems].filter(x => x.event) : feedItems} />
      </section>
    </main>
  );
}
