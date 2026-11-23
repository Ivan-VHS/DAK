"""Native Tk desktop shell for Mora.

This is a user-space desktop application, not the DuckOS compositor or kernel.
It uses Tk widgets directly and does not embed a browser or render HTML.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from .model import (
    build_intent_plan,
    calculate_sha256,
    config_directory,
    create_recovery_snapshot,
    filter_commons_apps,
    load_preferences,
    normalize_preferences,
    save_preferences,
    validate_recovery_snapshot,
)

BACKGROUND = "#080808"
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
    "cockos": ("Аудио и музыкальные проекты", "Локальная карточка аудио-направления. Нативный аудиодвижок и управление устройствами пока не входят в эту оболочку."),
    "kavun": ("Фотографии и медиатека", "Карточка медиатеки. Индексация фотографий, импорт и обработка требуют отдельного нативного сервиса."),
    "kabon": ("Личные финансы", "Карточка финансового рабочего пространства. Здесь пока нет подключения к банковским счетам или финансовых сервисов."),
    "gloverty": ("Автоматизация задач", "Каталог автоматизаций. Произвольные скрипты не исполняются; действия DuckOS должны проходить через отдельные проверяемые сервисы."),
    "po": ("Компас и ориентирование", "Карточка инструмента ориентирования. Для работы с датчиками и геопозицией потребуется нативный драйвер и брокер разрешений."),
    "illidia": ("Игры и библиотека", "Каталог игрового направления. Запуск игр и управление графическими API из этого окна не выполняются."),
    "unify": ("Подключённые устройства", "Панель сведений об устройствах. Реальное подключение и управление периферией остаются задачей системных служб и драйверов."),
    "sestem": ("Системная панель", "Локальный обзор рабочего пространства и доступных компонентов DuckOS."),
    "setupup": ("Первичная настройка", "Профиль установки хранится локально. Установка или изменение системного образа из этой панели не выполняется."),
    "orriganize": ("Проекты и задачи", "Локальное пространство организации. Синхронизация между устройствами пока не предоставляется."),
    "abriganza": ("Архивы и файлы", "Панель файловых инструментов. В этой версии доступна только безопасная работа с выбранными пользовательскими файлами."),
    "olaab": ("Мультимедиа", "Карточка мультимедийной библиотеки. Кодирование и воспроизведение будут подключаться через отдельные нативные модули."),
    "concrete-thump": ("Ритм и темп", "Инструмент для подготовки музыкальных профилей. Звуковое воспроизведение и синтез здесь не заявлены."),
    "seu-beu": ("Обмен и приватность", "Локальный список мер перед передачей файлов. Шифрование и проверка личности требуют отдельных криптографических служб."),
    "love-il": ("Личный дневник", "Карточка приватных записей. Синхронизация и шифрование на уровне хранилища ещё не реализованы."),
    "poi": ("Быстрые заметки", "Локальная область заметок. Сохранение записей появится после подключения постоянного хранилища приложений."),
    "poi-2": ("База знаний", "Карточка базы знаний. Индексация, поиск и синхронизация пока не являются системными функциями."),
    "po-2": ("Маршруты и точки", "Панель маршрутов. Геолокация, карты и навигационные датчики требуют отдельной системной интеграции."),
    "gamecharager": ("Игровая библиотека", "Локальный инспектор файлов игры. Обнаружение совместимости не запускает выбранные приложения."),
    "exedotexe": ("Инспектор Windows-файлов", "Проверка заголовков PE/ELF и подготовка диагностических сведений без выполнения файла."),
    "mora-ai": ("Локальные планы действий", "Ограниченный набор правил для нескольких безопасных настроек и открытия встроенных панелей. Это не подключённая языковая модель."),
    "security": ("Профиль разрешений", "Список пользовательских предпочтений. Переключатели не выдают системные права и не заменяют нативный брокер возможностей."),
    "updates": ("Резервная копия настроек", "Экспорт и восстановление только настроек Mora. Обновление разделов DuckOS и загрузочный откат пока не реализованы."),
    "runtime": ("Совместимость приложений", "Диагностика локальных PE/ELF-файлов и статусы совместимости. Выполнение выбранных программ отключено."),
    "workspace": ("Управление рабочей средой", "Настройки интерфейса Mora: фокус, плотность отображения и локальный профиль ресурсов."),
    "provenance": ("Проверка целостности", "Вычисляет SHA-256 выбранного файла. Хэш не доказывает автора, подпись или подлинность источника."),
    "mora-boost": ("Игровая лаборатория", "Точка интеграции с отдельным OPlague workbench. Эта панель не меняет драйверы, частоты или системные параметры."),
    "desktop": ("Обслуживание рабочего пространства", "Открывает отдельное нативное окно Duck Desktop для аудита файлов рабочего стола и пользовательской автозагрузки."),
    "mora-commons": ("Каталог Mora Commons", "Каталог описаний приложений. Запись в каталоге не означает, что приложение установлено или доступно как системная служба."),
}

MATURITY_LABELS = {
    "partial_local_workspace": "Локальная рабочая область · частично",
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


class MoraWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.preferences = load_preferences()
        self.registry = self._load_json("apps.json", {"built_in_apps": []})
        self.commons = self._load_json("commons-catalog.json", {"apps": [], "categories": []})
        self.apps = list(self.registry.get("built_in_apps", []))
        self.apps_by_id = {str(app.get("id")): app for app in self.apps}
        self._pending_plan: dict[str, Any] | None = None
        self._clock_job: str | None = None

        root.title("Mora — DuckOS")
        root.geometry("1320x860")
        root.minsize(900, 640)
        root.configure(background=BACKGROUND)
        self._configure_style()
        self._build_shell()
        self._render_apps()
        self._update_clock()
        root.bind("<Control-k>", self._focus_search)
        root.bind("<Control-K>", self._focus_search)
        root.bind("<Escape>", self._clear_search)
        root.protocol("WM_DELETE_WINDOW", self.close)

    @staticmethod
    def _data_directory() -> Path:
        return Path(__file__).with_name("data")

    def _load_json(self, filename: str, fallback: dict[str, Any]) -> dict[str, Any]:
        path = self._data_directory() / filename
        try:
            if path.is_symlink() or path.stat().st_size > 4 * 1024 * 1024:
                return fallback
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else fallback
        except (OSError, UnicodeError, json.JSONDecodeError):
            return fallback

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=BACKGROUND, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("TFrame", background=BACKGROUND)
        style.configure("Surface.TFrame", background=SURFACE)
        style.configure("TLabel", background=BACKGROUND, foreground=TEXT)
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 22), foreground=TEXT)
        style.configure("Eyebrow.TLabel", font=("Segoe UI", 9, "bold"), foreground=ACCENT)
        style.configure("TButton", padding=(12, 9), background=ELEVATED, foreground=TEXT, bordercolor=BORDER)
        style.map("TButton", background=[("active", ACCENT)], foreground=[("active", ON_ACCENT)])
        style.configure("Accent.TButton", padding=(14, 10), background=ACCENT, foreground=ON_ACCENT, font=("Segoe UI Semibold", 10))
        style.map("Accent.TButton", background=[("active", ACCENT_HOVER)])
        style.configure("TEntry", fieldbackground=SURFACE, foreground=TEXT, insertcolor=ACCENT, padding=9)
        style.configure("TCombobox", fieldbackground=SURFACE, foreground=TEXT, padding=7)
        style.configure("TCheckbutton", background=BACKGROUND, foreground=TEXT)
        style.map("TCheckbutton", background=[("active", BACKGROUND)])
        style.configure("TNotebook", background=BACKGROUND, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 8), background=ELEVATED, foreground=TEXT)
        style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", ON_ACCENT)])

    def _build_shell(self) -> None:
        outer = tk.Frame(self.root, background=BACKGROUND)
        outer.pack(fill="both", expand=True)

        sidebar = tk.Frame(outer, background=SURFACE, width=238, padx=20, pady=22)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="DUCK", background=SURFACE, foreground=ACCENT,
                 font=("Segoe UI Black", 12, "bold")).pack(anchor="w")
        tk.Label(sidebar, text="Mora", background=SURFACE, foreground=TEXT,
                 font=("Segoe UI Semibold", 27, "bold")).pack(anchor="w", pady=(0, 22))
        tk.Label(sidebar, text="РАБОЧЕЕ ПРОСТРАНСТВО", background=SURFACE,
                 foreground=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 8))
        self._sidebar_button(sidebar, "⌂   Главная", self._show_home)
        self._sidebar_button(sidebar, "⚙   Control", lambda: self.open_app("workspace"))
        self._sidebar_button(sidebar, "▦   Duck Desktop", lambda: self.open_app("desktop"))
        self._sidebar_button(sidebar, "✦   Mora AI", lambda: self.open_app("mora-ai"))
        self._sidebar_button(sidebar, "◇   Sentinel", lambda: self.open_app("security"))
        self._sidebar_button(sidebar, "✣   Mora Commons", lambda: self.open_app("mora-commons"))
        self._sidebar_button(sidebar, "⌘   Reaper Studio", lambda: self.open_app("reaper"))

        tk.Frame(sidebar, background=BORDER, height=1).pack(fill="x", pady=20)
        tk.Label(sidebar, text="СИСТЕМНЫЙ СТАТУС", background=SURFACE,
                 foreground=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.sidebar_status = tk.Label(sidebar, text="Локальная сессия Mora",
                 background=SURFACE, foreground=SECONDARY, justify="left",
                 wraplength=185, font=("Segoe UI", 9))
        self.sidebar_status.pack(anchor="w", pady=(8, 0))
        tk.Label(sidebar, text="Нативное приложение · без WebView",
                 background=SURFACE, foreground=MUTED, wraplength=185,
                 justify="left", font=("Segoe UI", 8)).pack(side="bottom", anchor="w")

        main = tk.Frame(outer, background=BACKGROUND, padx=28, pady=22)
        main.pack(side="left", fill="both", expand=True)

        header = tk.Frame(main, background=BACKGROUND)
        header.pack(fill="x")
        title_block = tk.Frame(header, background=BACKGROUND)
        title_block.pack(side="left", fill="x", expand=True)
        tk.Label(title_block, text="MORA DESKTOP", background=BACKGROUND,
                 foreground=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(title_block, text="Рабочее пространство DuckOS",
                 background=BACKGROUND, foreground=TEXT,
                 font=("Segoe UI Semibold", 22, "bold")).pack(anchor="w", pady=(3, 0))
        clock_block = tk.Frame(header, background=BACKGROUND)
        clock_block.pack(side="right", anchor="e")
        self.clock_label = tk.Label(clock_block, text="", background=BACKGROUND,
                                    foreground=TEXT, font=("Segoe UI Semibold", 18))
        self.clock_label.pack(anchor="e")
        self.date_label = tk.Label(clock_block, text="", background=BACKGROUND,
                                   foreground=MUTED, font=("Segoe UI", 9))
        self.date_label.pack(anchor="e", pady=(2, 0))

        controls = tk.Frame(main, background=BACKGROUND)
        controls.pack(fill="x", pady=(22, 16))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(controls, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.insert(0, "Поиск приложений")
        self.search_entry.bind("<FocusIn>", self._clear_search_placeholder)
        self.search_entry.bind("<KeyRelease>", lambda _event: self._render_apps())
        self.category_var = tk.StringVar(value="Все категории")
        categories = ["Все категории"] + sorted({
            str(app.get("category", "other")) for app in self.apps
        })
        category_box = ttk.Combobox(controls, textvariable=self.category_var,
                                    values=categories, state="readonly", width=22)
        category_box.pack(side="left", padx=(10, 0))
        category_box.bind("<<ComboboxSelected>>", lambda _event: self._render_apps())
        ttk.Button(controls, text="Настройки", command=lambda: self.open_app("workspace")).pack(side="left", padx=(10, 0))

        intro = tk.Frame(main, background=SURFACE, padx=20, pady=16,
                         highlightthickness=1, highlightbackground=BORDER)
        intro.pack(fill="x", pady=(0, 18))
        tk.Label(intro, text="ОДНА СРЕДА. ПОНЯТНЫЕ ИНСТРУМЕНТЫ.",
                 background=SURFACE, foreground=ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(intro, text="Открывайте приложения и системные панели из единого нативного рабочего пространства.",
                 background=SURFACE, foreground=TEXT, justify="left",
                 wraplength=900, font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 0))

        app_heading = tk.Frame(main, background=BACKGROUND)
        app_heading.pack(fill="x", pady=(0, 10))
        tk.Label(app_heading, text="Приложения", background=BACKGROUND,
                 foreground=TEXT, font=("Segoe UI Semibold", 15, "bold")).pack(side="left")
        self.count_label = tk.Label(app_heading, text="", background=BACKGROUND,
                                    foreground=MUTED, font=("Segoe UI", 9))
        self.count_label.pack(side="right")

        app_area = tk.Frame(main, background=BACKGROUND)
        app_area.pack(fill="both", expand=True)
        self.app_canvas = tk.Canvas(app_area, background=BACKGROUND, highlightthickness=0)
        scrollbar = ttk.Scrollbar(app_area, orient="vertical", command=self.app_canvas.yview)
        self.cards_frame = tk.Frame(self.app_canvas, background=BACKGROUND)
        self.cards_frame.bind("<Configure>", lambda _event: self.app_canvas.configure(
            scrollregion=self.app_canvas.bbox("all")
        ))
        self.app_canvas.create_window((0, 0), window=self.cards_frame, anchor="nw", tags="cards")
        self.app_canvas.configure(yscrollcommand=scrollbar.set)
        self.app_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.app_canvas.bind("<Configure>", self._resize_cards)
        self.root.bind_all("<MouseWheel>", self._scroll_apps, add="+")

        footer = tk.Frame(main, background=BACKGROUND)
        footer.pack(fill="x", pady=(12, 0))
        tk.Label(footer, text="Duck black · white · yellow",
                 background=BACKGROUND, foreground=MUTED,
                 font=("Segoe UI", 8)).pack(side="left")
        tk.Label(footer, text="Mora native user-space shell · 0.1",
                 background=BACKGROUND, foreground=MUTED,
                 font=("Segoe UI", 8)).pack(side="right")

    def _sidebar_button(self, parent: tk.Widget, label: str, command: Any) -> None:
        tk.Button(parent, text=label, command=command, anchor="w",
                  background=SURFACE, foreground=TEXT, activebackground=ACCENT,
                  activeforeground=ON_ACCENT, relief="flat", borderwidth=0,
                  padx=10, pady=10, font=("Segoe UI", 10)).pack(fill="x", pady=2)

    def _clear_search_placeholder(self, _event: Any = None) -> None:
        if self.search_var.get() == "Поиск приложений":
            self.search_var.set("")

    def _focus_search(self, _event: Any = None) -> str:
        self.search_entry.focus_set()
        self._clear_search_placeholder()
        self.search_entry.selection_range(0, "end")
        return "break"

    def _clear_search(self, _event: Any = None) -> str:
        if self.root.focus_get() == self.search_entry:
            self.search_var.set("")
            self._render_apps()
            return "break"
        return "break"

    def _resize_cards(self, event: Any) -> None:
        self.app_canvas.itemconfigure("cards", width=event.width)
        self._render_apps()

    def _scroll_apps(self, event: Any) -> None:
        try:
            self.app_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (AttributeError, tk.TclError):
            pass

    def _render_apps(self) -> None:
        for child in self.cards_frame.winfo_children():
            child.destroy()
        query = self.search_var.get().strip()
        if query == "Поиск приложений":
            query = ""
        selected_category = self.category_var.get()
        apps = [
            app for app in self.apps
            if (selected_category == "Все категории" or app.get("category") == selected_category)
            and query.casefold() in (
                str(app.get("name", "")) + " " + str(app.get("category", "")) + " " +
                APP_DESCRIPTIONS.get(str(app.get("id")), ("", ""))[0]
            ).casefold()
        ]
        width = max(600, self.app_canvas.winfo_width())
        columns = max(2, min(5, width // 205))
        for index, app in enumerate(apps):
            app_id = str(app.get("id", ""))
            name = str(app.get("name", app_id))
            category = str(app.get("category", "other")).replace("_", " ").title()
            subtitle = APP_DESCRIPTIONS.get(app_id, (category, ""))[0]
            tile = tk.Frame(self.cards_frame, background=SURFACE, padx=12, pady=12,
                            highlightthickness=1, highlightbackground=BORDER)
            tile.grid(row=index // columns, column=index % columns, sticky="nsew",
                      padx=(0, 10), pady=(0, 10))
            tile.grid_columnconfigure(0, weight=1)
            button = tk.Button(
                tile, text=name, command=lambda selected=app_id: self.open_app(selected),
                anchor="w", background=SURFACE, foreground=TEXT,
                activebackground=ACCENT, activeforeground=ON_ACCENT,
                relief="flat", borderwidth=0, padx=2, pady=3,
                font=("Segoe UI Semibold", 11, "bold"),
            )
            button.grid(row=0, column=0, sticky="ew")
            tk.Label(tile, text=subtitle, background=SURFACE, foreground=MUTED,
                     anchor="w", justify="left", wraplength=170,
                     font=("Segoe UI", 9)).grid(row=1, column=0, sticky="ew", pady=(6, 0))
            tk.Label(tile, text=category, background=SURFACE, foreground=ACCENT,
                     anchor="w", font=("Segoe UI", 8, "bold")).grid(row=2, column=0, sticky="ew", pady=(10, 0))
        for column in range(columns):
            self.cards_frame.grid_columnconfigure(column, weight=1, uniform="app")
        self.count_label.configure(text=f"{len(apps)} из {len(self.apps)}")
        self.app_canvas.configure(scrollregion=self.app_canvas.bbox("all"))

    def _update_clock(self) -> None:
        now = datetime.now()
        self.clock_label.configure(text=now.strftime("%H:%M"))
        self.date_label.configure(text=now.strftime("%A, %d %B %Y"))
        self._clock_job = self.root.after(15000, self._update_clock)

    def _show_home(self) -> None:
        self.search_var.set("")
        self.category_var.set("Все категории")
        self._render_apps()

    def _app_info(self, app_id: str) -> tuple[dict[str, Any], str, str]:
        app = self.apps_by_id.get(app_id, {"id": app_id, "name": "Reaper", "category": "developer"})
        subtitle, description = APP_DESCRIPTIONS.get(
            app_id, ("Инструменты разработчика", "Открывает отдельное нативное окно Reaper Studio.")
        )
        return app, subtitle, description

    def open_app(self, app_id: str) -> None:
        if app_id not in self.apps_by_id and app_id != "reaper":
            messagebox.showwarning("Mora", "Это приложение не зарегистрировано.", parent=self.root)
            return
        app, subtitle, description = self._app_info(app_id)
        window = tk.Toplevel(self.root)
        window.title(f"{app.get('name', app_id)} — Mora")
        window.geometry("820x620")
        window.minsize(640, 460)
        window.configure(background=BACKGROUND)

        top = tk.Frame(window, background=SURFACE, padx=22, pady=18)
        top.pack(fill="x")
        tk.Label(top, text=str(app.get("category", "system")).upper(),
                 background=SURFACE, foreground=ACCENT,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(top, text=str(app.get("name", app_id)), background=SURFACE,
                 foreground=TEXT, font=("Segoe UI Semibold", 21, "bold")).pack(anchor="w", pady=(4, 2))
        tk.Label(top, text=subtitle, background=SURFACE, foreground=MUTED,
                 font=("Segoe UI", 10)).pack(anchor="w")
        body = tk.Frame(window, background=BACKGROUND, padx=22, pady=20)
        body.pack(fill="both", expand=True)
        tk.Label(body, text=description, background=BACKGROUND, foreground=SECONDARY,
                 justify="left", wraplength=730, font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 14))

        maturity = str(app.get("maturity", "catalog_concept"))
        label = MATURITY_LABELS.get(maturity, "Каталог приложения")
        tk.Label(body, text=f"СТАТУС: {label}", background=BACKGROUND,
                 foreground=ACCENT, font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 14))

        panel = tk.Frame(body, background=BACKGROUND)
        panel.pack(fill="both", expand=True, anchor="nw")
        if app_id == "workspace":
            self._build_control_panel(panel)
        elif app_id == "security":
            self._build_security_panel(panel)
        elif app_id == "updates":
            self._build_recovery_panel(panel)
        elif app_id == "mora-ai":
            self._build_ai_panel(panel)
        elif app_id == "provenance":
            self._build_proof_panel(panel)
        elif app_id in {"runtime", "exedotexe", "gamecharager"}:
            self._build_bridge_panel(panel)
        elif app_id == "desktop":
            self._build_desktop_panel(panel)
        elif app_id == "reaper":
            self._build_reaper_panel(panel)
        elif app_id == "mora-commons":
            self._build_commons_panel(panel)
        elif app_id == "mora-boost":
            self._build_boost_panel(panel)
        else:
            self._build_catalog_panel(panel, app)

        ttk.Button(body, text="Закрыть", command=window.destroy).pack(anchor="e", pady=(12, 0))

    def _build_control_panel(self, parent: tk.Widget) -> None:
        tk.Label(parent, text="Настройки текущей оболочки", background=BACKGROUND,
                 foreground=TEXT, font=("Segoe UI Semibold", 13, "bold")).pack(anchor="w", pady=(0, 12))
        focus = tk.BooleanVar(value=self.preferences["focusMode"])
        reduced = tk.BooleanVar(value=self.preferences["appearance"]["reducedMotion"])
        density = tk.StringVar(value=self.preferences["appearance"]["density"])
        profile = tk.StringVar(value=self.preferences["powerProfile"])

        ttk.Checkbutton(parent, text="Режим фокуса", variable=focus).pack(anchor="w", pady=5)
        ttk.Checkbutton(parent, text="Уменьшить анимацию интерфейса", variable=reduced).pack(anchor="w", pady=5)
        ttk.Label(parent, text="Плотность", style="Muted.TLabel").pack(anchor="w", pady=(12, 4))
        ttk.Combobox(parent, textvariable=density, values=("comfortable", "compact"),
                     state="readonly", width=24).pack(anchor="w")
        ttk.Label(parent, text="Локальный профиль предпочтений", style="Muted.TLabel").pack(anchor="w", pady=(12, 4))
        ttk.Combobox(parent, textvariable=profile, values=("saver", "balanced", "performance"),
                     state="readonly", width=24).pack(anchor="w")

        def save() -> None:
            self.preferences["focusMode"] = bool(focus.get())
            self.preferences["appearance"]["reducedMotion"] = bool(reduced.get())
            self.preferences["appearance"]["density"] = density.get()
            self.preferences["powerProfile"] = profile.get()
            self.preferences = normalize_preferences(self.preferences)
            if save_preferences(self.preferences):
                self.sidebar_status.configure(text="Настройки Mora сохранены локально")
                messagebox.showinfo("Control", "Настройки сохранены.", parent=parent)
            else:
                messagebox.showerror("Control", "Не удалось сохранить настройки.", parent=parent)

        ttk.Button(parent, text="Сохранить настройки", style="Accent.TButton",
                   command=save).pack(anchor="w", pady=(18, 0))
        ttk.Label(parent, text="Профиль не меняет частоты процессора, драйверы, службы или планировщик ОС.",
                  style="Muted.TLabel", wraplength=690).pack(anchor="w", pady=(16, 0))

    def _build_security_panel(self, parent: tk.Widget) -> None:
        tk.Label(parent, text="Локальные предпочтения разрешений", background=BACKGROUND,
                 foreground=TEXT, font=("Segoe UI Semibold", 13, "bold")).pack(anchor="w", pady=(0, 8))
        variables: dict[str, tk.BooleanVar] = {}
        for capability in self.preferences["permissions"]:
            variable = tk.BooleanVar(value=self.preferences["permissions"][capability])
            variables[capability] = variable
            ttk.Checkbutton(parent, text=f"{capability.capitalize()} — включено в локальном профиле",
                            variable=variable).pack(anchor="w", pady=4)

        def save() -> None:
            self.preferences["permissions"] = {
                name: variable.get() for name, variable in variables.items()
            }
            self.preferences = normalize_preferences(self.preferences)
            if save_preferences(self.preferences):
                messagebox.showinfo("Sentinel", "Локальные предпочтения сохранены.", parent=parent)
            else:
                messagebox.showerror("Sentinel", "Не удалось сохранить профиль.", parent=parent)

        ttk.Button(parent, text="Сохранить профиль", style="Accent.TButton",
                   command=save).pack(anchor="w", pady=(14, 0))
        ttk.Label(parent, text="Важно: эти переключатели не предоставляют и не блокируют доступ на уровне ядра, процессов или устройств. Все системные возможности остаются вне этого профиля.",
                  style="Muted.TLabel", wraplength=710).pack(anchor="w", pady=(14, 0))

    def _build_recovery_panel(self, parent: tk.Widget) -> None:
        tk.Label(parent, text="Резервная копия настроек Mora", background=BACKGROUND,
                 foreground=TEXT, font=("Segoe UI Semibold", 13, "bold")).pack(anchor="w", pady=(0, 8))
        tk.Label(parent, text="В копию входят только настройки оболочки и локальные предпочтения. Пользовательские файлы и разделы DuckOS не затрагиваются.",
                 background=BACKGROUND, foreground=MUTED, wraplength=710,
                 justify="left").pack(anchor="w", pady=(0, 14))

        def export_snapshot() -> None:
            snapshot = create_recovery_snapshot(self.preferences)
            destination = filedialog.asksaveasfilename(
                parent=parent, title="Экспортировать настройки Mora",
                defaultextension=".json", filetypes=[("JSON", "*.json")],
                initialfile="mora-settings-backup.json",
            )
            if not destination:
                return
            try:
                Path(destination).write_text(
                    json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            except OSError as error:
                messagebox.showerror("Restore", str(error), parent=parent)
            else:
                messagebox.showinfo("Restore", "Копия настроек сохранена.", parent=parent)

        def import_snapshot() -> None:
            source = filedialog.askopenfilename(
                parent=parent, title="Выбрать копию настроек Mora",
                filetypes=[("JSON", "*.json")],
            )
            if not source:
                return
            try:
                candidate = json.loads(Path(source).read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                messagebox.showerror("Restore", f"Не удалось прочитать копию: {error}", parent=parent)
                return
            snapshot = validate_recovery_snapshot(candidate)
            if snapshot is None:
                messagebox.showerror("Restore", "Формат копии не поддерживается.", parent=parent)
                return
            if not messagebox.askyesno("Restore", "Заменить текущие настройки Mora содержимым копии?", parent=parent):
                return
            if not save_preferences(snapshot["preferences"]):
                messagebox.showerror("Restore", "Не удалось сохранить восстановленные настройки.", parent=parent)
                return
            self.preferences = snapshot["preferences"]
            messagebox.showinfo("Restore", "Настройки восстановлены.", parent=parent)

        ttk.Button(parent, text="Экспортировать копию", style="Accent.TButton",
                   command=export_snapshot).pack(anchor="w", pady=4)
        ttk.Button(parent, text="Восстановить из JSON", command=import_snapshot).pack(anchor="w", pady=4)

    def _build_ai_panel(self, parent: tk.Widget) -> None:
        tk.Label(parent, text="Опишите простое действие", background=BACKGROUND,
                 foreground=TEXT, font=("Segoe UI Semibold", 13, "bold")).pack(anchor="w", pady=(0, 8))
        query = tk.StringVar()
        ttk.Entry(parent, textvariable=query).pack(fill="x", pady=(0, 10))
        output = tk.Text(parent, height=10, wrap="word", background=SURFACE,
                         foreground=TEXT, insertbackground=ACCENT, relief="flat",
                         padx=12, pady=10)
        output.pack(fill="both", expand=True)
        state: dict[str, Any] = {"plan": None}

        def preview() -> None:
            result = build_intent_plan(query.get())
            state["plan"] = result if result.get("ok") else None
            output.configure(state="normal")
            output.delete("1.0", "end")
            output.insert("end", result.get("message", "План отсутствует."))
            if result.get("ok"):
                output.insert("end", "\n\n" + json.dumps(result["actions"], ensure_ascii=False, indent=2))
            output.configure(state="disabled")

        def approve() -> None:
            plan = state["plan"]
            if not plan:
                messagebox.showwarning("Mora AI", "Сначала подготовьте допустимый план.", parent=parent)
                return
            if not messagebox.askyesno("Mora AI", "Применить показанный локальный план?", parent=parent):
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
            self.preferences = normalize_preferences(self.preferences)
            if not save_preferences(self.preferences):
                messagebox.showerror("Mora AI", "Не удалось сохранить настройки.", parent=parent)
            else:
                messagebox.showinfo("Mora AI", "Локальный план применён.", parent=parent)

        actions = tk.Frame(parent, background=BACKGROUND)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Подготовить план", style="Accent.TButton",
                   command=preview).pack(side="left")
        ttk.Button(actions, text="Подтвердить план", command=approve).pack(side="left", padx=8)
        ttk.Label(parent, text="Mora AI в этой версии — локальный ограниченный rule-engine. Он не запускает командную строку, не исполняет произвольный код и не вызывает внешнюю модель.",
                  style="Muted.TLabel", wraplength=710).pack(anchor="w", pady=(12, 0))

    def _build_proof_panel(self, parent: tk.Widget) -> None:
        result = tk.Text(parent, height=8, wrap="word", background=SURFACE,
                         foreground=TEXT, relief="flat", padx=12, pady=10)
        result.pack(fill="x", pady=(0, 10))

        def choose_file() -> None:
            path = filedialog.askopenfilename(parent=parent, title="Выбрать файл для SHA-256")
            if not path:
                return
            try:
                report = calculate_sha256(path)
            except ValueError as error:
                messagebox.showerror("Proof", str(error), parent=parent)
                return
            result.configure(state="normal")
            result.delete("1.0", "end")
            result.insert("end", json.dumps(report, ensure_ascii=False, indent=2))
            result.configure(state="disabled")

        ttk.Button(parent, text="Вычислить SHA-256", style="Accent.TButton",
                   command=choose_file).pack(anchor="w")
        ttk.Label(parent, text="Локальное хэширование не доказывает авторство, подпись или происхождение файла.",
                  style="Muted.TLabel", wraplength=700).pack(anchor="w", pady=(12, 0))

    def _build_bridge_panel(self, parent: tk.Widget) -> None:
        output = tk.Text(parent, height=14, wrap="word", background=SURFACE,
                         foreground=TEXT, relief="flat", padx=12, pady=10)
        output.pack(fill="both", expand=True, pady=(0, 10))

        def inspect_file() -> None:
            from ..compat.bridge import inspect_binary

            path = filedialog.askopenfilename(
                parent=parent, title="Выбрать PE/ELF-файл",
                filetypes=[("Исполняемые файлы", "*.exe *.dll *.sys *.elf"), ("Все файлы", "*.*")],
            )
            if not path:
                return
            try:
                report = inspect_binary(Path(path))
            except (OSError, ValueError, RuntimeError) as error:
                messagebox.showerror("Bridge", str(error), parent=parent)
                return
            output.configure(state="normal")
            output.delete("1.0", "end")
            output.insert("end", json.dumps(report, ensure_ascii=False, indent=2))
            output.configure(state="disabled")

        ttk.Button(parent, text="Выбрать файл и проверить заголовки",
                   style="Accent.TButton", command=inspect_file).pack(anchor="w")
        ttk.Label(parent, text="Файл только читается. Запуск, распаковка, загрузка DLL и установка runtime не выполняются.",
                  style="Muted.TLabel", wraplength=700).pack(anchor="w", pady=(12, 0))

    def _build_desktop_panel(self, parent: tk.Widget) -> None:
        from ..desktop.service import audit_desktop

        output = tk.Text(parent, height=14, wrap="word", background=SURFACE,
                         foreground=TEXT, relief="flat", padx=12, pady=10)
        output.pack(fill="both", expand=True, pady=(0, 10))

        def refresh() -> None:
            try:
                report = audit_desktop()
            except (OSError, ValueError, RuntimeError) as error:
                report = {"error": str(error)}
            output.configure(state="normal")
            output.delete("1.0", "end")
            output.insert("end", json.dumps(report, ensure_ascii=False, indent=2))
            output.configure(state="disabled")

        def launch() -> None:
            command = [sys.executable, "-m", "duckos", "desktop", "gui"]
            try:
                subprocess.Popen(command, shell=False, close_fds=True)
            except OSError as error:
                messagebox.showerror("Duck Desktop", str(error), parent=parent)

        actions = tk.Frame(parent, background=BACKGROUND)
        actions.pack(fill="x")
        ttk.Button(actions, text="Обновить аудит", command=refresh).pack(side="left")
        ttk.Button(actions, text="Открыть Duck Desktop", style="Accent.TButton",
                   command=launch).pack(side="left", padx=8)
        refresh()

    def _build_reaper_panel(self, parent: tk.Widget) -> None:
        from ..desktop.reaper import ReaperWorkbench

        workbench = ReaperWorkbench()
        report = workbench.inspect()
        output = tk.Text(parent, height=12, wrap="word", background=SURFACE,
                         foreground=TEXT, relief="flat", padx=12, pady=10)
        output.pack(fill="both", expand=True, pady=(0, 10))
        output.insert("end", json.dumps(report, ensure_ascii=False, indent=2))
        output.configure(state="disabled")

        def open_studio() -> None:
            try:
                process = workbench.open_studio()
            except (OSError, ValueError, RuntimeError) as error:
                messagebox.showerror("Reaper", str(error), parent=parent)
            else:
                messagebox.showinfo("Reaper", f"Reaper Studio открыт. PID: {process.pid}", parent=parent)

        ttk.Button(parent, text="Открыть Reaper Studio", style="Accent.TButton",
                   command=open_studio).pack(anchor="w")

    def _build_commons_panel(self, parent: tk.Widget) -> None:
        search = tk.StringVar()
        category = tk.StringVar(value="all")
        controls = tk.Frame(parent, background=BACKGROUND)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Entry(controls, textvariable=search).pack(side="left", fill="x", expand=True)
        category_values = ["all"] + [item["id"] for item in self.commons.get("categories", [])]
        ttk.Combobox(controls, textvariable=category, values=category_values,
                     state="readonly", width=18).pack(side="left", padx=(8, 0))
        listing = tk.Listbox(parent, background=SURFACE, foreground=TEXT,
                             selectbackground=ACCENT, selectforeground=ON_ACCENT,
                             relief="flat", height=12)
        listing.pack(fill="both", expand=True)
        details = tk.Text(parent, height=5, wrap="word", background=SURFACE,
                          foreground=SECONDARY, relief="flat", padx=10, pady=8)
        details.pack(fill="x", pady=(10, 0))
        matches: list[dict[str, Any]] = []

        def render(_event: Any = None) -> None:
            nonlocal matches
            matches = filter_commons_apps(self.commons.get("apps", []), search.get(), category.get())
            listing.delete(0, "end")
            for app in matches:
                listing.insert("end", f"{app.get('name')}  ·  {app.get('subtitle')}")
            details.configure(state="normal")
            details.delete("1.0", "end")
            if not matches:
                details.insert("end", "Нет совпадений.")
            elif matches:
                details.insert("end", matches[0].get("description", ""))
            details.configure(state="disabled")

        def select_item(_event: Any = None) -> None:
            selected = listing.curselection()
            if not selected or selected[0] >= len(matches):
                return
            details.configure(state="normal")
            details.delete("1.0", "end")
            details.insert("end", matches[selected[0]].get("description", ""))
            details.configure(state="disabled")

        search.trace_add("write", render)
        category.trace_add("write", render)
        listing.bind("<<ListboxSelect>>", select_item)
        render()

    def _build_boost_panel(self, parent: tk.Widget) -> None:
        ttk.Label(parent, text="OPlague Gaming Lab подключается как отдельный проект.",
                  style="Muted.TLabel", wraplength=690).pack(anchor="w")
        ttk.Label(parent, text="Mora не меняет драйверы, частоты, напряжение, приоритеты процессов или параметры ядра. Для игровой диагностики используйте самостоятельные команды DuckOS и OPlague.",
                  style="Muted.TLabel", wraplength=690).pack(anchor="w", pady=(12, 0))
        ttk.Button(parent, text="Показать статус интеграции",
                   command=lambda: messagebox.showinfo(
                       "Mora Boost",
                       "Интеграция описана в документации. Автоматическое управление оборудованием этой панелью не выполняется.",
                       parent=parent,
                   )).pack(anchor="w", pady=(14, 0))

    def _build_catalog_panel(self, parent: tk.Widget, app: dict[str, Any]) -> None:
        app_id = str(app.get("id", ""))
        maturity = str(app.get("maturity", ""))
        note = (
            "Это зарегистрированное приложение каталога. Его браузерная версия удалена. "
            "Нативные функции подключаются отдельно и не считаются реализованными только из-за наличия карточки."
        )
        if maturity == "partial_local_workspace":
            note = (
                "Нативная точка входа подготовлена. Полноценная реализация данных и системных сервисов "
                "для этого приложения остаётся отдельной задачей."
            )
        ttk.Label(parent, text=note, style="Muted.TLabel",
                  wraplength=700, justify="left").pack(anchor="w", pady=(0, 12))
        ttk.Label(parent, text=f"Идентификатор: {app_id}",
                  style="Muted.TLabel").pack(anchor="w")
        ttk.Label(parent, text=f"Категория: {app.get('category', 'other')}",
                  style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

    def close(self) -> None:
        if self._clock_job:
            try:
                self.root.after_cancel(self._clock_job)
            except tk.TclError:
                pass
        self.root.destroy()


def run_native_mora() -> int:
    root = tk.Tk()
    MoraWindow(root)
    root.mainloop()
    return 0


def main() -> int:
    return run_native_mora()


if __name__ == "__main__":
    raise SystemExit(main())
