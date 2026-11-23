"""Native Qt desktop shell for Mora.

The main desktop is built from PySide6 widgets. It does not create a browser,
WebView, HTML document, JavaScript runtime or DOM tree.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QDateTime, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .controls import MoraSlider
from .model import (
    build_intent_plan,
    calculate_sha256,
    create_recovery_snapshot,
    filter_commons_apps,
    load_preferences,
    normalize_preferences,
    save_preferences,
    validate_recovery_snapshot,
)

PAGE = "#080808"
SURFACE = "#151515"
ELEVATED = "#242424"
BORDER = "#3A3A3A"
TEXT = "#FFFFFF"
SECONDARY = "#E5E5E5"
MUTED = "#A6A6A6"
ACCENT = "#FFD400"
ACCENT_HOVER = "#FFE45C"
ON_ACCENT = "#080808"

APP_DESCRIPTIONS = {
    "cockos": ("Аудио и музыкальные проекты", "Карточка аудио-направления. Аудиодвижок, запись и управление системными аудиосессиями подключаются отдельными службами."),
    "kavun": ("Фотографии и медиатека", "Карточка медиатеки. Индексация фотографий, импорт и обработка требуют отдельного нативного модуля."),
    "kabon": ("Личные финансы", "Карточка финансового пространства. Банковские подключения и платёжные операции здесь не выполняются."),
    "gloverty": ("Автоматизация задач", "Каталог автоматизаций. Произвольные скрипты не исполняются; действия должны проходить через проверяемые системные службы."),
    "po": ("Компас и ориентирование", "Карточка инструмента ориентирования. Работа с датчиками и геопозицией требует нативных драйверов и брокера разрешений."),
    "illidia": ("Игры и библиотека", "Каталог игрового направления. Запуск игр и управление графическими API из этой панели не выполняются."),
    "unify": ("Подключённые устройства", "Панель устройств. Подключение и управление периферией остаются задачей отдельных служб и драйверов."),
    "sestem": ("Системная панель", "Локальный обзор рабочего пространства и документированного состояния компонентов DuckOS."),
    "setupup": ("Первичная настройка", "Настройки пользовательской среды Mora. Установка или изменение системного образа из этой панели не выполняются."),
    "orriganize": ("Проекты и задачи", "Точка входа для организации проектов. Полноценное хранение задач и синхронизация пока не подключены."),
    "abriganza": ("Архивы и файлы", "Инструменты выбранных пользовательских файлов. Архивы не распаковываются и не исполняются."),
    "olaab": ("Мультимедиа", "Карточка мультимедийной библиотеки. Кодирование и воспроизведение требуют отдельных нативных модулей."),
    "concrete-thump": ("Ритм и темп", "Подготовка музыкальных профилей. Аудиосинтез и маршрутизация звука этой панелью не заявлены."),
    "seu-beu": ("Обмен и приватность", "Локальный список проверок перед передачей данных. Шифрование и подтверждение личности требуют отдельных служб."),
    "love-il": ("Личный дневник", "Карточка приватных записей. Зашифрованное хранилище и синхронизация ещё не подключены."),
    "poi": ("Быстрые заметки", "Точка входа для коротких заметок. Постоянное хранилище приложения пока не реализовано."),
    "poi-2": ("База знаний", "Карточка базы знаний. Индексация, полнотекстовый поиск и синхронизация требуют отдельных модулей."),
    "po-2": ("Маршруты и точки", "Панель планирования маршрутов. GPS, карты и навигационные датчики пока не подключены."),
    "gamecharager": ("Игровая библиотека", "Локальная карточка игрового каталога и точка входа для безопасной диагностики файлов."),
    "exedotexe": ("Инспектор Windows-файлов", "Проверка заголовков PE/ELF и подготовка диагностических сведений без выполнения выбранного файла."),
    "mora-ai": ("Локальные планы действий", "Ограниченный набор правил для безопасных настроек и открытия встроенных панелей. Внешняя языковая модель не подключена."),
    "security": ("Профиль разрешений", "Список пользовательских предпочтений. Переключатели не предоставляют системные права и не заменяют брокер возможностей."),
    "updates": ("Резервная копия настроек", "Экспорт и восстановление только настроек Mora. Обновление системных разделов и загрузочный откат не реализованы."),
    "runtime": ("Совместимость приложений", "Диагностика локальных PE/ELF-файлов. Выполнение выбранных программ и установка runtime отключены."),
    "workspace": ("Управление рабочей средой", "Параметры интерфейса Mora: фокус, плотность отображения и локальный профиль предпочтений."),
    "provenance": ("Проверка целостности", "Вычисление SHA-256 выбранного файла. Хэш не доказывает автора, подпись или подлинность источника."),
    "mora-boost": ("Игровая лаборатория", "Точка интеграции с отдельным OPlague workbench. Mora не меняет драйверы, частоты, напряжение или параметры ядра."),
    "desktop": ("Обслуживание рабочего пространства", "Нативный аудит пользовательского рабочего стола и отдельная утилита Duck Desktop."),
    "mora-commons": ("Каталог Mora Commons", "Локальный каталог приложений из поставляемых JSON-данных. Запись каталога не означает, что приложение установлено."),
}

MATURITY_LABELS = {
    "partial_local_workspace": "Нативная рабочая область · частично",
    "partial_local_rules": "Локальные правила · частично",
    "shell_policy_only": "Профиль оболочки",
    "shell_snapshot_only": "Резервная копия настроек",
    "partial_pe_cli_and_prefix_foundation": "Диагностика совместимости",
    "shell_preferences": "Настройки оболочки",
    "sha256_only": "SHA-256",
    "external_native_workbench": "Внешний нативный инструмент",
    "partial_native_userland_tool": "Нативная пользовательская утилита",
    "implemented_local_catalog": "Локальный каталог",
}


def _read_packaged_json(filename: str, fallback: dict[str, Any]) -> dict[str, Any]:
    path = Path(__file__).with_name("data") / filename
    try:
        if path.is_symlink() or path.stat().st_size > 4 * 1024 * 1024:
            return fallback
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return fallback
    return value if isinstance(value, dict) else fallback


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)


class AppCard(QFrame):
    activated = Signal()

    def mouseReleaseEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit()
        super().mouseReleaseEvent(event)


class MoraWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.preferences = load_preferences()
        self._display_scale = self.preferences["appearance"]["uiScale"]
        self._app_dialogs: dict[str, QDialog] = {}
        self.theme = _read_packaged_json("theme.json", {})
        glass = self.theme.get("materials", {}).get("glass", {})
        self.glass_surface = str(glass.get("surface", "rgba(21, 21, 21, 236)"))
        self.glass_border = str(glass.get("border", "rgba(255, 255, 255, 30)"))
        registry = _read_packaged_json("apps.json", {"built_in_apps": []})
        commons = _read_packaged_json("commons-catalog.json", {"apps": [], "categories": []})
        self.apps = list(registry.get("built_in_apps", []))
        self.apps_by_id = {str(item.get("id")): item for item in self.apps}
        self.commons = commons
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(15_000)
        self._clock_timer.timeout.connect(self._update_clock)

        self.setWindowTitle("Mora — DuckOS")
        self.resize(1380, 900)
        self.setMinimumSize(940, 660)
        self._apply_palette()
        self._build_shell()
        self._render_apps()
        self._update_clock()
        self._clock_timer.start()

        shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        shortcut.activated.connect(self.search_entry.setFocus)
        shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        clear_shortcut = QShortcut(QKeySequence("Escape"), self)
        clear_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        clear_shortcut.activated.connect(self._clear_search)

    def _apply_palette(self) -> None:
        scale = self._display_scale / 100
        scaled = lambda points: f"{points * scale:.2f}pt"
        self.setStyleSheet(f"""
            QWidget {{
                background: {PAGE};
                color: {TEXT};
                font-family: "Segoe UI";
                font-size: {scaled(10)};
            }}
            QMainWindow, QDialog {{ background: {PAGE}; }}
            QFrame#Sidebar {{
                background: {SURFACE};
                background: {self.glass_surface};
                border: 1px solid {self.glass_border};
                border-radius: 18px;
            }}
            QFrame#Card, QFrame#Hero, QFrame#Panel {{
                background: {SURFACE};
                background: {self.glass_surface};
                border: 1px solid {self.glass_border};
                border-radius: 16px;
            }}
            QLabel#Brand {{ color: {ACCENT}; font-size: {scaled(10)}; font-weight: 800; }}
            QLabel#Wordmark {{ color: {TEXT}; font-size: {scaled(27)}; font-weight: 800; }}
            QLabel#PageTitle {{ color: {TEXT}; font-size: {scaled(23)}; font-weight: 700; }}
            QLabel#SectionTitle {{ color: {TEXT}; font-size: {scaled(14)}; font-weight: 700; }}
            QLabel#Eyebrow {{ color: {ACCENT}; font-size: {scaled(8)}; font-weight: 800; }}
            QLabel#Muted {{ color: {MUTED}; }}
            QLabel#Clock {{ color: {TEXT}; font-size: {scaled(19)}; font-weight: 700; }}
            QPushButton {{
                background: {ELEVATED};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 9px 13px;
                min-height: 18px;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
                background: #302B12;
            }}
            QPushButton:pressed {{ background: {ACCENT}; color: {ON_ACCENT}; }}
            QPushButton#Primary {{
                background: {ACCENT};
                color: {ON_ACCENT};
                border-color: {ACCENT};
                font-weight: 800;
            }}
            QPushButton#Primary:hover {{ background: {ACCENT_HOVER}; }}
            QPushButton#Nav {{
                text-align: left;
                background: transparent;
                border: 1px solid transparent;
                padding: 11px 12px;
            }}
            QPushButton#Nav:hover {{
                background: {ELEVATED};
                border-color: {BORDER};
            }}
            QLineEdit, QComboBox, QPlainTextEdit, QListWidget, QSpinBox {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 9px;
                selection-background-color: {ACCENT};
                selection-color: {ON_ACCENT};
            }}
            QComboBox QAbstractItemView {{
                background: {SURFACE};
                color: {TEXT};
                selection-background-color: {ACCENT};
                selection-color: {ON_ACCENT};
            }}
            QSpinBox {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 9px;
                padding: 5px 7px;
                min-height: 22px;
                font-variant-numeric: tabular-nums;
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                border-radius: 3px;
                background: {BORDER};
            }}
            QSlider::sub-page:horizontal {{
                border-radius: 3px;
                background: {ACCENT};
            }}
            QSlider::add-page:horizontal {{
                border-radius: 3px;
                background: {ELEVATED};
            }}
            QSlider::handle:horizontal {{
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border: 2px solid {PAGE};
                border-radius: 9px;
                background: {ACCENT};
            }}
            QSlider::handle:horizontal:hover,
            QSlider::handle:horizontal:focus {{
                background: {ACCENT_HOVER};
                border-color: {ACCENT_HOVER};
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
            QPlainTextEdit:focus, QListWidget:focus,
            QPushButton:focus, QCheckBox:focus {{
                border: 2px solid {ACCENT_HOVER};
            }}
            QCheckBox {{ spacing: 9px; padding: 5px; }}
            QCheckBox::indicator {{
                width: 17px; height: 17px;
                border: 1px solid {MUTED};
                border-radius: 5px;
                background: {ELEVATED};
            }}
            QCheckBox::indicator:checked {{
                background: {ACCENT};
                border-color: {ACCENT};
            }}
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {PAGE};
                width: 10px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER};
                border-radius: 4px;
                min-height: 28px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {MUTED}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

    @staticmethod
    def _label(text: str, object_name: str = "") -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        if object_name:
            label.setObjectName(object_name)
        return label

    @staticmethod
    def _panel() -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        return panel

    def _build_shell(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(16)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 20, 18, 18)
        side.setSpacing(7)
        side.addWidget(self._label("DUCK", "Brand"))
        side.addWidget(self._label("Mora", "Wordmark"))
        side.addSpacing(18)
        side.addWidget(self._label("РАБОЧЕЕ ПРОСТРАНСТВО", "Eyebrow"))
        for title, app_id in (
            ("⌂   Главная", ""),
            ("⚙   Control", "workspace"),
            ("▦   Duck Desktop", "desktop"),
            ("✦   Mora AI", "mora-ai"),
            ("◇   Sentinel", "security"),
            ("✣   Mora Commons", "mora-commons"),
            ("⌘   Reaper Studio", "reaper"),
        ):
            button = QPushButton(title)
            button.setObjectName("Nav")
            button.clicked.connect(
                self._show_home if not app_id else lambda _checked=False, selected=app_id: self.open_app(selected)
            )
            side.addWidget(button)
        side.addStretch(1)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {BORDER};")
        side.addWidget(divider)
        side.addWidget(self._label("СИСТЕМНЫЙ СТАТУС", "Eyebrow"))
        side.addWidget(self._label(
            "Нативная Qt-сессия Mora\nПользовательский уровень · без WebView",
            "Muted",
        ))
        outer.addWidget(sidebar)

        main = QWidget()
        content = QVBoxLayout(main)
        content.setContentsMargins(10, 4, 4, 4)
        content.setSpacing(14)

        header = QHBoxLayout()
        title_stack = QVBoxLayout()
        title_stack.addWidget(self._label("MORA DESKTOP", "Eyebrow"))
        title_stack.addWidget(self._label("Рабочее пространство DuckOS", "PageTitle"))
        header.addLayout(title_stack, 1)
        clock_stack = QVBoxLayout()
        self.clock_label = self._label("", "Clock")
        self.date_label = self._label("", "Muted")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        clock_stack.addWidget(self.clock_label)
        clock_stack.addWidget(self.date_label)
        header.addLayout(clock_stack)
        content.addLayout(header)

        controls = QHBoxLayout()
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Поиск приложений и системных инструментов…")
        self.search_entry.textChanged.connect(self._render_apps)
        self.category_box = QComboBox()
        self.category_box.addItem("Все категории", "all")
        categories = sorted({str(app.get("category", "other")) for app in self.apps})
        for category in categories:
            self.category_box.addItem(category.replace("_", " ").title(), category)
        self.category_box.currentIndexChanged.connect(self._render_apps)
        controls.addWidget(self.search_entry, 1)
        controls.addWidget(self.category_box)
        settings_button = QPushButton("Настройки")
        settings_button.clicked.connect(lambda: self.open_app("workspace"))
        controls.addWidget(settings_button)
        content.addLayout(controls)

        hero = QFrame()
        hero.setObjectName("Hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(20, 16, 20, 16)
        hero_layout.addWidget(self._label("ОДНА СРЕДА. ПОНЯТНЫЕ ИНСТРУМЕНТЫ.", "Eyebrow"))
        hero_layout.addWidget(self._label(
            "Нативное рабочее пространство для приложений и системных инструментов DuckOS.",
        ))
        content.addWidget(hero)

        section = QHBoxLayout()
        section.addWidget(self._label("Приложения", "SectionTitle"))
        section.addStretch(1)
        self.count_label = self._label("", "Muted")
        section.addWidget(self.count_label)
        content.addLayout(section)

        self.app_scroll = QScrollArea()
        self.app_scroll.setWidgetResizable(True)
        self.app_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.app_container = QWidget()
        self.app_grid = QGridLayout(self.app_container)
        self.app_grid.setContentsMargins(0, 0, 8, 0)
        self.app_grid.setSpacing(12)
        self.app_scroll.setWidget(self.app_container)
        content.addWidget(self.app_scroll, 1)

        footer = QHBoxLayout()
        footer.addWidget(self._label("Duck · чёрный / белый / жёлтый", "Muted"))
        footer.addStretch(1)
        footer.addWidget(self._label("Mora · PySide6 · пользовательский уровень", "Muted"))
        content.addLayout(footer)
        outer.addWidget(main, 1)

    def _update_clock(self) -> None:
        now = QDateTime.currentDateTime()
        self.clock_label.setText(now.toString("HH:mm"))
        self.date_label.setText(now.toString("dddd, dd MMMM yyyy"))

    def _clear_search(self) -> None:
        if self.search_entry.hasFocus():
            self.search_entry.clear()

    def _preview_ui_scale(self, value: int) -> None:
        self._display_scale = int(value)
        self._apply_palette()

    def _restore_ui_scale_preview(self, *_args: Any) -> None:
        self._display_scale = self.preferences["appearance"]["uiScale"]
        self._apply_palette()

    def _render_apps(self, *_args: Any) -> None:
        while self.app_grid.count():
            item = self.app_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        query = self.search_entry.text().strip().casefold()
        category = self.category_box.currentData()
        matches = [
            app for app in self.apps
            if (category == "all" or app.get("category") == category)
            and query in " ".join((
                str(app.get("name", "")),
                str(app.get("id", "")),
                str(app.get("category", "")),
                APP_DESCRIPTIONS.get(str(app.get("id")), ("", ""))[0],
            )).casefold()
        ]

        available_width = max(480, self.app_scroll.viewport().width())
        columns = max(2, min(5, available_width // 210))
        for index, app in enumerate(matches):
            self.app_grid.addWidget(
                self._create_app_card(app),
                index // columns,
                index % columns,
            )
        for column in range(columns):
            self.app_grid.setColumnStretch(column, 1)
        self.count_label.setText(f"{len(matches)} из {len(self.apps)}")
        if not matches:
            empty = self._label("Ничего не найдено. Измените запрос или категорию.", "Muted")
            self.app_grid.addWidget(empty, 0, 0, 1, columns)

    def _create_app_card(self, app: dict[str, Any]) -> QFrame:
        app_id = str(app.get("id", ""))
        name = str(app.get("name", app_id))
        category = str(app.get("category", "other")).replace("_", " ").title()
        subtitle = APP_DESCRIPTIONS.get(app_id, (category, ""))[0]

        card = AppCard()
        card.setObjectName("Card")
        card.activated.connect(lambda selected=app_id: self.open_app(selected))
        card.setMinimumHeight(132)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 13, 14, 13)
        layout.setSpacing(8)

        open_button = QPushButton(name)
        open_button.setStyleSheet(
            "text-align: left; background: transparent; border: none; "
            "padding: 2px; font-weight: 700;"
        )
        open_button.clicked.connect(lambda _checked=False, selected=app_id: self.open_app(selected))
        layout.addWidget(open_button)

        subtitle_label = self._label(subtitle, "Muted")
        layout.addWidget(subtitle_label)
        layout.addStretch(1)
        meta = self._label(category.upper(), "Eyebrow")
        layout.addWidget(meta)

        return card

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        QTimer.singleShot(0, self._render_apps)

    def _show_home(self) -> None:
        self.search_entry.clear()
        self.category_box.setCurrentIndex(0)
        self.app_scroll.verticalScrollBar().setValue(0)

    def open_app(self, app_id: str) -> None:
        if app_id == "reaper":
            self._open_reaper()
            return

        current = self._app_dialogs.get(app_id)
        if current is not None:
            if current.isMinimized():
                current.showNormal()
            current.raise_()
            current.activateWindow()
            return

        app = self.apps_by_id.get(app_id)
        if app is None:
            QMessageBox.warning(self, "Mora", "Приложение отсутствует в реестре.")
            return

        subtitle, description = APP_DESCRIPTIONS.get(
            app_id, ("Нативное приложение", "Описание приложения пока не добавлено.")
        )
        dialog = QDialog(self)
        dialog.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        dialog.setWindowModality(Qt.WindowModality.NonModal)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dialog.setSizeGripEnabled(True)
        dialog.setWindowTitle(f"{app.get('name', app_id)} — Mora")

        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else None
        usable_width = max(1, available.width() - 32) if available is not None else 760
        usable_height = max(1, available.height() - 72) if available is not None else 610
        width = min(760, usable_width)
        height = min(610, usable_height)
        dialog.setMinimumSize(min(580, width), min(420, height))
        dialog.resize(width, height)

        layout = QVBoxLayout(dialog)
        header = QFrame()
        header.setObjectName("Panel")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(18, 15, 18, 15)
        header_layout.addWidget(self._label(str(app.get("category", "system")).upper(), "Eyebrow"))
        header_layout.addWidget(self._label(str(app.get("name", app_id)), "SectionTitle"))
        header_layout.addWidget(self._label(subtitle, "Muted"))
        layout.addWidget(header)

        body_content = QWidget()
        body = QVBoxLayout(body_content)
        body.addWidget(self._label(description))
        maturity = str(app.get("maturity", "catalog_concept"))
        body.addWidget(self._label(
            f"СТАТУС: {MATURITY_LABELS.get(maturity, 'Каталог приложения')}",
            "Eyebrow",
        ))
        try:
            self._build_app_panel(app_id, app, body)
        except Exception as error:
            body.addWidget(self._label(
                "Панель не удалось открыть. Остальная оболочка продолжает работать.\n"
                f"{type(error).__name__}: {error}",
                "Muted",
            ))
        body.addStretch(1)

        scroll = QScrollArea(dialog)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(body_content)
        layout.addWidget(scroll, 1)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(dialog.accept)
        close_button.setObjectName("Primary")
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

        self._app_dialogs[app_id] = dialog
        dialog.finished.connect(
            lambda _result, key=app_id: self._app_dialogs.pop(key, None)
        )
        dialog.destroyed.connect(
            lambda *_args, key=app_id: self._app_dialogs.pop(key, None)
        )
        if app_id == "workspace":
            dialog.finished.connect(self._restore_ui_scale_preview)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _build_app_panel(self, app_id: str, app: dict[str, Any], layout: QVBoxLayout) -> None:
        if app_id == "workspace":
            self._build_control_panel(layout)
        elif app_id == "security":
            self._build_security_panel(layout)
        elif app_id == "updates":
            self._build_recovery_panel(layout)
        elif app_id == "mora-ai":
            self._build_ai_panel(layout)
        elif app_id == "provenance":
            self._build_proof_panel(layout)
        elif app_id in {"runtime", "exedotexe", "gamecharager"}:
            self._build_bridge_panel(layout)
        elif app_id == "desktop":
            self._build_desktop_panel(layout)
        elif app_id == "mora-commons":
            self._build_commons_panel(layout)
        elif app_id == "mora-boost":
            self._build_boost_panel(layout)
        else:
            self._build_catalog_panel(app_id, app, layout)

    def _save_profile(self, title: str = "Control") -> bool:
        self.preferences = normalize_preferences(self.preferences)
        if save_preferences(self.preferences):
            QMessageBox.information(self, title, "Настройки сохранены локально.")
            return True
        QMessageBox.critical(self, title, "Не удалось сохранить настройки Mora.")
        return False

    def _build_control_panel(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._label("Настройки текущей оболочки", "SectionTitle"))
        scale = MoraSlider(
            "Масштаб интерфейса",
            80,
            140,
            self.preferences["appearance"]["uiScale"],
            suffix="%",
            step=5,
            precise_step=1,
        )
        scale.valueChanged.connect(self._preview_ui_scale)
        focus = QCheckBox("Режим фокуса")
        focus.setChecked(self.preferences["focusMode"])
        reduced = QCheckBox("Уменьшить анимацию интерфейса")
        reduced.setChecked(self.preferences["appearance"]["reducedMotion"])
        density = QComboBox()
        density.addItem("Комфортная", "comfortable")
        density.addItem("Компактная", "compact")
        density.setCurrentIndex(1 if self.preferences["appearance"]["density"] == "compact" else 0)
        profile = QComboBox()
        for value, label in (
            ("saver", "Экономия"),
            ("balanced", "Сбалансированный"),
            ("performance", "Производительность"),
        ):
            profile.addItem(label, value)
        profile.setCurrentIndex(max(0, profile.findData(self.preferences["powerProfile"])))

        form = QFormLayout()
        form.addRow(scale)
        form.addRow(focus)
        form.addRow(reduced)
        form.addRow("Плотность", density)
        form.addRow("Профиль предпочтений", profile)
        layout.addLayout(form)

        save = QPushButton("Сохранить настройки")
        save.setObjectName("Primary")

        def commit() -> None:
            self.preferences["focusMode"] = focus.isChecked()
            self.preferences["appearance"]["reducedMotion"] = reduced.isChecked()
            self.preferences["appearance"]["density"] = density.currentData()
            self.preferences["appearance"]["uiScale"] = scale.value()
            self.preferences["powerProfile"] = profile.currentData()
            self._display_scale = scale.value()
            self._apply_palette()
            self._save_profile()

        save.clicked.connect(commit)
        layout.addWidget(save, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._label(
            "Профиль описывает предпочтения Mora. Он не меняет частоты CPU/GPU, драйверы, "
            "системные службы или глобальный планировщик.",
            "Muted",
        ))

    def _build_security_panel(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._label("Локальные предпочтения разрешений", "SectionTitle"))
        variables: dict[str, QCheckBox] = {}
        for capability, enabled in self.preferences["permissions"].items():
            checkbox = QCheckBox(f"{capability.capitalize()} — включено в локальном профиле")
            checkbox.setChecked(enabled)
            variables[capability] = checkbox
            layout.addWidget(checkbox)

        save = QPushButton("Сохранить профиль")
        save.setObjectName("Primary")

        def commit() -> None:
            self.preferences["permissions"] = {
                name: checkbox.isChecked() for name, checkbox in variables.items()
            }
            self._save_profile("Sentinel")

        save.clicked.connect(commit)
        layout.addWidget(save, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._label(
            "Эти переключатели не предоставляют и не блокируют доступ на уровне ядра, "
            "процессов или устройств. Для этого нужен отдельный системный брокер возможностей.",
            "Muted",
        ))

    def _build_recovery_panel(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._label("Резервная копия настроек Mora", "SectionTitle"))
        layout.addWidget(self._label(
            "В копию входят только настройки оболочки и локальные предпочтения. "
            "Пользовательские файлы и разделы DuckOS не затрагиваются.",
            "Muted",
        ))
        actions = QHBoxLayout()
        export_button = QPushButton("Экспортировать копию")
        export_button.setObjectName("Primary")
        import_button = QPushButton("Восстановить из JSON")
        actions.addWidget(export_button)
        actions.addWidget(import_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        def export_snapshot() -> None:
            destination, _ = QFileDialog.getSaveFileName(
                self, "Экспортировать настройки Mora", "mora-settings-backup.json",
                "JSON (*.json)",
            )
            if not destination:
                return
            snapshot = create_recovery_snapshot(self.preferences)
            try:
                Path(destination).write_text(_json_text(snapshot) + "\n", encoding="utf-8")
            except OSError as error:
                QMessageBox.critical(self, "Restore", str(error))
            else:
                QMessageBox.information(self, "Restore", "Копия настроек сохранена.")

        def import_snapshot() -> None:
            source, _ = QFileDialog.getOpenFileName(
                self, "Выбрать копию настроек Mora", "", "JSON (*.json)"
            )
            if not source:
                return
            try:
                if Path(source).stat().st_size > 1024 * 1024:
                    raise ValueError("Файл резервной копии превышает 1 МиБ.")
                candidate = json.loads(Path(source).read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
                QMessageBox.critical(self, "Restore", f"Не удалось прочитать копию: {error}")
                return
            snapshot = validate_recovery_snapshot(candidate)
            if snapshot is None:
                QMessageBox.critical(self, "Restore", "Формат копии не поддерживается.")
                return
            decision = QMessageBox.question(
                self, "Restore", "Заменить текущие настройки Mora содержимым копии?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if decision != QMessageBox.StandardButton.Yes:
                return
            if not save_preferences(snapshot["preferences"]):
                QMessageBox.critical(self, "Restore", "Не удалось сохранить восстановленные настройки.")
                return
            self.preferences = snapshot["preferences"]
            QMessageBox.information(self, "Restore", "Настройки восстановлены.")

        export_button.clicked.connect(export_snapshot)
        import_button.clicked.connect(import_snapshot)

    def _build_ai_panel(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._label("Опишите простое действие", "SectionTitle"))
        query = QLineEdit()
        query.setPlaceholderText("Например: включи режим фокуса и экономию энергии")
        output = QPlainTextEdit()
        output.setReadOnly(True)
        output.setMinimumHeight(170)
        layout.addWidget(query)
        layout.addWidget(output, 1)
        actions = QHBoxLayout()
        preview_button = QPushButton("Подготовить план")
        preview_button.setObjectName("Primary")
        approve_button = QPushButton("Подтвердить план")
        actions.addWidget(preview_button)
        actions.addWidget(approve_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        state: dict[str, Any] = {"plan": None}

        def preview() -> None:
            result = build_intent_plan(query.text())
            state["plan"] = result if result.get("ok") else None
            output.setPlainText(result.get("message", "План отсутствует."))
            if result.get("ok"):
                output.appendPlainText("\n" + _json_text(result["actions"]))

        def approve() -> None:
            plan = state["plan"]
            if not plan:
                QMessageBox.warning(self, "Mora AI", "Сначала подготовьте допустимый план.")
                return
            answer = QMessageBox.question(
                self, "Mora AI", "Применить показанный локальный план?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            for action in plan["actions"]:
                if action["type"] == "open-app":
                    self.open_app(action["appId"])
                elif action["type"] == "set":
                    setting = action["setting"]
                    if setting == "focusMode":
                        self.preferences["focusMode"] = action["value"]
                    elif setting == "powerProfile":
                        self.preferences["powerProfile"] = action["value"]
                    elif setting == "reducedMotion":
                        self.preferences["appearance"]["reducedMotion"] = action["value"]
            self._save_profile("Mora AI")

        preview_button.clicked.connect(preview)
        query.returnPressed.connect(preview)
        approve_button.clicked.connect(approve)
        layout.addWidget(self._label(
            "Mora AI здесь — локальный ограниченный rule-engine. Он не запускает shell, "
            "произвольный код и не вызывает внешнюю модель.",
            "Muted",
        ))

    def _build_proof_panel(self, layout: QVBoxLayout) -> None:
        output = QPlainTextEdit()
        output.setReadOnly(True)
        output.setMinimumHeight(160)
        button = QPushButton("Вычислить SHA-256")
        button.setObjectName("Primary")

        def choose_file() -> None:
            path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл для SHA-256")
            if not path:
                return
            try:
                report = calculate_sha256(path)
            except ValueError as error:
                QMessageBox.critical(self, "Proof", str(error))
                return
            output.setPlainText(_json_text(report))

        button.clicked.connect(choose_file)
        layout.addWidget(output)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._label(
            "Локальное хэширование не доказывает авторство, подпись или происхождение файла.",
            "Muted",
        ))

    def _build_bridge_panel(self, layout: QVBoxLayout) -> None:
        output = QPlainTextEdit()
        output.setReadOnly(True)
        output.setMinimumHeight(190)
        button = QPushButton("Выбрать файл и проверить заголовки")
        button.setObjectName("Primary")

        def inspect_file() -> None:
            from ..compat.bridge import inspect_binary

            path, _ = QFileDialog.getOpenFileName(
                self, "Выбрать PE/ELF-файл", "",
                "Исполняемые файлы (*.exe *.dll *.sys *.elf);;Все файлы (*.*)",
            )
            if not path:
                return
            try:
                report = inspect_binary(Path(path))
            except (OSError, ValueError, RuntimeError) as error:
                QMessageBox.critical(self, "Bridge", str(error))
                return
            output.setPlainText(_json_text(report))

        button.clicked.connect(inspect_file)
        layout.addWidget(output, 1)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._label(
            "Файл только читается. Запуск, распаковка, загрузка DLL и установка runtime не выполняются.",
            "Muted",
        ))

    def _build_desktop_panel(self, layout: QVBoxLayout) -> None:
        from ..desktop.service import audit_desktop

        output = QPlainTextEdit()
        output.setReadOnly(True)
        output.setMinimumHeight(200)
        refresh_button = QPushButton("Обновить аудит")
        open_button = QPushButton("Открыть Duck Desktop")
        open_button.setObjectName("Primary")
        actions = QHBoxLayout()
        actions.addWidget(refresh_button)
        actions.addWidget(open_button)
        actions.addStretch(1)
        layout.addWidget(output, 1)
        layout.addLayout(actions)

        def refresh() -> None:
            try:
                report = audit_desktop()
            except (OSError, ValueError, RuntimeError) as error:
                report = {"error": str(error)}
            output.setPlainText(_json_text(report))

        def launch() -> None:
            try:
                subprocess.Popen(
                    [sys.executable, "-m", "duckos", "desktop", "gui"],
                    shell=False,
                    close_fds=True,
                )
            except OSError as error:
                QMessageBox.critical(self, "Duck Desktop", str(error))

        refresh_button.clicked.connect(refresh)
        open_button.clicked.connect(launch)
        refresh()

    def _open_reaper(self) -> None:
        from ..desktop.reaper import ReaperWorkbench

        workbench = ReaperWorkbench()
        current = self._app_dialogs.get("reaper")
        if current is not None:
            if current.isMinimized():
                current.showNormal()
            current.raise_()
            current.activateWindow()
            return

        dialog = QDialog(self)
        dialog.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        dialog.setWindowModality(Qt.WindowModality.NonModal)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dialog.setSizeGripEnabled(True)
        dialog.setWindowTitle("Reaper Studio — Mora")
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else None
        width = min(700, max(1, available.width() - 32)) if available is not None else 700
        height = min(420, max(1, available.height() - 72)) if available is not None else 420
        dialog.setMinimumSize(min(480, width), min(300, height))
        dialog.resize(width, height)
        layout = QVBoxLayout(dialog)
        report = QPlainTextEdit()
        report.setReadOnly(True)
        report.setPlainText(_json_text(workbench.inspect()))
        layout.addWidget(report, 1)
        launch = QPushButton("Открыть Reaper Studio")
        launch.setObjectName("Primary")
        layout.addWidget(launch, alignment=Qt.AlignmentFlag.AlignLeft)

        def start() -> None:
            try:
                process = workbench.open_studio()
            except (OSError, ValueError, RuntimeError) as error:
                QMessageBox.critical(dialog, "Reaper", str(error))
            else:
                QMessageBox.information(dialog, "Reaper", f"Reaper Studio открыт. PID: {process.pid}")

        launch.clicked.connect(start)
        self._app_dialogs["reaper"] = dialog
        dialog.finished.connect(
            lambda _result: self._app_dialogs.pop("reaper", None)
        )
        dialog.destroyed.connect(
            lambda *_args: self._app_dialogs.pop("reaper", None)
        )
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _build_commons_panel(self, layout: QVBoxLayout) -> None:
        controls = QHBoxLayout()
        search = QLineEdit()
        search.setPlaceholderText("Поиск в Mora Commons…")
        category = QComboBox()
        category.addItem("Все направления", "all")
        for item in self.commons.get("categories", []):
            category.addItem(item["title"], item["id"])
        controls.addWidget(search, 1)
        controls.addWidget(category)
        layout.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Vertical)
        listing = QListWidget()
        detail = QPlainTextEdit()
        detail.setReadOnly(True)
        splitter.addWidget(listing)
        splitter.addWidget(detail)
        splitter.setSizes([260, 180])
        layout.addWidget(splitter, 1)
        state: dict[str, list[dict[str, Any]]] = {"matches": []}

        def render(*_args: Any) -> None:
            matches = filter_commons_apps(
                self.commons.get("apps", []), search.text(), category.currentData()
            )
            state["matches"] = matches
            listing.clear()
            for item in matches:
                row = QListWidgetItem(f"{item.get('name')}  ·  {item.get('subtitle')}")
                row.setData(Qt.ItemDataRole.UserRole, item.get("id"))
                listing.addItem(row)
            detail.setPlainText("Выберите приложение." if matches else "Нет совпадений.")

        def show_detail(item: QListWidgetItem) -> None:
            app_id = item.data(Qt.ItemDataRole.UserRole)
            match = next((entry for entry in state["matches"] if entry.get("id") == app_id), None)
            if match is None:
                return
            detail.setPlainText(
                f"{match.get('name')}\n{match.get('subtitle')}\n\n"
                f"{match.get('description')}\n\n"
                "Статус: описание продукта в каталоге. Наличие записи не означает установку приложения."
            )

        search.textChanged.connect(render)
        category.currentIndexChanged.connect(render)
        listing.itemClicked.connect(show_detail)
        render()

    def _build_boost_panel(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._label(
            "OPlague Gaming Lab подключается как отдельный проект.",
            "SectionTitle",
        ))
        layout.addWidget(self._label(
            "Mora не меняет драйверы, частоты, напряжение, приоритеты процессов или параметры ядра. "
            "Для игровой диагностики используются отдельные проверяемые инструменты DuckOS и OPlague.",
            "Muted",
        ))
        button = QPushButton("Открыть проект OPlague")
        button.setObjectName("Primary")
        button.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://github.com/Ivan-VHS/OPlague")
        ))
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignLeft)

    def _build_catalog_panel(
        self,
        app_id: str,
        app: dict[str, Any],
        layout: QVBoxLayout,
    ) -> None:
        maturity = str(app.get("maturity", "catalog_concept"))
        if maturity == "partial_local_workspace":
            text = (
                "Нативная точка входа подготовлена. Полноценная работа с данными и системными "
                "службами для этого приложения остаётся отдельным этапом."
            )
        else:
            text = (
                "Это зарегистрированное приложение каталога. Нативные функции подключаются "
                "отдельно и не считаются реализованными только из-за наличия карточки."
            )
        layout.addWidget(self._label(text, "Muted"))
        form = QFormLayout()
        form.addRow("Идентификатор", QLabel(app_id))
        form.addRow("Категория", QLabel(str(app.get("category", "other"))))
        form.addRow("Среда выполнения", QLabel("PySide6 · user-space"))
        layout.addLayout(form)


def run_native_mora() -> int:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName("Mora")
    app.setOrganizationName("Ivan-VHS")
    app.setApplicationDisplayName("Mora — DuckOS")
    window = MoraWindow()
    window.show()
    return app.exec()


def main() -> int:
    try:
        return run_native_mora()
    except ImportError as error:
        raise SystemExit(
            "Mora requires the native Qt desktop extra. Install it with: "
            "python -m pip install 'duckos-build-tools[native-ui]'. "
            f"Qt import details: {error}"
        ) from error


if __name__ == "__main__":
    raise SystemExit(main())
