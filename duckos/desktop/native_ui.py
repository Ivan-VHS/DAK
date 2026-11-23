"""Tk-based native user-space maintenance window for Duck Desktop."""
from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from .service import DesktopService, move_desktop_items_to_inbox

COLORS = {
    "background": "#101010", "surface": "#1B1B1B", "raised": "#252525",
    "text": "#F7F7F7", "muted": "#BDBDBD", "accent": "#FFD400",
    "accent_text": "#111111", "border": "#454545",
}


class DesktopWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.service = DesktopService()
        self.report: dict[str, Any] = {}
        root.title("Duck Desktop — обслуживание рабочего пространства")
        root.geometry("1040x700")
        root.minsize(820, 560)
        root.configure(bg=COLORS["background"])
        self._style()
        self._build()

    def _style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=COLORS["background"])
        style.configure("TLabel", background=COLORS["background"], foreground=COLORS["text"], font=("Segoe UI", 10))
        style.configure("Muted.TLabel", foreground=COLORS["muted"])
        style.configure("Title.TLabel", foreground=COLORS["accent"], font=("Segoe UI Semibold", 20))
        style.configure("TButton", padding=(12, 8), background=COLORS["raised"], foreground=COLORS["text"], bordercolor=COLORS["border"])
        style.map("TButton", background=[("active", COLORS["accent"])], foreground=[("active", COLORS["accent_text"])])
        style.configure("Accent.TButton", padding=(14, 9), background=COLORS["accent"], foreground=COLORS["accent_text"], font=("Segoe UI Semibold", 10))
        style.configure("TNotebook", background=COLORS["background"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 9), background=COLORS["raised"], foreground=COLORS["text"])
        style.map("TNotebook.Tab", background=[("selected", COLORS["accent"])], foreground=[("selected", COLORS["accent_text"])])
        style.configure("Treeview", background=COLORS["surface"], fieldbackground=COLORS["surface"], foreground=COLORS["text"], rowheight=28)
        style.configure("Treeview.Heading", background=COLORS["raised"], foreground=COLORS["accent"])

    def _build(self) -> None:
        header = ttk.Frame(self.root, padding=(22, 18, 22, 12))
        header.pack(fill="x")
        ttk.Label(header, text="DUCK DESKTOP", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Нативное обслуживание рабочего пространства · только пользовательские данные", style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

        tabs = ttk.Notebook(self.root)
        tabs.pack(fill="both", expand=True, padx=20, pady=(4, 20))
        overview, clean, startup, processes, rules = [ttk.Frame(tabs, padding=18) for _ in range(5)]
        for tab, title in zip((overview, clean, startup, processes, rules), ("Обзор", "Рабочий стол", "Автозагрузка", "Процессы", "Правила")):
            tabs.add(tab, text=title)

        self.overview = tk.Text(overview, wrap="word", bg=COLORS["surface"], fg=COLORS["text"], insertbackground=COLORS["accent"], relief="flat", padx=18, pady=16, font=("Segoe UI", 11), state="disabled")
        self.overview.pack(fill="both", expand=True)
        actions = ttk.Frame(overview)
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="Обновить диагностику", style="Accent.TButton", command=self.refresh).pack(side="left")
        ttk.Button(actions, text="Открыть папку рабочего стола", command=self.open_desktop).pack(side="left", padx=8)

        ttk.Label(clean, text="Файлы рабочего стола", style="Title.TLabel").pack(anchor="w")
        ttk.Label(clean, text="Выберите обычные файлы и перенесите их в ~/Inbox. Папки и ссылки не перемещаются.", style="Muted.TLabel").pack(anchor="w", pady=(4, 12))
        self.desktop_tree = ttk.Treeview(clean, columns=("kind", "size", "note"), show="tree headings", selectmode="extended")
        self.desktop_tree.heading("#0", text="Имя")
        for key, label, width in (("kind", "Тип", 100), ("size", "Размер", 120), ("note", "Проверка", 280)):
            self.desktop_tree.heading(key, text=label)
            self.desktop_tree.column(key, width=width, anchor="w")
        self.desktop_tree.column("#0", width=330)
        self.desktop_tree.pack(fill="both", expand=True)
        clean_actions = ttk.Frame(clean)
        clean_actions.pack(fill="x", pady=(12, 0))
        ttk.Button(clean_actions, text="Перенести выбранное в Inbox", style="Accent.TButton", command=self.move_selected).pack(side="left")
        ttk.Button(clean_actions, text="Обновить", command=self.refresh).pack(side="left", padx=8)

        ttk.Label(startup, text="Пользовательская автозагрузка", style="Title.TLabel").pack(anchor="w")
        ttk.Label(startup, text="Записи не удаляются: файлы переносятся в резервную папку, значения HKCU Run сохраняются для восстановления.", style="Muted.TLabel", wraplength=850).pack(anchor="w", pady=(4, 12))
        self.startup_tree = ttk.Treeview(startup, columns=("state", "source"), show="tree headings", selectmode="browse")
        self.startup_tree.heading("#0", text="Элемент")
        self.startup_tree.column("#0", width=360)
        self.startup_tree.heading("state", text="Состояние")
        self.startup_tree.column("state", width=120)
        self.startup_tree.heading("source", text="Источник")
        self.startup_tree.column("source", width=240)
        self.startup_tree.pack(fill="both", expand=True)
        startup_actions = ttk.Frame(startup)
        startup_actions.pack(fill="x", pady=(12, 0))
        ttk.Button(startup_actions, text="Отключить выбранное", style="Accent.TButton", command=lambda: self.change_startup(False)).pack(side="left")
        ttk.Button(startup_actions, text="Восстановить выбранное", command=lambda: self.change_startup(True)).pack(side="left", padx=8)
        ttk.Button(startup_actions, text="Обновить", command=self.refresh).pack(side="left")

        ttk.Label(processes, text="Наблюдение за ресурсами", style="Title.TLabel").pack(anchor="w")
        ttk.Label(processes, text="Локальный диагностический снимок. Duck не завершает процессы и не меняет их приоритеты.", style="Muted.TLabel").pack(anchor="w", pady=(4, 12))
        self.process_tree = ttk.Treeview(processes, columns=("pid", "memory", "cpu"), show="tree headings")
        self.process_tree.heading("#0", text="Процесс")
        self.process_tree.column("#0", width=360)
        for key, label, width in (("pid", "PID", 100), ("memory", "Память", 150), ("cpu", "CPU", 100)):
            self.process_tree.heading(key, text=label)
            self.process_tree.column(key, width=width)
        self.process_tree.pack(fill="both", expand=True)
        ttk.Button(processes, text="Обновить процессы", style="Accent.TButton", command=self.refresh).pack(anchor="w", pady=(12, 0))

        ttk.Label(rules, text="Правила Duck Desktop", style="Title.TLabel").pack(anchor="w")
        statements = (
            "Рабочий стол — временная зона: ориентир не более 10 элементов.",
            "Файлы переносятся в Inbox, а не удаляются.",
            "Автозагрузка ограничена текущим пользователем.",
            "Перед отключением запись сохраняется для обратного восстановления.",
            "Аудит не запускает неизвестные программы и не читает содержимое документов.",
            "Очистка кэша, изменение системных служб и управление ядром не выполняются этим модулем.",
            "Виртуальные рабочие столы и системное управление окнами потребуют native compositor Duck.",
        )
        for statement in statements:
            row = ttk.Frame(rules)
            row.pack(fill="x", pady=(0, 12))
            ttk.Label(row, text="•", foreground=COLORS["accent"]).pack(side="left", padx=(0, 10))
            ttk.Label(row, text=statement, wraplength=820, justify="left").pack(side="left", fill="x", expand=True)
        self.refresh()

    @staticmethod
    def _bytes(value: int | None) -> str:
        if value is None:
            return "нет данных"
        amount = float(value)
        for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
            if amount < 1024 or unit == "ТБ":
                return f"{amount:.1f} {unit}"
            amount /= 1024
        return "нет данных"

    def refresh(self) -> None:
        self.report = self.service.audit()
        desktop, startup, resources = self.report["desktop"], self.report["startup"], self.report["resources"]
        lines = [
            "СВОДКА РАБОЧЕГО ПРОСТРАНСТВА", "",
            f"Элементов на рабочем столе: {desktop['count']} (ориентир: до 10)",
            f"Активных записей автозагрузки: {startup['count']}",
            f"Платформа: {resources['platform']} · {resources['architecture']}",
            f"Занято памяти: {resources['memory_used_percent'] if resources['memory_used_percent'] is not None else 'нет данных'}%",
            f"Доступно памяти: {self._bytes(resources['memory_available_bytes'])}",
            f"Загрузка CPU: {resources['cpu_percent'] if resources['cpu_percent'] is not None else 'нет данных'}%",
            "", "РЕКОМЕНДАЦИИ",
        ]
        lines.extend("• " + item["title"] + " — " + item["detail"] for item in self.report["recommendations"])
        if not self.report["recommendations"]:
            lines.append("• Существенных замечаний по базовым проверкам нет.")
        lines.extend(["", "Диагностика только читает данные. Перемещение и изменение автозагрузки выполняются отдельно после подтверждения.",
                      "Удалено файлов: 0 · Завершено процессов: 0 · Системные настройки не изменялись."])
        self.overview.configure(state="normal")
        self.overview.delete("1.0", "end")
        self.overview.insert("1.0", "\n".join(lines))
        self.overview.configure(state="disabled")

        for tree in (self.desktop_tree, self.startup_tree, self.process_tree):
            for item in tree.get_children():
                tree.delete(item)
        for item in desktop["items"]:
            note = "Проверьте имя" if item["looks_temporary"] else "Можно перенести" if item["safe_to_move"] else "Не перемещается"
            self.desktop_tree.insert("", "end", iid=item["name"], text=item["name"], values=(item["kind"], self._bytes(item["size_bytes"]), note))
        for entry in startup["entries"]:
            label = "Включено" if entry["enabled"] else "Отключено"
            source = "Реестр HKCU Run" if entry["source"] == "user_registry_run" else "Папка автозагрузки"
            self.startup_tree.insert("", "end", iid=entry["id"], text=entry["name"], values=(label, source))
        for process in resources["top_processes"]:
            cpu = "—" if process["cpu_percent"] is None else f"{process['cpu_percent']:.1f}%"
            self.process_tree.insert("", "end", text=process["name"], values=(process["pid"], self._bytes(process["memory_bytes"]), cpu))

    def move_selected(self) -> None:
        names = list(self.desktop_tree.selection())
        if not names:
            messagebox.showinfo("Duck Desktop", "Сначала выберите файлы.", parent=self.root)
            return
        if not messagebox.askyesno("Подтверждение", f"Перенести {len(names)} файлов в Inbox? Они не будут удалены или перезаписаны.", parent=self.root):
            return
        try:
            result = move_desktop_items_to_inbox(names)
        except (OSError, ValueError) as error:
            messagebox.showerror("Duck Desktop", str(error), parent=self.root)
            return
        messagebox.showinfo("Duck Desktop", f"Перемещено: {len(result['moved'])}\nОтклонено: {len(result['rejected'])}", parent=self.root)
        self.refresh()

    def change_startup(self, enabled: bool) -> None:
        selected = self.startup_tree.selection()
        if not selected:
            messagebox.showinfo("Автозагрузка", "Выберите запись.", parent=self.root)
            return
        verb = "восстановить" if enabled else "отключить"
        if not messagebox.askyesno("Автозагрузка", f"Подтвердить действие: {verb} запись текущего пользователя?", parent=self.root):
            return
        try:
            self.service.startup.set_enabled(selected[0], enabled)
        except (OSError, ValueError, RuntimeError, FileExistsError) as error:
            messagebox.showerror("Автозагрузка", str(error), parent=self.root)
            return
        self.refresh()
        messagebox.showinfo("Автозагрузка", "Изменение выполнено. Запись можно восстановить в Duck Desktop.", parent=self.root)

    def open_desktop(self) -> None:
        path = self.report.get("desktop", {}).get("path", "")
        try:
            if sys.platform == "win32":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path], shell=False)
            else:
                subprocess.Popen(["xdg-open", path], shell=False)
        except OSError as error:
            messagebox.showerror("Duck Desktop", str(error), parent=self.root)


def run_native_desktop() -> int:
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise RuntimeError(f"Не удалось открыть GUI: {error}. Проверьте Tk и наличие графического сеанса.") from error
    DesktopWindow(root)
    root.mainloop()
    return 0
