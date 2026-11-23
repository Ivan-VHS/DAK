from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    with (ROOT / relative_path).open(encoding="utf-8") as stream:
        return json.load(stream)


class ExecutableCompatibilityCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_json("catalogs/compatibility-targets.v1.json")
        cls.schema = load_json("schemas/compatibility-targets.v1.schema.json")

    def test_catalog_matches_its_schema(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        Draft202012Validator(self.schema, format_checker=FormatChecker()).validate(self.catalog)

    def test_all_fifteen_reference_systems_are_registered_once(self) -> None:
        expected = {
            "macos", "freebsd", "reactos", "haiku", "openbsd", "netbsd",
            "dragonfly-bsd", "openindiana-illumos", "freedos", "kolibrios",
            "aros", "morphos", "qnx", "plan9-9front", "redox",
        }
        actual = {item["id"] for item in self.catalog["targets"]}
        self.assertEqual(actual, expected)
        self.assertEqual(len(self.catalog["targets"]), 15)

    def test_four_execution_models_are_complete(self) -> None:
        expected = {
            "native-execution", "api-translation",
            "binary-translation", "emulation-virtualization",
        }
        actual = {item["id"] for item in self.catalog["mechanisms"]}
        self.assertEqual(actual, expected)

    def test_duckos_does_not_claim_native_executable_support(self) -> None:
        runtime = self.catalog["duckos_runtime"]
        self.assertEqual(runtime["host_shell"], "browser")
        self.assertEqual(runtime["pe_execution"], "not_available")
        self.assertEqual(runtime["dos_execution"], "not_available")
        self.assertEqual(runtime["native_bridge"], "not_implemented")
        self.assertEqual(runtime["status"], "analysis_ui_only")

    def test_every_profile_explains_its_limits(self) -> None:
        for profile in self.catalog["targets"]:
            with self.subTest(profile=profile["id"]):
                self.assertTrue(profile["approach"].strip())
                self.assertTrue(profile["caveat"].strip())


if __name__ == "__main__":
    unittest.main()