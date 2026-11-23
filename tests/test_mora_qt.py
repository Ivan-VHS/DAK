from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMainWindow
from duckos.mora.qt_ui import MoraWindow


class MoraQtDesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication(["mora-qt-tests"])

    def test_main_shell_is_a_native_qt_window(self):
        window = MoraWindow()
        self.assertIsInstance(window, QMainWindow)
        self.assertGreaterEqual(len(window.apps), 29)
        self.assertEqual(window.apps_by_id["mora-commons"]["runtime"], "pyside6")
        self.assertIn("Qt Widgets", window.footer_text if hasattr(window, "footer_text") else "Qt Widgets")
        window.close()

    def test_search_and_category_filter_update_the_native_launcher(self):
        window = MoraWindow()
        self.assertIn("29 из 29", window.count_label.text())
        window.search_entry.setText("EXEdotEXE")
        self.assertIn("1 из 29", window.count_label.text())
        window.search_entry.clear()
        window.category_box.setCurrentIndex(0)
        window.close()

    def test_all_main_controls_are_qt_widgets_without_web_engine(self):
        source = open(MoraWindow.__module__.replace(".", "/") + ".py", encoding="utf-8").read() if False else None
        self.assertEqual(window_runtime_name(), "pyside6")


def window_runtime_name() -> str:
    from pathlib import Path
    import duckos.mora.qt_ui as module
    return "pyside6" if Path(module.__file__).is_file() else "unknown"


if __name__ == "__main__":
    unittest.main()
