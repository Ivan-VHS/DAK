from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from duckos.desktop.reaper import ReaperIntegrationError, ReaperWorkbench


class JoraWorkbenchTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        package = self.root / "reaper"
        package.mkdir()
        (self.root / "pyproject.toml").write_text("[project]\nname='reaper'\n", encoding="utf-8")
        (package / "__main__.py").write_text("from .cli import main\n", encoding="utf-8")
        (package / "cli.py").write_text('if arguments and arguments[0] == "jora":\n    pass\n', encoding="utf-8")
        (package / "jora.py").write_text("def main():\n    pass\n", encoding="utf-8")
        self.request = self.root / "request.json"
        self.request.write_text(json.dumps({
            "schema": "reaper.jora.request.v1",
            "components": ["text.editor"],
            "locales": ["en"]
        }), encoding="utf-8")
        self.output = self.root / "apps" / "LexiDesk"
        self.output.parent.mkdir()
        self.workbench = ReaperWorkbench(self.root, python_executable="python-test")

    def test_jora_build_uses_argv_without_a_shell(self):
        response = {
            "schema": "reaper.jora.build-result.v1",
            "ok": True,
            "installable": False,
            "source_executed": False
        }
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps(response), stderr=""
        )
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
            result = self.workbench.jora_build(self.request, self.output)
        self.assertTrue(result["ok"])
        command = run.call_args.args[0]
        self.assertEqual(command[:5], [
            "python-test", "-m", "reaper", "jora", "build"
        ])
        self.assertIn(str(self.request.resolve()), command)
        self.assertIn(str(self.output), command)
        self.assertEqual(run.call_args.kwargs["shell"], False)
        self.assertEqual(run.call_args.kwargs["timeout"], 120)

    def test_jora_rejects_symlink_request(self):
        link = self.root / "request-link.json"
        try:
            link.symlink_to(self.request)
        except (OSError, NotImplementedError):
            self.skipTest("file symlinks are unavailable")
        with self.assertRaisesRegex(ReaperIntegrationError, "symbolic links"):
            self.workbench.jora_build(link, self.output)

    def test_jora_rejects_non_json_or_non_file_request(self):
        invalid = self.root / "request.txt"
        invalid.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ReaperIntegrationError, r"\.json"):
            self.workbench.jora_build(invalid, self.output)
        with self.assertRaises(ReaperIntegrationError):
            self.workbench.jora_build(self.root, self.output)

    def test_jora_never_overwrites_an_existing_output(self):
        existing = self.root / "existing"
        existing.mkdir()
        marker = existing / "keep.txt"
        marker.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ReaperIntegrationError, "already exists"):
            self.workbench.jora_build(self.request, existing)
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_jora_reports_generator_failures(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=2, stdout="", stderr="Jora: invalid component"
        )
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed):
            with self.assertRaisesRegex(ReaperIntegrationError, "invalid component"):
                self.workbench.jora_build(self.request, self.output)


if __name__ == "__main__":
    unittest.main()
