from __future__ import annotations

import unittest

from duckos.module_abi import ModuleABIError, SCHEMA, resolve_load_order, validate_module


class ModuleABITests(unittest.TestCase):
    def test_validates_target_abi_and_capabilities(self):
        manifest = {
            "schema": SCHEMA, "name": "nvme", "version": "0.1.0",
            "architecture": "x86_64", "kernel_abi": "duckos-kernel-abi-1",
            "entry_symbol": "duckos_nvme_init", "dependencies": ["pci"],
            "capabilities": ["bus.pci", "storage.block"],
        }
        report = validate_module(manifest, architecture="x86_64", kernel_abi="duckos-kernel-abi-1")
        self.assertTrue(report["valid"])
        self.assertFalse(report["module_loaded"])
        with self.assertRaises(ModuleABIError):
            validate_module(manifest, architecture="aarch64", kernel_abi="duckos-kernel-abi-1")

    def test_resolves_dependencies_and_detects_cycles(self):
        modules = [
            {"name": "nvme", "dependencies": ["pci"]},
            {"name": "pci", "dependencies": []},
            {"name": "fs", "dependencies": ["block"]},
            {"name": "block", "dependencies": []},
        ]
        order = resolve_load_order(modules)
        self.assertLess(order.index("pci"), order.index("nvme"))
        self.assertLess(order.index("block"), order.index("fs"))
        with self.assertRaises(ModuleABIError):
            resolve_load_order([
                {"name": "a", "dependencies": ["b"]},
                {"name": "b", "dependencies": ["a"]},
            ])

    def test_missing_dependency_is_not_ignored(self):
        with self.assertRaises(ModuleABIError):
            resolve_load_order([{"name": "usb", "dependencies": ["bus"]}])


if __name__ == "__main__":
    unittest.main()
