from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

from dakos.deployment import (
    DeploymentError,
    build_release_bundle,
    create_deployment_plan,
    verify_release_bundle,
    _load_strict_json,
)
from dakos.manifest import SCHEMA


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "components"
        self.root.mkdir()
        components = []
        for name in ("bootloader", "kernel", "initramfs", "rootfs"):
            payload = (name + "-dakos-fixture").encode("ascii")
            path = self.root / f"{name}.bin"
            path.write_bytes(payload)
            components.append({
                "name": name,
                "path": path.name,
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            })
        self.manifest = {
            "schema": SCHEMA,
            "name": "Dak",
            "version": "0.2.0-test",
            "architecture": "x86_64",
            "kernel_abi": "dakos-reaper-abi-test",
            "components": components,
        }
        self.output = Path(self.temporary.name) / "dakos-test.tar.gz"

    def test_release_metadata_rejects_duplicate_nested_json_keys(self):
        with self.assertRaisesRegex(DeploymentError, "duplicate object key"):
            _load_strict_json(
                '{"metadata":{"name":"first","name":"second"}}',
                "release metadata",
            )

    def test_release_metadata_rejects_non_finite_numbers(self):
        for value in ("NaN", "Infinity", "-Infinity", "1e999"):
            with self.subTest(value=value):
                with self.assertRaises(DeploymentError):
                    _load_strict_json('{"metric":' + value + "}", "release metadata")

    def test_release_metadata_bounds_integer_digits_and_nesting(self):
        oversized_integer = "9" * 1025
        with self.assertRaisesRegex(DeploymentError, "1024-digit limit"):
            _load_strict_json('{"count":' + oversized_integer + "}", "manifest")
        depth = 129
        with self.assertRaisesRegex(DeploymentError, "128-level limit"):
            _load_strict_json("[" * depth + "0" + "]" * depth, "manifest")

    def test_release_metadata_depth_scanner_ignores_brackets_in_strings(self):
        payload = '{"text":"' + ("[{" * 1000) + '"}'
        result = _load_strict_json(payload, "release metadata")
        self.assertEqual(result["text"], "[{" * 1000)

    def test_release_metadata_depth_scanner_handles_escaped_quotes(self):
        value = 'quoted " text with brackets [ { ] } and slash \\ marker'
        payload = __import__("json").dumps({"text": value})
        self.assertEqual(_load_strict_json(payload, "release metadata")["text"], value)

    def test_builds_and_verifies_component_bundle(self):
        result = build_release_bundle(self.manifest, self.root, self.output)
        self.assertTrue(result["valid"])
        self.assertFalse(result["bootable_iso_created"])
        report = verify_release_bundle(self.output)
        self.assertTrue(report["valid"])
        self.assertEqual(report["component_count"], 4)
        self.assertEqual(report["signature_status"], "unsigned")
        self.assertFalse(report["bootable_image_verified"])

    def test_release_archive_is_reproducible(self):
        first = build_release_bundle(self.manifest, self.root, self.output)
        second_path = Path(self.temporary.name) / "dakos-test-copy.tar.gz"
        second = build_release_bundle(self.manifest, self.root, second_path)
        self.assertEqual(first["archive_sha256"], second["archive_sha256"])

    def test_detects_corrupt_component_payload(self):
        build_release_bundle(self.manifest, self.root, self.output)
        corrupt = Path(self.temporary.name) / "corrupt.tar.gz"
        with tarfile.open(self.output, "r:gz") as source, tarfile.open(corrupt, "w:gz") as target:
            for member in source.getmembers():
                if member.isfile():
                    stream = source.extractfile(member)
                    with stream:
                        data = stream.read()
                else:
                    data = None
                if member.name.endswith("payload/kernel.bin"):
                    data = b"tampered-kernel"
                    member.size = len(data)
                target.addfile(member, __import__("io").BytesIO(data) if data is not None else None)
        with self.assertRaises(DeploymentError):
            verify_release_bundle(corrupt)

    def test_creates_non_destructive_usb_layout_with_ab_slots(self):
        plan = create_deployment_plan(self.manifest, self.root, target="usb")
        names = [part["name"] for part in plan["image_layout"]["partitions"]]
        self.assertEqual(names, ["efi", "dak_system_a", "dak_system_b", "dak_recovery", "dak_data"])
        self.assertFalse(plan["execution"]["disk_written"])
        self.assertFalse(plan["secure_boot"]["ready"])

    def test_creates_https_ipxe_handoff_and_keeps_verification_boundary_explicit(self):
        plan = create_deployment_plan(
            self.manifest, self.root, target="pxe",
            base_url="https://boot.example.test/dakos", secure_boot=True,
        )
        self.assertIn("#!ipxe", plan["network"]["ipxe_script"])
        self.assertIn("https://boot.example.test/dakos/manifest.json", plan["network"]["manifest_url"])
        self.assertEqual(plan["network"]["manifest_verification_owner"], "native-dak-bootloader")
        self.assertFalse(plan["network"]["signature_enforcement_configured"])
        self.assertTrue(plan["network"]["https_transport"])

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for signing tests")
    def test_ed25519_release_signature_is_verified(self):
        private_key = Path(self.temporary.name) / "release-private.pem"
        public_key = Path(self.temporary.name) / "release-public.pem"
        subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(private_key)], check=True, capture_output=True)
        subprocess.run(["openssl", "pkey", "-in", str(private_key), "-pubout", "-out", str(public_key)], check=True, capture_output=True)
        result = build_release_bundle(self.manifest, self.root, self.output, signing_key=private_key)
        self.assertTrue(result["signed"])
        report = verify_release_bundle(self.output, public_key=public_key)
        self.assertTrue(report["signature_verified"])
        self.assertEqual(report["signature_status"], "verified")

    def test_secure_network_boot_rejects_plain_http(self):
        with self.assertRaisesRegex(DeploymentError, "requires an HTTPS"):
            create_deployment_plan(
                self.manifest, self.root, target="http",
                base_url="http://boot.example.test/dakos", secure_boot=True,
            )

    def test_rejects_unknown_target_and_unsafe_url(self):
        with self.assertRaises(DeploymentError):
            create_deployment_plan(self.manifest, self.root, target="tftp")
        with self.assertRaises(DeploymentError):
            create_deployment_plan(
                self.manifest, self.root, target="pxe",
                base_url="https://user:secret@example.test/dakos",
            )


if __name__ == "__main__":
    unittest.main()
