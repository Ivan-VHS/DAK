from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from dak.cli import main
from dak.terminal import CommandSpec, TerminalInputError, TerminalService
from dak.terminal.service import _tokenize


class ExtendedTerminalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.state = Path(temporary.name) / "terminal-state"
        self.terminal = TerminalService(state_dir=self.state)

    def test_status_reports_a_restricted_command_runtime(self):
        result = self.terminal.execute("status", record_history=False)["result"]
        self.assertEqual(result["schema"], "dak.terminal-status.v1")
        self.assertEqual(result["runtime_state"], "ready")
        self.assertFalse(result["execution_policy"]["host_shell"])
        self.assertFalse(result["execution_policy"]["arbitrary_process_launch"])

    def test_command_tokenizer_preserves_quoted_windows_paths(self):
        path = r"C:\Program Files\DAK Tools\inspect.exe"
        self.assertEqual(_tokenize('bridge inspect "' + path + '"'), [
            "bridge", "inspect", path
        ])

    def test_unregistered_shell_syntax_is_not_executed(self):
        marker = self.state.parent / "should-not-exist.txt"
        command = "help; python -c 'from pathlib import Path; Path(" + repr(str(marker)) + ").write_text(" + repr("bad") + ")'"
        with self.assertRaises(TerminalInputError):
            self.terminal.execute(command)
        self.assertFalse(marker.exists())

    def test_alias_expands_to_a_registered_command_and_persists(self):
        self.terminal.execute("alias v version", record_history=False)
        result = self.terminal.execute("v", record_history=False)
        self.assertEqual(result["command"], ["version"])
        self.assertEqual(result["result"]["project"], "DAK")
        reloaded = TerminalService(state_dir=self.state)
        self.assertEqual(reloaded.execute("v", record_history=False)["command"], ["version"])

    def test_alias_cannot_shadow_a_builtin_command(self):
        with self.assertRaises(TerminalInputError):
            self.terminal.execute("alias status version", record_history=False)

    def test_history_redacts_secret_options(self):
        with self.assertRaises(TerminalInputError):
            self.terminal.execute("help --token top-secret-value")
        entries = self.terminal.execute("history show", record_history=False)["result"]["entries"]
        self.assertEqual(len(entries), 1)
        self.assertIn("[redacted]", entries[0]["command"])
        self.assertNotIn("top-secret-value", json.dumps(entries))

    def test_history_clear_leaves_no_clear_command_record(self):
        self.terminal.execute("version")
        self.terminal.execute("history clear")
        self.assertEqual(self.terminal._read_history(), [])

    def test_config_changes_are_validated_and_persisted(self):
        self.terminal.execute('config set prompt "duck dev"', record_history=False)
        self.terminal.execute("config set history_limit 25", record_history=False)
        reloaded = TerminalService(state_dir=self.state)
        self.assertEqual(reloaded.prompt, "duck dev")
        self.assertEqual(reloaded.config["history_limit"], 25)
        with self.assertRaises(TerminalInputError):
            reloaded.execute('config set prompt "' + chr(27) + '[31m"', record_history=False)

    def test_command_completion_follows_the_registered_command_tree(self):
        self.assertEqual(self.terminal.completion_candidates("", "br"), ["bridge"])
        self.assertEqual(self.terminal.completion_candidates("bridge ", "pl"), ["plan"])
        self.assertEqual(self.terminal.completion_candidates("history ", ""), ["clear", "show"])

    def test_extensions_require_explicit_registration(self):
        command = CommandSpec(
            ("sample", "check"),
            "Test-only extension command.",
            "sample check",
            lambda arguments: {"arguments": arguments, "available": True},
        )
        extended = TerminalService(
            state_dir=self.state / "extended",
            extra_commands=[command],
        )
        result = extended.execute("sample check hello", record_history=False)
        self.assertEqual(result["result"], {"arguments": ["hello"], "available": True})


    def test_state_reader_rejects_nested_duplicate_json_keys(self):
        source = self.state / "duplicate.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('{"outer":{"value":1,"value":2}}', encoding="utf-8")
        with self.assertRaisesRegex(TerminalInputError, "duplicate object key"):
            self.terminal._read_json(source, 1024, {})

    def test_state_reader_rejects_non_finite_json_numbers(self):
        source = self.state / "nonfinite.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        for number in ("NaN", "Infinity", "-Infinity", "1e999"):
            with self.subTest(number=number):
                source.write_text('{"value":' + number + "}", encoding="utf-8")
                with self.assertRaises(TerminalInputError):
                    self.terminal._read_json(source, 1024, {})

    def test_state_reader_enforces_json_nesting_depth(self):
        source = self.state / "nested.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        depth = 129
        source.write_text("[" * depth + "0" + "]" * depth, encoding="utf-8")
        with self.assertRaisesRegex(TerminalInputError, "nesting exceeds"):
            self.terminal._read_json(source, 4096, {})

    def test_state_reader_ignores_brackets_inside_json_strings(self):
        source = self.state / "strings.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        content = '{"text":"' + ("[{" * 1000) + '"}'
        source.write_text(content, encoding="utf-8")
        self.assertEqual(self.terminal._read_json(source, 8192, {})["text"], "[{" * 1000)

    def test_state_reader_handles_escaped_quotes_inside_json_strings(self):
        source = self.state / "escaped-strings.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        value = 'quoted " text with braces { [ ] } and backslash \\ marker'
        source.write_text(json.dumps({"text": value}), encoding="utf-8")
        self.assertEqual(self.terminal._read_json(source, 1024, {})["text"], value)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are POSIX-only")
    def test_state_reader_rejects_fifo_without_blocking(self):
        self.state.mkdir(parents=True)
        fifo = self.state / "history.json"
        os.mkfifo(fifo)
        with self.assertRaisesRegex(TerminalInputError, "regular file"):
            self.terminal._read_json(fifo, 1024, [])

    def test_state_reader_rejects_symlinked_parent_directory(self):
        target = self.state.parent / "external-state"
        target.mkdir()
        linked_state = self.state.parent / "linked-state"
        linked_state.symlink_to(target, target_is_directory=True)
        service = TerminalService.__new__(TerminalService)
        service.state_dir = linked_state
        with self.assertRaisesRegex(TerminalInputError, "directory must not be a symlink"):
            service._read_json(linked_state / "config.json", 1024, {})

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are POSIX-only")
    def test_module_order_rejects_fifo_without_blocking(self):
        source = self.state.parent / "module-order.json"
        os.mkfifo(source)
        with self.assertRaisesRegex(TerminalInputError, "regular file"):
            self.terminal.execute("module order " + str(source), record_history=False)

    def test_module_order_rejects_symlinked_input(self):
        target = self.state.parent / "modules.json"
        target.write_text('[]', encoding="utf-8")
        linked = self.state.parent / "modules-link.json"
        linked.symlink_to(target)
        with self.assertRaisesRegex(TerminalInputError, "symlinks"):
            self.terminal.execute("module order " + str(linked), record_history=False)

    def test_module_order_rejects_oversized_file(self):
        from dak.terminal import service as terminal_module
        source = self.state.parent / "large-modules.json"
        source.write_text('[]', encoding="utf-8")
        previous = terminal_module.MAX_INPUT_JSON_BYTES
        terminal_module.MAX_INPUT_JSON_BYTES = 1
        try:
            with self.assertRaisesRegex(TerminalInputError, "size limit"):
                self.terminal.execute("module order " + str(source), record_history=False)
        finally:
            terminal_module.MAX_INPUT_JSON_BYTES = previous

    def test_terminal_command_is_wired_to_the_existing_cli(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["terminal", "run", "version"])
        self.assertEqual(status, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["schema"], "dak.terminal-result.v1")
        self.assertEqual(payload["result"]["project"], "DAK")


if __name__ == "__main__":
    unittest.main()
