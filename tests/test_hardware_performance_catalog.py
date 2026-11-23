from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


class HardwarePerformanceCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(
            (ROOT / "schemas" / "hardware-performance-suite.v1.schema.json").read_text(encoding="utf-8")
        )
        cls.catalog = json.loads(
            (ROOT / "catalogs" / "hardware-performance-suite.v1.json").read_text(encoding="utf-8")
        )

    def test_schema_is_valid_and_catalog_conforms(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        errors = sorted(
            Draft202012Validator(self.schema).iter_errors(self.catalog),
            key=lambda error: list(error.absolute_path),
        )
        self.assertEqual(
            errors,
            [],
            "\n".join(
                f"{list(error.absolute_path)}: {error.message}"
                for error in errors
            ),
        )

    def test_catalog_has_fifteen_unique_applications_and_real_entrypoints(self) -> None:
        applications = self.catalog["applications"]
        self.assertEqual(len(applications), 15)
        self.assertEqual(len({app["id"] for app in applications}), 15)

        for app in applications:
            relative_path = app["entrypoint"].split("#", 1)[0]
            self.assertTrue((ROOT / relative_path).is_file(), app["id"])

    def test_no_application_claims_verified_maturity_without_evidence(self) -> None:
        self.assertEqual(self.catalog["maturity_status"], "partial")
        self.assertTrue(all(app["maturity_status"] == "specified" for app in self.catalog["applications"]))
        self.assertTrue(all(app["prototype_status"] == "partial" for app in self.catalog["applications"]))

    def test_system_changing_operations_are_clearly_bounded(self) -> None:
        modes = {app["id"]: app["operation_mode"] for app in self.catalog["applications"]}
        self.assertEqual(modes["device-atlas"], "read-only")
        self.assertEqual(modes["firmware-atlas"], "read-only")
        self.assertEqual(modes["uefi-guard"], "read-only")
        self.assertEqual(modes["driver-capture"], "export-only")
        self.assertEqual(modes["driver-restore"], "explicit-apply")
        self.assertEqual(modes["gameframe"], "profile-only")


if __name__ == "__main__":
    unittest.main()
