from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from duckos.cli import main


class JoraCliTests(unittest.TestCase):
    def test_jora_build_accepts_an_explicit_reaper_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = root / "request.json"
            request.write_text("{}", encoding="utf-8")
            output = root / "new-app"
            reaper_root = root / "reaper"
            reaper_root.mkdir()
            with patch("duckos.desktop.reaper.ReaperWorkbench") as workbench:
                workbench.return_value.jora_build.return_value = {"ok": True}
                exit_code = main([
                    "jora", "--root", str(reaper_root),
                    "build", str(request), str(output)
                ])
            self.assertEqual(exit_code, 0)
            workbench.assert_called_once_with(reaper_root)
            workbench.return_value.jora_build.assert_called_once_with(request, output)

    def test_jora_build_command_dispatches_to_reaper_workbench(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = root / "request.json"
            request.write_text("{}", encoding="utf-8")
            output = root / "new-app"
            expected = {"ok": True, "result": {"installable": False}}
            with patch("duckos.desktop.reaper.ReaperWorkbench") as workbench:
                workbench.return_value.jora_build.return_value = expected
                exit_code = main(["jora", "build", str(request), str(output)])
            self.assertEqual(exit_code, 0)
            workbench.assert_called_once_with(None)
            workbench.return_value.jora_build.assert_called_once_with(request, output)


if __name__ == "__main__":
    unittest.main()
