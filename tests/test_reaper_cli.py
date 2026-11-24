from __future__ import annotations

import json
import subprocess
import sys
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

    def test_reaper_studio_command_starts_the_native_app(self):
        process = type("Process", (), {"pid": 4812})()
        with patch("duckos.desktop.reaper.subprocess.Popen", return_value=process):
            code, output = self.invoke("reaper", "--root", str(self.root), "studio")
        payload = json.loads(output)
        self.assertEqual(code, 0)
        self.assertTrue(payload["started"])
        self.assertEqual(payload["pid"], 4812)
        self.assertFalse(payload["shell"])



    def test_reaper_run_forwards_limits_and_returns_program_status(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=4, stdout='{"ok": false, "exit_code": 4}', stderr=""
        )
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
            code, output = self.invoke(
                "reaper", "--root", str(self.root), "run", str(self.source),
                "--steps", "700", "--heap-bytes", "4096",
            )
        self.assertEqual(code, 4)
        self.assertEqual(json.loads(output)["exit_code"], 4)
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--steps") + 1], "700")
        self.assertEqual(command[command.index("--heap-bytes") + 1], "4096")

    def test_reaper_native_build_is_an_explicit_output_operation(self):
        (self.root / "reaper" / "native_compiler.py").write_text(
            "COMPILER = True\\n", encoding="utf-8"
        )
        destination = self.root / "compiled-program"
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps({"ok": True, "mode": "native", "executable": str(destination)}),
            stderr="",
        )
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
            code, output = self.invoke(
                "reaper", "--root", str(self.root), "native",
                str(self.source), "--output", str(destination),
            )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["result"]["mode"], "native")
        self.assertIn("--native", run.call_args.args[0])
        self.assertIn(str(destination), run.call_args.args[0])

    def test_reaper_toolchain_inventory_uses_the_upstream_read_only_module(self):
        (self.root / "reaper" / "toolchain_inventory.py").write_text(
            "def main():\\n    pass\\n", encoding="utf-8"
        )
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout='{"schema":"reaper.toolchain-inventory.v1","tools":[]}',
            stderr="",
        )
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
            code, output = self.invoke("reaper", "--root", str(self.root), "toolchain")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["result"]["schema"], "reaper.toolchain-inventory.v1")
        self.assertEqual(run.call_args.args[0][2], "reaper.toolchain_inventory")

    def test_reaper_lsp_protocol_uses_inherited_stdio(self):
        (self.root / "reaper" / "lsp.py").write_text("def serve():\\n    pass\\n", encoding="utf-8")
        completed = subprocess.CompletedProcess(args=[], returncode=0)
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
            code, output = self.invoke("reaper", "--root", str(self.root), "lsp")
        self.assertEqual(code, 0)
        self.assertEqual(output, "")
        self.assertEqual(run.call_args.args[0], [sys.executable, "-m", "reaper", "lsp"])
        self.assertNotIn("capture_output", run.call_args.kwargs)
        self.assertFalse(run.call_args.kwargs["shell"])

if __name__ == "__main__":
    unittest.main()
