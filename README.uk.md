<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

<h1 align="center"><strong>🦆 Duck — операційна система з пріоритетом Reaper</strong></h1>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/DAK/actions/workflows/ci.yml) [![Boot image](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/boot-image.yml?branch=main&label=Boot%20image)](https://github.com/Ivan-VHS/DAK/actions/workflows/boot-image.yml) [![Native Mora](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/native-mora.yml?branch=main&label=Native%20Mora)](https://github.com/Ivan-VHS/DAK/actions/workflows/native-mora.yml)

> **Системна основа з пріоритетом Reaper, нативна desktop-оболонка хоста й локальна екосистема інструментів — із явними межами кожної підсистеми.**

**Стан:** Експериментальний проєкт · Stage 1 x86_64 перевірено в QEMU · **Версія:** Stage 1 boot foundation · **Стандарт README:** Psychoporter 666 v1.0 · **Дата перевірки:** 2026-11-25 UTC · **Source:** [Ivan-VHS/DAK](https://github.com/Ivan-VHS/DAK)

<p align="center"><img src="assets/readme/duckos-overview.svg" alt="Duck system architecture overview" width="100%"></p>

## Швидка навігація

[🚀 Demo: Browser reference preview](mora/index.html) · [Documentation](docs/README.md) · [Source](https://github.com/Ivan-VHS/DAK) · [Issues](https://github.com/Ivan-VHS/DAK/issues)

## Призначення та межі

Duck — експериментальний проєкт ОС із пріоритетом Reaper. Поточну роботу навмисно розділено на завантажувальну основу ядра, policy-контракти Reaper і нативний desktop-застосунок Mora для хостової ОС.

## Можливості

- Шлях x86_64 Stage 1 перевіряє передавання керування від Limine та Boot Info v1, виділяє ранній кадр 4 KiB, виводить DUCKOS_BOOT_OK stage=1 і зупиняється. QEMU-перевірки BIOS та UEFI проходять.
- Reaper надає еталонний напрям policy-контрактів, зокрема 40 контрактів Core Subsystem MVP. Нативне enforcement ядром ще не реалізовано.
- Mora має нативний host-застосунок Qt 6 Widgets із вікнами під керуванням хостової ОС та локальним каталогом застосунків. Stage 1 kernel його не запускає.
- mora/index.html збережено як браузерне reference preview. Це не нативний compositor і не desktop ядра.

## Мапа системи

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

## Збирання нативної Mora

Збирання release-образу орієнтоване на Linux x86_64 і потребує Git із submodules, GCC/G++, CMake, Python 3 як інструмент збирання, Node.js 22, Qt 6 Widgets, xorriso, curl, tar, QEMU та OVMF.

~~~sh
cmake -S . -B build/mora-native -DCMAKE_BUILD_TYPE=Release -DDUCKOS_BUILD_NATIVE_MORA=ON
cmake --build build/mora-native --target duckos_mora_native --parallel
ctest --test-dir build/mora-native --output-on-failure
~~~

The Qt desktop target is optional and is skipped when Qt 6 Widgets is not found. Mora runs as a host-native application; it is not started by the Stage 1 kernel.

## Браузерне reference preview

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

## Збирання release-образу

~~~sh
bash boot/build-release-iso.sh --work-dir build/release --output dist/Duck-Release-x86_64.iso
~~~

Release-конвеєр перевіряє pins репозиторіїв, запускає збирання й тести проєктів, створює SHA-256 inventory та збирає гібридний BIOS/UEFI ISO. ISO — preview вихідного коду й інструментів, а не повноцінна встановлювана ОС.

## Стан ядра та наступні шари

| Layer | Status |
|---|---|
| Limine handoff і Boot Info v1 | Реалізовано; перевірено в QEMU |
| Раннє виділення фізичних кадрів | Реалізовано для Stage 1 |
| Reaper Core Subsystem MVP | 40 reference-контрактів; native enforcement очікується |
| Page tables та адресні простори | Очікується |
| Interrupts, timers і preemptive scheduler | Очікується |
| Модель процесів і syscall ABI | Очікується |
| Kernel-enforced capabilities і zero-copy IPC | Очікується |
| PCI/USB/ACPI та ізольоване середовище драйверів | Очікується |
| Файлова система, supervisor, installer і постійний сеанс | Очікується |
| Native compositor, GPU та audio stack | Очікується |

Поточна стадія ядра зупиняється після перевірки handoff і раннього виділення кадру. Поки немає ізоляції процесів, завантаження драйверів, сховища, мережі, постійного сеансу або kernel-enforced sandboxing. Записи каталогу Mora не виконують команди маніфестів і не надають апаратних привілеїв.

## Архітектурні цілі

x86_64 — основна ціль для Intel та AMD. Ельбрус збережено як окремий напрям сумісності; це не означає наявності backend компілятора, boot image або матриці випробувань на фізичному обладнанні.

## Федерація вихідного коду та цілісність

The active source set is pinned in federation/repositories.v1.json. Initialize the exact recorded revisions with:

~~~sh
git submodule update --init --recursive
~~~

The peer projects remain separate repositories with independent ownership, licenses, contracts and release cycles:

- [Reaper](https://github.com/Ivan-VHS/Reaper)
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki)
- [OPlague](https://github.com/Ivan-VHS/OPlague)
- [VentuSample](https://github.com/Ivan-VHS/VentuSample)

## Документація

- [Architecture](docs/ARCHITECTURE.md)
- [Implementation status](docs/IMPLEMENTATION_STATUS.md)
- [Bootable image](docs/BOOTABLE_IMAGE.md)
- [Core subsystem MVP](docs/CORE_MVP_V1.md)
- [Ecosystem integration](docs/ECOSYSTEM_INTEGRATION.md)
- [Project evolution ladder](docs/PROJECT_EVOLUTION_LADDER.md)
- [Native Reaper integration](docs/REAPER_INTEGRATION.md)
- [Documentation index](docs/README.md)

The implementation-status ledger, bootable-image guide and project evolution ladder are the authoritative records for delivered and pending system layers.

## Ліцензія та правовий статус

У корені репозиторію немає файла LICENSE або декларації ліцензії. Не можна припускати MIT, Apache-2.0 чи право на розповсюдження. Ліцензію має обрати й затвердити правовласник до розповсюдження.

Do not redistribute bundled or third-party materials outside the applicable license grants. A Git submodule pin records a source revision; it does not change ownership or license terms.

## Інженерне правило

Описуйте поведінку на підставі вихідного коду, тестів, схем, збирання та CI. Каталог або roadmap не доводять реалізацію. Налаштування браузера — не kernel enforcement; аналіз PE — не запуск процесу; checksum — не доказ авторства.

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 UTC</sub></p>