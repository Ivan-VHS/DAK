"""Deterministic formula analysis and bounded architecture planning for Jora."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from .registry import (
    COMPONENTS,
    COMPONENT_BY_ID,
    component_suggestions,
    resolve_component,
)

MAX_COMPONENTS = 256
MAX_FORMULA_CHARS = 16_384
MAX_SYNERGY_NEIGHBORS = 4


class FormulaError(ValueError):
    """Raised when a Jora application formula is invalid or ambiguous."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _split_formula(source: str) -> list[str]:
    if not isinstance(source, str) or not source.strip():
        raise FormulaError("Введите хотя бы один компонент формулы.")
    if len(source) > MAX_FORMULA_CHARS:
        raise FormulaError(f"Формула превышает лимит {MAX_FORMULA_CHARS} символов.")
    # '+' is the canonical operator. Commas, semicolons and conjunctions are
    # accepted as ergonomic separators, while component names remain registry data.
    tokens = re.split(r"\s*(?:\+|;|,|\bи\b|\band\b)\s*", source.strip(), flags=re.IGNORECASE)
    tokens = [token.strip() for token in tokens if token.strip()]
    if not tokens:
        raise FormulaError("Формула не содержит компонентов.")
    if len(tokens) > MAX_COMPONENTS:
        raise FormulaError(f"Допускается не более {MAX_COMPONENTS} компонентов в одной генерации.")
    return tokens


def _parse_token(token: str, index: int) -> dict[str, Any]:
    role = "standard"
    value = token
    for prefix, normalized_role in (
        ("основной:", "primary"),
        ("главный:", "primary"),
        ("primary:", "primary"),
        ("фоновый:", "background"),
        ("вспомогательный:", "background"),
        ("background:", "background"),
        ("опциональный:", "optional"),
        ("optional:", "optional"),
    ):
        if value.casefold().startswith(prefix):
            role = normalized_role
            value = value[len(prefix):].strip()
            break
    weight = 1
    match = re.search(r"\s*[xх×]\s*(\d+)\s*$", value, flags=re.IGNORECASE)
    if match:
        weight = int(match.group(1))
        value = value[:match.start()].strip()
        if not 1 <= weight <= 16:
            raise FormulaError(f"Вес компонента должен быть от 1 до 16: {token!r}")
    component = resolve_component(value)
    if component is None:
        suggestions = component_suggestions(value)
        suffix = f" Возможные варианты: {', '.join(suggestions)}." if suggestions else ""
        raise FormulaError(f"Неизвестный компонент: {value!r}.{suffix}")
    return {
        "position": index,
        "param_id": component["id"],
        "name": component["name"],
        "role": role,
        "weight": weight,
        "domain": component["domain"],
    }


def _validate_composition(items: list[dict[str, Any]]) -> list[str]:
    ids = [item["param_id"] for item in items]
    seen: set[str] = set()
    duplicate_ids: set[str] = set()
    for component_id in ids:
        if component_id in seen:
            duplicate_ids.add(component_id)
        seen.add(component_id)
    duplicates = sorted(duplicate_ids)
    if duplicates:
        raise FormulaError("Повторяющиеся компоненты: " + ", ".join(duplicates) + ". Укажите разные вариации или оставьте компонент один раз.")
    conflicts: list[str] = []
    selected = set(ids)
    network_components = {"cloud_sync", "cloud_streaming"}
    if "offline_mode" in selected and selected.intersection(network_components):
        conflicts.append("Строго офлайн-режим несовместим с компонентами, которым требуется сеть.")
    return conflicts


def normalize_formula(source: str) -> dict[str, Any]:
    tokens = _split_formula(source)
    items = [_parse_token(token, index) for index, token in enumerate(tokens)]
    conflicts = _validate_composition(items)
    if conflicts:
        raise FormulaError(" ".join(conflicts))
    canonical = {
        "schema": "duckos.jora.formula.v1",
        "components": [
            {
                "param_id": item["param_id"],
                "role": item["role"],
                "weight": item["weight"],
                "position": item["position"],
            }
            for item in items
        ],
    }
    digest = hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()
    return {
        "schema": "duckos.jora.formula.v1",
        "source": source,
        "components": items,
        "component_ids": [item["param_id"] for item in items],
        "canonical": canonical,
        "formula_hash": digest,
        "complexity": sum(item["weight"] for item in items),
        "conflicts": [],
    }


def _shared_contracts(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    a = COMPONENT_BY_ID[left["param_id"]]
    b = COMPONENT_BY_ID[right["param_id"]]
    shared = sorted(set(a["inputs"] + a["outputs"]) & set(b["inputs"] + b["outputs"]))
    if shared:
        return shared
    # Domain-specific adapters are first-class graph edges even if a producer
    # and consumer use different concrete record types.
    known = {
        frozenset(("text_editor", "audio_editor")): ["text.segment", "timeline.marker"],
        frozenset(("text_editor", "translator")): ["text.segment", "translation.segment"],
        frozenset(("audio_editor", "translator")): ["audio.segment", "translation.segment"],
        frozenset(("spreadsheet", "charts")): ["data.table", "chart.figure"],
        frozenset(("code_editor", "debugger")): ["source.file", "debug.report"],
        frozenset(("code_editor", "build_pipeline")): ["source.file", "build.artifact"],
        frozenset(("text_editor", "presentation")): ["text.document", "presentation.file"],
        frozenset(("image_editor", "video_editor")): ["image.asset", "video.asset"],
        frozenset(("notes", "task_board")): ["note.item", "task.item"],
        frozenset(("task_board", "calendar")): ["task.item", "calendar.event"],
        frozenset(("file_manager", "search_index")): ["filesystem.entry", "search.result"],
        frozenset(("version_control", "build_pipeline")): ["source.revision", "build.artifact"],
    }
    return known.get(frozenset((left["param_id"], right["param_id"])), [])


def build_graph(formula: dict[str, Any], *, max_neighbors: int = MAX_SYNERGY_NEIGHBORS) -> dict[str, Any]:
    if not 1 <= max_neighbors <= 16:
        raise ValueError("max_neighbors must be between 1 and 16")
    components = formula["components"]
    nodes = [{
        "id": "reaper:core",
        "kind": "coordinator",
        "name": "Reaper orchestration core",
        "domain": "runtime",
    }]
    nodes.extend({
        "id": item["param_id"],
        "kind": "component",
        "name": item["name"],
        "domain": item["domain"],
        "role": item["role"],
        "weight": item["weight"],
    } for item in components)
    edges: list[dict[str, Any]] = []
    for item in components:
        edges.append({
            "source": "reaper:core",
            "target": item["param_id"],
            "kind": "register_component",
            "contracts": ["jora.component.v1"],
        })

    # Bounded rolling indexes avoid scanning all earlier vertices. Every
    # component has a finite number of contracts; each index retains only M
    # recent candidates, so work per inserted node is bounded by M * K.
    synergy_pairs: set[tuple[str, str]] = set()
    contract_index: dict[str, list[str]] = {}
    domain_index: dict[str, list[str]] = {}
    seen_components: dict[str, dict[str, Any]] = {}
    special_pairs = {
        "text_editor": {"audio_editor"},
        "audio_editor": {"text_editor"},
    }
    for right in components:
        right_id = right["param_id"]
        right_spec = COMPONENT_BY_ID[right_id]
        candidates: set[str] = set()
        contracts_used = set(right_spec["inputs"] + right_spec["outputs"])
        for contract in contracts_used:
            candidates.update(contract_index.get(contract, ()))
        candidates.update(domain_index.get(right["domain"], ()))
        candidates.update(left_id for left_id in special_pairs.get(right_id, ()) if left_id in seen_components)
        scored = []
        for left_id in candidates:
            left = seen_components[left_id]
            contracts = _shared_contracts(left, right)
            if not contracts and left["domain"] == right["domain"]:
                contracts = ["domain.shared"]
            if contracts:
                scored.append((len(contracts), left_id, contracts))
        scored.sort(key=lambda item: (-item[0], item[1]))
        for _score, left_id, contracts in scored[:max_neighbors]:
            pair = tuple(sorted((left_id, right_id)))
            if pair in synergy_pairs:
                continue
            synergy_pairs.add(pair)
            edges.append({
                "source": pair[0],
                "target": pair[1],
                "kind": "typed_synergy",
                "contracts": contracts,
            })
        for contract in contracts_used:
            index = contract_index.setdefault(contract, [])
            index.append(right_id)
            if len(index) > max_neighbors:
                del index[:-max_neighbors]
        domain_list = domain_index.setdefault(right["domain"], [])
        domain_list.append(right_id)
        if len(domain_list) > max_neighbors:
            del domain_list[:-max_neighbors]
        seen_components[right_id] = right

    cluster_map: dict[str, list[str]] = {}
    for item in components:
        cluster_map.setdefault(item["domain"], []).append(item["param_id"])
    clusters = [
        {"id": f"cluster:{domain}", "domain": domain, "members": members}
        for domain, members in sorted(cluster_map.items())
    ]
    return {
        "schema": "duckos.jora.graph.v1",
        "topology": "bounded_hub_cluster",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "max_synergy_neighbors": max_neighbors,
        "nodes": nodes,
        "edges": edges,
        "clusters": clusters,
        "complexity": {
            "node_growth": "O(N)",
            "edge_growth": "O(N*M)",
            "candidate_lookup": "O(N*M*K) with bounded contract-index width K",
            "max_direct_synergy_degree": max_neighbors,
            "note": "Finite generation is bounded by the configured component and resource budgets; this is not a claim of infinite execution.",
        },
    }


def select_languages(formula: dict[str, Any], *, profile: str = "desktop", toolchain: dict[str, str | None] | None = None) -> dict[str, Any]:
    if profile not in {"desktop", "web", "cli", "source_only"}:
        raise ValueError("profile must be desktop, web, cli or source_only")
    if toolchain is None:
        has_python = bool(shutil.which("python3") or shutil.which("python") or sys.executable)
        has_rust = bool(shutil.which("rustc"))
        has_c = bool(shutil.which("cc") or shutil.which("gcc") or shutil.which("clang"))
        has_typescript = bool(shutil.which("tsc"))
    else:
        # An explicit toolchain map is a deterministic test/build-environment override.
        has_python = bool(toolchain.get("python"))
        has_rust = bool(toolchain.get("rust"))
        has_c = bool(toolchain.get("c"))
        has_typescript = bool(toolchain.get("typescript"))
    chosen = [{"language": "Reaper", "role": "core", "reason": "Обязательное системно-интеграционное ядро Jora и основной генерируемый исходник."}]
    required = {item["param_id"] for item in formula["components"]}
    warnings: list[str] = []
    if required & {"translator", "glossary", "speech_to_text", "text_to_speech", "search_index", "subtitle_export", "presentation"}:
        if has_python:
            chosen.append({"language": "Python", "role": "specialized", "reason": "Доступен локальный Python toolchain; выбран для текстовых и контентных адаптеров."})
        else:
            warnings.append("Python недоступен: специализированный текстовый адаптер не включён в пакет.")
    if "audio_editor" in required or "video_editor" in required:
        if has_rust:
            chosen.append({"language": "Rust", "role": "specialized", "reason": "rustc доступен; выбран для безопасного вспомогательного аудио/медиа ядра."})
        elif has_c:
            chosen.append({"language": "C", "role": "specialized", "reason": "Доступен C-компилятор; выбран компактный ABI-модуль для медиа-операций."})
        else:
            warnings.append("Rust/C toolchain не найден: для этой сборки доступен только Reaper-каркас без нативного DSP-модуля.")
    if profile == "web":
        if has_typescript:
            chosen.append({"language": "TypeScript", "role": "ui", "reason": "tsc обнаружен в среде сборки; выбран для веб-интерфейса."})
        else:
            warnings.append("TypeScript toolchain не найден; веб-профиль использует существующую JavaScript оболочку или требует настройки сборщика.")
    unique = []
    seen = set()
    for item in chosen:
        key = item["language"].casefold()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return {
        "schema": "duckos.jora.language-plan.v1",
        "profile": profile,
        "languages": unique,
        "warnings": warnings,
        "reaper_compiler": "not_assumed",
        "native_compilation": "only_when_a_real_target_toolchain_is_detected",
    }


def _generated_brand(ids: list[str]) -> tuple[str, str]:
    selected = set(ids)
    if selected == {"text_editor", "audio_editor", "translator"}:
        return "Слововолна", "slovovolna"
    if "audio_editor" in selected and "translator" in selected:
        return "Voxling", "voxling"
    if "text_editor" in selected and "translator" in selected:
        return "Lexora", "lexora"
    if "code_editor" in selected and "debugger" in selected:
        return "Tracecraft", "tracecraft"
    if "spreadsheet" in selected and "charts" in selected:
        return "DataVista", "datavista"
    if "notes" in selected and "task_board" in selected:
        return "Taskora", "taskora"
    domain_names = sorted({COMPONENT_BY_ID[item]["domain"] for item in ids})
    stems = {
        "text": "Lex", "audio": "Vox", "language": "Ling", "media": "Frame",
        "productivity": "Tempo", "data": "Datum", "development": "Forge",
        "system": "Nexus", "network": "Relay", "quality": "Clarity",
    }
    stem = stems.get(domain_names[0], "Nova") if domain_names else "Nova"
    if len(domain_names) > 1:
        stem += stems.get(domain_names[1], "Flow")
    digest = hashlib.sha256("|".join(ids).encode("utf-8")).hexdigest()[:4]
    display = stem + digest.upper()
    slug = re.sub(r"[^a-z0-9]+", "-", display.casefold()).strip("-")
    return display, slug


def generate_identity(formula: dict[str, Any], *, existing_slugs: set[str] | None = None) -> dict[str, str]:
    display, slug = _generated_brand(formula["component_ids"])
    occupied = existing_slugs or set()
    if slug in occupied:
        suffix = formula["formula_hash"][:6]
        slug = f"{slug}-{suffix}"
        display = f"{display} {suffix.upper()}"
    summary = "; ".join(COMPONENT_BY_ID[item]["summary"] for item in formula["component_ids"])
    return {
        "display_name": display,
        "slug": slug,
        "app_id": f"local.duckos.jora.{slug.replace('-', '.')}",
        "tagline": f"Собрано из {len(formula['components'])} совместимых компонентов",
        "description": summary,
    }


def analyze_formula(source: str, *, profile: str = "desktop", existing_slugs: set[str] | None = None) -> dict[str, Any]:
    formula = normalize_formula(source)
    graph = build_graph(formula)
    languages = select_languages(formula, profile=profile)
    identity = generate_identity(formula, existing_slugs=existing_slugs)
    return {
        "schema": "duckos.jora.analysis.v1",
        "formula": formula,
        "identity": identity,
        "graph": graph,
        "languages": languages,
    }
