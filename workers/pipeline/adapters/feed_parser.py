import email.utils
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any


def strip_html(raw_html: str) -> str:
    """Removes HTML tags and unescapes entities deterministically."""
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_feed_datetime(raw_date: str | None) -> datetime:
    """Parses RFC 2822, RFC 822, or ISO 8601 dates to a UTC datetime."""
    if not raw_date:
        return datetime.now(timezone.utc)

    cleaned = raw_date.strip()

    # Try RFC 2822 / 822 (standard RSS pubDate)
    try:
        dt = email.utils.parsedate_to_datetime(cleaned)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # Try ISO 8601 (Atom updated / published)
    try:
        iso_str = cleaned.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    return datetime.now(timezone.utc)


def _local_tag(elem: ET.Element) -> str:
    return elem.tag.split("}")[-1].lower()


def parse_feed_xml(
    content: str | bytes,
    outlet_name: str,
    default_language: str = "en",
) -> list[dict[str, Any]]:
    """Deterministically parses RSS 2.0 or Atom XML feed content into raw article dictionaries."""
    if isinstance(content, str):
        raw_bytes = content.encode("utf-8")
    else:
        raw_bytes = content

    try:
        root = ET.fromstring(raw_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"Failed to parse XML feed: {exc}") from exc

    items: list[dict[str, Any]] = []

    # Detect feed type: RSS (<channel><item>...) or Atom (<feed><entry>...)
    root_tag = _local_tag(root)

    element_list: list[ET.Element] = []
    if root_tag == "rss" or root_tag == "rdf":
        channel = None
        for child in root:
            if _local_tag(child) == "channel":
                channel = child
                break
        container = channel if channel is not None else root
        for child in container:
            if _local_tag(child) == "item":
                element_list.append(child)
    elif root_tag == "feed":  # Atom
        for child in root:
            if _local_tag(child) == "entry":
                element_list.append(child)
    else:
        # Fallback: search recursively for item or entry
        for elem in root.iter():
            tag = _local_tag(elem)
            if tag in {"item", "entry"}:
                element_list.append(elem)

    for el in element_list:
        title = ""
        link = ""
        description = ""
        author = None
        pub_date_str = None

        for child in el:
            tag = _local_tag(child)
            text = (child.text or "").strip()

            if tag == "title":
                title = strip_html(text)
            elif tag == "link":
                if text:
                    link = text
                elif "href" in child.attrib:
                    link = child.attrib["href"]
            elif tag in {"description", "summary", "content", "encoded"}:
                if not description or tag in {"encoded", "content"}:
                    candidate = strip_html(text)
                    if candidate:
                        description = candidate
            elif tag in {"author", "creator"}:
                # Atom author may have child <name>
                if len(child) > 0:
                    for sub in child:
                        if _local_tag(sub) == "name" and sub.text:
                            author = sub.text.strip()
                            break
                elif text:
                    author = text
            elif tag in {"pubdate", "published", "updated", "date"}:
                if not pub_date_str or tag in {"pubdate", "published"}:
                    pub_date_str = text

        if not title or not link:
            continue

        published_at = parse_feed_datetime(pub_date_str)
        body = description if description else title

        items.append(
            {
                "outlet": outlet_name,
                "author": author,
                "source_url": link,
                "published_at": published_at,
                "headline": title,
                "body": body,
                "language": default_language,
            }
        )

    return items
