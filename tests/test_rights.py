from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from duckos.rights import (
    CONTENT_MANIFEST_SCHEMA,
    ENTITLEMENT_SCHEMA,
    RightsAuditLog,
    RightsError,
    build_transfer_manifest,
    build_user_content_record,
    evaluate_capture_policy,
    validate_transfer_manifest,
    verify_content_manifest,
    verify_entitlement,
    verify_licensed_content,
)


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


@unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for Ed25519 tests")
class RightsVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.private_key = cls.root / "issuer-private.pem"
        cls.public_key = cls.root / "issuer-public.pem"
        subprocess.run(
            ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(cls.private_key)],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["openssl", "pkey", "-in", str(cls.private_key), "-pubout", "-out", str(cls.public_key)],
            check=True, capture_output=True,
        )
        cls.trusted_keys = {"studio-key-2026": cls.public_key}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def sign(self, document: dict) -> dict:
        payload = dict(document)
        payload.pop("signature", None)
        message = self.root / "message.json"
        signature = self.root / "message.sig"
        message.write_bytes(canonical(payload))
        subprocess.run(
            ["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", str(self.private_key),
             "-in", str(message), "-out", str(signature)],
            check=True, capture_output=True,
        )
        result = dict(payload)
        result["signature"] = {
            "algorithm": "Ed25519",
            "value": base64.b64encode(signature.read_bytes()).decode("ascii"),
        }
        return result

    def entitlement(self, *, scope="profile", profile_id="profile-ivan",
                    device_id=None, offline_until=1_700_001_800,
                    expires_at=1_700_003_600, rights=None,
                    manifest_sha256="a" * 64):
        license_data = {
            "scope": scope,
            "profile_id": profile_id if scope == "profile" else None,
            "home_device_id": device_id if scope == "home_device" else None,
            "rights": rights or ["install", "launch", "backup", "transfer"],
            "region": "WW",
            "issued_at": 1_700_000_000,
            "not_before": 1_700_000_000,
            "expires_at": expires_at,
            "offline_valid_until": offline_until,
        }
        return self.sign({
            "schema": ENTITLEMENT_SCHEMA,
            "entitlement_id": "entitlement-aster",
            "issuer": {"id": "studio.example", "key_id": "studio-key-2026"},
            "content": {
                "id": "game.aster", "kind": "game",
                "manifest_sha256": manifest_sha256,
            },
            "license": license_data,
        })

    def test_profile_entitlement_is_bound_to_its_owner(self):
        token = self.entitlement()
        allowed = verify_entitlement(
            token, self.trusted_keys, profile_id="profile-ivan",
            home_device_id="duck-bedroom", required_action="launch",
            now=1_700_000_100,
        )
        denied = verify_entitlement(
            token, self.trusted_keys, profile_id="profile-other",
            home_device_id="duck-bedroom", required_action="launch",
            now=1_700_000_100,
        )
        self.assertTrue(allowed["allowed"])
        self.assertEqual(allowed["status"], "licensed_profile")
        self.assertFalse(denied["allowed"])
        self.assertEqual(denied["reason_code"], "wrong_profile")

    def test_home_device_entitlement_works_for_any_local_profile_on_that_device(self):
        token = self.entitlement(scope="home_device", device_id="duck-living-room")
        allowed = verify_entitlement(
            token, self.trusted_keys, profile_id="guest-profile",
            home_device_id="duck-living-room", offline=True, now=1_700_000_100,
        )
        denied = verify_entitlement(
            token, self.trusted_keys, profile_id="guest-profile",
            home_device_id="duck-bedroom", offline=True, now=1_700_000_100,
        )
        self.assertTrue(allowed["allowed"])
        self.assertEqual(allowed["status"], "licensed_home_device")
        self.assertFalse(denied["allowed"])
        self.assertEqual(denied["reason_code"], "wrong_home_device")

    def test_offline_window_and_subscription_expiry_are_separate(self):
        token = self.entitlement(offline_until=1_700_000_150)
        offline_denied = verify_entitlement(
            token, self.trusted_keys, profile_id="profile-ivan",
            home_device_id=None, offline=True, now=1_700_000_151,
        )
        still_online_valid = verify_entitlement(
            token, self.trusted_keys, profile_id="profile-ivan",
            home_device_id=None, offline=False, now=1_700_000_151,
        )
        expired = verify_entitlement(
            self.entitlement(expires_at=1_700_000_120),
            self.trusted_keys, profile_id="profile-ivan",
            home_device_id=None, now=1_700_000_121,
        )
        self.assertEqual(offline_denied["reason_code"], "offline_window_expired")
        self.assertTrue(still_online_valid["allowed"])
        self.assertEqual(expired["reason_code"], "expired")

    def test_untrusted_issuer_and_invalid_signature_fail_closed(self):
        token = self.entitlement()
        untrusted = verify_entitlement(
            token, {}, profile_id="profile-ivan", home_device_id=None,
            now=1_700_000_100,
        )
        token["license"]["rights"] = ["launch", "redistribute"]
        tampered = verify_entitlement(
            token, self.trusted_keys, profile_id="profile-ivan",
            home_device_id=None, now=1_700_000_100,
        )
        self.assertFalse(untrusted["allowed"])
        self.assertEqual(untrusted["reason_code"], "untrusted_issuer")
        self.assertFalse(tampered["allowed"])
        self.assertEqual(tampered["reason_code"], "signature_invalid")

    def test_region_and_action_restrictions_are_explained(self):
        token = self.entitlement(rights=["launch"])
        region = dict(token)
        region["license"] = dict(token["license"], region="US")
        region = self.sign(region)
        wrong_region = verify_entitlement(
            region, self.trusted_keys, profile_id="profile-ivan",
            home_device_id=None, region="UA", now=1_700_000_100,
        )
        no_backup = verify_entitlement(
            token, self.trusted_keys, profile_id="profile-ivan",
            home_device_id=None, required_action="backup", now=1_700_000_100,
        )
        self.assertEqual(wrong_region["reason_code"], "region_restricted")
        self.assertEqual(no_backup["reason_code"], "action_not_licensed")

    def test_content_signature_and_exact_package_hashes_are_verified(self):
        package = self.root / "package"
        binary = package / "bin" / "game.dat"
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(b"official game payload")
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        manifest = self.sign({
            "schema": CONTENT_MANIFEST_SCHEMA,
            "content": {"id": "game.aster", "kind": "game", "title": "Echoes of Aster"},
            "publisher": {"id": "studio.example", "key_id": "studio-key-2026"},
            "attribution": {
                "creator": {"display_name": "Studio Example"},
                "source": {"type": "official_store", "reference": "store.example/game.aster"},
                "copyright": {"notice": "Copyright Studio Example", "license_id": "store-entitlement"},
            },
            "files": [{"path": "bin/game.dat", "size_bytes": len(binary.read_bytes()), "sha256": digest}],
            "capture_policy": {"allowed_actions": ["screenshot"], "denied_actions": ["recording", "streaming"]},
        })
        result = verify_content_manifest(manifest, package, self.trusted_keys)
        self.assertTrue(result["valid"])
        self.assertEqual(result["files_verified"], 1)
        policy = evaluate_capture_policy(result["capture_policy"], "recording", manifest_verified=True)
        self.assertFalse(policy["allowed"])
        self.assertEqual(policy["reason_code"], "capture_restricted")

        binary.write_bytes(b"modified payload")
        tampered = verify_content_manifest(manifest, package, self.trusted_keys)
        self.assertFalse(tampered["valid"])
        self.assertEqual(tampered["reason_code"], "integrity_mismatch")

    def test_combined_verification_binds_license_to_manifest_and_package(self):
        package = self.root / "licensed-package"
        binary = package / "bin" / "game.dat"
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(b"official game payload")
        manifest = self.sign({
            "schema": CONTENT_MANIFEST_SCHEMA,
            "content": {"id": "game.aster", "kind": "game", "title": "Echoes of Aster"},
            "publisher": {"id": "studio.example", "key_id": "studio-key-2026"},
            "attribution": {
                "creator": {"display_name": "Studio Example"},
                "source": {"type": "official_store", "reference": "store.example/game.aster"},
                "copyright": {"notice": "Copyright Studio Example", "license_id": "store-entitlement"},
            },
            "files": [{
                "path": "bin/game.dat",
                "size_bytes": binary.stat().st_size,
                "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            }],
            "capture_policy": {
                "allowed_actions": ["screenshot"],
                "denied_actions": ["recording", "streaming"],
            },
        })
        manifest_digest = hashlib.sha256(canonical(manifest)).hexdigest()
        token = self.entitlement(manifest_sha256=manifest_digest)

        verified = verify_licensed_content(
            token, manifest, package, self.trusted_keys,
            profile_id="profile-ivan", home_device_id=None,
            required_action="launch", now=1_700_000_100,
        )
        self.assertTrue(verified["allowed"])
        self.assertTrue(verified["valid"])
        self.assertEqual(verified["reason_code"], "verified")
        self.assertEqual(verified["manifest_sha256"], manifest_digest)
        self.assertFalse(verified["native_launch_enforcement"])

        capture_token = self.entitlement(
            manifest_sha256=manifest_digest,
            rights=["launch", "capture_recording", "stream"],
        )
        denied_recording = verify_licensed_content(
            capture_token, manifest, package, self.trusted_keys,
            profile_id="profile-ivan", home_device_id=None,
            required_action="capture_recording", now=1_700_000_100,
        )
        denied_streaming = verify_licensed_content(
            capture_token, manifest, package, self.trusted_keys,
            profile_id="profile-ivan", home_device_id=None,
            required_action="stream", now=1_700_000_100,
        )
        self.assertFalse(denied_recording["allowed"])
        self.assertEqual(denied_recording["reason_code"], "capture_restricted")
        self.assertFalse(denied_recording["native_enforcement"])
        self.assertFalse(denied_streaming["allowed"])
        self.assertEqual(denied_streaming["reason_code"], "capture_restricted")

        changed_document = dict(manifest)
        changed_document.pop("signature")
        changed_document["content"] = dict(manifest["content"], title="Substituted title")
        changed_manifest = self.sign(changed_document)
        substituted = verify_licensed_content(
            token, changed_manifest, package, self.trusted_keys,
            profile_id="profile-ivan", home_device_id=None,
            now=1_700_000_100,
        )
        self.assertFalse(substituted["allowed"])
        self.assertEqual(substituted["reason_code"], "manifest_digest_mismatch")

        binary.write_bytes(b"modified game payload")
        tampered_package = verify_licensed_content(
            token, manifest, package, self.trusted_keys,
            profile_id="profile-ivan", home_device_id=None,
            now=1_700_000_100,
        )
        self.assertFalse(tampered_package["allowed"])
        self.assertEqual(tampered_package["reason_code"], "integrity_mismatch")

    def test_combined_verification_rejects_a_different_content_identity(self):
        package = self.root / "identity-package"
        package.mkdir(exist_ok=True)
        manifest = self.sign({
            "schema": CONTENT_MANIFEST_SCHEMA,
            "content": {"id": "game.other", "kind": "game", "title": "Another Game"},
            "publisher": {"id": "studio.example", "key_id": "studio-key-2026"},
            "attribution": {
                "creator": {"display_name": "Studio Example"},
                "source": {"type": "official_store", "reference": "store.example/game.other"},
                "copyright": {"notice": "Copyright Studio Example", "license_id": "store-entitlement"},
            },
            "files": [{"path": "game.dat", "size_bytes": 0, "sha256": hashlib.sha256(b"").hexdigest()}],
        })
        token = self.entitlement(
            manifest_sha256=hashlib.sha256(canonical(manifest)).hexdigest()
        )
        decision = verify_licensed_content(
            token, manifest, package, self.trusted_keys,
            profile_id="profile-ivan", home_device_id=None,
            now=1_700_000_100,
        )
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason_code"], "content_identity_mismatch")

    def test_unverified_capture_policy_is_not_treated_as_permission(self):
        decision = evaluate_capture_policy(
            {"allowed_actions": ["screenshot"], "denied_actions": []},
            "screenshot", manifest_verified=False,
        )
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason_code"], "unverified_capture_policy")
        self.assertFalse(decision["native_enforcement"])

    def test_package_manifest_rejects_path_traversal(self):
        package = self.root / "empty-package"
        package.mkdir(exist_ok=True)
        document = {
            "schema": CONTENT_MANIFEST_SCHEMA,
            "content": {"id": "theme.duck", "kind": "theme", "title": "Theme"},
            "publisher": {"id": "studio.example", "key_id": "studio-key-2026"},
            "attribution": {"creator": {}, "source": {}, "copyright": {}},
            "files": [{"path": "../outside", "size_bytes": 1, "sha256": "b" * 64}],
        }
        signed = self.sign(document)
        with self.assertRaises(RightsError):
            verify_content_manifest(signed, package, self.trusted_keys)

    def test_user_saves_keep_self_declared_attribution_separate(self):
        record = build_user_content_record(
            content_id="save.aster.ivan",
            title="Echoes of Aster save",
            kind="save",
            creator="Ivan",
            source_description="Created by the local game profile",
            copyright_notice="Player-created progress data",
            files=[{"path": "slot-01.sav", "size_bytes": 12, "sha256": "c" * 64}],
        )
        self.assertTrue(record["save_data_separate_from_protected_package"])
        self.assertEqual(record["attribution"]["status"], "self_declared_not_publisher_verified")
        self.assertEqual(record["signature_status"], "unsigned_user_metadata")

    def test_transfer_keeps_signed_documents_and_does_not_grant_rights(self):
        content_manifest = {
            "schema": CONTENT_MANIFEST_SCHEMA,
            "content": {"id": "game.aster", "kind": "game", "title": "Echoes of Aster"},
            "publisher": {"id": "studio.example", "key_id": "studio-key-2026"},
            "signature": {"algorithm": "Ed25519", "value": "unchanged-signature"},
        }
        entitlement = self.entitlement()
        transfer = build_transfer_manifest([{
            "content_manifest": content_manifest,
            "entitlement": entitlement,
            "save_metadata": {"save_id": "save-01", "owner_profile_id": "profile-ivan"},
        }])
        validated = validate_transfer_manifest(transfer)
        self.assertEqual(transfer["items"][0]["entitlement"], entitlement)
        self.assertTrue(validated["valid"])
        self.assertFalse(validated["authorization_granted"])
        self.assertTrue(validated["reverification_required_on_import"])

    def test_audit_log_detects_changed_events_and_refuses_append(self):
        path = self.root / "audit" / "rights.jsonl"
        log = RightsAuditLog(path)
        log.append(
            action="entitlement.verify", content_id="game.aster",
            entitlement_id="entitlement-aster", status="blocked",
            reason_code="wrong_profile",
        )
        self.assertTrue(log.verify()["valid"])
        record = json.loads(path.read_text(encoding="utf-8"))
        record["status"] = "allowed"
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        self.assertFalse(log.verify()["valid"])
        with self.assertRaises(RightsError):
            log.append(
                action="entitlement.verify", content_id="game.aster",
                entitlement_id="entitlement-aster", status="allowed",
                reason_code="verified",
            )


if __name__ == "__main__":
    unittest.main()
