"""Read-only industrial operations and maintenance console for DuckOS.

Foundry correlates existing DuckOS diagnostics into one operator report. It
does not control machinery, install drivers, stop processes or change the OS.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
from datetime import datetime, timezone
from typing import Any

from .compat.bridge import detect_runtimes
from .desktop.service import DesktopService
from .hardware_inventory import HardwareInventoryError, collect_host_inventory

SCHEMA = "duckos.foundry.snapshot.v1"
RUNBOOK_SCHEMA = "duckos.foundry.runbook.v1"

_PROFILES = {
    "routine": {
        "title": "Пусковой контроль",
        "description": "Краткая проверка перед началом рабочего цикла.",
        "steps": [
            ("resources", "Проверить загрузку процессора и доступную память"),
            ("workspace", "Просмотреть рабочую среду и пользовательскую автозагрузку"),
            ("hardware", "Сверить состояние обнаруженных устройств и драйверов"),
            ("runtime", "Проверить наличие совместимых сред, если они требуются"),
        ],
    },
    "preventive": {
        "title": "Профилактическое обслуживание",
        "description": "Плановая проверка ресурсов, устройств и готовности подсистем.",
        "steps": [
            ("snapshot", "Снять полный диагностический слепок DuckOS"),
            ("resources", "Сопоставить текущую нагрузку с обычным рабочим уровнем"),
            ("hardware", "Проверить устройства с отсутствующим драйвером или ошибкой"),
            ("workspace", "Разобрать рекомендации по рабочей среде и автозагрузке"),
            ("runtime", "Проверить доступность совместимых сред без их запуска"),
            ("review", "Зафиксировать решения оператора отдельным регламентом"),
        ],
    },
    "incident": {
        "title": "Разбор инцидента",
        "description": "Сначала собрать свидетельства, затем определить безопасный порядок проверки.",
        "steps": [
            ("snapshot", "Сохранить исходный диагностический слепок до изменений"),
            ("resources", "Найти процессы и ресурсы с аномальной нагрузкой"),
            ("hardware", "Проверить ошибки устройств и состояние привязки драйверов"),
            ("runtime", "Проверить диагностические блокеры совместимости"),
            ("review", "Сопоставить время события с журналами соответствующих компонентов"),
            ("approval", "Любое изменение выполнять отдельно после оценки риска и подтверждения"),
        ],
    },
    "commissioning": {
        "title": "Ввод в эксплуатацию",
        "description": "Проверить базовую готовность узлов и программных контуров.",
        "steps": [
            ("snapshot", "Снять исходное состояние системы"),
            ("hardware", "Сверить обнаруженные устройства и драйверы"),
            ("resources", "Проверить доступность системной памяти и процессорных метрик"),
            ("runtime", "Проверить обнаруживаемые среды совместимости"),
            ("workspace", "Проверить пользовательскую среду и точки запуска"),
            ("review", "Сверить ограничения реализации DuckOS перед допуском к эксплуатации"),
        ],
    },
}


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _finding(
    finding_id: str,
    severity: str,
    title: str,
    detail: str,
    next_step: str,
) -> dict[str, str]:
    return {
        "id": finding_id,
        "severity": severity,
        "title": title,
        "detail": detail,
        "next_step": next_step,
    }


def _evaluate(
    desktop_audit: dict[str, Any] | None,
    hardware: dict[str, Any] | None,
    runtimes: dict[str, Any] | None,
) -> tuple[str, list[dict[str, str]], dict[str, Any]]:
    findings: list[dict[str, str]] = []
    resources = desktop_audit.get("resources", {}) if desktop_audit else {}
    memory = _as_number(resources.get("memory_used_percent"))
    cpu = _as_number(resources.get("cpu_percent"))

    if memory is not None:
        if memory >= 95:
            findings.append(_finding(
                "memory-pressure", "critical", "Критическая нагрузка памяти",
                f"Используется {memory:.1f}% обнаруженной физической памяти.",
                "Проверить процессы с наибольшим расходом памяти и подтвердить причину роста.",
            ))
        elif memory >= 85:
            findings.append(_finding(
                "memory-pressure", "warning", "Повышенная нагрузка памяти",
                f"Используется {memory:.1f}% обнаруженной физической памяти.",
                "Проверить динамику памяти и процессы с наибольшим расходом.",
            ))

    if cpu is not None and cpu >= 98:
        findings.append(_finding(
            "cpu-pressure", "warning", "Высокая загрузка процессора",
            f"Измеренная загрузка CPU составляет {cpu:.1f}%.",
            "Проверить активные процессы и повторить измерение после короткого интервала.",
        ))

    if desktop_audit:
        desktop = desktop_audit.get("desktop", {})
        count = desktop.get("count")
        if isinstance(count, int) and count > 10:
            findings.append(_finding(
                "workspace-load", "info", "Рабочая область требует разбора",
                f"На рабочем столе обнаружено элементов: {count}; ориентир Duck Desktop — 10.",
                "Просмотреть список и вручную переместить ненужные обычные файлы в Inbox.",
            ))

        for recommendation in desktop_audit.get("recommendations", []):
            if recommendation.get("id") == "temporary-names":
                findings.append(_finding(
                    "temporary-files", "info", "Найдены временные имена файлов",
                    recommendation.get("detail", "Проверьте элементы рабочего стола."),
                    "Проверить назначение файлов; Foundry не удаляет и не перемещает их автоматически.",
                ))

    device_summary = hardware.get("summary", {}) if hardware else {}
    device_problems = device_summary.get("device_problem", 0)
    missing_drivers = device_summary.get("driver_missing", 0)
    if isinstance(device_problems, int) and device_problems:
        findings.append(_finding(
            "device-problems", "warning", "Устройства сообщают об ошибках",
            f"В снимке обнаружено устройств с ошибочным состоянием: {device_problems}.",
            "Сверить точные идентификаторы и журналы устройства штатными средствами платформы.",
        ))
    if isinstance(missing_drivers, int) and missing_drivers:
        findings.append(_finding(
            "drivers-unbound", "info", "Есть устройства без привязанного драйвера",
            f"Устройств без обнаруженной привязки драйвера: {missing_drivers}.",
            "Проверить модель устройства и совместимость драйвера; Foundry ничего не устанавливает.",
        ))

    runtime_count = None
    if runtimes:
        runtime_rows = runtimes.get("runtimes", [])
        runtime_count = sum(1 for item in runtime_rows if item.get("available") is True)
        if runtime_count == 0:
            findings.append(_finding(
                "no-compat-runtime", "info", "Среды совместимости не обнаружены",
                "DuckBridge не нашёл поддерживаемых точек запуска совместимости.",
                "Это не влияет на нативные приложения; проверьте Bridge только при необходимости.",
            ))

    critical = any(item["severity"] == "critical" for item in findings)
    warning = any(item["severity"] == "warning" for item in findings)
    source_count = sum(value is not None for value in (desktop_audit, hardware, runtimes))
    if source_count == 0:
        state = "unavailable"
    elif critical:
        state = "critical"
    elif warning:
        state = "attention"
    else:
        state = "nominal"

    metrics = {
        "cpu_percent": cpu,
        "memory_used_percent": memory,
        "memory_total_bytes": resources.get("memory_total_bytes"),
        "memory_available_bytes": resources.get("memory_available_bytes"),
        "desktop_items": (desktop_audit or {}).get("desktop", {}).get("count"),
        "startup_entries": (desktop_audit or {}).get("startup", {}).get("count"),
        "devices_total": device_summary.get("total_devices"),
        "devices_with_problems": device_problems,
        "devices_without_driver": missing_drivers,
        "compatibility_runtimes": runtime_count,
    }
    return state, findings, metrics


def collect_foundry_snapshot(
    *,
    include_devices: bool = True,
    include_runtimes: bool = True,
) -> dict[str, Any]:
    """Collect bounded local diagnostics without changing host state."""
    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    desktop_audit: dict[str, Any] | None = None
    hardware: dict[str, Any] | None = None
    runtimes: dict[str, Any] | None = None
    errors: list[dict[str, str]] = []

    try:
        desktop_audit = DesktopService().audit()
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        errors.append({"source": "duck-desktop", "message": str(error)[:240]})

    if include_devices:
        try:
            hardware = collect_host_inventory()
        except (HardwareInventoryError, OSError, RuntimeError) as error:
            errors.append({"source": "hardware-inventory", "message": str(error)[:240]})

    if include_runtimes:
        try:
            runtimes = detect_runtimes()
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            errors.append({"source": "duckbridge", "message": str(error)[:240]})

    state, findings, metrics = _evaluate(desktop_audit, hardware, runtimes)
    modules = [
        {
            "id": "resources",
            "name": "Ресурсы и процессы",
            "state": "available" if desktop_audit and desktop_audit.get("resources") else "unavailable",
            "source": "Duck Desktop host snapshot",
        },
        {
            "id": "workspace",
            "name": "Рабочая среда",
            "state": "available" if desktop_audit else "unavailable",
            "source": "Duck Desktop read-only audit",
        },
        {
            "id": "hardware",
            "name": "Устройства и драйверы",
            "state": "available" if hardware else "unavailable" if include_devices else "not_requested",
            "source": "PCI/USB sysfs or Windows PnP inventory",
        },
        {
            "id": "runtime",
            "name": "Среды совместимости",
            "state": "available" if runtimes else "unavailable" if include_runtimes else "not_requested",
            "source": "DuckBridge runtime discovery",
        },
        {
            "id": "recovery",
            "name": "Обновление и восстановление ОС",
            "state": "specified",
            "source": "A/B update and recovery architecture; native OS updater is not connected",
        },
        {
            "id": "security",
            "name": "Изоляция и контроль полномочий",
            "state": "specified",
            "source": "Sentinel shell preferences; kernel enforcement is not connected",
        },
    ]

    return {
        "schema": SCHEMA,
        "captured_at": captured_at,
        "operating_system": "DuckOS",
        "host": {
            "platform": platform.system(),
            "architecture": platform.machine() or "unknown",
        },
        "scope": "local_read_only_user_space",
        "state": state,
        "metrics": metrics,
        "modules": modules,
        "findings": findings,
        "sources": {
            "desktop_audit": desktop_audit,
            "hardware_inventory": hardware,
            "runtime_discovery": runtimes,
        },
        "collection_errors": errors,
        "execution_policy": {
            "read_only": True,
            "network_access": False,
            "processes_started": False,
            "processes_terminated": False,
            "drivers_changed": False,
            "system_settings_changed": False,
            "external_machinery_control": False,
        },
        "privacy": {
            "raw_device_instance_ids_included": False,
            "device_identity_hashes_are_per_snapshot": True,
            "report_is_local": True,
        },
    }


def build_runbook(profile: str, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create an operator-reviewed checklist. Nothing in a runbook is executed."""
    if profile not in _PROFILES:
        raise ValueError(f"unknown Foundry profile: {profile}")
    definition = _PROFILES[profile]
    findings = snapshot.get("findings", []) if isinstance(snapshot, dict) else []
    steps = []
    for index, (step_id, title) in enumerate(definition["steps"], start=1):
        steps.append({
            "number": index,
            "id": step_id,
            "title": title,
            "state": "pending",
            "execution": "manual_only",
            "destructive": False,
        })

    return {
        "schema": RUNBOOK_SCHEMA,
        "profile": profile,
        "title": definition["title"],
        "description": definition["description"],
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "linked_snapshot": snapshot.get("captured_at") if isinstance(snapshot, dict) else None,
        "steps": steps,
        "open_findings": [item.get("id") for item in findings if isinstance(item, dict)],
        "execution_policy": {
            "automatic_execution": False,
            "shell_commands": False,
            "hardware_writes": False,
            "operator_review_required": True,
        },
    }


def write_snapshot(path: str | Path, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Create a new private report file; refuse links and existing destinations."""
    destination = Path(path).expanduser()
    if destination.name in {"", ".", ".."} or destination.is_symlink():
        raise ValueError("report destination must be a regular new file path")
    parent = destination.parent.resolve(strict=True)
    if not parent.is_dir():
        raise ValueError("report parent must be an existing directory")
    target = parent / destination.name
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"report already exists: {target.name}")

    encoded = json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(target, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            target.unlink()
        except OSError:
            pass
        raise
    return {
        "schema": "duckos.foundry.report-export.v1",
        "written": str(target),
        "bytes": len(encoded.encode("utf-8")),
        "overwritten": False,
        "disk_write": "explicit_operator_export",
    }
