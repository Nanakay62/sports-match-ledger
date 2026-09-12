import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Activity, Shield, Trophy, User } from "lucide-react";
import { TopicFeed, type FeedItem } from "@/components/topic-feed";
import { buildStatusReasoning } from "@/lib/evidence";
import { getClaims, getTopic } from "@/lib/mock-data";
import { localizeClaim, localizeEvent } from "@/lib/data-loader";
import { getDictionary } from "@/lib/i18n";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const topic = getTopic(slug);
  return {
    title: topic ? `${topic.name}: topic ledger` : "Topic not found",
  };
}

export default async function TopicPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams?: Promise<{ lang?: string }>;
}) {
  const { slug } = await params;
  const sParams = searchParams ? await searchParams : undefined;
  const lang = sParams?.lang || "en";
  const t = getDictionary(lang);
  const querySuffix = lang !== "en" ? `?lang=${lang}` : "";

  const topic = getTopic(slug);
  if (!topic) notFound();

  const Icon =
    topic.type === "club"
      ? Shield
      : topic.type === "competition"
      ? Trophy
      : topic.type === "sport"
      ? Activity
      : User;

  const items: FeedItem[] = topic.events.map((event) => {
    const locEvent = localizeEvent(event, lang);
    const locClaims = getClaims(event.id).map((c) => localizeClaim(c, lang));
    return {
      event: locEvent,
      reasoning: buildStatusReasoning(locEvent, locClaims),
    };
  });

  return (
    <main className="mx-auto max-w-4xl px-4 pb-20 md:px-6">
      <nav
        className="pt-6 font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink-faint"
        aria-label="Breadcrumb"
      >
        <Link href={`/${querySuffix}`} className="hover:text-ink">
          {t.navLedger}
        </Link>
        <span className="mx-1.5">/</span>
        <span>Topics</span>
        <span className="mx-1.5">/</span>
        <span>{topic.name}</span>
      </nav>

      <header className="mt-6 border-b-2 border-ink pb-6">
        <div className="flex items-center gap-2 font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink-faint">
          <Icon className="size-3.5" aria-hidden />
          <span>{topic.type} dossier</span>
        </div>
        <h1 className="mt-2 font-display text-4xl font-medium tracking-tight md:text-5xl">
          {topic.name}
        </h1>
        <p className="mt-2 text-[14.5px] leading-relaxed text-ink-soft">
          All claims, transfers and corroborated stories on file involving {topic.name}.
        </p>
      </header>

      <div className="mt-8">
        <TopicFeed items={items} />
      </div>
    </main>
  );
}
