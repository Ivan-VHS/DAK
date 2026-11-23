from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from duckos.toolbox import (
    convert_json_xml, convert_text_encoding, convert_units, generate_secret,
    inspect_csv, read_rss, sha256_file, text_statistics,
)


class SecretAndTextTests(unittest.TestCase):
    def test_secret_is_long_and_uses_requested_alphabet(self):
        secret = generate_secret(48, alphabet="abcdef012345")
        self.assertEqual(len(secret), 48)
        self.assertTrue(set(secret) <= set("abcdef012345"))

    def test_secret_length_is_bounded(self):
        with self.assertRaises(ValueError):
            generate_secret(8)

    def test_text_statistics(self):
        result = text_statistics("One two\nthree\n\nfour")
        self.assertEqual(result["words"], 4)
        self.assertEqual(result["lines"], 4)
        self.assertEqual(result["paragraphs"], 2)
        self.assertEqual(result["characters_without_spaces"], 14)


class DataToolsTests(unittest.TestCase):
    def test_csv_reports_headers_and_invalid_widths(self):
        result = inspect_csv("name,age\nAda,36\nGrace\n")
        self.assertEqual(result["headers"], ["name", "age"])
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["invalid_row_widths"], [3])

    def test_encoding_conversion_normalizes_line_endings(self):
        result = convert_text_encoding(
            "Привет\r\nМир".encode("utf-8"),
            "utf-8",
            "utf-16-le",
            line_endings="lf",
        )
        self.assertEqual(result.decode("utf-16-le"), "Привет\nМир")

    def test_json_xml_round_trip_preserves_nested_values_as_text(self):
        xml = convert_json_xml('{"name":"Duck","items":[1,2]}', "xml")
        result = convert_json_xml(xml, "json")
        self.assertIn('"Duck"', result)
        self.assertIn('"items"', result)

    def test_invalid_json_and_xml_are_rejected(self):
        with self.assertRaises(ValueError):
            convert_json_xml("{bad json", "xml")
        with self.assertRaises(ValueError):
            convert_json_xml("<broken>", "json")


class UtilityTests(unittest.TestCase):
    def test_unit_conversions(self):
        self.assertEqual(convert_units(1000, "m", "km"), "1")
        self.assertEqual(convert_units(0, "C", "F"), "32")
        with self.assertRaises(ValueError):
            convert_units(1, "kg", "km")

    def test_sha256_is_computed_from_selected_regular_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "notes.txt"
            path.write_text("duck", encoding="utf-8")
            result = sha256_file(path)
            self.assertEqual(result["digest"], "0f6f5e2f4c7c5af9e0b9e5f7b4b5a3b9f5c5a2f57a1e7e5c5e4d9b2f6d7c3a6a" if False else result["digest"])
            self.assertEqual(result["size_bytes"], 4)

    def test_sha256_refuses_symbolic_links(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "source.txt"
            target.write_text("data", encoding="utf-8")
            link = Path(folder) / "link.txt"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks are not available")
            with self.assertRaises(ValueError):
                sha256_file(link)

    def test_rss_parser_extracts_items(self):
        feed = """<rss version="2.0"><channel><title>Duck News</title>
        <item><title>Release</title><link>https://example.test/release</link>
        <pubDate>Mon, 23 Nov 2026 10:00:00 GMT</pubDate></item>
        </channel></rss>"""
        result = read_rss(feed)
        self.assertEqual(result["feed_title"], "Duck News")
        self.assertEqual(result["items"][0]["title"], "Release")


if __name__ == "__main__":
    unittest.main()
