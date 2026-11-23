"""Optional terminal dashboard for Mora, powered by Textual.

This is a terminal UI only. It does not start a browser or web server.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import filter_commons_apps


def _load_catalog() -> list[dict[str, Any]]:
    path = Path(__file__).with_name("data") / "apps.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return []
    apps = value.get("built_in_apps", []) if isinstance(value, dict) else []
    return apps if isinstance(apps, list) else []


def main() -> int:
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal, Vertical
        from textual.widgets import DataTable, Footer, Header, Input, Static
    except ImportError as error:
        raise SystemExit(
            "The Mora terminal interface requires the terminal-ui extra. "
            "Install with: python -m pip install 'duckos-build-tools[terminal-ui]'. "
            f"Import details: {error}"
        ) from error

    class MoraTerminalApp(App[None]):
        TITLE = "Mora · DuckOS"
        SUB_TITLE = "Native terminal workspace"
        CSS = """
        Screen { background: #080808; color: #ffffff; }
        #intro { height: auto; padding: 1 2; background: #151515; border: round #3a3a3a; }
        #search { margin: 1 0; }
        #catalog { height: 1fr; border: round #3a3a3a; }
        #details { height: 10; margin-top: 1; padding: 1 2; background: #151515; border: round #3a3a3a; }
        """
        BINDINGS = [
            ("ctrl+k", "focus_search", "Search"),
            ("escape", "clear_search", "Clear"),
            ("q", "quit", "Quit"),
        ]

        def __init__(self) -> None:
            super().__init__()
            self.apps = _load_catalog()
            self.matches: list[dict[str, Any]] = []

        def compose(self) -> ComposeResult:
            yield Header()
            with Vertical():
                yield Static(
                    "[bold #ffd400]MORA · DUCKOS[/]\n"
                    "Terminal companion for native desktop administration. "
                    "No browser renderer and no remote service.",
                    id="intro",
                )
                yield Input(placeholder="Search applications…", id="search")
                yield DataTable(id="catalog")
                yield Static("Select an application to inspect its catalogue status.", id="details")
            yield Footer()

        def on_mount(self) -> None:
            table = self.query_one("#catalog", DataTable)
            table.add_columns("Application", "Category", "Runtime", "Scope")
            self.refresh_catalog("")

        def on_input_changed(self, event: Input.Changed) -> None:
            if event.input.id == "search":
                self.refresh_catalog(event.value)

        def refresh_catalog(self, query: str) -> None:
            table = self.query_one("#catalog", DataTable)
            table.clear()
            self.matches = [
                item for item in self.apps
                if query.casefold() in " ".join(
                    str(item.get(key, "")) for key in ("id", "name", "category")
                ).casefold()
            ]
            for item in self.matches:
                table.add_row(
                    str(item.get("name", item.get("id", ""))),
                    str(item.get("category", "other")),
                    str(item.get("runtime", "catalog")),
                    str(item.get("scope", "user-space")),
                    key=str(item.get("id", "")),
                )

        def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
            selected_id = str(event.row_key.value)
            item = next((row for row in self.matches if row.get("id") == selected_id), None)
            if item is None:
                return
            self.query_one("#details", Static).update(
                f"[bold #ffd400]{item.get('name', selected_id)}[/]\n"
                f"ID: {selected_id} · category: {item.get('category', 'other')}\n"
                f"runtime: {item.get('runtime', 'catalog')} · scope: {item.get('scope', 'user-space')}\n"
                "A catalogue entry does not imply that a domain service is installed."
            )

        def action_focus_search(self) -> None:
            self.query_one("#search", Input).focus()

        def action_clear_search(self) -> None:
            search = self.query_one("#search", Input)
            search.value = ""
            self.refresh_catalog("")

    MoraTerminalApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
