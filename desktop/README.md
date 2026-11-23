# DuckOS Desktop Shell

The browser shell contains a built-in application window for **«Вечерний курьер»**.
The newspaper interface is bundled at newsroom/ and reads only from the local
DuckOS Newsroom API; it never calls publisher domains directly from the browser.

## Start the desktop

From the repository root:

    python -m http.server 4173 --directory desktop

Open http://127.0.0.1:4173. Select «Новости» in the sidebar or dock, or press
Ctrl+K and search for «Вечерний курьер».

## Start live news

In a second terminal, from the repository root:

    PYTHONPATH=native/services python -m duckos_services news serve

The service listens on 127.0.0.1:8765, fetches free public RSS/Atom sources on
startup and refreshes every five minutes. It keeps the last successful cache
under ~/.local/state/duckos/news-cache.json. It is safe to start the UI without
the service; the newsroom explains how to connect instead of showing invented
headlines.

## Shell actions

- Ctrl+K — app and command search.
- Sidebar, dock, and search all launch «Вечерний курьер».
- Theme and Reduce Motion remain shell settings.
- News search, category tabs, unread filter, saved articles, manual refresh,
  and original-publisher links are available inside the app.

The CPU/GPU/RAM/SSD cards on the home screen remain demonstration values. The
Newsroom is separate: its source status and publication times come from real
RSS/Atom responses and are not represented as host telemetry.
