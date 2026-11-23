from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from duckos.cli import main


class FoundryCliTests(unittest.TestCase):
    def invoke(self, *arguments: str) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(list(arguments))
        return status, output.getvalue()

    @patch("duckos.foundry.collect_foundry_snapshot")
    def test_audit_prints_a_machine_readable_report(self, collect):
        collect.return_value = {
            "schema": "duckos.foundry.snapshot.v1",
            "state": "nominal",
            "execution_policy": {"read_only": True},
        }
        status, output = self.invoke("foundry", "audit", "--skip-devices", "--skip-runtimes")
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output)["schema"], "duckos.foundry.snapshot.v1")
        collect.assert_called_once_with(include_devices=False, include_runtimes=False)

    @patch("duckos.foundry.build_runbook")
    @patch("duckos.foundry.collect_foundry_snapshot")
    def test_plan_returns_a_reviewable_runbook(self, collect, build):
        collect.return_value = {"schema": "duckos.foundry.snapshot.v1"}
        build.return_value = {"schema": "duckos.foundry.runbook.v1", "steps": []}
        status, output = self.invoke("foundry", "plan", "--profile", "incident")
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output)["schema"], "duckos.foundry.runbook.v1")
        build.assert_called_once_with("incident", collect.return_value)

    @patch("duckos.foundry.collect_foundry_snapshot")
    def test_audit_can_export_to_a_new_file(self, collect):
        collect.return_value = {"schema": "duckos.foundry.snapshot.v1"}
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "foundry.json"
            status, output = self.invoke("foundry", "audit", "--output", str(target))
            self.assertEqual(status, 0)
            payload = json.loads(output)
            self.assertEqual(payload["written"], str(target))
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), collect.return_value)


if __name__ == "__main__":
    unittest.main()
