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
)
_BY_ID = {item["id"]: item for item in PARAMETERS}
def _key(value: str) -> str:
    return re.sub(r"[^0-9a-zа-я]+", " ", value.casefold().replace("ё","е"), flags=re.IGNORECASE).strip()
_ALIASES: dict[str,str] = {}
for item in PARAMETERS:
    for alias in [item["id"], item["name"], item["name_en"], *item["aliases"]]:
        _ALIASES[_key(alias)] = item["id"]
def resolve_parameter(value: str) -> dict[str,Any] | None:
    key = _ALIASES.get(_key(value))
    return _BY_ID.get(key) if key else None
def catalog_payload() -> dict[str,Any]:
    return {"schema":SCHEMA,"version":1,"maturity":"seed_registry","parameters":[dict(item) for item in PARAMETERS],"limits":{"max_formula_chars":2048,"max_components":64},"note":"Seed registry. Full 666-variant taxonomy remains an importable catalogue expansion, not a completion claim."}
