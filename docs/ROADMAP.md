# Дорожная карта DuckOS

## 0.1.0-rc.1 — пользовательская основа

- [x] Визуальная система по предоставленным референсам
- [x] Desktop shell preview и базовые интеракции
- [x] Git submodules для четырёх проектов Ivan-VHS
- [x] Каталог системных CLI-инструментов
- [x] Linux read-only collectors и файловые инструменты
- [x] Тесты и CI

## 0.1.x — укрепление пользовательского слоя

- [ ] Реальный backend телеметрии через ограниченный локальный агент
- [ ] JSON manifests для запуска федеративных приложений
- [ ] IPC контракт с проверкой версии и полномочий
- [ ] Полноценные интеграционные тесты на Windows и Linux
- [ ] Accessibility audit: keyboard-only, screen reader, контраст
- [ ] Подписанные release assets и SBOM

## 0.2.x — Linux session prototype

- [ ] Нативный session manager и compositor spike
- [ ] App lifecycle, focus, workspaces, clipboard permissions
- [ ] Permission broker и журналы чувствительных действий
- [ ] Package format, install/uninstall transaction, rollback
- [ ] Системные настройки через явные backend adapters

## 0.3.x — системная интеграция

- [ ] IPC между shell и системными сервисами
- [ ] Реальные GPU/storage/network telemetry adapters
- [ ] User service supervisor и health reporting
- [ ] Snapshot/restore настроек и состояния сессии
- [ ] Интеграционные сценарии для Pytyliki, Reaper, OPlague и VentuSample

## До заявления о готовой ОС

- [ ] Bootloader и образ загрузки
- [ ] Ядро/выбранная Linux base system и пакетная политика
- [ ] Init, login/session management и recovery
- [ ] Подписанные системные обновления и rollback
- [ ] Security review, threat model, hardware matrix
- [ ] Установка на чистую виртуальную машину и физическое тестовое устройство

Переход между этапами допускается только после прохождения тестов. Наличие пункта в дорожной карте не означает, что он уже реализован.
