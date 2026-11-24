"""Versioned seed catalogue for Jora formula components."""
from __future__ import annotations
import re
from typing import Any

SCHEMA = "jora.parameter-registry.v1"
PARAMETERS: tuple[dict[str, Any], ...] = (
    {"id":"text_editor","name":"Текстовый редактор","name_en":"Text editor","aliases":["текст","редактор текста","text","text editor","document editor","markdown editor"],"domain":"text","description":"Документы, сегменты, заметки и структурированный текст.","preferred_languages":["reaper","python"],"variants":["plain text","markdown","многоязычный текст","субтитры","техническая документация","сценарии и диалоги"]},
    {"id":"audio_editor","name":"Аудиоредактор","name_en":"Audio editor","aliases":["аудио","звук","редактор звука","sound editor","audio editor","wave editor"],"domain":"media","description":"Аудиодорожки, маркеры, временные сегменты и экспорт аудио.","preferred_languages":["reaper","rust","python"],"variants":["многодорожечный звук","запись подкастов","дубляж","шумоподавление","таймкоды","аудиоанализатор"]},
    {"id":"translator","name":"Переводчик","name_en":"Translator","aliases":["перевод","локализация","translate","translator","localization"],"domain":"language","description":"Перевод сегментов, глоссарии и память переводов.","preferred_languages":["reaper","python"],"variants":["глоссарий","память переводов","перевод субтитров","дубляжный перевод","многоязычная локализация","терминология"]},
    {"id":"subtitles","name":"Субтитры","name_en":"Subtitles","aliases":["субтитры","captions","subtitle editor","srt","vtt"],"domain":"language","description":"Создание, тайминг, проверка и экспорт субтитров.","preferred_languages":["reaper","python"],"variants":["SRT","WebVTT","ASS/SSA","SDH"]},
    {"id":"notes","name":"Заметки","name_en":"Notes","aliases":["заметки","note taking","notes","memo"],"domain":"productivity","description":"Быстрые записи, теги и связанные заметки.","preferred_languages":["reaper"],"variants":["быстрые заметки","связанные заметки","дневник"]},
    {"id":"task_board","name":"Доска задач","name_en":"Task board","aliases":["задачи","канбан","task board","kanban","todo"],"domain":"productivity","description":"Статусы задач, списки и приоритеты.","preferred_languages":["reaper"],"variants":["канбан","список задач","доска проекта"]},
    {"id":"calendar","name":"Календарь","name_en":"Calendar","aliases":["календарь","calendar","schedule"],"domain":"productivity","description":"События и временные планы.","preferred_languages":["reaper"],"variants":["планировщик","календарь проекта"]},
    {"id":"offline_mode","name":"Офлайн-режим","name_en":"Offline mode","aliases":["офлайн","без интернета","offline","offline mode"],"domain":"runtime","description":"Локальное хранение и работа без сетевого соединения.","preferred_languages":["reaper"],"conflicts":["cloud_translation"],"variants":["локальное хранилище","без сети"]},
    {"id":"cloud_translation","name":"Облачный перевод","name_en":"Cloud translation","aliases":["облачный перевод","cloud translation","online translation"],"domain":"language","description":"Адаптеры удалённых переводческих служб.","preferred_languages":["reaper","python"],"conflicts":["offline_mode"],"variants":["удалённый перевод","API перевода"]},
    {"id":"text_to_speech","name":"Синтез речи","name_en":"Text to speech","aliases":["озвучка текста","синтез речи","text to speech","tts"],"domain":"audio","description":"Генерация речи из текста через подключаемый голосовой движок.","preferred_languages":["reaper","python","rust"],"variants":["голосовые профили","пакетная озвучка","экспорт речи"]},
    {"id":"speech_to_text","name":"Распознавание речи","name_en":"Speech to text","aliases":["распознавание речи","транскрибация","speech to text","stt","transcription"],"domain":"audio","description":"Преобразование аудиосегментов в текст.","preferred_languages":["reaper","python","rust"],"variants":["транскрипция интервью","разметка спикеров","распознавание субтитров"]},
    {"id":"code_editor","name":"Редактор кода","name_en":"Code editor","aliases":["код","редактор кода","code editor","IDE"],"domain":"development","description":"Редактирование исходников, диагностика и структура проектов.","preferred_languages":["reaper","rust","python"],"variants":["подсветка синтаксиса","отладка","проектные шаблоны"]},
    {"id":"spreadsheet","name":"Таблицы","name_en":"Spreadsheet","aliases":["таблица","таблицы","электронные таблицы","spreadsheet","sheet"],"domain":"data","description":"Табличные данные, формулы и фильтрация записей.","preferred_languages":["reaper","python"],"variants":["CSV","сводные таблицы","формулы"]},
    {"id":"image_editor","name":"Редактор изображений","name_en":"Image editor","aliases":["изображения","редактор изображений","image editor","photo editor"],"domain":"visual","description":"Растровые изображения, слои и экспорт графики.","preferred_languages":["reaper","rust","python"],"variants":["слои","маски","пакетный экспорт"]},
    {"id":"video_editor","name":"Видеоредактор","name_en":"Video editor","aliases":["видео","редактор видео","video editor"],"domain":"video","description":"Видеоклипы, монтажные последовательности и таймкоды.","preferred_languages":["reaper","rust","python"],"variants":["монтаж","таймлайн","экспорт видео"]},
    {"id":"presentation","name":"Презентации","name_en":"Presentation","aliases":["презентация","презентации","presentation","slides"],"domain":"documents","description":"Слайды, заметки докладчика и экспорт презентаций.","preferred_languages":["reaper","python"],"variants":["слайды","шаблоны","экспорт PDF"]},
    {"id":"file_manager","name":"Файловый менеджер","name_en":"File manager","aliases":["файлы","файловый менеджер","file manager","file browser"],"domain":"system","description":"Навигация, метаданные и операции над пользовательскими файлами.","preferred_languages":["reaper","rust"],"variants":["поиск файлов","метаданные","избранные каталоги"]},
    {"id":"api_client","name":"API-клиент","name_en":"API client","aliases":["api","api клиент","api client","http client"],"domain":"network","description":"Работа с HTTP API, запросами, схемами и ответами.","preferred_languages":["reaper","python","go"],"variants":["REST","GraphQL","коллекции запросов"]},
    {"id":"automation","name":"Автоматизация","name_en":"Automation","aliases":["автоматизация","automation","workflow automation"],"domain":"automation","description":"Триггеры, правила, события и автоматические действия.","preferred_languages":["reaper","python"],"variants":["сценарии","триггеры","планировщик действий"]},
    {"id":"data_visualizer","name":"Визуализация данных","name_en":"Data visualizer","aliases":["визуализация данных","графики","data visualizer","charts"],"domain":"analytics","description":"Графики, агрегаты и интерактивное представление данных.","preferred_languages":["reaper","python","typescript"],"variants":["диаграммы","дашборды","сравнение рядов"]},
    {"id":"database_manager","name":"Менеджер баз данных","name_en":"Database manager","aliases":["база данных","менеджер баз данных","database manager","database"],"domain":"data","description":"Схемы, запросы, миграции и просмотр записей.","preferred_languages":["reaper","rust","python"],"variants":["SQLite","миграции","просмотр схемы"]},
)
_BY_ID = {item["id"]: item for item in PARAMETERS}

def _key(value: str) -> str:
    return re.sub(r"[^0-9a-zа-я]+", " ", value.casefold().replace("ё", "е"), flags=re.IGNORECASE).strip()

_ALIASES: dict[str, str] = {}
for item in PARAMETERS:
    for alias in [item["id"], item["name"], item["name_en"], *item["aliases"]]:
        _ALIASES[_key(alias)] = item["id"]

def resolve_parameter(value: str) -> dict[str, Any] | None:
    parameter_id = _ALIASES.get(_key(value))
    return _BY_ID.get(parameter_id) if parameter_id else None

def catalog_payload() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "version": 1,
        "maturity": "seed_registry",
        "parameters": [dict(item) for item in PARAMETERS],
        "limits": {"max_formula_chars": 2048, "max_components": 64},
        "note": "Executable seed registry with 21 canonical capability parameters. The extended 666-variant source taxonomy remains a separately versioned import.",
    }
