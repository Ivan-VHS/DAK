"""Native Duck Desktop panel for the Beelzebub AV user-space scanner."""
from __future__ import annotations
import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Callable
from ..security import BeelzebubError, BeelzebubWorkbench


def build_scan_options(*, hashdb: str = "", signature: str = "", public_key: str = "",
                       clam_port: str = "3310", yara_bin: str = "", yara_rules: str = "") -> dict[str, Any]:
    feed = tuple(v.strip() for v in (hashdb, signature, public_key))
    if any(feed) and not all(feed):
        raise ValueError("Для подписанной базы нужны все три файла: база, подпись и публичный ключ.")
    yara = tuple(v.strip() for v in (yara_bin, yara_rules))
    if any(yara) and not all(yara):
        raise ValueError("Для YARA-X укажите одновременно исполняемый файл и файл правил.")
    port_text = clam_port.strip()
    port = None
    if port_text:
        if not port_text.isdecimal() or not 1 <= int(port_text) <= 65535:
            raise ValueError("Порт ClamAV должен быть целым числом от 1 до 65535.")
        port = int(port_text)
    return {
        "hashdb": Path(feed[0]) if all(feed) else None,
        "signature": Path(feed[1]) if all(feed) else None,
        "public_key": Path(feed[2]) if all(feed) else None,
        "clam_port": port,
        "yara_bin": Path(yara[0]) if all(yara) else None,
        "yara_rules": Path(yara[1]) if all(yara) else None,
    }


class BeelzebubPanel:
    """Tk view; all scanner work is dispatched off the UI thread."""
    def __init__(self, parent: ttk.Frame, *, root: tk.Misc,
                 workbench: BeelzebubWorkbench | None = None) -> None:
        self.parent, self.root = parent, root
        self.workbench = workbench or BeelzebubWorkbench()
        self._queue: queue.Queue[tuple[str, Any | None, str | None]] = queue.Queue()
        self._busy = False
        self.target = tk.StringVar(root)
        self.status = tk.StringVar(root, "Проверка доступности BAV…")
        self.hashdb = tk.StringVar(root)
        self.signature = tk.StringVar(root)
        self.public_key = tk.StringVar(root)
        self.clam_port = tk.StringVar(root, "3310")
        self.yara_bin = tk.StringVar(root)
        self.yara_rules = tk.StringVar(root)

    def build(self) -> None:
        ttk.Label(self.parent, text="BEELZEBUB AV · BAV", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self.parent, text=(
            "Проверка выбранных файлов отдельным Java 21-процессом. BAV не запускает "
            "проверяемый файл, не удаляет оригинал и пока не перехватывает открытие "
            "файлов или запуск процессов на уровне ядра."
        ), style="Muted.TLabel", wraplength=900, justify="left").pack(anchor="w", pady=(4, 12))
        status = ttk.Frame(self.parent, padding=12)
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, textvariable=self.status, style="Title.TLabel").pack(anchor="w")
        ttk.Label(status, text="Статус отражает наличие JAR и Java, а не состояние постоянной защиты.",
                  style="Muted.TLabel").pack(anchor="w", pady=(3, 0))
        target = ttk.LabelFrame(self.parent, text="Объект проверки", padding=10)
        target.pack(fill="x", pady=(0, 10))
        ttk.Entry(target, textvariable=self.target).pack(side="left", fill="x", expand=True)
        ttk.Button(target, text="Выбрать файл…", command=self.choose_target).pack(side="left", padx=(8, 0))
        config = ttk.LabelFrame(self.parent, text="Доверенные источники и движки", padding=10)
        config.pack(fill="x", pady=(0, 10))
        self._path_row(config, 0, "SHA-256 база", self.hashdb)
        self._path_row(config, 1, "Подпись базы", self.signature)
        self._path_row(config, 2, "Публичный ключ", self.public_key)
        ttk.Label(config, text="ClamAV TCP loopback port").grid(row=3, column=0, sticky="w", pady=3)
        ttk.Entry(config, textvariable=self.clam_port, width=12).grid(row=3, column=1, sticky="w", pady=3)
        self._path_row(config, 4, "YARA-X executable (optional)", self.yara_bin)
        self._path_row(config, 5, "YARA-X rules (optional)", self.yara_rules)
        config.columnconfigure(1, weight=1)
        ttk.Label(self.parent, text=(
            "Для CLEAN нужны действующая подписанная база и все обязательные движки. "
            "Нет базы, ошибка движка, тайм-аут или повреждённый отчёт дают INDETERMINATE, "
            "а не CLEAN. ClamAV должен быть настроен локально; YARA-X — дополнительный движок."
        ), style="Muted.TLabel", wraplength=900, justify="left").pack(anchor="w", pady=(0, 10))
        actions = ttk.Frame(self.parent)
        actions.pack(fill="x", pady=(0, 8))
        ttk.Button(actions, text="Обновить статус", command=self.refresh_status).pack(side="left")
        ttk.Button(actions, text="Сканировать выбранный объект", style="Accent.TButton",
                   command=self.scan).pack(side="left", padx=8)
        ttk.Label(self.parent, text="Отчёт проверки · JSON", style="Muted.TLabel").pack(anchor="w", pady=(3, 5))
        self.output = ScrolledText(self.parent, height=12, wrap="word", bg="#1B1B1B", fg="#F7F7F7",
                                   insertbackground="#FFD400", relief="flat", padx=12, pady=10,
                                   font=("Cascadia Code", 9), state="disabled")
        self.output.pack(fill="both", expand=True)
        self.refresh_status()
        self.root.after(100, self._poll)

    def _path_row(self, parent: ttk.LabelFrame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Button(parent, text="Обзор…", command=lambda: self._browse(variable, label)).grid(
            row=row, column=2, padx=(8, 0), pady=3)

    def _browse(self, variable: tk.StringVar, label: str) -> None:
        chosen = filedialog.askopenfilename(parent=self.root, title=f"Выбрать: {label}")
        if chosen:
            variable.set(chosen)

    def choose_target(self) -> None:
        chosen = filedialog.askopenfilename(parent=self.root, title="Выбрать файл для проверки")
        if chosen:
            self.target.set(chosen)

    def refresh_status(self) -> None:
        self._start_task("status", self.workbench.inspect)

    def scan(self) -> None:
        target = self.target.get().strip()
        if not target:
            messagebox.showinfo("Beelzebub AV", "Сначала выберите файл для проверки.", parent=self.root)
            return
        try:
            options = build_scan_options(hashdb=self.hashdb.get(), signature=self.signature.get(),
                public_key=self.public_key.get(), clam_port=self.clam_port.get(),
                yara_bin=self.yara_bin.get(), yara_rules=self.yara_rules.get())
        except ValueError as error:
            messagebox.showerror("Параметры BAV", str(error), parent=self.root)
            return
        self._start_task("scan", lambda: self.workbench.scan(Path(target), **options))

    def _start_task(self, label: str, operation: Callable[[], Any]) -> None:
        if self._busy:
            self.status.set("BAV · предыдущая операция ещё выполняется")
            return
        self._busy = True
        self.status.set("BAV · выполняется сканирование…" if label == "scan" else "BAV · проверка компонентов…")
        def worker() -> None:
            try:
                self._queue.put((label, operation(), None))
            except (OSError, ValueError, RuntimeError, BeelzebubError) as error:
                self._queue.put((label, None, str(error)))
            except Exception as error:
                self._queue.put((label, None, f"{type(error).__name__}: {error}"))
        threading.Thread(target=worker, name=f"duckos-bav-{label}", daemon=True).start()

    def _append(self, value: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", value.rstrip() + "\\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _poll(self) -> None:
        try:
            while True:
                label, payload, error = self._queue.get_nowait()
                self._busy = False
                if error:
                    self.status.set(f"BAV · {label}: ошибка")
                    self._append(f"{label}: {error}")
                    continue
                if label == "status":
                    available = bool(payload.get("available"))
                    self.status.set("BAV · JAR и Java доступны (user-space)" if available
                                    else "BAV · сканер пока недоступен")
                    self._append(json.dumps(payload, ensure_ascii=False, indent=2))
                    continue
                code, report = payload
                summary = report.get("summary", {})
                verdict = "MALICIOUS" if code == 2 else "INDETERMINATE" if code == 3 else "CLEAN" if code == 0 else "ERROR"
                self.status.set(f"BAV · {verdict} · файлов: {summary.get('files', 0)}")
                self._append(json.dumps(report, ensure_ascii=False, indent=2))
        except queue.Empty:
            pass
        try:
            if self.root.winfo_exists():
                self.root.after(120, self._poll)
        except Exception:
            return
