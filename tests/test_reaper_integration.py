from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from duckos.desktop.reaper import ReaperIntegrationError, ReaperWorkbench


class ReaperWorkbenchTests(unittest.TestCase):
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
        (package / "native_compiler.py").write_text("COMPILER = True\n", encoding="utf-8")
        (package / "multisyntax.py").write_text("FRONTENDS = ('reaper', 'brainfuck')\n", encoding="utf-8")
        self.source = self.root / "example.rpr"
        self.source.write_text("emit 42\n", encoding="utf-8")
        self.workbench = ReaperWorkbench(self.root, python_executable="python-test")

    def test_inspect_reports_available_native_capabilities(self):
        result = self.workbench.inspect()
        self.assertTrue(result["available"])
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["repository"], str(self.root))
        self.assertEqual(
            result["capabilities"],
            ["reference_runtime", "cli", "native_studio", "static_typecheck", "native_aot_subset",
             "multi_syntax_frontends", "polyglot_runner", "syntax_validation"],
        )

    def test_check_invokes_reaper_cli_without_a_shell(self):
        response = {"ok": True, "mode": "static-check", "diagnostics": []}
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps(response, ensure_ascii=False), stderr="",
        )
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
            result = self.workbench.check(self.source)
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"], response)
        arguments = run.call_args.args[0]
        self.assertEqual(arguments[:4], ["python-test", "-m", "reaper", "--check"])
        self.assertIn("--json", arguments)
        self.assertEqual(run.call_args.kwargs["shell"], False)
        self.assertEqual(run.call_args.kwargs["cwd"], self.root)

    def test_typecheck_invokes_the_shared_reaper_checker(self):
        response = {"ok": True, "diagnostics": [], "summary": {"errors": 0}}
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps(response, ensure_ascii=False), stderr="",
        )
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
            result = self.workbench.typecheck(self.source)
        self.assertTrue(result["ok"])
        self.assertEqual(run.call_args.args[0][2:4], ["reaper", "typecheck"])
        self.assertIn(str(self.source.resolve()), run.call_args.args[0])

    def test_syntax_registry_uses_the_local_reaper_checkout(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps({"syntaxes": [{"name": "brainfuck"}]}), stderr="",
        )
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
            result = self.workbench.syntax_registry()
        self.assertEqual(result["result"]["syntaxes"][0]["name"], "brainfuck")
        self.assertEqual(run.call_args.args[0][2:], ["reaper", "syntax", "--list", "--json"])
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_syntax_check_accepts_python_subset_and_uses_validation_only(self):
        source = self.root / "sample.py"
        source.write_text("print(42)\n", encoding="utf-8")
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps({"valid": True, "execution_performed": False}), stderr="",
        )
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
            result = self.workbench.check_syntax(source, syntax="python")
        self.assertTrue(result["ok"])
        arguments = run.call_args.args[0]
        self.assertEqual(arguments[2:7], ["reaper", "syntax", "--check", "--json", "--syntax"])
        self.assertIn("python", arguments)
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_polyglot_run_preserves_steps_and_uses_the_shared_runtime(self):
        source = self.root / "demo.polyglot"
        source.write_text("%% brainfuck\n+.", encoding="utf-8")
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps({"block_count": 1, "steps": 2}), stderr="",
        )
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
            result = self.workbench.run_syntax(source, polyglot=True, max_steps=500)
        self.assertEqual(result["result"]["block_count"], 1)
        self.assertIn("--polyglot", run.call_args.args[0])
        self.assertIn("500", run.call_args.args[0])

    def test_syntax_source_extensions_are_validated_without_trusting_symlinks(self):
        unsupported = self.root / "sample.exe"
        unsupported.write_text("not source", encoding="utf-8")
        with self.assertRaisesRegex(ReaperIntegrationError, "supported syntax extension"):
            self.workbench.check_syntax(unsupported)
        link = self.root / "linked.py"
        link.symlink_to(self.root / "sample.py")
        with self.assertRaisesRegex(ReaperIntegrationError, "symbolic links"):
            self.workbench.run_syntax(link)

    def test_studio_launch_uses_a_separate_process(self):
        fake_process = object()
        with patch("duckos.desktop.reaper.subprocess.Popen", return_value=fake_process) as launch:
            result = self.workbench.open_studio()
        self.assertIs(result, fake_process)
        self.assertEqual(launch.call_args.args[0], ["python-test", "-m", "reaper.desktop"])
        self.assertFalse(launch.call_args.kwargs["shell"])

    def test_missing_repository_is_reported_without_launching(self):
        workbench = ReaperWorkbench(self.root / "not-a-repository")
        result = workbench.inspect()
        self.assertFalse(result["available"])
        self.assertEqual(result["status"], "not_found")
        with self.assertRaises(ReaperIntegrationError):
            workbench.open_studio()

    def test_typecheck_requires_a_checkout_with_the_checker(self):
        (self.root / "reaper" / "typecheck.py").unlink()
        result = self.workbench.inspect()
        self.assertNotIn("static_typecheck", result["capabilities"])
        with self.assertRaisesRegex(ReaperIntegrationError, "predates"):
            self.workbench.typecheck(self.source)

    def test_source_file_extension_and_file_kind_are_checked(self):
        wrong = self.root / "notes.txt"
        wrong.write_text("not source", encoding="utf-8")
        with self.assertRaisesRegex(ReaperIntegrationError, r"\.rpr or \.most"):
            self.workbench.check(wrong)
        with self.assertRaises(ReaperIntegrationError):
            self.workbench.check(self.root)

    def test_timeout_is_reported_as_an_integration_error(self):
        with patch(
            "duckos.desktop.reaper.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["python"], timeout=1),
        ):
            with self.assertRaisesRegex(ReaperIntegrationError, "time limit"):
                self.workbench.check(self.source)


if __name__ == "__main__":
    unittest.main()
