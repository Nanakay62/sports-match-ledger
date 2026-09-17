"""Sports News AI — Weekly Newsletter Digest Generator
Queries the Accountability Ledger for resolved claims, active rumours, and disputes
from the past 7 days, rendering Markdown and HTML digests.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.database.models import EventModel
from packages.database.session import SessionLocal


def generate_weekly_newsletter(output_dir: str = "_newsletters") -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    week_str = now.strftime("%Y-W%W")
    cutoff_date = now - timedelta(days=7)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    md_path = os.path.join(output_dir, f"newsletter_{week_str}.md")
    html_path = os.path.join(output_dir, f"newsletter_{week_str}.html")

    with SessionLocal() as db:
        events = db.query(EventModel).filter(EventModel.created_at >= cutoff_date).order_by(EventModel.created_at.desc()).all()
        if not events:
            # Fallback to all available events if no events in past 7 days (e.g. testing/dev)
            events = db.query(EventModel).order_by(EventModel.created_at.desc()).all()

    confirmed_events = [e for e in events if e.status == "Confirmed"]
    disputed_events = [e for e in events if e.status in {"Disputed", "Corrected"}]
    active_rumours = [e for e in events if e.status in {"Rumour", "Developing", "Well corroborated"}]

    # Build Markdown
    md_lines = [
        f"# Sports News AI — Weekly Accountability Digest ({week_str})",
        "",
        "> *The sports news app that keeps the receipts. Every claim tracked, attributed, and scored against authoritative outcomes.*",
        "",
        "---",
        "",
        f"## 1. Confirmed Outcomes & Official Signings ({len(confirmed_events)})",
        "",
    ]
    if not confirmed_events:
        md_lines.append("*No official signings confirmed in this reporting cycle.*")
    else:
        for ev in confirmed_events[:10]:
            first_rep = f" · First reported by **{ev.first_reported_outlet}**" if ev.first_reported_outlet else ""
            md_lines.append(f"- **{ev.headline}**{first_rep}")
            md_lines.append(f"  {ev.summary}")
            md_lines.append(f"  [View Verification Receipts →](https://sportsnewsai.com/event/{ev.id})")
            md_lines.append("")

    md_lines.extend(
        [
            "---",
            "",
            f"## 2. Busted Rumours & Official Denials ({len(disputed_events)})",
            "",
        ]
    )
    if not disputed_events:
        md_lines.append("*No disputed or debunked claims in this reporting cycle.*")
    else:
        for ev in disputed_events[:10]:
            md_lines.append(f"- **{ev.headline}** (Status: `{ev.status}`)")
            md_lines.append(f"  {ev.summary}")
            md_lines.append(f"  [Inspect Dispute Ledger →](https://sportsnewsai.com/event/{ev.id})")
            md_lines.append("")

    md_lines.extend(
        [
            "---",
            "",
            f"## 3. Active Rumours Under Corroboration ({len(active_rumours)})",
            "",
        ]
    )
    if not active_rumours:
        md_lines.append("*No active rumours currently tracked.*")
    else:
        for ev in active_rumours[:10]:
            first_rep = f" · First reported by **{ev.first_reported_outlet}**" if ev.first_reported_outlet else ""
            md_lines.append(f"- **{ev.headline}** (Status: `{ev.status}`){first_rep}")
            md_lines.append(f"  {ev.summary}")
            md_lines.append(f"  [Track Rumour Lifecycle →](https://sportsnewsai.com/event/{ev.id})")
            md_lines.append("")

    md_lines.extend(
        [
            "---",
            "",
            "### About Sports News AI",
            "We track sports rumours across 7 languages, keep an immutable append-only ledger of who reported what first, and compute public reliability scores for every major outlet and journalist.",
            "",
            "[View Full Public Ledger](https://sportsnewsai.com) · [Review Methodology](https://sportsnewsai.com/methodology) · [Unsubscribe](https://sportsnewsai.com/newsletter/unsubscribe)",
        ]
    )

    md_content = "\n".join(md_lines)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # Simple HTML conversion for email clients
    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Sports News AI — Weekly Digest {week_str}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1e293b; max-width: 640px; margin: 0 auto; padding: 24px 16px; }}
        h1 {{ font-size: 24px; color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }}
        h2 {{ font-size: 18px; color: #1e293b; margin-top: 24px; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; background: #e2e8f0; color: #334155; }}
        .event-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-bottom: 12px; }}
        a {{ color: #2563eb; text-decoration: none; font-weight: 500; }}
        footer {{ margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 16px; font-size: 12px; color: #64748b; }}
    </style>
</head>
<body>
    <h1>Sports News AI — Weekly Accountability Digest</h1>
    <p><em>The sports news app that keeps the receipts. Week {week_str}.</em></p>
    
    <h2>Confirmed Outcomes &amp; Signings ({len(confirmed_events)})</h2>
    {"".join(f'<div class="event-card"><strong>{e.headline}</strong><p>{e.summary}</p><a href="https://sportsnewsai.com/event/{e.id}">View Receipts &rarr;</a></div>' for e in confirmed_events[:10])}

    <h2>Busted Rumours &amp; Denials ({len(disputed_events)})</h2>
    {"".join(f'<div class="event-card"><strong>{e.headline}</strong> <span class="badge">{e.status}</span><p>{e.summary}</p><a href="https://sportsnewsai.com/event/{e.id}">Inspect Dispute &rarr;</a></div>' for e in disputed_events[:10])}

    <h2>Active Rumours Under Corroboration ({len(active_rumours)})</h2>
    {"".join(f'<div class="event-card"><strong>{e.headline}</strong> <span class="badge">{e.status}</span><p>{e.summary}</p><a href="https://sportsnewsai.com/event/{e.id}">Track Rumour &rarr;</a></div>' for e in active_rumours[:10])}

    <footer>
        <p>Sports News AI Accountability Ledger · <a href="https://sportsnewsai.com/methodology">Methodology v1.2.0</a></p>
    </footer>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_body)

    return md_path, html_path


if __name__ == "__main__":
    md, html = generate_weekly_newsletter()
    print(f"Generated Markdown newsletter at: {md}")
    print(f"Generated HTML newsletter at: {html}")
