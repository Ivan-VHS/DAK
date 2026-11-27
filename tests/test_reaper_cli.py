from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from dakos.cli import main


class ReaperCliTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        package = self.root / "reaper"
        package.mkdir()
        (self.root / "pyproject.toml").write_text("[project]\nname='reaper'\n", encoding="utf-8")
        (package / "__main__.py").write_text("from .cli import main\n", encoding="utf-8")
        (package / "cli.py").write_text(
            'if arguments and arguments[0] == "typecheck":\n    pass\n',
            encoding="utf-8",
        )
        (package / "desktop.py").write_text("def main():\n    pass\n", encoding="utf-8")
        (package / "typecheck.py").write_text("def main():\n    pass\n", encoding="utf-8")
        self.source = self.root / "app.rpr"
        self.source.write_text("emit 1\n", encoding="utf-8")

    def invoke(self, *arguments: str) -> tuple[int, str]:
        output = StringIO()
        with redirect_stdout(output):
            result = main(list(arguments))
        return result, output.getvalue()

    def test_reaper_status_is_machine_readable(self):
        code, output = self.invoke("reaper", "--root", str(self.root), "status")
        payload = json.loads(output)
        self.assertEqual(code, 0)
        self.assertTrue(payload["available"])
        self.assertIn("native_studio", payload["capabilities"])
        self.assertIn("static_typecheck", payload["capabilities"])

    def test_reaper_check_returns_the_child_exit_status(self):
        payload = {"ok": False, "diagnostics": [{"code": "RPR-T0004"}]}
        completed = subprocess.CompletedProcess(
            args=[], returncode=1,
            stdout=json.dumps(payload), stderr="",
        )
        with patch("dakos.desktop.reaper.subprocess.run", return_value=completed):
            code, output = self.invoke("reaper", "--root", str(self.root), "check", str(self.source))
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output)["result"], payload)

    def test_reaper_studio_command_starts_the_native_app(self):
        process = type("Process", (), {"pid": 4812})()
        with patch("dakos.desktop.reaper.subprocess.Popen", return_value=process):
            code, output = self.invoke("reaper", "--root", str(self.root), "studio")
        payload = json.loads(output)
        self.assertEqual(code, 0)
        self.assertTrue(payload["started"])
        self.assertEqual(payload["pid"], 4812)
        self.assertFalse(payload["shell"])


if __name__ == "__main__":
    unittest.main()
