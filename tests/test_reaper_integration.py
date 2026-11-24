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
        target = self.root / "targets" / "duckos"
        target.mkdir(parents=True)
        (target / "boot_contract_v1.rpr").write_text("emit 0\n", encoding="utf-8")
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
            ["reference_runtime", "cli", "native_studio", "static_typecheck", "native_aot_subset"],
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


    def test_native_build_uses_the_explicit_output_path_and_no_shell(self):
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "program"
            with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
                result = self.workbench.build_native(self.source, output, optimization="s")
        self.assertTrue(result["ok"])
        command = run.call_args.args[0]
        self.assertEqual(command[:4], ["python-test", "-m", "reaper", str(self.source.resolve())])
        self.assertEqual(command[command.index("--native") + 1], str(output.resolve()))
        self.assertEqual(command[command.index("--optimization") + 1], "s")
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertEqual(run.call_args.kwargs["timeout"], 150)

    def test_native_build_rejects_source_overwrite_and_invalid_optimization(self):
        with self.assertRaisesRegex(ReaperIntegrationError, "overwrite"):
            self.workbench.build_native(self.source, self.source)
        with self.assertRaisesRegex(ReaperIntegrationError, "optimization"):
            self.workbench.build_native(self.source, self.root / "program", optimization="fast")

    def test_duckos_target_check_compares_reference_and_native_output(self):
        expected = "0\\n0\\n-2\\n-3\\n-4\\n-5\\n-6\\n-6\\n-7\\n"

        def fake_run(command, **kwargs):
            if command[0] == "python-test":
                if "--native" in command:
                    native_output = Path(command[command.index("--native") + 1])
                    native_output.write_text("native test executable", encoding="utf-8")
                    return subprocess.CompletedProcess(command, 0, "", "")
                if "--check" in command:
                    return subprocess.CompletedProcess(command, 0, "", "")
                return subprocess.CompletedProcess(command, 0, expected, "")
            return subprocess.CompletedProcess(command, 0, expected, "")

        with patch("duckos.desktop.reaper.subprocess.run", side_effect=fake_run) as run:
            result = self.workbench.check_duckos_target()
        self.assertTrue(result["valid"])
        self.assertEqual(result["fixtures"], 9)
        self.assertEqual(result["reference_runtime"], "pass")
        self.assertEqual(result["native_aot"], "pass")
        self.assertTrue(result["native_program_executed"])
        self.assertFalse(result["hardware_accessed"])
        self.assertEqual(run.call_count, 4)
        self.assertTrue(all(call.kwargs["shell"] is False for call in run.call_args_list))
        self.assertTrue(any("--syntax-only" in call.args[0] for call in run.call_args_list))

    def test_duckos_target_check_rejects_a_missing_target(self):
        (self.root / "targets" / "duckos" / "boot_contract_v1.rpr").unlink()
        with self.assertRaisesRegex(ReaperIntegrationError, "does not contain"):
            self.workbench.check_duckos_target()

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

    def test_invalid_environment_override_does_not_fall_back_to_checkout(self):
        with patch.dict("os.environ", {"DUCKOS_REAPER_ROOT": str(self.root / "not-a-repository")}):
            workbench = ReaperWorkbench()
        self.assertFalse(workbench.inspect()["available"])
        self.assertEqual(workbench.inspect()["status"], "not_found")

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
