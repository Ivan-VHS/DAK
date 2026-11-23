"""Shared native controls for the Mora desktop.

All range controls use the same pointer, keyboard, wheel and exact-value rules.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class _SliderTrack(QSlider):
    """A native slider with predictable coarse and fine keyboard movement."""

    def __init__(self, precise_step: int, parent: QWidget | None = None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._precise_step = max(1, int(precise_step))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setTracking(True)

    def keyPressEvent(self, event: object) -> None:
        key = event.key()
        directions = {
            Qt.Key.Key_Left: -1,
            Qt.Key.Key_Down: -1,
            Qt.Key.Key_Right: 1,
            Qt.Key.Key_Up: 1,
        }
        direction = directions.get(key)
        if direction is not None:
            fine = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            step = self._precise_step if fine else max(1, self.singleStep())
            self.setValue(self.value() + direction * step)
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event: object) -> None:
        delta = event.angleDelta().y()
        if not delta:
            delta = event.pixelDelta().y()
        if not delta:
            event.ignore()
            return

        fine = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        step = self._precise_step if fine else max(1, self.singleStep())
        notches = max(1, round(abs(delta) / 120))
        direction = 1 if delta > 0 else -1
        self.setValue(self.value() + direction * step * notches)
        event.accept()


class MoraSlider(QWidget):
    """A labelled range control with a fixed-width, precisely editable value."""

    valueChanged = Signal(int)

    def __init__(
        self,
        title: str,
        minimum: int,
        maximum: int,
        value: int,
        *,
        suffix: str = "",
        step: int = 1,
        precise_step: int = 1,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if minimum > maximum:
            raise ValueError("minimum must not exceed maximum")
        if step < 1 or precise_step < 1:
            raise ValueError("slider steps must be positive")

        self.setObjectName("MoraSlider")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAccessibleName(title)

        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("SliderTitle")

        self.track = _SliderTrack(precise_step, self)
        self.track.setObjectName("SliderTrack")
        self.track.setRange(minimum, maximum)
        self.track.setSingleStep(step)
        self.track.setPageStep(max(step, step * 5))
        self.track.setValue(max(minimum, min(maximum, int(value))))
        self.track.setAccessibleName(title)
        self.track.setAccessibleDescription(
            f"Диапазон от {minimum} до {maximum}. "
            "Стрелки меняют значение; Shift вместе со стрелкой задаёт точный шаг. "
            "Home и End устанавливают границы."
        )

        self.value_input = QSpinBox(self)
        self.value_input.setObjectName("SliderValue")
        self.value_input.setRange(minimum, maximum)
        self.value_input.setSingleStep(precise_step)
        self.value_input.setSuffix(suffix)
        self.value_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.value_input.setKeyboardTracking(False)
        self.value_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.value_input.setFixedWidth(88)
        self.value_input.setAccessibleName(f"{title}: точное значение")
        self.value_input.setValue(self.track.value())

        heading = QHBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.setSpacing(12)
        heading.addWidget(self.title_label, 1)
        heading.addWidget(self.value_input, 0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        layout.addLayout(heading)
        layout.addWidget(self.track)

        self.title_label.setBuddy(self.track)
        self.track.valueChanged.connect(self._from_track)
        self.value_input.valueChanged.connect(self._from_input)

    def value(self) -> int:
        return self.track.value()

    def setValue(self, value: int) -> None:
        self.track.setValue(max(self.track.minimum(), min(self.track.maximum(), int(value))))

    def _from_track(self, value: int) -> None:
        self.value_input.setValue(value)
        self.valueChanged.emit(value)

    def _from_input(self, value: int) -> None:
        self.track.setValue(value)
