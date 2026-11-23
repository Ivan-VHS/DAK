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

    def test_catalog_is_a_design_proposal_with_twenty_eight_apps(self) -> None:
        self.assertEqual(self.catalog["schema_version"], 1)
        self.assertEqual(self.catalog["suite"]["id"], "dak.base-suite")
        self.assertEqual(self.catalog["suite"]["status"], "design")
        self.assertEqual(len(self.catalog["applications"]), 28)

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

    def test_rights_and_controller_contracts_are_registered(self) -> None:
        services = set(self.catalog["services"])
        expected_services = {
            "dak.rights.v1", "dak.publisher-trust.v1", "dak.content-integrity.v1",
            "dak.content-provenance.v1", "dak.rights-audit.v1", "dak.capture-policy.v1",
            "dak.rights-transfer.v1", "dak.user-content.v1", "dak.controller-input.v1",
            "dak.console-navigation.v1",
        }
        self.assertTrue(expected_services.issubset(services))

        apps = {item["id"]: item for item in self.catalog["applications"]}
        game = apps["dak.gamecharager"]
        self.assertTrue({"games.licenses.read", "games.saves.read", "games.saves.write",
                         "content.integrity.verify", "capture.policy.read",
                         "controller.input.read"}.issubset(set(game["permissions"])))
        self.assertTrue({"dak.rights.v1", "dak.publisher-trust.v1", "dak.rights-audit.v1",
                         "dak.capture-policy.v1", "dak.controller-input.v1",
                         "dak.console-navigation.v1"}.issubset(set(game["services"])))
        sharing = apps["dak.seu-beu"]
        self.assertIn("rights.transfer.review", sharing["permissions"])
        self.assertIn("dak.rights-transfer.v1", sharing["services"])

    def test_all_requested_extensions_are_registered(self) -> None:
        app_ids = {app["id"] for app in self.catalog["applications"]}
        expected = {
            "dak.sestem", "dak.setupup", "dak.orriganize", "dak.abriganza",
            "dak.olaab", "dak.concrete-thump", "dak.seu-beu", "dak.love-il",
            "dak.poi", "dak.poi-2", "dak.po-2", "dak.gamecharager", "dak.exedotexe",
        }
        self.assertTrue(expected.issubset(app_ids))


if __name__ == "__main__":
    unittest.main()
