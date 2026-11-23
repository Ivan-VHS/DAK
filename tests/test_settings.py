from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from duckos.settings import (
    SCHEMA, SettingsStore, default_settings, validate_profile,
    validate_settings, network_probe, settings_search,
)


class SettingsValidationTests(unittest.TestCase):
    def test_defaults_are_valid(self):
        self.assertEqual(validate_settings(default_settings()), [])

    def test_static_ipv4_requires_matching_mask_and_gateway(self):
        profile = default_settings()["profiles"]["Дом"]
        profile["network"].update({
            "ipv4_method": "static",
            "ipv4_address": "192.168.10.20",
            "ipv4_prefix": 24,
            "ipv4_netmask": "255.255.255.0",
            "ipv4_gateway": "192.168.10.1",
            "dns_primary": "1.1.1.1",
            "dns_secondary": "2606:4700:4700::1111",
        })
        self.assertEqual(validate_profile(profile), [])

        profile["network"]["ipv4_gateway"] = "192.168.11.1"
        errors = validate_profile(profile)
        self.assertTrue(any(row["field"] == "network.ipv4_gateway" for row in errors))

    def test_rejects_invalid_dns_mtu_and_doh(self):
        profile = default_settings()["profiles"]["Дом"]
        profile["network"].update({
            "dns_primary": "999.1.1.1",
            "mtu": 12000,
            "doh_url": "http://resolver.example/dns-query",
        })
        fields = {row["field"] for row in validate_profile(profile)}
        self.assertIn("network.dns_primary", fields)
        self.assertIn("network.mtu", fields)
        self.assertIn("network.doh_url", fields)

    def test_ipv6_static_address_is_validated(self):
        profile = default_settings()["profiles"]["Дом"]
        profile["network"].update({
            "ipv6_method": "static",
            "ipv6_address": "2001:db8::20",
            "ipv6_prefix": 64,
            "ipv6_gateway": "2001:db8::1",
        })
        self.assertEqual(validate_profile(profile), [])
        profile["network"]["ipv6_address"] = "not-an-ip"
        self.assertTrue(any(row["field"] == "network.ipv6_address" for row in validate_profile(profile)))

    def test_rejects_unsafe_visual_values(self):
        profile = default_settings()["profiles"]["Дом"]
        profile["appearance"].update({"accent": "yellow", "ui_scale": 5})
        fields = {row["field"] for row in validate_profile(profile)}
        self.assertIn("appearance.accent", fields)
        self.assertIn("appearance.ui_scale", fields)

    def test_search_returns_breadcrumbs(self):
        rows = settings_search("dns")
        self.assertTrue(rows)
        self.assertTrue(all("Сеть" in row["path"] for row in rows))

    def test_malformed_import_values_return_validation_errors(self):
        payload = default_settings()
        payload["active_profile"] = []
        self.assertTrue(validate_settings(payload))

        payload = default_settings()
        payload["profiles"]["Дом"]["network"]["ipv4_method"] = []
        self.assertTrue(validate_settings(payload))

        payload = default_settings()
        payload["profiles"]["Дом"]["power"]["mode"] = {}
        self.assertTrue(validate_settings(payload))

        payload = default_settings()
        payload["profiles"]["Дом"]["appearance"]["theme"] = []
        self.assertTrue(validate_settings(payload))


class SettingsStoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.store = SettingsStore(self.root / "settings.json")

    def test_save_update_profile_and_history(self):
        created = self.store.save()
        self.assertTrue(created["created"])
        updated = self.store.update_profile("Дом", "appearance", {"accent": "#336699"})
        self.assertFalse(updated["system_changes_performed"])
        name, profile = self.store.active_profile()
        self.assertEqual(name, "Дом")
        self.assertEqual(profile["appearance"]["accent"], "#336699")
        self.assertTrue(self.store.snapshots())
        events = self.store.events()
        self.assertIn("profile.update", [event["action"] for event in events])
        self.assertFalse(events[-1]["system_changes_performed"])

    def test_profile_creation_and_switch(self):
        self.store.save()
        self.store.create_profile("Студия", clone_from="Работа")
        self.store.activate_profile("Студия")
        self.assertEqual(self.store.active_profile()[0], "Студия")
        self.assertIn("Студия", self.store.list_profiles())

    def test_invalid_update_does_not_change_saved_state(self):
        self.store.save()
        before = self.store.load()
        with self.assertRaises(ValueError):
            self.store.update_profile("Дом", "network", {"mtu": 16000})
        self.assertEqual(self.store.load(), before)

    def test_export_import_and_rollback(self):
        self.store.save()
        self.store.update_profile("Дом", "appearance", {"accent": "#224466"})
        snapshot = self.store.snapshots()[0]["id"]
        export_file = self.root / "export.json"
        self.store.export_to(export_file)
        self.store.update_profile("Дом", "appearance", {"accent": "#AA5500"})
        self.store.import_from(export_file)
        self.assertEqual(self.store.active_profile()[1]["appearance"]["accent"], "#224466")
        self.store.update_profile("Дом", "appearance", {"accent": "#AA5500"})
        self.store.rollback(snapshot)
        self.assertEqual(self.store.active_profile()[1]["appearance"]["accent"], "#FFD400")

    def test_import_rejects_wrong_schema(self):
        wrong = self.root / "wrong.json"
        wrong.write_text(json.dumps({"schema": "old"}), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.store.import_from(wrong)

    def test_symlink_settings_file_is_rejected(self):
        target = self.root / "target.json"
        target.write_text(json.dumps(default_settings()), encoding="utf-8")
        link = self.root / "linked.json"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks are not available in this environment")
        with self.assertRaises(ValueError):
            SettingsStore(link)

    def test_export_refuses_symlink_destination(self):
        target = self.root / "target.json"
        target.write_text("{}", encoding="utf-8")
        link = self.root / "export-link.json"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks are not available in this environment")
        with self.assertRaises(ValueError):
            self.store.export_to(link)


class NetworkProbeValidationTests(unittest.TestCase):
    def test_invalid_probe_inputs_are_rejected_before_network_access(self):
        with self.assertRaises(ValueError):
            network_probe("bad host")
        with self.assertRaises(ValueError):
            network_probe("example.com", port=70000)


if __name__ == "__main__":
    unittest.main()
