from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from duckos.desktop.reaper import MAX_OUTPUT_BYTES, ReaperIntegrationError, ReaperWorkbench


class FakeProcess:
    def __init__(self, *, returncode=0, stdout="", stderr="", timeout_once=False):
        self.returncode = returncode
        self.stdout = io.BytesIO(stdout.encode("utf-8"))
        self.stderr = io.BytesIO(stderr.encode("utf-8"))
        self.timeout_once = timeout_once
        self.killed = False
        self.wait_timeout = None

    def wait(self, timeout=None):
        self.wait_timeout = timeout
        if self.timeout_once and not self.killed:
            raise subprocess.TimeoutExpired(cmd=["reaper"], timeout=timeout)
        return self.returncode

    def kill(self):
        self.killed = True


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
        process = FakeProcess(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        with patch("duckos.desktop.reaper.subprocess.Popen", return_value=process) as run:
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
        process = FakeProcess(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        with patch("duckos.desktop.reaper.subprocess.Popen", return_value=process) as run:
            result = self.workbench.typecheck(self.source)
        self.assertTrue(result["ok"])
        self.assertEqual(run.call_args.args[0][2:4], ["reaper", "typecheck"])
        self.assertIn(str(self.source.resolve()), run.call_args.args[0])

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
        process = FakeProcess(timeout_once=True)
        with patch("duckos.desktop.reaper.subprocess.Popen", return_value=process):
            with self.assertRaisesRegex(ReaperIntegrationError, "time limit"):
                self.workbench.check(self.source)
        self.assertTrue(process.killed)



    def test_run_uses_explicit_interpreter_limits_and_keeps_native_ffi_disabled(self):
        response = {"ok": True, "result": 42}
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(response), stderr="")
        process = FakeProcess(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        with patch("duckos.desktop.reaper.subprocess.Popen", return_value=process) as run:
            result = self.workbench.run(self.source, limits={"steps": 500, "heap_bytes": 1024})
        self.assertTrue(result["ok"])
        command = run.call_args.args[0]
        self.assertIn("--steps", command)
        self.assertEqual(command[command.index("--steps") + 1], "500")
        self.assertEqual(command[command.index("--heap-bytes") + 1], "1024")
        self.assertIn("--json", command)
        self.assertNotIn("--allow-native-ffi", command)
        self.assertEqual(process.wait_timeout, 60)
        self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_run_rejects_resource_limits_above_the_bridge_policy(self):
        with self.assertRaisesRegex(ReaperIntegrationError, "steps"):
            self.workbench.run(self.source, limits={"steps": 10_000_001})

    def test_module_graph_uses_reaper_read_only_inspection_mode(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='{"modules": []}', stderr=""
        )
        process = FakeProcess(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        with patch("duckos.desktop.reaper.subprocess.Popen", return_value=process) as run:
            result = self.workbench.module_graph(self.source)
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"], {"modules": []})
        self.assertIn("--module-graph", run.call_args.args[0])
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_native_build_invokes_only_the_experimental_aot_subset(self):
        destination = self.root / "program"
        response = {"ok": True, "mode": "native", "executable": str(destination)}
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(response), stderr=""
        )
        process = FakeProcess(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        with patch("duckos.desktop.reaper.subprocess.Popen", return_value=process) as run:
            result = self.workbench.native_build(self.source, destination, optimization="s")
        self.assertTrue(result["ok"])
        command = run.call_args.args[0]
        self.assertEqual(command[2:4], ["reaper", "--native"])
        self.assertIn(str(destination), command)
        self.assertIn("--optimization", command)
        self.assertEqual(command[command.index("--optimization") + 1], "s")
        self.assertEqual(process.wait_timeout, 120)
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_emit_c_uses_a_distinct_destination_and_never_overwrites_source(self):
        destination = self.root / "program.c"
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='{"ok": true, "mode": "emit-c"}', stderr=""
        )
        process = FakeProcess(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        with patch("duckos.desktop.reaper.subprocess.Popen", return_value=process) as run:
            result = self.workbench.emit_c(self.source, destination)
        self.assertTrue(result["ok"])
        self.assertIn("--emit-c", run.call_args.args[0])
        with self.assertRaisesRegex(ReaperIntegrationError, "overwrite"):
            self.workbench.emit_c(self.source, self.source)

    def test_toolchain_inventory_uses_the_read_only_inventory_module(self):
        (self.root / "reaper" / "toolchain_inventory.py").write_text(
            'def main():\\n    pass\\n', encoding="utf-8"
        )
        response = {"schema": "reaper.toolchain-inventory.v1", "tools": []}
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(response), stderr=""
        )
        process = FakeProcess(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        with patch("duckos.desktop.reaper.subprocess.Popen", return_value=process) as run:
            result = self.workbench.toolchain_inventory(search_path="/usr/bin")
        self.assertTrue(result["ok"])
        command = run.call_args.args[0]
        self.assertEqual(command[2:4], ["reaper.toolchain_inventory", "--path"])
        self.assertEqual(command[4], "/usr/bin")
        self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)

    def test_lsp_and_dap_are_passed_through_without_capturing_protocol_streams(self):
        (self.root / "reaper" / "lsp.py").write_text("def serve():\\n    pass\\n", encoding="utf-8")
        (self.root / "reaper" / "dap.py").write_text("def serve():\\n    pass\\n", encoding="utf-8")
        with patch(
            "duckos.desktop.reaper.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=7),
        ) as run:
            code = self.workbench.serve_protocol("lsp")
        self.assertEqual(code, 7)
        self.assertEqual(run.call_args.args[0], ["python-test", "-m", "reaper", "lsp"])
        self.assertEqual(run.call_args.kwargs["cwd"], self.root)
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertNotIn("capture_output", run.call_args.kwargs)
        with self.assertRaisesRegex(ReaperIntegrationError, "protocol"):
            self.workbench.serve_protocol("http")

    def test_missing_lsp_module_is_not_advertised_or_started(self):
        state = self.workbench.inspect()
        self.assertNotIn("language_server", state["capabilities"])
        with self.assertRaisesRegex(ReaperIntegrationError, "LSP"):
            self.workbench.serve_protocol("lsp")

    def test_source_size_is_bounded_before_subprocess_launch(self):
        large_source = self.root / "large.rpr"
        large_source.write_bytes(b"x" * (4 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(ReaperIntegrationError, "input limit"):
            self.workbench.check(large_source)


    def test_output_capture_is_bounded_before_text_decoding(self):
        large_output = "x" * (MAX_OUTPUT_BYTES + 4096)
        process = FakeProcess(stdout=large_output)
        with patch("duckos.desktop.reaper.subprocess.Popen", return_value=process):
            result = self.workbench.check(self.source)
        self.assertTrue(result["truncated"])
        self.assertEqual(len(result["stdout"].encode("utf-8")), MAX_OUTPUT_BYTES)

    def test_capability_status_matches_the_versioned_duckos_contract(self):
        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "reaper-workbench.v1.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        report = self.workbench.inspect()
        self.assertEqual(schema["properties"]["schema"]["const"], report["schema"])
        self.assertEqual(schema["properties"]["runtime_boundary"]["const"], report["runtime_boundary"])
        self.assertFalse(report["execution_is_os_sandboxed"])
        self.assertEqual(report["capability_states"]["native_aot_subset"], "experimental")

if __name__ == "__main__":
    unittest.main()
