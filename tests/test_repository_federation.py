from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.federate_repositories import FederationError, parse_gitmodules, validate_manifest

ROOT = Path(__file__).resolve().parents[1]


class RepositoryFederationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "federation" / "repositories.v1.json").read_text(encoding="utf-8")
        )

    def test_checked_in_registry_is_valid_and_contains_all_four_sources(self):
        self.assertEqual(validate_manifest(self.manifest), [])
        self.assertEqual(
            {item["repository"] for item in self.manifest["repositories"]},
            {"Ivan-VHS/Pytyliki", "Ivan-VHS/Reaper", "Ivan-VHS/OPlague", "Ivan-VHS/VentuSample"},
        )

    def test_duplicate_repository_path_is_rejected(self):
        altered = copy.deepcopy(self.manifest)
        altered["repositories"][1]["path"] = "projects/pytyliki"
        self.assertTrue(any("path" in error or "duplicate" in error for error in validate_manifest(altered)))

    def test_unknown_repository_id_is_reported_without_crashing(self):
        altered = copy.deepcopy(self.manifest)
        altered["repositories"][0]["id"] = "unknown-project"
        errors = validate_manifest(altered)
        self.assertTrue(any("unexpected repository id" in error for error in errors))

    def test_wrong_commit_pin_is_rejected(self):
        altered = copy.deepcopy(self.manifest)
        altered["repositories"][0]["pinned_commit"] = "main"
        self.assertTrue(any("pinned_commit" in error for error in validate_manifest(altered)))

    def test_auto_build_and_execute_are_forbidden(self):
        altered = copy.deepcopy(self.manifest)
        altered["repositories"][2]["auto_execute"] = True
        self.assertTrue(any("automatic build and execution" in error for error in validate_manifest(altered)))

    def test_unknown_dependency_is_rejected(self):
        altered = copy.deepcopy(self.manifest)
        altered["repositories"][0]["depends_on"] = ["missing-project"]
        self.assertTrue(any("unknown dependency" in error for error in validate_manifest(altered)))

    def test_dependency_cycle_is_rejected(self):
        altered = copy.deepcopy(self.manifest)
        altered["repositories"][0]["depends_on"] = ["reaper"]
        altered["repositories"][1]["depends_on"] = ["pytyliki"]
        self.assertTrue(any("dependency cycle" in error for error in validate_manifest(altered)))

    def test_gitmodules_is_one_to_one_with_the_registry(self):
        config = parse_gitmodules((ROOT / ".gitmodules").read_text(encoding="utf-8"))
        expected = {item["path"]: item["url"] for item in self.manifest["repositories"]}
        self.assertEqual({key: item["url"] for key, item in config.items()}, expected)

    def test_gitmodules_rejects_unexpected_section(self):
        with self.assertRaises(FederationError):
            parse_gitmodules('[remote "origin"]\n\turl = https://example.invalid\n')

    def test_reaper_is_registered_as_a_native_user_space_workbench(self):
        reaper = next(x for x in self.manifest["repositories"] if x["id"] == "reaper")
        self.assertEqual(reaper["integration_status"], "native-workbench")
        self.assertIn("native Duck Desktop workbench", reaper["integration_mode"])
        self.assertFalse(reaper["auto_build"])
        self.assertFalse(reaper["auto_execute"])

    def test_all_specialist_projects_are_registered_for_native_launch(self):
        launchable = {"pytyliki", "oplague", "ventusample"}
        for project in self.manifest["repositories"]:
            if project["id"] in launchable:
                self.assertEqual(project["integration_status"], "native-app-launcher")
                self.assertFalse(project["auto_build"])
                self.assertFalse(project["auto_execute"])
                self.assertTrue(any("launcher" in item for item in project["integration_mode"]))

    def test_ventusample_declares_only_an_optional_reaper_dependency(self):
        ventu = next(x for x in self.manifest["repositories"] if x["id"] == "ventusample")
        self.assertEqual(ventu["optional_dependencies"], ["reaper"])
        self.assertEqual(ventu["depends_on"], [])


if __name__ == "__main__":
    unittest.main()
