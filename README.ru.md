# Duck — проект операционной системы с приоритетом Reaper

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/DAK/actions/workflows/ci.yml) [![Boot image](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/boot-image.yml?branch=main&label=Boot%20image)](https://github.com/Ivan-VHS/DAK/actions/workflows/boot-image.yml) [![Native desktop](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/native-mora.yml?branch=main&label=Native%20desktop)](https://github.com/Ivan-VHS/DAK/actions/workflows/native-mora.yml)

> Экспериментальная системная основа x86_64: загрузка Stage 1, проверенная в QEMU, policy-контракты Reaper и отдельная нативная desktop-оболочка хостовой ОС.

**Сведения о проекте:** экспериментальная разработка · основа загрузки Stage 1 · x86_64 / Limine BIOS+UEFI · архитектурное направление Reaper-first · host shell C++17 / необязательный Qt 6 Widgets 6.4+ · единая версия ОС не объявлена · **Документация проверена:** 2026-11-27 UTC

<p align="center"><img src="assets/readme/duckos-overview.svg" alt="Обзор архитектуры Duck и host desktop" width="100%"></p>

## Назначение и границы

Duck — экспериментальный проект операционной системы, а не готовая устанавливаемая desktop-ОС. Необходимо различать три самостоятельные поверхности выполнения:

1. **Ядро Stage 1:** freestanding-основа x86_64, которая проверяет handoff Limine и Boot Info v1, выполняет раннее выделение физического кадра, выводит маркер загрузки и останавливается.
2. **Policy-ветка Reaper:** эталонные контракты подсистем и исполняемые policy-тесты. Нативное enforcement ядром и freestanding-компилятор/backend Reaper пока не поставляются.
3. **Host desktop:** отдельное приложение C++17 / Qt 6 Widgets, окна которого принадлежат хостовой ОС. Ядро Stage 1 его не запускает.

Текущий загрузочный bridge — узкая freestanding-граница на C11. Reaper остаётся целевым первоклассным языком и policy-слоем; успешная проверка в reference runtime не доказывает наличие нативного компилятора, привилегий ядра или доступа к оборудованию.

## Текущее состояние реализации

### Загрузка и основа ядра

- x86_64 Stage 1 использует закреплённый путь Limine v12.11.1 для BIOS/UEFI и проверяет Boot Info v1.
- Ранний physical-frame allocator выбирает проверенные доступные области памяти, выделяет и очищает один кадр 4 KiB через HHDM, затем выводит `DUCKOS_BOOT_OK stage=1`.
- Основа обработки исключений включает IDT vectors 0–31, нормализованные assembly stubs и фатальную диагностику через serial/framebuffer. Maskable interrupts не включены.
- Структуры GDT/TSS/IST для bootstrap и host contract tests присутствуют; per-CPU setup, запуск дополнительных процессоров и полная интеграция прерываний/runtime остаются незавершёнными.
- Reaper предоставляет 40 эталонных контрактов Core Subsystem MVP. Нативное применение политик ядром ожидается.

Загрузочный образ прошёл Stage 1 проверки QEMU BIOS и UEFI. После этого ядро пока останавливается, не запуская процесс или пользовательский сеанс.

### Нативная desktop-оболочка хоста

- Необязательное приложение C++17 использует Qt 6 Widgets 6.4+ и создаёт реальные top-level окна, которыми управляет хостовая ОС.
- Локальный каталог служит для обнаружения приложений; нативный launcher не исполняет строки команд из manifest и не выдаёт аппаратные привилегии.
- Текущие поверхности включают локальное сохранение черновиков, просмотр выбранной пользователем папки только для чтения и визуальную панель waveform VentuSample. Waveform-панель не воспроизводит звук и не вызывает DSP VentuSample.
- Браузерное preview [`desktop/demo/index.html`](desktop/demo/index.html) — reference-прототип, а не compositor ядра и не реализация через WebView.

### Незавершённые слои ОС

| Область | Текущая граница |
|---|---|
| Память | Одно раннее выделение кадра; переиспользуемый allocator/free и page tables ожидаются |
| Прерывания | Только диагностика исключений; внешняя IRQ-маршрутизация и timer scheduling ожидаются |
| Процессы | Модель процессов, Ring 3 и syscall ABI ожидаются |
| Безопасность | Kernel-enforced capabilities и изолированная среда драйверов ожидаются |
| Хранилище и службы | Filesystem, package manager, init/service supervisor и installer ожидаются |
| Графика и устройства | Compositor ядра, GPU и audio stack ожидаются |

Пока нет полноценного scheduler, изоляции процессов, постоянного пользовательского сеанса, файловой системы, сетевого стека или загрузчика драйверов ядра. Policy-контракты и функции host-приложения не заменяют эти службы ОС.

## Сборка и проверка

Нативная сборка рассчитана на Linux x86_64. Необязательная host desktop-оболочка требует компилятор C++17 и Qt 6 Widgets 6.4+. Для release image дополнительно нужны Git/submodules, CMake, компиляторы C/C++, Python 3 как build tooling, Node.js 22, xorriso, curl, tar, QEMU и OVMF.

Сборка нативного desktop при наличии Qt:

~~~sh
cmake -S . -B build/dak-native -DCMAKE_BUILD_TYPE=Release -DDAK_BUILD_NATIVE_DESKTOP=ON
cmake --build build/dak-native --target dak_desktop_native --parallel
ctest --test-dir build/dak-native --output-on-failure
~~~

Запуск браузерного reference preview и его тестов:

~~~sh
./scripts/run-mora.sh
npm test
npm run validate:ecosystem
npm run test:ecosystem
~~~

Запуск preview в Windows PowerShell:

~~~powershell
.\scripts/run-mora.ps1
npm test
~~~

Сборка федеративного Stage 1 release image:

~~~sh
bash boot/build-release-iso.sh --work-dir build/release --output dist/Duck-Stage1-x86_64.iso
~~~

Release pipeline проверяет закреплённые исходники, собирает/тестирует host workbenches, упаковывает исходники и notices и записывает SHA-256 checksums. Полученный ISO — preview исходников и инструментов, а не полноценная устанавливаемая операционная система. Контрольная сумма не является подписью издателя.

## Экосистема и интерфейсы

Репозиторий подключает четыре независимых upstream-проекта в качестве submodules. Для инициализации используйте точно закреплённые ревизии:

~~~sh
git submodule update --init --recursive
~~~

- [Reaper](https://github.com/Ivan-VHS/Reaper) — язык, reference runtime и policy-контракты.
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) — инвентаризация процессора, ограниченные измерения и C ABI v1.
- [OPlague](https://github.com/Ivan-VHS/OPlague) — read-only-доказательства по устройствам/пакетам и версионированные telemetry snapshots.
- [VentuSample](https://github.com/Ivan-VHS/VentuSample) — offline-генерация аудио и версионированные sample packs.

Reaper использует Pytyliki C ABI v1 только через явно заданный путь к доверенной библиотеке и проверяет контракты OPlague snapshot/report для read-only-анализа. Адаптер policy для нормализованной GPU telemetry OPlague существует; доверенный native JSON ingestion и проверка provenance издателя/сборки ещё ожидаются. Потребитель VentuSample pack v1 пока только описан контрактом. Peer workbenches остаются user-space проектами: они не являются kernel modules и не запускаются Stage 1.

## Документация и границы доверия

- [Состояние реализации](docs/IMPLEMENTATION_STATUS.md) · [Индекс документации](docs/README.md)
- [Загрузочный образ Stage 1](docs/BOOTABLE_IMAGE.md) · [Обработка x86_64 исключений](docs/X86_64_EXCEPTION_HANDLING.md)
- [Контракты Core Subsystem MVP](docs/CORE_MVP_V1.md) · [Интеграция экосистемы](docs/ECOSYSTEM_INTEGRATION.md)
- [Архитектура desktop](docs/DAK_DESKTOP.md) · [Единый стандарт документации](docs/UNIFIED_DOCUMENTATION_STANDARD.md)
- [Лестница зрелости проекта](docs/PROJECT_EVOLUTION_LADDER.md) · [Инженерная дорожная карта](docs/IMPLEMENTATION_ROADMAP.md)

Не считайте reference policy, функцию host desktop или инициализированный submodule нативным enforcement ядра, интеграцией с ОС или доступом к оборудованию. Подключённые проекты сохраняют собственную историю, сопровождающих и upstream-лицензии. В корне репозитория сейчас нет файла `LICENSE`, поэтому условия распространения не объявлены; сторонние notices не предоставляют дополнительных прав.

---
<p align="center"><sub>Duck · репозиторий: Ivan-VHS/DAK · проверка README 2026-11-27 UTC</sub></p>
