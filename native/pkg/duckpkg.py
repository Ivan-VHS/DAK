#!/usr/bin/env python3
"""Small transactional package store for DuckOS; deliberately has no install hooks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath


_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._+-]{0,63}$")
_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MAX_MANIFEST_BYTES = 1024 * 1024
_MAX_PACKAGE_FILES = 10000
_MAX_PACKAGE_BYTES = 512 * 1024 * 1024
_MAX_FILE_BYTES = 256 * 1024 * 1024


class PackageError(Exception):
    """An invalid package or an unsafe package operation."""


def safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    raw_parts = value.split("/")
    if (
        not value
        or "\\" in value
        or "\0" in value
        or path.is_absolute()
        or any(part in ("", ".", "..") for part in raw_parts)
    ):
        raise PackageError(f"unsafe package path: {value!r}")
    return path


def read_registry(path: Path) -> dict:
    if not path.exists():
        return {"packages": []}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PackageError(f"cannot read package registry: {error}") from error

    if not isinstance(data, dict) or not isinstance(data.get("packages"), list):
        raise PackageError("package registry has an invalid format")
    return data


def write_registry(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(data, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_manifest(archive: tarfile.TarFile) -> dict:
    try:
        member = archive.getmember("manifest.json")
    except KeyError as error:
        raise PackageError("archive is missing manifest.json") from error

    if not member.isfile() or member.size > _MAX_MANIFEST_BYTES:
        raise PackageError("manifest.json must be a regular file under 1 MiB")

    stream = archive.extractfile(member)
    if stream is None:
        raise PackageError("cannot read package manifest")

    try:
        manifest = json.loads(stream.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PackageError(f"invalid package manifest: {error}") from error

    if not isinstance(manifest, dict):
        raise PackageError("package manifest must be a JSON object")

    name = manifest.get("name")
    version = manifest.get("version")
    files = manifest.get("files")

    if not isinstance(name, str) or not _NAME_RE.fullmatch(name):
        raise PackageError("manifest name must be a lowercase package identifier")
    if not isinstance(version, str) or not _VERSION_RE.fullmatch(version):
        raise PackageError("manifest version is invalid")
    if not isinstance(files, dict) or not files:
        raise PackageError("manifest files must be a non-empty path-to-SHA256 object")

    cleaned: dict[str, str] = {}
    for raw_path, digest in files.items():
        if not isinstance(raw_path, str) or not isinstance(digest, str):
            raise PackageError("manifest file entries must be strings")
        safe_path = safe_relative_path(raw_path).as_posix()
        if safe_path in cleaned or not _SHA256_RE.fullmatch(digest):
            raise PackageError(f"invalid file entry or SHA-256 digest: {raw_path!r}")
        cleaned[safe_path] = digest

    manifest["files"] = cleaned
    return manifest


def _copy_verified_member(
    archive: tarfile.TarFile,
    member: tarfile.TarInfo,
    relative_path: str,
    expected_digest: str,
    destination: Path,
) -> None:
    if not member.isfile():
        raise PackageError(f"package payload must contain regular files only: {member.name}")

    source = archive.extractfile(member)
    if source is None:
        raise PackageError(f"cannot read package payload: {member.name}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()

    with source, destination.open("xb") as target:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            target.write(chunk)
        target.flush()
        os.fsync(target.fileno())

    if digest.hexdigest() != expected_digest:
        destination.unlink(missing_ok=True)
        raise PackageError(f"SHA-256 mismatch for {relative_path}")

    destination.chmod(0o755 if member.mode & 0o111 else 0o644)


def install_package(archive_path: Path, root: Path) -> Path:
    root = root.resolve()
    store = root / "opt" / "duckos" / "packages"
    staging_parent = store / ".staging"
    registry_path = root / "var" / "lib" / "duckpkg" / "installed.json"

    store.mkdir(parents=True, exist_ok=True)
    staging_parent.mkdir(parents=True, exist_ok=True)
    registry = read_registry(registry_path)

    try:
        archive = tarfile.open(archive_path, mode="r:*")
    except (OSError, tarfile.TarError) as error:
        raise PackageError(f"cannot open package archive: {error}") from error

    with archive:
        members = archive.getmembers()
        names: set[str] = set()

        payload_bytes = 0
        for member in members:
            if member.name in names:
                raise PackageError(f"duplicate archive entry: {member.name}")
            names.add(member.name)

            if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                raise PackageError(f"links and special files are not allowed: {member.name}")

            if member.name != "manifest.json":
                if member.name in ("payload", "payload/"):
                    if not member.isdir():
                        raise PackageError("payload root must be a directory")
                elif member.name.startswith("payload/"):
                    relative = member.name[len("payload/"):]
                    if member.isdir() and relative.endswith("/"):
                        relative = relative[:-1]
                    safe_relative_path(relative)
                else:
                    raise PackageError(f"unexpected archive entry: {member.name}")

                if member.isfile():
                    if member.size < 0 or member.size > _MAX_FILE_BYTES:
                        raise PackageError(f"payload file is too large: {member.name}")
                    payload_bytes += member.size
                    if payload_bytes > _MAX_PACKAGE_BYTES:
                        raise PackageError("package exceeds the 512 MiB unpacked size limit")

        manifest = _read_manifest(archive)
        expected = manifest["files"]
        if len(expected) > _MAX_PACKAGE_FILES:
            raise PackageError(f"package exceeds the {_MAX_PACKAGE_FILES} file limit")

        payload_members: dict[str, tarfile.TarInfo] = {}

        for member in members:
            if not member.name.startswith("payload/") or member.isdir():
                continue
            relative = member.name[len("payload/"):]
            safe_relative_path(relative)
            if relative in payload_members:
                raise PackageError(f"duplicate payload path: {relative}")
            payload_members[relative] = member

        if set(payload_members) != set(expected):
            missing = sorted(set(expected) - set(payload_members))
            extra = sorted(set(payload_members) - set(expected))
            raise PackageError(f"archive/manifest file list differs (missing={missing}, extra={extra})")

        package_name = manifest["name"]
        version = manifest["version"]
        target = store / package_name / version

        if target.exists():
            raise PackageError(f"{package_name} {version} is already installed")

        with tempfile.TemporaryDirectory(prefix="install-", dir=staging_parent) as temp:
            staged = Path(temp) / "package"
            staged.mkdir()

            for relative, digest in expected.items():
                member = payload_members[relative]
                destination = staged.joinpath(*safe_relative_path(relative).parts)
                _copy_verified_member(archive, member, relative, digest, destination)

            manifest_copy = staged / "manifest.json"
            manifest_copy.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged, target)

        record = {
            "name": package_name,
            "version": version,
            "path": target.relative_to(root).as_posix(),
            "files": expected,
        }
        registry["packages"] = [
            item for item in registry["packages"]
            if not (item.get("name") == package_name and item.get("version") == version)
        ]
        registry["packages"].append(record)

        try:
            write_registry(registry_path, registry)
        except OSError:
            shutil.rmtree(target, ignore_errors=True)
            raise

    return target


def list_packages(root: Path) -> list[dict]:
    registry = read_registry(root.resolve() / "var" / "lib" / "duckpkg" / "installed.json")
    return sorted(registry["packages"], key=lambda item: (item["name"], item["version"]))


def verify_package(root: Path, name: str) -> list[str]:
    root = root.resolve()
    registry_path = root / "var" / "lib" / "duckpkg" / "installed.json"
    registry = read_registry(registry_path)
    records = [item for item in registry["packages"] if item.get("name") == name]

    if not records:
        raise PackageError(f"package is not installed: {name}")

    errors: list[str] = []
    for record in records:
        base = root.joinpath(*safe_relative_path(record["path"]).parts)
        for relative, expected in record.get("files", {}).items():
            file_path = base.joinpath(*safe_relative_path(relative).parts)
            try:
                if not file_path.is_file() or file_path.is_symlink():
                    raise OSError("not a regular file")
                hasher = hashlib.sha256()
                with file_path.open("rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        hasher.update(chunk)
                digest = hasher.hexdigest()
                if digest != expected:
                    raise OSError("digest mismatch")
            except OSError as error:
                errors.append(f"{record['version']}:{relative}: {error}")

    return errors


def remove_package(root: Path, name: str, version: str) -> None:
    if not _NAME_RE.fullmatch(name) or not _VERSION_RE.fullmatch(version):
        raise PackageError("invalid package name or version")

    root = root.resolve()
    registry_path = root / "var" / "lib" / "duckpkg" / "installed.json"
    registry = read_registry(registry_path)
    matches = [
        item for item in registry["packages"]
        if item.get("name") == name and item.get("version") == version
    ]

    if not matches:
        raise PackageError(f"package is not installed: {name} {version}")

    package_path = root / "opt" / "duckos" / "packages" / name / version
    if package_path.is_symlink():
        raise PackageError("refusing to remove a symlinked package directory")
    if package_path.exists():
        resolved = package_path.resolve()
        expected_parent = (root / "opt" / "duckos" / "packages" / name).resolve()
        if resolved.parent != expected_parent:
            raise PackageError("package path escaped the package store")
        shutil.rmtree(package_path)

    registry["packages"] = [
        item for item in registry["packages"]
        if not (item.get("name") == name and item.get("version") == version)
    ]
    write_registry(registry_path, registry)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(os.environ.get("DUCKOS_ROOT", "rootfs")))
    commands = parser.add_subparsers(dest="action", required=True)

    install = commands.add_parser("install", help="verify and install a local .tar package")
    install.add_argument("archive", type=Path)

    commands.add_parser("list", help="list installed packages")

    verify = commands.add_parser("verify", help="verify files of an installed package")
    verify.add_argument("name")

    remove = commands.add_parser("remove", help="remove one installed package version")
    remove.add_argument("name")
    remove.add_argument("version")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    root = args.root

    try:
        if args.action == "install":
            destination = install_package(args.archive, root)
            print(f"installed into {destination}")
        elif args.action == "list":
            packages = list_packages(root)
            if not packages:
                print("no packages installed")
            for package in packages:
                print(f"{package['name']} {package['version']}")
        elif args.action == "verify":
            errors = verify_package(root, args.name)
            if errors:
                for error in errors:
                    print(error, file=sys.stderr)
                return 1
            print(f"{args.name}: verified")
        elif args.action == "remove":
            remove_package(root, args.name, args.version)
            print(f"removed {args.name} {args.version}")
    except (OSError, PackageError, tarfile.TarError) as error:
        print(f"duckpkg: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
