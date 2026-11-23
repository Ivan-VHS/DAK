from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from duckos.desktop.native_apps import NativeApplicationError, NativeApplicationHub


class NativeApplicationHubTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "projects").mkdir()

    def project(self, name: str) -> Path:
        path = self.root / "projects" / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def hub(self, system: str = "windows") -> NativeApplicationHub:
        return NativeApplicationHub(
            self.root,
            platform_name=system,
            python_executable="python-test",
        )

    def test_missing_checkouts_are_reported_without_launching(self) -> None:
        states = self.hub().inspect_all()
        self.assertEqual(
            {item["id"] for item in states},
            {"reaper", "pytyliki", "oplague", "ventusample"},
        )
        self.assertTrue(all(item["status"] == "checkout_missing" for item in states))
        self.assertTrue(all(item["available"] is False for item in states))

    def test_pytyliki_requires_a_built_windows_gui(self) -> None:
        project = self.project("pytyliki")
        (project / "build" / "Release").mkdir(parents=True)
        (project / "build" / "Release" / "pytyliki-gui.exe").write_bytes(b"test")
        state = self.hub("windows").inspect("pytyliki")
        self.assertEqual(state["status"], "ready")
        self.assertTrue(state["available"])

    def test_pytyliki_is_not_advertised_as_native_on_linux(self) -> None:
        self.project("pytyliki")
        state = self.hub("linux").inspect("pytyliki")
        self.assertEqual(state["status"], "unsupported_platform")
        self.assertFalse(state["available"])

    def test_missing_ventusample_binary_is_not_built_implicitly(self) -> None:
        self.project("ventusample")
        state = self.hub("linux").inspect("ventusample")
        self.assertEqual(state["status"], "not_built")
        self.assertFalse(state["automatic_build"])
        with self.assertRaisesRegex(NativeApplicationError, "native GUI binary was not found"):
            self.hub("linux").open("ventusample")

    def test_ventusample_linux_binary_is_discovered(self) -> None:
        project = self.project("ventusample")
        build = project / "build"
        build.mkdir()
        binary = build / "VentuSample"
        binary.write_bytes(b"test")
        state = self.hub("linux").inspect("ventusample")
        self.assertEqual(state["status"], "ready")
        self.assertEqual(state["launch_target"], str(binary.resolve()))

    def test_oplague_requires_python_entry_and_tkinter(self) -> None:
        project = self.project("oplague")
        (project / "oplague_app.py").write_text(
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        with patch("duckos.desktop.native_apps.importlib.util.find_spec", return_value=None):
            state = self.hub().inspect("oplague")
        self.assertEqual(state["status"], "runtime_unavailable")
        self.assertFalse(state["available"])

    def test_oplague_launch_uses_python_and_never_a_shell(self) -> None:
        project = self.project("oplague")
        entry = project / "oplague_app.py"
        entry.write_text("raise SystemExit(0)\n", encoding="utf-8")
        process = subprocess.CompletedProcess(args=[], returncode=0)
        with patch("duckos.desktop.native_apps.importlib.util.find_spec", return_value=object()):
            with patch("duckos.desktop.native_apps.subprocess.Popen", return_value=process) as launch:
                result = self.hub().open("oplague")
        self.assertIs(result, process)
        self.assertEqual(
            launch.call_args.args[0],
            ["python-test", str(entry.resolve())],
        )
        self.assertFalse(launch.call_args.kwargs["shell"])
        self.assertEqual(launch.call_args.kwargs["cwd"], project.resolve())

    def test_pytyliki_launch_uses_only_the_verified_binary(self) -> None:
        project = self.project("pytyliki")
        (project / "build" / "Release").mkdir(parents=True)
        binary = project / "build" / "Release" / "pytyliki-gui.exe"
        binary.write_bytes(b"test")
        process = subprocess.CompletedProcess(args=[], returncode=0)
        with patch("duckos.desktop.native_apps.subprocess.Popen", return_value=process) as launch:
            result = self.hub().open("pytyliki")
        self.assertIs(result, process)
        self.assertEqual(launch.call_args.args[0], [str(binary.resolve())])
        self.assertFalse(launch.call_args.kwargs["shell"])

    def test_project_symlink_is_rejected(self) -> None:
        external = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(external, ignore_errors=True))
        try:
            (self.root / "projects" / "oplague").symlink_to(external, target_is_directory=True)
        except OSError:
            self.skipTest("directory symlinks are unavailable in this environment")
        state = self.hub().inspect("oplague")
        self.assertEqual(state["status"], "checkout_missing")
        self.assertFalse(state["available"])

    def test_reaper_uses_the_existing_bounded_workbench(self) -> None:
        project = self.project("reaper")
        package = project / "reaper"
        package.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname='reaper'\n", encoding="utf-8")
        (package / "__main__.py").write_text("from .cli import main\n", encoding="utf-8")
        (package / "cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")
        (package / "desktop.py").write_text("def main():\n    return 0\n", encoding="utf-8")
        state = self.hub().inspect("reaper")
        self.assertEqual(state["status"], "ready")
        self.assertTrue(state["available"])

    def test_mora_registry_exposes_all_federated_projects(self) -> None:
        registry_path = Path(__file__).resolve().parents[1] / "duckos" / "mora" / "data" / "apps.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        ids = {item["id"] for item in registry["built_in_apps"]}
        self.assertTrue({"reaper", "pytyliki", "oplague", "ventusample"}.issubset(ids))
        for item in registry["built_in_apps"]:
            if item["id"] in {"reaper", "pytyliki", "oplague", "ventusample"}:
                self.assertEqual(item["scope"], "user-space")
                self.assertTrue(item["source"].startswith("projects/"))

    def test_native_binary_resolving_outside_project_is_rejected(self) -> None:
        project = self.project("ventusample")
        external = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(external, ignore_errors=True))
        (external / "VentuSample").write_bytes(b"test")
        try:
            (project / "build").symlink_to(external, target_is_directory=True)
        except OSError:
            self.skipTest("directory symlinks are unavailable in this environment")
        state = self.hub("linux").inspect("ventusample")
        self.assertEqual(state["status"], "not_built")
        self.assertFalse(state["available"])

    def test_unknown_app_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(NativeApplicationError, "Unknown native application"):
            self.hub().inspect("arbitrary-command")


if __name__ == "__main__":
    unittest.main()
