"""Native settings panel for Duck Desktop.

All edits are user-scoped configuration drafts. Applying a form saves a profile;
it does not silently change host networking, firmware, drivers or power limits.
"""
from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from pathlib import Path
from typing import Any

from ..settings import SettingsStore, default_profile, network_probe, settings_search, validate_profile


class SettingsPanel(ttk.Frame):
    SECTIONS = ("network", "power", "appearance", "security", "profiles", "history")
    TITLES = {
        "network": "Сеть",
        "power": "Питание",
        "appearance": "Внешний вид",
        "security": "Безопасность",
        "profiles": "Профили",
        "history": "История и диагностика",
    }

    def __init__(self, parent: tk.Misc, store: SettingsStore | None = None) -> None:
        super().__init__(parent, padding=14)
        self.store = store or SettingsStore()
        self.store.save()
        self.active_name, self.profile = self.store.active_profile()
        self._loaded = json.loads(json.dumps(self.profile))
        self._loading = False
        self._dirty = False
        self._last_tab = 0
        self._variables: dict[str, tk.Variable] = {}
        self.status = tk.StringVar(value="Параметры хранятся в пользовательском профиле Duck.")
        self.breadcrumb = tk.StringVar(value="Duck → Настройки → Сеть")
        self.search_text = tk.StringVar()
        self.profile_choice = tk.StringVar(value=self.active_name)
        self.host_test = tk.StringVar(value="example.com")
        self.snapshot_selection: str | None = None

        self._build()
        self._load_profile()

    def _build(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="ЦЕНТР НАСТРОЕК DUCK", font=("Segoe UI Semibold", 16)).pack(anchor="w")
        ttk.Label(header, textvariable=self.breadcrumb).pack(anchor="w", pady=(3, 0))

        search_row = ttk.Frame(self)
        search_row.pack(fill="x", pady=(6, 10))
        ttk.Label(search_row, text="Найти параметр").pack(side="left")
        search = ttk.Entry(search_row, textvariable=self.search_text)
        search.pack(side="left", fill="x", expand=True, padx=8)
        search.bind("<KeyRelease>", self._search)
        ttk.Button(search_row, text="Очистить", command=lambda: self.search_text.set("")).pack(side="right")

        self.search_results = tk.Listbox(self, height=3, activestyle="dotbox", exportselection=False)
        self.search_results.pack(fill="x", pady=(0, 8))
        self.search_results.bind("<<ListboxSelect>>", self._open_search_result)
        self.search_results.pack_forget()

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)
        self.pages: dict[str, ttk.Frame] = {}
        for section in self.SECTIONS:
            shell = ttk.Frame(self.tabs)
            canvas = tk.Canvas(
                shell,
                highlightthickness=0,
                background=ttk.Style(self).lookup("TFrame", "background") or "#101010",
            )
            scrollbar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            page = ttk.Frame(canvas, padding=12)
            window_id = canvas.create_window((0, 0), window=page, anchor="nw")
            page.bind("<Configure>", lambda _event, target=canvas: target.configure(scrollregion=target.bbox("all")))
            canvas.bind("<Configure>", lambda event, target=canvas, item=window_id: target.itemconfigure(item, width=event.width))
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            self.pages[section] = page
            self.tabs.add(shell, text=self.TITLES[section])

        self._build_network(self.pages["network"])
        self._build_power(self.pages["power"])
        self._build_appearance(self.pages["appearance"])
        self._build_security(self.pages["security"])
        self._build_profiles(self.pages["profiles"])
        self._build_history(self.pages["history"])

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Применить в профиль", command=self._apply_current).pack(side="left")
        ttk.Button(actions, text="Отменить правки", command=self._discard_current).pack(side="left", padx=6)
        ttk.Button(actions, text="Значения по умолчанию", command=self._reset_current).pack(side="left")
        ttk.Label(self, textvariable=self.status, wraplength=900).pack(anchor="w", pady=(8, 0))
        self.tabs.bind("<<NotebookTabChanged>>", self._tab_changed)
        self.bind("<Escape>", lambda _event: self.focus_set())

    def _row(self, parent: ttk.Frame, label: str, key: str, default: Any, row: int, *, width: int = 24) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
        variable = tk.StringVar(value=str(default))
        variable.trace_add("write", self._mark_dirty)
        self._variables[key] = variable
        entry = ttk.Entry(parent, textvariable=variable, width=width)
        entry.grid(row=row, column=1, sticky="ew", pady=4)
        return entry

    def _choice(self, parent: ttk.Frame, label: str, key: str, values: tuple[str, ...], default: str, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
        variable = tk.StringVar(value=default)
        variable.trace_add("write", self._mark_dirty)
        self._variables[key] = variable
        ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=21).grid(
            row=row, column=1, sticky="ew", pady=4
        )

    def _toggle(self, parent: ttk.Frame, label: str, key: str, default: bool, row: int) -> None:
        variable = tk.BooleanVar(value=default)
        variable.trace_add("write", self._mark_dirty)
        self._variables[key] = variable
        ttk.Checkbutton(parent, text=label, variable=variable).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=4
        )

    def _build_network(self, page: ttk.Frame) -> None:
        ttk.Label(
            page,
            text="Редактируется профиль подключения. Сохранение не переключает сетевой адаптер и не меняет маршруты хоста.",
            wraplength=850,
        ).pack(anchor="w", pady=(0, 10))
        form = ttk.Frame(page)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        self._toggle(form, "Использовать IPv4 в этом профиле", "network.ipv4_enabled", True, 0)
        self._choice(form, "IPv4", "network.ipv4_method", ("dhcp", "static"), "dhcp", 1)
        self._row(form, "IPv4-адрес", "network.ipv4_address", "", 2)
        self._row(form, "Длина префикса", "network.ipv4_prefix", 24, 3)
        self._row(form, "Маска подсети", "network.ipv4_netmask", "255.255.255.0", 4)
        self._row(form, "Шлюз", "network.ipv4_gateway", "", 5)
        self._toggle(form, "Использовать IPv6 в этом профиле", "network.ipv6_enabled", True, 6)
        self._choice(form, "IPv6", "network.ipv6_method", ("auto", "static"), "auto", 7)
        self._row(form, "IPv6-адрес", "network.ipv6_address", "", 8)
        self._row(form, "IPv6-префикс", "network.ipv6_prefix", 64, 9)
        self._row(form, "IPv6-шлюз", "network.ipv6_gateway", "", 10)
        self._row(form, "DNS 1", "network.dns_primary", "", 11)
        self._row(form, "DNS 2", "network.dns_secondary", "", 12)
        self._row(form, "DNS over HTTPS", "network.doh_url", "", 13)
        self._row(form, "DNS over TLS · сервер", "network.dot_server", "", 14)
        self._row(form, "MTU", "network.mtu", 1500, 15)
        self._toggle(form, "Использовать прокси в этом профиле", "network.proxy_enabled", False, 16)
        self._row(form, "Адрес прокси", "network.proxy_url", "", 17)
        form.columnconfigure(1, weight=1)

        test_row = ttk.Frame(page)
        test_row.pack(fill="x", pady=(12, 0))
        ttk.Label(test_row, text="Проверка DNS и TCP").pack(side="left")
        ttk.Entry(test_row, textvariable=self.host_test, width=24).pack(side="left", padx=8)
        ttk.Button(test_row, text="Проверить узел", command=self._probe_network).pack(side="left")

    def _build_power(self, page: ttk.Frame) -> None:
        ttk.Label(
            page,
            text="Профиль описывает предпочтения. Изменение лимитов CPU/GPU, реального заряда и сна требует платформенной службы питания.",
            wraplength=850,
        ).pack(anchor="w", pady=(0, 10))
        form = ttk.Frame(page)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        self._choice(form, "Режим", "power.mode", ("eco", "quiet", "balanced", "performance", "maximum"), "balanced", 0)
        self._row(form, "Автоэкономия · порог %", "power.eco_threshold", 20, 1)
        self._toggle(form, "Включать автоэкономию только от батареи", "power.eco_only_on_battery", True, 2)
        self._row(form, "Лимит заряда · %", "power.charge_limit", 80, 3)
        self._row(form, "Экран от сети · минут (0 = никогда)", "power.screen_timeout_ac", 10, 4)
        self._row(form, "Экран от батареи · минут", "power.screen_timeout_battery", 5, 5)
        self._row(form, "Сон от сети · минут (0 = никогда)", "power.sleep_timeout_ac", 30, 6)
        self._row(form, "Сон от батареи · минут", "power.sleep_timeout_battery", 15, 7)
        ttk.Label(page, text="Данные аккумулятора зависят от драйвера и могут быть недоступны на настольном ПК.").pack(anchor="w", pady=(12, 0))

    def _build_appearance(self, page: ttk.Frame) -> None:
        ttk.Label(page, text="Предпросмотр токенов оформления будет показан ниже. Изменения сохраняются в профиле Duck.", wraplength=850).pack(anchor="w", pady=(0, 10))
        form = ttk.Frame(page)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        self._choice(form, "Тема", "appearance.theme", ("system", "light", "dark"), "system", 0)
        self._row(form, "Акцент #RRGGBB", "appearance.accent", "#FFD400", 1)
        self._row(form, "Масштаб UI · 0.75–2.0", "appearance.ui_scale", 1.0, 2)
        self._row(form, "Масштаб иконок · 0.75–2.0", "appearance.icon_scale", 1.0, 3)
        self._choice(form, "Плотность", "appearance.density", ("compact", "comfortable"), "comfortable", 4)
        self._toggle(form, "Уменьшить анимацию", "appearance.reduced_motion", False, 5)
        self.preview = ttk.Label(page, text="Duck · пример интерфейса · акцент #FFD400")
        self.preview.pack(anchor="w", pady=(16, 0))

    def _build_security(self, page: ttk.Frame) -> None:
        ttk.Label(
            page,
            text="Параметры сеанса сохраняются как профиль пользователя. Фактическая блокировка экрана и защита сеанса должны выполняться системной службой Duck.",
            wraplength=850,
        ).pack(anchor="w", pady=(0, 10))
        form = ttk.Frame(page)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        self._row(form, "Автоблокировка · минут (0 = выключена)", "security.auto_lock_minutes", 5, 0)
        self._toggle(form, "Требовать блокировку при переходе в сон", "security.lock_on_sleep", True, 1)
        ttk.Label(
            page,
            text="Это сохранённая политика предпочтений, а не действующий механизм аутентификации или блокировки.",
            wraplength=850,
        ).pack(anchor="w", pady=(12, 0))

    def _build_profiles(self, page: ttk.Frame) -> None:
        ttk.Label(page, text="Профили — это согласованные наборы пользовательских предпочтений, а не переключатели драйверов.", wraplength=850).pack(anchor="w", pady=(0, 10))
        row = ttk.Frame(page)
        row.pack(fill="x")
        ttk.Label(row, text="Выбранный профиль").pack(side="left")
        self.profile_box = ttk.Combobox(row, textvariable=self.profile_choice, state="readonly", width=22)
        self.profile_box.pack(side="left", padx=8)
        self.profile_box.bind("<<ComboboxSelected>>", self._select_profile)
        ttk.Button(row, text="Создать копию…", command=self._create_profile).pack(side="left", padx=5)
        ttk.Button(row, text="Сделать активным", command=self._activate_profile).pack(side="left")
        self.profile_summary = tk.Text(page, height=12, wrap="word", state="disabled")
        self.profile_summary.pack(fill="both", expand=True, pady=(12, 0))
        ttk.Label(page, text="Дом · Работа · Игра · Дорога — начальные профили; каждый можно настроить независимо.", wraplength=850).pack(anchor="w", pady=(8, 0))

    def _build_history(self, page: ttk.Frame) -> None:
        top = ttk.Frame(page)
        top.pack(fill="x")
        ttk.Button(top, text="Обновить", command=self._refresh_history).pack(side="left")
        ttk.Button(top, text="Экспорт JSON…", command=self._export).pack(side="left", padx=6)
        ttk.Button(top, text="Импорт JSON…", command=self._import).pack(side="left")
        ttk.Button(top, text="Снимки состояния", command=self._refresh_history).pack(side="left", padx=6)
        self.history = tk.Text(page, height=17, wrap="word", state="disabled")
        self.history.pack(fill="both", expand=True, pady=(10, 0))
        self._refresh_history()

    def _mark_dirty(self, *_args: Any) -> None:
        if not self._loading:
            self._dirty = True
            self.status.set("Есть несохранённые изменения формы.")
            self._update_preview()

    def _section_values(self, section: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, variable in self._variables.items():
            prefix, field = key.split(".", 1)
            if prefix != section:
                continue
            value = variable.get()
            if key.endswith("_enabled") or key.endswith("_only_on_battery") or key.endswith("_motion") or key.endswith("_on_sleep"):
                value = bool(value)
            elif key.endswith("_prefix") or key.endswith("_threshold") or key.endswith("_limit") or key.endswith("_timeout_ac") or key.endswith("_timeout_battery") or key.endswith("_minutes") or key.endswith(".mtu"):
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    value = value
            elif key.endswith("_scale"):
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    value = value
            result[field] = value
        return result

    def _current_section(self) -> str:
        index = self.tabs.index(self.tabs.select())
        return self.SECTIONS[index]

    def _load_profile(self) -> None:
        self._loading = True
        try:
            self.profile = self.store.active_profile()[1] if self.active_name == self.store.active_profile()[0] else self.store.load()["profiles"][self.active_name]
            for key, variable in self._variables.items():
                section, field = key.split(".", 1)
                value = self.profile[section][field]
                variable.set(str(value) if not isinstance(value, bool) else value)
            self.profile_choice.set(self.active_name)
            self.profile_box.configure(values=self.store.list_profiles())
            self._loaded = json.loads(json.dumps(self.profile))
            self._dirty = False
            self._update_preview()
            self._refresh_profile_summary()
            self.status.set(f"Профиль «{self.active_name}» загружен. Изменения ещё не применены.")
            self.breadcrumb.set(f"Duck → Настройки → {self.TITLES[self._current_section()]}")
        finally:
            self._loading = False

    def _update_preview(self) -> None:
        if not hasattr(self, "preview"):
            return
        accent = self._variables["appearance.accent"].get()
        theme = self._variables["appearance.theme"].get()
        scale = self._variables["appearance.ui_scale"].get()
        self.preview.configure(text=f"Предпросмотр · {theme} · {accent} · масштаб {scale}")
        try:
            self.preview.configure(foreground=accent)
        except tk.TclError:
            pass

    def _open_search_result(self, _event: tk.Event | None = None) -> None:
        selection = self.search_results.curselection()
        if not selection:
            return
        item = self._search_rows[selection[0]]
        if self._dirty:
            self.status.set("Сохраните или отмените изменения перед переходом из текущей формы.")
            self.search_results.selection_clear(0, "end")
            return
        index = self.SECTIONS.index(item["section"])
        self.tabs.select(index)
        self.breadcrumb.set("Duck → Настройки → " + item["path"])

    def _search(self, _event: tk.Event | None = None) -> None:
        self._search_rows = settings_search(self.search_text.get())
        self.search_results.delete(0, "end")
        for item in self._search_rows[:20]:
            self.search_results.insert("end", f"{item['title']}   ·   {item['path']}")
        if self.search_text.get().strip():
            self.search_results.pack(fill="x", pady=(0, 8), before=self.tabs)
        else:
            self.search_results.pack_forget()

    def _tab_changed(self, _event: tk.Event | None = None) -> None:
        current = self.tabs.index(self.tabs.select())
        if current != self._last_tab and self._dirty:
            answer = messagebox.askyesnocancel(
                "Несохранённые изменения",
                "Сохранить текущий раздел перед переходом?\nДа — сохранить, Нет — отменить правки, Отмена — остаться здесь.",
                parent=self.winfo_toplevel(),
            )
            if answer is None:
                self.tabs.select(self._last_tab)
                return
            if answer:
                if not self._apply_section(self.SECTIONS[self._last_tab]):
                    self.tabs.select(self._last_tab)
                    return
            else:
                self._load_profile()
        self._last_tab = current
        self.breadcrumb.set(f"Duck → Настройки → {self.TITLES[self.SECTIONS[current]]}")
        if self.SECTIONS[current] == "history":
            self._refresh_history()
        elif self.SECTIONS[current] == "profiles":
            self._refresh_profile_summary()

    def _apply_current(self) -> None:
        section = self._current_section()
        if section in {"profiles", "history"}:
            self.status.set("Выберите профиль или действие в этой вкладке.")
            return
        self._apply_section(section)

    def _apply_section(self, section: str) -> bool:
        errors = validate_profile({
            **self.profile,
            section: self._section_values(section),
        })
        relevant = [
            item for item in errors
            if item["field"].startswith(section + ".")
            or (section == "network" and item["field"] == "locale")
        ]
        if relevant:
            first = relevant[0]
            self.status.set(f"Ошибка · {first['field']}: {first['message']}")
            return False
        try:
            result = self.store.update_profile(self.active_name, section, self._section_values(section))
        except (OSError, ValueError) as error:
            self.status.set(f"Не сохранено · {error}")
            return False
        self.profile = self.store.load()["profiles"][self.active_name]
        self._loaded = json.loads(json.dumps(self.profile))
        self._dirty = False
        self.status.set(f"Раздел «{self.TITLES[section]}» сохранён. Системные параметры хоста не изменялись.")
        self._refresh_profile_summary()
        self._refresh_history()
        return not bool(result.get("system_changes_performed"))

    def _discard_current(self) -> None:
        self._load_profile()

    def _reset_current(self) -> None:
        section = self._current_section()
        if section not in {"network", "power", "appearance", "security"}:
            self.status.set("Сброс доступен для сети, питания, оформления и предпочтений сеанса.")
            return
        if not messagebox.askyesno("Сброс раздела", f"Вернуть только раздел «{self.TITLES[section]}» к значениям по умолчанию?", parent=self.winfo_toplevel()):
            return
        self._loading = True
        defaults = default_profile()[section]
        for key, variable in self._variables.items():
            prefix, field = key.split(".", 1)
            if prefix == section:
                value = defaults[field]
                variable.set(str(value) if not isinstance(value, bool) else value)
        self._loading = False
        self._dirty = True
        self.status.set("Раздел сброшен в форме. Нажмите «Применить в профиль», чтобы сохранить.")

    def _select_profile(self, _event: tk.Event | None = None) -> None:
        if self._dirty:
            messagebox.showwarning("Профили", "Сначала сохраните или отмените текущие правки.", parent=self.winfo_toplevel())
            self.profile_choice.set(self.active_name)
            return
        self.active_name = self.profile_choice.get()
        self.profile = self.store.load()["profiles"][self.active_name]
        self._load_profile()
        self.status.set(f"Открыт профиль «{self.active_name}». Активный в настройках системы: {self.store.load()['active_profile']}.")

    def _create_profile(self) -> None:
        name = simpledialog.askstring("Новый профиль", "Имя профиля:", parent=self.winfo_toplevel())
        if not name:
            return
        try:
            self.store.create_profile(name, clone_from=self.active_name)
        except (OSError, ValueError) as error:
            messagebox.showerror("Профили", str(error), parent=self.winfo_toplevel())
            return
        self.active_name = name
        self.profile_choice.set(name)
        self._load_profile()

    def _activate_profile(self) -> None:
        if self._dirty:
            messagebox.showwarning("Профили", "Сначала сохраните или отмените текущие правки.", parent=self.winfo_toplevel())
            return
        try:
            self.store.activate_profile(self.active_name)
        except (OSError, ValueError) as error:
            self.status.set(str(error))
            return
        self.status.set(f"Профиль «{self.active_name}» выбран как активный профиль настроек. Аппаратные параметры не переключались.")
        self._refresh_history()

    def _refresh_profile_summary(self) -> None:
        if not hasattr(self, "profile_summary"):
            return
        data = self.store.load()
        lines = [f"Активный профиль: {data['active_profile']}", ""]
        for name, profile in sorted(data["profiles"].items()):
            network = profile["network"]
            power = profile["power"]
            appearance = profile["appearance"]
            mode = network["ipv4_method"].upper() if network["ipv4_enabled"] else "IPv4 выкл."
            if network["ipv4_method"] == "static" and network["ipv4_address"]:
                mode += " · " + network["ipv4_address"] + "/" + str(network["ipv4_prefix"])
            lines.append(f"{name} · {mode} · {power['mode']} · {appearance['theme']} · {appearance['accent']}")
        self.profile_summary.configure(state="normal")
        self.profile_summary.delete("1.0", "end")
        self.profile_summary.insert("1.0", "\n".join(lines))
        self.profile_summary.configure(state="disabled")

    def _probe_network(self) -> None:
        host = self.host_test.get().strip()
        try:
            result = network_probe(host)
        except ValueError as error:
            self.status.set(str(error))
            return
        self.status.set(
            f"Проверка {host}: {'успешно' if result['ok'] else 'ошибка ' + result['stage']} · "
            + json.dumps(result, ensure_ascii=False)
        )

    def _refresh_history(self) -> None:
        if not hasattr(self, "history"):
            return
        lines = ["СНИМКИ СОСТОЯНИЯ"]
        for item in self.store.snapshots():
            lines.append(f"• {item['id']} · {item['size_bytes']} Б")
        lines.extend(["", "ЖУРНАЛ ИЗМЕНЕНИЙ"])
        for item in self.store.events(100):
            lines.append(f"• {item['time_unix']} · {item['action']} · {item.get('details', {})}")
        if len(lines) == 2:
            lines.append("Пока нет событий.")
        self.history.configure(state="normal")
        self.history.delete("1.0", "end")
        self.history.insert("1.0", "\n".join(lines))
        self.history.configure(state="disabled")

    def _export(self) -> None:
        filename = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(), title="Экспорт настроек Duck",
            defaultextension=".json", filetypes=(("JSON", "*.json"),),
        )
        if not filename:
            return
        try:
            result = self.store.export_to(filename)
        except (OSError, ValueError) as error:
            messagebox.showerror("Экспорт", str(error), parent=self.winfo_toplevel())
            return
        self.status.set(f"Настройки экспортированы: {result['path']}")

    def _import(self) -> None:
        filename = filedialog.askopenfilename(
            parent=self.winfo_toplevel(), title="Импорт настроек Duck",
            filetypes=(("JSON", "*.json"),),
        )
        if not filename:
            return
        if not messagebox.askyesno("Импорт настроек", "Проверить файл, сохранить текущий снимок и заменить пользовательскую конфигурацию?", parent=self.winfo_toplevel()):
            return
        try:
            self.store.import_from(filename)
        except (OSError, ValueError) as error:
            messagebox.showerror("Импорт", str(error), parent=self.winfo_toplevel())
            return
        data = self.store.load()
        self.active_name = data["active_profile"]
        self._load_profile()
        self._refresh_history()
