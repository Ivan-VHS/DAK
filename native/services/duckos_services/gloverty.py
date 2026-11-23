"""Gloverty: semantic UI palettes and WCAG contrast checks."""

from __future__ import annotations

from .common import ServiceError


PALETTES = {
    "dark": {
        "background": "#07111F",
        "surface": "#12283D",
        "text": "#F1F7FC",
        "muted": "#B5C6D4",
        "accent": "#7BE0FF",
        "danger": "#FF8A8A",
        "success": "#7DE2B2",
    },
    "light": {
        "background": "#F3F7FA",
        "surface": "#FFFFFF",
        "text": "#172B3A",
        "muted": "#455E70",
        "accent": "#006D91",
        "danger": "#A82020",
        "success": "#146B43",
    },
    "high-contrast": {
        "background": "#000000",
        "surface": "#111111",
        "text": "#FFFFFF",
        "muted": "#E5E5E5",
        "accent": "#FFFF00",
        "danger": "#FF6666",
        "success": "#66FF99",
    },
}


def _rgb(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
        raise ServiceError(f"invalid color value: {value!r}")
    try:
        red = int(value[1:3], 16)
        green = int(value[3:5], 16)
        blue = int(value[5:7], 16)
    except ValueError as error:
        raise ServiceError(f"invalid color value: {value!r}") from error
    return red, green, blue


def _luminance(color: str) -> float:
    channels = []
    for channel in _rgb(color):
        value = channel / 255
        linear = value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        channels.append(linear)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(foreground: str, background: str) -> float:
    first = _luminance(foreground)
    second = _luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def palette(name: str) -> dict[str, str]:
    try:
        return dict(PALETTES[name])
    except KeyError as error:
        raise ServiceError(f"unknown theme: {name}") from error


def audit_palette(name: str) -> dict:
    """Return explicit contrast results for common interface text and status colors."""
    colors = palette(name)
    pairs = (
        ("text/background", "text", "background", 4.5),
        ("muted/background", "muted", "background", 4.5),
        ("text/surface", "text", "surface", 4.5),
        ("accent/background", "accent", "background", 3.0),
        ("danger/background", "danger", "background", 3.0),
        ("success/background", "success", "background", 3.0),
    )
    checks = []
    for label, foreground, background, minimum in pairs:
        ratio = contrast_ratio(colors[foreground], colors[background])
        checks.append({
            "pair": label,
            "ratio": round(ratio, 2),
            "minimum": minimum,
            "passes": ratio >= minimum,
        })
    return {
        "theme": name,
        "passes": all(item["passes"] for item in checks),
        "checks": checks,
    }
