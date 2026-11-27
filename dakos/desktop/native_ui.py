"""Tk-based native user-space maintenance window for Dak Desktop."""
from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Callable

from .service import DesktopService, move_desktop_items_to_inbox
from .reaper import ReaperIntegrationError, ReaperWorkbench

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
        self.reaper = ReaperWorkbench()
        self.reaper_source: Path | None = None
        self._reaper_queue: queue.Queue[tuple[str, dict[str, Any] | None, str | None]] = queue.Queue()
        self._reaper_busy = False
        self._reaper_studio_process: subprocess.Popen[str] | None = None
        root.title("Dak Desktop — обслуживание рабочего пространства")
        root.geometry("1040x700")
        root.minsize(820, 560)
        root.configure(bg=COLORS["background"])
        self._style()
        self._build()
        self.root.after(100, self._poll_reaper_queue)

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
        overview, clean, startup, processes, rules, reaper_tab = [
            ttk.Frame(tabs, padding=18) for _ in range(6)
        ]
        for tab, title in zip(
            (overview, clean, startup, processes, rules, reaper_tab),
            ("Обзор", "Рабочий стол", "Автозагрузка", "Процессы", "Правила", "Reaper"),
        ):
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
        ttk.Label(processes, text="Локальный диагностический снимок. Dak не завершает процессы и не меняет их приоритеты.", style="Muted.TLabel").pack(anchor="w", pady=(4, 12))
        self.process_tree = ttk.Treeview(processes, columns=("pid", "memory", "cpu"), show="tree headings")
        self.process_tree.heading("#0", text="Процесс")
        self.process_tree.column("#0", width=360)
        for key, label, width in (("pid", "PID", 100), ("memory", "Память", 150), ("cpu", "CPU", 100)):
            self.process_tree.heading(key, text=label)
            self.process_tree.column(key, width=width)
        self.process_tree.pack(fill="both", expand=True)
        ttk.Button(processes, text="Обновить процессы", style="Accent.TButton", command=self.refresh).pack(anchor="w", pady=(12, 0))

        ttk.Label(rules, text="Правила Dak Desktop", style="Title.TLabel").pack(anchor="w")
        statements = (
            "Рабочий стол — временная зона: ориентир не более 10 элементов.",
            "Файлы переносятся в Inbox, а не удаляются.",
            "Автозагрузка ограничена текущим пользователем.",
            "Перед отключением запись сохраняется для обратного восстановления.",
            "Аудит не запускает неизвестные программы и не читает содержимое документов.",
            "Очистка кэша, изменение системных служб и управление ядром не выполняются этим модулем.",
            "Виртуальные рабочие столы и системное управление окнами потребуют native compositor Dak.",
        )
        for statement in statements:
            row = ttk.Frame(rules)
            row.pack(fill="x", pady=(0, 12))
            ttk.Label(row, text="•", foreground=COLORS["accent"]).pack(side="left", padx=(0, 10))
            ttk.Label(row, text=statement, wraplength=820, justify="left").pack(side="left", fill="x", expand=True)

        self._build_reaper_tab(reaper_tab)
        self.refresh()

    def _build_reaper_tab(self, tab: ttk.Frame) -> None:
        ttk.Label(tab, text="REAPER WORKBENCH", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            tab,
            text=(
                "Нативная интеграция системного языка Reaper. Dak использует "
                "закреплённый исходный checkout и запускает его CLI отдельным процессом."
            ),
            style="Muted.TLabel",
            wraplength=850,
            justify="left",
        ).pack(anchor="w", pady=(4, 12))

        self.reaper_status = tk.StringVar(value="Проверка исходного checkout…")
        self.reaper_location = tk.StringVar(value="Репозиторий ещё не обнаружен")
        self.reaper_selected = tk.StringVar(value="Исходный файл не выбран")

        status_panel = ttk.Frame(tab, padding=12)
        status_panel.pack(fill="x", pady=(0, 10))
        ttk.Label(status_panel, textvariable=self.reaper_status, style="Title.TLabel").pack(anchor="w")
        ttk.Label(status_panel, textvariable=self.reaper_location, style="Muted.TLabel", wraplength=850).pack(anchor="w", pady=(4, 0))
        ttk.Label(tab, textvariable=self.reaper_selected, style="Muted.TLabel", wraplength=850).pack(anchor="w", pady=(0, 8))

        actions = ttk.Frame(tab)
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="Обновить статус", command=self._refresh_reaper_status).pack(side="left")
        ttk.Button(actions, text="Открыть Reaper Studio", style="Accent.TButton", command=self._open_reaper_studio).pack(side="left", padx=8)
        ttk.Button(actions, text="Выбрать .rpr", command=self._choose_reaper_source).pack(side="left", padx=8)
        ttk.Button(actions, text="Проверить", command=self._check_reaper_source).pack(side="left")
        ttk.Button(actions, text="Проверить типы", command=self._typecheck_reaper_source).pack(side="left", padx=8)

        ttk.Label(
            tab,
            text="Результаты проверки · JSON / диагностика",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 5))
        self.reaper_output = ScrolledText(
            tab,
            height=15,
            wrap="word",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            relief="flat",
            padx=12,
            pady=10,
            font=("Cascadia Code", 9),
            state="disabled",
        )
        self.reaper_output.pack(fill="both", expand=True)
        self._refresh_reaper_status()

    def _append_reaper_output(self, value: str) -> None:
        self.reaper_output.configure(state="normal")
        self.reaper_output.insert("end", value.rstrip() + "\n")
        self.reaper_output.see("end")
        self.reaper_output.configure(state="disabled")

    def _refresh_reaper_status(self) -> None:
        state = self.reaper.inspect()
        if not state["available"]:
            self.reaper_status.set("REAPER · checkout не найден")
            self.reaper_location.set(state["message"])
            self._append_reaper_output(state["message"])
            return

        capabilities = state["capabilities"]
        labels = {
            "reference_runtime": "reference runtime",
            "cli": "CLI",
            "native_studio": "native Studio",
            "static_typecheck": "static type analysis",
            "native_aot_subset": "experimental native AOT",
        }
        available = ", ".join(labels[item] for item in capabilities if item in labels)
        self.reaper_status.set("REAPER · доступен")
        self.reaper_location.set(f"{state['repository']} · {available}")
        self._append_reaper_output("Reaper integration ready")
        self._append_reaper_output(json.dumps(state, ensure_ascii=False, indent=2))

    def _choose_reaper_source(self) -> None:
        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Выбрать исходный файл Reaper",
            filetypes=[
                ("Reaper source", "*.rpr *.most"),
                ("All files", "*.*"),
            ],
        )
        if not filename:
            return
        self.reaper_source = Path(filename)
        self.reaper_selected.set(str(self.reaper_source))

    def _start_reaper_task(
        self,
        label: str,
        operation: Callable[[], dict[str, Any]],
    ) -> None:
        if self._reaper_busy:
            messagebox.showinfo("Reaper", "Предыдущая проверка ещё выполняется.", parent=self.root)
            return
        if self.reaper_source is None:
            self._choose_reaper_source()
            if self.reaper_source is None:
                return

        source = self.reaper_source
        self._reaper_busy = True
        self.reaper_status.set(f"REAPER · {label}…")

        def worker() -> None:
            try:
                result = operation()
                self._reaper_queue.put((label, result, None))
            except (OSError, ValueError, RuntimeError, ReaperIntegrationError) as error:
                self._reaper_queue.put((label, None, str(error)))
            except Exception as error:
                self._reaper_queue.put((label, None, f"{type(error).__name__}: {error}"))

        threading.Thread(
            target=worker,
            name="dakos-reaper-check",
            daemon=True,
        ).start()

    def _check_reaper_source(self) -> None:
        self._start_reaper_task(
            "Проверка",
            lambda: self.reaper.check(self.reaper_source),
        )

    def _typecheck_reaper_source(self) -> None:
        self._start_reaper_task(
            "Анализ типов",
            lambda: self.reaper.typecheck(self.reaper_source),
        )

    def _poll_reaper_queue(self) -> None:
        try:
            while True:
                label, result, error = self._reaper_queue.get_nowait()
                self._reaper_busy = False
                if error:
                    self.reaper_status.set(f"REAPER · {label}: ошибка")
                    self._append_reaper_output(f"{label} failed: {error}")
                    continue
                assert result is not None
                state = "успешно" if result["ok"] else f"ошибка ({result['exit_code']})"
                self.reaper_status.set(f"REAPER · {label}: {state}")
                payload = result.get("result")
                rendered = (
                    json.dumps(payload, ensure_ascii=False, indent=2)
                    if payload is not None
                    else result.get("stdout", "")
                )
                if rendered:
                    self._append_reaper_output(rendered)
                if result.get("stderr"):
                    self._append_reaper_output("STDERR:\n" + result["stderr"])
        except queue.Empty:
            pass
        try:
            if self.root.winfo_exists():
                self.root.after(100, self._poll_reaper_queue)
        except tk.TclError:
            return

    def _open_reaper_studio(self) -> None:
        try:
            state = self.reaper.inspect()
            if not state["available"] or "native_studio" not in state["capabilities"]:
                raise ReaperIntegrationError(
                    "Reaper Studio is unavailable. Initialize the Reaper source checkout first."
                )
            process = self.reaper.open_studio()
        except (OSError, ValueError, RuntimeError, ReaperIntegrationError) as error:
            messagebox.showerror("Reaper Studio", str(error), parent=self.root)
            return
        self._reaper_studio_process = process
        self.reaper_status.set("REAPER · Studio запущена")
        self._append_reaper_output("Reaper Studio started as a separate user-space process.")

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
            messagebox.showinfo("Dak Desktop", "Сначала выберите файлы.", parent=self.root)
            return
        if not messagebox.askyesno("Подтверждение", f"Перенести {len(names)} файлов в Inbox? Они не будут удалены или перезаписаны.", parent=self.root):
            return
        try:
            result = move_desktop_items_to_inbox(names)
        except (OSError, ValueError) as error:
            messagebox.showerror("Dak Desktop", str(error), parent=self.root)
            return
        messagebox.showinfo("Dak Desktop", f"Перемещено: {len(result['moved'])}\nОтклонено: {len(result['rejected'])}", parent=self.root)
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
        messagebox.showinfo("Автозагрузка", "Изменение выполнено. Запись можно восстановить в Dak Desktop.", parent=self.root)

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
            messagebox.showerror("Dak Desktop", str(error), parent=self.root)


def run_native_desktop() -> int:
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise RuntimeError(f"Не удалось открыть GUI: {error}. Проверьте Tk и наличие графического сеанса.") from error
    DesktopWindow(root)
    root.mainloop()
    return 0
