from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from duckos.cli import main
from duckos.shell import ShellError, host_status, read_app_catalog, readiness_report


class ShellHostTests(unittest.TestCase):
    def test_host_status_reports_real_host_and_explicit_native_boundaries(self):
        report = host_status(environ={"WAYLAND_DISPLAY": "wayland-0", "DISPLAY": ":0"})

        self.assertEqual(report["schema"], "duckos.shell-host-status.v1")
        self.assertEqual(report["runtime_state"], "ready")
        self.assertEqual(report["desktop"]["display_backend"], "wayland")
        self.assertFalse(report["desktop"]["native_compositor"])
        self.assertFalse(report["desktop"]["native_window_manager"])
        self.assertFalse(report["host_writes_performed"])
        self.assertFalse(report["network_access_performed"])
        self.assertIn("host.read", report["available_capabilities"])

    def test_display_backend_detection_has_ordered_fallbacks(self):
        self.assertEqual(host_status(environ={"DISPLAY": ":0"})["desktop"]["display_backend"], "x11")
        self.assertEqual(host_status(environ={})["desktop"]["display_backend"], "windows-desktop" if __import__("sys").platform == "win32" else "macos-window-server" if __import__("sys").platform == "darwin" else "not-detected")

    def test_app_catalogue_contains_the_first_party_suite(self):
        report = read_app_catalog()
        names = {app["id"]: app["name"] for app in report["apps"]}

        self.assertEqual(report["schema"], "duckos.shell-app-catalog.v1")
        self.assertGreaterEqual(report["count"], 14)
        self.assertEqual(names["illidia"], "Illidia")
        self.assertIn("workspace", names)
        self.assertEqual(len(report["system_services"]), 8)

    def test_invalid_or_duplicate_catalogue_entries_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "apps.json"
            path.write_text(json.dumps({
                "schema_version": "test",
                "built_in_apps": [
                    {"id": "same", "name": "One", "category": "system", "panel": "mora/a"},
                    {"id": "same", "name": "Two", "category": "system", "panel": "mora/b"},
                ],
                "system_services": [],
            }), encoding="utf-8")
            with self.assertRaises(ShellError):
                read_app_catalog(path)

    def test_readiness_report_does_not_claim_reaper_was_executed(self):
        report = readiness_report()
        checks = {item["id"]: item["available"] for item in report["checks"]}

        self.assertTrue(report["all_required_sources_present"])
        self.assertTrue(checks["mora/shell.js"])
        self.assertTrue(checks["duckos/ui/window_manager.rpr"])
        self.assertFalse(report["reaper_contracts_executed"])
        self.assertFalse(report["native_compositor_implemented"])
        self.assertFalse(report["host_processes_started"])

    def test_cli_exposes_shell_status_apps_and_verify(self):
        output = StringIO()
        with redirect_stdout(output):
            status = main(["shell", "status"])
        self.assertEqual(status, 0)
        host = json.loads(output.getvalue())
        self.assertEqual(host["schema"], "duckos.shell-host-status.v1")

        output = StringIO()
        with redirect_stdout(output):
            status = main(["shell", "apps"])
        self.assertEqual(status, 0)
        apps = json.loads(output.getvalue())
        self.assertGreaterEqual(apps["count"], 14)

        output = StringIO()
        with redirect_stdout(output):
            status = main(["shell", "verify"])
        self.assertEqual(status, 0)
        readiness = json.loads(output.getvalue())
        self.assertTrue(readiness["all_required_sources_present"])


if __name__ == "__main__":
    unittest.main()
