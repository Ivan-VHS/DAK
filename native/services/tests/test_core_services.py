from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

from duckos_services.cli import main as cli_main
from duckos_services.cockos import PipeWireAudioBus
from duckos_services.common import ServiceError
from duckos_services.events import EventBus
from duckos_services.gloverty import PALETTES, audit_palette, contrast_ratio
from duckos_services.illidia import SnapshotStore
from duckos_services.kabon import InputRouter, normalize_chord
from duckos_services.kavun import compute_layout
from duckos_services.po import CommandRegistry
from duckos_services.unify import DuckOSHub


class FakePipeWire:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, command: list[str], **_kwargs) -> SimpleNamespace:
        self.calls.append(command)
        if command[1] == "-o":
            output = "media-player:output_FL\nmedia-player:output_FR\n"
        elif command[1] == "-i":
            output = "speakers:playback_FL\nspeakers:playback_FR\n"
        elif command[1] == "-l":
            output = "media-player:output_FL -> speakers:playback_FL\n"
        else:
            output = ""
        return SimpleNamespace(returncode=0, stdout=output, stderr="")


class EventBusTests(unittest.TestCase):
    def test_filter_history_and_isolated_subscriber_errors(self) -> None:
        bus = EventBus(history_limit=2)
        received = []
        bus.subscribe(received.append, "theme.changed")
        bus.subscribe(lambda _event: (_ for _ in ()).throw(RuntimeError("broken observer")))
        bus.publish("profile.changed", "unify")
        bus.publish("theme.changed", "gloverty", {"theme": "dark"})
        bus.publish("theme.changed", "gloverty", {"theme": "light"})

        self.assertEqual(len(received), 2)
        self.assertEqual(len(bus.history()), 2)
        self.assertEqual(bus.history("theme.changed")[-1].payload["theme"], "light")
        self.assertTrue(bus.last_failures)


class CockosTests(unittest.TestCase):
    def test_routes_only_existing_pipewire_ports(self) -> None:
        runner = FakePipeWire()
        audio = PipeWireAudioBus(runner=runner)
        result = audio.connect(
            "media-player:output_FL",
            "speakers:playback_FL",
        )

        self.assertEqual(result["status"], "linked")
        self.assertEqual(
            runner.calls[-1],
            ["pw-link", "media-player:output_FL", "speakers:playback_FL"],
        )

    def test_rejects_unknown_ports_before_connect(self) -> None:
        runner = FakePipeWire()
        audio = PipeWireAudioBus(runner=runner)
        with self.assertRaises(ServiceError):
            audio.connect("not-a-port", "speakers:playback_FL")
        self.assertEqual(len(runner.calls), 1)


class KavunTests(unittest.TestCase):
    def test_main_stack_fits_output_and_keeps_primary_window(self) -> None:
        result = compute_layout(
            1920,
            1080,
            [{"id": "editor", "role": "primary"}, {"id": "terminal"}, {"id": "docs"}],
            mode="main-stack",
        )

        self.assertEqual(result[0]["id"], "editor")
        self.assertEqual(result[0]["x"], 16)
        for item in result:
            self.assertGreater(item["width"], 0)
            self.assertGreater(item["height"], 0)
            self.assertLessEqual(item["x"] + item["width"], 1904)
            self.assertLessEqual(item["y"] + item["height"], 1064)

    def test_duplicate_window_ids_are_rejected(self) -> None:
        with self.assertRaises(ServiceError):
            compute_layout(800, 600, [{"id": "same"}, {"id": "same"}])


class KaBonTests(unittest.TestCase):
    def test_context_binding_precedes_global_binding(self) -> None:
        router = InputRouter()
        router.bind("editor", "Control+K", "po.open")
        self.assertEqual(normalize_chord("Shift+Ctrl+s"), "Ctrl+Shift+S")
        self.assertEqual(router.dispatch("Ctrl+K", "editor"), "po.open")
        self.assertEqual(router.dispatch("Super+1", "editor"), "kavun.workspace.1")
        self.assertIsNone(router.dispatch("Alt+F4"))

    def test_unregistered_actions_are_rejected(self) -> None:
        with self.assertRaises(ServiceError):
            InputRouter().bind("global", "Ctrl+X", "python.execute")


class GlovertyTests(unittest.TestCase):
    def test_every_palette_meets_declared_text_contrast_thresholds(self) -> None:
        for name in PALETTES:
            with self.subTest(theme=name):
                self.assertTrue(audit_palette(name)["passes"])

    def test_contrast_is_symmetric(self) -> None:
        self.assertAlmostEqual(
            contrast_ratio("#FFFFFF", "#000000"),
            contrast_ratio("#000000", "#FFFFFF"),
        )


class PoTests(unittest.TestCase):
    def test_search_and_confirmation_gate(self) -> None:
        registry = CommandRegistry()
        registry.register(
            "session.restore",
            "Restore session",
            "Restore a saved session snapshot",
            lambda _args: "restored",
            destructive=True,
        )

        self.assertEqual(registry.search("restore")[0]["id"], "session.restore")
        self.assertEqual(
            registry.execute("session.restore")["status"],
            "confirmation-required",
        )
        self.assertEqual(registry.execute("session.restore", confirmed=True), "restored")

    def test_unknown_command_cannot_execute(self) -> None:
        with self.assertRaises(ServiceError):
            CommandRegistry().execute("shell.run", {"command": "rm -rf /"})


class IllidiaTests(unittest.TestCase):
    def test_snapshot_round_trip_and_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = SnapshotStore(Path(temporary))
            saved = store.save({"theme": "dark", "workspace": 2}, "before edit")
            self.assertEqual(store.restore(saved["id"]), {"theme": "dark", "workspace": 2})
            self.assertEqual(store.list()[0]["id"], saved["id"])

            path = Path(temporary) / f"{saved['id']}.json"
            content = path.read_text(encoding="utf-8").replace('"dark"', '"light"')
            path.write_text(content, encoding="utf-8")
            with self.assertRaises(ServiceError):
                store.restore(saved["id"])

    def test_snapshot_rejects_unapproved_state_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = SnapshotStore(Path(temporary))
            with self.assertRaises(ServiceError):
                store.save({"password": "must not be stored"})


class UnifyTests(unittest.TestCase):
    def test_profile_changes_publish_and_persist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            hub = DuckOSHub(Path(temporary))
            events = []
            hub.events.subscribe(events.append, "profile.changed")

            result = hub.switch_profile("focus")
            reopened = DuckOSHub(Path(temporary))

            self.assertEqual(result["theme"], "high-contrast")
            self.assertEqual(result["layout"], "columns")
            self.assertEqual(reopened.settings["profile"], "focus")
            self.assertEqual(len(events), 1)

    def test_snapshot_restores_session_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            hub = DuckOSHub(Path(temporary))
            checkpoint = hub.create_snapshot("before profile change")
            hub.switch_profile("low-power")
            restored = hub.restore_snapshot(checkpoint["id"])
            self.assertEqual(restored["profile"], "balanced")
            self.assertEqual(restored["layout"], "main-stack")


class CliTests(unittest.TestCase):
    def test_po_search_lists_registered_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = io.StringIO()
            with redirect_stdout(output):
                result = cli_main([
                    "--state-dir", temporary, "po", "search", "snapshot",
                ])

        self.assertEqual(result, 0)
        self.assertIn('"id": "snapshot.create"', output.getvalue())
        self.assertIn('"id": "snapshot.restore"', output.getvalue())

    def test_po_restore_is_blocked_without_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = io.StringIO()
            with redirect_stdout(output):
                result = cli_main([
                    "--state-dir", temporary,
                    "po", "run", "snapshot.restore",
                    "--arguments", '{"id":"not-a-real-snapshot"}',
                ])

        self.assertEqual(result, 0)
        self.assertIn('"status": "confirmation-required"', output.getvalue())

    def test_shortcut_binding_survives_new_cli_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with redirect_stdout(io.StringIO()):
                bind_result = cli_main([
                    "--state-dir", temporary,
                    "shortcuts", "bind", "editor", "Ctrl+O", "po.open",
                ])

            output = io.StringIO()
            with redirect_stdout(output):
                dispatch_result = cli_main([
                    "--state-dir", temporary,
                    "shortcuts", "dispatch", "Ctrl+O", "--context", "editor",
                ])

        self.assertEqual(bind_result, 0)
        self.assertEqual(dispatch_result, 0)
        self.assertEqual(output.getvalue().strip(), '"po.open"')


if __name__ == "__main__":
    unittest.main()
