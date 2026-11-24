from __future__ import annotations

import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from duckos.cli import main


class BeelzebubCliTests(unittest.TestCase):
    def invoke(self, *arguments: str) -> tuple[int, str]:
        output = StringIO()
        with redirect_stdout(output):
            result = main(list(arguments))
        return result, output.getvalue()

    def test_status_reports_user_space_only_and_exit_three_when_unavailable(self):
        status = {
            "schema": "duckos.beelzebub-status.v1",
            "available": False,
            "capabilities": {"kernel_enforcement": False, "on_access_interception": False},
        }
        with patch("duckos.security.BeelzebubWorkbench.inspect", return_value=status):
            code, output = self.invoke("beelzebub", "status")
        self.assertEqual(code, 3)
        self.assertFalse(json.loads(output)["capabilities"]["kernel_enforcement"])

    def test_scan_forwards_only_explicit_arguments_and_preserves_malicious_exit(self):
        payload = {"schema": "beelzebub.scan-batch.v1", "summary": {"files": 1, "clean": 0, "malicious": 1, "indeterminate": 0}, "files": []}
        with patch("duckos.security.BeelzebubWorkbench.scan", return_value=(2, payload)) as scan:
            code, output = self.invoke(
                "beelzebub", "scan", "sample.bin",
                "--hashdb", "hashes.db", "--signature", "hashes.sig", "--public-key", "feed.pub",
                "--clam-port", "3310", "--quarantine",
                "--quarantine-dir", "private-quarantine", "--quarantine-key", "private.key",
            )
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output)["summary"]["malicious"], 1)
        args, kwargs = scan.call_args
        self.assertEqual(args[0], Path("sample.bin"))
        self.assertEqual(kwargs["clam_port"], 3310)
        self.assertTrue(kwargs["quarantine"])
        self.assertEqual(kwargs["public_key"], Path("feed.pub"))

    def test_scan_subcommand_requires_target(self):
        with self.assertRaises(SystemExit):
            self.invoke("beelzebub", "scan")


if __name__ == "__main__":
    unittest.main()
