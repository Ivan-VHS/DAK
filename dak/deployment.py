"""DAK release packaging and deployment planning.

Creates deterministic, optionally signed component bundles and safe deployment
plans. It never writes raw disks or claims to execute a firmware boot path.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import tempfile
from typing import Any
from urllib.parse import quote, urlsplit

from .image_layout import plan_image
from .manifest import ManifestError, validate_manifest

RELEASE_SCHEMA = "dak.release.v1"
DEPLOYMENT_SCHEMA = "dak.deployment-plan.v1"
MAX_METADATA_BYTES = 1024 * 1024
MAX_JSON_INTEGER_DIGITS = 1024
MAX_JSON_NESTING_DEPTH = 128
MAX_ARCHIVE_MEMBERS = 256
MAX_ARCHIVE_BYTES = 34 * 1024 * 1024 * 1024
_MIB = 1024 * 1024
_GIB = 1024 * _MIB
_ALIGNMENT = _MIB


class DeploymentError(ValueError):
    """Raised when a release bundle or deployment plan is invalid."""


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DeploymentError(f"JSON contains a duplicate object key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise DeploymentError(f"JSON contains a non-standard numeric constant: {value}")


def _parse_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise DeploymentError("JSON contains a non-finite floating-point value")
    return parsed


def _parse_json_integer(value: str) -> int:
    digits = value[1:] if value.startswith("-") else value
    if len(digits) > MAX_JSON_INTEGER_DIGITS:
        raise DeploymentError(
            f"JSON integer exceeds the {MAX_JSON_INTEGER_DIGITS}-digit limit"
        )
    return int(value)


def _validate_json_nesting(raw: str, label: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    for character in raw:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > MAX_JSON_NESTING_DEPTH:
                raise DeploymentError(
                    f"{label} JSON nesting exceeds the {MAX_JSON_NESTING_DEPTH}-level limit"
                )
        elif character in "]}":
            depth -= 1


def _load_strict_json(raw: bytes | str, label: str) -> Any:
    """Decode bounded release JSON with duplicate-key and finite-number checks."""
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        encoded_size = len(text.encode("utf-8"))
        if encoded_size > MAX_METADATA_BYTES:
            raise DeploymentError(f"{label} exceeds the {MAX_METADATA_BYTES}-byte limit")
        _validate_json_nesting(text, label)
        return json.loads(
            text,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
            parse_float=_parse_json_float,
            parse_int=_parse_json_integer,
        )
    except UnicodeDecodeError as error:
        raise DeploymentError(f"{label} is not valid UTF-8") from error
    except json.JSONDecodeError as error:
        raise DeploymentError(f"{label} is invalid JSON: {error}") from error
    except RecursionError as error:
        raise DeploymentError(f"{label} exceeds the supported JSON nesting depth") from error


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _hash_stream(stream: Any) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    while chunk := stream.read(1024 * 1024):
        size += len(chunk)
        digest.update(chunk)
    return size, digest.hexdigest()


def _safe_path(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise DeploymentError("artifact path must be non-empty relative text")
    if "\\" in value or value.startswith("/") or ":" in value:
        raise DeploymentError(f"unsafe artifact path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value or any(part in {"", ".", ".."} for part in path.parts):
        raise DeploymentError(f"unsafe artifact path: {value!r}")
    if any(ord(char) < 32 for char in value):
        raise DeploymentError("artifact paths must not contain control characters")
    return value


def _openssl(arguments: list[str]) -> None:
    try:
        result = subprocess.run(
            ["openssl", *arguments], check=False, capture_output=True,
            text=True, timeout=30,
        )
    except FileNotFoundError as error:
        raise DeploymentError("OpenSSL is required for signing or signature verification") from error
    except subprocess.TimeoutExpired as error:
        raise DeploymentError("OpenSSL operation timed out") from error
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown OpenSSL error"
        raise DeploymentError(f"OpenSSL operation failed: {detail[:500]}")


def _key_file(value: str | Path, label: str) -> Path:
    path = Path(value).expanduser()
    if path.is_symlink() or not path.is_file():
        raise DeploymentError(f"{label} must be an existing regular file, not a symlink")
    return path.resolve(strict=True)


def _sign(release_file: Path, key: str | Path, signature: Path) -> None:
    private_key = _key_file(key, "private key")
    try:
        details = subprocess.run(
            ["openssl", "pkey", "-in", str(private_key), "-text", "-noout"],
            check=False, capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError as error:
        raise DeploymentError("OpenSSL is required for release signing") from error
    if details.returncode or "ED25519" not in (details.stdout + details.stderr).upper():
        raise DeploymentError("release signing currently requires an Ed25519 private key")
    _openssl([
        "pkeyutl", "-sign", "-rawin", "-inkey", str(private_key),
        "-in", str(release_file), "-out", str(signature),
    ])


def _verify_signature(release_file: Path, signature: Path, key: str | Path) -> None:
    public_key = _key_file(key, "public key")
    try:
        details = subprocess.run(
            ["openssl", "pkey", "-pubin", "-in", str(public_key), "-text", "-noout"],
            check=False, capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError as error:
        raise DeploymentError("OpenSSL is required for signature verification") from error
    if details.returncode or "ED25519" not in (details.stdout + details.stderr).upper():
        raise DeploymentError("release verification currently requires an Ed25519 public key")
    _openssl([
        "pkeyutl", "-verify", "-pubin", "-inkey", str(public_key), "-rawin",
        "-in", str(release_file), "-sigfile", str(signature),
    ])


def _write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def _write_archive(source: Path, destination: Path) -> None:
    temporary: Path | None = None
    try:
        handle = tempfile.NamedTemporaryFile(
            prefix=f".{destination.name}.", suffix=".tmp",
            dir=destination.parent, delete=False,
        )
        temporary = Path(handle.name)
        with handle:
            with gzip.GzipFile(fileobj=handle, mode="wb", filename="", mtime=0, compresslevel=9) as compressed:
                with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                    entries = sorted(source.rglob("*"), key=lambda item: item.relative_to(source.parent).as_posix())
                    for item in entries:
                        name = item.relative_to(source.parent).as_posix()
                        info = tarfile.TarInfo(name + ("/" if item.is_dir() else ""))
                        info.uid = info.gid = info.mtime = 0
                        info.uname = info.gname = ""
                        info.mode = 0o755 if item.is_dir() else 0o644
                        if item.is_dir():
                            info.type = tarfile.DIRTYPE
                            archive.addfile(info)
                        elif item.is_file() and not item.is_symlink():
                            info.size = item.stat().st_size
                            with item.open("rb") as stream:
                                archive.addfile(info, stream)
                        else:
                            raise DeploymentError(f"unsupported file type in release staging: {item}")
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build_release_bundle(
    manifest: dict[str, Any],
    component_root: str | Path,
    output_archive: str | Path,
    *,
    signing_key: str | Path | None = None,
) -> dict[str, Any]:
    """Create a deterministic component bundle; this is not a bootable image."""
    supplied_root = Path(component_root).expanduser()
    if supplied_root.is_symlink():
        raise DeploymentError("component root must not be a symlink")
    try:
        root = supplied_root.resolve(strict=True)
    except OSError as error:
        raise DeploymentError(f"cannot open component root: {error}") from error
    if not root.is_dir():
        raise DeploymentError("component root must be a directory")
    try:
        validation = validate_manifest(manifest, root, verify_files=True)
    except ManifestError as error:
        raise DeploymentError(str(error)) from error

    output = Path(output_archive).expanduser()
    if output.suffixes[-2:] != [".tar", ".gz"] and output.suffix != ".tgz":
        raise DeploymentError("release output must end in .tar.gz or .tgz")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink() or (output.exists() and not output.is_file()):
        raise DeploymentError("release output must be a regular file path, not a symlink or directory")
    resolved_output = output.resolve(strict=False)
    if resolved_output == root or root in resolved_output.parents:
        raise DeploymentError("release archive must be outside the component root")

    clean_manifest = json.loads(_json_bytes(manifest).decode("utf-8"))
    manifest_data = _json_bytes(clean_manifest)
    work = Path(tempfile.mkdtemp(prefix=".dak-release-", dir=output.parent))
    stage = work / "dak-release"
    stage.mkdir()
    try:
        payload_root = stage / "payload"
        for component in validation["components"]:
            relative = _safe_path(component["path"])
            source = root.joinpath(*PurePosixPath(relative).parts)
            target = payload_root.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as reader, target.open("xb") as writer:
                shutil.copyfileobj(reader, writer, length=1024 * 1024)
            with target.open("rb") as copied:
                size, digest = _hash_stream(copied)
            if size != component["size_bytes"] or digest != component["sha256"]:
                raise DeploymentError(f"component changed while packaging: {relative}")

        _write_new(stage / "manifest.json", manifest_data)
        release = {
            "schema": RELEASE_SCHEMA,
            "name": clean_manifest["name"],
            "version": clean_manifest["version"],
            "architecture": clean_manifest["architecture"],
            "kernel_abi": clean_manifest["kernel_abi"],
            "manifest_sha256": hashlib.sha256(manifest_data).hexdigest(),
            "component_count": validation["component_count"],
            "release_kind": "component-bundle",
            "signature_algorithm": "Ed25519" if signing_key is not None else None,
            "artifacts": {
                "component_bundle": True,
                "bootable_iso_created": False,
                "bootable_usb_created": False,
                "cloud_image_converted": False,
                "firmware_boot_verified": False,
                "disk_writes_performed": False,
            },
        }
        _write_new(stage / "release.json", _json_bytes(release))
        if signing_key is not None:
            _sign(stage / "release.json", signing_key, stage / "release.json.sig")

        readme = (
            "DAK release component bundle\n"
            "================================\n\n"
            f"Version: {clean_manifest['version']}\n"
            f"Architecture: {clean_manifest['architecture']}\n\n"
            "This archive contains validated system components and release metadata.\n"
            "It is not an ISO, bootable USB image, or cloud disk image.\n"
            "No firmware boot, raw-disk write, installation, or hardware test was run.\n"
            "A native DAK bootloader, kernel entry point, filesystem image builder,\n"
            "and target-specific verification are still required for those outputs.\n"
        )
        _write_new(stage / "README.txt", readme.encode("utf-8"))

        checksummed = [stage / "manifest.json", stage / "release.json", stage / "README.txt"]
        signature = stage / "release.json.sig"
        if signature.exists():
            checksummed.append(signature)
        checksummed.extend(path for path in sorted(payload_root.rglob("*")) if path.is_file())
        lines = []
        for path in checksummed:
            with path.open("rb") as stream:
                digest = _hash_stream(stream)[1]
            lines.append(f"{digest}  {path.relative_to(stage).as_posix()}")
        _write_new(stage / "SHA256SUMS", ("\n".join(lines) + "\n").encode("utf-8"))
        _write_archive(stage, output)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    with output.open("rb") as stream:
        size, digest = _hash_stream(stream)
    return {
        "schema": "dak.release-build-result.v1",
        "valid": True,
        "archive": str(output.resolve()),
        "archive_size_bytes": size,
        "archive_sha256": digest,
        "component_count": validation["component_count"],
        "signed": signing_key is not None,
        "signature_algorithm": "Ed25519" if signing_key is not None else None,
        "bootable_iso_created": False,
        "bootable_usb_created": False,
        "disk_writes_performed": False,
    }


def verify_release_bundle(
    archive_path: str | Path,
    *,
    public_key: str | Path | None = None,
) -> dict[str, Any]:
    """Verify archive structure, payload hashes and an optional Ed25519 signature."""
    archive_file = Path(archive_path).expanduser()
    if archive_file.is_symlink() or not archive_file.is_file():
        raise DeploymentError("release archive must be an existing regular file, not a symlink")
    files: dict[str, tarfile.TarInfo] = {}
    total_size = 0
    try:
        with tarfile.open(archive_file, mode="r:gz") as archive:
            members = archive.getmembers()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                raise DeploymentError("release archive contains too many entries")
            for member in members:
                name = member.name.rstrip("/")
                path = PurePosixPath(name)
                parts = path.parts
                if not name or name.startswith("/") or "\\" in name or str(path) != name:
                    raise DeploymentError("release archive contains a non-canonical path")
                if not parts or parts[0] != "dak-release" or any(part in {"", ".", ".."} for part in parts):
                    raise DeploymentError(f"unsafe path in release archive: {member.name}")
                if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                    raise DeploymentError("release archive contains a link or unsupported entry")
                if member.isfile():
                    if name in files:
                        raise DeploymentError(f"duplicate archive entry: {name}")
                    total_size += member.size
                    if member.size < 0 or total_size > MAX_ARCHIVE_BYTES:
                        raise DeploymentError("release archive exceeds the expanded-size safety limit")
                    files[name] = member

            required = {
                "dak-release/manifest.json", "dak-release/release.json",
                "dak-release/SHA256SUMS", "dak-release/README.txt",
            }
            if not required <= files.keys():
                raise DeploymentError("release archive is missing required metadata")

            def read_member(name: str, limit: int = MAX_METADATA_BYTES) -> bytes:
                info = files.get(name)
                if info is None or info.size > limit:
                    raise DeploymentError(f"missing or oversized release metadata: {name}")
                stream = archive.extractfile(info)
                if stream is None:
                    raise DeploymentError(f"cannot read release entry: {name}")
                with stream:
                    return stream.read(limit + 1)

            manifest = _load_strict_json(
                read_member("dak-release/manifest.json"), "release manifest"
            )
            release = _load_strict_json(
                read_member("dak-release/release.json"), "release metadata"
            )
            try:
                checksum_text = read_member("dak-release/SHA256SUMS").decode("utf-8")
            except UnicodeDecodeError as error:
                raise DeploymentError("release checksums are not valid UTF-8") from error
            if not isinstance(release, dict) or release.get("schema") != RELEASE_SCHEMA:
                raise DeploymentError(f"release metadata must use {RELEASE_SCHEMA}")
            manifest_data = _json_bytes(manifest)
            if not isinstance(manifest, dict) or release.get("manifest_sha256") != hashlib.sha256(manifest_data).hexdigest():
                raise DeploymentError("release manifest digest does not match signed metadata")
            try:
                checked = validate_manifest(manifest, Path(__file__).resolve().parent, verify_files=False)
            except ManifestError as error:
                raise DeploymentError(f"system manifest is invalid: {error}") from error

            for component in checked["components"]:
                relative = _safe_path(component["path"])
                name = f"dak-release/payload/{relative}"
                info = files.get(name)
                if info is None or info.size != component["size_bytes"]:
                    raise DeploymentError(f"missing or incorrectly sized component: {relative}")
                stream = archive.extractfile(info)
                if stream is None:
                    raise DeploymentError(f"cannot read component: {relative}")
                with stream:
                    size, digest = _hash_stream(stream)
                if size != component["size_bytes"] or digest != component["sha256"]:
                    raise DeploymentError(f"component hash mismatch: {relative}")

            sums: dict[str, str] = {}
            for line in checksum_text.splitlines():
                match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
                if match is None:
                    raise DeploymentError("SHA256SUMS contains an invalid line")
                digest, relative = match.groups()
                relative = _safe_path(relative)
                if relative in sums:
                    raise DeploymentError(f"duplicate checksum path: {relative}")
                sums[relative] = digest
            expected = {
                name.removeprefix("dak-release/")
                for name in files if name != "dak-release/SHA256SUMS"
            }
            if set(sums) != expected:
                raise DeploymentError("SHA256SUMS does not cover exactly the release files")
            for relative, expected_hash in sums.items():
                stream = archive.extractfile(files[f"dak-release/{relative}"])
                if stream is None:
                    raise DeploymentError(f"cannot read checksummed file: {relative}")
                with stream:
                    _, actual_hash = _hash_stream(stream)
                if actual_hash != expected_hash:
                    raise DeploymentError(f"SHA-256 mismatch: {relative}")

            signature_name = "dak-release/release.json.sig"
            has_signature = signature_name in files
            signature_verified = False
            if public_key is not None:
                if not has_signature:
                    raise DeploymentError("a public key was supplied but the bundle has no signature")
                with tempfile.TemporaryDirectory(prefix="dak-verify-") as temporary:
                    base = Path(temporary)
                    release_file, signature_file = base / "release.json", base / "release.json.sig"
                    _write_new(release_file, read_member("dak-release/release.json"))
                    _write_new(signature_file, read_member(signature_name))
                    _verify_signature(release_file, signature_file, public_key)
                signature_verified = True
            if has_signature != (release.get("signature_algorithm") == "Ed25519"):
                raise DeploymentError("release signature metadata is inconsistent")
            if release.get("name") != manifest.get("name") or release.get("version") != manifest.get("version"):
                raise DeploymentError("release metadata does not match the system manifest")

            return {
                "schema": "dak.release-verification.v1",
                "valid": True,
                "name": manifest["name"],
                "version": manifest["version"],
                "architecture": manifest["architecture"],
                "component_count": checked["component_count"],
                "checksums_verified": len(sums),
                "signature_present": has_signature,
                "signature_verified": signature_verified,
                "signature_status": "verified" if signature_verified else ("present-not-checked" if has_signature else "unsigned"),
                "bootable_image_verified": False,
                "disk_writes_performed": False,
            }
    except (tarfile.TarError, OSError, EOFError) as error:
        raise DeploymentError(f"cannot verify release archive: {error}") from error


def _base_url(value: Any, *, secure_boot: bool) -> str:
    if not isinstance(value, str) or not value or len(value) > 2048 or any(char.isspace() for char in value):
        raise DeploymentError("base_url must be a valid HTTP(S) URL")
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError as error:
        raise DeploymentError("base_url contains an invalid host or port") from error
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise DeploymentError("base_url must use http:// or https:// and include a hostname")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise DeploymentError("base_url must not contain credentials, query parameters or fragments")
    if secure_boot and parsed.scheme != "https":
        raise DeploymentError("secure network deployment requires an HTTPS base_url")
    return value.rstrip("/")


def create_deployment_plan(
    manifest: dict[str, Any],
    component_root: str | Path,
    *,
    target: str,
    base_url: str | None = None,
    secure_boot: bool = False,
    data_size_bytes: int = 2 * _GIB,
) -> dict[str, Any]:
    """Prepare a non-destructive USB, network or cloud deployment plan."""
    if target not in {"usb", "pxe", "http", "cloud"}:
        raise DeploymentError("target must be usb, pxe, http or cloud")
    if not isinstance(secure_boot, bool):
        raise DeploymentError("secure_boot must be a boolean")
    if isinstance(data_size_bytes, bool) or not isinstance(data_size_bytes, int) or not 512 * _MIB <= data_size_bytes <= 32 * _GIB:
        raise DeploymentError("data_size_bytes must be between 512 MiB and 32 GiB")
    try:
        report = validate_manifest(manifest, component_root, verify_files=True)
    except (ManifestError, OSError) as error:
        raise DeploymentError(str(error)) from error

    components = {item["name"]: item for item in report["components"]}
    bootloader = components["bootloader"]
    rootfs_bytes = components["rootfs"]["size_bytes"]
    slot_bytes = max(2 * _GIB, ((rootfs_bytes * 5 // 4 + _ALIGNMENT - 1) // _ALIGNMENT) * _ALIGNMENT)
    layout = plan_image([
        {"name": "efi", "type": "efi-system", "size_bytes": 512 * _MIB},
        {"name": "duck_system_a", "type": "duck-system", "size_bytes": slot_bytes},
        {"name": "duck_system_b", "type": "duck-system", "size_bytes": slot_bytes},
        {"name": "duck_recovery", "type": "duck-recovery", "size_bytes": 512 * _MIB},
        {"name": "duck_data", "type": "duck-data", "size_bytes": data_size_bytes},
    ])

    network = None
    if target in {"pxe", "http"}:
        base = _base_url(base_url, secure_boot=secure_boot)
        loader = f"{base}/payload/{quote(bootloader['path'], safe='/')}"
        manifest_url = f"{base}/manifest.json"
        script = "\n".join([
            "#!ipxe",
            "dhcp || goto failed",
            f"set duck_manifest {manifest_url}",
            "chain --autofree " + loader + " manifest=$" + "{duck_manifest} || goto failed",
            ":failed",
            "echo DAK network handoff failed",
            "shell",
            "",
        ])
        network = {
            "protocol": "PXE/iPXE" if target == "pxe" else "UEFI HTTP Boot with iPXE handoff",
            "base_url": base,
            "bootloader_url": loader,
            "manifest_url": manifest_url,
            "ipxe_script": script,
            "manifest_verification_owner": "native-duck-bootloader",
            "signature_enforcement_configured": False,
            "https_transport": urlsplit(base).scheme == "https",
        }
    elif base_url is not None:
        raise DeploymentError("base_url is only valid for PXE or HTTP deployment")

    return {
        "schema": DEPLOYMENT_SCHEMA,
        "system": {
            "name": manifest["name"],
            "version": manifest["version"],
            "architecture": manifest["architecture"],
            "kernel_abi": manifest["kernel_abi"],
        },
        "target": target,
        "partition_table": "GPT",
        "image_layout": layout,
        "update_strategy": {
            "mode": "A/B",
            "slots": ["duck_system_a", "duck_system_b"],
            "initial_active_slot": "duck_system_a",
            "rollback_policy": "native-bootloader-required",
            "implemented_by_this_plan": False,
        },
        "secure_boot": {
            "requested": secure_boot,
            "ready": False,
            "reason": "firmware trust enrollment and native signature verification are not implemented by this planner",
        },
        "network": network,
        "cloud_formats": ["raw", "qcow2", "vhdx"] if target == "cloud" else [],
        "execution": {
            "image_created": False,
            "disk_written": False,
            "firmware_boot_tested": False,
            "hardware_tested": False,
        },
    }
