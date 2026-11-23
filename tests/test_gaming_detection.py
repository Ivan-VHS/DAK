from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from duckos.gaming.detection import (
    GamingDetectionError,
    detect_game_processes,
    load_game_profiles,
)


class GamingDetectionTests(unittest.TestCase):
    def catalog(self):
        return {
            "schema": "duckos.game-profile-catalog.v1",
            "profiles": [
                {
                    "id": "sample-game",
                    "name": "Sample Game",
                    "engine": "directx12",
                    "executables": ["SampleGame.exe", "sample-render.exe"],
                }
            ],
        }

    def test_matches_exact_executable_names_case_insensitively(self):
        report = detect_game_processes(
            self.catalog(),
            processes=[
                {"pid": 100, "executable_name": "samplegame.EXE"},
                {"pid": 200, "executable_name": "browser.exe"},
            ],
        )
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["candidates"][0]["game_id"], "sample-game")
        self.assertEqual(report["candidates"][0]["pid"], 100)
        self.assertFalse(report["automatic_activation_allowed"])
        self.assertFalse(report["command_line_arguments_collected"])

    def test_does_not_guess_between_overlapping_profiles(self):
        catalog = self.catalog()
        catalog["profiles"].append({
            "id": "second-profile", "name": "Second", "engine": "unknown",
            "executables": ["SampleGame.exe"],
        })
        report = detect_game_processes(
            catalog, processes=[{"pid": 42, "executable_name": "SampleGame.exe"}]
        )
        self.assertEqual(report["candidate_count"], 2)
        self.assertTrue(all(item["ambiguous_profile_match"] for item in report["candidates"]))

    def test_rejects_paths_duplicate_ids_and_invalid_process_rows(self):
        catalog = self.catalog()
        catalog["profiles"][0]["executables"] = ["../sample.exe"]
        with self.assertRaises(GamingDetectionError):
            detect_game_processes(catalog, processes=[])
        catalog = self.catalog()
        catalog["profiles"].append(dict(catalog["profiles"][0]))
        with self.assertRaises(GamingDetectionError):
            detect_game_processes(catalog, processes=[])
        with self.assertRaises(GamingDetectionError):
            detect_game_processes(self.catalog(), processes=[{"pid": True, "executable_name": "samplegame.exe"}])

    def test_loads_only_regular_bounded_profile_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "profiles.json"
            path.write_text(json.dumps(self.catalog()), encoding="utf-8")
            loaded = load_game_profiles(path)
            self.assertEqual(loaded["schema"], "duckos.game-profile-catalog.v1")
            with self.assertRaises(GamingDetectionError):
                load_game_profiles(Path(folder) / "missing.json")

    def test_empty_process_snapshot_is_valid_and_unknown_is_not_invented(self):
        report = detect_game_processes(self.catalog(), processes=[])
        self.assertEqual(report["candidate_count"], 0)
        self.assertEqual(report["processes_examined"], 0)
        self.assertTrue(report["requires_session_confirmation"])


if __name__ == "__main__":
    unittest.main()
