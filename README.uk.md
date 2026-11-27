# 🦆 Duck — операційна система з пріоритетом Reaper

<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/DAK/actions/workflows/ci.yml) [![Boot image](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/boot-image.yml?branch=main&label=Boot%20image)](https://github.com/Ivan-VHS/DAK/actions/workflows/boot-image.yml) [![Native Mora](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/native-mora.yml?branch=main&label=Native%20Mora)](https://github.com/Ivan-VHS/DAK/actions/workflows/native-mora.yml)

> **Системна основа з пріоритетом Reaper, нативна desktop-оболонка хоста й локальна екосистема інструментів — із явними межами кожної підсистеми.**

**Стан:** Експериментальний проєкт · Stage 1 x86_64 перевірено в QEMU · **Версія:** Stage 1 boot foundation · **Стандарт README:** Psychoporter 666 v1.0 · **Дата перевірки:** 2026-11-25 UTC · **Source:** [Ivan-VHS/DAK](https://github.com/Ivan-VHS/DAK)

<p align="center"><img src="assets/readme/duckos-overview.svg" alt="Duck system architecture overview" width="100%"></p>

## Швидка навігація

[🚀 Demo: Browser reference preview](mora/index.html) · [Documentation](docs/README.md) · [Source](https://github.com/Ivan-VHS/DAK) · [Issues](https://github.com/Ivan-VHS/DAK/issues)

## Призначення та межі

Duck — експериментальний проєкт ОС із пріоритетом Reaper. Поточну роботу навмисно розділено на завантажувальну основу ядра, policy-контракти Reaper і нативний desktop-застосунок Mora для хостової ОС.

## Можливості

- Шлях x86_64 Stage 1 перевіряє передавання керування від Limine та Boot Info v1, виділяє ранній кадр 4 KiB, ініціалізує обмежений scheduler descriptor для BSP 0 і читає топологію CPUID та доступність MCE/MCA. Він ще не диспетчеризує потоки й не запускає вторинні CPU. QEMU-перевірки BIOS та UEFI проходять.
- Reaper надає reference-контракти для топології процесора, admission у scheduler та рішень RAS-подій і відновлення. Нові Reaper і C11 контракти проходять перевірки; фактичний SMP dispatch, APIC/IPI та обробка machine-check ще очікують реалізації.
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

Ціль Qt Desktop необов’язкова й пропускається, якщо Qt 6 Widgets не знайдено. Mora працює як нативний застосунок хостової ОС і не запускається ядром Stage 1.

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

Браузерна оболонка — демонстраційна поверхня. Вона не є нативним композитором і не означає інтеграції з ядром.

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
| Інвентаризація BSP, виявлення MCE/MCA та descriptor scheduler BSP | Реалізовано; завантаження QEMU BIOS/UEFI перевірено |
| Диспетчеризація потоків, preemptive timers, запуск AP, APIC/IPI та відновлення MCA | Очікується |
| Модель процесів і syscall ABI | Очікується |
| Kernel-enforced capabilities і zero-copy IPC | Очікується |
| PCI/USB/ACPI та ізольоване середовище драйверів | Очікується |
| Файлова система, supervisor, installer і постійний сеанс | Очікується |
| Native compositor, GPU та audio stack | Очікується |

Поточна стадія ядра також виконує read-only виявлення CPUID/MCE/MCA та ініціалізує один descriptor scheduler для BSP. Диспетчеризації потоків, SMP/AP startup, timer preemption, читання MCA-банків і системного відновлення, ізоляції процесів, завантаження драйверів, сховища, мережі, постійного сеансу й kernel-enforced sandboxing ще немає. Записи каталогу Mora не виконують команди маніфестів і не надають апаратних привілеїв.

## Архітектурні цілі

x86_64 — основна ціль для Intel та AMD. Ельбрус збережено як окремий напрям сумісності; це не означає наявності backend компілятора, boot image або матриці випробувань на фізичному обладнанні.

## Федерація вихідного коду та цілісність

Активний набір вихідного коду зафіксовано у `federation/repositories.v1.json`. Ініціалізуйте саме зазначені ревізії командою:

~~~sh
git submodule update --init --recursive
~~~

Пов’язані проєкти залишаються окремими репозиторіями з власниками, ліцензіями, контрактами та циклами випуску:

- [Reaper](https://github.com/Ivan-VHS/Reaper)
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki)
- [OPlague](https://github.com/Ivan-VHS/OPlague)
- [VentuSample](https://github.com/Ivan-VHS/VentuSample)

## Документація

- [Архітектура](docs/ARCHITECTURE.md)
- [Стан реалізації](docs/IMPLEMENTATION_STATUS.md)
- [Завантажувальний образ](docs/BOOTABLE_IMAGE.md)
- [MVP підсистем ядра](docs/CORE_MVP_V1.md)
- [Інтеграція екосистеми](docs/ECOSYSTEM_INTEGRATION.md)
- [Шкала еволюції проєкту](docs/PROJECT_EVOLUTION_LADDER.md)
- [Нативна інтеграція Reaper](docs/REAPER_INTEGRATION.md)
- [Індекс документації](docs/README.md)

Реєстр стану реалізації, посібник із завантажувального образу та шкала еволюції проєкту є основними джерелами відомостей про готові й заплановані шари системи.

## Ліцензія та правовий статус

У корені репозиторію немає файла LICENSE або декларації ліцензії. Не можна припускати MIT, Apache-2.0 чи право на розповсюдження. Ліцензію має обрати й затвердити правовласник до розповсюдження.

Не розповсюджуйте включені або сторонні матеріали поза межами прав, наданих відповідними ліцензіями. Фіксація Git submodule визначає ревізію вихідного коду, але не змінює правовласника чи умови ліцензії.

## Інженерне правило

Описуйте поведінку на підставі вихідного коду, тестів, схем, збирання та CI. Каталог або roadmap не доводять реалізацію. Налаштування браузера — не kernel enforcement; аналіз PE — не запуск процесу; checksum — не доказ авторства.

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 UTC</sub></p>

## Участь у розробці

Перед зміною коду, контрактів або документації ознайомтеся з [CONTRIBUTING.md](CONTRIBUTING.md). Робіть зміни перевірними, запускайте відповідні перевірки та точно описуйте докази реалізації.
