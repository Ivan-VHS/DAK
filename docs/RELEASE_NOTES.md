# DuckOS 0.1.0-rc.1

Дата сборки: 22 ноября 2026.

## Вошло в поставку

- Desktop shell preview с тёмной стеклянной темой, холодным голубым свечением, адаптивной сеткой и центральным Duck Assist emblem.
- Навигация, быстрый поиск по Ctrl+K, модальные карточки приложений, dock, уведомления, переключатели Wi-Fi/Bluetooth demo, тема и Reduce Motion.
- Federation через четыре Git submodules с закреплением конкретных upstream commits в git tree.
- 17 CLI-команд пользовательского уровня, включая system/process diagnostics, mmap, filesystem diff, safe process dump, mount audit и атомарную запись.
- Unit tests для безопасной записи, diff, snapshot и маскирования аргументов.
- GitHub Actions CI и документы о границах функций и безопасности.

## Известные ограничения

- UI preview работает в браузере и не является нативным compositor или desktop session.
- Dashboard telemetry — статическая демонстрация, не реальные датчики.
- Linux-команды используют /proc, /sys и inotify; системная поддержка вне Linux ограничена и явно диагностируется.
- Нет ядра, bootloader, installer ISO, native GPU driver, package manager, login manager или sandbox для приложений.
- Интеграционные карточки открывают описание проекта; запуск приложений через host session manager появится после IPC/app-manifest слоя.

## Проверка перед stable

Сначала дождаться результата CI, затем проверить submodules clone, запустить все CLI-тесты и проверить интерфейс на Linux и Windows. Не публиковать stable/ISO до появления загрузочного слоя и security review.
