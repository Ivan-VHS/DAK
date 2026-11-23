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

    def test_all_twenty_first_party_applications_are_present(self) -> None:
        expected = {
            "cockos", "kavun", "ka-bon", "gloverty", "po", "illidia", "unify",
            "sestem", "setupup", "orriganize", "abriganza", "olaab", "concrete-thump",
            "seu-beu", "love-il", "poi", "poi-2", "po-2", "gamecharager", "exedotexe",
        }
        actual = {item["id"] for item in self.catalog["applications"]}
        self.assertEqual(actual, expected)
        self.assertEqual(len(self.catalog["applications"]), 20)

    def test_native_shell_and_application_maturity_are_not_conflated(self) -> None:
        self.assertEqual(self.catalog["maturity_status"], "specified")
        native_shell = self.catalog["native_shell"]
        self.assertEqual(native_shell["maturity_status"], "implemented")
        self.assertEqual(native_shell["runtime"], "python-tk")
        self.assertIn("not the DuckOS compositor", native_shell["scope"])
        for app in self.catalog["applications"]:
            self.assertEqual(app["maturity_status"], "specified")
            self.assertNotIn("prototype_status", app)
            self.assertNotIn("prototype_evidence", app)

    def test_every_workflow_has_valid_endpoints_and_user_consent(self) -> None:
        app_ids = {item["id"] for item in self.catalog["applications"]}
        self.assertEqual(len(self.catalog["workflows"]), 9)
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

    def test_native_shell_files_and_documentation_targets_exist(self) -> None:
        expected_paths = [
            "duckos/mora/native_ui.py",
            "duckos/mora/model.py",
            "duckos/mora/data/apps.json",
            "duckos/mora/data/commons-catalog.json",
            "docs/PREINSTALLED_APPLICATIONS.md",
            "docs/UNIFY_TRANSFER_FORMAT_V1.md",
            "schemas/unify.transfer.v1.schema.json",
            "catalogs/dak-base-applications.v1.yaml",
        ]
        for relative in expected_paths:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_native_launcher_registry_mentions_all_application_names(self) -> None:
        registry = load_json("mora/apps.json")
        expected = {"kabon" if item["id"] == "ka-bon" else item["id"] for item in self.catalog["applications"]}
        actual = {item["id"] for item in registry["built_in_apps"]}
        self.assertTrue(expected.issubset(actual))
        self.assertTrue(all(item.get("runtime") == "native-tk" for item in registry["built_in_apps"]))
        native_source = (ROOT / "duckos/mora/native_ui.py").read_text(encoding="utf-8")
        self.assertIn("tk.Tk()", native_source)
        for name in (
            "Cockos", "Kavun", "Ka-bon", "Gloverty", "Po", "Illidia", "Unify",
            "Sestem", "SetupUP", "Orriganize", "Abriganza", "Olaab",
            "Concrete Thump", "Seu-Beu", "Love-IL", "Poi", "Poi-2",
            "Po-2", "GameCharager", "EXEdotEXE",
        ):
            with self.subTest(app=name):
                self.assertIn(name, native_source + json.dumps(registry, ensure_ascii=False))

    def test_retired_html_entry_points_are_absent(self) -> None:
        self.assertFalse((ROOT / "mora/index.html").exists())
        self.assertFalse((ROOT / "prototype/mora-home.html").exists())
        self.assertTrue((ROOT / "duckos/mora/native_ui.py").is_file())

    def test_dak_catalog_is_present_and_remains_design_only(self) -> None:
        catalog = (ROOT / "catalogs/dak-base-applications.v1.yaml").read_text(encoding="utf-8")
        self.assertIn("status: design", catalog)
        self.assertIn("id: dak.settings", catalog)
        for app_id in (
            "sestem", "setupup", "orriganize", "abriganza", "olaab",
            "concrete-thump", "seu-beu", "love-il", "poi", "poi-2",
            "po-2", "gamecharager", "exedotexe",
        ):
            with self.subTest(app=app_id):
                self.assertIn("id: dak." + app_id, catalog)


if __name__ == "__main__":
    unittest.main()
