# Архитектура DuckOS

## Слои

~~~text
┌─────────────────────────────────────────────────────────────┐
│ DuckOS Desktop Shell                                        │
│ windows · dock · search · quick settings · notifications    │
├─────────────────────────────────────────────────────────────┤
│ DuckOS Session / App Launcher                               │
│ app manifests · command dispatch · user preferences         │
├───────────────────────────┬─────────────────────────────────┤
│ DuckOS Tools               │ Ivan-VHS Federation             │
│ procfs · mmap · filesystem │ Pytyliki · Reaper · OPlague     │
│ diagnostics · safe writes │ VentuSample                     │
├───────────────────────────┴─────────────────────────────────┤
│ Host operating system: Linux first; Windows UI preview       │
├─────────────────────────────────────────────────────────────┤
│ Hardware: CPU · memory · storage · network · audio · GPU     │
└─────────────────────────────────────────────────────────────┘
~~~

## Контракт DuckOS

DuckOS владеет оболочкой, сессией, каталогом приложений, настройками интерфейса, CLI-инструментами общего назначения и форматом интеграционных манифестов. Он не дублирует внутренние реализации проектов федерации.

- CPU topology, memory lab и bounded processor measurement принадлежат Pytyliki.
- Язык, parser/compiler/runtime и code intelligence принадлежат Reaper.
- Device discovery и driver-package evidence принадлежат OPlague. Эта интеграция остаётся read-only.
- Audio generation и offline DSP принадлежат VentuSample. DuckOS не превращает системную оболочку в DAW.

В DuckOS допускается адаптер запуска или передачи файла, но не приватный импорт исходников подмодуля и не независимая копия его движка.

## Текущая реализация

Каталог desktop — автономный web UI preview. Он не имеет доступа к реальным ресурсам хоста; телеметрические значения помечены как demo. Это позволяет проверять визуальную систему без выдачи браузеру опасных полномочий.

Каталог tools — Python 3.10+ пользовательские CLI-команды. Linux-интеграции читают procfs/sysfs и возвращают понятную ошибку при отсутствии интерфейса. Команды не требуют root для обычного сценария и не поднимают привилегии сами.

Каталог federation — Git submodules с upstream commit pins. Исходники и лицензии остаются в своих репозиториях.

## Следующий архитектурный шаг

Для нативной сборки потребуется отдельный compositor/session manager, backend IPC, менеджер приложений, пакетная система и boot chain. Их нельзя безопасно заменить статической HTML-страницей или набором Python-команд. Каждый следующий слой должен получить отдельный API, threat model, тестовый стенд и измеряемый критерий готовности.
