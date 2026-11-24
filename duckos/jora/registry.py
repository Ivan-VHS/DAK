"""Versioned capability registry for the DuckOS Jora synthesis engine."""
from __future__ import annotations

from copy import deepcopy

REGISTRY_SCHEMA = "duckos.jora.component-registry.v1"
REGISTRY_VERSION = "1.0.0"

# Registry entries are declarative. They describe capability boundaries; they do
# not assert that every target platform or optional backend is installed.
_COMPONENTS = (
    {
        "id": "text_editor", "name": "Текстовый редактор",
        "aliases": ("текстовый редактор", "редактор текста", "text editor", "text_editor", "markdown editor", "markdown редактор"),
        "domain": "text", "inputs": ("text.document",), "outputs": ("text.document", "text.segment"),
        "preferred_languages": ("python",), "summary": "Создание и редактирование структурированных текстовых документов.",
    },
    {
        "id": "audio_editor", "name": "Аудиоредактор",
        "aliases": ("аудиоредактор", "редактор аудио", "audio editor", "audio_editor", "sound editor", "звукоредактор"),
        "domain": "audio", "inputs": ("audio.asset", "audio.segment"), "outputs": ("audio.asset", "audio.segment", "timeline.marker"),
        "preferred_languages": ("rust", "c"), "summary": "Неразрушающая работа с аудиофрагментами и временной шкалой.",
    },
    {
        "id": "translator", "name": "Переводчик",
        "aliases": ("переводчик", "перевод", "локализация", "translator", "translation", "translation workspace"),
        "domain": "language", "inputs": ("text.segment", "glossary.term"), "outputs": ("translation.segment", "glossary.term"),
        "preferred_languages": ("python",), "summary": "Перевод сегментов с контекстом и терминологией.",
    },
    {
        "id": "subtitle_export", "name": "Экспорт субтитров",
        "aliases": ("субтитры", "экспорт субтитров", "subtitle export", "subtitle_export", "srt", "vtt"),
        "domain": "media", "inputs": ("text.segment", "translation.segment", "timeline.marker"), "outputs": ("subtitle.file",),
        "preferred_languages": ("python",), "summary": "Экспорт синхронизированных субтитров SRT/VTT.",
    },
    {
        "id": "speech_to_text", "name": "Распознавание речи",
        "aliases": ("распознавание речи", "транскрибация", "speech to text", "stt", "speech_to_text"),
        "domain": "language", "inputs": ("audio.asset",), "outputs": ("text.segment",),
        "preferred_languages": ("python",), "summary": "Преобразование аудиозаписи в текст через подключаемый движок.",
    },
    {
        "id": "text_to_speech", "name": "Синтез речи",
        "aliases": ("синтез речи", "озвучка", "text to speech", "tts", "text_to_speech"),
        "domain": "audio", "inputs": ("text.segment",), "outputs": ("audio.asset",),
        "preferred_languages": ("python", "rust"), "summary": "Создание речи через выбранный TTS-провайдер.",
    },
    {
        "id": "glossary", "name": "Глоссарий",
        "aliases": ("глоссарий", "терминологический словарь", "словарь терминов", "glossary", "termbase"),
        "domain": "language", "inputs": ("text.document", "translation.segment"), "outputs": ("glossary.term",),
        "preferred_languages": ("python",), "summary": "Управление утверждёнными терминами и вариантами перевода.",
    },
    {
        "id": "notes", "name": "Заметки",
        "aliases": ("заметки", "блокнот", "notes", "notepad"),
        "domain": "productivity", "inputs": ("text.document",), "outputs": ("note.item",),
        "preferred_languages": (), "summary": "Быстрые заметки и аннотации проекта.",
    },
    {
        "id": "task_board", "name": "Доска задач",
        "aliases": ("доска задач", "задачи", "канбан", "task board", "kanban", "task_board"),
        "domain": "productivity", "inputs": ("note.item",), "outputs": ("task.item",),
        "preferred_languages": (), "summary": "Управление задачами и статусами выполнения.",
    },
    {
        "id": "calendar", "name": "Календарь",
        "aliases": ("календарь", "calendar", "schedule", "расписание"),
        "domain": "productivity", "inputs": ("task.item",), "outputs": ("calendar.event",),
        "preferred_languages": (), "summary": "Планирование событий и сроков.",
    },
    {
        "id": "spreadsheet", "name": "Таблицы",
        "aliases": ("таблицы", "электронные таблицы", "spreadsheet", "sheets"),
        "domain": "data", "inputs": ("data.record",), "outputs": ("data.table",),
        "preferred_languages": ("python",), "summary": "Редактирование и анализ табличных данных.",
    },
    {
        "id": "charts", "name": "Визуализация данных",
        "aliases": ("графики", "диаграммы", "визуализация данных", "charts", "data visualization"),
        "domain": "data", "inputs": ("data.table",), "outputs": ("chart.figure",),
        "preferred_languages": ("python",), "summary": "Построение графиков и визуальных отчётов.",
    },
    {
        "id": "code_editor", "name": "Редактор кода",
        "aliases": ("редактор кода", "кодовый редактор", "code editor", "code_editor", "ide"),
        "domain": "development", "inputs": ("source.file",), "outputs": ("source.file", "source.symbol"),
        "preferred_languages": (), "summary": "Редактирование исходного кода и навигация по проекту.",
    },
    {
        "id": "debugger", "name": "Отладчик",
        "aliases": ("отладчик", "debugger", "debug"),
        "domain": "development", "inputs": ("source.file", "runtime.event"), "outputs": ("debug.report",),
        "preferred_languages": (), "summary": "Диагностика и анализ выполнения программ.",
    },
    {
        "id": "build_pipeline", "name": "Сборочный конвейер",
        "aliases": ("сборка", "сборочный конвейер", "build pipeline", "build_pipeline", "сборщик"),
        "domain": "development", "inputs": ("source.file", "build.config"), "outputs": ("build.artifact", "test.report"),
        "preferred_languages": (), "summary": "Воспроизводимая сборка, тестирование и упаковка проекта.",
    },
    {
        "id": "file_manager", "name": "Файловый менеджер",
        "aliases": ("файловый менеджер", "файлы", "file manager", "file_manager"),
        "domain": "system", "inputs": ("filesystem.entry",), "outputs": ("filesystem.entry",),
        "preferred_languages": (), "summary": "Навигация и операции над файлами в разрешённой области.",
    },
    {
        "id": "search_index", "name": "Поисковый индекс",
        "aliases": ("поиск", "поисковый индекс", "search index", "search_index", "full text search"),
        "domain": "data", "inputs": ("data.record", "text.document"), "outputs": ("search.result",),
        "preferred_languages": ("python", "rust"), "summary": "Индексация и поиск по локальным данным.",
    },
    {
        "id": "version_control", "name": "Версионирование",
        "aliases": ("контроль версий", "версионирование", "version control", "git"),
        "domain": "development", "inputs": ("source.file",), "outputs": ("source.revision",),
        "preferred_languages": (), "summary": "История изменений и сравнение ревизий.",
    },
    {
        "id": "image_editor", "name": "Редактор изображений",
        "aliases": ("редактор изображений", "фоторедактор", "image editor", "image_editor"),
        "domain": "media", "inputs": ("image.asset",), "outputs": ("image.asset",),
        "preferred_languages": ("rust", "c"), "summary": "Редактирование растровых и векторных изображений.",
    },
    {
        "id": "video_editor", "name": "Видеоредактор",
        "aliases": ("видеоредактор", "редактор видео", "video editor", "video_editor"),
        "domain": "media", "inputs": ("video.asset", "audio.asset"), "outputs": ("video.asset", "timeline.marker"),
        "preferred_languages": ("rust", "c"), "summary": "Монтаж видео и синхронизация медиа дорожек.",
    },
    {
        "id": "presentation", "name": "Генератор презентаций",
        "aliases": ("презентации", "генератор презентаций", "presentation", "presentation generator"),
        "domain": "productivity", "inputs": ("text.document", "image.asset", "data.table"), "outputs": ("presentation.file",),
        "preferred_languages": ("python",), "summary": "Формирование презентаций из структурированного материала.",
    },
    {
        "id": "cloud_sync", "name": "Облачная синхронизация",
        "aliases": ("облачная синхронизация", "cloud sync", "cloud_sync", "облако"),
        "domain": "network", "inputs": ("project.snapshot",), "outputs": ("remote.snapshot",),
        "preferred_languages": ("python",), "summary": "Синхронизация с явно настроенным удалённым провайдером.",
    },
    {
        "id": "cloud_streaming", "name": "Только облачная обработка",
        "aliases": ("только облако", "облачный стриминг", "cloud streaming", "cloud_streaming"),
        "domain": "network", "inputs": ("remote.asset",), "outputs": ("remote.result",),
        "preferred_languages": ("python",), "summary": "Обязательная обработка удалённым сервисом.",
    },
    {
        "id": "offline_mode", "name": "Строго офлайн-режим",
        "aliases": ("строго офлайн", "офлайн режим", "offline mode", "offline_mode"),
        "domain": "quality", "inputs": (), "outputs": (),
        "preferred_languages": (), "summary": "Запрет сетевых зависимостей в runtime-профиле.",
    },
    {
        "id": "automation_rules", "name": "Правила автоматизации",
        "aliases": ("автоматизация", "правила автоматизации", "automation rules", "automation_rules", "if then"),
        "domain": "productivity", "inputs": ("system.event",), "outputs": ("automation.action",),
        "preferred_languages": (), "summary": "Декларативные правила событий и действий с ограничениями.",
    },
)

COMPONENTS = tuple(deepcopy(item) for item in _COMPONENTS)
COMPONENT_BY_ID = {item["id"]: item for item in COMPONENTS}

_ALIAS_TO_ID: dict[str, str] = {}
for _item in COMPONENTS:
    for _alias in (_item["id"], _item["name"], *_item["aliases"]):
        _key = " ".join(str(_alias).casefold().replace("_", " ").split())
        if _key in _ALIAS_TO_ID and _ALIAS_TO_ID[_key] != _item["id"]:
            raise RuntimeError(f"duplicate Jora component alias: {_key}")
        _ALIAS_TO_ID[_key] = _item["id"]


def normalize_alias(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").split())


def resolve_component(value: str) -> dict | None:
    component_id = _ALIAS_TO_ID.get(normalize_alias(value))
    return deepcopy(COMPONENT_BY_ID[component_id]) if component_id else None


def component_suggestions(value: str, *, limit: int = 5) -> list[str]:
    from difflib import get_close_matches

    key = normalize_alias(value)
    matches = get_close_matches(key, _ALIAS_TO_ID.keys(), n=limit, cutoff=0.48)
    return list(dict.fromkeys(_ALIAS_TO_ID[item] for item in matches))
