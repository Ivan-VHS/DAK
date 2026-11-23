"""Optional native Qt Quick scene preview for Mora.

QML is a native Qt declarative UI language. This window is not a web page
and does not embed a WebView or browser engine.
"""

from __future__ import annotations

import sys

QML_SOURCE = """
import QtQuick
import QtQuick.Controls

ApplicationWindow {
    id: window
    width: 960
    height: 640
    minimumWidth: 720
    minimumHeight: 480
    visible: true
    title: "Mora · Qt Quick scene"
    color: "#080808"

    Rectangle {
        anchors.fill: parent
        anchors.margins: 30
        radius: 24
        color: "#151515"
        border.width: 1
        border.color: "#3A3A3A"

        Column {
            anchors.fill: parent
            anchors.margins: 34
            spacing: 20

            Text {
                text: "DUCKOS · MORA"
                color: "#FFD400"
                font.pixelSize: 14
                font.bold: true
            }

            Text {
                text: "Native Qt Quick scene"
                color: "#FFFFFF"
                font.pixelSize: 34
                font.bold: true
            }

            Text {
                text: "Declarative animation and scene rendering without HTML or WebView."
                color: "#E5E5E5"
                font.pixelSize: 15
                wrapMode: Text.WordWrap
            }

            Rectangle {
                width: parent.width
                height: 180
                radius: 18
                color: "#242424"
                border.width: 1
                border.color: "#3A3A3A"

                Rectangle {
                    id: pulse
                    width: 110
                    height: 110
                    radius: 55
                    anchors.centerIn: parent
                    color: "#FFD400"
                    opacity: 0.82

                    SequentialAnimation on scale {
                        loops: Animation.Infinite
                        NumberAnimation { to: 1.12; duration: 1100; easing.type: Easing.InOutSine }
                        NumberAnimation { to: 0.90; duration: 1100; easing.type: Easing.InOutSine }
                    }
                    SequentialAnimation on opacity {
                        loops: Animation.Infinite
                        NumberAnimation { to: 1.0; duration: 1100 }
                        NumberAnimation { to: 0.72; duration: 1100 }
                    }
                }
            }

            Item { height: 12 }

            Text {
                text: "Qt Quick · native scene · user-space"
                color: "#A6A6A6"
                font.pixelSize: 12
            }
        }
    }
}
"""


def main() -> int:
    try:
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtQml import QQmlApplicationEngine
    except ImportError as error:
        raise SystemExit(
            "The Mora scene preview requires the native-ui extra. "
            "Install with: python -m pip install 'duckos-build-tools[native-ui]'. "
            f"Import details: {error}"
        ) from error

    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.loadData(QML_SOURCE.encode("utf-8"))
    if not engine.rootObjects():
        raise RuntimeError("Qt Quick could not create the native Mora scene.")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
