# DuckOS

**DuckOS 0.1.0-rc.1** — первая собираемая поставка пользовательской оболочки, системных утилит и федерации приложений Ivan-VHS.

DuckOS задуман как самостоятельная рабочая среда: тёмная стеклянная оболочка с быстрым поиском, окнами, доком, уведомлениями и панелью ресурсов. Визуальное направление собрано по двум предоставленным референсам: компактная продуктивная ОС с холодным сине-голубым свечением и отдельный спокойный HUD-помощник Duck.

> **Честный статус релиза.** Это release candidate пользовательского слоя и набора CLI-инструментов, а не готовое ядро, загрузчик или установочный ISO. Shell открывается в браузере; системные команды работают в пользовательском пространстве Linux. Реальная телеметрия и привилегированные операции не подменяются демонстрационными данными.

## Что уже входит

- **DuckOS Shell** — адаптивный рабочий стол с окнами-приложениями, доком, палитрой команд, быстрыми настройками, уведомлениями, переключением темы и Reduce Motion.
- **DuckOS Tools** — Python 3.10+ CLI без сторонних runtime-зависимостей. В наборе: монитор CPU/RAM/swap/interrupts, просмотр FD по PID, mmap benchmark с page faults, сравнение деревьев каталогов, безопасный дамп process environment, поиск дисковых hotspots, аудит mount flags, карта OOM scores, анализ IRQ, clock jitter, entropy gauge, snapshot системы, атомарная запись, поиск проблемных symlink, гистограмма возраста файлов и probe размера страницы.
- **Core Services** — Cockos (PipeWire audio routing), Kavun (window geometry), Ka-bon (contextual shortcuts), Gloverty (themes and contrast), Po (safe command registry), Illidia (session snapshots), Unify (profiles and event bus) и Newsroom (актуальная новостная лента RSS/Atom). Это пользовательский сервисный слой, а не модули freestanding-ядра.
- **Federation** — Pytyliki, Reaper, OPlague и VentuSample подключаются как Git submodules. История, лицензия и собственная сборка каждого проекта остаются на месте.
- **Release hygiene** — CI, тесты базовых операций, схема федерации, архитектурные и security-заметки.

## Быстрый запуск

~~~bash
git clone --recurse-submodules https://github.com/Ivan-VHS/DuckOS.git
cd DuckOS

python -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

python -m pip install -e ./tools
duckos --help
~~~

Открыть графическую оболочку без backend:

~~~bash
python -m http.server 4173 --directory desktop
~~~

Затем откройте http://127.0.0.1:4173. Статус CPU/GPU/RAM/SSD в браузерной демонстрации помечен как **demo**: оболочка не выдаёт синтетические графики за показания компьютера.

Запуск тестов:

~~~bash
python -m unittest discover -s tools/tests -v
make -C native services-test
~~~

## Репозитории внутри DuckOS

| Подмодуль | Роль в системе |
|---|---|
| federation/Pytyliki | CPU, память, ограниченные измерения и процессорная диагностика |
| federation/Reaper | язык Reaper, runtime, компиляторные и developer-инструменты |
| federation/OPlague | read-only инвентаризация устройств и анализ метаданных драйверов |
| federation/VentuSample | локальная генерация аудио и офлайн-DSP |

При обычном git clone подмодули не загружаются автоматически. Используйте --recurse-submodules или выполните git submodule update --init --recursive.

Подмодули не копируются в исходники DuckOS и не переписывают границы проектов. DuckOS отвечает за оболочку, запуск интеграций и собственные системные инструменты.

## Команды

~~~text
duckos sysmon-pulse [--interval 1] [--once]
duckos fd-watch PID [--kind all|file|socket|pipe] [--interval 1]
duckos inotify-exec DIRECTORY [--pattern GLOB] -- COMMAND [ARGS...]
duckos proc-env-dump PID
duckos mount-audit
duckos oom-score-map
duckos irq-balance-check
duckos clock-jitter [--samples 1000] [--period-ms 1]
duckos entropy-gauge
duckos sysinfo-snapshot [--output FILE]
duckos page-size-probe
duckos mmap-bench FILE [--size-mib N]
duckos dir-tree-diff LEFT RIGHT [--json]
duckos disk-hotspots DIRECTORY [--limit 20]
duckos atomic-write FILE TEXT
duckos symlink-loop-find DIRECTORY
duckos file-age-hist DIRECTORY
~~~

Некоторые команды читают Linux /proc, /sys и /proc/self/mountinfo; вне Linux они сообщат о неподдерживаемом источнике вместо выдуманных данных. Обычные команды работают без root. Для чтения чужого процесса ядро может потребовать дополнительных прав.

## Принципы DuckOS

1. **Сначала наблюдение.** Инвентаризация и диагностика по умолчанию read-only.
2. **Никакой магии с правами.** DuckOS не включает root-режим автоматически и не запускает shell-команды через shell=True.
3. **Понятные границы.** Демонстрационная оболочка, native backend, ядро и драйверы — разные уровни готовности.
4. **Свой код — человеческий.** Небольшие функции, понятные имена, явная обработка ошибок, минимум абстракций ради абстракций.
5. **Свои лицензии остаются своими.** Каждый federation submodule сохраняет исходный LICENSE; корневые файлы DuckOS лицензированы отдельно.

## Native platform bring-up

Ветка work/native-os-foundation добавляет отдельный нативный контур DuckOS поверх пользовательской оболочки и Linux-инструментов. Исходники и инструкции находятся в каталоге [native](https://github.com/Ivan-VHS/DuckOS/tree/work/native-os-foundation/native).

| Подсистема | Реализовано в этой ветке | Что ещё не готово |
|---|---|---|
| Kernel / Limine | Freestanding x86-64 ELF, ранняя serial-консоль, карта памяти, framebuffer, обнаружение и проверка initramfs | Аллокаторы, IDT/APIC, прерывания, процессы, планировщик, VFS и драйверы |
| Boot / initramfs | Конфигурация Limine, newc CPIO-сборщик, ранний init и валидация архива | Распаковка в RAM и запуск PID 1 ядром |
| Wayland | wlroots compositor bring-up и отдельный EGL/GLES shell-клиент с опросом GL_RENDERER | Input seat, фокус, полная логика оболочки и GPU-драйверы собственного kernel |
| Packages / driver ABI | Локальный SHA-256-проверяющий пакетный store и версия ABI 1.0 | Подписанные репозитории, зависимости, модульный загрузчик и kernel device model |
| AI sandbox | Linux-обёртка Bubblewrap с отдельными namespace и лимитами | Собственный syscall policy и изоляция на уровне DuckOS kernel |
| ISO | Скрипт подготовки BIOS/UEFI boot-test image | Установщик разделов, recovery/rollback и проверенный desktop boot |
| Core Services | Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify user-space prototypes | Binding to compositor/seat, shared theme provider and authenticated IPC |

Это ранняя нативная bring-up ветка, а не готовая ОС для повседневной установки. GPU-ускорение через Mesa/wlroots доступно только при запуске compositor на подходящем Linux-хосте; собственный kernel DuckOS пока не содержит DRM/GPU-драйверов. Подробные границы реализации и следующие инженерные этапы описаны в [native/README.md](https://github.com/Ivan-VHS/DuckOS/blob/work/native-os-foundation/native/README.md).

Core Services CLI: `PYTHONPATH=native/services python -m duckos_services status`. Подробности и ограничения: [docs/CORE_SERVICES.md](docs/CORE_SERVICES.md).

Базовая сборка (Linux x86-64, Clang/LLD):

~~~bash
make -C native kernel initramfs test
~~~

Сборка Wayland compositor требует wlroots 0.18 и Wayland development headers. ISO требует Limine BIOS/UEFI assets, xorriso и Limine host utility; см. [инструкцию](https://github.com/Ivan-VHS/DuckOS/blob/work/native-os-foundation/native/README.md).

## Newsroom — «Вечерний курьер»

Newsroom собирает бесплатные публичные RSS/Atom-ленты BBC News Україна, The Kyiv Independent и BBC News World. Служба обновляет источники при запуске и затем каждые пять минут, сохраняет последний успешный кэш и показывает ссылки на оригинальные публикации. Запуск, API, ограничения и тесты описаны в [docs/NEWSROOM.md](docs/NEWSROOM.md).
