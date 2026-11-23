from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from duckos_services.common import ServiceError
from duckos_services.news import (
    NewsService,
    NewsSource,
    _is_local_origin,
    classify_category,
    parse_feed,
)


SOURCE = NewsSource(
    "test-feed",
    "Test News",
    "https://news.example.test/rss.xml",
    "en",
    ("example.test",),
)

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Test</title>
  <item>
    <title>Ukraine scientists test a new energy system</title>
    <link>https://news.example.test/story/one</link>
    <description><![CDATA[<p>Researchers <b>published</b> a result.</p><script>alert(1)</script>]]></description>
    <pubDate>Mon, 23 Nov 2026 12:30:00 GMT</pubDate>
    <guid>item-one</guid>
    <author>Reporter One</author>
  </item>
  <item>
    <title>Unsafe link is ignored</title>
    <link>javascript:alert(1)</link>
    <description>It must never become a clickable story.</description>
  </item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Atom</title>
  <entry>
    <title>Football final ends in a draw</title>
    <link rel="alternate" href="https://news.example.test/sport/final"/>
    <summary>Both teams scored twice.</summary>
    <updated>2026-11-23T13:00:00Z</updated>
    <id>urn:test:sport</id>
    <author><name>Sports Desk</name></author>
  </entry>
</feed>"""


class NewsParserTests(unittest.TestCase):
    def test_rss_parser_extracts_safe_plain_text_and_source_metadata(self) -> None:
        articles = parse_feed(SOURCE, RSS)
        self.assertEqual(len(articles), 1)
        story = articles[0]
        self.assertEqual(story["title"], "Ukraine scientists test a new energy system")
        self.assertEqual(story["category"], "Наука")
        self.assertEqual(story["source"], "Test News")
        self.assertEqual(story["author"], "Reporter One")
        self.assertIn("published a result", story["summary"])
        self.assertNotIn("script", story["summary"])
        self.assertEqual(story["url"], "https://news.example.test/story/one")

    def test_atom_parser_reads_link_date_and_author(self) -> None:
        articles = parse_feed(SOURCE, ATOM)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["category"], "Спорт")
        self.assertEqual(articles[0]["author"], "Sports Desk")
        self.assertEqual(articles[0]["published_at"], "2026-11-23T13:00:00Z")

    def test_rejects_xml_entity_declarations(self) -> None:
        with self.assertRaises(ServiceError):
            parse_feed(SOURCE, b"<!DOCTYPE rss [<!ENTITY x SYSTEM 'file:///etc/passwd'>]><rss/>")

    def test_oversized_feed_is_rejected(self) -> None:
        with self.assertRaises(ServiceError):
            parse_feed(SOURCE, b"x" * (2 * 1024 * 1024 + 1))

    def test_category_classifier_handles_common_languages(self) -> None:
        self.assertEqual(classify_category("Уряд оголосив нову програму"), "Политика")
        self.assertEqual(classify_category("Українські міста готуються до зими"), "Украина")
        self.assertEqual(classify_category("A new AI technology was released"), "Технологии")


class NewsServiceTests(unittest.TestCase):
    def test_refresh_persists_and_filters_items(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = NewsService(
                Path(temporary),
                sources=(SOURCE,),
                fetcher=lambda _source: RSS,
            )
            result = service.refresh()
            snapshot = service.snapshot(category="Наука")

            self.assertEqual(result["status"], "updated")
            self.assertEqual(snapshot["total"], 1)
            self.assertEqual(snapshot["items"][0]["source_id"], "test-feed")
            self.assertTrue((Path(temporary) / "news-cache.json").exists())

            restored = NewsService(Path(temporary), sources=(SOURCE,), fetcher=lambda _source: RSS)
            self.assertEqual(restored.status()["article_count"], 1)
            self.assertEqual(restored.snapshot()["items"][0]["title"], snapshot["items"][0]["title"])

    def test_failed_source_does_not_erase_last_good_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            calls = 0

            def fetch(_source: NewsSource) -> bytes:
                nonlocal calls
                calls += 1
                if calls == 1:
                    return RSS
                raise OSError("source temporarily unavailable")

            service = NewsService(Path(temporary), sources=(SOURCE,), fetcher=fetch)
            service.refresh()
            failed = service.refresh()

            self.assertEqual(failed["status"], "no-new-data")
            self.assertEqual(service.status()["article_count"], 1)
            self.assertEqual(service.snapshot()["items"][0]["title"], "Ukraine scientists test a new energy system")

    def test_query_and_category_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = NewsService(Path(temporary), sources=(SOURCE,), fetcher=lambda _source: RSS)
            service.refresh()
            self.assertEqual(service.snapshot(query="reporter one")["total"], 1)
            with self.assertRaises(ServiceError):
                service.snapshot(category="Unknown")
            with self.assertRaises(ServiceError):
                service.snapshot(limit=999)

    def test_malformed_cache_fields_are_ignored_safely(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cache = Path(temporary) / "news-cache.json"
            cache.write_text('{"items": null, "sources": null, "updated_at": 12}', encoding="utf-8")
            service = NewsService(Path(temporary), sources=(SOURCE,), fetcher=lambda _source: RSS)
            self.assertEqual(service.status()["article_count"], 0)
            self.assertIsNone(service.status()["updated_at"])

    def test_loopback_origin_policy_rejects_public_origins(self) -> None:
        self.assertTrue(_is_local_origin("http://127.0.0.1:4173"))
        self.assertTrue(_is_local_origin("http://localhost:8000"))
        self.assertFalse(_is_local_origin("https://example.com"))
        self.assertFalse(_is_local_origin("http://attacker.example"))
        self.assertFalse(_is_local_origin("null"))


if __name__ == "__main__":
    unittest.main()
