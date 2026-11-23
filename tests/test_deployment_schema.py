from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from duckos.deployment import build_release_bundle, create_deployment_plan
from duckos.manifest import SCHEMA

ROOT = Path(__file__).resolve().parents[1]


class DeploymentSchemaTests(unittest.TestCase):
    def test_release_metadata_matches_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "root"
            root.mkdir()
            components = []
            for name in ("bootloader", "kernel", "initramfs", "rootfs"):
                payload = (name + "-schema-test").encode("ascii")
                path = root / f"{name}.bin"
                path.write_bytes(payload)
                components.append({
                    "name": name,
                    "path": path.name,
                    "size_bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                })
            manifest = {
                "schema": SCHEMA,
                "name": "DuckOS",
                "version": "schema-test",
                "architecture": "x86_64",
                "kernel_abi": "duckos-reaper-abi-test",
                "components": components,
            }
            archive_path = base / "release.tar.gz"
            build_release_bundle(manifest, root, archive_path)

            with tarfile.open(archive_path, "r:gz") as archive:
                release = json.load(archive.extractfile("duckos-release/release.json"))

            schema = json.loads((ROOT / "schemas/release.v1.schema.json").read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema).validate(release)

    def test_deployment_plan_matches_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "root"
            root.mkdir()
            components = []
            for name in ("bootloader", "kernel", "initramfs", "rootfs"):
                payload = (name + "-schema-test").encode("ascii")
                path = root / f"{name}.bin"
                path.write_bytes(payload)
                components.append({
                    "name": name,
                    "path": path.name,
                    "size_bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                })
            manifest = {
                "schema": SCHEMA,
                "name": "DuckOS",
                "version": "schema-test",
                "architecture": "x86_64",
                "kernel_abi": "duckos-reaper-abi-test",
                "components": components,
            }
            plan = create_deployment_plan(
                manifest, root, target="pxe",
                base_url="https://boot.example.test/duckos",
            )

            layout_schema = json.loads((ROOT / "schemas/image-layout.v1.schema.json").read_text(encoding="utf-8"))
            schema = json.loads((ROOT / "schemas/deployment-plan.v1.schema.json").read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(layout_schema)
            Draft202012Validator.check_schema(schema)
            registry = Registry().with_resource(
                "https://github.com/Ivan-VHS/DuckOS/blob/main/schemas/image-layout.v1.schema.json",
                Resource.from_contents(layout_schema),
            )
            Draft202012Validator(schema, registry=registry).validate(plan)


if __name__ == "__main__":
    unittest.main()
