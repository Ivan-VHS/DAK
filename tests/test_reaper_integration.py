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
        apps = package / "apps"
        apps.mkdir()
        (apps / "__init__.py").write_text("", encoding="utf-8")
        (apps / "manifest.json").write_text('{"schema":"reaper.application-suite.v1","applications":[]}', encoding="utf-8")
        (package / "apps_cli.py").write_text("def main():\n    pass\n", encoding="utf-8")
        (self.root / "pyproject.toml").write_text("[project]\nname='reaper'\n", encoding="utf-8")
        (package / "__main__.py").write_text("from .cli import main\n", encoding="utf-8")
        (package / "cli.py").write_text(
            'if arguments and arguments[0] == "typecheck":\n    pass\nif arguments and arguments[0] == "apps":\n    pass\n',
            encoding="utf-8",
        )
        (package / "desktop.py").write_text("def main():\n    pass\n", encoding="utf-8")
        (package / "typecheck.py").write_text("def main():\n    pass\n", encoding="utf-8")
        (package / "native_compiler.py").write_text("COMPILER = True\n", encoding="utf-8")
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
            ["reference_runtime", "cli", "native_studio", "static_typecheck", "native_aot_subset", "application_suite"],
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


    def test_list_apps_uses_the_reaper_cli_without_a_shell(self):
        response = {"schema": "reaper.application-suite.v1", "count": 15, "applications": []}
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps(response, ensure_ascii=False), stderr="",
        )
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
            result = self.workbench.list_apps()
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"], response)
        self.assertEqual(run.call_args.args[0], ["python-test", "-m", "reaper", "apps", "list"])
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_run_app_validates_json_and_uses_bounded_subprocess(self):
        source = self.root / "input.json"
        source.write_text('{"readings":[]}', encoding="utf-8")
        output = self.root / "result.json"
        response = {"ok": True, "app_id": "telemetry_guard"}
        completed = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps(response), stderr="",
        )
        with patch("duckos.desktop.reaper.subprocess.run", return_value=completed) as run:
            result = self.workbench.run_app("telemetry_guard", source, output)
        self.assertTrue(result["ok"])
        arguments = run.call_args.args[0]
        self.assertEqual(arguments[:6], [
            "python-test", "-m", "reaper", "apps", "run", "telemetry_guard",
        ])
        self.assertIn(str(source.resolve()), arguments)
        self.assertIn(str(output.resolve()), arguments)
        self.assertEqual(run.call_args.kwargs["timeout"], 30)
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_run_app_rejects_invalid_ids_and_non_json_inputs(self):
        source = self.root / "input.txt"
        source.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ReaperIntegrationError, "application ID"):
            self.workbench.run_app("../telemetry_guard", source)
        with self.assertRaisesRegex(ReaperIntegrationError, r"\.json"):
            self.workbench.run_app("telemetry_guard", source)

    def test_run_app_refuses_to_overwrite_input(self):
        source = self.root / "payload.json"
        source.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ReaperIntegrationError, "must not overwrite"):
            self.workbench.run_app("telemetry_guard", source, source)

    def test_older_checkout_does_not_advertise_application_suite(self):
        (self.root / "reaper" / "apps" / "__init__.py").unlink()
        state = self.workbench.inspect()
        self.assertNotIn("application_suite", state["capabilities"])
        with self.assertRaisesRegex(ReaperIntegrationError, "application suite"):
            self.workbench.list_apps()

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
