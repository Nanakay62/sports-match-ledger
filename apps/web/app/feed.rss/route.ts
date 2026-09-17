import { fetchEvents } from "@/lib/api";

export const dynamic = "force-dynamic";

function escapeXml(unsafe: string): string {
  return unsafe.replace(/[<>&'"]/g, (c) => {
    switch (c) {
      case "<":
        return "&lt;";
      case ">":
        return "&gt;";
      case "&":
        return "&amp;";
      case "'":
        return "&apos;";
      case '"':
        return "&quot;";
      default:
        return c;
    }
  });
}

export async function GET() {
  const events = await fetchEvents();
  const siteUrl = process.env.NEXT_PUBLIC_APP_URL || "https://sportsnewsai.example";
  const nowRfc = new Date().toUTCString();

  const itemsXml = events
    .map((event) => {
      const title = escapeXml(event.headline);
      const link = `${siteUrl}/event/${event.id}`;
      const guid = escapeXml(event.id);
      const pubDate = new Date(event.updatedAt).toUTCString();
      const statusLabel = event.status.replace("_", " ").toUpperCase();

      let desc = `${event.summary}\n\nStatus: ${statusLabel} | Evidence Sources: ${event.independentSources}`;
      if (event.firstReportedBy) {
        desc += ` | First reported by: ${event.firstReportedBy.outlet} (${event.firstReportedBy.leadTimeMinutes}m lead)`;
      }
      const descXml = escapeXml(desc);
      const category = escapeXml(`${event.sport} / ${event.competition}`);

      return `    <item>
      <title>${title}</title>
      <link>${link}</link>
      <guid isPermaLink="false">${guid}</guid>
      <pubDate>${pubDate}</pubDate>
      <description>${descXml}</description>
      <category>${category}</category>
    </item>`;
    })
    .join("\n");

  const rssXml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Sports News AI · Accountability Ledger</title>
    <link>${siteUrl}</link>
    <description>Evidence-grounded sports news with the Accountability Ledger and source receipts.</description>
    <language>en</language>
    <lastBuildDate>${nowRfc}</lastBuildDate>
    <generator>Sports News AI Ledger Feed Generator</generator>
    <atom:link href="${siteUrl}/feed.rss" rel="self" type="application/rss+xml" />
${itemsXml}
  </channel>
</rss>`;

  return new Response(rssXml, {
    status: 200,
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
      "Cache-Control": "public, max-age=60, s-maxage=300",
    },
  });
}
