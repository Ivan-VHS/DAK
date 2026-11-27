from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from dakos.cli import main
from dakos.manifest import SCHEMA


class DeploymentCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "components"
        self.root.mkdir()
        components = []
        for name in ("bootloader", "kernel", "initramfs", "rootfs"):
            payload = (name + "-cli-fixture").encode("ascii")
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
            "name": "DAKOS",
            "version": "0.2.0-cli-test",
            "architecture": "x86_64",
            "kernel_abi": "dakos-reaper-abi-test",
            "components": components,
        }
        self.manifest_path = self.base / "system-manifest.json"
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def run_cli(self, *arguments):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(list(arguments))
        self.assertEqual(status, 0)
        return output.getvalue()

    def test_build_and_verify_commands_are_wired(self):
        archive = self.base / "DAKOS-test.tar.gz"
        build_output = json.loads(self.run_cli(
            "build-release", str(self.manifest_path), str(self.root), str(archive)
        ))
        self.assertTrue(build_output["valid"])
        verify_output = json.loads(self.run_cli("verify-release", str(archive)))
        self.assertTrue(verify_output["valid"])
        self.assertFalse(verify_output["bootable_image_verified"])

    def test_deployment_plan_command_writes_a_dry_run_json_file(self):
        plan_path = self.base / "plans" / "usb-plan.json"
        output = json.loads(self.run_cli(
            "deployment-plan",
            str(self.manifest_path),
            str(self.root),
            "--target", "usb",
            "--output", str(plan_path),
        ))
        self.assertFalse(output["disk_written"])
        self.assertTrue(plan_path.is_file())
        self.assertTrue(plan_path.read_text(encoding="utf-8").endswith("\n"))
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["target"], "usb")
        self.assertFalse(plan["execution"]["disk_written"])


if __name__ == "__main__":
    unittest.main()
