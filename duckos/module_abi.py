"""Static validation and dependency ordering for DuckOS driver-module manifests."""
from __future__ import annotations

import re
from typing import Any

SCHEMA = "duckos.driver-module.v1"
MAX_MODULES = 1024
MAX_DEPENDENCIES = 4096
_ARCHITECTURES = {"x86_64", "aarch64", "riscv64", "i686"}
_VERSION = re.compile(
    r"^(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z.-]+))?(?:[+]([0-9A-Za-z.-]+))?$"
)
_KERNEL_ABI = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")


class ModuleABIError(ValueError):
    """Raised when a driver module contract is incompatible or malformed."""


def validate_module(manifest: Any, *, architecture: str, kernel_abi: str) -> dict[str, Any]:
    fields = {"schema", "name", "version", "architecture", "kernel_abi", "entry_symbol", "dependencies", "capabilities"}
    if not isinstance(manifest, dict) or set(manifest) != fields:
        raise ModuleABIError(f"module fields must be exactly {sorted(fields)}")
    if manifest.get("schema") != SCHEMA:
        raise ModuleABIError(f"schema must be {SCHEMA}")
    name = manifest.get("name")
    version = manifest.get("version")
    entry = manifest.get("entry_symbol")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", name):
        raise ModuleABIError("module name must be a lowercase identifier")
    if not isinstance(version, str) or len(version) > 64 or _VERSION.fullmatch(version) is None:
        raise ModuleABIError("module version must be valid semantic version text")
    if not isinstance(entry, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", entry):
        raise ModuleABIError("entry_symbol is not a valid symbol name")
    module_architecture = manifest.get("architecture")
    if not isinstance(module_architecture, str) or module_architecture not in _ARCHITECTURES or module_architecture != architecture:
        raise ModuleABIError("module architecture does not match the target")
    manifest_kernel_abi = manifest.get("kernel_abi")
    if (not isinstance(kernel_abi, str) or _KERNEL_ABI.fullmatch(kernel_abi) is None
            or not isinstance(manifest_kernel_abi, str)
            or _KERNEL_ABI.fullmatch(manifest_kernel_abi) is None
            or manifest_kernel_abi != kernel_abi):
        raise ModuleABIError("module kernel ABI does not match a valid target ABI identifier")
    dependencies = manifest.get("dependencies")
    capabilities = manifest.get("capabilities")
    if not isinstance(dependencies, list) or len(dependencies) > MAX_DEPENDENCIES:
        raise ModuleABIError("dependencies must be a bounded array")
    if any(not isinstance(item, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", item)
           for item in dependencies):
        raise ModuleABIError("dependencies must be module identifiers")
    if len(set(dependencies)) != len(dependencies):
        raise ModuleABIError("dependencies must be unique module identifiers")
    if not isinstance(capabilities, list) or len(capabilities) > 64:
        raise ModuleABIError("capabilities must be a bounded array")
    if any(not isinstance(item, str) or not re.fullmatch(r"[a-z][a-z0-9_.-]{0,63}", item)
           for item in capabilities):
        raise ModuleABIError("capabilities must be lowercase identifiers")
    if len(set(capabilities)) != len(capabilities):
        raise ModuleABIError("capabilities must be unique identifiers")
    return {
        "schema": "duckos.driver-module-validation.v1",
        "valid": True,
        "name": name,
        "version": version,
        "architecture": architecture,
        "kernel_abi": kernel_abi,
        "dependencies": sorted(dependencies),
        "capabilities": sorted(set(capabilities)),
        "module_loaded": False,
    }


def resolve_load_order(modules: list[dict[str, Any]]) -> list[str]:
    """Return a deterministic dependency-first order without recursive traversal."""
    import heapq

    if not isinstance(modules, list) or len(modules) > MAX_MODULES:
        raise ModuleABIError(f"module list must contain at most {MAX_MODULES} items")
    by_name: dict[str, set[str]] = {}
    for item in modules:
        if not isinstance(item, dict):
            raise ModuleABIError("each module needs a name and dependency list")
        name = item.get("name")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", name):
            raise ModuleABIError("module name must be a lowercase identifier")
        if name in by_name:
            raise ModuleABIError(f"duplicate module: {name}")
        dependencies = item.get("dependencies")
        if not isinstance(dependencies, list) or any(
            not isinstance(dep, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", dep)
            for dep in dependencies
        ):
            raise ModuleABIError(f"{name}: dependencies must be an array of module identifiers")
        if len(set(dependencies)) != len(dependencies):
            raise ModuleABIError(f"{name}: duplicate dependency")
        by_name[name] = set(dependencies)

    edge_count = sum(len(value) for value in by_name.values())
    if edge_count > MAX_DEPENDENCIES:
        raise ModuleABIError("module dependency graph exceeds its edge limit")
    for name, dependencies in by_name.items():
        missing = dependencies - by_name.keys()
        if missing:
            raise ModuleABIError(f"{name}: missing dependencies {sorted(missing)}")

    # Kahn's algorithm produces a stable topological order and avoids recursion
    # even for a maximum-sized module list.
    remaining = {name: len(dependencies) for name, dependencies in by_name.items()}
    dependents: dict[str, list[str]] = {name: [] for name in by_name}
    for name, dependencies in by_name.items():
        for dependency in dependencies:
            dependents[dependency].append(name)
    ready = [name for name, count in remaining.items() if count == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        name = heapq.heappop(ready)
        order.append(name)
        for dependent in sorted(dependents[name]):
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                heapq.heappush(ready, dependent)
    if len(order) != len(by_name):
        cyclic = sorted(name for name, count in remaining.items() if count > 0)
        raise ModuleABIError(f"dependency cycle detected among {cyclic}")
    return order
