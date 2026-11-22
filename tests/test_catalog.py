from __future__ import annotations

import unittest
from pathlib import Path

from tools.catalog import TARGET_COUNT, catalog_page, catalog_summary, implemented_functions


ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_registry_has_the_requested_size(self) -> None:
        summary = catalog_summary(ROOT)
        self.assertEqual(summary["target_count"], 87_965)
        self.assertEqual(summary["implemented_count"] + summary["reserved_count"], 87_965)

    def test_public_reaper_functions_are_discovered_from_source(self) -> None:
        functions = implemented_functions(ROOT)
        self.assertGreaterEqual(len(functions), 50)
        self.assertTrue(all(item["language"] == "Reaper" for item in functions))
        self.assertTrue(all(item["status"] == "implemented" for item in functions))
        self.assertTrue(all((ROOT / item["source"]).is_file() for item in functions))

    def test_reserved_entries_are_not_mislabeled(self) -> None:
        page = catalog_page(ROOT, TARGET_COUNT - 5, 10)
        self.assertEqual(page["returned"], 5)
        self.assertTrue(all(item["status"] == "reserved" for item in page["items"]))
        self.assertTrue(all(item["source"] is None for item in page["items"]))

    def test_pages_have_stable_ids_and_unique_names(self) -> None:
        first = catalog_page(ROOT, 0, 30)["items"]
        second = catalog_page(ROOT, 30, 30)["items"]
        combined = first + second
        self.assertEqual(len({item["id"] for item in combined}), 60)
        self.assertEqual(len({item["name"] for item in combined}), 60)
        self.assertEqual(first[0]["id"], "DUCK-00001")
        self.assertEqual(second[0]["id"], "DUCK-00031")


if __name__ == "__main__":
    unittest.main()
