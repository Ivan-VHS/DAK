"""Tests for the program adoption manifest validator."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validate_program_adoption import validate_manifest


class ProgramAdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        manifest_path = ROOT / "manifests" / "ivan-vhs-program-adoption.v1.json"
        cls.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    def test_repository_manifest_is_valid(self) -> None:
        self.assertEqual(validate_manifest(self.manifest), [])

    def test_duplicate_catalogue_assignment_is_rejected(self) -> None:
        altered = copy.deepcopy(self.manifest)
        altered["projects"][2]["catalogue_ranges"] = [[501, 701]]
        errors = validate_manifest(altered)
        self.assertTrue(any("assigned to both" in error for error in errors))

    def test_missing_range_is_rejected(self) -> None:
        altered = copy.deepcopy(self.manifest)
        altered["projects"][0]["catalogue_ranges"] = [[1, 119], [171, 250]]
        errors = validate_manifest(altered)
        self.assertTrue(any("unassigned catalogue IDs: 120" in error for error in errors))

    def test_wrong_entry_count_is_rejected(self) -> None:
        altered = copy.deepcopy(self.manifest)
        altered["projects"][1]["entry_count"] = 249
        errors = validate_manifest(altered)
        self.assertTrue(any("entry_count should be 250" in error for error in errors))

    def test_duckos_cannot_claim_catalogue_ids(self) -> None:
        altered = copy.deepcopy(self.manifest)
        altered["projects"][4]["catalogue_ranges"] = [[1, 1]]
        altered["projects"][4]["entry_count"] = 1
        errors = validate_manifest(altered)
        self.assertTrue(any("integration host must not own catalogue IDs" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
