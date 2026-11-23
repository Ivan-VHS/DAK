"""Host runtime discovery, private executable storage and direct process creation.

This module is a host-side execution service. It is not a PE loader inside the
DuckOS kernel; the kernel process model and syscall ABI are still future work.
"""
from __future__ import annotations

import ctypes.util
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
import uuid
import zipfile
from datetime import datetime, timezone
from typing import Any, BinaryIO

from .executable import (
    ExecutableFormatError,
    inspect_executable,
    is_launchable_dos_image,
    is_launchable_windows_image,
)

MAX_EXECUTABLE_BYTES = 8 * 1024 * 1024 * 1024
MAX_ARCHIVE_BYTES = 8 * 1024 * 1024 * 1024
MAX_APP_BYTES = 16 * 1024 * 1024 * 1024
MAX_APP_FILES = 4096
MAX_ARGUMENTS = 128
MAX_ARGUMENT_LENGTH = 2048
_APP_SCHEMA = "duckos.executable-app.v1"
_VM_SCHEMA = "duckos.guest-machine.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_APP_ID = re.compile(r"^[0-9a-f]{24}$")
_VM_NAME = re.compile(r"^[a-z][a-z0-9-]{0,47}$")
_DXVK_DLLS = ("d3d9.dll", "d3d10core.dll", "d3d11.dll", "dxgi.dll")


class RuntimeErrorBase(RuntimeError):
    """Base error for runtime discovery, import and launch operations."""


class RuntimeUnavailable(RuntimeErrorBase):
    """Raised when the host does not have the selected execution runtime."""


class RuntimePermissionError(RuntimeErrorBase):
    """Raised when a launch would exceed the explicitly approved policy."""


class AppStoreError(RuntimeErrorBase):
    """Raised for unsafe or invalid imported application packages."""


class AppStore:
    """Private, content-addressed store for user-imported applications."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else default_state_dir()
        self.apps = self.root / "apps"
        self.staging = self.root / "staging"
        self.data = self.root / "app-data"
        self.prefixes = self.root / "wine-prefixes"
        self.vms = self.root / "vms"
        for folder in (self.root, self.apps, self.staging, self.data, self.prefixes, self.vms):
            _make_private_directory(folder)

    def import_source(
        self,
        source: str | Path,
        *,
        entrypoint: str | None = None,
        display_name: str | None = None,
    ) -> dict[str, Any]:
        supplied = Path(source).expanduser()
        if supplied.is_symlink():
            raise AppStoreError("source must not be a symbolic link")
        try:
            resolved = supplied.resolve(strict=True)
        except OSError as error:
            raise AppStoreError(f"cannot open source: {error}") from error

        stage = Path(tempfile.mkdtemp(prefix="import-", dir=self.staging))
        try:
            if resolved.is_dir():
                self._copy_directory(resolved, stage)
            elif resolved.is_file() and resolved.suffix.lower() == ".zip":
                self._extract_zip(resolved, stage)
            elif resolved.is_file():
                if resolved.stat().st_size > MAX_EXECUTABLE_BYTES:
                    raise AppStoreError("executable exceeds the 8 GiB import limit")
                safe_name = _safe_filename(resolved.name)
                self._copy_file(resolved, stage / safe_name, MAX_EXECUTABLE_BYTES)
            else:
                raise AppStoreError("source must be a file, ZIP package or directory")

            files = self._build_file_manifest(stage)
            entry = self._select_entrypoint(stage, files, entrypoint)
            executable = inspect_executable(stage / entry)
            if not (is_launchable_windows_image(executable) or is_launchable_dos_image(executable)):
                raise AppStoreError("entry point is not a launchable PE or DOS executable")
            if executable.get("is_dll"):
                raise AppStoreError("DLL files are libraries and cannot be launched as applications")

            tree_hash = _tree_hash(files)
            app_id = tree_hash[:24]
            name = _safe_display_name(display_name or Path(entry).stem)
            manifest = {
                "schema": _APP_SCHEMA,
                "id": app_id,
                "name": name,
                "entrypoint": entry,
                "executable": executable,
                "files": files,
                "imported_at": datetime.now(timezone.utc).isoformat(),
                "trust_state": "untrusted",
                "requested_capabilities": ["graphics", "audio", "input", "filesystem.appdata"],
                "signature_state": "not_verified",
            }
            self._write_json(stage / "manifest.json", manifest)
            destination = self.apps / app_id
            if destination.exists():
                shutil.rmtree(stage)
                return self.get_app(app_id)
            os.replace(stage, destination)
            _make_private_directory(destination)
            return self.get_app(app_id)
        except Exception:
            if stage.exists():
                shutil.rmtree(stage, ignore_errors=True)
            raise

    def _copy_directory(self, source: Path, destination: Path) -> None:
        total = 0
        count = 0
        for current, directories, filenames in os.walk(source, topdown=True, followlinks=False):
            current_path = Path(current)
            relative_dir = current_path.relative_to(source)
            target_dir = destination / relative_dir
            _make_private_directory(target_dir)

            for directory in list(directories):
                item = current_path / directory
                if item.is_symlink():
                    raise AppStoreError(f"symbolic-link directories are not allowed: {directory}")

            directories.sort()
            for filename in sorted(filenames):
                item = current_path / filename
                if item.is_symlink() or not item.is_file():
                    raise AppStoreError(f"only regular files can be imported: {filename}")
                relative = item.relative_to(source).as_posix()
                _validate_relative_path(relative)
                size = item.stat().st_size
                total += size
                count += 1
                if size > MAX_EXECUTABLE_BYTES or total > MAX_APP_BYTES or count > MAX_APP_FILES:
                    raise AppStoreError("application package exceeds its file-count or size limit")
                self._copy_file(item, destination / relative, MAX_EXECUTABLE_BYTES)

    def _extract_zip(self, archive: Path, destination: Path) -> None:
        if archive.stat().st_size > MAX_ARCHIVE_BYTES:
            raise AppStoreError("ZIP archive exceeds the 8 GiB compressed-size limit")
        total = 0
        seen: set[str] = set()
        count = 0
        try:
            with zipfile.ZipFile(archive, "r") as bundle:
                for member in bundle.infolist():
                    raw_name = member.filename
                    if member.is_dir():
                        normalized = raw_name.rstrip("/")
                        if normalized:
                            _validate_relative_path(normalized)
                            _make_private_directory(destination.joinpath(*PurePosixPath(normalized).parts))
                        continue

                    relative = _validate_relative_path(raw_name)
                    key = relative.casefold()
                    if key in seen:
                        raise AppStoreError(f"duplicate ZIP path: {relative}")
                    seen.add(key)

                    unix_mode = member.external_attr >> 16
                    if stat.S_ISLNK(unix_mode):
                        raise AppStoreError(f"symbolic links are not allowed in ZIP files: {relative}")
                    if member.flag_bits & 0x1:
                        raise AppStoreError("encrypted ZIP entries are not supported")

                    size = member.file_size
                    compressed = member.compress_size
                    if size > MAX_EXECUTABLE_BYTES:
                        raise AppStoreError(f"ZIP entry is too large: {relative}")
                    if size and compressed == 0:
                        raise AppStoreError(f"invalid compressed size: {relative}")
                    if compressed and size > compressed * 500:
                        raise AppStoreError(f"ZIP compression ratio is excessive: {relative}")

                    total += size
                    count += 1
                    if total > MAX_APP_BYTES or count > MAX_APP_FILES:
                        raise AppStoreError("ZIP package exceeds the total size or file-count limit")

                    output = destination.joinpath(*PurePosixPath(relative).parts)
                    _make_private_directory(output.parent)
                    with bundle.open(member, "r") as input_stream:
                        self._copy_stream(input_stream, output, MAX_EXECUTABLE_BYTES, expected_size=size)
        except (zipfile.BadZipFile, OSError) as error:
            raise AppStoreError(f"cannot read ZIP package: {error}") from error

    @staticmethod
    def _copy_stream(
        source: BinaryIO,
        destination: Path,
        limit: int,
        *,
        expected_size: int | None = None,
    ) -> tuple[int, str]:
        digest = hashlib.sha256()
        total = 0
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            with destination.open("xb") as output:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > limit:
                        raise AppStoreError(f"{destination.name} exceeds the import limit")
                    digest.update(chunk)
                    output.write(chunk)
            if expected_size is not None and total != expected_size:
                destination.unlink(missing_ok=True)
                raise AppStoreError(f"ZIP entry size mismatch: {destination.name}")
            try:
                destination.chmod(0o600)
            except OSError:
                pass
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return total, digest.hexdigest()

    def _copy_file(self, source: Path, destination: Path, limit: int) -> None:
        with source.open("rb") as input_stream:
            self._copy_stream(input_stream, destination, limit)

    def _build_file_manifest(self, root: Path) -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []
        total = 0
        for item in sorted(root.rglob("*")):
            if item.is_symlink():
                raise AppStoreError("symbolic links are not allowed in imported packages")
            if not item.is_file() or item.name == "manifest.json":
                continue
            relative = item.relative_to(root).as_posix()
            _validate_relative_path(relative)
            size, digest = _hash_file(item, MAX_EXECUTABLE_BYTES)
            total += size
            files.append({"path": relative, "size_bytes": size, "sha256": digest})
            if len(files) > MAX_APP_FILES or total > MAX_APP_BYTES:
                raise AppStoreError("application package exceeds its limits")
        if not files:
            raise AppStoreError("application package contains no files")
        return files

    @staticmethod
    def _select_entrypoint(
        root: Path,
        files: list[dict[str, Any]],
        requested: str | None,
    ) -> str:
        if requested:
            relative = _validate_relative_path(requested.replace("\\", "/"))
            if not (root / relative).is_file():
                raise AppStoreError("requested entry point is not present in the package")
            try:
                info = inspect_executable(root / relative)
            except ExecutableFormatError as error:
                raise AppStoreError(str(error)) from error
            if not (is_launchable_windows_image(info) or is_launchable_dos_image(info)):
                raise AppStoreError("requested entry point is not a supported PE or DOS executable")
            return relative

        candidates: list[str] = []
        for record in files:
            if Path(record["path"]).suffix.lower() not in {".exe", ".com"}:
                continue
            try:
                info = inspect_executable(root / record["path"])
            except ExecutableFormatError:
                continue
            if is_launchable_windows_image(info) or is_launchable_dos_image(info):
                candidates.append(record["path"])
        if not candidates:
            raise AppStoreError("no PE or DOS entry point found; specify --entrypoint")
        if len(candidates) > 1:
            raise AppStoreError(
                "package contains multiple executables; choose one with --entrypoint"
            )
        return candidates[0]

    def get_app(self, app_id: str) -> dict[str, Any]:
        if not isinstance(app_id, str) or not _APP_ID.fullmatch(app_id):
            raise AppStoreError("invalid application identifier")
        folder = self.apps / app_id
        manifest_path = folder / "manifest.json"
        if folder.is_symlink() or manifest_path.is_symlink():
            raise AppStoreError("application store contains a symbolic link")
        try:
            if manifest_path.stat().st_size > 1024 * 1024:
                raise AppStoreError("application manifest exceeds 1 MiB")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AppStoreError(f"cannot read application manifest: {error}") from error

        required = {
            "schema", "id", "name", "entrypoint", "executable", "files",
            "imported_at", "trust_state", "requested_capabilities", "signature_state",
        }
        if not isinstance(manifest, dict) or set(manifest) != required:
            raise AppStoreError("application manifest has an invalid structure")
        if manifest["schema"] != _APP_SCHEMA or manifest["id"] != app_id:
            raise AppStoreError("application manifest identity does not match its store path")
        if manifest["trust_state"] != "untrusted" or manifest["signature_state"] != "not_verified":
            raise AppStoreError("imported application trust state is invalid")
        files = manifest["files"]
        if not isinstance(files, list) or not 1 <= len(files) <= MAX_APP_FILES:
            raise AppStoreError("application file list is invalid")

        seen: set[str] = set()
        total = 0
        normalized: list[dict[str, Any]] = []
        for record in files:
            if not isinstance(record, dict) or set(record) != {"path", "size_bytes", "sha256"}:
                raise AppStoreError("application file record is invalid")
            relative = _validate_relative_path(record["path"])
            key = relative.casefold()
            if key in seen:
                raise AppStoreError("duplicate application file path")
            seen.add(key)
            expected_size = record["size_bytes"]
            expected_hash = record["sha256"]
            if isinstance(expected_size, bool) or not isinstance(expected_size, int) or not 0 <= expected_size <= MAX_EXECUTABLE_BYTES:
                raise AppStoreError("application file size is invalid")
            if not isinstance(expected_hash, str) or not _SHA256.fullmatch(expected_hash):
                raise AppStoreError("application file hash is invalid")
            path = folder.joinpath(*PurePosixPath(relative).parts)
            if path.is_symlink():
                raise AppStoreError(f"application file is a symbolic link: {relative}")
            size, digest = _hash_file(path, MAX_EXECUTABLE_BYTES)
            if size != expected_size or digest != expected_hash:
                raise AppStoreError(f"application file failed integrity verification: {relative}")
            total += size
            if total > MAX_APP_BYTES:
                raise AppStoreError("application exceeds the aggregate size limit")
            normalized.append({"path": relative, "size_bytes": size, "sha256": digest})

        if _tree_hash(normalized)[:24] != app_id:
            raise AppStoreError("application package identity hash does not match its files")
        entry = _validate_relative_path(manifest["entrypoint"])
        if entry not in {record["path"] for record in normalized}:
            raise AppStoreError("application entry point is not in its file manifest")
        actual = inspect_executable(folder / entry)
        if actual != manifest["executable"]:
            raise AppStoreError("application entry point metadata has changed")
        if not (is_launchable_windows_image(actual) or is_launchable_dos_image(actual)):
            raise AppStoreError("application entry point is not launchable")
        return manifest

    def list_apps(self, *, verify: bool = True) -> list[dict[str, Any]]:
        result = []
        for folder in sorted(self.apps.iterdir()):
            if not folder.is_dir() or folder.is_symlink() or not _APP_ID.fullmatch(folder.name):
                continue
            try:
                manifest = self.get_app(folder.name) if verify else json.loads(
                    (folder / "manifest.json").read_text(encoding="utf-8")
                )
                result.append(_public_app(manifest))
            except (OSError, ValueError, AppStoreError):
                result.append({"id": folder.name, "name": "Повреждённый пакет", "status": "invalid"})
        return result

    def app_paths(self, app_id: str) -> tuple[Path, Path, Path]:
        manifest = self.get_app(app_id)
        root = self.apps / app_id
        entry = root.joinpath(*PurePosixPath(manifest["entrypoint"]).parts)
        data = self.data / app_id
        _make_private_directory(data)
        _make_private_directory(data / "home")
        _make_private_directory(data / "cache")
        return root, entry, data

    def register_vm(
        self,
        name: str,
        disk_path: str | Path,
        *,
        memory_mb: int = 4096,
        cpus: int = 4,
    ) -> dict[str, Any]:
        if not isinstance(name, str) or not _VM_NAME.fullmatch(name):
            raise RuntimeErrorBase("VM name must be a lowercase identifier")
        if isinstance(memory_mb, bool) or not 1024 <= memory_mb <= 65536:
            raise RuntimeErrorBase("VM memory must be between 1024 and 65536 MiB")
        if isinstance(cpus, bool) or not 1 <= cpus <= min(32, os.cpu_count() or 1):
            raise RuntimeErrorBase("VM CPU count must be between 1 and the host CPU count (maximum 32)")
        supplied = Path(disk_path).expanduser()
        if supplied.is_symlink():
            raise RuntimeErrorBase("VM disk must not be a symbolic link")
        try:
            disk = supplied.resolve(strict=True)
        except OSError as error:
            raise RuntimeErrorBase(f"cannot open VM disk: {error}") from error
        if not disk.is_file() or disk.stat().st_size < 1024 * 1024:
            raise RuntimeErrorBase("VM disk must be a regular image of at least 1 MiB")
        suffix = disk.suffix.lower()
        if suffix not in {".qcow2", ".img", ".raw"}:
            raise RuntimeErrorBase("VM disk format must use .qcow2, .img or .raw")
        digest = _hash_file(disk, 512 * 1024 * 1024 * 1024)[1]
        record = {
            "schema": _VM_SCHEMA,
            "name": name,
            "disk_path": str(disk),
            "disk_format": "qcow2" if suffix == ".qcow2" else "raw",
            "disk_size_bytes": disk.stat().st_size,
            "disk_sha256": digest,
            "memory_mb": memory_mb,
            "cpus": cpus,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        self._write_json(self.vms / f"{name}.json", record)
        return _public_vm(record)

    def get_vm(self, name: str) -> dict[str, Any]:
        if not isinstance(name, str) or not _VM_NAME.fullmatch(name):
            raise RuntimeErrorBase("invalid VM name")
        manifest_path = self.vms / f"{name}.json"
        if manifest_path.is_symlink():
            raise RuntimeErrorBase("VM manifest must not be a symbolic link")
        try:
            record = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeErrorBase(f"cannot read VM manifest: {error}") from error
        fields = {
            "schema", "name", "disk_path", "disk_format", "disk_size_bytes",
            "disk_sha256", "memory_mb", "cpus", "registered_at",
        }
        if not isinstance(record, dict) or set(record) != fields or record["schema"] != _VM_SCHEMA:
            raise RuntimeErrorBase("VM manifest is invalid")
        disk = Path(record["disk_path"])
        if disk.is_symlink() or not disk.is_file():
            raise RuntimeErrorBase("registered VM disk is missing or unsafe")
        size, digest = _hash_file(disk, 512 * 1024 * 1024 * 1024)
        if size != record["disk_size_bytes"] or digest != record["disk_sha256"]:
            raise RuntimeErrorBase("registered VM disk failed integrity verification")
        return record

    def list_vms(self) -> list[dict[str, Any]]:
        result = []
        for manifest in sorted(self.vms.glob("*.json")):
            try:
                record = self.get_vm(manifest.stem)
                result.append(_public_vm(record))
            except (OSError, ValueError, RuntimeErrorBase):
                result.append({"name": manifest.stem, "status": "invalid"})
        return result

    @staticmethod
    def _write_json(path: Path, value: dict[str, Any]) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        try:
            with temporary.open("x", encoding="utf-8") as stream:
                json.dump(value, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            try:
                temporary.chmod(0o600)
            except OSError:
                pass
            os.replace(temporary, path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise


class RuntimeManager:
    """Detect host runtimes and create processes through argv-based OS APIs."""

    def __init__(self, store: AppStore | None = None):
        self.store = store or AppStore()
        self.processes: dict[str, dict[str, Any]] = {}

    def detect_runtimes(self) -> list[dict[str, Any]]:
        host_windows = os.name == "nt"
        linux = platform.system() == "Linux"
        bwrap = shutil.which("bwrap") if linux else None
        results = [
            {
                "id": "native-pe",
                "name": "Windows native PE",
                "available": host_windows,
                "kind": "windows-pe",
                "description": "Создание процесса .exe напрямую через Windows CreateProcess API.",
                "isolation": "host-user-token" if host_windows else "unavailable",
                "network_isolation": False,
                "graphics": "DirectX/OpenGL/Vulkan через драйверы Windows",
                "requires_unisolated_approval": True,
            }
        ]

        if not host_windows:
            wine = _find_program(("wine64", "wine", "wine-stable"))
            results.append({
                "id": "wine",
                "name": "Wine Windows API",
                "available": wine is not None,
                "executable": str(wine) if wine else None,
                "kind": "windows-pe",
                "description": "Win32/NT API compatibility runtime; CPU instructions run on the host architecture.",
                "isolation": "bubblewrap" if bwrap else "none",
                "network_isolation": bool(bwrap),
                "graphics": "DXVK can translate Direct3D 9/10/11 to Vulkan when separately installed; otherwise Wine graphics backend is used.",
                "requires_unisolated_approval": not bool(bwrap),
            })

        dosbox = _find_program(("dosbox-x", "dosbox", "dosbox-staging"))
        results.append({
            "id": "dosbox",
            "name": "DOSBox / DOSBox-X",
            "available": dosbox is not None,
            "executable": str(dosbox) if dosbox else None,
            "kind": "dos",
            "description": "Runs DOS MZ/COM applications inside a PC/DOS emulator.",
            "isolation": "bubblewrap" if bwrap else "emulator-mount-only",
            "network_isolation": bool(bwrap),
            "graphics": "DOSBox graphics emulation; not a modern DirectX runtime.",
            "requires_unisolated_approval": not bool(bwrap),
        })

        qemu = _find_program(("qemu-system-x86_64", "qemu-system-x86_64.exe"))
        results.append({
            "id": "qemu-x86_64",
            "name": "QEMU x86_64 virtual machine",
            "available": qemu is not None,
            "executable": str(qemu) if qemu else None,
            "kind": "virtual-machine",
            "description": "Boots a registered guest disk image. It does not directly execute a host .exe file.",
            "isolation": "guest-machine",
            "network_isolation": True,
            "graphics": "Virtual display by default; GPU passthrough and gaming acceleration are not configured.",
            "requires_unisolated_approval": True,
        })

        return results

    def capabilities(self) -> dict[str, Any]:
        runtimes = self.detect_runtimes()
        vulkan_library = ctypes.util.find_library("vulkan")
        vulkaninfo = _find_program(("vulkaninfo",))
        vulkan_device = False
        if vulkaninfo:
            try:
                result = subprocess.run(
                    [str(vulkaninfo), "--summary"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=4,
                    check=False,
                    shell=False,
                )
                vulkan_device = result.returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                vulkan_device = False
        return {
            "protocol": "duckos.runtime.v1",
            "host": {
                "os": platform.system(),
                "release": platform.release(),
                "architecture": platform.machine(),
                "python": platform.python_version(),
            },
            "runtimes": runtimes,
            "features": {
                "process_creation": True,
                "managed_import_store": True,
                "executable_integrity_check": True,
                "bubblewrap": any(item["isolation"] == "bubblewrap" for item in runtimes),
                "vulkan_loader": bool(vulkan_library),
                "vulkan_device": vulkan_device,
                "dxvk_installation": "user-supplied-archive-with-expected-sha256",
                "native_duckos_kernel_pe_loader": False,
                "native_duckos_syscall_abi": False,
            },
            "limits": {
                "direct_pe": "Supported on Windows host; on POSIX requires Wine.",
                "dos": "Requires DOSBox/DOSBox-X installed on the host.",
                "windows_vm": "Requires QEMU and a separately installed, licensed guest OS.",
                "d3d12": "DXVK does not implement Direct3D 12; a separate vkd3d-proton integration is required.",
            },
        }

    def import_app(
        self,
        source: str | Path,
        *,
        entrypoint: str | None = None,
        display_name: str | None = None,
    ) -> dict[str, Any]:
        return _public_app(self.store.import_source(
            source, entrypoint=entrypoint, display_name=display_name
        ))

    def launch_app(
        self,
        app_id: str,
        *,
        runtime_id: str = "auto",
        arguments: list[str] | None = None,
        approved: bool = False,
        allow_unisolated: bool = False,
        allow_network: bool = False,
    ) -> dict[str, Any]:
        if not approved:
            raise RuntimePermissionError("launch requires an explicit user approval")
        args = _validate_arguments(arguments or [])
        manifest = self.store.get_app(app_id)
        app_root, entrypoint, app_data = self.store.app_paths(app_id)
        info = manifest["executable"]
        adapter = self._select_runtime(info, runtime_id)
        policy = self._runtime_policy(adapter)
        if policy["requires_unisolated_approval"] and not allow_unisolated:
            raise RuntimePermissionError(
                "the selected host runtime cannot enforce the requested process sandbox; "
                "explicitly approve an unisolated host launch to continue"
            )

        if adapter["id"] == "native-pe":
            command = [str(entrypoint), *args]
            environment = os.environ.copy()
            working_directory = app_root
            isolation = "host-user-token; no DuckOS sandbox"
            graphics = "Windows host graphics drivers"
        elif adapter["id"] == "wine":
            command, environment, working_directory, isolation, graphics = self._wine_command(
                app_id, app_root, entrypoint, app_data, args, allow_network, allow_unisolated
            )
        elif adapter["id"] == "dosbox":
            if args:
                raise RuntimeErrorBase("DOSBox argument forwarding is not enabled for this launch profile")
            command, environment, working_directory, isolation, graphics = self._dosbox_command(
                app_root, entrypoint, app_data, allow_network, allow_unisolated
            )
        else:
            raise RuntimeUnavailable("selected runtime cannot launch this executable format")

        process_id = uuid.uuid4().hex
        log_path = app_data / f"process-{process_id}.log"
        flags = 0
        if os.name == "nt":
            flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        else:
            flags = 0
        try:
            with log_path.open("ab") as log:
                process = subprocess.Popen(
                    command,
                    cwd=working_directory,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    shell=False,
                    close_fds=True,
                    start_new_session=(os.name != "nt"),
                    creationflags=flags,
                )
        except OSError as error:
            raise RuntimeErrorBase(f"host process creation failed: {error}") from error

        self.processes[process_id] = {
            "process": process,
            "app_id": app_id,
            "app_name": manifest["name"],
            "runtime_id": adapter["id"],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "log_path": str(log_path),
            "isolation": isolation,
        }
        return {
            "process_id": process_id,
            "host_pid": process.pid,
            "app_id": app_id,
            "app_name": manifest["name"],
            "runtime_id": adapter["id"],
            "state": "running",
            "isolation": isolation,
            "network_policy": "allowed by user" if allow_network else (
                "blocked by network namespace" if "network namespace" in isolation else "host policy; not enforced"
            ),
            "graphics_backend": graphics,
            "log": str(log_path),
        }

    def _select_runtime(self, info: dict[str, Any], runtime_id: str) -> dict[str, Any]:
        available = {item["id"]: item for item in self.detect_runtimes() if item["available"]}
        if runtime_id == "auto":
            if info["format"] == "windows-pe":
                target = "native-pe" if os.name == "nt" else "wine"
            elif info["format"] in {"dos-mz", "dos-com", "dos-legacy"}:
                target = "dosbox"
            else:
                raise RuntimeUnavailable("this executable format is not supported by the Windows/DOS launch adapters")
        else:
            target = runtime_id
        adapter = available.get(target)
        if adapter is None:
            if target == "native-pe":
                raise RuntimeUnavailable("native PE launch is available only on a Windows host")
            if target == "wine":
                raise RuntimeUnavailable("Wine was not found on this host; install Wine using the host package manager")
            if target == "dosbox":
                raise RuntimeUnavailable("DOSBox/DOSBox-X was not found on this host")
            raise RuntimeUnavailable(f"runtime is unavailable: {target}")
        if adapter["kind"] == "windows-pe" and info["format"] != "windows-pe":
            raise RuntimeUnavailable("the selected runtime accepts Windows PE images only")
        if adapter["kind"] == "dos" and info["format"] not in {"dos-mz", "dos-com", "dos-legacy"}:
            raise RuntimeUnavailable("DOSBox accepts DOS MZ/COM applications, not modern Windows PE files")
        if info.get("is_dll"):
            raise RuntimeUnavailable("DLL libraries cannot be launched as an application")
        return adapter

    def _runtime_policy(self, adapter: dict[str, Any]) -> dict[str, Any]:
        return {
            "requires_unisolated_approval": adapter["requires_unisolated_approval"],
            "isolation": adapter["isolation"],
        }

    def _wine_command(
        self,
        app_id: str,
        app_root: Path,
        entrypoint: Path,
        app_data: Path,
        arguments: list[str],
        allow_network: bool,
        allow_unisolated: bool,
    ) -> tuple[list[str], dict[str, str], Path, str, str]:
        adapter = next(item for item in self.detect_runtimes() if item["id"] == "wine")
        wine = adapter.get("executable")
        if not wine:
            raise RuntimeUnavailable("Wine is not installed")
        prefix = self.store.prefixes / app_id
        _make_private_directory(prefix)
        environment = _runtime_environment(app_data, prefix)
        dxvk = self._dxvk_manifest(app_id, prefix, require_vulkan=True)
        command = [wine, str(entrypoint)]
        if dxvk:
            environment["WINEDLLOVERRIDES"] = ";".join(
                f"{name[:-4]}=native,b" for name in _DXVK_DLLS
            )
            environment["DXVK_STATE_CACHE_PATH"] = str(app_data / "dxvk-cache")
            _make_private_directory(app_data / "dxvk-cache")
            graphics = "DXVK: Direct3D 9/10/11 → Vulkan"
        else:
            graphics = "Wine graphics backend (DXVK not installed for this prefix)"

        sandbox = shutil.which("bwrap") if platform.system() == "Linux" else None
        if sandbox:
            wrapped = self._bubblewrap(
                [wine, str(entrypoint), *arguments],
                app_root=app_root,
                app_data=app_data,
                prefix=prefix,
                environment=environment,
                allow_network=allow_network,
            )
            return wrapped, environment, app_root, "bubblewrap filesystem sandbox" + (
                "; host network enabled by approval" if allow_network else "; network namespace isolated"
            ), graphics
        if not allow_unisolated:
            raise RuntimePermissionError("Wine sandbox is unavailable; install bubblewrap or explicitly approve an unisolated launch")
        return [wine, str(entrypoint), *arguments], environment, app_root, "unisolated host process; explicitly approved", graphics

    def _dosbox_command(
        self,
        app_root: Path,
        entrypoint: Path,
        app_data: Path,
        allow_network: bool,
        allow_unisolated: bool,
    ) -> tuple[list[str], dict[str, str], Path, str, str]:
        adapter = next(item for item in self.detect_runtimes() if item["id"] == "dosbox")
        executable = adapter.get("executable")
        if not executable:
            raise RuntimeUnavailable("DOSBox is not installed")
        if any(char in str(app_root) for char in ('"', "\n", "\r")):
            raise RuntimeErrorBase("DOSBox configuration cannot safely represent this application path")
        relative = entrypoint.relative_to(app_root).as_posix()
        if any(char in relative for char in ('"', "\n", "\r", ";")):
            raise RuntimeErrorBase("DOS executable path contains unsupported DOSBox configuration characters")
        game_path = relative.replace("/", "\\")
        config_path = app_data / "dosbox.conf"
        config = (
            "[sdl]\nfullscreen=false\n"
            "[dosbox]\nmemsize=16\n"
            "[cpu]\ncore=auto\ncycles=auto\n"
            "[autoexec]\n@echo off\n"
            f'mount c "{app_root}"\n'
            "c:\n"
            "cd \\\n"
            f'"{game_path}"\n'
            "exit\n"
        )
        config_path.write_text(config, encoding="utf-8")
        try:
            config_path.chmod(0o600)
        except OSError:
            pass
        environment = _runtime_environment(app_data, None)
        command = [executable, "-conf", str(config_path)]
        sandbox = shutil.which("bwrap") if platform.system() == "Linux" else None
        if sandbox:
            return self._bubblewrap(
                command,
                app_root=app_root,
                app_data=app_data,
                prefix=None,
                environment=environment,
                allow_network=allow_network,
            ), environment, app_root, "bubblewrap filesystem sandbox" + (
                "; host network enabled by approval" if allow_network else "; network namespace isolated"
            ), "DOSBox emulated VGA/SVGA and Sound Blaster"
        if not allow_unisolated:
            raise RuntimePermissionError("DOSBox sandbox is unavailable; install bubblewrap or explicitly approve an unisolated launch")
        return command, environment, app_root, "emulator-mounted directory; host sandbox unavailable", "DOSBox emulated VGA/SVGA and Sound Blaster"

    @staticmethod
    def _bubblewrap(
        command: list[str],
        *,
        app_root: Path,
        app_data: Path,
        prefix: Path | None,
        environment: dict[str, str],
        allow_network: bool,
    ) -> list[str]:
        bwrap = shutil.which("bwrap")
        if not bwrap:
            raise RuntimeUnavailable("bubblewrap is not installed")
        wrapped = [
            bwrap, "--die-with-parent", "--new-session",
            "--ro-bind", "/", "/",
            "--dev", "/dev",
            "--proc", "/proc",
            "--tmpfs", "/tmp",
            "--bind", str(app_root), str(app_root),
            "--bind", str(app_data), str(app_data),
        ]
        if prefix is not None:
            wrapped.extend(["--bind", str(prefix), str(prefix)])
        for device in (Path("/dev/dri"), Path("/dev/snd")):
            if device.exists():
                wrapped.extend(["--dir", str(device), "--dev-bind", str(device), str(device)])
        if not allow_network:
            wrapped.append("--unshare-net")
        for key, value in sorted(environment.items()):
            wrapped.extend(["--setenv", key, value])
        wrapped.extend(["--chdir", str(app_root), "--", *command])
        return wrapped

    def install_dxvk(
        self,
        app_id: str,
        archive_path: str | Path,
        expected_sha256: str,
    ) -> dict[str, Any]:
        if os.name == "nt":
            raise RuntimeUnavailable("DXVK is a Wine runtime component; Windows native PE launch already uses the Windows graphics stack")
        wine_adapter = next((item for item in self.detect_runtimes() if item["id"] == "wine"), None)
        if not wine_adapter or not wine_adapter["available"]:
            raise RuntimeUnavailable("install Wine before installing DXVK")
        if not isinstance(expected_sha256, str) or not _SHA256.fullmatch(expected_sha256):
            raise RuntimeErrorBase("expected SHA-256 must be 64 lowercase hexadecimal characters")
        archive = Path(archive_path).expanduser()
        if archive.is_symlink() or not archive.is_file():
            raise RuntimeErrorBase("DXVK archive must be a regular, non-symlink file")
        archive_hash = _hash_file(archive, 512 * 1024 * 1024)[1]
        if archive_hash != expected_sha256:
            raise RuntimeErrorBase("DXVK archive SHA-256 does not match the supplied expected digest")

        self.store.get_app(app_id)
        app_root, _, app_data = self.store.app_paths(app_id)
        prefix = self.store.prefixes / app_id
        _make_private_directory(prefix)
        environment = _runtime_environment(app_data, prefix)
        wine = wine_adapter["executable"]
        wineboot = _find_program(("wineboot", "wineboot64"))
        if not wineboot:
            raise RuntimeUnavailable("wineboot was not found beside the installed Wine runtime")
        if not (prefix / "system.reg").exists():
            try:
                subprocess.run(
                    [str(wineboot), "-u"],
                    cwd=app_root,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=180,
                    check=True,
                    shell=False,
                )
            except (OSError, subprocess.SubprocessError) as error:
                raise RuntimeErrorBase(f"Wine prefix initialization failed: {error}") from error

        extracted: dict[str, dict[str, Any]] = {"x64": {}, "x32": {}}
        license_payload: bytes | None = None
        try:
            with tarfile.open(archive, "r:*") as bundle:
                for member in bundle.getmembers():
                    if not member.isfile() or member.issym() or member.islnk():
                        continue
                    parts = PurePosixPath(member.name).parts
                    if member.name.startswith("/") or ".." in parts:
                        raise RuntimeErrorBase("DXVK archive contains an unsafe path")
                    if member.size > 64 * 1024 * 1024:
                        raise RuntimeErrorBase("DXVK archive member exceeds 64 MiB")
                    if len(parts) >= 2 and parts[-2] in {"x64", "x32"} and parts[-1].lower() in _DXVK_DLLS:
                        architecture = parts[-2]
                        dll_name = parts[-1].lower()
                        if dll_name in extracted[architecture]:
                            raise RuntimeErrorBase(f"duplicate DXVK library: {dll_name}")
                        stream = bundle.extractfile(member)
                        if stream is None:
                            raise RuntimeErrorBase(f"cannot read DXVK library: {dll_name}")
                        payload = stream.read(64 * 1024 * 1024 + 1)
                        if len(payload) != member.size:
                            raise RuntimeErrorBase(f"DXVK library size mismatch: {dll_name}")
                        extracted[architecture][dll_name] = {
                            "content": payload,
                            "sha256": hashlib.sha256(payload).hexdigest(),
                            "size_bytes": len(payload),
                        }
                    elif parts and parts[-1].lower() in {"license", "license.txt", "copying"}:
                        stream = bundle.extractfile(member)
                        if stream:
                            license_payload = stream.read(1024 * 1024)
        except (tarfile.TarError, OSError) as error:
            raise RuntimeErrorBase(f"cannot read DXVK archive: {error}") from error

        for architecture in ("x64", "x32"):
            missing = set(_DXVK_DLLS) - extracted[architecture].keys()
            if missing:
                raise RuntimeErrorBase(f"DXVK archive is missing {architecture} libraries: {sorted(missing)}")

        manifest_path = app_data / "dxvk-install.json"
        if manifest_path.exists():
            previous = self._dxvk_manifest(app_id, prefix, require_vulkan=False)
            if not previous:
                raise RuntimeErrorBase("existing DXVK installation failed integrity verification")
        else:
            for folder_name in ("system32", "syswow64"):
                folder = prefix / "drive_c" / "windows" / folder_name
                if folder.exists() and any((folder / name).exists() for name in _DXVK_DLLS):
                    raise RuntimeErrorBase("prefix contains unmanaged Direct3D DLLs; refusing to overwrite them")

        install_records = []
        targets = (
            ("x64", prefix / "drive_c" / "windows" / "system32"),
            ("x32", prefix / "drive_c" / "windows" / "syswow64"),
        )
        for architecture, folder in targets:
            _make_private_directory(folder)
            for name in _DXVK_DLLS:
                item = extracted[architecture][name]
                output = folder / name
                temporary = folder / (name + ".duckos-new")
                temporary.write_bytes(item["content"])
                try:
                    temporary.chmod(0o600)
                except OSError:
                    pass
                os.replace(temporary, output)
                install_records.append({
                    "architecture": architecture,
                    "path": str(output.relative_to(prefix).as_posix()),
                    "sha256": item["sha256"],
                    "size_bytes": item["size_bytes"],
                })

        if license_payload:
            license_path = app_data / "licenses" / "DXVK-LICENSE.txt"
            _make_private_directory(license_path.parent)
            license_path.write_bytes(license_payload)

        record = {
            "schema": "duckos.dxvk-install.v1",
            "app_id": app_id,
            "archive_sha256": archive_hash,
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "files": install_records,
        }
        AppStore._write_json(manifest_path, record)
        return {
            "installed": True,
            "app_id": app_id,
            "archive_sha256": archive_hash,
            "libraries_installed": len(install_records),
            "graphics_backend": "DXVK Direct3D 9/10/11 to Vulkan",
            "license_saved": bool(license_payload),
            "note": "DXVK does not implement Direct3D 12; a separate vkd3d-proton adapter is required.",
        }

    def _dxvk_manifest(self, app_id: str, prefix: Path, *, require_vulkan: bool) -> dict[str, Any] | None:
        app_data = self.store.data / app_id
        path = app_data / "dxvk-install.json"
        if not path.exists():
            return None
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeErrorBase(f"DXVK installation manifest is invalid: {error}") from error
        if not isinstance(record, dict) or record.get("schema") != "duckos.dxvk-install.v1" or record.get("app_id") != app_id:
            raise RuntimeErrorBase("DXVK installation manifest identity is invalid")
        files = record.get("files")
        if not isinstance(files, list) or len(files) != len(_DXVK_DLLS) * 2:
            raise RuntimeErrorBase("DXVK installation manifest is incomplete")
        for item in files:
            relative = _validate_relative_path(item.get("path"))
            target = prefix.joinpath(*PurePosixPath(relative).parts)
            if target.is_symlink():
                raise RuntimeErrorBase("DXVK library path is a symbolic link")
            size, digest = _hash_file(target, 64 * 1024 * 1024)
            if size != item.get("size_bytes") or digest != item.get("sha256"):
                raise RuntimeErrorBase("DXVK library failed integrity verification")
        if require_vulkan and not ctypes.util.find_library("vulkan"):
            raise RuntimeUnavailable("DXVK is installed but this host has no Vulkan loader")
        return record

    def launch_vm(
        self,
        name: str,
        *,
        approved: bool = False,
        allow_network: bool = False,
        persistent: bool = False,
    ) -> dict[str, Any]:
        if not approved:
            raise RuntimePermissionError("VM launch requires explicit user approval")
        vm = self.store.get_vm(name)
        adapter = next(item for item in self.detect_runtimes() if item["id"] == "qemu-x86_64")
        executable = adapter.get("executable")
        if not executable:
            raise RuntimeUnavailable("QEMU system x86_64 was not found")
        if persistent and not approved:
            raise RuntimePermissionError("persistent guest writes require a separate explicit approval")
        disk_driver = vm["disk_format"]
        file_block = {"driver": "file", "filename": vm["disk_path"], "node-name": "duckos-file"}
        image_block = {
            "driver": "qcow2" if disk_driver == "qcow2" else "raw",
            "file": "duckos-file",
            "node-name": "duckos-disk",
        }
        command = [
            executable,
            "-machine", "q35,accel=tcg",
            "-m", str(vm["memory_mb"]),
            "-smp", str(vm["cpus"]),
            "-blockdev", json.dumps(file_block, separators=(",", ":")),
            "-blockdev", json.dumps(image_block, separators=(",", ":")),
            "-device", "virtio-blk-pci,drive=duckos-disk",
            "-vga", "std",
            "-display", "default",
            "-boot", "menu=on",
        ]
        if persistent:
            command.extend(["-no-snapshot"])
        else:
            command.append("-snapshot")
        if allow_network:
            command.extend(["-netdev", "user,id=duckos-net", "-device", "virtio-net-pci,netdev=duckos-net"])
        else:
            command.append("-nic")
            command.append("none")

        vm_data = self.store.root / "vm-state" / name
        _make_private_directory(vm_data)
        log_path = vm_data / "qemu.log"
        process_id = uuid.uuid4().hex
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
        try:
            with log_path.open("ab") as log:
                process = subprocess.Popen(
                    command,
                    cwd=vm_data,
                    env=os.environ.copy(),
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    shell=False,
                    close_fds=True,
                    start_new_session=(os.name != "nt"),
                    creationflags=flags,
                )
        except OSError as error:
            raise RuntimeErrorBase(f"QEMU process creation failed: {error}") from error
        self.processes[process_id] = {
            "process": process,
            "app_id": None,
            "app_name": "VM " + name,
            "runtime_id": "qemu-x86_64",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "log_path": str(log_path),
            "isolation": "QEMU guest; host process sandbox not provided",
        }
        return {
            "process_id": process_id,
            "host_pid": process.pid,
            "vm_name": name,
            "runtime_id": "qemu-x86_64",
            "state": "running",
            "network_policy": "user-mode NAT" if allow_network else "network device disabled",
            "disk_policy": "persistent writes approved" if persistent else "temporary snapshot; original disk unchanged",
            "graphics_backend": "QEMU virtual VGA; no GPU passthrough configured",
            "log": str(log_path),
        }

    def list_processes(self) -> list[dict[str, Any]]:
        result = []
        for process_id, record in list(self.processes.items()):
            process = record["process"]
            code = process.poll()
            result.append({
                "process_id": process_id,
                "host_pid": process.pid,
                "app_id": record["app_id"],
                "name": record["app_name"],
                "runtime_id": record["runtime_id"],
                "state": "running" if code is None else "exited",
                "exit_code": code,
                "started_at": record["started_at"],
                "isolation": record["isolation"],
                "log": record["log_path"],
            })
        return result

    def terminate_process(self, process_id: str) -> dict[str, Any]:
        record = self.processes.get(process_id)
        if not record:
            raise RuntimeErrorBase("process is not managed by this service instance")
        process = record["process"]
        if process.poll() is not None:
            return {"process_id": process_id, "state": "exited", "exit_code": process.returncode}
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        return {"process_id": process_id, "state": "terminated", "exit_code": process.returncode}


def default_state_dir() -> Path:
    override = os.environ.get("DUCKOS_HOME")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "DuckOS"
    base = os.environ.get("XDG_DATA_HOME")
    return (Path(base).expanduser() if base else Path.home() / ".local" / "share") / "duckos"


def _make_private_directory(path: Path) -> None:
    if path.exists() and path.is_symlink():
        raise RuntimeErrorBase(f"managed path must not be a symbolic link: {path}")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not path.is_dir():
        raise RuntimeErrorBase(f"managed path is not a directory: {path}")
    try:
        path.chmod(0o700)
    except OSError:
        pass


def _safe_filename(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 240:
        raise AppStoreError("filename must contain 1..240 characters")
    if value in {".", ".."} or "/" in value or "\\" in value or any(ord(char) < 32 for char in value):
        raise AppStoreError("filename contains path separators or control characters")
    return value


def _safe_display_name(value: str) -> str:
    text = " ".join(str(value).split())
    if not text or len(text) > 120 or any(ord(char) < 32 for char in text):
        raise AppStoreError("application display name is invalid")
    return text


def _validate_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise AppStoreError("package path must be non-empty text of at most 1024 characters")
    if "\\" in value or value.startswith("/") or ":" in value or any(ord(char) < 32 for char in value):
        raise AppStoreError(f"unsafe package path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts) or str(path) != value:
        raise AppStoreError(f"non-canonical package path: {value!r}")
    return value


def _hash_file(path: Path, limit: int) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > limit:
                    raise RuntimeErrorBase(f"{path.name} exceeds the {limit} byte limit")
                digest.update(chunk)
    except OSError as error:
        raise RuntimeErrorBase(f"cannot hash {path}: {error}") from error
    return size, digest.hexdigest()


def _tree_hash(files: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for item in sorted(files, key=lambda record: record["path"]):
        digest.update(item["path"].encode("utf-8"))
        digest.update(b"\x00")
        digest.update(str(item["size_bytes"]).encode("ascii"))
        digest.update(b"\x00")
        digest.update(item["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _public_app(manifest: dict[str, Any]) -> dict[str, Any]:
    executable = manifest["executable"]
    return {
        "id": manifest["id"],
        "name": manifest["name"],
        "entrypoint": manifest["entrypoint"],
        "format": executable["format"],
        "architecture": executable["architecture"],
        "bits": executable["bits"],
        "size_bytes": executable["size_bytes"],
        "trust_state": manifest["trust_state"],
        "signature_state": manifest["signature_state"],
        "file_count": len(manifest["files"]),
    }


def _public_vm(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": record["name"],
        "disk_format": record["disk_format"],
        "disk_size_bytes": record["disk_size_bytes"],
        "memory_mb": record["memory_mb"],
        "cpus": record["cpus"],
        "integrity": "sha256-verified-on-launch",
    }


def _find_program(names: tuple[str, ...]) -> Path | None:
    for name in names:
        located = shutil.which(name)
        if located:
            path = Path(located).resolve()
            if path.is_file() and os.access(path, os.X_OK):
                return path
    return None


def _runtime_environment(app_data: Path, prefix: Path | None) -> dict[str, str]:
    allowed = {
        "PATH", "USER", "LOGNAME", "LANG", "LC_ALL", "DISPLAY", "WAYLAND_DISPLAY",
        "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS", "PULSE_SERVER", "PIPEWIRE_REMOTE",
        "XAUTHORITY", "XDG_CURRENT_DESKTOP", "XDG_SESSION_TYPE", "QT_QPA_PLATFORM",
        "SDL_VIDEODRIVER", "WINELOADER", "WINESERVER",
    }
    environment = {key: value for key, value in os.environ.items() if key in allowed}
    home = app_data / "home"
    _make_private_directory(home)
    _make_private_directory(app_data / "cache")
    environment.update({
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_CACHE_HOME": str(app_data / "cache"),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
        "WINEDEBUG": "-all",
    })
    if prefix is not None:
        environment["WINEPREFIX"] = str(prefix)
    return environment


def _validate_arguments(arguments: list[str]) -> list[str]:
    if not isinstance(arguments, list) or len(arguments) > MAX_ARGUMENTS:
        raise RuntimeErrorBase(f"application arguments must be a list with at most {MAX_ARGUMENTS} items")
    result = []
    for item in arguments:
        if not isinstance(item, str) or len(item) > MAX_ARGUMENT_LENGTH or "\x00" in item:
            raise RuntimeErrorBase("each application argument must be text of at most 2048 characters without NUL")
        result.append(item)
    return result
