# DuckOS

**DuckOS 0.1.0-rc.1** — первая собираемая поставка пользовательской оболочки, системных утилит и федерации приложений Ivan-VHS.

DuckOS задуман как самостоятельная рабочая среда: тёмная стеклянная оболочка с быстрым поиском, окнами, доком, уведомлениями и панелью ресурсов. Визуальное направление собрано по двум предоставленным референсам: компактная продуктивная ОС с холодным сине-голубым свечением и отдельный спокойный HUD-помощник Duck.

> **Честный статус релиза.** Это release candidate пользовательского слоя и набора CLI-инструментов, а не готовое ядро, загрузчик или установочный ISO. Shell открывается в браузере; системные команды работают в пользовательском пространстве Linux. Реальная телеметрия и привилегированные операции не подменяются демонстрационными данными.

## Что уже входит

- **DuckOS Shell** — адаптивный рабочий стол с окнами-приложениями, доком, палитрой команд, быстрыми настройками, уведомлениями, переключением темы и Reduce Motion.
- **DuckOS Tools** — Python 3.10+ CLI без сторонних runtime-зависимостей. В наборе: монитор CPU/RAM/swap/interrupts, просмотр FD по PID, mmap benchmark с page faults, сравнение деревьев каталогов, безопасный дамп process environment, поиск дисковых hotspots, аудит mount flags, карта OOM scores, анализ IRQ, clock jitter, entropy gauge, snapshot системы, атомарная запись, поиск проблемных symlink, гистограмма возраста файлов и probe размера страницы.
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

## Текущее ограничение

В этой версии ещё нет собственного kernel, bootloader, initramfs, Wayland compositor, package manager, драйверного ABI, аппаратного GPU-ускорения оболочки, sandbox для AI-агента или установочного образа. Они описаны как отдельные будущие подсистемы, а не заявлены как готовая функциональность.

См. архитектуру, матрицу функций, безопасность и дорожную карту в каталоге docs.
