from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class DakBaseApplicationCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = ROOT / "catalogs/dak-base-applications.v1.yaml"
        cls.catalog = yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_catalog_is_a_design_proposal_with_twenty_nine_apps(self) -> None:
        self.assertEqual(self.catalog["schema_version"], 1)
        self.assertEqual(self.catalog["suite"]["id"], "dak.base-suite")
        self.assertEqual(self.catalog["suite"]["status"], "design")
        self.assertEqual(len(self.catalog["applications"]), 29)

    def test_application_ids_are_unique_and_service_references_resolve(self) -> None:
        applications = self.catalog["applications"]
        app_ids = [item["id"] for item in applications]
        self.assertEqual(len(app_ids), len(set(app_ids)))

        service_ids = set(self.catalog["services"])
        for app in applications:
            with self.subTest(app=app["id"]):
                self.assertEqual(app["entry"], "app://" + app["id"] + "/main")
                self.assertTrue(set(app["services"]).issubset(service_ids))
                self.assertIsInstance(app["permissions"], list)

    def test_all_requested_extensions_are_registered(self) -> None:
        app_ids = {app["id"] for app in self.catalog["applications"]}
        expected = {
            "dak.sestem", "dak.setupup", "dak.orriganize", "dak.abriganza",
            "dak.olaab", "dak.concrete-thump", "dak.seu-beu", "dak.love-il",
            "dak.poi", "dak.poi-2", "dak.po-2", "dak.gamecharager", "dak.exedotexe",
            "dak.beelzebub-av",
        }
        self.assertTrue(expected.issubset(app_ids))


if __name__ == "__main__":
    unittest.main()
