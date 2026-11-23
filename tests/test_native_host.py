from __future__ import annotations

import json
import os
import pwd
import socket
import shutil
import subprocess
import threading
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from duckos.host.config import create_bridge_token, write_policy
from duckos.host.client import NativeHostClient
from duckos.host.runtime import (
    CapabilityPolicy,
    DriverManager,
    HostError,
    NativeHostBroker,
    ProcessSupervisor,
    SafeTerminal,
    current_uid,
)
from duckos.host.server import UnixHostServer, _read_tokens


class FakeProcess:
    def __init__(self):
        self.pid = 424242
        self.returncode = None
        self.waited = False

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.waited = True
        self.returncode = 0
        return self.returncode


class NativeHostTests(unittest.TestCase):
    def test_policy_file_is_schema_checked_and_grants_are_explicit(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "host-policy.json"
            created = write_policy(path, 1001, ["host.read", "terminal.safe"])
            loaded = CapabilityPolicy.load(path)
            self.assertEqual(created["mode"], "0600")
            self.assertTrue(loaded.permits(1001, "host.read"))
            self.assertFalse(loaded.permits(1001, "driver.load"))
            self.assertFalse(loaded.permits(1002, "host.read"))
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_unknown_capabilities_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "host-policy.json"
            path.write_text(json.dumps({
                "schema": "duckos.host-policy.v1",
                "principals": {"1000": ["root.shell"]},
            }), encoding="utf-8")
            path.chmod(0o600)
            with self.assertRaisesRegex(HostError, "unknown capabilities"):
                CapabilityPolicy.load(path)

    def test_mora_token_is_stored_as_digest_and_file_is_private(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tokens.json"
            created = create_bridge_token(path, 1000)
            tokens = _read_tokens(path)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(len(tokens), 1)
            self.assertEqual(next(iter(tokens.values())), 1000)
            self.assertNotIn(created["token"], path.read_text(encoding="utf-8"))

    def test_token_file_rejects_permissive_permissions(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tokens.json"
            create_bridge_token(path, 1000)
            path.chmod(0o644)
            with self.assertRaisesRegex(HostError, "mode 0600"):
                _read_tokens(path)

    def test_terminal_only_executes_named_diagnostics_without_shell(self):
        captured = {}

        def runner(argv, **kwargs):
            captured["argv"] = argv
            captured["kwargs"] = kwargs
            return subprocess.CompletedProcess(argv, 0, "host facts\n", "")

        terminal = SafeTerminal(runner=runner)
        result = terminal.execute("system", current_uid())
        self.assertEqual(result["stdout"], "host facts\n")
        self.assertFalse(result["shell_used"])
        self.assertFalse(captured["kwargs"]["shell"])
        self.assertEqual(captured["argv"][1:], ["-a"])
        self.assertEqual(captured["kwargs"]["timeout"], 5)
        with self.assertRaisesRegex(HostError, "not allowlisted"):
            terminal.execute("bash -c id", current_uid())

    def test_process_supervisor_passes_an_argument_vector_and_drops_root_identity(self):
        executable = Path(sys.executable).resolve()
        fake = FakeProcess()
        captured = {}

        def popen(argv, **kwargs):
            captured["argv"] = argv
            captured["kwargs"] = kwargs
            return fake

        supervisor = ProcessSupervisor(
            {"test-app": {"name": "Test", "argv": [str(executable), "-c", "pass"]}},
            popen=popen,
        )
        record = supervisor.start("test-app", current_uid())
        self.assertEqual(record["status"], "running")
        self.assertEqual(captured["argv"], [str(executable), "-c", "pass"])
        self.assertFalse(captured["kwargs"]["shell"])
        self.assertTrue(captured["kwargs"]["start_new_session"])
        self.assertEqual(captured["kwargs"]["stdin"], subprocess.DEVNULL)
        if os.geteuid() == 0:
            account = pwd.getpwuid(current_uid())
            expected_groups = sorted(set(os.getgrouplist(account.pw_name, account.pw_gid)) - {account.pw_gid})
            self.assertEqual(captured["kwargs"]["user"], current_uid())
            self.assertEqual(captured["kwargs"]["group"], account.pw_gid)
            self.assertEqual(captured["kwargs"]["extra_groups"], expected_groups)

    def test_process_sessions_are_owned_and_can_be_stopped(self):
        if os.name != "posix":
            self.skipTest("POSIX process groups are required")
        supervisor = ProcessSupervisor({
            "sleep": {
                "name": "Temporary test session",
                "argv": [sys.executable, "-c", "import time; time.sleep(30)"],
            },
        })
        record = supervisor.start("sleep", current_uid())
        self.assertEqual(supervisor.list(current_uid())[0]["session_id"], record["session_id"])
        with self.assertRaisesRegex(HostError, "not found or is not owned"):
            supervisor.stop(record["session_id"], current_uid() + 100000)
        stopped = supervisor.stop(record["session_id"], current_uid())
        self.assertEqual(stopped["status"], "exited")

    def test_application_specific_capability_is_required(self):
        uid = 1001
        policy = CapabilityPolicy({uid: {"session.spawn"}})
        processes = ProcessSupervisor({
            "compositor": {
                "name": "Compositor",
                "argv": [sys.executable, "-c", "pass"],
                "capabilities": ["display.manage"],
            },
        })
        broker = NativeHostBroker(policy, processes=processes)
        with self.assertRaisesRegex(HostError, "capability denied: display.manage"):
            broker.dispatch(uid, {
                "id": 1,
                "method": "session.start",
                "params": {"application_id": "compositor"},
            })

    def test_arbitrary_host_command_and_driver_name_are_denied(self):
        uid = 1001
        policy = CapabilityPolicy({uid: {"terminal.safe", "driver.inspect", "driver.load"}})
        broker = NativeHostBroker(policy)
        with self.assertRaisesRegex(HostError, "not allowlisted"):
            broker.dispatch(uid, {
                "id": 1,
                "method": "terminal.run",
                "params": {"command_id": "sh -c whoami"},
            })
        with self.assertRaisesRegex(HostError, "allowlist"):
            broker.dispatch(uid, {
                "id": 2,
                "method": "driver.load",
                "params": {"category": "graphics", "module": "arbitrary.ko"},
            })

    def test_unknown_rpc_fields_and_methods_are_rejected(self):
        broker = NativeHostBroker()
        with self.assertRaisesRegex(HostError, "only id, method and params"):
            broker.dispatch(current_uid(), {
                "id": 1, "method": "host.status", "command": "rm -rf /",
            })
        with self.assertRaisesRegex(HostError, "unknown host RPC"):
            broker.dispatch(current_uid(), {"id": 2, "method": "shell.exec", "params": {}})

    def test_driver_inventory_is_read_only(self):
        report = DriverManager().list()
        self.assertEqual(report["schema"], "duckos.driver-inventory.v1")
        self.assertIn("modules", report)
        self.assertTrue(all("loaded" in item for item in report["modules"]))

    def test_unix_socket_uses_peer_credentials_and_client_rpc(self):
        if not hasattr(socket, "SO_PEERCRED"):
            self.skipTest("Linux SO_PEERCRED is required")
        with tempfile.TemporaryDirectory() as temporary:
            socket_path = Path(temporary) / "host.sock"
            broker = NativeHostBroker(CapabilityPolicy.for_current_user())
            server = UnixHostServer(socket_path, broker, mode=0o600)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                result = NativeHostClient(socket_path).call("host.status")
                self.assertIn(result["host"], {"Linux", "Darwin", "FreeBSD"})
                self.assertEqual(result["uid"], current_uid())
                self.assertTrue(result["process_supervisor"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
