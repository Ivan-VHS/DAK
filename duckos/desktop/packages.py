"""SHA-256 package integrity checks and explicit hash-bound unsigned approvals."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import stat
from typing import Any

from .storage import read_json_state, write_json_state

SCHEMA = "duckos.package-trust.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
MAX_PACKAGE_BYTES = 8 * 1024 * 1024 * 1024


class PackageTrustError(ValueError):
    """Raised when a package cannot be inspected or an approval is invalid."""


@dataclass(frozen=True)
class SignatureEvidence:
    """Result supplied by a configured cryptographic signature verifier.

    Creating this value does not verify a signature. Only a trusted verifier
    adapter should construct verified evidence after checking the signature,
    signer trust and revocation state.
    """

    verified: bool
    key_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.verified, bool):
            raise PackageTrustError("signature verification status must be boolean")
        if not isinstance(self.key_id, str) or not self.key_id.strip() or len(self.key_id) > 256:
            raise PackageTrustError("signature evidence must include a bounded key ID")


def sha256_file(path: str | Path, *, maximum_bytes: int = MAX_PACKAGE_BYTES) -> tuple[int, str]:
    target = Path(path).expanduser()
    if isinstance(maximum_bytes, bool) or not isinstance(maximum_bytes, int) or maximum_bytes < 1:
        raise PackageTrustError("maximum_bytes must be a positive integer")
    try:
        if target.is_symlink():
            raise PackageTrustError("symbolic-link package paths are not allowed")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(target, flags)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise PackageTrustError("package path must refer to a regular file")
            if metadata.st_size < 1:
                raise PackageTrustError("empty package files are not allowed")
            if metadata.st_size > maximum_bytes:
                raise PackageTrustError(f"package exceeds the {maximum_bytes}-byte inspection limit")
            digest = hashlib.sha256()
            size = 0
            with os.fdopen(descriptor, "rb") as stream:
                descriptor = -1
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    size += len(chunk)
                    if size > maximum_bytes:
                        raise PackageTrustError("package grew beyond the configured inspection limit")
                    digest.update(chunk)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
    except PackageTrustError:
        raise
    except OSError as error:
        raise PackageTrustError(f"cannot inspect package: {error}") from error
    return size, digest.hexdigest()


class PackageTrustStore:
    def __init__(self, state_file: str | Path) -> None:
        self.state_file = Path(state_file).expanduser()
        self._default = {"schema": SCHEMA, "version": 1, "approved_hashes": {}}
        self._read()

    def _read(self) -> dict[str, Any]:
        state = read_json_state(self.state_file, self._default)
        approvals = state.get("approved_hashes")
        if state.get("schema") != SCHEMA or state.get("version") != 1 or not isinstance(approvals, dict):
            raise PackageTrustError("package trust store has an unsupported schema")
        for digest, record in approvals.items():
            if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
                raise PackageTrustError("package trust store contains an invalid SHA-256 key")
            if not isinstance(record, dict) or not isinstance(record.get("approved_at_utc"), str):
                raise PackageTrustError(f"invalid local approval record for {digest}")
        return state

    def verify(
        self,
        path: str | Path,
        *,
        expected_sha256: str | None = None,
        signature: SignatureEvidence | None = None,
    ) -> dict[str, Any]:
        size, actual = sha256_file(path)
        if expected_sha256 is not None:
            if not isinstance(expected_sha256, str) or not _SHA256.fullmatch(expected_sha256):
                raise PackageTrustError("expected_sha256 must be 64 lowercase hexadecimal characters")
            if actual != expected_sha256:
                return {
                    "schema": "duckos.package-verification.v1",
                    "status": "blocked",
                    "reason": "sha256-mismatch",
                    "sha256": actual,
                    "size_bytes": size,
                    "signature_verified": False,
                    "launch_allowed": False,
                    "execution_performed": False,
                }

        if signature is not None and signature.verified:
            status = "trusted"
            signer = signature.key_id
        elif actual in self._read()["approved_hashes"]:
            status = "local-approved"
            signer = None
        else:
            status = "unknown"
            signer = None

        return {
            "schema": "duckos.package-verification.v1",
            "status": status,
            "reason": "integrity-and-trust-policy-evaluated",
            "sha256": actual,
            "size_bytes": size,
            "signature_verified": bool(signature and signature.verified),
            "signer_key_id": signer,
            "launch_allowed": status in {"trusted", "local-approved"},
            "execution_performed": False,
        }

    def approve_unsigned(
        self,
        path: str | Path,
        *,
        confirmed: bool,
        expected_sha256: str | None = None,
    ) -> dict[str, Any]:
        if confirmed is not True:
            raise PackageTrustError("unsigned approval requires explicit user confirmation")
        size, digest = sha256_file(path)
        if expected_sha256 is not None and digest != expected_sha256:
            raise PackageTrustError("package changed before approval; SHA-256 does not match")
        state = self._read()
        state["approved_hashes"][digest] = {
            "approved_at_utc": datetime.now(timezone.utc).isoformat(),
            "approval_scope": "exact-sha256",
        }
        write_json_state(self.state_file, state)
        return {
            "schema": "duckos.package-approval.v1",
            "status": "local-approved",
            "sha256": digest,
            "size_bytes": size,
            "approval_scope": "exact-sha256",
            "execution_performed": False,
        }
