from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "pkg" / "duckpkg.py"
SPEC = importlib.util.spec_from_file_location("duckos_duckpkg", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
duckpkg = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(duckpkg)


def make_package(path: Path, payload: bytes = b"hello\n") -> None:
    manifest = {
        "name": "hello",
        "version": "1.0.0",
        "files": {"usr/bin/hello": hashlib.sha256(payload).hexdigest()},
    }

    with tarfile.open(path, "w:gz") as archive:
        manifest_bytes = json.dumps(manifest).encode("utf-8")
        manifest_info = tarfile.TarInfo("manifest.json")
        manifest_info.size = len(manifest_bytes)
        archive.addfile(manifest_info, io.BytesIO(manifest_bytes))

        payload_info = tarfile.TarInfo("payload/usr/bin/hello")
        payload_info.mode = 0o755
        payload_info.size = len(payload)
        archive.addfile(payload_info, io.BytesIO(payload))


class PackageManagerTests(unittest.TestCase):
    def test_install_verify_and_remove(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "root"
            archive = Path(temporary) / "hello.tar.gz"
            make_package(archive)

            installed = duckpkg.install_package(archive, root)
            self.assertEqual((installed / "usr/bin/hello").read_bytes(), b"hello\n")
            self.assertEqual(duckpkg.verify_package(root, "hello"), [])
            self.assertEqual(len(duckpkg.list_packages(root)), 1)

            duckpkg.remove_package(root, "hello", "1.0.0")
            self.assertEqual(duckpkg.list_packages(root), [])

    def test_rejects_payload_digest_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "root"
            archive = Path(temporary) / "bad.tar.gz"
            manifest = {
                "name": "hello",
                "version": "1.0.0",
                "files": {"usr/bin/hello": hashlib.sha256(b"expected").hexdigest()},
            }

            with tarfile.open(archive, "w:gz") as output:
                manifest_bytes = json.dumps(manifest).encode("utf-8")
                item = tarfile.TarInfo("manifest.json")
                item.size = len(manifest_bytes)
                output.addfile(item, io.BytesIO(manifest_bytes))
                payload = b"tampered"
                item = tarfile.TarInfo("payload/usr/bin/hello")
                item.size = len(payload)
                output.addfile(item, io.BytesIO(payload))

            with self.assertRaises(duckpkg.PackageError):
                duckpkg.install_package(archive, root)

    def test_rejects_path_traversal(self) -> None:
        with self.assertRaises(duckpkg.PackageError):
            duckpkg.safe_relative_path("../escape")


if __name__ == "__main__":
    unittest.main()
