from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "initramfs" / "mkinitramfs.py"
SPEC = importlib.util.spec_from_file_location("duckos_mkinitramfs", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
mkinitramfs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mkinitramfs)


class InitramfsTests(unittest.TestCase):
    def test_archive_is_reproducible_and_has_trailer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "root"
            root.mkdir()
            (root / "init").write_text("#!/bin/sh\necho ready\n", encoding="utf-8")
            (root / "bin").mkdir()
            (root / "bin" / "busybox").write_bytes(b"busybox")

            first = Path(temporary) / "first.cpio"
            second = Path(temporary) / "second.cpio"
            mkinitramfs.build_archive(root, first, epoch=123)
            mkinitramfs.build_archive(root, second, epoch=123)

            data = first.read_bytes()
            self.assertEqual(data, second.read_bytes())
            self.assertTrue(data.startswith(b"070701"))
            self.assertIn(b"TRAILER!!!\0", data)

    def test_rejects_symlink_that_escapes_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "root"
            root.mkdir()
            (root / "escape").symlink_to("../outside")
            output = Path(temporary) / "bad.cpio"

            with self.assertRaises(ValueError):
                mkinitramfs.build_archive(root, output, epoch=1)


if __name__ == "__main__":
    unittest.main()
