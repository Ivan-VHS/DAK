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

    def test_canonical_mora_and_embedded_web_routes(self) -> None:
        self.assertEqual(
            mora_host.resolve_desktop_page("/mora/"),
            mora_host.ROOT / "mora" / "index.html",
        )
        self.assertEqual(
            mora_host.resolve_desktop_page("/projects"),
            mora_host.ROOT / "index.html",
        )
        self.assertEqual(
            mora_host.resolve_desktop_page("/prototype/mora-home.html"),
            mora_host.ROOT / "prototype" / "mora-home.html",
        )
        self.assertEqual(
            mora_host.resolve_desktop_page("/mora/mora.js"),
            mora_host.ROOT / "mora" / "mora.js",
        )
        self.assertIsNone(mora_host.resolve_desktop_page("/"))
        self.assertIsNone(mora_host.resolve_desktop_page("/unknown"))

    def test_static_assets_have_explicit_content_types(self) -> None:
        self.assertEqual(
            mora_host.resolve_static_asset("/mora/mora.css")[1],
            "text/css; charset=utf-8",
        )
        self.assertEqual(
            mora_host.resolve_static_asset("/mora/mora.js")[1],
            "application/javascript; charset=utf-8",
        )
        self.assertIsNone(mora_host.resolve_static_asset("/mora/../../mora_host.py"))

    def test_four_native_tools_are_part_of_the_same_mora_catalog(self) -> None:
        expected = {"reaper", "oplague", "ventusample", "pytyliki"}
        actual = {app["id"] for app in mora_host.APP_SPECS}
        self.assertEqual(actual, expected)
        for app in mora_host.APP_SPECS:
            with self.subTest(app=app["id"]):
                self.assertTrue(app["repo"])
                self.assertTrue(app["fallback"]["name"])
                self.assertTrue(app["fallback"]["capabilities"])

    def test_mora_catalog_contains_all_web_and_native_applications(self) -> None:
        shell = (mora_host.ROOT / "mora" / "mora.js").read_text(encoding="utf-8")
        web_page = (mora_host.ROOT / "prototype" / "mora-home.html").read_text(
            encoding="utf-8"
        )
        for app_id in ("cockos", "kavun", "kabon", "gloverty", "po", "illidia", "unify"):
            with self.subTest(web_app=app_id):
                self.assertIn('id: "' + app_id + '"', shell)
                self.assertIn("render" + app_id.title(), web_page)
        for app_id in ("reaper", "oplague", "ventusample", "pytyliki"):
            with self.subTest(native_app=app_id):
                self.assertIn('nativeId: "' + app_id + '"', shell)
        self.assertIn("launchNative", shell)
        self.assertIn("app-embed", web_page)

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

    def test_sibling_checkout_does_not_need_a_merged_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "DuckOS"
            sibling = Path(temporary) / "OPlague"
            root.mkdir()
            sibling.mkdir()
            with patch.object(mora_host, "ROOT", root):
                resolved = mora_host.resolve_repository(
                    "oplague", {"repositories": {}}
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

    def test_unknown_application_cannot_be_launched(self) -> None:
        with self.assertRaises(KeyError):
            mora_host.launch_app("not-an-app")

    def test_manifest_fallback_is_grounded_in_registered_app_spec(self) -> None:
        spec = next(item for item in mora_host.APP_SPECS if item["id"] == "reaper")
        info = mora_host.app_manifest(None, spec)
        self.assertEqual(info["name"], "Reaper Studio")
        self.assertEqual(info["category"], "developer")

    def test_origin_check_rejects_other_local_sites(self) -> None:
        handler = object.__new__(mora_host.MoraHandler)
        handler.headers = {
            "Host": "127.0.0.1:43860",
            "Origin": "http://127.0.0.1:43860",
        }
        self.assertTrue(handler._origin_allowed())
        handler.headers["Origin"] = "http://localhost:43860"
        self.assertFalse(handler._origin_allowed())
        handler.headers["Origin"] = "https://127.0.0.1:43860"
        self.assertFalse(handler._origin_allowed())


if __name__ == "__main__":
    unittest.main()
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

    def test_unknown_application_cannot_be_launched(self) -> None:
        with self.assertRaises(KeyError):
            mora_host.launch_app("not-an-app")

    def test_manifest_fallback_is_grounded_in_registered_app_spec(self) -> None:
        spec = next(item for item in mora_host.APP_SPECS if item["id"] == "reaper")
        info = mora_host.app_manifest(None, spec)
        self.assertEqual(info["name"], "Reaper Studio")
        self.assertEqual(info["category"], "developer")

    def test_origin_check_rejects_other_local_sites(self) -> None:
        handler = object.__new__(mora_host.MoraHandler)
        handler.headers = {
            "Host": "127.0.0.1:43860",
            "Origin": "http://127.0.0.1:43860",
        }
        self.assertTrue(handler._origin_allowed())
        handler.headers["Origin"] = "http://localhost:43860"
        self.assertFalse(handler._origin_allowed())
        handler.headers["Origin"] = "https://127.0.0.1:43860"
        self.assertFalse(handler._origin_allowed())


if __name__ == "__main__":
    unittest.main()
