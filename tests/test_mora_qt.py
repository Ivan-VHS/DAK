from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    import PySide6
except ImportError:
    PySide6 = None

if PySide6 is not None:
    from PySide6.QtWidgets import QApplication, QMainWindow
    from duckos.mora.qt_ui import MoraWindow
else:
    QApplication = None
    QMainWindow = None
    MoraWindow = None


@unittest.skipUnless(PySide6 is not None, "Install the native-ui extra to run Qt tests")
class MoraQtDesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication(["mora-qt-tests"])

    def test_main_shell_is_a_native_qt_window(self):
        window = MoraWindow()
        self.assertIsInstance(window, QMainWindow)
        self.assertGreaterEqual(len(window.apps), 29)
        self.assertEqual(window.apps_by_id["mora-commons"]["runtime"], "pyside6")
        self.assertEqual(window.windowTitle(), "Mora — DuckOS")
        window.close()

    def test_search_updates_the_native_launcher(self):
        window = MoraWindow()
        self.assertIn("29 из 29", window.count_label.text())
        window.search_entry.setText("EXEdotEXE")
        self.assertIn("1 из 29", window.count_label.text())
        window.close()

    def test_main_source_has_no_browser_engine_or_tk_runtime(self):
        import duckos.mora.qt_ui as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("QWebEngine", source)
        self.assertNotIn("QWebView", source)
        self.assertNotIn("tkinter", source.casefold())
        self.assertIn("QApplication", source)


if __name__ == "__main__":
    unittest.main()
