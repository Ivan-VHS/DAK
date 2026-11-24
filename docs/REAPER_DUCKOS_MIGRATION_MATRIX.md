# DuckOS–Reaper migration matrix and implementation cards

**Version:** 0.1.0  
**Date:** 24 November 2026  
**Status:** supporting implementation breakdown; planned work, not implementation evidence  
**Canonical architecture:** [Full 60,000-character migration blueprint](REAPER_DUCKOS_FULL_MIGRATION.md)

This companion turns the architecture blueprint into repository-level work packages. The cards identify existing ownership, intended target, contract surface and test gates. They deliberately distinguish a policy module from a native platform mechanism. Completing a card requires source, tests, CI, status metadata and documentation to move together.

## Appendix A. Реестр миграции модулей

Карточки ниже представляют рабочую декомпозицию задач по репозиториям. «Цель» описывает будущего владельца, а не заявляет, что реализация уже существует. Каждая карточка при начале работы разбивается на issues/PRs. Карточка может считаться завершённой только после синхронного обновления source, tests, CI и status metadata.

### A.1. Подробные карточки компонент

#### DuckOS CLI — duckos/cli.py

**Текущее состояние.** Python dispatcher вызывает manifest validation, image planning, hardware inventory, compatibility inspection, DuckBridge, desktop tools и Reaper workbench.

**Целевая реализация.** Перенести семантику команд и argument contracts в Reaper CLI modules; временный Python launcher оставить только для bootstrap до native executable.

**Контракт.** Stable command IDs, typed argument schemas, JSON result schema, exit codes, path limits, output mode and explicit execution mode.

**Проверка и критерий готовности.** Проверить help, malformed arguments, invalid paths, deterministic output, exit codes, timeouts и equivalence reference/native. Native CLI не должен молча откатываться к Python.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Deployment — duckos/deployment.py

**Текущее состояние.** Python создаёт component bundles, проверяет digest, поддерживает optional signing и выдаёт dry-run deployment plans.

**Целевая реализация.** Перенести policy, manifest transforms и orchestration в Reaper; OpenSSL/archiver/firmware tools оставить явными host adapters до появления проверенного эквивалента.

**Контракт.** Versioned release manifest, canonical paths, bounded archive handling, SHA-256 inventory, Ed25519 envelope, target and rollback metadata.

**Проверка и критерий готовности.** Проверить traversal, duplicate paths, symlink entries, source mutation, expanded-size limit, signature failure, interrupted staging и сохранность предыдущего artifact.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### System manifest — duckos/manifest.py

**Текущее состояние.** Python validator проверяет обязательные bootloader/kernel/initramfs/rootfs, canonical relative paths, byte lengths и SHA-256.

**Целевая реализация.** Сделать schema и validator семантику частью Reaper standard library и DuckOS build modules; JSON Schema оставить как interchange artifact.

**Контракт.** Exact fields, schema version, canonical paths, size limits, supported architectures, kernel ABI, unique component names and digest semantics.

**Проверка и критерий готовности.** Один valid/invalid corpus должен работать одинаково на legacy validator, interpreter, VM и native compiler; отдельно тестировать traversal и integer overflow.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Driver ABI — duckos/module_abi.py

**Текущее состояние.** Python проверяет descriptor shape, architecture, kernel ABI, dependencies and capability IDs; module loading не выполняется.

**Целевая реализация.** Перенести descriptor semantics в Reaper; loader mechanism оставить в kernel и target relocation adapter.

**Контракт.** Manifest schema, module identity, semantic version, target ABI, imports/exports, dependency graph, capabilities, memory budget and trust evidence.

**Проверка и критерий готовности.** Проверить duplicate modules, missing dependencies, cycles, architecture mismatch, ABI mismatch, capability escalation and deterministic load order.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### PE parser — duckos/compat/pe.py

**Текущее состояние.** Bounded PE32/PE32+ header, section and import inspection выполняются read-only.

**Целевая реализация.** Портировать parser в Reaper bounded binary-reader library; byte access — explicit file-read effect; сохранить общие fixtures.

**Контракт.** Byte order, bounds, machine IDs, header variants, RVA mapping, section count and import directory semantics.

**Проверка и критерий готовности.** Fuzz truncated headers, overflowed offsets, overlapping sections, invalid counts, malformed strings и большие файлы; audit не запускает target.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Compatibility prefix — duckos/compat/prefix.py

**Текущее состояние.** Создаёт и проверяет изолированные prefix directories; это подготовка среды, не Windows runtime.

**Целевая реализация.** Перенести prefix policy и manifest migration в Reaper; directory mutation — через scoped filesystem API с approval/rollback.

**Контракт.** Prefix schema, canonical root, architecture, app identity, ownership, path policy, runtime and data directories.

**Проверка и критерий готовности.** Проверить symlink/junction/reparse point, traversal, casefold collisions, stale lock, partial creation and manifest corruption.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### DuckBridge discovery — duckos/compat/bridge.py

**Текущее состояние.** Python обнаруживает Wine, Proton, CrossOver, Bottles, Box64 и QEMU entrypoints и формирует argv launch plans без исполнения.

**Целевая реализация.** Перенести discovery policy/backend selection в Reaper; executable discovery оставить restricted platform provider; process creation — отдельная capability.

**Контракт.** Runtime inventory schema, executable evidence, target architecture, formats, environment allowlist and plan status.

**Проверка и критерий готовности.** Проверить missing tools, non-executable paths, Flatpak wrapper, multiple Proton candidates и hostile PATH; discovery не запускает программу.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Compatibility diagnosis — duckos/compat/runtime.py

**Текущее состояние.** Диагностика исследует imports, prefix paths и architecture mismatch; native NT/Win32 runtime помечен unavailable.

**Целевая реализация.** Перенести semantic analysis в Reaper и добавить provider interface readiness. Сохранять inspectable_not_runnable до настоящего runtime.

**Контракт.** Structured blockers, missing imports, architecture comparison, prefix selection and launch-performed state.

**Проверка и критерий готовности.** Любой отсутствующий компонент должен блокировать запуск; report не может быть runnable без process manager, image loader, API, ABI и sandbox.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Hardware inventory — duckos/hardware_inventory.py

**Текущее состояние.** DuckOS собирает read-only PCI/USB или Windows PnP inventory и JSON с privacy-preserving identity hashes.

**Целевая реализация.** Сделать data model и validation Reaper-native; platform enumeration — provider с явным read-only system effect.

**Контракт.** Inventory schema, device identity, bus, source provider, platform, architecture, driver status, count and digest rules.

**Проверка и критерий готовности.** Проверить provider absence, unreadable nodes, duplicate IDs, stale data, privacy leakage и digest/count mismatch; запрещено менять драйвер.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Image layout — duckos/image_layout.py

**Текущее состояние.** Planner считает aligned, non-overlapping image regions и выдаёт metadata; диск не записывается.

**Целевая реализация.** Перенести layout arithmetic в Reaper pure policy; будущий writer сделать отдельным privileged installer service.

**Контракт.** Byte offsets, exclusive end, alignment, sectors, image size, partition roles and checked arithmetic.

**Проверка и критерий готовности.** Property tests доказывают alignment, bounds and non-overlap; тестировать extreme sizes, overflow и invalid alignment.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Duck Desktop UI — duckos/desktop/native_ui.py

**Текущее состояние.** Tk user-space window and tabs предоставляют maintenance controls; это не production compositor.

**Целевая реализация.** Перенести state, command orchestration и validation в Reaper services; Tk может остаться временным host GUI adapter.

**Контракт.** Typed command request/reply, asynchronous job states, cancellation, progress, UI capability gating and diagnostic envelope.

**Проверка и критерий готовности.** Проверить responsiveness, cancellation, disabled privileged actions без broker support и единый authorization path.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Desktop service — duckos/desktop/service.py

**Текущее состояние.** Python координирует read-only audits, cleanup hints и reversible user-level actions; некоторые операции меняют user startup settings.

**Целевая реализация.** Перенести policy и transaction plans в Reaper; platform mutations делегировать narrow services с backup-before-change и rollback.

**Контракт.** Operation manifest, before/after snapshot, user scope, confirmation, backup path, rollback token and report.

**Проверка и критерий готовности.** Windows/Linux adapters тестировать отдельно; проверить отсутствие несанкционированного удаления, privilege escalation и точного восстановления.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Reaper launcher — duckos/desktop/reaper.py

**Текущее состояние.** Bridge запускает pinned Reaper Python CLI отдельным процессом, argv, shell=False, timeout и output limit.

**Целевая реализация.** Сохранить process isolation; заменить entrypoint на verified native Reaper executable лишь после native host compiler milestone.

**Контракт.** Repository discovery, version negotiation, argument allowlist, regular source validation, output caps, timeout and JSON result.

**Проверка и критерий готовности.** Проверить invalid checkout, stale pin, symlink source, invalid suffix, output overflow, timeout and child exit; никакого shell parsing или implicit FFI.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Extended Terminal — duckos/terminal/service.py

**Текущее состояние.** Python реализует command registry, argument validation и bounded history; полномочия ограничены.

**Целевая реализация.** Перенести parser, registry, policy и state machine в Reaper. External commands отключены без отдельной process capability.

**Контракт.** Command ID, typed parameters, allowlist, environment, history bounds, redaction and effects.

**Проверка и критерий готовности.** Проверить injection, unknown command, malformed option, history overflow, secret redaction и отказ process execution.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Mora core — mora/core.js

**Текущее состояние.** Browser-local core обрабатывает app metadata, actions и часть общей shell logic.

**Целевая реализация.** Перенести canonical domain model/action validation в Reaper; JavaScript оставить event/render adapter или generated WASM glue.

**Контракт.** App identity, command schema, preferences, shell state, event names and API result envelope.

**Проверка и критерий готовности.** Одинаковые сценарии старого JS и Reaper сравниваются на migration period; тестировать offline, malformed storage и state migration.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Mora app — mora/app.js

**Текущее состояние.** Большой browser application script связывает launcher, panels, tools and local interactions.

**Целевая реализация.** Разложить на per-app Reaper modules и shared contracts; не переводить монолит line-by-line.

**Контракт.** Application manifest, state owner, lifecycle, command handler, input schema, localization, capabilities and persistence namespace.

**Проверка и критерий готовности.** Проверить каждое приложение, navigation, restart, denied permission, responsive viewport and keyboard-only workflows.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Mora Commons — mora/commons-catalog.js

**Текущее состояние.** Каталог и discovery helpers живут в локальном frontend и отделены от native package services.

**Целевая реализация.** Сделать canonical schema и discovery logic Reaper-owned; JSON сохранить как portable data/interchange format.

**Контракт.** Stable IDs, provider, category, version, maturity, required service, permissions, install source and localized metadata.

**Проверка и критерий готовности.** Validator отвергает duplicate IDs, undeclared permissions, unknown providers and unsupported maturity; catalog != installed app.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Mora service worker

**Текущее состояние.** Service worker кэширует static shell assets в ограниченной browser scope.

**Целевая реализация.** Оставить небольшой browser-owned worker; Reaper формирует cache policy и immutable asset manifest.

**Контракт.** Cache namespace version, asset digest, scope, eviction and offline fallback.

**Проверка и критерий готовности.** Проверить scope, stale cache cleanup, offline shell, upgrade rollback and absence of secret/token storage.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Boot info C — foundation/boot_info.c,h

**Текущее состояние.** C представляет и валидирует ранний handoff до готовности freestanding Reaper.

**Целевая реализация.** Сохранить minimal audited C/assembly boundary до появления Reaper entry; Reaper определяет canonical schema и verifier.

**Контракт.** Fixed-width fields, memory map count/stride, version, framebuffer, initramfs range, checksum and reserved-field policy.

**Проверка и критерий готовности.** C и Reaper validators читают одни golden binary fixtures; тестировать unaligned/truncated/unsupported/overflow.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Kernel boot — duckos/kernel/boot.rpr

**Текущее состояние.** Reaper source проверяет startup phase order and transitions.

**Целевая реализация.** Оставить policy в Reaper; firmware calls, CPU mode and early stack — target-specific mechanisms.

**Контракт.** Phase enum, transition graph, failure state, recovery route and boot events.

**Проверка и критерий готовности.** Tree-walk, VM and native target используют одинаковые valid/invalid transition tests; emulator trace нужен для native claim.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Memory and arena — duckos/kernel/memory.rpr,arena.rpr

**Текущее состояние.** Контракты моделируют signed ranges, 64-byte arena generation и SoA sizing, не physical allocator.

**Целевая реализация.** Расширить Reaper types/backend для physical/virtual addresses, page alignment and ownership; allocator/page table реализует kernel.

**Контракт.** Half-open range, page size, permissions, memory class, generation, budget and mapping lease.

**Проверка и критерий готовности.** Проверить overflow, address boundary, double release, stale generation, overlap and alignment; physical mapping требует emulator evidence.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Scheduler — duckos/kernel/scheduler.rpr,flock.rpr

**Текущее состояние.** Policies выбирают priority/deadline и least-loaded worker детерминированно.

**Целевая реализация.** Сохранить policy как Reaper pure code; kernel реализует queue synchronization, timer preemption, context switch and affinity.

**Контракт.** Task state, priority, deadline, load/capacity, affinity, budget, starvation and wake reason.

**Проверка и критерий готовности.** Property tests фиксируют детерминизм; emulator tests измеряют реальные переключения, wakeup и отсутствие потери задач.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### IPC — duckos/kernel/ipc.rpr,zero_copy_bus.rpr

**Текущее состояние.** Контракты проверяют bounded queues, byte accounting and backpressure; shared memory ещё не mapped.

**Целевая реализация.** Reaper владеет API и state machine; kernel — synchronization, wakeup, process validation and page mapping.

**Контракт.** Message version, queue cap, max bytes, sequence, identity, backpressure, cancellation and handles.

**Проверка и критерий готовности.** Тестировать full/empty, close, sender/receiver crash, stale capability, concurrent IO; zero-copy требует isolation evidence.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Security — duckos/security/*.rpr

**Текущее состояние.** Reaper modules выражают capability membership, attenuation и trust-state transitions.

**Целевая реализация.** Расширить typed registry/effect checker; DuckOS kernel broker enforce grants at runtime.

**Контракт.** Capability ID, scope, operations, generation, delegation, provenance, revocation and audit code.

**Проверка и критерий готовности.** Negative tests пытаются расширить authority, использовать unknown/stale grants и untrusted input; runtime обязан отказать.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Driver policy — duckos/drivers/*.rpr

**Текущее состояние.** Descriptor policies проверяют ABI metadata и resource/IRQ conflicts; signature verifier и loader отсутствуют.

**Целевая реализация.** Reaper владеет descriptors/policy; DuckOS — enumeration, verification, mapping, interrupt controller and isolated host.

**Контракт.** Device identity, bus, resources, IRQ, DMA, module ABI, signer and capability manifest.

**Проверка и критерий готовности.** Тестировать BAR overlap, IRQ conflicts, bad signatures, wrong architecture, dependency cycles и hot-unplug cleanup.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Supervisor — duckos/services/supervisor.rpr

**Текущее состояние.** Модель конечного restart budget не является process supervisor.

**Целевая реализация.** Lifecycle/restart policy — Reaper service manager; kernel process manager предоставляет create/terminate/wait.

**Контракт.** Service state, dependencies, readiness, backoff, restart count, crash reason and resource limits.

**Проверка и критерий готовности.** Тестировать crash loops, dependency failure, cancellation, restart storms and recovery; policy success != process started.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Storage — duckos/storage/*.rpr

**Текущее состояние.** Контракты моделируют graph refs, dependency validation and deterministic LWW merge.

**Целевая реализация.** Построить Reaper storage library поверх DuckOS VFS/journal; persistent graph и replication оформить отдельными спецификациями.

**Контракт.** Content digest, node kind, dependency set, journal generation, actor, logical clock and durable commit marker.

**Проверка и критерий готовности.** Тестировать corrupt journal, torn write, duplicate/out-of-order events and unresolved refs; LWW не называть общим CRDT.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Telemetry — duckos/system/telemetry.rpr,three_media.rpr

**Текущее состояние.** Модули классифицируют внешние samples и выбирают CPU/accelerator/node-mesh; sensor collection/GPU submission отсутствуют.

**Целевая реализация.** Reaper задаёт normalization/policy; native providers читают sensors и submit accelerator work через capabilities.

**Контракт.** Metric ID, unit, timestamp, provenance, retention, thresholds and execution target.

**Проверка и критерий готовности.** Проверить stale sample, invalid units, threshold edge and missing provider; performance claim требует hardware measurements.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### UI policy — duckos/ui/*.rpr

**Текущее состояние.** Модули моделируют theme, reduced motion and frame budget; compositor/renderer отсутствуют.

**Целевая реализация.** Оставить policy в Reaper; render backend получает canonical tokens and accessibility state.

**Контракт.** Theme tokens, motion profile, viewport, focus policy, frame budget and user preference.

**Проверка и критерий готовности.** Проверить token compatibility, contrast, motion override, frame budget and RTL/localization; renderer parity тестируется реально.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Reaper lexer — reaper/lexer.py,src/lexer.c

**Текущее состояние.** Python lexer задаёт полную текущую грамматику; C lexer является меньшим самостоятельным срезом.

**Целевая реализация.** Создать единый corpus и выровнять frontends по canonical token IDs; добавить explicit dialect and Unicode policy.

**Контракт.** Token ID, lexeme, span, trivia, dialect, encoding and diagnostic code.

**Проверка и критерий готовности.** Cross-test fixtures по Python/C; fuzz long token, Unicode, escape, invalid UTF-8 and adversarial comments.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Reaper parser — reaper/parser.py,src/parser.c,selfhost/parser.rpr

**Текущее состояние.** Python parser поддерживает более широкий синтаксис, чем partial C parser и self-host demo.

**Целевая реализация.** Формализовать grammar/AST schema; parity объявлять только после shared corpus pass.

**Контракт.** AST kind, value, span, dialect provenance, precedence and recovery.

**Проверка и критерий готовности.** Golden AST tests фиксируют эквивалентность; self-host parser не объявлять полным без всей grammar conformance.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Reaper type checker — reaper/typecheck.py

**Текущее состояние.** Консервативный checker выводит некоторые primitive/list types, проверяет arity/operators/mutability; unknown остаётся Any.

**Целевая реализация.** Добавить type definitions, generics policy, Option/Result, pointer/handle types, target layouts, effects and no-Any privileged boundary.

**Контракт.** Type identity, inference variables, coercion rules, ABI representation, errors and effect set.

**Проверка и критерий готовности.** Negative fixtures обязаны отвергать unsafe memory, capability/ownership misuse; soundness claim ограничен формальной спецификацией.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Reaper IR/VM — reaper/ir.py,reaper/vm.py

**Текущее состояние.** Canonical stack IR и bytecode VM существуют в Python alongside tree-walk runtime.

**Целевая реализация.** Зафиксировать IR edition, verifier invariants, resource lifecycle and serialized format; расширить CFG/memory/effect operations.

**Контракт.** IR version, opcode schema, typed operands, blocks, terminators, maps, effects and limits.

**Проверка и критерий готовности.** Differential compare results/errors; invalid bytecode rejected before run; resource cleanup and limits must match.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Reaper runtime — reaper/runtime.py

**Текущее состояние.** Python reference runtime исполняет широкий язык, scopes, builtins, quotas and adapters.

**Целевая реализация.** Сохранить как oracle до parity; постепенно перенести supported semantics в native VM/runtime. Kernel не зависит от CPython.

**Контракт.** Value representation, scope, stack, heap budget, steps, call depth, error semantics and effects.

**Проверка и критерий готовности.** Native route проходит differential tests по result, output, diagnostics и resource state для всего заявленного subset.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Reaper modules — reaper/modules.py

**Текущее состояние.** Loader обеспечивает .rpr, canonical resolution, import depth, UTF-8, export isolation and cycle checks.

**Целевая реализация.** Расширить module packages, dependency locks, signed metadata and interface hashes.

**Контракт.** Module ID, source digest, exports, dependency lock, visibility, target, capability and cycle rules.

**Проверка и критерий готовности.** Тестировать symlink escape, traversal, cycles, TOCTOU file change, duplicate export and ABI mismatch.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Native compiler — reaper/native_compiler.py,src/*

**Текущее состояние.** AOT subset выдаёт C17 и вызывает host GCC/Clang; native C path частичен.

**Целевая реализация.** Использовать как transitional backend; расширить typed IR, object metadata, debug symbols, target lowering and freestanding.

**Контракт.** Target triple, edition, IR version, ABI, relocations, sections, stack estimate and provenance.

**Проверка и критерий готовности.** Каждый supported feature parity-tested; unsupported fail at source location; argv-only compiler and atomic output replacement.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Reaper FFI/resources — reaper/ffi.py,resources.py,memory.py

**Текущее состояние.** Есть explicit host interop and bounded resource/heap accounting; это не kernel privilege model.

**Целевая реализация.** Разделить hosted FFI и DuckOS syscall/native module ABI; handles сделать typed/non-forgeable на OS boundary.

**Контракт.** Library identity, symbol type, convention, ownership, capability, close semantics and error state.

**Проверка и критерий готовности.** Проверить double close, invalid signature, unload in-use, revoked capability and quotas; arbitrary FFI запрещён kernel profile.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Studio/LSP/DAP

**Текущее состояние.** Studio — Windows IDE foundation; LSP/DAP дают local diagnostics/completion/debugging.

**Целевая реализация.** Добавить target-profile workspace, ownership/effect diagnostics, native symbols and kernel panic symbolization.

**Контракт.** Protocol version, workspace ID, URI, target, diagnostic code, debug session and breakpoint contract.

**Проверка и критерий готовности.** Проверить multi-file navigation, locale switching, native breakpoints, protocol errors and disconnected target.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Self-hosting — selfhost/*.rpr

**Текущее состояние.** Tokenizer/parser examples показывают направление, но не являются full compiler.

**Целевая реализация.** Расти к self-hosted lexer/parser/typechecker/IR/compiler; сохранять Stage 0 bootstrap.

**Контракт.** Bootstrap version, compiler digest, output digest, edition and toolchain lock.

**Проверка и критерий готовности.** N-stage rebuild comparison, clean-room build and signed bootstrap recovery; demo parser не считать self-hosted compiler.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Kora and standard library

**Текущее состояние.** Manifest-backed helpers дают переиспользуемые host-level utilities.

**Целевая реализация.** Определить deterministic core library, OS adapters and no_std modules; отделить pure algorithms from platform IO.

**Контракт.** Package manifest, API semver, effects, target support, limits and capabilities.

**Проверка и критерий готовности.** API compatibility, no_std build, dependency cycles, deterministic serialization and target conformance.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.

#### Build and CI across both repos

**Текущее состояние.** DuckOS checks .rpr and runs tree-walk/VM contracts; Reaper owns Python, C17 and project-contract CI.

**Целевая реализация.** Добавлять gates по мере готовности, фиксировать pins/toolchains и собирать machine-readable evidence.

**Контракт.** Commit pin, workflow inputs, compiler digest, target profile, schema set and artifact provenance.

**Проверка и критерий готовности.** Fail on pin drift, stale outputs, schema mismatch and missing evidence; write permissions ограничивать release automation.

**Правило перехода.** Старая реализация остаётся эталоном и способом восстановления до тех пор, пока новая реализация не прошла те же golden fixtures, граничные тесты, негативные сценарии и интеграционный профиль. При расхождении обе стороны блокируют продвижение релиза; нельзя исправлять тест простым удалением неудобного случая. Изменение поведения оформляется как ADR и версия контракта, а не маскируется под техническую миграцию. Диагностика должна содержать постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях должны быть разные уровни подробности, но одинаковые семантика и security invariants.


---

## Appendix B. Пример целевого Reaper-кода и статус синтаксиса

Ниже приведены концептуальные формы, иллюстрирующие требуемые свойства системного языка. Это **проектные примеры**, а не обещание, что нынешний parser/runtime принимает их. Точный синтаксис утверждается в отдельной language edition после тестов и реализации.

~~~reaper
// Концептуально: чистая политика отделена от платформенного эффекта.
craft choose_ready_task(tasks: Slice<TaskView>) -> Result<TaskId, ScheduleError>
    effect pure
{
    yield scheduler_policy::select(tasks)
}

// Capability является параметром контекста, а не строкой,
// которую код может сам себе выдать.
craft read_device_status(
    device: DeviceHandle,
    access: Capability<DeviceRead>
) -> Result<DeviceStatus, DeviceError>
    effect device.read
{
    yield platform::device::read_status(device, access)
}

// DMA lease имеет линейное владение.
craft submit_dma(buffer: DmaBuffer, queue: DmaQueue)
    -> Result<DmaTicket, DmaError>
    effect dma.submit
{
    let ticket = queue.submit(move buffer)?
    yield ticket
}
~~~

До фактической поддержки компилятором такие блоки хранятся в design examples, а не в тестах must compile. После реализации примеры переносятся в conformance corpus и закрепляются за языковой edition.

## Appendix C. Предлагаемая структура системных директорий

Ниже — ориентир для будущей source organization. Это не требование переименовать всё дерево немедленно; миграция сопровождается module map и сохранением истории.

~~~text
duckos/
  boot/
    protocol/
    stages/
    recovery/
  kernel/
    arch/
      x86_64/
      aarch64/
      riscv64/
    memory/
    scheduler/
    process/
    syscall/
    ipc/
    security/
    drivers/
    vfs/
    panic/
  services/
    init/
    supervisor/
    device-broker/
    package-manager/
    logging/
    telemetry/
    network/
    graphics/
  desktop/
    mora/
    compositor/
    input/
    accessibility/
  apps/
    first-party/
    system-tools/
  profiles/
    targets/
    capabilities/
    resource-budgets/
  contracts/
    boot/
    abi/
    ipc/
    drivers/
    packages/
  tests/
    unit/
    conformance/
    emulator/
    hardware/
~~~

Reaper repo owns reusable compiler/runtime libraries, standard library, target descriptions and SDK. DuckOS tree contains only DuckOS-specific target modules and system implementation. Shared source is not copied into both repositories; cross-repository interfaces are published as versioned schemas and packages.

## Appendix D. Required artifact types

Each release should provide: source manifest with repository commit and submodule pins; compiler/toolchain lock and digest; language edition, IR edition, target triple and ABI versions; validated system manifest; kernel/module/package inventory; build provenance and dependency SBOM; checksums for every binary component; signature envelope and verification result; linker map, section report and stack-use report; conformance summary separating host, VM, native, emulator and hardware; known limitations and recovery instructions; reproducible build command and environment profile.

The public release page must state which target was built, where it was executed, which subsystems were hardware-tested, and which features remain partial. A successful build on a developer workstation does not prove the image boots on physical hardware.

## Appendix E. Review checklist for each cross-repository PR

1. Does the change affect Reaper language semantics, DuckOS semantics, both, or only documentation?
2. Is the contract owner identified?
3. Are source commit and dependency pin explicit?
4. Are schema, ABI and language edition versions recorded?
5. Are both repositories' tests or validators required by the change run?
6. Does the change preserve previous behavior or supply a migration?
7. Are capability and privilege implications reviewed?
8. Are input bounds and resource budgets present?
9. Are unsupported states reported as unsupported rather than guessed?
10. Can a failed update be rolled back?
11. Does documentation match source and tests?
12. Are new examples actually supported by implementation?
13. Are generated outputs deterministic?
14. Are licenses and upstream attribution preserved?
15. Is the pull request narrow enough to review?

## Appendix F. Minimum issue decomposition for the first implementation wave

The first wave should not attempt the physical kernel. It should deliver a reliable and synchronized contract baseline: reconcile DuckOS architecture/foundation documents; create one system-capability inventory with maturity/evidence; formalize the current .rpr subset used by every DuckOS module; add cross-runtime golden fixtures for policy modules; add a Reaper DuckOS target-profile manifest and validator; make DuckOS CI verify its checked-out Reaper pin against federation metadata; add a machine-readable report showing interpreter/VM coverage; document all remaining Python/JavaScript/C ownership boundaries; define the first x86_64 target ADR; define the first kernel ABI and module descriptor ADR; make no production claim about native kernel execution until the relevant target exists.

The second wave may begin type/effect/ownership additions in Reaper. The third wave may expand native compilation. Only then should DuckOS begin moving boot-critical code to the new native target. This ordering reduces the risk of writing large quantities of OS code against an unstable compiler and later rewriting it when the type system or ABI changes.

## Appendix G. Rollback and deprecation policy

A legacy module may be removed only when a named replacement exists; replacement covers the documented feature surface; all inputs and outputs are contract-equivalent or migrated explicitly; CI exercises replacement; old data and configuration have a migration path; recovery instructions exist; downstream consumers have been identified; and a deprecation period appropriate to the interface has elapsed.

For Python modules, deprecation is staged: freeze feature additions; publish Reaper replacement API; run shadow comparison; switch non-critical callers; switch build tooling; switch system-image build; remove from production runtime; retain offline recovery tool if needed. A Python script retained solely for developers must not be imported by runtime services.

For browser JavaScript, deprecation is different: event/render adapter code may remain because browser APIs are JavaScript-facing. Only duplicated domain policy and authoritative state are removed. HTML/CSS assets are not unmigrated system logic.

For C and assembly, deprecation is based on native Reaper target coverage and auditability. Architecture entry, atomic intrinsics and low-level register operations may remain permanently as tiny platform-specific boundary units. Every exception has a stable API and security review.

## Appendix H. Required non-goals

This initiative does not turn Reaper into a DuckOS-only language; embed arbitrary CPython into the kernel; grant source code direct kernel, physical memory or device access; claim that generating C17 equals native systems compiler parity; execute PE/ELF binaries merely because they can be parsed; treat a valid manifest as a verified signature; let browser Mora launch host programs; collapse all federated repositories into one repository; advance submodule pins without review; rewrite every file line-by-line without behavioral inventory; remove fallback tooling before reproducible replacement; claim hard real-time properties without worst-case evidence; equate a reference-runtime test with boot, driver, graphics or hardware proof.

## Appendix I. Final operating model

After migration, the normal development loop is:

1. A developer edits Reaper modules for a DuckOS target profile.
2. Reaper Studio/LSP provides language, type, effect, ownership and target diagnostics.
3. Reaper validates imports, capabilities, resource budgets and target restrictions.
4. Native compiler emits deterministic target objects with debug/source metadata.
5. DuckOS SDK links objects against versioned kernel/service ABI and validated system libraries.
6. System packager creates a signed component bundle and bootable image.
7. Emulator tests exercise boot, syscalls, memory, IPC, service lifecycle and recovery.
8. Qualified hardware tests verify real devices and performance.
9. Runtime diagnostics report kernel/service/compiler/ABI versions and evidence.
10. Release metadata preserves source pins, toolchain digest, tests, signatures and recovery method.

Reaper remains useful on any supported host or target even when DuckOS is not installed. DuckOS remains a coherent OS repository and consumes Reaper through pinned SDK/toolchain and contracts. This is the desired relationship: one language platform, one operating-system implementation, explicit interfaces, independent release cycles and jointly validated integration.

## Appendix J. Release engineering notes for component cards

Для каждой карточки выше release owner обязан зафиксировать source revision, schema edition, target profile, build environment, dependency closure и результат проверок. В отчёте перечисляются положительные сценарии, граничные значения, негативные случаи, ошибки ресурсов и процедуры восстановления. Переход к следующему этапу разрешается только после достижения заявленного уровня зрелости и независимого evidence. При обновлении зависимостей нельзя автоматически изменять внешний ABI. Изменение API оформляется новой версией и migration tooling. Все операции с файлами и системными ресурсами выполняются в заранее определённой области; ошибочный input не должен оставлять частично записанный результат. Диагностика содержит постоянный code, severity, source location или объектную идентичность, рекомендуемое действие и execution mode. Для компонентов, работающих с данными пользователя, отчёт не раскрывает секреты, приватные ключи и исходные аппаратные идентификаторы. В debug и production профилях могут различаться уровни подробности, но не семантика и security invariants.


## Appendix J.1. Component-specific release gates

### J.1. DuckOS CLI — duckos/cli.py: отдельный release gate

Релизная проверка для DuckOS CLI — duckos/cli.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Python dispatcher вызывает manifest validation, image planning, hardware inventory, compatibility inspection, DuckBridge, desktop tools и Reaper workbench. Целевой переход: Перенести семантику команд и argument contracts в Reaper CLI modules; временный Python launcher оставить только для bootstrap до native executable. Контракт: Stable command IDs, typed argument schemas, JSON result schema, exit codes, path limits, output mode and explicit execution mode. Критерий проверки: Проверить help, malformed arguments, invalid paths, deterministic output, exit codes, timeouts и equivalence reference/native. Native CLI не должен молча откатываться к Python. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.2. Deployment — duckos/deployment.py: отдельный release gate

Релизная проверка для Deployment — duckos/deployment.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Python создаёт component bundles, проверяет digest, поддерживает optional signing и выдаёт dry-run deployment plans. Целевой переход: Перенести policy, manifest transforms и orchestration в Reaper; OpenSSL/archiver/firmware tools оставить явными host adapters до появления проверенного эквивалента. Контракт: Versioned release manifest, canonical paths, bounded archive handling, SHA-256 inventory, Ed25519 envelope, target and rollback metadata. Критерий проверки: Проверить traversal, duplicate paths, symlink entries, source mutation, expanded-size limit, signature failure, interrupted staging и сохранность предыдущего artifact. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.3. System manifest — duckos/manifest.py: отдельный release gate

Релизная проверка для System manifest — duckos/manifest.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Python validator проверяет обязательные bootloader/kernel/initramfs/rootfs, canonical relative paths, byte lengths и SHA-256. Целевой переход: Сделать schema и validator семантику частью Reaper standard library и DuckOS build modules; JSON Schema оставить как interchange artifact. Контракт: Exact fields, schema version, canonical paths, size limits, supported architectures, kernel ABI, unique component names and digest semantics. Критерий проверки: Один valid/invalid corpus должен работать одинаково на legacy validator, interpreter, VM и native compiler; отдельно тестировать traversal и integer overflow. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.4. Driver ABI — duckos/module_abi.py: отдельный release gate

Релизная проверка для Driver ABI — duckos/module_abi.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Python проверяет descriptor shape, architecture, kernel ABI, dependencies and capability IDs; module loading не выполняется. Целевой переход: Перенести descriptor semantics в Reaper; loader mechanism оставить в kernel и target relocation adapter. Контракт: Manifest schema, module identity, semantic version, target ABI, imports/exports, dependency graph, capabilities, memory budget and trust evidence. Критерий проверки: Проверить duplicate modules, missing dependencies, cycles, architecture mismatch, ABI mismatch, capability escalation and deterministic load order. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.5. PE parser — duckos/compat/pe.py: отдельный release gate

Релизная проверка для PE parser — duckos/compat/pe.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Bounded PE32/PE32+ header, section and import inspection выполняются read-only. Целевой переход: Портировать parser в Reaper bounded binary-reader library; byte access — explicit file-read effect; сохранить общие fixtures. Контракт: Byte order, bounds, machine IDs, header variants, RVA mapping, section count and import directory semantics. Критерий проверки: Fuzz truncated headers, overflowed offsets, overlapping sections, invalid counts, malformed strings и большие файлы; audit не запускает target. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.6. Compatibility prefix — duckos/compat/prefix.py: отдельный release gate

Релизная проверка для Compatibility prefix — duckos/compat/prefix.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Создаёт и проверяет изолированные prefix directories; это подготовка среды, не Windows runtime. Целевой переход: Перенести prefix policy и manifest migration в Reaper; directory mutation — через scoped filesystem API с approval/rollback. Контракт: Prefix schema, canonical root, architecture, app identity, ownership, path policy, runtime and data directories. Критерий проверки: Проверить symlink/junction/reparse point, traversal, casefold collisions, stale lock, partial creation and manifest corruption. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.7. DuckBridge discovery — duckos/compat/bridge.py: отдельный release gate

Релизная проверка для DuckBridge discovery — duckos/compat/bridge.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Python обнаруживает Wine, Proton, CrossOver, Bottles, Box64 и QEMU entrypoints и формирует argv launch plans без исполнения. Целевой переход: Перенести discovery policy/backend selection в Reaper; executable discovery оставить restricted platform provider; process creation — отдельная capability. Контракт: Runtime inventory schema, executable evidence, target architecture, formats, environment allowlist and plan status. Критерий проверки: Проверить missing tools, non-executable paths, Flatpak wrapper, multiple Proton candidates и hostile PATH; discovery не запускает программу. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.8. Compatibility diagnosis — duckos/compat/runtime.py: отдельный release gate

Релизная проверка для Compatibility diagnosis — duckos/compat/runtime.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Диагностика исследует imports, prefix paths и architecture mismatch; native NT/Win32 runtime помечен unavailable. Целевой переход: Перенести semantic analysis в Reaper и добавить provider interface readiness. Сохранять inspectable_not_runnable до настоящего runtime. Контракт: Structured blockers, missing imports, architecture comparison, prefix selection and launch-performed state. Критерий проверки: Любой отсутствующий компонент должен блокировать запуск; report не может быть runnable без process manager, image loader, API, ABI и sandbox. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.9. Hardware inventory — duckos/hardware_inventory.py: отдельный release gate

Релизная проверка для Hardware inventory — duckos/hardware_inventory.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: DuckOS собирает read-only PCI/USB или Windows PnP inventory и JSON с privacy-preserving identity hashes. Целевой переход: Сделать data model и validation Reaper-native; platform enumeration — provider с явным read-only system effect. Контракт: Inventory schema, device identity, bus, source provider, platform, architecture, driver status, count and digest rules. Критерий проверки: Проверить provider absence, unreadable nodes, duplicate IDs, stale data, privacy leakage и digest/count mismatch; запрещено менять драйвер. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.10. Image layout — duckos/image_layout.py: отдельный release gate

Релизная проверка для Image layout — duckos/image_layout.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Planner считает aligned, non-overlapping image regions и выдаёт metadata; диск не записывается. Целевой переход: Перенести layout arithmetic в Reaper pure policy; будущий writer сделать отдельным privileged installer service. Контракт: Byte offsets, exclusive end, alignment, sectors, image size, partition roles and checked arithmetic. Критерий проверки: Property tests доказывают alignment, bounds and non-overlap; тестировать extreme sizes, overflow и invalid alignment. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.11. Duck Desktop UI — duckos/desktop/native_ui.py: отдельный release gate

Релизная проверка для Duck Desktop UI — duckos/desktop/native_ui.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Tk user-space window and tabs предоставляют maintenance controls; это не production compositor. Целевой переход: Перенести state, command orchestration и validation в Reaper services; Tk может остаться временным host GUI adapter. Контракт: Typed command request/reply, asynchronous job states, cancellation, progress, UI capability gating and diagnostic envelope. Критерий проверки: Проверить responsiveness, cancellation, disabled privileged actions без broker support и единый authorization path. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.12. Desktop service — duckos/desktop/service.py: отдельный release gate

Релизная проверка для Desktop service — duckos/desktop/service.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Python координирует read-only audits, cleanup hints и reversible user-level actions; некоторые операции меняют user startup settings. Целевой переход: Перенести policy и transaction plans в Reaper; platform mutations делегировать narrow services с backup-before-change и rollback. Контракт: Operation manifest, before/after snapshot, user scope, confirmation, backup path, rollback token and report. Критерий проверки: Windows/Linux adapters тестировать отдельно; проверить отсутствие несанкционированного удаления, privilege escalation и точного восстановления. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.13. Reaper launcher — duckos/desktop/reaper.py: отдельный release gate

Релизная проверка для Reaper launcher — duckos/desktop/reaper.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Bridge запускает pinned Reaper Python CLI отдельным процессом, argv, shell=False, timeout и output limit. Целевой переход: Сохранить process isolation; заменить entrypoint на verified native Reaper executable лишь после native host compiler milestone. Контракт: Repository discovery, version negotiation, argument allowlist, regular source validation, output caps, timeout and JSON result. Критерий проверки: Проверить invalid checkout, stale pin, symlink source, invalid suffix, output overflow, timeout and child exit; никакого shell parsing или implicit FFI. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.14. Extended Terminal — duckos/terminal/service.py: отдельный release gate

Релизная проверка для Extended Terminal — duckos/terminal/service.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Python реализует command registry, argument validation и bounded history; полномочия ограничены. Целевой переход: Перенести parser, registry, policy и state machine в Reaper. External commands отключены без отдельной process capability. Контракт: Command ID, typed parameters, allowlist, environment, history bounds, redaction and effects. Критерий проверки: Проверить injection, unknown command, malformed option, history overflow, secret redaction и отказ process execution. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.15. Mora core — mora/core.js: отдельный release gate

Релизная проверка для Mora core — mora/core.js не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Browser-local core обрабатывает app metadata, actions и часть общей shell logic. Целевой переход: Перенести canonical domain model/action validation в Reaper; JavaScript оставить event/render adapter или generated WASM glue. Контракт: App identity, command schema, preferences, shell state, event names and API result envelope. Критерий проверки: Одинаковые сценарии старого JS и Reaper сравниваются на migration period; тестировать offline, malformed storage и state migration. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.16. Mora app — mora/app.js: отдельный release gate

Релизная проверка для Mora app — mora/app.js не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Большой browser application script связывает launcher, panels, tools and local interactions. Целевой переход: Разложить на per-app Reaper modules и shared contracts; не переводить монолит line-by-line. Контракт: Application manifest, state owner, lifecycle, command handler, input schema, localization, capabilities and persistence namespace. Критерий проверки: Проверить каждое приложение, navigation, restart, denied permission, responsive viewport and keyboard-only workflows. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.17. Mora Commons — mora/commons-catalog.js: отдельный release gate

Релизная проверка для Mora Commons — mora/commons-catalog.js не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Каталог и discovery helpers живут в локальном frontend и отделены от native package services. Целевой переход: Сделать canonical schema и discovery logic Reaper-owned; JSON сохранить как portable data/interchange format. Контракт: Stable IDs, provider, category, version, maturity, required service, permissions, install source and localized metadata. Критерий проверки: Validator отвергает duplicate IDs, undeclared permissions, unknown providers and unsupported maturity; catalog != installed app. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.18. Mora service worker: отдельный release gate

Релизная проверка для Mora service worker не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Service worker кэширует static shell assets в ограниченной browser scope. Целевой переход: Оставить небольшой browser-owned worker; Reaper формирует cache policy и immutable asset manifest. Контракт: Cache namespace version, asset digest, scope, eviction and offline fallback. Критерий проверки: Проверить scope, stale cache cleanup, offline shell, upgrade rollback and absence of secret/token storage. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.19. Boot info C — foundation/boot_info.c,h: отдельный release gate

Релизная проверка для Boot info C — foundation/boot_info.c,h не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: C представляет и валидирует ранний handoff до готовности freestanding Reaper. Целевой переход: Сохранить minimal audited C/assembly boundary до появления Reaper entry; Reaper определяет canonical schema и verifier. Контракт: Fixed-width fields, memory map count/stride, version, framebuffer, initramfs range, checksum and reserved-field policy. Критерий проверки: C и Reaper validators читают одни golden binary fixtures; тестировать unaligned/truncated/unsupported/overflow. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.20. Kernel boot — duckos/kernel/boot.rpr: отдельный release gate

Релизная проверка для Kernel boot — duckos/kernel/boot.rpr не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Reaper source проверяет startup phase order and transitions. Целевой переход: Оставить policy в Reaper; firmware calls, CPU mode and early stack — target-specific mechanisms. Контракт: Phase enum, transition graph, failure state, recovery route and boot events. Критерий проверки: Tree-walk, VM and native target используют одинаковые valid/invalid transition tests; emulator trace нужен для native claim. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.21. Memory and arena — duckos/kernel/memory.rpr,arena.rpr: отдельный release gate

Релизная проверка для Memory and arena — duckos/kernel/memory.rpr,arena.rpr не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Контракты моделируют signed ranges, 64-byte arena generation и SoA sizing, не physical allocator. Целевой переход: Расширить Reaper types/backend для physical/virtual addresses, page alignment and ownership; allocator/page table реализует kernel. Контракт: Half-open range, page size, permissions, memory class, generation, budget and mapping lease. Критерий проверки: Проверить overflow, address boundary, double release, stale generation, overlap and alignment; physical mapping требует emulator evidence. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.22. Scheduler — duckos/kernel/scheduler.rpr,flock.rpr: отдельный release gate

Релизная проверка для Scheduler — duckos/kernel/scheduler.rpr,flock.rpr не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Policies выбирают priority/deadline и least-loaded worker детерминированно. Целевой переход: Сохранить policy как Reaper pure code; kernel реализует queue synchronization, timer preemption, context switch and affinity. Контракт: Task state, priority, deadline, load/capacity, affinity, budget, starvation and wake reason. Критерий проверки: Property tests фиксируют детерминизм; emulator tests измеряют реальные переключения, wakeup и отсутствие потери задач. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.23. IPC — duckos/kernel/ipc.rpr,zero_copy_bus.rpr: отдельный release gate

Релизная проверка для IPC — duckos/kernel/ipc.rpr,zero_copy_bus.rpr не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Контракты проверяют bounded queues, byte accounting and backpressure; shared memory ещё не mapped. Целевой переход: Reaper владеет API и state machine; kernel — synchronization, wakeup, process validation and page mapping. Контракт: Message version, queue cap, max bytes, sequence, identity, backpressure, cancellation and handles. Критерий проверки: Тестировать full/empty, close, sender/receiver crash, stale capability, concurrent IO; zero-copy требует isolation evidence. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.24. Security — duckos/security/*.rpr: отдельный release gate

Релизная проверка для Security — duckos/security/*.rpr не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Reaper modules выражают capability membership, attenuation и trust-state transitions. Целевой переход: Расширить typed registry/effect checker; DuckOS kernel broker enforce grants at runtime. Контракт: Capability ID, scope, operations, generation, delegation, provenance, revocation and audit code. Критерий проверки: Negative tests пытаются расширить authority, использовать unknown/stale grants и untrusted input; runtime обязан отказать. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.25. Driver policy — duckos/drivers/*.rpr: отдельный release gate

Релизная проверка для Driver policy — duckos/drivers/*.rpr не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Descriptor policies проверяют ABI metadata и resource/IRQ conflicts; signature verifier и loader отсутствуют. Целевой переход: Reaper владеет descriptors/policy; DuckOS — enumeration, verification, mapping, interrupt controller and isolated host. Контракт: Device identity, bus, resources, IRQ, DMA, module ABI, signer and capability manifest. Критерий проверки: Тестировать BAR overlap, IRQ conflicts, bad signatures, wrong architecture, dependency cycles и hot-unplug cleanup. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.26. Supervisor — duckos/services/supervisor.rpr: отдельный release gate

Релизная проверка для Supervisor — duckos/services/supervisor.rpr не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Модель конечного restart budget не является process supervisor. Целевой переход: Lifecycle/restart policy — Reaper service manager; kernel process manager предоставляет create/terminate/wait. Контракт: Service state, dependencies, readiness, backoff, restart count, crash reason and resource limits. Критерий проверки: Тестировать crash loops, dependency failure, cancellation, restart storms and recovery; policy success != process started. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.27. Storage — duckos/storage/*.rpr: отдельный release gate

Релизная проверка для Storage — duckos/storage/*.rpr не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Контракты моделируют graph refs, dependency validation and deterministic LWW merge. Целевой переход: Построить Reaper storage library поверх DuckOS VFS/journal; persistent graph и replication оформить отдельными спецификациями. Контракт: Content digest, node kind, dependency set, journal generation, actor, logical clock and durable commit marker. Критерий проверки: Тестировать corrupt journal, torn write, duplicate/out-of-order events and unresolved refs; LWW не называть общим CRDT. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.28. Telemetry — duckos/system/telemetry.rpr,three_media.rpr: отдельный release gate

Релизная проверка для Telemetry — duckos/system/telemetry.rpr,three_media.rpr не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Модули классифицируют внешние samples и выбирают CPU/accelerator/node-mesh; sensor collection/GPU submission отсутствуют. Целевой переход: Reaper задаёт normalization/policy; native providers читают sensors и submit accelerator work через capabilities. Контракт: Metric ID, unit, timestamp, provenance, retention, thresholds and execution target. Критерий проверки: Проверить stale sample, invalid units, threshold edge and missing provider; performance claim требует hardware measurements. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.29. UI policy — duckos/ui/*.rpr: отдельный release gate

Релизная проверка для UI policy — duckos/ui/*.rpr не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Модули моделируют theme, reduced motion and frame budget; compositor/renderer отсутствуют. Целевой переход: Оставить policy в Reaper; render backend получает canonical tokens and accessibility state. Контракт: Theme tokens, motion profile, viewport, focus policy, frame budget and user preference. Критерий проверки: Проверить token compatibility, contrast, motion override, frame budget and RTL/localization; renderer parity тестируется реально. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.30. Reaper lexer — reaper/lexer.py,src/lexer.c: отдельный release gate

Релизная проверка для Reaper lexer — reaper/lexer.py,src/lexer.c не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Python lexer задаёт полную текущую грамматику; C lexer является меньшим самостоятельным срезом. Целевой переход: Создать единый corpus и выровнять frontends по canonical token IDs; добавить explicit dialect and Unicode policy. Контракт: Token ID, lexeme, span, trivia, dialect, encoding and diagnostic code. Критерий проверки: Cross-test fixtures по Python/C; fuzz long token, Unicode, escape, invalid UTF-8 and adversarial comments. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.31. Reaper parser — reaper/parser.py,src/parser.c,selfhost/parser.rpr: отдельный release gate

Релизная проверка для Reaper parser — reaper/parser.py,src/parser.c,selfhost/parser.rpr не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Python parser поддерживает более широкий синтаксис, чем partial C parser и self-host demo. Целевой переход: Формализовать grammar/AST schema; parity объявлять только после shared corpus pass. Контракт: AST kind, value, span, dialect provenance, precedence and recovery. Критерий проверки: Golden AST tests фиксируют эквивалентность; self-host parser не объявлять полным без всей grammar conformance. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.32. Reaper type checker — reaper/typecheck.py: отдельный release gate

Релизная проверка для Reaper type checker — reaper/typecheck.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Консервативный checker выводит некоторые primitive/list types, проверяет arity/operators/mutability; unknown остаётся Any. Целевой переход: Добавить type definitions, generics policy, Option/Result, pointer/handle types, target layouts, effects and no-Any privileged boundary. Контракт: Type identity, inference variables, coercion rules, ABI representation, errors and effect set. Критерий проверки: Negative fixtures обязаны отвергать unsafe memory, capability/ownership misuse; soundness claim ограничен формальной спецификацией. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.33. Reaper IR/VM — reaper/ir.py,reaper/vm.py: отдельный release gate

Релизная проверка для Reaper IR/VM — reaper/ir.py,reaper/vm.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Canonical stack IR и bytecode VM существуют в Python alongside tree-walk runtime. Целевой переход: Зафиксировать IR edition, verifier invariants, resource lifecycle and serialized format; расширить CFG/memory/effect operations. Контракт: IR version, opcode schema, typed operands, blocks, terminators, maps, effects and limits. Критерий проверки: Differential compare results/errors; invalid bytecode rejected before run; resource cleanup and limits must match. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.34. Reaper runtime — reaper/runtime.py: отдельный release gate

Релизная проверка для Reaper runtime — reaper/runtime.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Python reference runtime исполняет широкий язык, scopes, builtins, quotas and adapters. Целевой переход: Сохранить как oracle до parity; постепенно перенести supported semantics в native VM/runtime. Kernel не зависит от CPython. Контракт: Value representation, scope, stack, heap budget, steps, call depth, error semantics and effects. Критерий проверки: Native route проходит differential tests по result, output, diagnostics и resource state для всего заявленного subset. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.35. Reaper modules — reaper/modules.py: отдельный release gate

Релизная проверка для Reaper modules — reaper/modules.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Loader обеспечивает .rpr, canonical resolution, import depth, UTF-8, export isolation and cycle checks. Целевой переход: Расширить module packages, dependency locks, signed metadata and interface hashes. Контракт: Module ID, source digest, exports, dependency lock, visibility, target, capability and cycle rules. Критерий проверки: Тестировать symlink escape, traversal, cycles, TOCTOU file change, duplicate export and ABI mismatch. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.36. Native compiler — reaper/native_compiler.py,src/*: отдельный release gate

Релизная проверка для Native compiler — reaper/native_compiler.py,src/* не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: AOT subset выдаёт C17 и вызывает host GCC/Clang; native C path частичен. Целевой переход: Использовать как transitional backend; расширить typed IR, object metadata, debug symbols, target lowering and freestanding. Контракт: Target triple, edition, IR version, ABI, relocations, sections, stack estimate and provenance. Критерий проверки: Каждый supported feature parity-tested; unsupported fail at source location; argv-only compiler and atomic output replacement. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.37. Reaper FFI/resources — reaper/ffi.py,resources.py,memory.py: отдельный release gate

Релизная проверка для Reaper FFI/resources — reaper/ffi.py,resources.py,memory.py не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Есть explicit host interop and bounded resource/heap accounting; это не kernel privilege model. Целевой переход: Разделить hosted FFI и DuckOS syscall/native module ABI; handles сделать typed/non-forgeable на OS boundary. Контракт: Library identity, symbol type, convention, ownership, capability, close semantics and error state. Критерий проверки: Проверить double close, invalid signature, unload in-use, revoked capability and quotas; arbitrary FFI запрещён kernel profile. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.38. Studio/LSP/DAP: отдельный release gate

Релизная проверка для Studio/LSP/DAP не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Studio — Windows IDE foundation; LSP/DAP дают local diagnostics/completion/debugging. Целевой переход: Добавить target-profile workspace, ownership/effect diagnostics, native symbols and kernel panic symbolization. Контракт: Protocol version, workspace ID, URI, target, diagnostic code, debug session and breakpoint contract. Критерий проверки: Проверить multi-file navigation, locale switching, native breakpoints, protocol errors and disconnected target. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.39. Self-hosting — selfhost/*.rpr: отдельный release gate

Релизная проверка для Self-hosting — selfhost/*.rpr не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Tokenizer/parser examples показывают направление, но не являются full compiler. Целевой переход: Расти к self-hosted lexer/parser/typechecker/IR/compiler; сохранять Stage 0 bootstrap. Контракт: Bootstrap version, compiler digest, output digest, edition and toolchain lock. Критерий проверки: N-stage rebuild comparison, clean-room build and signed bootstrap recovery; demo parser не считать self-hosted compiler. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.40. Kora and standard library: отдельный release gate

Релизная проверка для Kora and standard library не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: Manifest-backed helpers дают переиспользуемые host-level utilities. Целевой переход: Определить deterministic core library, OS adapters and no_std modules; отделить pure algorithms from platform IO. Контракт: Package manifest, API semver, effects, target support, limits and capabilities. Критерий проверки: API compatibility, no_std build, dependency cycles, deterministic serialization and target conformance. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

### J.41. Build and CI across both repos: отдельный release gate

Релизная проверка для Build and CI across both repos не ограничивается успешной компиляцией. Тестовый профиль должен фиксировать поведение на корректном вводе, пустом вводе, верхней границе, некорректной схеме, истёкшем handle, превышенном лимите и недоступном provider. Текущее состояние: DuckOS checks .rpr and runs tree-walk/VM contracts; Reaper owns Python, C17 and project-contract CI. Целевой переход: Добавлять gates по мере готовности, фиксировать pins/toolchains и собирать machine-readable evidence. Контракт: Commit pin, workflow inputs, compiler digest, target profile, schema set and artifact provenance. Критерий проверки: Fail on pin drift, stale outputs, schema mismatch and missing evidence; write permissions ограничивать release automation. Компонент считается интегрированным только когда его вызывающая сторона и принимающая сторона используют одну версию контракта, ошибки имеют стабильный код, версии можно диагностировать, а отказ не оставляет частично изменённое состояние. В release evidence сохраняются commit SHA, целевой профиль, toolchain digest, тестовый отчёт и известные ограничения. Изменение статуса с partial на implemented требует исходной реализации, а не только схемы или README. Изменение implemented на qualified требует emulator или hardware evidence в зависимости от области. Никакая карточка не может сама повысить зрелость соседней подсистемы.

