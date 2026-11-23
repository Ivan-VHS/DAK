"""Native Tk workbench for DuckOS Foundry."""
from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any

from .foundry import build_runbook, collect_foundry_snapshot, write_snapshot

COLORS = {
    "background": "#101010",
    "surface": "#1B1B1B",
    "raised": "#252525",
    "text": "#F7F7F7",
    "muted": "#BDBDBD",
    "accent": "#FFD400",
    "accent_text": "#111111",
    "border": "#454545",
}

_PROFILES = {
    "Пусковой контроль": "routine",
    "Профилактическое обслуживание": "preventive",
    "Разбор инцидента": "incident",
    "Ввод в эксплуатацию": "commissioning",
}


class FoundryWindow:
    """Operator console; all measurements are local and read-only."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.snapshot: dict[str, Any] | None = None
        self._busy = False
        self._results: queue.Queue[tuple[dict[str, Any] | None, str | None]] = queue.Queue()
        root.title("Duck Foundry — промышленная консоль DuckOS")
        root.geometry("1080x720")
        root.minsize(860, 580)
        root.configure(bg=COLORS["background"])
        self._style()
        self._build()
        self.root.after(120, self._poll_results)
        self.refresh()

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
        style.configure("Metric.TLabel", foreground=COLORS["accent"], font=("Segoe UI Semibold", 18))
        style.configure("TButton", padding=(12, 8), background=COLORS["raised"], foreground=COLORS["text"])
        style.map("TButton", background=[("active", COLORS["accent"])], foreground=[("active", COLORS["accent_text"])])
        style.configure("Accent.TButton", padding=(14, 9), background=COLORS["accent"], foreground=COLORS["accent_text"])
        style.configure("TNotebook", background=COLORS["background"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(15, 9), background=COLORS["raised"], foreground=COLORS["text"])
        style.map("TNotebook.Tab", background=[("selected", COLORS["accent"])], foreground=[("selected", COLORS["accent_text"])])
        style.configure("Treeview", background=COLORS["surface"], fieldbackground=COLORS["surface"], foreground=COLORS["text"], rowheight=29)
        style.configure("Treeview.Heading", background=COLORS["raised"], foreground=COLORS["accent"])

    def _build(self) -> None:
        header = ttk.Frame(self.root, padding=(22, 18, 22, 12))
        header.pack(fill="x")
        ttk.Label(header, text="DUCK FOUNDRY", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Индустриальная консоль диагностики · ресурсы · устройства · регламенты",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        actions = ttk.Frame(header)
        actions.pack(anchor="e", pady=(10, 0))
        self.refresh_button = ttk.Button(actions, text="Снять новый слепок", style="Accent.TButton", command=self.refresh)
        self.refresh_button.pack(side="left")
        self.export_button = ttk.Button(actions, text="Экспорт отчёта", command=self.export_report, state="disabled")
        self.export_button.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Подготовка диагностического контура…")
        self.state_var = tk.StringVar(value="НЕ ПРОВЕРЕНО")
        status_row = ttk.Frame(self.root, padding=(22, 0, 22, 12))
        status_row.pack(fill="x")
        ttk.Label(status_row, textvariable=self.state_var, style="Metric.TLabel").pack(side="left")
        ttk.Label(status_row, textvariable=self.status_var, style="Muted.TLabel").pack(side="left", padx=(14, 0))

        tabs = ttk.Notebook(self.root)
        tabs.pack(fill="both", expand=True, padx=20, pady=(2, 20))
        overview, signals, runbooks, policy = [ttk.Frame(tabs, padding=16) for _ in range(4)]
        for tab, title in zip((overview, signals, runbooks, policy), ("Сводка", "Сигналы", "Регламенты", "Границы")):
            tabs.add(tab, text=title)

        metric_area = ttk.Frame(overview)
        metric_area.pack(fill="x", pady=(0, 16))
        self.metric_vars: dict[str, tk.StringVar] = {}
        for key, label in (
            ("cpu_percent", "CPU"),
            ("memory_used_percent", "ПАМЯТЬ"),
            ("devices_total", "УСТРОЙСТВА"),
            ("devices_with_problems", "ОШИБКИ УСТРОЙСТВ"),
        ):
            card = ttk.Frame(metric_area, padding=12)
            card.pack(side="left", fill="x", expand=True, padx=(0, 8))
            ttk.Label(card, text=label, style="Muted.TLabel").pack(anchor="w")
            variable = tk.StringVar(value="—")
            self.metric_vars[key] = variable
            ttk.Label(card, textvariable=variable, style="Metric.TLabel").pack(anchor="w", pady=(5, 0))

        ttk.Label(overview, text="Открытые замечания", style="Title.TLabel").pack(anchor="w", pady=(4, 8))
        self.finding_tree = ttk.Treeview(overview, columns=("severity", "detail"), show="tree headings", height=9)
        self.finding_tree.heading("#0", text="Сигнал")
        self.finding_tree.heading("severity", text="Уровень")
        self.finding_tree.heading("detail", text="Описание")
        self.finding_tree.column("#0", width=230)
        self.finding_tree.column("severity", width=110, anchor="center")
        self.finding_tree.column("detail", width=520)
        self.finding_tree.pack(fill="both", expand=True)
        ttk.Label(
            overview,
            text="Слепок собирается локально. Значения, которые не поддерживает платформа, показываются как недоступные.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(10, 0))

        self.module_tree = ttk.Treeview(signals, columns=("state", "source"), show="tree headings")
        self.module_tree.heading("#0", text="Контур")
        self.module_tree.heading("state", text="Состояние")
        self.module_tree.heading("source", text="Источник")
        self.module_tree.column("#0", width=250)
        self.module_tree.column("state", width=140)
        self.module_tree.column("source", width=470)
        self.module_tree.pack(fill="both", expand=True)

        runbook_top = ttk.Frame(runbooks)
        runbook_top.pack(fill="x")
        self.profile_var = tk.StringVar(value="Профилактическое обслуживание")
        ttk.Label(runbook_top, text="Регламент").pack(side="left")
        self.profile_box = ttk.Combobox(
            runbook_top, textvariable=self.profile_var,
            values=tuple(_PROFILES), state="readonly", width=35,
        )
        self.profile_box.pack(side="left", padx=10)
        ttk.Button(runbook_top, text="Сформировать маршрут", style="Accent.TButton", command=self.render_runbook).pack(side="left")
        self.runbook_text = ScrolledText(
            runbooks, wrap="word", bg=COLORS["surface"], fg=COLORS["text"],
            insertbackground=COLORS["accent"], relief="flat", padx=14, pady=12,
            font=("Segoe UI", 10),
        )
        self.runbook_text.pack(fill="both", expand=True, pady=(14, 0))

        policy_text = (
            "Foundry — диагностический и регламентный контур пользовательского уровня.\n\n"
            "• Только чтение локальных метрик, списка процессов, рабочего пространства и устройств.\n"
            "• Сведения об устройствах используют одноразовые хеши идентификаторов, а не исходные Instance ID.\n"
            "• Обнаружение Wine / Proton / CrossOver / Bottles / QEMU не запускает найденные программы.\n"
            "• Регламенты создают проверяемые оператором шаги; они не являются сценариями автоматического исполнения.\n"
            "• Не останавливает процессы, не меняет приоритеты, драйверы, службы, питание, реестр, ядро или загрузчик.\n"
            "• Не управляет внешними станками, промышленными контроллерами или физическими исполнительными механизмами.\n"
            "• Сборщик не обращается к сети и не загружает отчёты автоматически.\n"
        )
        self.policy_text = ScrolledText(
            policy, wrap="word", bg=COLORS["surface"], fg=COLORS["text"],
            insertbackground=COLORS["accent"], relief="flat", padx=14, pady=12,
            font=("Segoe UI", 10), height=18,
        )
        self.policy_text.pack(fill="both", expand=True)
        self.policy_text.insert("1.0", policy_text)
        self.policy_text.configure(state="disabled")
        self.render_runbook()

    def refresh(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.refresh_button.configure(state="disabled")
        self.status_var.set("Сбор локальных сигналов…")
        worker = threading.Thread(target=self._collect, name="duck-foundry-audit", daemon=True)
        worker.start()

    def _collect(self) -> None:
        try:
            self._results.put((collect_foundry_snapshot(), None))
        except Exception as error:
            self._results.put((None, str(error)))

    def _poll_results(self) -> None:
        try:
            snapshot, error = self._results.get_nowait()
        except queue.Empty:
            self.root.after(120, self._poll_results)
            return

        self._busy = False
        self.refresh_button.configure(state="normal")
        if error:
            self.status_var.set("Не удалось завершить сбор: " + error)
            self._poll_results_again()
            return
        self.snapshot = snapshot
        self.export_button.configure(state="normal")
        self._render_snapshot()
        self._poll_results_again()

    def _poll_results_again(self) -> None:
        self.root.after(120, self._poll_results)

    def _render_snapshot(self) -> None:
        assert self.snapshot is not None
        metrics = self.snapshot["metrics"]
        state_labels = {
            "nominal": "НОРМА",
            "attention": "ВНИМАНИЕ",
            "critical": "КРИТИЧЕСКИЙ СИГНАЛ",
            "unavailable": "НЕТ ДАННЫХ",
        }
        self.state_var.set(state_labels.get(self.snapshot["state"], "НЕИЗВЕСТНО"))
        self.status_var.set("Слепок: " + self.snapshot["captured_at"] + " · локальный режим чтения")

        for key, variable in self.metric_vars.items():
            value = metrics.get(key)
            if isinstance(value, (int, float)):
                variable.set(f"{value:.1f}%" if key in {"cpu_percent", "memory_used_percent"} else str(value))
            else:
                variable.set("—")

        for item in self.finding_tree.get_children():
            self.finding_tree.delete(item)
        for finding in self.snapshot["findings"]:
            self.finding_tree.insert(
                "", "end", text=finding["title"],
                values=(finding["severity"].upper(), finding["detail"]),
            )

        for item in self.module_tree.get_children():
            self.module_tree.delete(item)
        for module in self.snapshot["modules"]:
            self.module_tree.insert(
                "", "end", text=module["name"],
                values=(module["state"], module["source"]),
            )
        self.render_runbook()

    def render_runbook(self) -> None:
        profile = _PROFILES[self.profile_var.get()]
        runbook = build_runbook(profile, self.snapshot)
        lines = [
            runbook["title"],
            runbook["description"],
            "",
            "ШАГИ ОПЕРАТОРА",
        ]
        for item in runbook["steps"]:
            lines.append(f'{item["number"]:02d}. {item["title"]}')
        lines.extend([
            "",
            "Политика: только ручная проверка. Никакие шаги не запускаются автоматически.",
            "Открытые замечания: " + (", ".join(runbook["open_findings"]) or "нет"),
        ])
        self.runbook_text.configure(state="normal")
        self.runbook_text.delete("1.0", "end")
        self.runbook_text.insert("1.0", "\n".join(lines))
        self.runbook_text.configure(state="disabled")

    def export_report(self) -> None:
        if self.snapshot is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Экспорт слепка Duck Foundry",
            defaultextension=".json",
            filetypes=(("JSON", "*.json"),),
            initialfile="duckos-foundry-report.json",
        )
        if not path:
            return
        try:
            result = write_snapshot(path, self.snapshot)
        except (OSError, TypeError, ValueError) as error:
            messagebox.showerror("Экспорт отчёта", str(error), parent=self.root)
            return
        messagebox.showinfo("Экспорт отчёта", "Отчёт сохранён: " + result["written"], parent=self.root)


def run_foundry() -> int:
    root = tk.Tk()
    FoundryWindow(root)
    root.mainloop()
    return 0
