from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from duckos_tools import filesystem, system


class FilesystemToolTests(unittest.TestCase):
    def test_dir_tree_diff_reports_new_and_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            left = Path(temporary) / "left"
            right = Path(temporary) / "right"
            left.mkdir()
            right.mkdir()
            (left / "same.txt").write_text("before", encoding="utf-8")
            (right / "same.txt").write_text("after", encoding="utf-8")
            (right / "new.txt").write_text("new", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                filesystem.dir_tree_diff(str(left), str(right))

            rendered = output.getvalue()
            self.assertIn("same.txt", rendered)
            self.assertIn("new.txt", rendered)
            self.assertIn("Изменений: 2", rendered)

    def test_dir_tree_diff_json_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            left = Path(temporary) / "left"
            right = Path(temporary) / "right"
            left.mkdir()
            right.mkdir()
            (right / "added.txt").write_text("hello", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                filesystem.dir_tree_diff(str(left), str(right), as_json=True)

            result = json.loads(output.getvalue())
            self.assertEqual(result["schema"], "duckos.dir-tree-diff.v1")
            self.assertEqual(result["changes"][0]["status"], "added")

    def test_atomic_write_replaces_file_and_leaves_no_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "settings.conf"
            target.write_text("old", encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                filesystem.atomic_write(str(target), "new value")

            self.assertEqual(target.read_text(encoding="utf-8"), "new value")
            self.assertEqual([path.name for path in Path(temporary).iterdir()], ["settings.conf"])

    def test_atomic_write_refuses_symlink(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are not supported")
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "real.txt"
            link = Path(temporary) / "alias.txt"
            target.write_text("keep", encoding="utf-8")
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("creating symlinks is not permitted")

            with self.assertRaises(ValueError):
                filesystem.atomic_write(str(link), "do not follow")
            self.assertEqual(target.read_text(encoding="utf-8"), "keep")

    def test_file_age_hist_includes_all_buckets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            Path(temporary, "today.txt").write_text("fresh", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                filesystem.file_age_hist(temporary)
            self.assertIn("до 1 дня", output.getvalue())
            self.assertIn("старше года", output.getvalue())


class SystemToolTests(unittest.TestCase):
    def test_secret_arguments_are_masked(self) -> None:
        arguments = ["service", "--token", "private", "--mode=fast", "--api-key=abc"]
        self.assertEqual(
            system._redact_arguments(arguments),
            ["service", "--token", "[REDACTED]", "--mode=fast", "--api-key=[REDACTED]"],
        )

    def test_system_snapshot_outputs_schema(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            system.sysinfo_snapshot()
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["schema"], "duckos.sysinfo.v1")
        self.assertIn("captured_at", payload)
        self.assertIn("cpu", payload)

    def test_byte_formatter_scales_values(self) -> None:
        self.assertEqual(system._format_bytes(1024), "1.0 KiB")
        self.assertEqual(system._format_bytes(1024 * 1024), "1.0 MiB")


if __name__ == "__main__":
    unittest.main()
