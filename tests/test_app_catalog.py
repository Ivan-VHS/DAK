from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    with (ROOT / relative_path).open(encoding="utf-8") as stream:
        return json.load(stream)


class ApplicationCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_json("catalogs/preinstalled-applications.v1.json")
        cls.schema = load_json("schemas/preinstalled-applications.v1.schema.json")

    def test_catalog_matches_its_schema(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        Draft202012Validator(
            self.schema, format_checker=FormatChecker()
        ).validate(self.catalog)

    def test_all_seven_default_applications_are_present(self) -> None:
        expected = {
            "cockos", "kavun", "ka-bon", "gloverty", "po", "illidia", "unify"
        }
        actual = {item["id"] for item in self.catalog["applications"]}
        self.assertEqual(actual, expected)
        self.assertEqual(len(self.catalog["applications"]), 7)

    def test_native_and_browser_maturity_are_not_conflated(self) -> None:
        self.assertEqual(self.catalog["maturity_status"], "specified")
        self.assertEqual(self.catalog["prototype"]["maturity_status"], "partial")
        for app in self.catalog["applications"]:
            self.assertEqual(app["maturity_status"], "specified")
            self.assertEqual(app["prototype_status"], "partial")

    def test_every_workflow_has_valid_endpoints_and_user_consent(self) -> None:
        app_ids = {item["id"] for item in self.catalog["applications"]}
        self.assertEqual(len(self.catalog["workflows"]), 4)
        for workflow in self.catalog["workflows"]:
            self.assertIn(workflow["source"], app_ids)
            self.assertIn(workflow["target"], app_ids)
            self.assertTrue(workflow["user_consent_required"])

    def test_unify_transfer_schema_and_bounds_are_registered(self) -> None:
        transfer_schema = load_json("schemas/unify.transfer.v1.schema.json")
        Draft202012Validator.check_schema(transfer_schema)
        contract = next(
            item for item in self.catalog["interfaces"]
            if item["id"] == "unify.transfer.v1"
        )
        self.assertEqual(contract["schema"], "schemas/unify.transfer.v1.schema.json")
        self.assertEqual(contract["max_package_bytes"], 20 * 1024 * 1024)
        self.assertEqual(contract["max_clip_bytes"], 12 * 1024 * 1024)

    def test_prototype_and_documentation_targets_exist(self) -> None:
        expected_paths = [
            "prototype/mora-home.html",
            "docs/PREINSTALLED_APPLICATIONS.md",
            "docs/UNIFY_TRANSFER_FORMAT_V1.md",
            "schemas/unify.transfer.v1.schema.json",
        ]
        for relative in expected_paths:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_browser_prototype_mentions_all_application_names(self) -> None:
        html = (ROOT / "prototype/mora-home.html").read_text(encoding="utf-8")
        for name in ("Cockos", "Kavun", "Ka-bon", "Gloverty", "Po", "Illidia", "Unify"):
            with self.subTest(app=name):
                self.assertIn(name, html)
        self.assertIn("mora.local-suite.v1", html)
        self.assertIn("IndexedDB", html)


if __name__ == "__main__":
    unittest.main()
