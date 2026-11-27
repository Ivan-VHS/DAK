from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dakos.desktop.service import StartupManager, audit_desktop, list_desktop_items, move_desktop_items_to_inbox


class DesktopAuditTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.desktop = self.home / "Desktop"
        self.desktop.mkdir()

    def test_audit_is_read_only_and_flags_temporary_names(self):
        (self.desktop / "Screenshot 2026-11-23.png").write_bytes(b"image")
        (self.desktop / "project-notes.md").write_text("notes", encoding="utf-8")
        before = sorted(item.name for item in self.desktop.iterdir())
        report = audit_desktop(self.home)
        self.assertEqual(report["schema"], "dakos.desktop-audit.v1")
        self.assertEqual(report["desktop"]["count"], 2)
        self.assertTrue(any(item["looks_temporary"] for item in report["desktop"]["items"]))
        self.assertEqual(report["operations_performed"]["files_deleted"], 0)
        self.assertEqual(sorted(item.name for item in self.desktop.iterdir()), before)

    def test_move_to_inbox_preserves_files_and_never_overwrites(self):
        (self.desktop / "notes.txt").write_text("new", encoding="utf-8")
        inbox = self.home / "Inbox"
        inbox.mkdir()
        (inbox / "notes.txt").write_text("existing", encoding="utf-8")
        result = move_desktop_items_to_inbox(["notes.txt"], self.home)
        self.assertEqual(len(result["moved"]), 1)
        self.assertEqual((inbox / "notes.txt").read_text(encoding="utf-8"), "existing")
        self.assertEqual((inbox / "notes (2).txt").read_text(encoding="utf-8"), "new")
        self.assertFalse((self.desktop / "notes.txt").exists())
        self.assertEqual(result["deleted"], 0)
        self.assertEqual(result["overwritten"], 0)

    def test_move_rejects_paths_folders_and_symlinks(self):
        (self.desktop / "folder").mkdir()
        (self.desktop / "safe.txt").write_text("ok", encoding="utf-8")
        try:
            (self.desktop / "link.txt").symlink_to(self.desktop / "safe.txt")
        except (OSError, NotImplementedError):
            pass
        result = move_desktop_items_to_inbox(["../outside.txt", "folder", "safe.txt", "link.txt"], self.home)
        self.assertEqual(len(result["moved"]), 1)
        rejected = {row["name"] for row in result["rejected"]}
        self.assertIn("../outside.txt", rejected)
        self.assertIn("folder", rejected)
        self.assertEqual((self.home / "Inbox" / "safe.txt").read_text(encoding="utf-8"), "ok")

    def test_item_limit_is_validated(self):
        with self.assertRaises(ValueError):
            list_desktop_items(self.home, max_items=0)


class StartupManagerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.startup = self.home / ".config" / "autostart"
        self.disabled = self.home / ".config" / "dakos" / "disabled-autostart"
        self.startup.mkdir(parents=True)
        (self.startup / "backup-agent.desktop").write_text("[Desktop Entry]\nName=Backup Agent\n", encoding="utf-8")
        self.manager = StartupManager(
            self.home, platform_name="Linux", startup_dir=self.startup,
            disabled_dir=self.disabled, backup_dir=self.home / ".config" / "dakos" / "startup-backups",
        )

    def test_disable_and_restore_are_reversible(self):
        entry_id = StartupManager._id("folder", "backup-agent.desktop")
        self.assertTrue(self.manager.list_entries()[0]["enabled"])
        disabled = self.manager.set_enabled(entry_id, False)
        self.assertFalse(disabled["enabled"])
        self.assertTrue((self.disabled / "backup-agent.desktop").is_file())
        self.assertFalse(self.manager.list_entries()[0]["enabled"])
        restored = self.manager.set_enabled(entry_id, True)
        self.assertTrue(restored["enabled"])
        self.assertTrue((self.startup / "backup-agent.desktop").is_file())
        self.assertFalse((self.disabled / "backup-agent.desktop").exists())

    def test_rejects_traversal_and_unknown_scope(self):
        with self.assertRaises(ValueError):
            self.manager.set_enabled("folder:%2E%2E%2Fstartup", False)
        with self.assertRaises(ValueError):
            self.manager.set_enabled("machine:system-entry", False)

    def test_restore_refuses_to_overwrite_existing_item(self):
        entry_id = StartupManager._id("folder", "backup-agent.desktop")
        self.manager.set_enabled(entry_id, False)
        (self.startup / "backup-agent.desktop").write_text("another entry", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.manager.set_enabled(entry_id, True)
        self.assertTrue((self.disabled / "backup-agent.desktop").exists())


if __name__ == "__main__":
    unittest.main()
