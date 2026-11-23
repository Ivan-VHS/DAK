from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import mora_host


class MoraHostTests(unittest.TestCase):
    def test_theme_accepts_only_supported_values(self) -> None:
        self.assertEqual(mora_host.normalize_theme("dark"), "dark")
        self.assertEqual(mora_host.normalize_theme(" LIGHT "), "light")
        for value in ("system", "blue", "", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    mora_host.normalize_theme(value)

    def test_workspace_can_resolve_a_sibling_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "DuckOS"
            sibling = Path(temporary) / "Reaper"
            root.mkdir()
            sibling.mkdir()
            (sibling / "mora-app.json").write_text(
                json.dumps({"id": "reaper"}), encoding="utf-8"
            )
            with patch.object(mora_host, "ROOT", root):
                resolved = mora_host.resolve_repository(
                    "reaper", {"repositories": {}}
                )
            self.assertEqual(resolved, sibling.resolve())

    def test_custom_relative_repository_path_is_resolved_from_duckos(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "DuckOS"
            custom = root / "tools" / "Reaper"
            custom.mkdir(parents=True)
            (custom / "mora-app.json").write_text(
                json.dumps({"id": "reaper"}), encoding="utf-8"
            )
            with patch.object(mora_host, "ROOT", root):
                resolved = mora_host.resolve_repository(
                    "reaper", {"repositories": {"reaper": "tools/Reaper"}}
                )
            self.assertEqual(resolved, custom.resolve())

    def test_launch_targets_are_fixed_and_manifest_paths_are_not_executed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            entry = repo / "reaper_desktop.py"
            entry.write_text("pass\n", encoding="utf-8")
            self.assertEqual(
                mora_host.launch_target("reaper", repo),
                [mora_host.sys.executable, str(entry)],
            )
            self.assertIsNone(mora_host.launch_target("unknown", repo))

    def test_missing_repository_uses_honest_fallback_metadata(self) -> None:
        spec = next(item for item in mora_host.APP_SPECS if item["id"] == "reaper")
        info = mora_host.app_manifest(None, spec)
        self.assertEqual(info["name"], "Reaper Studio")
        self.assertEqual(info["category"], "developer")


if __name__ == "__main__":
    unittest.main()
