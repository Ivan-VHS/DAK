from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from duckos.mora.model import (
    build_intent_plan,
    calculate_sha256,
    create_recovery_snapshot,
    default_preferences,
    filter_commons_apps,
    load_preferences,
    normalize_preferences,
    save_preferences,
    validate_recovery_snapshot,
)


class MoraPreferencesTests(unittest.TestCase):
    def test_preferences_are_normalized_to_the_single_duck_profile(self):
        value = normalize_preferences({
            "appearance": {"theme": "light", "density": "compact", "reducedMotion": True},
            "focusMode": True,
            "powerProfile": "performance",
            "permissions": {"camera": True, "unknown": True},
        })
        self.assertEqual(value["appearance"]["theme"], "duck")
        self.assertEqual(value["appearance"]["density"], "compact")
        self.assertTrue(value["appearance"]["reducedMotion"])
        self.assertTrue(value["focusMode"])
        self.assertEqual(value["powerProfile"], "performance")
        self.assertEqual(value["permissions"], {
            "microphone": False, "camera": True, "location": False,
            "files": False, "network": False, "clipboard": False,
        })

    def test_invalid_values_fall_back_to_safe_defaults(self):
        value = normalize_preferences({"focusMode": "yes", "powerProfile": "root"})
        self.assertFalse(value["focusMode"])
        self.assertEqual(value["powerProfile"], "balanced")
        self.assertEqual(value["permissions"], default_preferences()["permissions"])

    def test_preferences_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "preferences.json"
            value = default_preferences()
            value["focusMode"] = True
            self.assertTrue(save_preferences(value, path))
            self.assertTrue(load_preferences(path)["focusMode"])

    def test_symlinked_preferences_are_not_read_or_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = root / "preferences.json"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available")
            self.assertFalse(save_preferences(default_preferences(), link))
            self.assertEqual(target.read_text(encoding="utf-8"), "{}")


class MoraRecoveryTests(unittest.TestCase):
    def test_recovery_snapshot_contains_only_normalized_preferences(self):
        snapshot = create_recovery_snapshot({
            "focusMode": True,
            "powerProfile": "saver",
            "permissions": {"camera": True, "shell": True},
        }, "2026-11-23T12:00:00+00:00")
        restored = validate_recovery_snapshot(snapshot)
        self.assertIsNotNone(restored)
        assert restored is not None
        self.assertTrue(restored["preferences"]["focusMode"])
        self.assertTrue(restored["preferences"]["permissions"]["camera"])
        self.assertNotIn("shell", restored["preferences"]["permissions"])
        self.assertIsNone(validate_recovery_snapshot({"schema": "unknown"}))

    def test_malformed_timestamp_is_rejected(self):
        snapshot = create_recovery_snapshot(default_preferences())
        snapshot["createdAt"] = "not-a-date"
        self.assertIsNone(validate_recovery_snapshot(snapshot))


class MoraIntentTests(unittest.TestCase):
    def test_intent_plans_only_allowlisted_local_actions(self):
        plan = build_intent_plan("включи режим фокуса и экономию энергии")
        self.assertTrue(plan["ok"])
        self.assertEqual(
            [action["setting"] for action in plan["actions"]],
            ["focusMode", "powerProfile"],
        )
        self.assertFalse(build_intent_plan("запусти powershell")["ok"])
        self.assertFalse(build_intent_plan("x" * 321)["ok"])
        self.assertFalse(build_intent_plan("")["ok"])

    def test_known_application_can_be_opened_without_shell_execution(self):
        plan = build_intent_plan("открой безопасность")
        self.assertTrue(plan["ok"])
        self.assertEqual(plan["actions"], [{"type": "open-app", "appId": "security"}])
        self.assertFalse(any("command" in action for action in plan["actions"]))


class MoraCommonsTests(unittest.TestCase):
    def test_catalog_search_and_category_filter(self):
        apps = [
            {"id": "a", "name": "TorqueSpec", "category": "workshop",
             "subtitle": "Моменты затяжки", "description": "Справочник крепежа",
             "capabilities": ["Н·м"], "keywords": ["резьба"]},
            {"id": "b", "name": "RoundTimer Pro", "category": "training",
             "subtitle": "Интервалы", "description": "Таймер раундов",
             "capabilities": ["Паузы"], "keywords": ["бокс"]},
        ]
        self.assertEqual([app["id"] for app in filter_commons_apps(apps, "резьба")], ["a"])
        self.assertEqual([app["id"] for app in filter_commons_apps(apps, "", "training")], ["b"])
        self.assertEqual(len(filter_commons_apps(apps)), 2)



class MoraRegistryTests(unittest.TestCase):
    def test_packaged_registry_has_the_expected_native_inventory(self):
        root = Path(__file__).resolve().parents[1] / "duckos" / "mora" / "data"
        registry = json.loads((root / "apps.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["schema_version"], "1.3.0")
        self.assertGreaterEqual(len(registry["built_in_apps"]), 29)
        self.assertTrue(all(app.get("runtime") == "pyside6" for app in registry["built_in_apps"]))
        self.assertTrue(all("panel" not in app for app in registry["built_in_apps"]))

    def test_commons_catalog_is_valid_json(self):
        root = Path(__file__).resolve().parents[1] / "duckos" / "mora" / "data"
        catalogue = json.loads((root / "commons-catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalogue["apps"]), 15)
        self.assertEqual(len({app["id"] for app in catalogue["apps"]}), 15)



class MoraToolkitRegistryTests(unittest.TestCase):
    def test_all_66_toolkits_are_reviewed_and_numbered_once(self):
        root = Path(__file__).resolve().parents[1] / "duckos" / "mora" / "data"
        registry = json.loads((root / "gui-toolkits.json").read_text(encoding="utf-8"))
        self.assertEqual(len(registry["entries"]), 66)
        self.assertEqual(
            [item["number"] for item in registry["entries"]],
            list(range(1, 67)),
        )
        self.assertEqual(registry["primary_runtime"], "PySide6")
        self.assertFalse(registry["html_runtime"])
        self.assertFalse(registry["webview"])
        self.assertIn("forbidden", {item["kind"] for item in registry["entries"]})
        self.assertTrue(all(item["reason"] for item in registry["entries"]))

    def test_native_bridge_metadata_is_safe_and_platform_scoped(self):
        from duckos.mora.native_bridge import native_bridge_status

        status = native_bridge_status()
        self.assertTrue(status["ctypes"])
        self.assertFalse(status["arbitrary_library_loading"])
        self.assertFalse(status["shell_execution"])

    def test_plot_reader_rejects_symlinks_and_reads_numeric_columns(self):
        from duckos.mora.plotting import read_numeric_columns

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            csv_file = root / "samples.csv"
            csv_file.write_text("time,value,label\n0,1.5,a\n1,2.5,b\n", encoding="utf-8")
            names, columns = read_numeric_columns(csv_file)
            self.assertEqual(names, ["time", "value"])
            self.assertEqual(columns["value"], [1.5, 2.5])
            link = root / "link.csv"
            try:
                link.symlink_to(csv_file)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available")
            with self.assertRaises(ValueError):
                read_numeric_columns(link)


class MoraIntegrityTests(unittest.TestCase):
    def test_sha256_reads_but_never_executes_a_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.bin"
            path.write_bytes(b"duck")
            report = calculate_sha256(path)
            self.assertRegex(report["digest"], r"^[0-9a-f]{64}$")
            self.assertEqual(report["size_bytes"], 4)
            self.assertFalse(report["executed"])

    def test_native_replacement_has_no_html_entry_points(self):
        root = Path(__file__).resolve().parents[1]
        self.assertFalse((root / "mora" / "index.html").exists())
        self.assertFalse((root / "prototype" / "mora-home.html").exists())


if __name__ == "__main__":
    unittest.main()
