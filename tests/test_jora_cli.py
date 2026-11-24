from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from duckos.cli import main


class JoraCliTests(unittest.TestCase):
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
