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
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QMainWindow, QPlainTextEdit
    from duckos.mora.controls import MoraSlider
    from duckos.mora.qt_ui import MoraWindow
else:
    Qt = None
    QTest = None
    QApplication = None
    QDialog = None
    QLineEdit = None
    QMainWindow = None
    QPlainTextEdit = None
    MoraSlider = None
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

    def test_shared_slider_keeps_drag_value_exact_and_bounded(self):
        slider = MoraSlider(
            "Масштаб интерфейса",
            80,
            140,
            100,
            suffix="%",
            step=5,
            precise_step=1,
        )
        slider.show()
        slider.track.setFocus()

        QTest.keyClick(slider.track, Qt.Key.Key_Right)
        self.assertEqual(slider.value(), 105)
        QTest.keyClick(
            slider.track,
            Qt.Key.Key_Right,
            Qt.KeyboardModifier.ShiftModifier,
        )
        self.assertEqual(slider.value(), 106)
        QTest.keyClick(slider.track, Qt.Key.Key_End)
        self.assertEqual(slider.value(), 140)
        QTest.keyClick(slider.track, Qt.Key.Key_Home)
        self.assertEqual(slider.value(), 80)

        slider.value_input.setValue(125)
        self.assertEqual(slider.value(), 125)
        self.assertEqual(slider.value_input.width(), 88)
        slider.setValue(10_000)
        self.assertEqual(slider.value(), 140)
        slider.close()

    def test_native_app_windows_are_modeless_resizable_and_reused(self):
        window = MoraWindow()
        window.show()
        window.open_app("workspace")
        settings = window._app_dialogs["workspace"]
        self.assertIsInstance(settings, QDialog)
        self.assertFalse(settings.isModal())
        self.assertTrue(settings.isVisible())
        self.assertTrue(settings.isSizeGripEnabled())
        self.assertTrue(
            bool(settings.windowFlags() & Qt.WindowType.WindowMinMaxButtonsHint)
        )

        window.open_app("security")
        security = window._app_dialogs["security"]
        self.assertFalse(security.isModal())
        self.assertIsNot(settings, security)
        window.open_app("workspace")
        self.assertIs(window._app_dialogs["workspace"], settings)

        settings.close()
        security.close()
        self.application.processEvents()
        window.close()

    def test_scale_preview_and_glass_material_keep_an_opaque_fallback(self):
        window = MoraWindow()
        window._preview_ui_scale(125)
        self.assertIn("font-size: 12.50pt;", window.styleSheet())
        self.assertIn("background: #151515;", window.styleSheet())
        self.assertIn("background: rgba(21, 21, 21, 236);", window.styleSheet())
        window._restore_ui_scale_preview()
        window.close()

    def test_enter_prepares_a_ukrainian_intent_without_bypassing_approval(self):
        window = MoraWindow()
        window.show()
        window.open_app("mora-ai")
        dialog = window._app_dialogs["mora-ai"]
        query = dialog.findChild(QLineEdit)
        output = dialog.findChild(QPlainTextEdit)
        self.assertIsNotNone(query)
        self.assertIsNotNone(output)
        query.setText("увімкни режим фокусу")
        QTest.keyClick(query, Qt.Key.Key_Return)
        self.application.processEvents()
        self.assertIn("focusMode", output.toPlainText())
        self.assertIn("План подготовлен", output.toPlainText())
        dialog.close()
        window.close()

    def test_qt_quick_scene_compiles_to_a_native_qml_window(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlApplicationEngine
        from duckos.mora.qml_scene import QML_SOURCE

        engine = QQmlApplicationEngine()
        engine.loadData(QML_SOURCE.encode("utf-8"), QUrl("mora-scene.qml"))
        self.assertTrue(engine.rootObjects())
        self.assertIn("ApplicationWindow", QML_SOURCE)
        self.assertNotIn("<html", QML_SOURCE.casefold())

    def test_main_source_has_no_browser_engine_or_tk_runtime(self):
        import duckos.mora.qt_ui as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("QWebEngine", source)
        self.assertNotIn("QWebView", source)
        self.assertNotIn("tkinter", source.casefold())
        self.assertIn("QApplication", source)


if __name__ == "__main__":
    unittest.main()
