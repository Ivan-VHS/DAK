from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from duckos.cli import main


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
        target = self.root / "targets" / "duckos"
        target.mkdir(parents=True)
        (target / "boot_contract_v1.rpr").write_text("emit 0\n", encoding="utf-8")
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
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed):
            code, output = self.invoke("reaper", "--root", str(self.root), "check", str(self.source))
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output)["result"], payload)


    def test_reaper_build_dispatches_a_bounded_native_build(self):
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as folder:
            output_path = str(Path(folder) / "app")
            with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
                code, output = self.invoke(
                    "reaper", "--root", str(self.root), "build",
                    str(self.source), "--output", output_path, "--optimization", "1",
                )
        payload = json.loads(output)
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        command = run.call_args.args[0]
        self.assertIn("--native", command)
        self.assertIn("--optimization", command)
        self.assertEqual(command[command.index("--optimization") + 1], "1")
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_reaper_target_check_runs_the_fixed_reference_and_native_fixture(self):
        expected = "0\\n0\\n-2\\n-3\\n-4\\n-5\\n-6\\n-6\\n-7\\n"

        def fake_run(command, **kwargs):
            if command[0] == sys.executable:
                if "--native" in command:
                    Path(command[command.index("--native") + 1]).write_text("test executable", encoding="utf-8")
                    return subprocess.CompletedProcess(command, 0, "", "")
                if "--check" in command:
                    return subprocess.CompletedProcess(command, 0, "", "")
                return subprocess.CompletedProcess(command, 0, expected, "")
            return subprocess.CompletedProcess(command, 0, expected, "")

        import sys
        with patch("duckos.desktop.reaper.subprocess.run", side_effect=fake_run):
            code, output = self.invoke("reaper", "--root", str(self.root), "target-check")
        payload = json.loads(output)
        self.assertEqual(code, 0)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["fixtures"], 9)
        self.assertTrue(payload["native_program_executed"])
        self.assertFalse(payload["hardware_accessed"])

    def test_reaper_studio_command_starts_the_native_app(self):
        process = type("Process", (), {"pid": 4812})()
        with patch("duckos.desktop.reaper.subprocess.Popen", return_value=process):
            code, output = self.invoke("reaper", "--root", str(self.root), "studio")
        payload = json.loads(output)
        self.assertEqual(code, 0)
        self.assertTrue(payload["started"])
        self.assertEqual(payload["pid"], 4812)
        self.assertFalse(payload["shell"])


if __name__ == "__main__":
    unittest.main()
