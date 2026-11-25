<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

<h1 align="center"><strong>🦆 Duck — операционная система с приоритетом Reaper</strong></h1>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/DAK/actions/workflows/ci.yml) [![Boot image](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/boot-image.yml?branch=main&label=Boot%20image)](https://github.com/Ivan-VHS/DAK/actions/workflows/boot-image.yml) [![Native Mora](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/native-mora.yml?branch=main&label=Native%20Mora)](https://github.com/Ivan-VHS/DAK/actions/workflows/native-mora.yml)

> **Системная основа с приоритетом Reaper, нативная desktop-оболочка хоста и локальная экосистема инструментов — с явными границами каждой подсистемы.**

**Состояние:** Экспериментальный проект · Stage 1 x86_64 проверен в QEMU · **Версия:** Stage 1 boot foundation · **Стандарт README:** Psychoporter 666 v1.0 · **Дата проверки:** 2026-11-25 UTC · **Source:** [Ivan-VHS/DAK](https://github.com/Ivan-VHS/DAK)

<p align="center"><img src="assets/readme/duckos-overview.svg" alt="Duck system architecture overview" width="100%"></p>

## Быстрая навигация

[🚀 Demo: Browser reference preview](mora/index.html) · [Documentation](docs/README.md) · [Source](https://github.com/Ivan-VHS/DAK) · [Issues](https://github.com/Ivan-VHS/DAK/issues)

## Назначение и границы

Duck — экспериментальный проект ОС с приоритетом Reaper. Текущая работа намеренно разделена на загрузочную основу ядра, policy-контракты Reaper и нативное desktop-приложение Mora для хостовой ОС.

## Возможности

- Путь x86_64 Stage 1 проверяет передачу управления от Limine и Boot Info v1, выделяет ранний кадр 4 KiB, выводит DUCKOS_BOOT_OK stage=1 и останавливается. QEMU-проверки BIOS и UEFI проходят.
- Reaper предоставляет эталонное направление policy-контрактов, включая 40 контрактов Core Subsystem MVP. Нативное enforcement ядром ещё не реализовано.
- У Mora есть нативное хост-приложение Qt 6 Widgets с окнами под управлением хостовой ОС и локальным каталогом приложений. Stage 1 kernel его не запускает.
- mora/index.html сохранён как браузерное reference preview. Это не нативный compositor и не desktop ядра.

## Карта системы

~~~mermaid
flowchart TB
  subgraph BOOT["x86_64 Stage 1 — QEMU verified"]
    L["Limine handoff"] --> B["Boot Info v1"]
    B --> F["Early 4 KiB frame"]
    F --> M["Serial marker / halt"]
  end
  subgraph POLICY["Reaper policy contracts"]
    R["Reference contracts"] --> T["Contract tests"]
    T -.-> N["Native enforcement pending"]
  end
  subgraph HOST["Mora host desktop — separate from kernel"]
    Q["Qt 6 Widgets"] --> W["Host-managed windows"]
    H["Browser reference preview"]
  end
  BOOT -.->|"desktop integration pending"| HOST
~~~

## Сборка нативной Mora

Сборка release-образа рассчитана на Linux x86_64 и требует Git/submodules, GCC/G++, CMake, Python 3 как инструмент сборки, Node.js 22, Qt 6 Widgets, xorriso, curl, tar, QEMU и OVMF.

~~~sh
cmake -S . -B build/mora-native -DCMAKE_BUILD_TYPE=Release -DDUCKOS_BUILD_NATIVE_MORA=ON
cmake --build build/mora-native --target duckos_mora_native --parallel
ctest --test-dir build/mora-native --output-on-failure
~~~

The Qt desktop target is optional and is skipped when Qt 6 Widgets is not found. Mora runs as a host-native application; it is not started by the Stage 1 kernel.

## Браузерное reference preview

Linux:
~~~sh
./scripts/run-mora.sh
npm test
~~~
Windows PowerShell:
~~~powershell
.\scripts\run-mora.ps1
npm test
~~~

The browser shell is a reference surface. It is not a native compositor and does not imply kernel integration.

## Сборка release-образа

~~~sh
bash boot/build-release-iso.sh --work-dir build/release --output dist/Duck-Release-x86_64.iso
~~~

Release-конвейер проверяет pins репозиториев, запускает сборки и тесты проектов, создаёт SHA-256 inventory и собирает гибридный BIOS/UEFI ISO. ISO — preview исходников и инструментов, а не полноценная устанавливаемая ОС.

## Состояние ядра и следующие слои

| Layer | Status |
|---|---|
| Limine handoff и Boot Info v1 | Реализовано; проверено в QEMU |
| Раннее выделение физических кадров | Реализовано для Stage 1 |
| Reaper Core Subsystem MVP | 40 reference-контрактов; native enforcement ожидается |
| Page tables и адресные пространства | Ожидается |
| Interrupts, timers и preemptive scheduler | Ожидается |
| Модель процессов и syscall ABI | Ожидается |
| Kernel-enforced capabilities и zero-copy IPC | Ожидается |
| PCI/USB/ACPI и изолированная среда драйверов | Ожидается |
| Файловая система, supervisor, installer и постоянный сеанс | Ожидается |
| Native compositor, GPU и audio stack | Ожидается |

Текущая стадия ядра останавливается после проверки handoff и раннего выделения кадра. Пока нет изоляции процессов, загрузки драйверов, хранилища, сети, постоянного сеанса или kernel-enforced sandboxing. Записи каталога Mora не исполняют команды манифестов и не выдают аппаратные привилегии.

## Архитектурные цели

x86_64 — основная цель для Intel и AMD. Эльбрус сохранён как отдельное направление совместимости; это не означает наличия backend компилятора, boot image или матрицы испытаний на физическом оборудовании.

## Федерация исходников и целостность

The active source set is pinned in federation/repositories.v1.json. Initialize the exact recorded revisions with:

~~~sh
git submodule update --init --recursive
~~~

The peer projects remain separate repositories with independent ownership, licenses, contracts and release cycles:

- [Reaper](https://github.com/Ivan-VHS/Reaper)
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki)
- [OPlague](https://github.com/Ivan-VHS/OPlague)
- [VentuSample](https://github.com/Ivan-VHS/VentuSample)

## Документация

- [Architecture](docs/ARCHITECTURE.md)
- [Implementation status](docs/IMPLEMENTATION_STATUS.md)
- [Bootable image](docs/BOOTABLE_IMAGE.md)
- [Core subsystem MVP](docs/CORE_MVP_V1.md)
- [Ecosystem integration](docs/ECOSYSTEM_INTEGRATION.md)
- [Project evolution ladder](docs/PROJECT_EVOLUTION_LADDER.md)
- [Native Reaper integration](docs/REAPER_INTEGRATION.md)
- [Documentation index](docs/README.md)

The implementation-status ledger, bootable-image guide and project evolution ladder are the authoritative records for delivered and pending system layers.

## Лицензия и правовой статус

В корне репозитория нет файла LICENSE или декларации лицензии. Нельзя предполагать MIT, Apache-2.0 или право на распространение. Лицензия должна быть выбрана и одобрена правообладателем до распространения.

Do not redistribute bundled or third-party materials outside the applicable license grants. A Git submodule pin records a source revision; it does not change ownership or license terms.

## Инженерное правило

Описывайте поведение на основании исходников, тестов, схем, сборки и CI. Каталог или roadmap не доказывают реализацию. Настройки браузера — не kernel enforcement; анализ PE — не запуск процесса; checksum — не доказательство авторства.

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 UTC</sub></p>