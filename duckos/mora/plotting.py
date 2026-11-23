"""Optional PyQtGraph CSV viewer for native Qt desktop workflows."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any


def read_numeric_columns(path: str | Path, *, max_rows: int = 100_000) -> tuple[list[str], dict[str, list[float]]]:
    target = Path(path).expanduser()
    if target.is_symlink():
        raise ValueError("Symbolic links are not accepted for CSV plotting.")
    try:
        size = target.stat().st_size
    except OSError as error:
        raise ValueError(f"Cannot read CSV file: {error}") from error
    if not target.is_file() or size > 32 * 1024 * 1024:
        raise ValueError("Select a regular CSV file smaller than 32 MiB.")

    columns: dict[str, list[float]] = {}
    try:
        with target.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if not reader.fieldnames:
                raise ValueError("CSV file has no header row.")
            fields = [str(field) for field in reader.fieldnames if field]
            for field in fields:
                columns[field] = []
            for row_number, row in enumerate(reader, start=1):
                if row_number > max_rows:
                    raise ValueError(f"CSV exceeds the {max_rows:,}-row limit.")
                for field in fields:
                    raw = (row.get(field) or "").strip()
                    try:
                        number = float(raw)
                    except ValueError:
                        continue
                    if number == number and abs(number) != float("inf"):
                        columns[field].append(number)
    except (OSError, UnicodeError, csv.Error) as error:
        raise ValueError(f"Cannot parse CSV file: {error}") from error

    numeric = {name: values for name, values in columns.items() if len(values) >= 2}
    if len(numeric) < 1:
        raise ValueError("No numeric column contains at least two values.")
    return list(numeric), numeric


def main() -> int:
    try:
        import pyqtgraph as pg
        from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox, QComboBox, QWidget, QVBoxLayout
    except ImportError as error:
        raise SystemExit(
            "The CSV plot viewer requires the plots extra. "
            "Install with: python -m pip install 'duckos-build-tools[plots]'. "
            f"Import details: {error}"
        ) from error

    app = QApplication.instance() or QApplication(sys.argv)
    path, _ = QFileDialog.getOpenFileName(
        None, "Open numeric CSV", "", "CSV files (*.csv);;All files (*.*)"
    )
    if not path:
        return 0
    try:
        names, columns = read_numeric_columns(path)
    except ValueError as error:
        QMessageBox.critical(None, "Mora Plot", str(error))
        return 2

    window = QMainWindow()
    window.setWindowTitle(f"Mora Plot — {Path(path).name}")
    window.resize(1100, 720)
    root = QWidget()
    layout = QVBoxLayout(root)
    y_selector = QComboBox()
    y_selector.addItems(names)
    plot = pg.PlotWidget()
    plot.showGrid(x=True, y=True, alpha=0.25)
    layout.addWidget(y_selector)
    layout.addWidget(plot, 1)
    window.setCentralWidget(root)

    def render() -> None:
        name = y_selector.currentText()
        plot.clear()
        plot.plot(list(range(len(columns[name]))), columns[name], pen=pg.mkPen("#ffd400", width=2))
        plot.setLabel("bottom", "Row")
        plot.setLabel("left", name)

    y_selector.currentIndexChanged.connect(render)
    render()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
