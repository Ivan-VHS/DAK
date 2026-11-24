# Полный переход DuckOS на Reaper: архитектура, миграция и согласованное развитие двух проектов

**Документ:** DuckOS–Reaper Full Language Migration and Platform Unification Plan  
**Версия:** 0.1.0 (проектная спецификация)  
**Дата фиксации исходного состояния:** 24 ноября 2026 года  
**Язык документа:** русский  
**Канонический владелец системных контрактов:** DuckOS  
**Канонический владелец языка, компилятора и исполнения:** Reaper  
**Статус:** архитектурный план; не является заявлением о завершённом переносе  
**Связанный проектный документ Reaper:** docs/DUCKOS_NATIVE_TARGET_PROFILE.md

---

## 1. Назначение и границы

Этот документ задаёт сквозную программу преобразования DuckOS в операционную систему, чьи системные политики, сервисная логика, прикладные процессы и системные инструменты реализуются на Reaper. Одновременно он задаёт встречную программу развития Reaper: язык должен получить недостающие свойства полноценного системного языка, чтобы DuckOS мог использовать его не только как язык контрактов и сценариев, но и как основную реализационную платформу.

Термин «полный перевод» означает перенос семантически значимой логики, алгоритмов, системных сервисов, политик, конфигурационной обработки и пользовательских приложений на Reaper. Он не означает механическое удаление каждого байта Python, C, JavaScript, HTML, CSS, JSON или ассемблера. Эти технологии могут оставаться в строго ограниченных ролях: ранний bootstrap, целевой машинный код, архитектурные инструкции, статическая разметка, оформление, совместимые внешние библиотеки и данные. Критерий перехода состоит в том, что ни один высокоуровневый системный сценарий DuckOS не зависит от Python-реализации как единственного источника поведения, а все публичные системные контракты могут быть проверены и исполнены официальным Reaper toolchain.

Документ разделяет четыре категории: подтверждённое состояние (код, тест, файл или CI уже присутствует); частичная реализация (часть функции существует, но полной готовностью не является); целевая спецификация (требование к будущей архитектуре); критерий приёмки (проверяемое условие до следующего этапа). Ни один раздел не является доказательством наличия загрузочного ядра, физического менеджера памяти, защищённой модели процессов, рабочего драйверного загрузчика, полноценного Win32/NT-слоя или нативного графического композитора.

## 2. Основное архитектурное решение

**DuckOS использует Reaper как основной язык системной реализации. Reaper остаётся независимым языком программирования и инструментальной платформой.** Это создаёт направленную зависимость: DuckOS зависит от версионированных языковых, runtime, ABI и compiler-контрактов Reaper; Reaper не зависит от внутренней структуры DuckOS и обязан работать вне него.

Reaper владеет грамматикой, лексической и синтаксической семантикой, AST, типовой системой, системой эффектов, промежуточным представлением, оптимизатором, VM, нативными backend-ами, стандартной библиотекой, модульной системой, отладчиком, LSP/DAP и компиляторными диагностическими контрактами. DuckOS владеет загрузочной последовательностью, системной ABI, ядром, системными вызовами, политикой памяти, планировщиком, процессами, IPC, VFS, драйверной моделью, сервисным менеджером, пакетной системой, безопасностью платформы, desktop-композитором и интеграцией приложений.

Между ними существует версионированный контракт целевой платформы. Он описывает ABI, целевой triple/profile, правила вызова, размеры и выравнивания типов, владение ресурсами, системные эффекты, capability-модель, формат объектного модуля, диагностические сведения и требования загрузчика. Python, C и JavaScript не объявляются «запрещёнными» глобально. Каждый оставшийся фрагмент обязан иметь объяснимую роль, ограниченную поверхность API, владельца, входные и выходные контракты, тесты и план возможной замены.

Центральная техническая цель — довести цепочку «исходник Reaper → lexer/parser → typed IR → verified system IR → target backend → object/image → linker → bootable artifact» до состояния, в котором весь системный код DuckOS проверяется и компилируется официальным Reaper toolchain. Пока нативная цепочка не достигла такого состояния, Python reference runtime остаётся эталоном совместимости для поддерживаемого языкового среза, но не должен считаться конечным системным исполнителем.

## 3. Зафиксированная исходная точка и проверенные факты

Исходное состояние проверено по основным веткам репозиториев 24 ноября 2026 года:

| Репозиторий | Ветка | Проверенный commit | Роль |
|---|---|---|---|
| Ivan-VHS/DuckOS | main | b2040d6426d97725c3c22293ece66b79b2ab2fef | ОС, контракты, desktop, сервисы |
| Ivan-VHS/Reaper | main | 9cfb9f496e3f005ca65e15df013ad7814a27f815 | язык, runtime, compiler, Studio |

В дереве DuckOS submodule projects/reaper закреплён на cd84d347959f9b6cf60d87ab3d36bc94e05fd80f. Сравнение этого pin с Reaper main показало, что upstream-ветка опережает закреплённый commit на два commit-а и не отстаёт от него. В этой разнице обнаружены профиль системных возможностей, его валидатор, workflow и обновление документационного индекса; это не основание молча перемещать submodule pin. Pin обновляется отдельным согласованным изменением DuckOS после выполнения тестов на выбранном Reaper commit.

DuckOS уже позиционируется в docs/ARCHITECTURE.md как Reaper-first OS implementation. Его код содержит Reaper-модули ядровых политик в duckos/kernel/*.rpr, duckos/drivers/*.rpr, duckos/security/*.rpr, duckos/storage/*.rpr, duckos/services/*.rpr, duckos/system/*.rpr и duckos/ui/*.rpr. Наличие этих модулей доказывает формализацию контрактов и проверку некоторых алгоритмов на Reaper reference runtime; оно не доказывает работу физических устройств или выполнение в kernel mode.

В DuckOS остаются значимые Python-подсистемы: CLI, deployment/build validation, manifest, hardware inventory, image layout, module ABI, PE/ELF inspection, compatibility-prefix tooling, runtime discovery, DuckBridge, terminal, native desktop services, Reaper launcher/workbench и вспомогательная логика. MORA использует JavaScript, HTML, CSS и JSON. Фундаментальная структура включает C-файлы boot-info и CMake. Следовательно, миграция должна иметь несколько независимых потоков и общий план совместимости.

Reaper уже имеет lexer/parser, AST, reference tree-walk runtime, Canonical IR, bytecode VM, консервативный type checker, модульный loader, resource/heap accounting, transaction API, CLI/REPL, Studio, LSP/DAP, Kora helpers, Python FFI boundary, экспериментальный C17 AOT scalar subset, отдельный native C17 lexer/parser/IR/lower/optimizer path, QCS validation frontend, hardware/embedded workbench и первые self-hosting tokenizer/parser примеры. Это существенная база, но не полный нативный компилятор.

Текущая документация Reaper указывает, что Python является исполняемой reference-реализацией широкого среза языка; C17 AOT поддерживает ограниченный scalar subset; C17 IR-путь частичен; полноценная генерация ELF/PE/Mach-O, DABI64, полная типовая проверка ownership/effects, системные MMIO/IRQ/DMA-сервисы и полная parity с Python пока не заявлены. Это ограничение определяет порядок проекта: сначала укрепить язык и промежуточное представление, затем ABI и backend, затем системный bring-up, затем удалять legacy-слои.

### 3.1. Что уже можно повторно использовать

DuckOS должен сохранить и превратить в тестовые спецификации уже существующие политики: startup phase order; signed range arithmetic; 64-byte frame arena model; SoA size calculations; priority/deadline scheduler selection; least-loaded worker policy; bounded FIFO queue; byte-accounted UDB backpressure; capability membership and attenuation; untrusted/validated/quarantined states; driver ABI descriptor checks; resource and IRQ conflict detection; service restart budget; content-addressed graph references; journal sequence monotonicity; deterministic LWW merge; CPU/accelerator/node-mesh selection; bounded telemetry policy; reduced-motion and frame-budget checks. Эти модули — исходные семантические эталоны, но для каждого следует разделить pure policy, host adapter и privileged implementation.

### 3.2. Что нельзя считать готовой системой

Пока не должны считаться готовыми: физический allocator и page tables; переключение контекста и preemptive scheduling; процессы и address spaces; syscall entry/return; kernel-enforced capabilities; shared-page zero-copy IPC; реальная PCI/PCIe/USB/ACPI enumeration; cryptographic module signature verification; isolated driver loading; durable BLAKE3 graph and event journal; GPU submission and compositor; UEFI/BIOS boot path; bootable ISO/USB; native NT/Win32 process runtime; полноценный package manager, init process tree и filesystem; нативный аудиостек. План предусматривает эти направления, но не приписывает их текущему коду.

## 4. Терминология зрелости и доказательства

Для каждого capability используются независимые поля:

- maturity: proposed, prototype, partial, implemented, qualified, deprecated;
- execution_mode: design_only, reference_runtime, hosted_native, freestanding, kernel_privileged, hardware_verified;
- integration_policy: required, optional, opt_in, disabled_by_default;
- verification: not_run, unit_pass, contract_pass, differential_pass, emulator_pass, hardware_pass;
- evidence: конкретные source paths, test paths, CI run, emulator target и, где применимо, hardware qualification record.

Нельзя смешивать статус реализации с политикой подключения. Optional не означает partial; contract_pass не означает hardware_verified; наличие schema не означает работающий service. Для системных API обязательно хранить минимальную и максимальную поддерживаемую версию, target profile, security owner, resource limits и известные ограничения.

Все status tables, README, capability registries и release metadata должны проверяться одним набором валидаторов. Формулировки «полностью поддерживается», «нативный», «безопасный», «реального времени» и «bootable» допустимы только при наличии точного определения, количественного критерия и проверочного доказательства.

## 5. Целевая архитектура

Целевая система делится на слои с односторонним направлением зависимостей.

### 5.1. Слой языка и компилятора Reaper

Содержит Unicode-aware lexer, parser frontends, AST, canonical syntax model, type checker, effect checker, ownership/borrow checker, HIR/MIR/IR, verifier, optimizer, target lowering, code generator, assembler/object writer либо надёжный промежуточный bridge, linker integration, debug/source maps, package metadata и deterministic diagnostics. Языковой слой не содержит правил конкретной ОС и не привязан к kernel structures.

### 5.2. Слой целевой платформы DuckOS

Содержит machine description, ABI profile, linker layout, boot protocol, syscall ABI, kernel object types, memory map, interrupt model, scheduler hooks, IPC primitives, capability identifiers, driver ABI, service manager API, VFS API и platform services. Все поля версионированы и имеют проверяемую схему.

### 5.3. Слой ядра

Ядро разделяется на architecture-neutral policy и architecture-specific mechanism. Общая политика реализуется на Reaper. Минимальные CPU entry/exit, interrupt stubs, context-switch assembly, page-table primitives и port/CSR operations могут быть target-specific backend intrinsics либо небольшими audited assembly/C units, если Reaper пока не генерирует безопасный код для соответствующей операции. Исключения инвентаризируются; C не должен незаметно становиться вторым высокоуровневым языком ядра.

### 5.4. Слой системных сервисов

Init, service supervisor, device broker, VFS providers, package manager, logger, telemetry collector, network stack, audio/video services и compatibility services являются изолированными Reaper components. Каждый сервис имеет manifest, capability set, memory/CPU budget, IPC schema, lifecycle state machine и health contract.

### 5.5. Слой рабочего стола и приложений

Mora и приложения используют единые typed UI/service contracts. Доменная логика, application state, validation, commands, persistence policy и orchestration переносится в Reaper modules. Разметка, стили, шрифтовые файлы, изображения и browser compatibility glue остаются presentation resources. Для нативного рабочего стола Reaper управляет model/controller/state, а compositor и platform adapter получают минимальный UI ABI.

### 5.6. Слой инструментов разработки

Reaper Studio и Duck Desktop остаются отдельными продуктами. Studio отвечает за исходный код, диагностики, граф IR, профили целей, debug, linker maps и hardware workbench. Duck Desktop предоставляет OS-level administration surface: установка компонентов, сервисы, логи, права, устройства и состояние ядра. Между ними используется versioned local protocol, а не импорт приватных Python-классов.

## 6. Принципы, которые миграция не имеет права нарушать

1. **Семантическая сохранность.** Для каждой переносимой функции зафиксированы входы, выходы, ошибки, побочные эффекты, порядок наблюдаемых действий и граничные случаи.
2. **Проверяемое владение.** Каждый handle, page mapping, DMA buffer, interrupt registration, lock, file descriptor, IPC endpoint и device session имеет однозначного владельца и момент освобождения.
3. **Изоляция привилегий.** Язык не может сам себе выдать kernel privilege. Capability предоставляет только доверенный host/kernel broker.
4. **Предсказуемые ресурсы.** Размеры input, queue depth, heap, stack, recursion, execution steps, open resources, retry budget, message size и timeouts ограничены контрактами.
5. **Никакой неявной магии I/O.** File, network, process, MMIO, IRQ, DMA, clock, entropy, power и privileged operation требуют декларируемого эффекта и явной capability.
6. **Совместимость через версии.** ABI, IR, object format, module manifest, syscall table, IPC protocol, data schema и migration rule не меняются несовместимым образом без новой major version или version negotiation.
7. **Доказательства отдельно от заявлений.** Результат reference interpreter теста не выдаётся за native codegen, emulator boot или hardware qualification.
8. **Fail closed.** Некорректная метаинформация, неподходящая архитектура, неизвестная capability, испорченный digest, отсутствующая подпись или превышенный лимит ведут к отказу.
9. **Воспроизводимость.** Pinned toolchains, source commits, submodule commits, build flags, generated artifacts, reproducible timestamps and hashes фиксируются.
10. **Независимость Reaper.** DuckOS target profile — одна из целей языка; его наличие не навязывает Reaper API всем другим пользователям.
11. **Модульность и расширяемость.** Добавление архитектуры, драйвера, service provider, frontend locale, plugin или backend не требует переписывать доменное ядро.
12. **Обратимость миграции.** На каждой стадии существует рабочий предыдущий путь или recovery artifact, пока новый путь не квалифицирован.

## 7. Языковой контракт Reaper для DuckOS

### 7.1. Стабильный пользовательский синтаксис

Сохраняются основные существующие конструкции craft, make, vary, change, yield, emit, when, otherwise, each, loop while, import, export и оператор потока ::. Existing programs remain parseable according to the declared language version. Изменение ключевого слова или precedence оформляется через language edition, migration tool и conformance corpus.

### 7.2. Синтаксические режимы и локализация

Reaper должен поддерживать несколько frontend profiles в одном project, с явными границами модуля и без эвристического смешивания токенов: canonical English syntax; Russian MOST profile; Ukrainian localized profile; additional declared locale profiles; flow-first expression syntax; classic call/expression syntax; declarative configuration blocks; embedded domain-specific frontends where selected explicitly.

Локализованный keyword не образует отдельную семантику. Каждый alias после разбора нормализуется в один canonical token/operator/AST node. Диагностика хранит canonical diagnostic code и locale-specific message catalog. Formatter по умолчанию сохраняет выбранный frontend profile; мигратор может преобразовать весь модуль или отдельный синтаксический блок только с явным обозначением dialect. Идентификаторы, строки, комментарии и внешние API names не должны повреждаться нормализацией.

### 7.3. Типовая система

Нужны fixed-width signed/unsigned integers, usize/isize, floating-point types с зафиксированной семантикой, bool, text/bytes, arrays, slices, tuples, structs, enums, tagged unions, option/result, function pointers, opaque handles, references, raw pointers только в unsafe boundary, atomics, vectors, address-space-qualified types и explicit physical units. Целочисленные переполнения имеют режимы checked, wrapping и saturating, указанные в операции или типе, а не неявную зависимость от backend.

Для ядра и драйверов Any не допускается на privileged boundary. Динамические значения могут существовать в userland, но преобразуются после строгой runtime validation к конкретному типу. ABI типы фиксируют размер, alignment, endianness и representation; компилятор выдаёт layout report.

### 7.4. Ownership, borrowing и lifetime

DMA buffers, mapped pages, IRQ tokens, device handles, locks, file descriptors, process handles и IPC endpoints требуют affine/linear lifecycle. Простой copy не должен дублировать эксклюзивное владение. Borrow checker предотвращает use-after-free, use-after-unmap, double-release и data race, насколько это возможно статически. Unsafe escape hatch имеет локальный scope, декларирует инварианты и проходит отдельный audit.

Система поддерживает deterministic destruction, explicit defer/drop semantics, structured cleanup при ошибке и запрет утечки ресурсов при panic/unwind или abrupt service restart. На target profiles без unwind применяется явно описанный abort/recovery strategy.

### 7.5. Эффекты

Функция должна декларировать эффекты вроде file.read, file.write, process.spawn, ipc.send, net.socket, clock.read, entropy.read, mmio.read, mmio.write, irq.register, dma.map, memory.map, power.manage, display.submit, audio.stream, unsafe. Список — versioned registry; эффекты не являются произвольными строками на security boundary.

Effect checker анализирует вызовы и транзитивные эффекты модулей. Manifest заявляет требуемые capabilities. Runtime/kernel broker решает, будет ли capability выдана конкретному экземпляру процесса. Эффект не тождественен разрешению: он сообщает, что операция возможна в логике программы; capability сообщает, что host действительно разрешил её.

### 7.6. Ошибки и control flow

Системные функции возвращают явный Result<T, E> или эквивалентный tagged union. Ошибка имеет стабильный code, severity, source span, subsystem, retryability и safe public message. Скрытый exception как неявный control flow на ABI границе запрещён. Ошибки cancellation, timeout, backpressure, stale handle, permission denied, device removal, memory pressure и schema mismatch должны иметь различимые коды.

## 8. Компиляторная архитектура и нативное исполнение

### 8.1. Pipeline

Целевой compiler pipeline: source bytes → encoding check → dialect-aware lexer → canonical AST → name resolution → typed HIR → effect/ownership analysis → MIR/CFG → verified canonical IR → optimization → target lowering → object emission → link → image metadata → verification.

Каждый этап сохраняет source map и диагностический trace. На границах IR применяется verifier, который проверяет типы operands, block terminators, dominance, control-flow graph integrity, resource state transitions, effect annotations, capability requirements, target restrictions and alignment promises. Невалидный IR невозможно передать backend.

### 8.2. IR поколения

Текущий Canonical IR и VM должны стать промежуточным совместимым слоем, а не одновременно неформальной реализацией всех будущих native semantics. Рекомендуется разделение: AST — синтаксические узлы, комментарии, точные spans и dialect provenance; HIR — разрешённые имена, типы, перегрузки, generic substitutions и effects; MIR — control-flow graph, explicit control transfers, ownership moves, drops, borrow regions and error edges; low-level IR — target-independent operations with explicit widths, alignment, memory ordering and calling convention; target IR — ABI-specific address spaces, registers, interrupts, MMIO operations and relocation intent; object metadata — symbols, sections, relocations, unwind/debug data, capabilities, imports and target profile.

IR schema/version и semantics specification хранятся отдельно от внутреннего Python object layout. Каждый сериализуемый формат имеет validator и compatibility tests.

### 8.3. Нативный backend

Нельзя перепрыгнуть от текущего scalar C17 AOT subset прямо к kernel binary. Развитие идёт последовательно: расширение типизированного IR; parity tests; host native backend; debug information; object writer/linker integration; cross targets; freestanding startup; relocation and linker script support; architecture ABI conformance; kernel-specific intrinsics; boot image integration. C17 generated source остаётся полезным промежуточным backend, но не каноническим форматом системы.

Для x86_64 сначала фиксируется одна конкретная ABI и один emulator target. Потом добавляются AArch64 и RISC-V64 через независимые target profiles. i686 сохраняется только при наличии практической необходимости и тестовой инфраструктуры. Каждый target profile содержит data layout, calling convention, stack direction/alignment, register preservation, TLS strategy, atomic capabilities, interrupt model, relocation types, object format, linker invocation and known limitations.

### 8.4. Детерминированность

При одинаковом source tree, toolchain pin, environment whitelist, target profile и build flags build должен выдавать идентичный normalized artifact. Build timestamp, random seeds, locale, path prefix and host absolute paths не могут протекать в reproducible section без явного исключения. Подписанные artifacts подписываются после детерминированной сборки; подпись не заменяет reproducible build.

## 9. Bootstrap и последовательное удаление Python-зависимости

Миграция не должна иметь big bang. Предлагаются четыре bootstrap поколения:

- **Stage 0 — текущий host bootstrap.** Python запускает Reaper reference runtime, CLI, тесты и часть build tooling. Его роль документирована и ограничена.
- **Stage 1 — Reaper VM bootstrap.** Reaper compiler/runtime сам проверяет и исполняет значительную часть compiler utilities на Canonical IR/VM; Python пока загружает процесс, собирает native backend и запускает окружение.
- **Stage 2 — Reaper native host compiler.** Достаточный поднабор Reaper компилируется в нативный executable, который проходит differential suite относительно Python reference implementation.
- **Stage 3 — self-hosted Reaper toolchain.** Компилятор Reaper строит сам себя из исходников Reaper, результат повторно собирает тот же toolchain и проходит bootstrap reproducibility проверки.

Python удаляется с critical path только после того, как Stage 3 повторяемо работает на поддерживаемых host platforms и есть восстановительный Stage 0 bundle, подписанный и сохранённый для аварийных случаев. Наличие self-hosting tokenizer/parser demos не означает self-hosted compiler.

Для каждого build command определяется, кто его исполняет, какие входы читает, какие outputs создаёт, какие privileges нужны, может ли он писать за пределы staging root и как восстанавливается после сбоя. Нельзя позволять скриптам миграции автоматически вызывать найденные toolchain binaries без явного запуска build step и проверки их hash/version.

## 10. Системный ABI DuckOS и ABI Reaper

### 10.1. Kernel ABI

DuckOS определяет отдельную versioned kernel ABI. Она включает target architecture и sub-architecture; data model и fixed-width base types; calling convention и stack alignment; register preservation и syscall transition rules; error code layout; handle representation and generation; capability token representation; memory mapping, ownership, pinning and unmapping; cancellation and timeout convention; syscall table version; kernel object layout only where explicitly public; module entry, init, shutdown and dependency contract; debug/unwind and panic metadata; endianness and atomic memory order guarantees.

Compiler-internal Python classes, AST node representation, CPython object addresses, arbitrary pointers и внутренние структуры Reaper runtime никогда не экспортируются как kernel ABI.

### 10.2. System call interface

System calls группируются по доменам: process/thread, memory, scheduler, synchronization, IPC, handle management, filesystem, time, device, capability, power, diagnostics and graphics. Таблица вызовов имеет stable numeric identifiers, ABI version, input/output schema, maximum buffer sizes, capability requirement and cancellation semantics.

Каждый syscall wrapper сначала валидирует user pointers, length, alignment, access rights, handle generation and capability. Copy-in/copy-out выполняется с fault containment. Kernel не доверяет длине, указателю или enum, переданным пользовательским процессом. Операции, которые могут блокироваться, поддерживают timeout/cancellation и не удерживают global locks во время ожидания.

### 10.3. Reaper host ABI и module ABI

Reaper native module format не смешивается с DuckOS driver ABI. Reaper имеет общий object/module interface, DuckOS target profile добавляет constrained system-module descriptor. Descriptor включает module identity, semantic version, compiler edition, language ABI, target triple, kernel ABI, exported symbols, imports, required capabilities, memory/stack budget, dependency list, signature metadata, build provenance and entrypoints.

Загрузка происходит в несколько стадий: parse metadata; validate target; verify hash/signature; resolve dependency graph; check capability policy; allocate protected memory; map sections; apply relocations; verify executable permissions; execute controlled init; publish handles only after successful init. Ошибка на любой стадии приводит к cleanup и rollback без публикации частично созданного модуля.

## 11. Boot и ранний startup

Boot contract задаёт boot protocol version, architecture, memory map, framebuffer descriptor, firmware tables, entropy source state, initramfs location/size/digest, command line, verified boot status, CPU capabilities, NUMA topology when available, boot device identity, recovery selection and handoff checksum.

Ранние стадии: firmware transfers control to minimal entry; entry validates boot information and CPU mode; establish minimal stack and serial diagnostics; verify kernel image metadata and required CPU features; build initial page tables and guarded stacks; initialize physical page allocator; initialize interrupt controller and timer; enter scheduler and create idle/boot tasks; mount initramfs and start first user-space supervisor; activate core services under least privilege; initialize graphics after recovery console is available.

Boot stage should avoid dynamic allocation until allocator is initialized. Every phase writes a bounded structured boot event. Recovery mode is a real alternate boot configuration, not only a label in a contract test. A failed phase cannot be marked complete. Watchdog, panic and emergency console need defined no-heap fallback paths.

## 12. Memory architecture

Memory design distinguishes physical pages, virtual address spaces, kernel mappings, user mappings, stack, static data, heap, region/arena, shared buffers, pinned DMA pages and device MMIO windows. The current 64-byte arena alignment is an algorithmic contract; it does not replace page alignment or cache/DMA alignment.

Allocator family includes physical page allocator, virtual region allocator, kernel slab/object allocator, user-space virtual memory manager, per-thread stack allocator, bounded arena allocator for boot/events, shared-memory buffer allocator and DMA-safe allocator. Each allocator has explicit ownership, failure mode, fragmentation metrics, limits, zeroing rules, guard behavior and concurrency model.

The system distinguishes allocation failure, quota exceeded, address-space exhaustion, fragmentation, invalid alignment, access violation, double free and stale mapping. Large allocations require overflow-safe arithmetic. All ranges use documented half-open interval semantics and checked addition/subtraction; signed/unsigned conversion cannot bypass range checks.

Memory mapping APIs are typed leases. A mapped region handle carries base, length, permissions, cache policy, memory type, generation and owner. Drop/unmap checks generation and prevents double release. MMIO mappings cannot be passed to ordinary heap APIs; DMA buffers cannot be freed while pinned or in-flight. Physical addresses are not represented as ordinary user pointers.

## 13. Scheduler, threads and processes

Policy and mechanism are separate. Reaper expresses deterministic choices; kernel mechanisms perform context switch, interrupt preemption, CPU affinity and wakeups.

The scheduler contract defines task states, legal transitions, priority classes, deadlines, CPU budget, affinity, criticality, fairness, starvation avoidance, wake conditions and cancellation. Real-time behavior cannot be claimed solely because an EDF-like comparison exists. The actual scheduler needs timer interrupt integration, bounded critical sections, measured dispatch latency and overload policy.

Threads have kernel-owned stacks, register context, TLS, FPU/vector state policy, signal/cancel state and join lifecycle. Processes own address space, handles, capabilities, executable mapping, environment, file namespace and resource budget. Process start is transactional: validate executable, reserve resources, create address space, map image, establish initial stack, attach handles, set entry and schedule only after all invariants hold.

The current flock/least-loaded selector can remain a scheduler policy helper. Work stealing requires safe runnable queues, migration rules, per-CPU synchronization, affinity and stack ownership; it is not implemented by merely moving a task identifier.

## 14. IPC и communication model

IPC primitives include bounded message queues, event notification, channels, request/response RPC, shared memory leases and capability transfer. Every message uses a versioned schema and explicit maximum payload. Queue-full returns backpressure; it must not silently drop a message unless the channel contract explicitly declares lossy delivery.

Message sequence numbers, replay policy, sender identity, receiver identity, cancellation, timeout, ownership of transferred handles and error behavior are specified. Kernel verifies that transferred capability handles are attenuated and that sender has transfer authority. Shared memory requires explicit mapping, memory ordering, producer/consumer protocol, lifetime lease and crash cleanup.

UDB byte-stream accounting remains useful as a flow-control policy. Native implementation must add wakeups, cancellation, process teardown and shared-page mechanics. Zero-copy cannot be advertised until it is measured and validated across address spaces.

## 15. Capability security and trust

Capability names are stable machine identifiers, not informal strings. Capability grants include subject, object/resource scope, operations, constraints, expiry/revocation generation and audit classification. Parent-to-child derivation is monotonic attenuation: child authority must be a subset or equal under declared delegation semantics.

Trust levels are not booleans supplied by untrusted callers. A signature status is produced by a cryptographic verifier with trust store, key identity, algorithm, certificate policy, revocation status and signed metadata binding. A package cannot claim itself verified. Hash equality proves byte identity, not provenance.

All external content begins untrusted: source code, driver package, network message, archive, executable, schema, device descriptor and update metadata. Validation returns a typed validated object carrying provenance. Quarantine is a non-executable state with clear retention and review policy. Validated data still does not bypass capability checks.

Kernel enforces capabilities at syscall and object-handle boundaries. User-space policy may request permissions, display consent and create audit summaries but cannot substitute for enforcement. Revocation semantics define whether active operations stop immediately, at next checkpoint or after lease expiry. Every long-lived handle observes revocation generation.

## 16. Driver framework and hardware boundary

Driver metadata is versioned and bound to target architecture, kernel ABI, language ABI, module ABI, device IDs, bus, dependencies, interrupt model, DMA constraints, memory budget and capabilities. Device discovery reads firmware/platform data through safe enumeration code. Driver matching is separate from driver loading.

A driver lifecycle includes discovered, matched, verified, authorized, staged, mapped, initialized, active, quiescing, stopped, failed and quarantined. Each state has allowed transitions and resource ownership. On device removal, DMA stops before memory is released; IRQ registrations are masked/unregistered; mappings are revoked; user-visible handles become stale.

Hardware operations live behind narrow typed Reaper intrinsics and platform adapters. MMIO register descriptors include address space, width, access policy, reset value when known, alignment, endianness, volatile/atomic semantics and side-effect description. Volatile alone is not a memory barrier. IRQ handlers are bounded, avoid allocations and blocking locks, and defer expensive work. DMA specifies cache-coherency operations and device/CPU ownership transfer.

The current DuckOS driver orchestrator checks descriptor conflicts and package metadata. Future implementation must not reinterpret a descriptor check as actual device support. Real PCI/USB/ACPI scanning, IOMMU, DMA isolation, MSI/MSI-X, interrupt routing and firmware quirks each need separate target-specific tests.

## 17. Storage, VFS и transactional state

OS needs VFS namespace rules, path normalization, mount permissions, file handles, metadata, directory iteration, filesystem error mapping, symlink policy, journaling and crash recovery. User paths are not trusted kernel paths. File operations use handle-based APIs and capabilities.

The existing manifest and deployment code can seed the package model: canonical relative paths, byte size, hash, architecture and kernel ABI. Package store additionally requires package identity, version, dependency constraints, signature, provenance, file ownership, permissions, capabilities, lifecycle scripts and rollback metadata.

Install/update is transactional: resolve and validate; download or stage; verify hash/signature; check free space and ABI; build inactive root; construct package DB delta; update boot selection only after all checks; write durable commit record; health-check new system; finalize or roll back. A power-loss test is required between every durability boundary.

The current Reaper RuntimeTransaction is an in-memory JSON-compatible host state engine with SHA-256, generation checks and rollback. It is not a filesystem transaction or physical flash operation. It can inform the state machine, but disk commits require journal semantics, fsync ordering, checksums, atomic rename/switch and recovery tests.

The semantic graph and CRDT direction must be scoped. LWW register is one operation, not a complete distributed CRDT. Durable event journal, graph consistency, content addressing, structural sharing, garbage collection and replication conflict rules require independent specs.

## 18. Service manager and process supervision

Services are described by a manifest: identity, version, entry point, imports, required capabilities, startup dependencies, readiness probe, health interval, restart policy, resource budgets, IPC endpoints, configuration schema, data directory and shutdown contract.

Supervisor states are explicit: discovered, validated, staged, starting, ready, degraded, stopping, stopped, failed, quarantined. Startup dependency cycles are rejected. Readiness differs from process creation. Restart policy has finite budgets, backoff, crash-loop detection and escalation to recovery mode. A service cannot restart forever or silently reset its resource quotas after a crash.

A service receives only capabilities required by its manifest and active policy. Hot reload requires a two-phase replace: start new instance in isolated namespace; verify readiness and state migration; atomically switch routing; drain old instance; revoke old handles; reclaim resources. Failed migration leaves old instance active.

## 19. Desktop, Mora и user applications

Mora is the main user-facing shell and currently is a web application assembled from HTML, CSS, JavaScript and JSON data/configuration. A full Reaper transition should port domain behavior in a controlled way while preserving visual system and usability.

The following responsibilities should move to Reaper modules: application registry normalization, installation state and policy evaluation; commands/actions and input validation; application lifecycle and persistence rules; shell navigation model, dock/window state machine and focus policy; user preferences schema, migrations and restore logic; capability requests and consent workflow; local audit/proof operations; service calls, error mapping and resource budgets; app catalog queries, safe file inspection orchestration and workflow coordination.

The following may remain as static or runtime-specific presentation resources: HTML semantic structure; CSS design tokens, responsive layout and animations; SVG, raster assets, icons and fonts; browser compatibility bootstrap that only binds browser events to a typed Reaper/WASM/native service API.

For browser delivery, the target is Reaper-to-WASM or an explicitly generated/validated browser adapter once the backend supports it. No such general WASM backend is assumed to exist today. Until then, JavaScript remains a narrow adapter and must not duplicate domain policy. Native Mora should call the same Reaper service contracts through a local system API. Both frontends consume identical typed schemas so behavior does not diverge.

A browser service worker remains a browser lifecycle component. It should cache only public immutable UI resources under explicit cache version, never store privileged capability tokens or trusted system secrets, and never become a surrogate privileged process launcher. The existing rule that browser Mora cannot launch host processes remains in force.

## 20. Application model and catalog

Each first-party app has a stable app ID, display name, semantic version, UI entry, Reaper module package, permissions, service dependencies, input/output contracts, data directory, update policy, accessibility requirements, localization resources and health status. Display labels can be localized; IDs remain stable.

Catalog entries are divided into concept, prototype, user-space app, native service and production-qualified app. A catalog description does not mean a deployable application exists. DAK base catalog and Mora launcher registry must derive from a validated canonical catalog rather than separately duplicated arrays.

App actions are capability-specific and typed. For example, file inspection can read a selected file only after user intent and a scoped read handle; archive extraction requires a separate extraction capability and destination budget; process creation is not implicitly granted by a game launcher; network transfer requires an explicit endpoint policy. Every app has a safe disabled state when an underlying native service is absent.

## 21. Reaper improvements required by the OS target

Reaper development runs in parallel with DuckOS migration. Priority improvements include: published language edition and compatibility policy; complete typed AST/HIR and source-map-preserving diagnostics; a sound-enough type system for privileged boundaries; ownership/borrow/lifetime and resource-state checking; effect/capability propagation through imports and call graphs; stable serialized IR and independent verifier; MIR/CFG with explicit errors, drops, atomics and memory operations; target profiles for x86_64 first, then AArch64 and RISC-V64; complete host native backend with debug symbols and reproducibility; freestanding runtime profile with no implicit Python dependency; object and relocation support or a formally pinned linker bridge; stable C ABI and target module metadata; linker map, stack and memory-use reporting; compiler/bootstrap parity tests; deterministic standard library for OS services; language server support for ownership/effect/capability diagnostics; debugger support for native registers, stack frames, kernel symbols and panic reports; language-level conformance suite runnable on interpreter, VM and native target; fuzzing and property tests for lexer, parser, verifier, loader and binary writers; documentation distinguishing current runtime, partial target and proposed feature.

The OS profile must not dictate that all Reaper programs need kernel privileges or system-specific syntax. Hosted command-line programs should continue to run without a DuckOS source tree or privileged helper.

## 22. DuckOS improvements required by the OS target

DuckOS must strengthen its own platform contracts: one authoritative architecture document and reconciled status vocabulary; stable boot-info schema and ABI version; system-call table and user/kernel boundary definition; process and thread lifecycle; protected memory map and allocator families; preemptive scheduling and synchronization implementation; explicit IPC schema registry; real capability broker and audit pipeline; driver discovery, signature and isolated loading architecture; VFS and durable transactional storage; service manifest and supervisor; package manager with A/B/recovery update; initramfs and bootable-image build; emulator harness and hardware test matrix; native compositor/input/accessibility contracts; Mora service API and browser/native shared data contract; migration of Python domain logic and JavaScript domain policy; crash dump, persistent logs and safe recovery; power, clock and thermal policy implementations; performance budgets and observability.

DuckOS не копирует Reaper compiler code в собственное дерево. Он потребляет pinned Reaper distribution и target profile. В DuckOS остаются только OS-side adapter, build orchestration, contract tests и runtime components, специфичные для платформы.

## 23. Inter-repository contract и version negotiation

Два репозитория версионируются независимо. Интеграция не должна зависеть от mutable main или недокументированных relative imports. DuckOS pins reviewed Reaper commit в Git submodule и federation registry. Reaper publishes target profile capability contract. DuckOS проверяет, что minimum required Reaper version и language edition поддерживаются выбранным pin.

Required compatibility fields: reaper_language_edition; reaper_ir_version; reaper_native_abi; duckos_target_profile; duckos_kernel_abi; duckos_driver_abi; object_format; architecture; capability_registry_version; syscall_table_version; module_manifest_schema; build_toolchain_lock_digest.

При mismatch compilation или loading завершается actionable machine-readable diagnostic. Система не делает silent downgrade ABI и не переинтерпретирует unknown fields. Minor backward-compatible additions допустимы только там, где schemas явно допускают extension fields. Breaking changes требуют major version и migration tooling.

Reaper upstream may advance independently. DuckOS submodule pin changes in a dedicated commit after: Reaper CI green; DuckOS .rpr corpus check; tree-walk and VM contract suite; differential interpreter/VM/native tests; system profile validator; API compatibility check; review of changed public contracts. Federation registry and pin обновляются в одном DuckOS pull request. Pin advance никогда не выполняется background updater или build workflow.

## 24. Testing strategy

Тестирование многослойное; одна зелёная suite недостаточна.

- Lexer/parser conformance: canonical keywords, MOST aliases, locale profiles, source spans, Unicode, malformed strings, comments, nested blocks and recovery.
- Type/effect/ownership: valid and invalid programs, negative fixtures, boundary types, capability propagation, lifetime misuse, use-after-move, aliasing and effect escalation.
- IR verification: invalid opcodes, block edges, operand types, dominance, source maps, stack discipline, alignment promises and invalid resource-state transitions.
- Runtime differential: tree-walk, VM and future native backend must return same values, output, errors, side-effect ordering and termination state for the supported shared subset.
- OS contract: each .rpr contract module tests normal, boundary, overflow, concurrency and failure cases.
- ABI conformance: calling convention, register preservation, struct layout, alignment, symbol naming, relocation and error return.
- Kernel tests: allocator, page mapping, scheduler, IPC, handle generation, capability checks and rollback.
- Emulator tests: boot sequence, serial output, initramfs mount, service startup, recovery and update rollback.
- Hardware qualification: device enumeration, timer accuracy, interrupt handling, DMA coherency, storage durability and power failure where applicable.
- Security tests: malformed ELF/PE/object files, malicious module metadata, invalid signatures, replay, stale handles, path traversal, symlink races, resource exhaustion and confused-deputy attempts.
- UI tests: keyboard navigation, focus, accessibility, reduced motion, localization, restart/restore and native/browser behavior parity.
- Build/release: reproducible compiler, deterministic archive, signature verification, SBOM, provenance and clean-room installation.

Property-based testing and fuzzing target parsers, IR verifier, manifest reader, archive reader, PE/ELF parser, ABI serializers and binary writer. Each discovered crash becomes a permanent regression fixture. Fuzzing inputs are bounded and run without privileges.

## 25. CI/CD и branch discipline

Reaper CI owns language/runtime/compiler tests, native C17 build, target profile schema, self-hosting checks and toolchain inventory. DuckOS CI owns OS contract tests, deployment manifests, app catalog, federation pin validation and cross-repository integration.

A full integration workflow checks out DuckOS recursively at recorded submodule pins, verifies the Reaper commit equals federation metadata, records compiler version, validates every .rpr file, executes policy suite through tree-walk and VM, runs static checks, verifies project contracts and generates machine-readable evidence. Native backend gates are added only after that backend can run the relevant conformance set.

Build cache keys include OS, architecture, compiler revision, language edition, ABI, target profile, dependency lock and schema set. Cache artifacts are never trusted solely because a cache key matches; digest is verified. CI tokens use least privilege. No workflow should have broad write permission to system branches unless a narrowly scoped release action requires it.

Feature work follows branches and pull requests. Cross-repository changes are linked by commit SHA and PR URL in both descriptions. If one side is not ready, the other PR remains explicitly blocked rather than merging an interface that cannot be consumed.

## 26. Migration stages and exit gates

### Stage 0 — Baseline and source-of-truth cleanup

Inventory all modules; reconcile conflicting docs; record current source commits and submodule pins; define capability maturity; create compatibility corpus; add missing tests. Exit when every existing system contract has a source, owner, semantics, test and maturity tag.

### Stage 1 — Reaper language contract

Publish edition, canonical AST, syntax profiles, stable diagnostic codes, type model and module import rules. Add parse-only and typecheck-only support for all DuckOS .rpr. Exit when all current modules compile deterministically under a pinned Reaper version and produce stable diagnostics.

### Stage 2 — Verified IR and runtime parity

Formalize IR, verifier, bytecode semantics and resource lifecycle. Run contract suite on tree-walk and VM and compare results. Add fault injection for runtime limits and resource cleanup. Exit when supported language semantics are equivalent and the IR is stable under version tests.

### Stage 3 — Native host execution

Expand native AOT from scalar subset through lists, modules, closures or a deliberately restricted OS subset; define supported profile explicitly. Build a native Reaper compiler host tool. Exit when selected compiler and OS utilities pass differential tests on native backend and debug diagnostics map to source.

### Stage 4 — Freestanding compiler target and ABI

Add target profiles, object generation, relocations, linker integration, freestanding startup, stack and memory layouts. Publish DuckOS ABI and module descriptor. Exit when minimal Reaper program links for emulator target and ABI conformance suite passes.

### Stage 5 — Kernel bring-up

Implement boot path, page allocator, page tables, interrupts, timer, context switch, scheduler and panic console. Use Reaper for policy and target intrinsics for minimal mechanisms. Exit when emulator boots and reaches a stable kernel shell with reproducible logs and negative tests.

### Stage 6 — Processes, syscalls, capabilities and IPC

Implement user address spaces, syscall boundary, handles, capabilities, channels and shared memory. Add adversarial tests. Exit when untrusted user process cannot read/write privileged memory or exceed granted capabilities in the supported threat model.

### Stage 7 — Drivers, VFS, services and packages

Add safe device enumeration, signature verification, module loader, VFS, service manager, package store, transaction journal, update/recovery and rollback. Exit when core services boot, package update can recover from injected interruption, and no unsigned module loads in production profile.

### Stage 8 — Desktop and app service migration

Port Mora domain logic, application registry, persistence and service control to Reaper; keep presentation adapter bounded. Build native compositor incrementally and preserve browser view. Exit when browser/native frontends share contracts and accessibility/regression suites pass.

### Stage 9 — Self-hosting and production qualification

Reaper builds itself; build is reproducible; Python is no longer critical to target builds or runtime; image is signed and boots through verified boot policy; independent recovery path works; target hardware matrix passes. Exit only after public release qualification and rollback documentation.

## 27. Transition and compatibility bridge

During migration there are three supported execution routes: legacy Python host tools for non-privileged maintenance and test baseline; Reaper reference runtime/VM for the broad language surface; qualified native Reaper target for the explicitly supported language/profile subset. Each route reports its own execution mode in JSON evidence. No implicit fallback from a failed native compile to Python is permitted in a production image. Developers may explicitly select a compatibility route with a warning and a source digest. Kernel mode never runs through Python.

For data migration, JSON and schema validation remain language-neutral. Reaper reads/writes versioned contracts and Python tools are retained temporarily as differential oracle. A schema migration is monotonic and reversible where possible; destructive conversions run against a copied snapshot and require explicit approval.

For process integration, DuckOS keeps the current secure subprocess boundary until a dedicated native executable exists. Argument vectors, shell disabled, bounded timeout, bounded stdout/stderr, regular source-file check and no implicit privileges remain mandatory. The eventual native workbench talks to Reaper CLI protocol; it does not load arbitrary compiler internals into Duck Desktop.

## 28. Localization, syntax modes and documentation

The system supports English, Russian and Ukrainian UI/diagnostics, with MOST explicitly treated as a Russian language profile rather than an unrelated compiler. Source files declare their dialect in manifest or module metadata. A single build can contain modules in different declared profiles when imports have explicit module boundaries. A source file is never guessed to be MOST merely because a token resembles an alias.

Diagnostic codes are locale-independent. Translation catalogs are completeness-checked. Missing translation falls back to selected default locale while preserving the same error code and source span. Formatter and IDE respect per-module dialect; cross-module navigation resolves canonical symbols.

Documentation needs a canonical language edition, grammar, compatibility table, compiler pipeline, OS target profile and capability evidence index. Examples are tagged by minimum compiler edition and target. Proposed syntax is clearly labeled and does not appear in working-example lists before parser and compiler support exists.

## 29. Performance and resource budgets

Performance is measured at boundaries, not inferred from code shape. Required metrics include boot phase duration, interrupt latency, context switch time, syscall latency, IPC throughput and tail latency, allocator fragmentation, allocation latency, page fault latency, filesystem fsync behavior, service restart time, compositor frame time and compiler throughput.

Each subsystem has a budget with target hardware and workload. Percentiles and worst-case bounds are reported separately. Averages do not mask tail latency. Benchmarks record CPU model, firmware, memory, storage, compiler revision, target profile, build flags and power policy. Thermal throttling and background load are noted.

Embedded/freestanding profiles require deterministic allocation and no unbounded recursion. Kernel hot paths avoid allocation and dynamic dispatch unless measured and permitted. Async/event loops define fairness and cancellation. Userland services have per-process resource quotas. Performance optimizations must preserve IR verifier guarantees and maintain reference/native semantic parity.

## 30. Security и threat model

Assets include kernel memory, user data, credentials, update keys, executable modules, device state, boot metadata, system configuration, logs and application data. Threat actors include malformed local files, compromised user process, malicious package, compromised driver, stale/replayed IPC, compromised build dependency and physical attacker within declared platform limits.

Primary boundaries: boot firmware → kernel entry; kernel → user process; syscall input → trusted kernel state; service IPC → receiving service; package store → module loader; user consent → capability broker; host adapter → physical device; browser shell → native service; Reaper compiler → generated object and linker.

The design defends against integer overflow, out-of-bounds memory, use-after-free, TOCTOU path race, symlink traversal, signature confusion, dependency substitution, malformed object files, capability escalation, confused deputy, stale handle reuse, unbounded queues, memory exhaustion, deadlock, priority inversion, data race, rollback attack and log secret leakage.

Cryptographic policy names algorithms and key lifecycle. SHA-256 is suitable for content integrity checks in current contracts but does not prove signer identity. Production signing requires protected private keys, rotation, revocation and offline recovery keys. Signature verification occurs before code mapping and before any plugin or driver init.

## 31. Risk register and mitigation

| Risk | Consequence | Mitigation / exit evidence |
|---|---|---|
| Python reference semantics differ from native backend | silent behavior changes | differential corpus and native parity gate |
| Incomplete ownership/effect checker | kernel memory corruption or privilege escalation | disallow unsafe constructs in kernel profile; audit and fuzz |
| ABI changes during migration | modules fail or corrupt state | versioned descriptors and compatibility matrix |
| Submodule pin drift | CI uses another language implementation | pin validator and reviewed pin PR |
| C17 subset mistaken for full compiler | false readiness claims | capability maturity registry and backend matrix |
| JS domain logic remains duplicated | browser/native divergence | typed Reaper service contracts and parity tests |
| Broad privilege in workbench | host compromise | separate process, argv-only, no shell, no implicit capabilities |
| Driver/package loader too early | system corruption | read-only audit first, mock loader, then emulator and signed hardware tests |
| storage update interruption | non-bootable system | A/B image, journal and power-cut injection |
| unbounded queues or allocations | denial of service | explicit budgets, quotas, fuzzing |
| documentation drifts from code | operators misunderstand support | automated evidence validators and release checklist |
| multi-architecture work too early | fragmented engineering effort | x86_64 first, add targets after ABI gates |
| self-hosting circular dependency | unrecoverable build | signed Stage 0 bootstrap artifact and reproducible rebuild |
| UI migration breaks accessibility | unusable desktop | accessibility regression suite and manual assistive-tech checks |

## 32. Architecture decision records required before implementation

Следующие решения должны быть написаны, проверены и версионированы; этот документ намеренно не выдумывает окончательные ответы там, где репозитории оставляют вопрос открытым: primary boot protocol and firmware support; x86_64 ABI and object format for first native target; linker choice and allowed external binutils; kernel execution and privilege model; page size and physical memory allocation policy; preemption, interrupt and scheduler design; process model and syscall calling convention; handle and capability representation; IPC ordering and shared-memory ownership; filesystem and journal format; signed package and driver trust root; crash/panic and recovery model; native graphics protocol and compositor backend; browser/WASM delivery strategy for Reaper application logic; Python bootstrap end-of-support criteria; language edition and MOST syntax evolution policy; compatibility guarantees for Reaper libraries and DuckOS images.

An ADR includes context, decision, rejected alternatives, compatibility impact, security impact, performance impact, migration path, rollback path and test evidence. A decision without owner and acceptance test is not normative.

## 33. Definition of completion

Миграция завершена только тогда, когда все production system services DuckOS имеют Reaper implementation либо явно обоснованное low-level исключение; ни один Python module не требуется для выполнения системной логики в production DuckOS image; все Reaper modules проходят type/effect/ownership/target checks; native backend поддерживает точный language subset образа с semantic parity; image build не зависит от Python interpreter во время runtime; boot path, kernel, syscalls, processes, IPC, capabilities, drivers, VFS, packages and service manager реализованы и тестируются; MORA browser/native clients используют одни Reaper-owned service contracts; внешние executable modules проверяются по подписанной metadata и совместимому ABI; update recovery прошёл fault-injection tests; compiler воспроизводим и self-hosted в документированном объёме; существуют emulator и physical hardware qualification reports для каждого заявленного target; документация, capability registry, project contract, CI и release artifacts согласованы.

Частичная готовность фиксируется отдельно по каждому этапу и подсистеме. Нельзя сводить многомерное состояние системы к одному зелёному индикатору.

---
