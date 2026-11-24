from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.validate_reaper_target import MigrationContractError, validate


class ReaperMigrationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "duckos").mkdir()
        (self.root / "federation").mkdir()
        self.pin = "cd84d347959f9b6cf60d87ab3d36bc94e05fd80f"
        self.manifest = {
            "schema": "duckos.reaper-migration.v1",
            "version": 1,
            "project": "DuckOS",
            "migration_goal": "Migrate the DuckOS executable system logic to Reaper.",
            "maturity": "contract-first",
            "reaper_dependency": {
                "repository": "Ivan-VHS/Reaper",
                "url": "https://github.com/Ivan-VHS/Reaper.git",
                "submodule_path": "projects/reaper",
                "pinned_commit": self.pin,
                "source_of_pin": "federation/repositories.v1.json",
                "required_entrypoints": ["--check", "--engine vm"],
                "runtime_status": "reference-runtime-and-vm",
                "native_aot_status": "experimental-scalar-subset",
            },
            "boot_target": {
                "architecture": None, "boot_protocol": None, "kernel_abi": None,
                "decision_status": "undecided", "boot_info_contract": "C11 host-tested",
                "bootable_image": False, "reason": "No approved target decision.",
            },
            "execution_profiles": {
                "reaper_reference_contract": {
                    "status": "implemented", "execution": ["tree-walk", "vm"],
                    "scope": "Host-executed contract only.",
                },
                "reaper_native_kernel": {
                    "status": "planned", "freestanding": False, "object_backend": False,
                    "linker_integration": False, "startup_runtime": False, "bootable": False,
                    "blockers": ["freestanding backend"],
                },
            },
            "source_inventory": [
                {"path": "duckos/kernel/boot.rpr", "subsystem": "boot",
                 "responsibility": "boot phase policy", "maturity": "reference-contract"},
            ],
            "non_reaper_boundaries": [],
            "gates": [
                {"id": "G0", "name": "baseline", "status": "implemented",
                 "acceptance": ["exact pin"]},
                {"id": "G1", "name": "target", "status": "planned",
                 "acceptance": ["approved ABI"]},
            ],
        }
        (self.root / "duckos" / "kernel").mkdir()
        (self.root / "duckos" / "kernel" / "boot.rpr").write_text("# policy\n", encoding="utf-8")
        (self.root / "duckos" / "reaper-migration.v1.json").write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )
        federation = {"repositories": [{
            "id": "reaper", "path": "projects/reaper", "pinned_commit": self.pin,
        }]}
        (self.root / "federation" / "repositories.v1.json").write_text(
            json.dumps(federation), encoding="utf-8"
        )

    def test_validates_exact_source_inventory_and_reaper_pin(self) -> None:
        result = validate(self.root, verify_git=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["reaper_commit"], self.pin)
        self.assertEqual(result["reaper_sources"], 1)
        self.assertFalse(result["bootable_image"])

    def test_detects_unregistered_reaper_source(self) -> None:
        (self.root / "duckos" / "kernel" / "extra.rpr").write_text("# extra\n", encoding="utf-8")
        with self.assertRaisesRegex(MigrationContractError, "unregistered Reaper sources"):
            validate(self.root, verify_git=False)

    def test_detects_pin_drift_between_manifest_and_federation(self) -> None:
        federation_path = self.root / "federation" / "repositories.v1.json"
        federation = json.loads(federation_path.read_text(encoding="utf-8"))
        federation["repositories"][0]["pinned_commit"] = "0" * 40
        federation_path.write_text(json.dumps(federation), encoding="utf-8")
        with self.assertRaisesRegex(MigrationContractError, "disagree about the Reaper pin"):
            validate(self.root, verify_git=False)

    def test_prevents_unapproved_architecture_or_bootability_claim(self) -> None:
        self.manifest["boot_target"]["architecture"] = "x86_64"
        (self.root / "duckos" / "reaper-migration.v1.json").write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(MigrationContractError, "must remain unset"):
            validate(self.root, verify_git=False)

    def test_checks_gitlink_exactly(self) -> None:
        completed = type("Result", (), {
            "returncode": 0,
            "stdout": f"160000 commit {self.pin}\tprojects/reaper\n",
            "stderr": "",
        })()
        with patch("tools.validate_reaper_target.subprocess.run", return_value=completed) as run:
            result = validate(self.root, verify_git=True)
        self.assertTrue(result["ok"])
        self.assertEqual(run.call_args.args[0][:2], ["git", "ls-tree"])


if __name__ == "__main__":
    unittest.main()
