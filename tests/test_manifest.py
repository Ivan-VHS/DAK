from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
import unittest

from duckos.manifest import ManifestError, SCHEMA, _hash_file, validate_manifest


class SystemManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.files = {}
        for name in ("bootloader", "kernel", "initramfs", "rootfs"):
            path = self.root / f"{name}.bin"
            payload = (name + "-fixture").encode("ascii")
            path.write_bytes(payload)
            self.files[name] = {
                "name": name, "path": path.name, "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }

    def make_manifest(self):
        return {
            "schema": SCHEMA, "name": "DuckOS", "version": "0.1.0",
            "architecture": "x86_64", "kernel_abi": "duckos-kernel-abi-1",
            "components": list(self.files.values()),
        }

    def test_component_hasher_rejects_symlinks_and_special_files(self):
        target = self.root / "regular.bin"
        target.write_bytes(b"safe component")
        link = self.root / "linked.bin"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are not available on this host")
        with self.assertRaisesRegex(ManifestError, "symbolic link"):
            _hash_file(link)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are POSIX-only")
    def test_component_hasher_rejects_fifo_without_blocking(self):
        fifo = self.root / "component.pipe"
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ManifestError, "regular file"):
            _hash_file(fifo)

    def test_component_hasher_enforces_actual_byte_limit(self):
        candidate = self.root / "bounded.bin"
        candidate.write_bytes(b"12345")
        import duckos.manifest as manifest_module
        previous = manifest_module.MAX_COMPONENT_BYTES
        manifest_module.MAX_COMPONENT_BYTES = 4
        try:
            with self.assertRaisesRegex(ManifestError, "4-byte component limit"):
                _hash_file(candidate)
        finally:
            manifest_module.MAX_COMPONENT_BYTES = previous

    def test_validates_real_component_hashes(self):
        report = validate_manifest(self.make_manifest(), self.root)
        self.assertTrue(report["valid"])
        self.assertEqual(report["component_count"], 4)
        self.assertFalse(report["disk_writes_performed"])

    def test_rejects_hash_mismatch_and_path_traversal(self):
        manifest = self.make_manifest()
        manifest["components"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ManifestError, "SHA-256 mismatch"):
            validate_manifest(manifest, self.root)
        manifest = self.make_manifest()
        manifest["components"][0]["path"] = "../escape"
        with self.assertRaises(ManifestError):
            validate_manifest(manifest, self.root)

    def test_requires_all_boot_components_and_rejects_malformed_component_names(self):
        manifest = self.make_manifest()
        manifest["components"].pop()
        with self.assertRaises(ManifestError):
            validate_manifest(manifest, self.root)
        manifest = self.make_manifest()
        manifest["components"][0]["name"] = []
        with self.assertRaises(ManifestError):
            validate_manifest(manifest, self.root)


if __name__ == "__main__":
    unittest.main()
