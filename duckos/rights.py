"""Local license, provenance and content-integrity contracts for DuckOS.

This module verifies publisher-signed metadata. It is not a DRM runtime, a store
account service, or a substitute for a native process/capture enforcement layer.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import time
from typing import Any, Mapping

ENTITLEMENT_SCHEMA = "duckos.entitlement.v1"
CONTENT_MANIFEST_SCHEMA = "duckos.content-manifest.v1"
TRANSFER_SCHEMA = "duckos.rights-transfer.v1"
USER_CONTENT_SCHEMA = "duckos.user-content-record.v1"
AUDIT_SCHEMA = "duckos.rights-audit-event.v1"

MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
MAX_FILES = 4096
MAX_CONTENT_BYTES = 34 * 1024 * 1024 * 1024
MAX_AUDIT_BYTES = 16 * 1024 * 1024
MAX_AUDIT_LINE_BYTES = 64 * 1024
SHA256_RE = re.compile(r"[0-9a-f]{64}")
IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
RIGHTS = frozenset({
    "install", "launch", "download", "backup", "transfer", "stream",
    "capture_screenshot", "capture_recording", "redistribute", "modify",
})
CONTENT_KINDS = frozenset({
    "game", "dlc", "theme", "media", "system_module", "save", "user_asset",
    "avatar", "preset", "mod",
})
CAPTURE_ACTIONS = frozenset({"screenshot", "recording", "streaming"})


class RightsError(ValueError):
    """Raised when a rights document or trust configuration is malformed."""


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise RightsError(f"document cannot be canonicalized: {error}") from error


def _read_document(path: str | Path, *, limit: int = MAX_DOCUMENT_BYTES) -> dict[str, Any]:
    source = Path(path).expanduser()
    if source.is_symlink() or not source.is_file():
        raise RightsError("input must be an existing regular file, not a symlink")
    try:
        if source.stat().st_size > limit:
            raise RightsError(f"input exceeds the {limit} byte safety limit")
        value = json.loads(source.read_text(encoding="utf-8"))
    except OSError as error:
        raise RightsError(f"cannot read {source}: {error}") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RightsError(f"invalid JSON document: {error}") from error
    if not isinstance(value, dict):
        raise RightsError("document root must be a JSON object")
    return value


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER_RE.fullmatch(value):
        raise RightsError(f"{label} must be a short stable identifier")
    return value


def _timestamp(value: Any, label: str, *, optional: bool = False) -> int | None:
    if optional and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RightsError(f"{label} must be a non-negative Unix timestamp")
    return value


def _safe_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise RightsError("artifact path must be non-empty relative text")
    if "\\" in value or value.startswith("/") or ":" in value:
        raise RightsError(f"unsafe artifact path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value:
        raise RightsError(f"artifact path is not canonical: {value!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise RightsError(f"artifact path contains an unsafe component: {value!r}")
    if any(ord(char) < 32 for char in value):
        raise RightsError("artifact paths must not contain control characters")
    return value


def _public_key_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if path.is_symlink() or not path.is_file():
        raise RightsError("trusted public key must be a regular file, not a symlink")
    if path.stat().st_size > 64 * 1024:
        raise RightsError("trusted public key file is too large")
    return path.resolve(strict=True)


def _verify_ed25519(payload: bytes, encoded_signature: Any, public_key: str | Path) -> bool:
    if not isinstance(encoded_signature, str) or len(encoded_signature) > 256:
        return False
    try:
        signature = base64.b64decode(encoded_signature, validate=True)
    except (binascii.Error, ValueError):
        return False
    if len(signature) != 64:
        return False

    key_path = _public_key_path(public_key)
    try:
        with tempfile.TemporaryDirectory(prefix="duckos-rights-") as temporary:
            root = Path(temporary)
            message_path = root / "message.bin"
            signature_path = root / "signature.bin"
            message_path.write_bytes(payload)
            signature_path.write_bytes(signature)
            result = subprocess.run(
                [
                    "openssl", "pkeyutl", "-verify", "-pubin", "-inkey", str(key_path),
                    "-rawin", "-in", str(message_path), "-sigfile", str(signature_path),
                ],
                check=False, capture_output=True, text=True, timeout=20,
            )
    except FileNotFoundError as error:
        raise RightsError("OpenSSL is required for Ed25519 rights verification") from error
    except subprocess.TimeoutExpired as error:
        raise RightsError("Ed25519 verification timed out") from error
    return result.returncode == 0


def _verify_signed_document(
    document: dict[str, Any],
    trusted_keys: Mapping[str, str | Path],
    *,
    signer_field: str,
) -> tuple[bool, str]:
    signer = document.get(signer_field)
    signature = document.get("signature")
    if not isinstance(signer, dict) or not isinstance(signature, dict):
        return False, "signature_missing"
    key_id = signer.get("key_id")
    if not isinstance(key_id, str) or key_id not in trusted_keys:
        return False, "untrusted_issuer"
    if signature.get("algorithm") != "Ed25519":
        return False, "unsupported_signature"
    payload = dict(document)
    payload.pop("signature", None)
    valid = _verify_ed25519(
        _canonical_json(payload), signature.get("value"), trusted_keys[key_id]
    )
    return valid, "verified" if valid else "signature_invalid"


def _blocked(
    reason_code: str,
    message: str,
    next_step: str,
    **details: Any,
) -> dict[str, Any]:
    return {
        "schema": "duckos.rights-decision.v1",
        "allowed": False,
        "status": "blocked",
        "reason_code": reason_code,
        "message": message,
        "next_step": next_step,
        **details,
    }


def verify_entitlement(
    entitlement: dict[str, Any],
    trusted_keys: Mapping[str, str | Path],
    *,
    profile_id: str | None,
    home_device_id: str | None,
    region: str | None = None,
    offline: bool = False,
    required_action: str | None = None,
    now: int | None = None,
) -> dict[str, Any]:
    """Verify a cached signed entitlement and apply profile/device/time policy.

    Profile grants follow the owner profile. Home-device grants follow the
    registered device and can be checked for any local profile on that device.
    """
    if not isinstance(entitlement, dict) or entitlement.get("schema") != ENTITLEMENT_SCHEMA:
        raise RightsError(f"entitlement must use {ENTITLEMENT_SCHEMA}")
    entitlement_id = _identifier(entitlement.get("entitlement_id"), "entitlement_id")
    issuer = entitlement.get("issuer")
    content = entitlement.get("content")
    license_data = entitlement.get("license")
    if not isinstance(issuer, dict) or not isinstance(content, dict) or not isinstance(license_data, dict):
        raise RightsError("entitlement issuer, content and license objects are required")
    issuer_id = _identifier(issuer.get("id"), "issuer.id")
    content_id = _identifier(content.get("id"), "content.id")
    content_kind = content.get("kind")
    if content_kind not in CONTENT_KINDS:
        raise RightsError("content.kind is not a supported DuckOS content type")
    content_hash = content.get("manifest_sha256")
    if not isinstance(content_hash, str) or not SHA256_RE.fullmatch(content_hash):
        raise RightsError("content.manifest_sha256 must be a lowercase SHA-256 digest")

    scope = license_data.get("scope")
    if scope not in {"profile", "home_device"}:
        raise RightsError("license.scope must be 'profile' or 'home_device'")
    bound_profile = license_data.get("profile_id")
    bound_device = license_data.get("home_device_id")
    if scope == "profile":
        bound_profile = _identifier(bound_profile, "license.profile_id")
        if bound_device is not None:
            raise RightsError("profile grants must not also be bound to a home device")
    else:
        bound_device = _identifier(bound_device, "license.home_device_id")
        if bound_profile is not None:
            raise RightsError("home-device grants must not also be bound to a profile")

    rights = license_data.get("rights")
    if not isinstance(rights, list) or not rights or any(not isinstance(item, str) or item not in RIGHTS for item in rights):
        raise RightsError("license.rights must be a non-empty list of known actions")
    if len(rights) != len(set(rights)):
        raise RightsError("license.rights must not contain duplicates")

    issued_at = _timestamp(license_data.get("issued_at"), "license.issued_at")
    not_before = _timestamp(license_data.get("not_before"), "license.not_before")
    expires_at = _timestamp(license_data.get("expires_at"), "license.expires_at", optional=True)
    offline_valid_until = _timestamp(
        license_data.get("offline_valid_until"), "license.offline_valid_until"
    )
    assert issued_at is not None and not_before is not None and offline_valid_until is not None
    if not_before < issued_at or offline_valid_until < issued_at:
        raise RightsError("license time window precedes its issue time")
    if expires_at is not None and expires_at < not_before:
        raise RightsError("license expires before it becomes valid")

    token_region = license_data.get("region")
    if token_region is not None:
        if not isinstance(token_region, str):
            raise RightsError("license.region must be text or null")
        token_region = token_region.strip().upper()
        if not token_region or len(token_region) > 16:
            raise RightsError("license.region must be a short region code or null")

    signature_valid, signature_status = _verify_signed_document(
        entitlement, trusted_keys, signer_field="issuer"
    )
    details = {
        "entitlement_id": entitlement_id,
        "issuer_id": issuer_id,
        "content_id": content_id,
        "content_kind": content_kind,
        "license_scope": scope,
        "signature_status": signature_status,
        "offline_check": offline,
    }
    if not signature_valid:
        reason = signature_status
        messages = {
            "untrusted_issuer": (
                "The signing key is not in the local trust store.",
                "Install the publisher's verified public key through the DuckOS trust service.",
            ),
            "signature_missing": (
                "The entitlement has no publisher signature.",
                "Obtain a signed entitlement from the original publisher or store.",
            ),
            "unsupported_signature": (
                "The entitlement uses an unsupported signature algorithm.",
                "Obtain a new entitlement signed with Ed25519.",
            ),
            "signature_invalid": (
                "The entitlement signature does not match its signed contents.",
                "Obtain a fresh entitlement from the original publisher or store.",
            ),
        }
        message, next_step = messages.get(
            reason,
            ("The entitlement signature could not be verified.",
             "Obtain a fresh entitlement from the original publisher or store."),
        )
        return _blocked(reason, message, next_step, **details)

    current_time = int(time.time()) if now is None else _timestamp(now, "now")
    assert current_time is not None
    if current_time < not_before:
        return _blocked(
            "not_yet_valid", "This entitlement is not valid yet.",
            "Check the device clock or retry after the activation time.", **details,
        )
    if expires_at is not None and current_time > expires_at:
        return _blocked(
            "expired", "This entitlement has expired.",
            "Renew the subscription or restore access through the original publisher.", **details,
        )
    if offline and current_time > offline_valid_until:
        return _blocked(
            "offline_window_expired",
            "The cached offline authorization window has ended.",
            "Reconnect and refresh the entitlement with the original publisher.", **details,
        )
    if scope == "profile" and profile_id != bound_profile:
        return _blocked(
            "wrong_profile", "This content is licensed to a different user profile.",
            "Sign in with the profile that owns the entitlement.", **details,
        )
    if scope == "home_device" and home_device_id != bound_device:
        return _blocked(
            "wrong_home_device", "This device is not the registered home device for this license.",
            "Re-authorize the home device through the original publisher.", **details,
        )
    requested_region = region.strip().upper() if isinstance(region, str) else None
    if token_region not in {None, "WW"} and not requested_region:
        return _blocked(
            "region_unknown", "The entitlement is region-restricted, but no current region was supplied.",
            "Supply the current account or device region before using this entitlement.", **details,
        )
    if token_region not in {None, "WW"} and requested_region != token_region:
        return _blocked(
            "region_restricted", "This entitlement is not valid in the current region.",
            "Check the publisher's regional terms or use an eligible account region.", **details,
        )
    if required_action is not None:
        if required_action not in RIGHTS:
            raise RightsError("required_action is not a recognized content right")
        if required_action not in rights:
            return _blocked(
                "action_not_licensed",
                f"The entitlement does not grant '{required_action}'.",
                "Use an allowed action or obtain the appropriate permission from the rights holder.",
                **details,
            )

    return {
        "schema": "duckos.rights-decision.v1",
        "allowed": True,
        "status": "licensed_profile" if scope == "profile" else "licensed_home_device",
        "reason_code": "verified",
        "message": (
            "Publisher signature and profile entitlement verified."
            if scope == "profile"
            else "Publisher signature and home-device entitlement verified."
        ),
        "next_step": None,
        "granted_rights": list(rights),
        **details,
    }


def verify_licensed_content(
    entitlement: dict[str, Any],
    manifest: dict[str, Any],
    root: str | Path,
    trusted_keys: Mapping[str, str | Path],
    *,
    profile_id: str | None,
    home_device_id: str | None,
    region: str | None = None,
    offline: bool = False,
    required_action: str | None = "launch",
    now: int | None = None,
) -> dict[str, Any]:
    """Verify an entitlement and the exact package manifest it authorizes.

    The entitlement digest is the SHA-256 of the canonical UTF-8 JSON encoding
    of the complete signed manifest, including its signature object. This binds
    the license to one exact manifest rather than merely to a content label.
    """
    decision = verify_entitlement(
        entitlement,
        trusted_keys,
        profile_id=profile_id,
        home_device_id=home_device_id,
        region=region,
        offline=offline,
        required_action=required_action,
        now=now,
    )
    if not decision.get("allowed"):
        return {
            "schema": "duckos.licensed-content-decision.v1",
            "allowed": False,
            "valid": False,
            "status": "blocked",
            "reason_code": decision.get("reason_code", "entitlement_denied"),
            "message": decision.get("message", "The entitlement was not accepted."),
            "next_step": decision.get("next_step"),
            "entitlement_decision": decision,
        }

    token_content = entitlement.get("content") if isinstance(entitlement, dict) else None
    manifest_content = manifest.get("content") if isinstance(manifest, dict) else None
    if not isinstance(token_content, dict) or not isinstance(manifest_content, dict):
        raise RightsError("entitlement and manifest must both contain content objects")

    if (
        token_content.get("id") != manifest_content.get("id")
        or token_content.get("kind") != manifest_content.get("kind")
    ):
        return {
            "schema": "duckos.licensed-content-decision.v1",
            "allowed": False,
            "valid": False,
            "status": "blocked",
            "reason_code": "content_identity_mismatch",
            "message": "The entitlement identifies different content from the supplied manifest.",
            "next_step": "Use the original manifest referenced by this entitlement.",
            "entitlement_decision": decision,
        }

    manifest_digest = hashlib.sha256(_canonical_json(manifest)).hexdigest()
    expected_digest = token_content.get("manifest_sha256")
    if not isinstance(expected_digest, str) or not hmac.compare_digest(
        expected_digest, manifest_digest
    ):
        return {
            "schema": "duckos.licensed-content-decision.v1",
            "allowed": False,
            "valid": False,
            "status": "blocked",
            "reason_code": "manifest_digest_mismatch",
            "message": "The signed entitlement does not reference this exact content manifest.",
            "next_step": "Restore the publisher's original manifest or obtain a matching entitlement.",
            "manifest_sha256": manifest_digest,
            "entitlement_decision": decision,
        }

    content_result = verify_content_manifest(manifest, root, trusted_keys)
    if not content_result.get("valid"):
        return {
            "schema": "duckos.licensed-content-decision.v1",
            "allowed": False,
            "valid": False,
            "status": "blocked",
            "reason_code": content_result.get("reason_code", "content_verification_failed"),
            "message": content_result.get("message", "The content package could not be verified."),
            "next_step": "Restore the original signed package from its publisher.",
            "manifest_sha256": manifest_digest,
            "entitlement_decision": decision,
            "content_verification": content_result,
        }

    return {
        "schema": "duckos.licensed-content-decision.v1",
        "allowed": True,
        "valid": True,
        "status": decision["status"],
        "reason_code": "verified",
        "message": "The entitlement, exact signed manifest and package files are verified.",
        "next_step": None,
        "manifest_sha256": manifest_digest,
        "granted_rights": decision.get("granted_rights", []),
        "entitlement_decision": decision,
        "content_verification": content_result,
        "capture_policy": content_result.get("capture_policy"),
        "native_launch_enforcement": False,
    }


def verify_content_manifest(
    manifest: dict[str, Any],
    root: str | Path,
    trusted_keys: Mapping[str, str | Path],
) -> dict[str, Any]:
    """Verify publisher signature and the exact file set described by a manifest."""
    if not isinstance(manifest, dict) or manifest.get("schema") != CONTENT_MANIFEST_SCHEMA:
        raise RightsError(f"content manifest must use {CONTENT_MANIFEST_SCHEMA}")
    content = manifest.get("content")
    publisher = manifest.get("publisher")
    files = manifest.get("files")
    attribution = manifest.get("attribution")
    if not isinstance(content, dict) or not isinstance(publisher, dict):
        raise RightsError("content and publisher objects are required")
    if not isinstance(attribution, dict):
        raise RightsError("attribution metadata is required")
    content_id = _identifier(content.get("id"), "content.id")
    kind = content.get("kind")
    if kind not in CONTENT_KINDS:
        raise RightsError("content.kind is not a supported DuckOS content type")
    publisher_id = _identifier(publisher.get("id"), "publisher.id")
    title = content.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 240:
        raise RightsError("content.title must contain 1 to 240 characters")
    if not isinstance(files, list) or not files or len(files) > MAX_FILES:
        raise RightsError(f"content manifest must describe between 1 and {MAX_FILES} files")

    expected: dict[str, tuple[int, str]] = {}
    total_bytes = 0
    for entry in files:
        if not isinstance(entry, dict):
            raise RightsError("each content file entry must be an object")
        relative = _safe_relative_path(entry.get("path"))
        size = entry.get("size_bytes")
        digest = entry.get("sha256")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise RightsError(f"invalid size for content file {relative}")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise RightsError(f"invalid SHA-256 for content file {relative}")
        if relative in expected:
            raise RightsError(f"duplicate content file path: {relative}")
        expected[relative] = (size, digest)
        total_bytes += size
        if total_bytes > MAX_CONTENT_BYTES:
            raise RightsError("content package exceeds the expanded-size safety limit")

    signature_valid, signature_status = _verify_signed_document(
        manifest, trusted_keys, signer_field="publisher"
    )
    details = {
        "schema": "duckos.content-verification.v1",
        "content_id": content_id,
        "content_kind": kind,
        "title": title,
        "publisher_id": publisher_id,
        "signature_status": signature_status,
        "creator": attribution.get("creator"),
        "copyright": attribution.get("copyright"),
        "source": attribution.get("source"),
    }
    if not signature_valid:
        reason = "untrusted_issuer" if signature_status == "untrusted_issuer" else "signature_invalid"
        return {
            "valid": False, "reason_code": reason,
            "message": "Publisher signature could not be verified against a local trust root.",
            "files_verified": 0, **details,
        }

    base = Path(root).expanduser()
    if base.is_symlink() or not base.is_dir():
        raise RightsError("content root must be a regular directory, not a symlink")
    base = base.resolve(strict=True)
    actual: dict[str, Path] = {}
    for directory, child_dirs, child_files in os.walk(base, followlinks=False):
        parent = Path(directory)
        for name in list(child_dirs):
            candidate = parent / name
            if candidate.is_symlink():
                raise RightsError(f"content package contains a symlink: {candidate.relative_to(base)}")
        for name in child_files:
            candidate = parent / name
            if candidate.is_symlink() or not candidate.is_file():
                raise RightsError(f"content package contains a non-regular file: {candidate.relative_to(base)}")
            relative = candidate.relative_to(base).as_posix()
            if relative in actual:
                raise RightsError(f"duplicate file encountered in content package: {relative}")
            actual[relative] = candidate

    if set(actual) != set(expected):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        return {
            "valid": False, "reason_code": "content_file_set_mismatch",
            "message": "The package file set does not exactly match its signed manifest.",
            "missing_files": missing[:20], "unexpected_files": extra[:20],
            "files_verified": 0, **details,
        }

    verified = 0
    for relative, (expected_size, expected_digest) in expected.items():
        path = actual[relative]
        size = 0
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                size += len(chunk)
                digest.update(chunk)
        if size != expected_size or digest.hexdigest() != expected_digest:
            return {
                "valid": False, "reason_code": "integrity_mismatch",
                "message": f"Content integrity check failed for '{relative}'.",
                "failed_path": relative, "files_verified": verified, **details,
            }
        verified += 1

    return {
        "valid": True, "reason_code": "verified",
        "message": "Publisher signature, package file list and SHA-256 digests verified.",
        "files_verified": verified, "package_bytes": total_bytes,
        "capture_policy": manifest.get("capture_policy"), **details,
    }


def evaluate_capture_policy(
    capture_policy: dict[str, Any] | None,
    action: str,
    *,
    manifest_verified: bool,
) -> dict[str, Any]:
    """Return the declared capture decision; a native compositor must enforce it."""
    if action not in CAPTURE_ACTIONS:
        raise RightsError("capture action must be screenshot, recording or streaming")
    if not manifest_verified or not isinstance(capture_policy, dict):
        return {
            "allowed": False, "status": "unknown",
            "reason_code": "unverified_capture_policy",
            "message": "No verified publisher capture policy is available.",
            "native_enforcement": False,
        }
    denied = capture_policy.get("denied_actions", [])
    permitted = capture_policy.get("allowed_actions", [])
    if not isinstance(denied, list) or not isinstance(permitted, list):
        raise RightsError("capture policy action lists must be arrays")
    if any(not isinstance(item, str) or item not in CAPTURE_ACTIONS for item in denied + permitted):
        raise RightsError("capture policy contains an unsupported action")
    if action in denied:
        return {
            "allowed": False, "status": "restricted",
            "reason_code": "capture_restricted",
            "message": f"The verified rights policy prohibits {action}.",
            "native_enforcement": False,
        }
    if action in permitted:
        return {
            "allowed": True, "status": "allowed",
            "reason_code": "capture_permitted",
            "message": f"The verified rights policy permits {action}.",
            "native_enforcement": False,
        }
    return {
        "allowed": False, "status": "not_declared",
        "reason_code": "capture_not_granted",
        "message": f"The verified rights policy does not grant {action}.",
        "native_enforcement": False,
    }


def build_user_content_record(
    *,
    content_id: str,
    title: str,
    kind: str,
    creator: str,
    source_description: str,
    copyright_notice: str,
    files: list[dict[str, Any]],
    license_id: str | None = None,
) -> dict[str, Any]:
    """Create a self-declared attribution record for a save or user-made asset."""
    content_id = _identifier(content_id, "content_id")
    if kind not in {"save", "theme", "avatar", "preset", "mod", "user_asset"}:
        raise RightsError("user content kind must be save, theme, avatar, preset, mod or user_asset")
    values = {
        "title": title, "creator": creator,
        "source_description": source_description, "copyright_notice": copyright_notice,
    }
    if any(not isinstance(value, str) or not value.strip() or len(value) > 500 for value in values.values()):
        raise RightsError("user content attribution fields must contain 1 to 500 characters")
    if not isinstance(files, list) or not files or len(files) > MAX_FILES:
        raise RightsError(f"user content must list between 1 and {MAX_FILES} files")
    checked_files = []
    seen: set[str] = set()
    for entry in files:
        if not isinstance(entry, dict):
            raise RightsError("user content file entries must be objects")
        path = _safe_relative_path(entry.get("path"))
        size, digest = entry.get("size_bytes"), entry.get("sha256")
        if path in seen:
            raise RightsError(f"duplicate user content path: {path}")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise RightsError(f"invalid user content size: {path}")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise RightsError(f"invalid user content SHA-256: {path}")
        checked_files.append({"path": path, "size_bytes": size, "sha256": digest})
        seen.add(path)
    return {
        "schema": USER_CONTENT_SCHEMA,
        "content": {"id": content_id, "title": title, "kind": kind},
        "attribution": {
            "creator": creator,
            "source": {"type": "user_declared", "description": source_description},
            "copyright_notice": copyright_notice,
            "license_id": license_id,
            "status": "self_declared_not_publisher_verified",
        },
        "files": checked_files,
        "save_data_separate_from_protected_package": kind == "save",
        "signature_status": "unsigned_user_metadata",
    }


def build_transfer_manifest(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Package metadata references without changing or re-issuing entitlement tokens."""
    if not isinstance(items, list) or not items or len(items) > 1000:
        raise RightsError("transfer manifest must contain between 1 and 1000 items")
    normalized = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise RightsError("transfer entries must be objects")
        manifest = item.get("content_manifest")
        if not isinstance(manifest, dict) or manifest.get("schema") != CONTENT_MANIFEST_SCHEMA:
            raise RightsError("each transfer entry must keep its original signed content manifest")
        content = manifest.get("content")
        if not isinstance(content, dict):
            raise RightsError("transfer content metadata is missing")
        content_id = _identifier(content.get("id"), "content.id")
        if content_id in seen:
            raise RightsError(f"duplicate transfer content id: {content_id}")
        seen.add(content_id)
        entitlement = item.get("entitlement")
        if entitlement is not None and (
            not isinstance(entitlement, dict) or entitlement.get("schema") != ENTITLEMENT_SCHEMA
        ):
            raise RightsError("transfer entitlement must remain an original signed entitlement document")
        save_metadata = item.get("save_metadata")
        if save_metadata is not None and not isinstance(save_metadata, dict):
            raise RightsError("save_metadata must be an object or null")
        normalized.append({
            "content_id": content_id,
            "content_manifest": manifest,
            "entitlement": entitlement,
            "save_metadata": save_metadata,
        })
    return {
        "schema": TRANSFER_SCHEMA,
        "version": 1,
        "created_at": int(time.time()),
        "items": normalized,
        "entitlement_handling": (
            "Signed entitlement documents are copied verbatim. Export does not transfer, "
            "reassign or widen rights. Profile and home-device bindings are rechecked on import."
        ),
        "authorization_granted": False,
    }


def validate_transfer_manifest(document: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict) or document.get("schema") != TRANSFER_SCHEMA or document.get("version") != 1:
        raise RightsError(f"transfer document must use {TRANSFER_SCHEMA} version 1")
    items = document.get("items")
    if not isinstance(items, list) or not items or len(items) > 1000:
        raise RightsError("transfer manifest must contain between 1 and 1000 items")
    seen: set[str] = set()
    tokens = 0
    saves = 0
    for item in items:
        if not isinstance(item, dict):
            raise RightsError("transfer entries must be objects")
        manifest = item.get("content_manifest")
        if not isinstance(manifest, dict) or manifest.get("schema") != CONTENT_MANIFEST_SCHEMA:
            raise RightsError("transfer entry is missing its original content manifest")
        content = manifest.get("content")
        if not isinstance(content, dict):
            raise RightsError("transfer entry is missing content metadata")
        content_id = _identifier(content.get("id"), "content.id")
        if content_id in seen:
            raise RightsError(f"duplicate transfer content id: {content_id}")
        seen.add(content_id)
        token = item.get("entitlement")
        if token is not None:
            if not isinstance(token, dict) or token.get("schema") != ENTITLEMENT_SCHEMA:
                raise RightsError("transfer entry contains a malformed entitlement")
            tokens += 1
        if content.get("kind") == "save":
            saves += 1
    return {
        "schema": "duckos.rights-transfer-validation.v1",
        "valid": True,
        "items": len(items),
        "entitlement_documents": tokens,
        "save_entries_separate_from_game_packages": saves,
        "authorization_granted": False,
        "reverification_required_on_import": True,
    }


def default_audit_path() -> Path:
    return Path.home() / ".duckos" / "rights-audit.jsonl"


class RightsAuditLog:
    """Append-only, hash-chained local evidence log; not tamper-proof storage."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path).expanduser() if path is not None else default_audit_path()

    def verify(self) -> dict[str, Any]:
        if self.path.is_symlink():
            raise RightsError("rights audit log must not be a symlink")
        if not self.path.exists():
            return {
                "schema": "duckos.rights-audit-verification.v1",
                "valid": True, "events": 0, "head_hash": "0" * 64,
            }
        if not self.path.is_file() or self.path.stat().st_size > MAX_AUDIT_BYTES:
            raise RightsError("rights audit log is not a regular file or exceeds 16 MiB")
        previous = "0" * 64
        events = 0
        with self.path.open("rb") as stream:
            for line_number, line in enumerate(stream, 1):
                if len(line) > MAX_AUDIT_LINE_BYTES or not line.endswith(b"\n"):
                    return {
                        "schema": "duckos.rights-audit-verification.v1",
                        "valid": False, "events": events,
                        "reason": f"invalid or oversized line {line_number}",
                    }
                try:
                    record = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return {
                        "schema": "duckos.rights-audit-verification.v1",
                        "valid": False, "events": events,
                        "reason": f"invalid JSON on line {line_number}",
                    }
                if not isinstance(record, dict) or record.get("schema") != AUDIT_SCHEMA:
                    return {
                        "schema": "duckos.rights-audit-verification.v1",
                        "valid": False, "events": events,
                        "reason": f"unexpected event schema on line {line_number}",
                    }
                supplied_hash = record.get("event_hash")
                body = dict(record)
                body.pop("event_hash", None)
                expected_hash = hashlib.sha256(_canonical_json(body)).hexdigest()
                if record.get("sequence") != events + 1 or record.get("previous_hash") != previous:
                    return {
                        "schema": "duckos.rights-audit-verification.v1",
                        "valid": False, "events": events,
                        "reason": f"broken sequence on line {line_number}",
                    }
                if not isinstance(supplied_hash, str) or not hmac.compare_digest(supplied_hash, expected_hash):
                    return {
                        "schema": "duckos.rights-audit-verification.v1",
                        "valid": False, "events": events,
                        "reason": f"event hash mismatch on line {line_number}",
                    }
                previous = supplied_hash
                events += 1
        return {
            "schema": "duckos.rights-audit-verification.v1",
            "valid": True, "events": events, "head_hash": previous,
        }

    def append(
        self,
        *,
        action: str,
        content_id: str | None,
        status: str,
        reason_code: str,
        entitlement_id: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(action, str) or not action or len(action) > 80:
            raise RightsError("audit action must be 1 to 80 characters")
        if not isinstance(status, str) or not status or len(status) > 40:
            raise RightsError("audit status must be 1 to 40 characters")
        if not isinstance(reason_code, str) or not reason_code or len(reason_code) > 80:
            raise RightsError("audit reason_code must be 1 to 80 characters")
        verification = self.verify()
        if not verification["valid"]:
            raise RightsError("rights audit chain is invalid; refusing to append new evidence")
        for parent in reversed(self.path.parent.parents):
            if parent.is_symlink():
                raise RightsError("rights audit path must not cross a symlinked directory")
        if self.path.parent.exists() and self.path.parent.is_symlink():
            raise RightsError("rights audit directory must not be a symlink")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        body = {
            "schema": AUDIT_SCHEMA,
            "sequence": verification["events"] + 1,
            "timestamp": int(time.time()),
            "action": action,
            "content_id": content_id,
            "entitlement_id": entitlement_id,
            "status": status,
            "reason_code": reason_code,
            "previous_hash": verification["head_hash"],
        }
        record = dict(body)
        record["event_hash"] = hashlib.sha256(_canonical_json(body)).hexdigest()
        data = _canonical_json(record) + b"\n"
        if self.path.exists() and self.path.stat().st_size + len(data) > MAX_AUDIT_BYTES:
            raise RightsError("rights audit log reached the 16 MiB limit; archive it before appending")
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(self.path, flags, 0o600)
        try:
            os.fchmod(descriptor, 0o600) if hasattr(os, "fchmod") else None
            view = memoryview(data)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise RightsError("could not append the rights audit record")
                view = view[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return record
