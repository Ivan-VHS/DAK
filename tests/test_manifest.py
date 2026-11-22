from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from duckos.manifest import ManifestError, SCHEMA, validate_manifest


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
