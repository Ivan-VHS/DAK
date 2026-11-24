from __future__ import annotations

import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from duckos.cli import main


class SecurityCliTests(unittest.TestCase):
    def invoke(self, arguments: list[str]) -> tuple[int, dict]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(arguments)
        return code, json.loads(output.getvalue())

    def test_status_reports_advisory_user_space_maturity(self):
        code, result = self.invoke(["security", "status"])
        self.assertEqual(code, 0)
        self.assertEqual(result["schema"], "duckos.security-status.v1")
        self.assertEqual(result["kernel_enforcement"], "not_implemented")

    def test_analyze_command_writes_a_valid_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            event_file = root / "events.json"
            report_file = root / "report.json"
            event_file.write_text(json.dumps({
                "schema": "duckos.security-events.v1",
                "events": [{
                    "event_id": "e1",
                    "timestamp_ms": 1_800_000_000_000,
                    "host_id": "host-a",
                    "source": "test",
                    "kind": "process.start",
                    "actor_id": "proc-a",
                    "attributes": {"image_name": "powershell.exe", "encoded_command": True},
                }],
            }), encoding="utf-8")
            code, result = self.invoke([
                "security", "analyze", str(event_file), "--output", str(report_file)
            ])
            self.assertEqual(code, 0)
            self.assertEqual(result["enforcement"], "advisory_only")
            stored = json.loads(report_file.read_text(encoding="utf-8"))
            self.assertEqual(stored["events_analyzed"], 1)

    def test_snapshot_cli_restores_a_managed_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "notes.txt"
            target.write_text("before", encoding="utf-8")
            _, created = self.invoke(["security", "snapshot", "create", str(root), "notes.txt"])
            target.write_text("after", encoding="utf-8")
            code, restored = self.invoke([
                "security", "snapshot", "restore", str(root), created["snapshot_id"]
            ])
            self.assertEqual(code, 0)
            self.assertTrue(restored["restored"])
            self.assertEqual(target.read_text(encoding="utf-8"), "before")

    def test_integrity_cli_verifies_expected_digest_without_repair(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "part.bin"
            target.write_bytes(b"known payload")
            manifest = root / "integrity.json"
            manifest.write_text(json.dumps({
                "schema": "duckos.integrity-manifest.v1",
                "files": [{
                    "path": "part.bin",
                    "sha256": hashlib.sha256(b"known payload").hexdigest(),
                }],
            }), encoding="utf-8")
            code, result = self.invoke(["security", "integrity", str(root), str(manifest)])
            self.assertEqual(code, 0)
            self.assertTrue(result["verified"])
            self.assertFalse(result["repair_performed"])


if __name__ == "__main__":
    unittest.main()
