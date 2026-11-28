# 🦆 DAK — операционная система с приоритетом Reaper

<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

> **Psychoporter 666** — точность архитектора × энергия исследователя × прослеживаемые доказательства. [Общий стандарт документации](https://github.com/Ivan-VHS/DAK/blob/main/docs/PSYCHOPORTER_DOCUMENTATION_STYLE_V1.md).  
> **Редакционная редакция · 2026-11-28:** обновлены подача и навигация; авторство, условия лицензий и сторонняя атрибуция сохранены.


[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/DAK/actions/workflows/ci.yml) [![Boot image](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/boot-image.yml?branch=main&label=Boot%20image)](https://github.com/Ivan-VHS/DAK/actions/workflows/boot-image.yml) [![Native DAK](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/native-mora.yml?branch=main&label=Native%20DAK)](https://github.com/Ivan-VHS/DAK/actions/workflows/native-mora.yml)

> **Системная основа с приоритетом Reaper, нативная desktop-оболочка хоста и локальная экосистема инструментов — с явными границами каждой подсистемы.**

**Состояние:** Экспериментальный проект · Stage 1 x86_64 проверен в QEMU · **Версия:** Stage 1 boot foundation · **Стандарт README:** Psychoporter 666 v1.1 · **Дата проверки:** 2026-11-25 UTC · **Source:** [Ivan-VHS/DAK](https://github.com/Ivan-VHS/DAK)

<p align="center"><img src="assets/readme/dak-overview.svg" alt="DAK system architecture overview" width="100%"></p>

## Быстрая навигация

[🚀 DAK Desktop HTML demo](desktop/demo/index.html) · [Documentation](docs/README.md) · [Source](https://github.com/Ivan-VHS/DAK) · [Issues](https://github.com/Ivan-VHS/DAK/issues)

## Назначение и границы

DAK — экспериментальный проект ОС с приоритетом Reaper. Текущая работа намеренно разделена на загрузочную основу ядра, policy-контракты Reaper и нативное desktop-приложение DAK для хостовой ОС.

## Возможности

- Путь x86_64 Stage 1 проверяет передачу управления от Limine и Boot Info v1, выделяет ранний кадр 4 KiB, выводит маркер успешного прохождения Stage 1 и останавливается. QEMU-проверки BIOS и UEFI проходят.
- Reaper предоставляет эталонное направление policy-контрактов, включая 40 контрактов Core Subsystem MVP. Нативное enforcement ядром ещё не реализовано.
- У DAK есть нативное хост-приложение Qt 6 Widgets с окнами под управлением хостовой ОС и локальным каталогом приложений. Stage 1 kernel его не запускает.
- desktop/demo/index.html сохранён как браузерное reference preview. Это не нативный compositor и не desktop ядра.

## DAK Desktop

- Нативная Qt 6 оболочка создаёт отдельные окна средствами хостовой ОС; она не является композитором ядра.
- Reaper-политики рабочего стола проверяют окна, геометрию, профили плотности и снимки сессии.
- [Интерактивное HTML-демо](desktop/demo/index.html) работает локально; значения ресурсов и устройств являются иллюстративными.
- Архитектура и инженерное направление: **Ivan-VHS**. Подробнее: [DAK Desktop](docs/DAK_DESKTOP.md).

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
  subgraph HOST["DAK host desktop — separate from kernel"]
    Q["Qt 6 Widgets"] --> W["Host-managed windows"]
    H["Browser reference preview"]
  end
  BOOT -.->|"desktop integration pending"| HOST
~~~

## Сборка нативной DAK

Сборка release-образа рассчитана на Linux x86_64 и требует Git/submodules, GCC/G++, CMake, Python 3 как инструмент сборки, Node.js 22, Qt 6 Widgets, xorriso, curl, tar, QEMU и OVMF.

~~~sh
cmake -S . -B build/dak-native -DCMAKE_BUILD_TYPE=Release -DDAK_BUILD_NATIVE_DESKTOP=ON
cmake --build build/dak-native --target dak_desktop_native --parallel
ctest --test-dir build/dak-native --output-on-failure
~~~

Цель Qt Desktop необязательна и пропускается, если Qt 6 Widgets не найден. DAK работает как нативное приложение хостовой ОС и не запускается ядром Stage 1.

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

Браузерная оболочка — демонстрационная поверхность. Она не является нативным композитором и не означает интеграцию с ядром.

## Сборка release-образа

~~~sh
bash boot/build-release-iso.sh --work-dir build/release --output dist/DAK-Release-x86_64.iso
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

Текущая стадия ядра останавливается после проверки handoff и раннего выделения кадра. Пока нет изоляции процессов, загрузки драйверов, хранилища, сети, постоянного сеанса или kernel-enforced sandboxing. Записи каталога DAK не исполняют команды манифестов и не выдают аппаратные привилегии.

## Архитектурные цели

x86_64 — основная цель для Intel и AMD. Эльбрус сохранён как отдельное направление совместимости; это не означает наличия backend компилятора, boot image или матрицы испытаний на физическом оборудовании.

## Федерация исходников и целостность

Активный набор исходников зафиксирован в `federation/repositories.v1.json`. Инициализируйте именно указанные ревизии командой:

~~~sh
git submodule update --init --recursive
~~~

Связанные проекты остаются отдельными репозиториями с собственными правообладателями, лицензиями, контрактами и циклами выпуска:

- [Reaper](https://github.com/Ivan-VHS/Reaper)
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki)
- [OPlague](https://github.com/Ivan-VHS/OPlague)
- [VentuSample](https://github.com/Ivan-VHS/VentuSample)

## Документация

- [Архитектура](docs/ARCHITECTURE.md)
- [Статус реализации](docs/IMPLEMENTATION_STATUS.md)
- [Загрузочный образ](docs/BOOTABLE_IMAGE.md)
- [MVP подсистем ядра](docs/CORE_MVP_V1.md)
- [Интеграция экосистемы](docs/ECOSYSTEM_INTEGRATION.md)
- [Шкала эволюции проекта](docs/PROJECT_EVOLUTION_LADDER.md)
- [Нативная интеграция Reaper](docs/REAPER_INTEGRATION.md)
- [Индекс документации](docs/README.md)

Реестр статуса реализации, руководство по загрузочному образу и шкала эволюции проекта являются основными источниками сведений о готовых и планируемых слоях системы.

## Лицензия и правовой статус

В корне репозитория нет файла LICENSE или декларации лицензии. Нельзя предполагать MIT, Apache-2.0 или право на распространение. Лицензия должна быть выбрана и одобрена правообладателем до распространения.

Не распространяйте включённые или сторонние материалы за пределами прав, предоставленных соответствующими лицензиями. Фиксация Git submodule указывает ревизию исходников, но не меняет правообладание и условия лицензирования.

## Инженерное правило

Описывайте поведение на основании исходников, тестов, схем, сборки и CI. Каталог или roadmap не доказывают реализацию. Настройки браузера — не kernel enforcement; анализ PE — не запуск процесса; checksum — не доказательство авторства.

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 UTC</sub></p>

## Участие в разработке

Перед изменением кода, контрактов или документации прочитайте [CONTRIBUTING.md](CONTRIBUTING.md). Сохраняйте изменения проверяемыми, запускайте соответствующие проверки и точно описывайте доказательства реализации.
