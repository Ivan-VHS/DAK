"""Safe user-space utilities shared by Duck's built-in tools.

All functions are bounded and operate on caller-selected data. They do not invoke
a shell, install packages, alter host networking or modify system services.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import secrets
import socket
import ssl
import struct
import time
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

MAX_TEXT_BYTES = 4 * 1024 * 1024
MAX_CSV_ROWS = 5000
MAX_FEED_ITEMS = 100
MAX_HASH_BYTES = 2 * 1024 * 1024 * 1024


def generate_secret(length: int = 32, *, alphabet: str | None = None) -> str:
    """Generate a cryptographically random secret using the OS CSPRNG."""
    if isinstance(length, bool) or not isinstance(length, int) or not 16 <= length <= 256:
        raise ValueError("Secret length must be between 16 and 256 characters")
    pool = alphabet or (
        "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
        "23456789!#$%&()*+,-./:;<=>?@[]^_{|}~"
    )
    if not isinstance(pool, str) or len(set(pool)) < 2 or len(pool) > 256:
        raise ValueError("Alphabet must contain at least two unique characters")
    return "".join(secrets.choice(pool) for _ in range(length))


def text_statistics(text: str) -> dict[str, int]:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    encoded_size = len(text.encode("utf-8"))
    if encoded_size > MAX_TEXT_BYTES:
        raise ValueError("Text exceeds the 4 MiB processing limit")
    lines = text.splitlines()
    paragraphs = [part for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
    return {
        "characters": len(text),
        "characters_without_spaces": sum(not char.isspace() for char in text),
        "words": len(re.findall(r"\S+", text)),
        "lines": len(lines),
        "paragraphs": len(paragraphs),
        "utf8_bytes": encoded_size,
    }


def inspect_csv(text: str, *, delimiter: str = ",", preview_rows: int = 50) -> dict[str, Any]:
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        raise ValueError("CSV input must be text no larger than 4 MiB")
    if not isinstance(delimiter, str) or len(delimiter) != 1:
        raise ValueError("Delimiter must be exactly one character")
    if isinstance(preview_rows, bool) or not isinstance(preview_rows, int) or not 1 <= preview_rows <= 200:
        raise ValueError("preview_rows must be between 1 and 200")
    try:
        rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True))
    except csv.Error as error:
        raise ValueError(f"Invalid CSV: {error}") from error
    if len(rows) > MAX_CSV_ROWS + 1:
        raise ValueError(f"CSV exceeds the {MAX_CSV_ROWS}-row limit")
    if not rows:
        return {"headers": [], "row_count": 0, "preview": [], "column_count": 0}
    headers = rows[0]
    mismatched = [
        index + 2 for index, row in enumerate(rows[1:])
        if len(row) != len(headers)
    ]
    return {
        "headers": headers,
        "row_count": max(0, len(rows) - 1),
        "column_count": len(headers),
        "preview": rows[1:preview_rows + 1],
        "invalid_row_widths": mismatched[:100],
    }


def convert_text_encoding(
    content: bytes,
    source_encoding: str,
    target_encoding: str,
    *,
    line_endings: str = "preserve",
) -> bytes:
    if not isinstance(content, bytes) or len(content) > MAX_TEXT_BYTES:
        raise ValueError("Input must be bytes no larger than 4 MiB")
    if line_endings not in {"preserve", "lf", "crlf", "cr"}:
        raise ValueError("line_endings must be preserve, lf, crlf or cr")
    try:
        decoded = content.decode(source_encoding, errors="strict")
    except (LookupError, UnicodeError) as error:
        raise ValueError(f"Cannot decode input: {error}") from error
    if line_endings != "preserve":
        normalized = decoded.replace("\r\n", "\n").replace("\r", "\n")
        ending = {"lf": "\n", "crlf": "\r\n", "cr": "\r"}[line_endings]
        decoded = normalized.replace("\n", ending)
    try:
        return decoded.encode(target_encoding, errors="strict")
    except (LookupError, UnicodeError) as error:
        raise ValueError(f"Cannot encode output: {error}") from error


def _json_to_xml(value: Any, tag: str = "item") -> ET.Element:
    element = ET.Element(tag)
    if isinstance(value, dict):
        for key, item in value.items():
            safe_tag = re.sub(r"[^A-Za-z0-9_.-]", "_", str(key))
            if not safe_tag or not re.match(r"[A-Za-z_]", safe_tag[0]):
                safe_tag = "field_" + safe_tag
            element.append(_json_to_xml(item, safe_tag))
    elif isinstance(value, list):
        for item in value:
            element.append(_json_to_xml(item, "item"))
    elif value is not None:
        element.text = str(value).lower() if isinstance(value, bool) else str(value)
    return element


def _xml_value(element: ET.Element) -> Any:
    children = list(element)
    if not children:
        text = element.text or ""
        return text
    grouped: dict[str, list[Any]] = {}
    for child in children:
        grouped.setdefault(child.tag, []).append(_xml_value(child))
    result: dict[str, Any] = {
        key: values[0] if len(values) == 1 else values
        for key, values in grouped.items()
    }
    if element.text and element.text.strip():
        result["#text"] = element.text.strip()
    return result


def convert_json_xml(content: str, target: str) -> str:
    if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_TEXT_BYTES:
        raise ValueError("Input must be text no larger than 4 MiB")
    if target == "xml":
        try:
            value = json.loads(content)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON: {error}") from error
        root = _json_to_xml(value, "root")
        return ET.tostring(root, encoding="unicode", xml_declaration=False)
    if target == "json":
        try:
            root = ET.fromstring(content)
        except ET.ParseError as error:
            raise ValueError(f"Invalid XML: {error}") from error
        return json.dumps({root.tag: _xml_value(root)}, ensure_ascii=False, indent=2, allow_nan=False)
    raise ValueError("target must be 'json' or 'xml'")


_UNIT_FACTORS: dict[str, tuple[str, Decimal]] = {
    "m": ("length", Decimal("1")),
    "km": ("length", Decimal("1000")),
    "cm": ("length", Decimal("0.01")),
    "mm": ("length", Decimal("0.001")),
    "in": ("length", Decimal("0.0254")),
    "ft": ("length", Decimal("0.3048")),
    "g": ("mass", Decimal("1")),
    "kg": ("mass", Decimal("1000")),
    "lb": ("mass", Decimal("453.59237")),
    "B": ("data", Decimal("1")),
    "KB": ("data", Decimal("1000")),
    "MB": ("data", Decimal("1000000")),
    "GB": ("data", Decimal("1000000000")),
    "KiB": ("data", Decimal("1024")),
    "MiB": ("data", Decimal("1048576")),
    "GiB": ("data", Decimal("1073741824")),
    "s": ("time", Decimal("1")),
    "min": ("time", Decimal("60")),
    "h": ("time", Decimal("3600")),
}


def convert_units(value: str | int | float, source_unit: str, target_unit: str) -> str:
    try:
        amount = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("Value must be a finite number") from error
    if not amount.is_finite():
        raise ValueError("Value must be finite")
    if source_unit in {"C", "F", "K"} and target_unit in {"C", "F", "K"}:
        if source_unit == "C":
            kelvin = amount + Decimal("273.15")
        elif source_unit == "F":
            kelvin = (amount - Decimal("32")) * Decimal(5) / Decimal(9) + Decimal("273.15")
        else:
            kelvin = amount
        if kelvin < 0:
            raise ValueError("Temperature cannot be below absolute zero")
        if target_unit == "K":
            result = kelvin
        elif target_unit == "C":
            result = kelvin - Decimal("273.15")
        else:
            result = (kelvin - Decimal("273.15")) * Decimal(9) / Decimal(5) + Decimal("32")
        return format(result.normalize(), "f")
    if source_unit not in _UNIT_FACTORS or target_unit not in _UNIT_FACTORS:
        raise ValueError("Unsupported unit")
    source_kind, source_factor = _UNIT_FACTORS[source_unit]
    target_kind, target_factor = _UNIT_FACTORS[target_unit]
    if source_kind != target_kind:
        raise ValueError("Units belong to different dimensions")
    result = amount * source_factor / target_factor
    return format(result.normalize(), "f")


def sha256_file(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if target.is_symlink() or not target.is_file():
        raise ValueError("Hash target must be a regular file, not a symbolic link")
    size = target.stat().st_size
    if size > MAX_HASH_BYTES:
        raise ValueError("File exceeds the 2 GiB hash limit")
    digest = hashlib.sha256()
    with target.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"algorithm": "SHA-256", "digest": digest.hexdigest(), "size_bytes": size}


def verify_tls(host: str, port: int = 443, timeout: float = 5.0) -> dict[str, Any]:
    if not isinstance(host, str) or not host.strip() or len(host) > 253 or any(char.isspace() for char in host):
        raise ValueError("Enter a valid TLS host name")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0.2 <= timeout <= 15:
        raise ValueError("Timeout must be between 0.2 and 15 seconds")
    context = ssl.create_default_context()
    started = time.monotonic()
    with socket.create_connection((host, port), timeout=float(timeout)) as raw:
        with context.wrap_socket(raw, server_hostname=host) as connection:
            certificate = connection.getpeercert()
            cipher = connection.cipher()
            return {
                "host": host,
                "port": port,
                "tls_version": connection.version(),
                "cipher": cipher[0] if cipher else None,
                "peer": certificate.get("subject", ()),
                "issuer": certificate.get("issuer", ()),
                "not_after": certificate.get("notAfter"),
                "verified_by_system_trust_store": True,
                "duration_ms": round((time.monotonic() - started) * 1000, 2),
            }


def read_rss(content: str, *, limit: int = 30) -> dict[str, Any]:
    if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_TEXT_BYTES:
        raise ValueError("Feed must be text no larger than 4 MiB")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_FEED_ITEMS:
        raise ValueError(f"limit must be between 1 and {MAX_FEED_ITEMS}")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as error:
        raise ValueError(f"Invalid RSS/Atom XML: {error}") from error

    def find_text(parent: ET.Element, names: tuple[str, ...]) -> str:
        for node in parent.iter():
            local_name = node.tag.rsplit("}", 1)[-1].casefold()
            if local_name in names and node.text:
                return re.sub(r"\s+", " ", node.text).strip()[:2000]
        return ""

    rows = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1].casefold() not in {"item", "entry"}:
            continue
        title = find_text(node, ("title",))
        link = find_text(node, ("link",))
        if not link:
            for child in node:
                if child.tag.rsplit("}", 1)[-1].casefold() == "link":
                    link = child.attrib.get("href", "")
                    break
        rows.append({
            "title": title,
            "link": link[:2048],
            "published": find_text(node, ("pubdate", "published", "updated", "date")),
            "summary": find_text(node, ("description", "summary", "content")),
        })
        if len(rows) >= limit:
            break
    return {
        "feed_title": find_text(root, ("title",)),
        "items": rows,
        "count": len(rows),
        "truncated": len(rows) >= limit,
    }


def list_listening_ports() -> dict[str, Any]:
    """Read TCP listening sockets; uses psutil if installed, /proc on Linux otherwise."""
    try:
        import psutil  # type: ignore[import-not-found]

        rows = []
        for connection in psutil.net_connections(kind="inet"):
            if connection.status != psutil.CONN_LISTEN or not connection.laddr:
                continue
            rows.append({
                "protocol": "tcp",
                "address": connection.laddr.ip,
                "port": int(connection.laddr.port),
                "pid": connection.pid,
            })
        rows.sort(key=lambda row: (row["port"], row["address"]))
        return {"source": "psutil", "ports": rows, "read_only": True}
    except ImportError:
        pass
    except OSError:
        pass

    proc = Path("/proc/net/tcp")
    if not proc.is_file():
        return {"source": "unavailable", "ports": [], "read_only": True, "note": "Install psutil or use a supported platform provider."}

    rows = []
    for filename in ("/proc/net/tcp", "/proc/net/tcp6"):
        path = Path(filename)
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="ascii").splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            parts = line.split()
            if len(parts) < 4 or parts[3] != "0A":
                continue
            raw_address, raw_port = parts[1].split(":")
            port = int(raw_port, 16)
            if filename.endswith("tcp6"):
                raw = bytes.fromhex(raw_address)
                address_bytes = b"".join(raw[index:index + 4][::-1] for index in range(0, 16, 4))
                address = socket.inet_ntop(socket.AF_INET6, address_bytes)
                protocol = "tcp6"
            else:
                address = socket.inet_ntop(socket.AF_INET, bytes.fromhex(raw_address)[::-1])
                protocol = "tcp"
            rows.append({"protocol": protocol, "address": address, "port": port, "pid": None})
    rows.sort(key=lambda row: (row["port"], row["address"]))
    return {"source": "procfs", "ports": rows, "read_only": True}
