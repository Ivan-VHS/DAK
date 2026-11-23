"""DuckOS Newsroom: cached, source-attributed RSS/Atom news aggregation.

Only the built-in, reviewed HTTPS feeds can be fetched. The API binds to loopback;
it does not expose arbitrary URL fetching or command execution.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from .common import ServiceError, atomic_write_json, read_json, utc_now


REFRESH_SECONDS = 300
MAX_FEED_BYTES = 2 * 1024 * 1024
MAX_ITEMS = 120
REQUEST_TIMEOUT = 8
USER_AGENT = "DuckOS-Newsroom/0.1 (+https://github.com/Ivan-VHS/DuckOS)"


@dataclass(frozen=True)
class NewsSource:
    identifier: str
    name: str
    url: str
    language: str
    domains: tuple[str, ...]


DEFAULT_SOURCES = (
    NewsSource(
        "bbc-ukraine",
        "BBC News Україна",
        "https://feeds.bbci.co.uk/ukrainian/rss.xml",
        "uk",
        ("bbci.co.uk", "bbc.com", "bbc.co.uk"),
    ),
    NewsSource(
        "kyiv-independent",
        "The Kyiv Independent",
        "https://kyivindependent.com/news-archive/rss/",
        "en",
        ("kyivindependent.com",),
    ),
    NewsSource(
        "bbc-world",
        "BBC News · Мир",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "en",
        ("bbci.co.uk", "bbc.com", "bbc.co.uk"),
    ),
)

CATEGORY_LABELS = (
    "Все",
    "Украина",
    "Мир",
    "Политика",
    "Экономика",
    "Технологии",
    "Наука",
    "Спорт",
    "Культура",
    "Другое",
)

_CATEGORY_TERMS = (
    ("Спорт", ("спорт", "football", "soccer", "match", "матч", "олімп", "олимп", "теніс", "теннис", "баскет", "marathon", "марафон")),
    ("Наука", ("наук", "science", "research", "дослідж", "исслед", "space", "космос", "косміч", "космич", "лаборатор", "scientist")),
    ("Технологии", ("технолог", "technology", "tech", "цифров", "digital", "ai ", "штучн", "искусствен", "artificial intelligence", "кібер", "кибер", "смартфон", "software")),
    ("Культура", ("культур", "culture", "театр", "кіно", "кино", "film", "музик", "music", "книг", "book", "мистец", "искусств", "вистав", "выстав")),
    ("Экономика", ("економ", "эконом", "econom", "ринок", "рынок", "market", "бізнес", "бизнес", "business", "інфляц", "инфляц", "ціни", "цены", "finance", "фінанс", "финанс")),
    ("Политика", ("політик", "политик", "politic", "парламент", "уряд", "правительств", "government", "президент", "вибор", "выбор", "election", "санкц", "sanction", "дипломат")),
    ("Украина", ("україн", "украин", "ukraine", "київ", "киев", "kyiv", "kharkiv", "харків", "харьков", "одес", "odesa", "львів", "львов", "дніпро", "днепр", "зсу", "armed forces of ukraine", "обстріл", "обстрел", "безпілот", "беспилот", "дрон", "drone")),
)


def _tag_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].split(":")[-1].casefold()


class _TextExtractor(HTMLParser):
    """Convert feed HTML to plain text without executing or retaining markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() in {"script", "style", "noscript"}:
            self._skip += 1
        elif tag.casefold() in {"p", "br", "div", "li"} and not self._skip:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1
        elif tag.casefold() in {"p", "div", "li"} and not self._skip:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)


def _plain_text(value: str, limit: int = 1400) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(value)
        parser.close()
    except Exception:
        parser.parts = [re.sub(r"<[^>]*>", " ", value)]
    cleaned = re.sub(r"\s+", " ", html.unescape(" ".join(parser.parts))).strip()
    return cleaned[:limit]


def _safe_link(value: str, source: NewsSource) -> str:
    candidate = value.strip()
    parsed = urllib.parse.urlsplit(candidate)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        return ""
    host = parsed.hostname.casefold().rstrip(".")
    if not any(host == domain or host.endswith("." + domain) for domain in source.domains):
        return ""
    if parsed.username or parsed.password:
        return ""
    return urllib.parse.urlunsplit(("https", parsed.netloc, parsed.path, parsed.query, ""))


def _parse_date(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _element_text(element: ET.Element, names: set[str]) -> str:
    for child in list(element):
        if _tag_name(child.tag) in names:
            if child.attrib.get("href"):
                return child.attrib["href"].strip()
            return "".join(child.itertext()).strip()
    return ""


def _entry_fields(entry: ET.Element, atom: bool) -> dict[str, str]:
    title = _element_text(entry, {"title"})
    link = ""
    if atom:
        links = [child for child in list(entry) if _tag_name(child.tag) == "link"]
        preferred = next((item for item in links if item.attrib.get("rel", "alternate") == "alternate"), None)
        link = (preferred or (links[0] if links else ET.Element("link"))).attrib.get("href", "")
    else:
        link = _element_text(entry, {"link"})
    description = _element_text(entry, {"summary", "description", "encoded", "content"})
    author = _element_text(entry, {"creator", "author"})
    published = _element_text(entry, {"pubdate", "published", "updated", "date"})
    identifier = _element_text(entry, {"guid", "id"})
    return {
        "title": title,
        "link": link,
        "summary": description,
        "author": author,
        "published": published,
        "identifier": identifier,
    }


def parse_feed(source: NewsSource, payload: bytes) -> list[dict[str, Any]]:
    """Parse RSS 2.0, RDF/RSS 1.0 or Atom XML into safe, plain-text articles."""
    if len(payload) > MAX_FEED_BYTES:
        raise ServiceError(f"{source.name}: feed exceeds the 2 MiB limit")
    if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
        raise ServiceError(f"{source.name}: DTD and entity declarations are not allowed")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as error:
        raise ServiceError(f"{source.name}: invalid feed XML ({error})") from error

    atom = _tag_name(root.tag) == "feed"
    entries = [node for node in root.iter() if _tag_name(node.tag) in {"item", "entry"}]
    articles: list[dict[str, Any]] = []

    for entry in entries:
        fields = _entry_fields(entry, atom)
        title = _plain_text(fields["title"], 240)
        link = _safe_link(fields["link"], source)
        if not title or not link:
            continue

        summary = _plain_text(fields["summary"], 1400)
        published = _parse_date(fields["published"])
        identity = fields["identifier"].strip() or link or title
        article_id = hashlib.sha256(
            f"{source.identifier}\0{identity}".encode("utf-8", "replace")
        ).hexdigest()[:24]
        category = classify_category(f"{title} {summary}")
        articles.append({
            "id": article_id,
            "title": title,
            "summary": summary,
            "url": link,
            "source_id": source.identifier,
            "source": source.name,
            "category": category,
            "language": source.language,
            "author": _plain_text(fields["author"], 120),
            "published_at": published,
        })
    return articles


def classify_category(text: str) -> str:
    normalized = " " + re.sub(r"\s+", " ", text.casefold()) + " "
    for category, terms in _CATEGORY_TERMS:
        if any(term in normalized for term in terms):
            return category
    return "Мир"


class _AllowedRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request: Any, response: Any, code: int, message: str,
                         headers: Any, new_url: str) -> Any:
        parsed = urllib.parse.urlsplit(new_url)
        host = (parsed.hostname or "").casefold().rstrip(".")
        allowed = any(
            host == domain or host.endswith("." + domain)
            for source in DEFAULT_SOURCES for domain in source.domains
        )
        if parsed.scheme.lower() != "https" or not allowed:
            raise urllib.error.HTTPError(new_url, code, "redirect host is not allowed", headers, None)
        return super().redirect_request(request, response, code, message, headers, new_url)


def fetch_feed(source: NewsSource) -> bytes:
    """Fetch one preconfigured HTTPS feed with bounded time and response size."""
    parsed = urllib.parse.urlsplit(source.url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ServiceError(f"{source.name}: only HTTPS feed URLs are allowed")
    if not any(
        parsed.hostname.casefold() == domain or parsed.hostname.casefold().endswith("." + domain)
        for domain in source.domains
    ):
        raise ServiceError(f"{source.name}: feed host is not on its allow-list")

    request = urllib.request.Request(
        source.url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.5",
        },
    )
    opener = urllib.request.build_opener(_AllowedRedirects())
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT) as response:
            content_type = response.headers.get("Content-Type", "").casefold()
            if "text/html" in content_type:
                raise ServiceError(f"{source.name}: server returned HTML instead of a feed")
            payload = response.read(MAX_FEED_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ServiceError(f"{source.name}: {error}") from error
    if len(payload) > MAX_FEED_BYTES:
        raise ServiceError(f"{source.name}: feed exceeds the 2 MiB limit")
    return payload


class NewsService:
    """Refreshes public feeds, keeps a disk cache and serves filtered snapshots."""

    def __init__(
        self,
        state_directory: Path | None = None,
        *,
        sources: tuple[NewsSource, ...] = DEFAULT_SOURCES,
        fetcher: Callable[[NewsSource], bytes] = fetch_feed,
        refresh_seconds: int = REFRESH_SECONDS,
    ) -> None:
        self.state_directory = (state_directory or (
            Path.home() / ".local" / "state" / "duckos"
        )).expanduser()
        self.cache_path = self.state_directory / "news-cache.json"
        self.sources = sources
        self.fetcher = fetcher
        self.refresh_seconds = max(60, min(int(refresh_seconds), 3600))
        self._lock = threading.RLock()
        self._refresh_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None
        saved = read_json(self.cache_path, {})
        self._items = saved.get("items", []) if isinstance(saved, dict) else []
        self._items = [item for item in self._items if self._valid_cached_item(item)]
        self._updated_at = saved.get("updated_at") if isinstance(saved, dict) else None
        self._source_status = saved.get("sources", []) if isinstance(saved, dict) else []
        if not isinstance(self._source_status, list):
            self._source_status = []

    @staticmethod
    def _valid_cached_item(item: Any) -> bool:
        return (
            isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and isinstance(item.get("title"), str)
            and isinstance(item.get("url"), str)
            and item["url"].startswith("https://")
        )

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "status": "ready" if self._items else "empty",
                "article_count": len(self._items),
                "updated_at": self._updated_at,
                "refresh_seconds": self.refresh_seconds,
                "sources": list(self._source_status),
            }

    def snapshot(self, category: str = "Все", query: str = "", limit: int = 80) -> dict[str, Any]:
        if category not in CATEGORY_LABELS:
            raise ServiceError(f"unknown news category: {category}")
        if not isinstance(query, str) or len(query) > 160:
            raise ServiceError("news search query must be at most 160 characters")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_ITEMS:
            raise ServiceError(f"news limit must be between 1 and {MAX_ITEMS}")

        term = query.casefold().strip()
        with self._lock:
            items = list(self._items)
            sources = list(self._source_status)
            updated_at = self._updated_at

        if category != "Все":
            items = [item for item in items if item.get("category") == category]
        if term:
            items = [
                item for item in items
                if term in (item.get("title", "") + " " + item.get("summary", "") + " " + item.get("source", "")).casefold()
            ]
        items.sort(key=lambda item: item.get("published_at") or "", reverse=True)
        return {
            "status": "ready" if items else ("empty" if self._updated_at else "loading"),
            "items": items[:limit],
            "total": len(items),
            "updated_at": updated_at,
            "refresh_seconds": self.refresh_seconds,
            "categories": list(CATEGORY_LABELS),
            "sources": sources,
        }

    def refresh(self) -> dict[str, Any]:
        if not self._refresh_lock.acquire(blocking=False):
            return {"status": "already-running", **self.status()}

        try:
            fetched: list[dict[str, Any]] = []
            source_states: list[dict[str, Any]] = []
            with ThreadPoolExecutor(max_workers=min(4, len(self.sources) or 1)) as pool:
                jobs = {pool.submit(self.fetcher, source): source for source in self.sources}
                for future in as_completed(jobs):
                    source = jobs[future]
                    try:
                        articles = parse_feed(source, future.result())
                        fetched.extend(articles)
                        source_states.append({
                            "id": source.identifier,
                            "name": source.name,
                            "status": "ok",
                            "article_count": len(articles),
                            "checked_at": utc_now(),
                            "error": None,
                        })
                    except Exception as error:
                        source_states.append({
                            "id": source.identifier,
                            "name": source.name,
                            "status": "error",
                            "article_count": 0,
                            "checked_at": utc_now(),
                            "error": str(error)[:180],
                        })

            with self._lock:
                # A failed source must not erase its last good articles from cache.
                successful_ids = {
                    state["id"] for state in source_states if state["status"] == "ok"
                }
                retained = [
                    item for item in self._items
                    if item.get("source_id") not in successful_ids
                ]
                merged = {item["id"]: item for item in retained}
                for item in fetched:
                    merged[item["id"]] = item
                self._items = sorted(
                    merged.values(),
                    key=lambda item: item.get("published_at") or "",
                    reverse=True,
                )[:MAX_ITEMS]
                self._source_status = sorted(source_states, key=lambda item: item["name"])
                if fetched:
                    self._updated_at = utc_now()
                elif self._updated_at is None:
                    self._updated_at = None
                cache = {
                    "version": 1,
                    "updated_at": self._updated_at,
                    "items": self._items,
                    "sources": self._source_status,
                }
                atomic_write_json(self.cache_path, cache)
                return {
                    "status": "updated" if fetched else "no-new-data",
                    "fetched": len(fetched),
                    "article_count": len(self._items),
                    "updated_at": self._updated_at,
                    "sources": list(self._source_status),
                }
        finally:
            self._refresh_lock.release()

    def start_auto_refresh(self) -> None:
        with self._lock:
            if self._worker and self._worker.is_alive():
                return
            self._stop_event.clear()

            def run() -> None:
                while not self._stop_event.is_set():
                    self.refresh()
                    self._stop_event.wait(self.refresh_seconds)

            self._worker = threading.Thread(
                target=run,
                name="duckos-news-refresh",
                daemon=True,
            )
            self._worker.start()

    def stop_auto_refresh(self) -> None:
        self._stop_event.set()
        worker = self._worker
        if worker and worker.is_alive():
            worker.join(timeout=2)


def _is_local_origin(origin: str) -> bool:
    try:
        parsed = urllib.parse.urlsplit(origin)
        host = (parsed.hostname or "").casefold()
        return (
            parsed.scheme == "http"
            and host in {"localhost", "127.0.0.1", "::1"}
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False


class NewsAPIHandler(BaseHTTPRequestHandler):
    """Loopback-only JSON API handler; NewsService is attached by the server factory."""

    server_version = "DuckOSNews/0.1"
    sys_version = ""

    @property
    def news(self) -> NewsService:
        return self.server.news_service  # type: ignore[attr-defined]

    def log_message(self, format_string: str, *args: Any) -> None:
        # Keep local service output useful without logging query strings or feed content.
        print(f"duckos-news: {self.address_string()} {format_string % args}")

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        origin = self.headers.get("Origin", "")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if origin and _is_local_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def _origin_is_allowed(self) -> bool:
        origin = self.headers.get("Origin")
        return not origin or _is_local_origin(origin)

    def do_OPTIONS(self) -> None:
        if not self._origin_is_allowed():
            self._send_json(403, {"error": "origin is not allowed"})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin", "http://127.0.0.1"))
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        self.end_headers()

    def do_GET(self) -> None:
        if not self._origin_is_allowed():
            self._send_json(403, {"error": "origin is not allowed"})
            return
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/api/news/health":
            self._send_json(200, {"service": "duckos-newsroom", **self.news.status()})
            return
        if parsed.path == "/api/news/sources":
            self._send_json(200, {"sources": [
                {
                    "id": source.identifier,
                    "name": source.name,
                    "url": source.url,
                    "language": source.language,
                }
                for source in self.news.sources
            ]})
            return
        if parsed.path != "/api/news":
            self._send_json(404, {"error": "not found"})
            return

        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        category = query.get("category", ["Все"])[0]
        term = query.get("q", [""])[0]
        try:
            limit = int(query.get("limit", ["80"])[0])
            payload = self.news.snapshot(category, term, limit)
        except (ValueError, ServiceError) as error:
            self._send_json(400, {"error": str(error)})
            return
        self._send_json(200, payload)

    def do_POST(self) -> None:
        if not self._origin_is_allowed():
            self._send_json(403, {"error": "origin is not allowed"})
            return
        if urllib.parse.urlsplit(self.path).path != "/api/news/refresh":
            self._send_json(404, {"error": "not found"})
            return
        length = self.headers.get("Content-Length", "0")
        if length not in {"", "0"}:
            self._send_json(400, {"error": "request body must be empty"})
            return
        result = self.news.refresh()
        self._send_json(200, result)


def serve_api(service: NewsService, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run the JSON API on loopback only."""
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ServiceError("DuckOS News API may only bind to a loopback address")
    if isinstance(port, bool) or not isinstance(port, int) or not 1024 <= port <= 65535:
        raise ServiceError("news API port must be between 1024 and 65535")

    class NewsHTTPServer(ThreadingHTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    server = NewsHTTPServer((host, port), NewsAPIHandler)
    server.news_service = service  # type: ignore[attr-defined]
    service.start_auto_refresh()
    print(f"DuckOS Newsroom API listening on http://{host}:{port}")
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nDuckOS Newsroom API stopped.")
    finally:
        service.stop_auto_refresh()
        server.server_close()
