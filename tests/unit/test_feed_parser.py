from workers.pipeline.adapters.feed_parser import parse_feed_datetime, parse_feed_xml, strip_html


def test_strip_html():
    raw = "<p>Arsenal have <strong>submitted</strong> a bid. <a href='https://example.com'>Read more</a></p>"
    clean = strip_html(raw)
    assert clean == "Arsenal have submitted a bid. Read more"
    assert "<" not in clean


def test_parse_feed_datetime_rfc2822():
    dt = parse_feed_datetime("Mon, 09 Sep 2024 14:30:00 +0000")
    assert dt.year == 2024
    assert dt.month == 9
    assert dt.day == 9
    assert dt.hour == 14
    assert dt.minute == 30


def test_parse_feed_datetime_iso8601():
    dt = parse_feed_datetime("2024-09-09T14:30:00Z")
    assert dt.year == 2024
    assert dt.month == 9
    assert dt.day == 9
    assert dt.hour == 14
    assert dt.minute == 30


def test_parse_rss2_feed():
    rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
      <channel>
        <title>Sports Wire</title>
        <link>https://example.com</link>
        <description>Sports news feed</description>
        <item>
          <title>Arsenal agree terms for Emeka Osei</title>
          <link>https://example.com/osei-deal-1</link>
          <description>&lt;p&gt;Sporting CP winger Emeka Osei has agreed terms with Arsenal.&lt;/p&gt;</description>
          <dc:creator>David Ornstein</dc:creator>
          <pubDate>Mon, 09 Sep 2024 12:00:00 GMT</pubDate>
        </item>
        <item>
          <title>Real Madrid monitor Davies contract situation</title>
          <link>https://example.com/davies-deal-2</link>
          <description>Bayern Munich left back Alphonso Davies remains on Real Madrid radar.</description>
          <author>editor@example.com (Staff Writer)</author>
          <pubDate>Mon, 09 Sep 2024 13:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """
    articles = parse_feed_xml(rss_xml, outlet_name="The Athletic", default_language="en")
    assert len(articles) == 2

    a1 = articles[0]
    assert a1["headline"] == "Arsenal agree terms for Emeka Osei"
    assert a1["source_url"] == "https://example.com/osei-deal-1"
    assert "Sporting CP winger Emeka Osei" in a1["body"]
    assert a1["author"] == "David Ornstein"
    assert a1["outlet"] == "The Athletic"
    assert a1["language"] == "en"

    a2 = articles[1]
    assert a2["headline"] == "Real Madrid monitor Davies contract situation"
    assert a2["source_url"] == "https://example.com/davies-deal-2"


def test_parse_atom_feed():
    atom_xml = """<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title>Calcio Mercato</title>
      <link href="https://example.it"/>
      <updated>2024-09-09T15:00:00Z</updated>
      <entry>
        <title>Juventus aprono trattative per Koopmeiners</title>
        <link href="https://example.it/koopmeiners-juve-1"/>
        <summary>I bianconeri hanno presentato una prima offerta formale all'Atalanta.</summary>
        <author>
          <name>Fabrizio Romano</name>
        </author>
        <published>2024-09-09T14:45:00Z</published>
      </entry>
    </feed>
    """
    articles = parse_feed_xml(atom_xml, outlet_name="Sky Sport Italia", default_language="it")
    assert len(articles) == 1

    a1 = articles[0]
    assert a1["headline"] == "Juventus aprono trattative per Koopmeiners"
    assert a1["source_url"] == "https://example.it/koopmeiners-juve-1"
    assert a1["author"] == "Fabrizio Romano"
    assert a1["language"] == "it"
    assert a1["outlet"] == "Sky Sport Italia"
