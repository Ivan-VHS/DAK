from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from duckos.desktop.beelzebub import BeelzebubIntegrationError, BeelzebubWorkbench


class BeelzebubWorkbenchTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        source = self.root / "apps" / "beelzebub-av" / "src" / "main" / "java" / "sample"
        source.mkdir(parents=True)
        (source / "Probe.java").write_text("final class Probe {}", encoding="utf-8")
        self.workbench = BeelzebubWorkbench(self.root)

    def test_status_is_read_only_and_discovers_sources(self) -> None:
        status = self.workbench.inspect()
        self.assertEqual(status["schema"], "duckos.beelzebub-status.v1")
        self.assertEqual(status["source_files"], 1)
        self.assertFalse(status["built"])
        self.assertEqual(Path(status["repository"]), self.root.resolve())
        self.assertEqual(status["execution_boundary"], "separate-user-space-process")

    def test_scan_rejects_non_directory_before_build(self) -> None:
        with self.assertRaises(BeelzebubIntegrationError):
            self.workbench.scan(self.root / "missing")

    def test_scan_rejects_symbolic_link_before_build(self) -> None:
        target = self.root / "target"
        target.mkdir()
        link = self.root / "link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links are unavailable on this host.")
        with self.assertRaises(BeelzebubIntegrationError):
            self.workbench.scan(link)

    def test_build_artifacts_use_the_configured_user_cache(self) -> None:
        cache = self.root / "user-cache"
        with patch.dict(os.environ, {"DUCKOS_BEELZEBUB_CACHE": str(cache)}):
            workbench = BeelzebubWorkbench(self.root)
        self.assertEqual(workbench.build_directory, cache / "build")
        self.assertEqual(workbench.jar_path, cache / "build" / "beelzebub-av.jar")

    def test_scan_timeout_is_bounded(self) -> None:
        folder = self.root / "folder"
        folder.mkdir()
        with self.assertRaises(ValueError):
            self.workbench.scan(folder, timeout=0)
        with self.assertRaises(ValueError):
            self.workbench.scan(folder, timeout=86401)


if __name__ == "__main__":
    unittest.main()
