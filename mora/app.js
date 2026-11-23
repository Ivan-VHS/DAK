import { MORA_COMMONS_APPS, MORA_COMMONS_CATEGORIES, filterCommonsApps } from "./commons-catalog.js";

import {
  RECOVERY_KEY,
  buildIntentPlan,
  createRecoverySnapshot,
  hashFile,
  inspectExecutable,
  loadPreferences,
  normalizePreferences,
  savePreferences,
  validateRecoverySnapshot
} from "./core.js";

const appDefinitions = {
  cockos: { name: "Cockos", subtitle: "Звук и запись", color: "#BDA27D", glyph: "∿" },
  kavun: { name: "Kavun", subtitle: "Фотографии", color: "#AF806B", glyph: "◒" },
  kabon: { name: "Ka-bon", subtitle: "Финансы", color: "#D58B3D", glyph: "₴" },
  gloverty: { name: "Gloverty", subtitle: "Сценарии", color: "#A78A8A", glyph: "ϟ" },
  po: { name: "Po", subtitle: "Компас", color: "#AAA18A", glyph: "⌖" },
  illidia: { name: "Illidia", subtitle: "Игры", color: "#82916F", glyph: "⌘" },
  unify: { name: "Unify", subtitle: "Устройства", color: "#7C9387", glyph: "∞" },
  sestem: { name: "Sestem", subtitle: "Статус системы", color: "#D2AA65", glyph: "♟" },
  setupup: { name: "SetupUP", subtitle: "Первичная настройка", color: "#B9C6A5", glyph: "✳" },
  orriganize: { name: "Orriganize", subtitle: "Задачи и проекты", color: "#C5A4A0", glyph: "▦" },
  abriganza: { name: "Abriganza", subtitle: "Архивы и файлы", color: "#C5B58C", glyph: "▤" },
  olaab: { name: "Olaab", subtitle: "Медиатека", color: "#9EB7B2", glyph: "◈" },
  "concrete-thump": { name: "Concrete Thump", subtitle: "Ритм и темп", color: "#D4A26F", glyph: "♫" },
  "seu-beu": { name: "Seu-Beu", subtitle: "Проверка обмена", color: "#A6B6A0", glyph: "◇" },
  "love-il": { name: "Love-IL", subtitle: "Личный дневник", color: "#C49BAE", glyph: "♡" },
  poi: { name: "Poi", subtitle: "Быстрые заметки", color: "#B7B2D2", glyph: "⌖" },
  "poi-2": { name: "Poi-2", subtitle: "База знаний", color: "#A5B5C8", glyph: "▧" },
  "po-2": { name: "Po-2", subtitle: "Маршруты и точки", color: "#A9B6A0", glyph: "➤" },
  gamecharager: { name: "GameCharager", subtitle: "Игровая библиотека", color: "#BBA77D", glyph: "▣" },
  exedotexe: { name: "EXEdotEXE", subtitle: "EXE-инспектор", color: "#A7AAB7", glyph: "E" },
  "mora-ai": { name: "Mora AI", subtitle: "Намерения и планы", color: "#C19A6A", glyph: "✦" },
  security: { name: "Sentinel", subtitle: "Права и доверие", color: "#829078", glyph: "◇" },
  updates: { name: "Restore", subtitle: "Обновления и откат", color: "#A97866", glyph: "↶" },
  runtime: { name: "Bridge", subtitle: "Windows compatibility", color: "#948F7D", glyph: "⇄" },
  workspace: { name: "Control", subtitle: "Среда и питание", color: "#A08B98", glyph: "⌘" },
  provenance: { name: "Proof", subtitle: "Файлы и SHA-256", color: "#8A8A76", glyph: "⌁" },
  "mora-boost": { name: "Mora Boost", subtitle: "Игровая производительность", color: "#A6A17D", glyph: "⚡" },
  desktop: { name: "Duck Desktop", subtitle: "Оптимизация рабочего пространства", color: "#FFD400", glyph: "▦" },
  "mora-commons": { name: "Mora Commons", subtitle: "Единый центр приложений", color: "#D58B3D", glyph: "✣" }
};

const windowLayer = document.getElementById("window-layer");
const activeAppLabel = document.getElementById("active-app");
const toastElement = document.getElementById("toast");
let nextZIndex = 10;
let toastTimeout = null;


let preferences = loadPreferences();
let pendingIntentPlan = null;

function applyPreferences() {
  document.documentElement.classList.toggle("reduce-motion", preferences.appearance.reducedMotion);
  document.documentElement.dataset.theme = preferences.appearance.theme;
  document.body.classList.toggle("focus-mode", preferences.focusMode);
  document.documentElement.dataset.powerProfile = preferences.powerProfile;

  const themeButton = document.querySelector('[data-action="toggle-theme"]');
  if (themeButton) {
    const currentTheme = preferences.appearance.theme;
    const labels = { amber: "Mora Amber", dark: "Тёмная тема", light: "Светлая тема" };
    themeButton.textContent = currentTheme === "amber" ? "A" : currentTheme === "dark" ? "◐" : "☼";
    themeButton.setAttribute("aria-pressed", String(currentTheme !== "amber"));
    themeButton.setAttribute("aria-label", "Текущая тема: " + labels[currentTheme] + ". Нажмите, чтобы переключить.");
    themeButton.title = "Тема: " + labels[currentTheme];
  }
}

function persistPreferences() {
  preferences = normalizePreferences(preferences);
  savePreferences(preferences);
  applyPreferences();
}

function capabilityRow(id, title, description) {
  const enabled = preferences.permissions[id] === true;
  return '<div class="permission-row"><div class="permission-copy"><strong>' + title +
    '</strong><span>' + description + '</span></div><button class="permission-toggle" data-capability="' +
    id + '" aria-pressed="' + String(enabled) + '">' + (enabled ? "Разрешено в профиле" : "Запрещено") + '</button></div>';
}

function profileButton(id, title) {
  const active = preferences.powerProfile === id;
  return '<button class="profile-choice' + (active ? ' active' : '') +
    '" data-power-profile="' + id + '" aria-pressed="' + String(active) + '">' + title + '</button>';
}

function recoveryStatus() {
  try {
    const raw = localStorage.getItem(RECOVERY_KEY);
    if (!raw) return "Точка восстановления оболочки ещё не создана.";
    const snapshot = validateRecoverySnapshot(JSON.parse(raw));
    return snapshot ? "Последняя точка оболочки: " + new Date(snapshot.createdAt).toLocaleString("ru-RU") : "Сохранённая точка повреждена или имеет неизвестную версию.";
  } catch {
    return "Хранилище браузера недоступно.";
  }
}

function renderIntentPlan(appWindow, plan) {
  const preview = appWindow.querySelector("[data-intent-preview]");
  const steps = appWindow.querySelector("[data-intent-steps]");
  const status = appWindow.querySelector("[data-intent-status]");
  const approve = appWindow.querySelector('[data-action="approve-intent"]');
  steps.replaceChildren();

  if (!plan || !plan.ok) {
    preview.hidden = true;
    approve.disabled = true;
    status.textContent = plan ? plan.message : "План не подготовлен.";
    return;
  }

  for (const action of plan.actions) {
    const item = document.createElement("li");
    item.textContent = action.label;
    steps.appendChild(item);
  }
  preview.hidden = false;
  approve.disabled = false;
  status.textContent = plan.summary;
}

function executeApprovedPlan() {
  if (!pendingIntentPlan || !pendingIntentPlan.ok) return;
  const appsToOpen = [];

  for (const action of pendingIntentPlan.actions) {
    if (action.type === "open-app" && appDefinitions[action.appId]) {
      appsToOpen.push(action.appId);
    } else if (action.type === "set" && action.setting === "focusMode") {
      preferences.focusMode = action.value === true;
    } else if (action.type === "set" && action.setting === "powerProfile" &&
               ["saver", "balanced", "performance"].includes(action.value)) {
      preferences.powerProfile = action.value;
    } else if (action.type === "set" && action.setting === "reducedMotion") {
      preferences.appearance.reducedMotion = action.value === true;
    }
  }

  persistPreferences();
  pendingIntentPlan = null;
  const agentWindow = windowLayer.querySelector('[data-window="mora-ai"]');
  if (agentWindow) {
    renderIntentPlan(agentWindow, null);
    agentWindow.querySelector("[data-intent-status]").textContent = "Подтверждённые локальные настройки применены.";
  }
  for (const appId of appsToOpen) openApp(appId);
  showToast("План Mora выполнен");
}

function setRecoveryStatus(message) {
  const status = windowLayer.querySelector('[data-window="updates"] [data-recovery-status]');
  if (status) status.textContent = message;
}

function updateSecurityPanel() {
  const panel = windowLayer.querySelector('[data-window="security"]');
  if (!panel) return;
  panel.querySelectorAll("[data-capability]").forEach((button) => {
    const enabled = preferences.permissions[button.dataset.capability] === true;
    button.setAttribute("aria-pressed", String(enabled));
    button.textContent = enabled ? "Разрешено в профиле" : "Запрещено";
  });
}

function updateWorkspacePanel() {
  const panel = windowLayer.querySelector('[data-window="workspace"]');
  if (!panel) return;
  panel.querySelectorAll("[data-power-profile]").forEach((button) => {
    const active = button.dataset.powerProfile === preferences.powerProfile;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  panel.querySelectorAll("[data-setting]").forEach((button) => {
    const enabled = button.dataset.setting === "focusMode"
      ? preferences.focusMode
      : preferences.appearance.reducedMotion;
    button.setAttribute("aria-pressed", String(enabled));
    button.textContent = enabled ? "Включено" : "Выключено";
  });
}


const EXTENSION_STORAGE_PREFIX = "duckos.mora.extension.";
const EXTENSION_APP_IDS = new Set([
  "orriganize", "olaab", "love-il", "poi", "poi-2", "po-2", "gamecharager"
]);

function extensionStorageKey(appId) {
  return EXTENSION_STORAGE_PREFIX + appId + ".v1";
}

function loadExtensionEntries(appId) {
  try {
    const value = JSON.parse(localStorage.getItem(extensionStorageKey(appId)) || "[]");
    return Array.isArray(value) ? value.filter((entry) => typeof entry === "string").slice(0, 100) : [];
  } catch {
    return [];
  }
}

function saveExtensionEntries(appId, entries) {
  try {
    localStorage.setItem(extensionStorageKey(appId), JSON.stringify(entries.slice(0, 100)));
    return true;
  } catch {
    return false;
  }
}

function renderExtensionEntries(appWindow) {
  const list = appWindow.querySelector("[data-extension-list]");
  if (!list) return;
  const appId = list.dataset.extensionList;
  const entries = loadExtensionEntries(appId);
  list.replaceChildren();

  if (entries.length === 0) {
    const empty = document.createElement("li");
    empty.className = "extension-empty";
    empty.textContent = "Пока пусто. Записи сохраняются только в этом профиле Mora.";
    list.append(empty);
    return;
  }

  entries.forEach((entry, index) => {
    const item = document.createElement("li");
    item.className = "extension-entry";
    const value = document.createElement("span");
    value.className = "extension-entry-text";
    value.textContent = entry;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "extension-entry-remove";
    remove.dataset.extensionRemove = String(index);
    remove.dataset.extensionApp = appId;
    remove.textContent = "Удалить";
    remove.setAttribute("aria-label", "Удалить запись");
    item.append(value, remove);
    list.append(item);
  });
}

function localCollectionPanel(appId, kicker, title, description, placeholder, label) {
  return '<p class="window-kicker">' + kicker + '</p><h2 class="window-heading">' + title + '</h2>' +
    '<p class="window-copy">' + description + '</p>' +
    '<form class="extension-form" data-extension-form data-extension-app="' + appId + '">' +
    '<label for="extension-entry-' + appId + '">' + label + '</label>' +
    '<div class="intent-input-row"><input id="extension-entry-' + appId + '" data-extension-input maxlength="160" autocomplete="off" placeholder="' + placeholder + '">' +
    '<button class="action-button" type="submit">Добавить</button></div></form>' +
    '<ul class="extension-entry-list" data-extension-list="' + appId + '" aria-live="polite"></ul>' +
    '<p class="extension-status" data-extension-status>Записи доступны только в текущем профиле браузера.</p>';
}

function extensionPanelMarkup(appId) {
  switch (appId) {
    case "sestem":
      return '<p class="window-kicker">SESTEM · ОБЗОР СИСТЕМЫ</p><h2 class="window-heading">Состояние DuckOS</h2>' +
        '<div class="extension-status-grid"><div class="extension-status-card"><strong>Mora Desktop</strong><span>Браузерная оболочка · активна</span></div>' +
        '<div class="extension-status-card"><strong>Контракты ядра</strong><span>Reaper reference runtime · проверяемая политика</span></div>' +
        '<div class="extension-status-card"><strong>DuckBridge</strong><span>Инспекция и планы запуска · без выполнения</span></div>' +
        '<div class="extension-status-card"><strong>Native boot</strong><span>Нативный загрузочный образ ещё не готов</span></div></div>' +
        '<div class="approval-actions"><button class="action-button" data-app="workspace">Открыть Control</button><button class="subtle-button" data-app="security">Открыть Sentinel</button></div>' +
        '<p class="window-copy">Панель показывает подтверждённую зрелость компонентов. Она не читает аппаратные датчики и не выдаёт статус оболочки за состояние ядра.</p>';
    case "setupup": {
      let complete = false;
      try { complete = Boolean(localStorage.getItem("duckos.mora.setupup.v1")); } catch {}
      const currentTheme = preferences.appearance.theme;
      const themeButton = (theme,label) => '<button class="extension-theme-button' + (currentTheme === theme ? ' active' : '') +
        '" data-setup-theme="' + theme + '" aria-pressed="' + String(currentTheme === theme) + '">' + label + '</button>';
      return '<p class="window-kicker">SETUPUP · МАСТЕР MORA</p><h2 class="window-heading">Настройте рабочее пространство</h2>' +
        '<p class="window-copy">Выберите тему и отметьте завершение локальной настройки. Установка ОС, разметка диска и настройка загрузчика здесь не выполняются.</p>' +
        '<div class="setting-block"><strong>Цветовая тема</strong><div class="extension-theme-options">' +
        themeButton("amber","Amber") + themeButton("dark","Dark") + themeButton("light","Light") +
        '</div></div><div class="approval-actions"><button class="action-button" data-action="setup-complete">Завершить настройку</button></div>' +
        '<p class="extension-status" data-setup-status>' + (complete ? 'Первичная настройка Mora уже завершена.' : 'Настройка ещё не завершена.') + '</p>';
    }
    case "orriganize":
      return localCollectionPanel("orriganize","ORRIGANIZE · ПОРЯДОК ДЕЛ","Проекты и задачи","Собирайте рабочие пункты и идеи в локальном списке. Gloverty остаётся отдельным центром автоматизаций; системное расписание и синхронизация не подключены.","Новая задача или проект","Добавить пункт");
    case "abriganza":
      return '<p class="window-kicker">ABRIGANZA · АРХИВНЫЙ ИНСПЕКТОР</p><h2 class="window-heading">Проверка архивного файла</h2>' +
        '<p class="window-copy">Прочитать имя, формат и размер выбранного архива. Содержимое не извлекается, не изменяется и не отправляется в сеть.</p>' +
        '<label class="file-picker">Выбрать архив<input type="file" data-archive-file accept=".zip,.7z,.rar,.tar,.gz,.bz2,.xz"></label>' +
        '<div class="inspection-report" data-archive-report>Архив ещё не выбран.</div>' +
        '<p class="window-copy">Полноценный распаковщик требует отдельного безопасного системного сервиса.</p>';
    case "olaab":
      return localCollectionPanel("olaab","OLAAB · МЕДИАТЕКА","Подборки и медиатеги","Создавайте названия альбомов и подборок. Здесь сохраняются текстовые ссылки и метки, а не сами медиафайлы.","Название альбома или подборки","Новая подборка");
    case "concrete-thump": {
      let bpm = 150, swing = 57;
      try {
        const saved = JSON.parse(localStorage.getItem("duckos.mora.concrete-thump.v1") || "null");
        if (saved && Number.isInteger(saved.bpm) && saved.bpm >= 40 && saved.bpm <= 240 &&
            Number.isInteger(saved.swing) && saved.swing >= 50 && saved.swing <= 75) ({bpm,swing} = saved);
      } catch {}
      return '<p class="window-kicker">CONCRETE THUMP · RHYTHM LAB</p><h2 class="window-heading">Ритмический профиль</h2>' +
        '<div class="extension-range-row"><div class="extension-range-heading"><label for="beat-bpm">Темп</label><output data-beat-value="bpm">' + bpm + ' BPM</output></div>' +
        '<input id="beat-bpm" type="range" min="40" max="240" value="' + bpm + '" data-beat-range="bpm"></div>' +
        '<div class="extension-range-row"><div class="extension-range-heading"><label for="beat-swing">Swing</label><output data-beat-value="swing">' + swing + '%</output></div>' +
        '<input id="beat-swing" type="range" min="50" max="75" value="' + swing + '" data-beat-range="swing"></div>' +
        '<button class="action-button" data-action="save-beat-profile">Сохранить профиль</button>' +
        '<p class="extension-status" data-beat-status>Локальные параметры. Генерация и воспроизведение аудио не подключены.</p>';
    }
    case "seu-beu":
      return '<p class="window-kicker">SEU-BEU · SHARE REVIEW</p><h2 class="window-heading">Проверка перед обменом</h2>' +
        '<p class="window-copy">Ручной список для проверки получателя, состава передачи и срока хранения. Это не шифрование и не системная защита.</p>' +
        '<div class="extension-checklist"><label class="extension-check"><input type="checkbox" data-share-check> Получатель и адрес передачи проверены</label>' +
        '<label class="extension-check"><input type="checkbox" data-share-check> Выбраны только нужные материалы</label>' +
        '<label class="extension-check"><input type="checkbox" data-share-check> Срок хранения и использование понятны</label></div>' +
        '<button class="action-button" data-action="review-share">Проверить список</button><p class="extension-status" data-share-status>Проверка ещё не запускалась.</p>';
    case "love-il":
      return localCollectionPanel("love-il","LOVE-IL · ЛИЧНОЕ ПРОСТРАНСТВО","Заметки для себя","Личные текстовые записи остаются в профиле браузера. Облачная синхронизация и медицинские функции не предполагаются.","Новая личная запись","Сохранить заметку");
    case "poi":
      return localCollectionPanel("poi","POI · QUICK CAPTURE","Быстрые заметки","Сохраняйте короткие мысли отдельно от проектных списков Orriganize.","Быстрая заметка","Добавить заметку");
    case "poi-2":
      return localCollectionPanel("poi-2","POI-2 · KNOWLEDGE CARDS","Карточки знаний","Личная база коротких справок в текущем браузерном профиле; системная индексация не подключена.","Новая карточка знаний","Добавить карточку");
    case "po-2":
      return localCollectionPanel("po-2","PO-2 · ROUTE PLANNER","Маршрут и точки","Ручной список остановок без GPS, геолокации и навигации в реальном времени.","Название точки или остановки","Добавить точку");
    case "gamecharager":
      return localCollectionPanel("gamecharager","GAMECHARAGER · GAME DESK","Игровая библиотека","Локальные игровые профили и read-only инспекция выбранного файла. Запуск игр и установка драйверов не выполняются.","Название игры или профиль","Добавить игру") +
        '<div class="setting-block"><strong>Проверка исполняемого файла</strong><label class="file-picker">Выбрать EXE или ELF<input type="file" data-executable-file accept=".exe,.dll,.elf"></label><div class="inspection-report" data-runtime-report>Файл ещё не выбран.</div></div>';
    case "exedotexe":
      return '<p class="window-kicker">EXEDOTEXE · EXECUTABLE INSPECTOR</p><h2 class="window-heading">Инспекция EXE и DLL</h2>' +
        '<p class="window-copy">Локальная проверка заголовка PE/ELF и контрольной суммы файла. Файл не запускается и не отправляется на сервер.</p>' +
        '<label class="file-picker">Выбрать исполняемый файл<input type="file" data-executable-file accept=".exe,.dll,.elf"></label>' +
        '<div class="inspection-report" data-runtime-report>Файл ещё не выбран.</div>' +
        '<div class="system-notice warning"><span class="notice-dot"></span><span>Это не антивирус, не проверка подписи издателя и не Windows runtime.</span></div>';
    default:
      return extensionPanelMarkup(appId);
  }
}

function commonsPanelMarkup() {
  const filters = MORA_COMMONS_CATEGORIES.map((category) =>
    '<button class="commons-filter" type="button" data-commons-filter="' + category.id +
    '" aria-pressed="false">' + category.title + '</button>'
  ).join("");

  return '<p class="window-kicker">MORA COMMONS · ЕДИНЫЙ КАТАЛОГ</p>' +
    '<h2 class="window-heading">Пространство возможностей</h2>' +
    '<p class="commons-intro">Пятнадцать направлений собраны по задачам, а не по полу. Каждый инструмент открыт каждому пользователю. Настраивайте каталог под свои интересы.</p>' +
    '<label class="commons-search"><span aria-hidden="true">⌕</span><input type="search" data-commons-search placeholder="Поиск по названию, функциям и ключевым словам" aria-label="Поиск приложений Mora Commons"></label>' +
    '<div class="commons-filters" data-commons-filters aria-label="Категории приложений">' +
    '<button class="commons-filter" type="button" data-commons-filter="all" aria-pressed="true">Все приложения</button>' +
    filters +
    '</div>' +
    '<p class="commons-count" data-commons-count aria-live="polite">Показано 15 приложений</p>' +
    '<div class="commons-grid" data-commons-grid></div>' +
    '<section class="commons-detail" data-commons-detail aria-live="polite" hidden></section>' +
    '<p class="window-copy">Каталог и избранное работают локально. Карточки описывают спецификации новых продуктов; отдельные исполняемые модули ещё не подключены.</p>';
}

function loadCommonsFavorites() {
  try {
    const stored = JSON.parse(localStorage.getItem("mora.commons.favorites.v1") || "[]");
    const knownIds = new Set(MORA_COMMONS_APPS.map((app) => app.id));
    return new Set(Array.isArray(stored) ? stored.filter((id) => knownIds.has(id)) : []);
  } catch {
    return new Set();
  }
}

let commonsFavorites = loadCommonsFavorites();

function saveCommonsFavorites() {
  try {
    localStorage.setItem("mora.commons.favorites.v1", JSON.stringify([...commonsFavorites]));
    return true;
  } catch {
    showToast("Избранное недоступно в этом профиле браузера");
    return false;
  }
}

function makeCommonsText(tagName, className, value) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  element.textContent = value;
  return element;
}

function renderCommonsDetails(detailPanel, app) {
  detailPanel.replaceChildren();

  const category = MORA_COMMONS_CATEGORIES.find((item) => item.id === app.category);
  const header = document.createElement("div");
  header.className = "commons-detail-head";
  header.appendChild(makeCommonsText("h3", "", app.name));

  const close = makeCommonsText("button", "commons-detail-close", "×");
  close.type = "button";
  close.dataset.commonsCloseDetail = "true";
  close.setAttribute("aria-label", "Закрыть описание приложения");
  header.appendChild(close);
  detailPanel.appendChild(header);

  detailPanel.appendChild(makeCommonsText("p", "commons-card-category", category ? category.title : ""));
  detailPanel.appendChild(makeCommonsText("p", "", app.description));

  const list = document.createElement("ul");
  for (const capability of app.capabilities) {
    list.appendChild(makeCommonsText("li", "", capability));
  }
  detailPanel.appendChild(list);

  detailPanel.appendChild(makeCommonsText(
    "p",
    "commons-detail-status",
    "Статус: спецификация. Каталог Mora Commons работает, но отдельный исполняемый модуль этого приложения ещё не подключён."
  ));
  detailPanel.hidden = false;
}

function initializeCommonsPanel(appWindow) {
  const search = appWindow.querySelector("[data-commons-search]");
  const filters = appWindow.querySelector("[data-commons-filters]");
  const grid = appWindow.querySelector("[data-commons-grid]");
  const count = appWindow.querySelector("[data-commons-count]");
  const details = appWindow.querySelector("[data-commons-detail]");
  let activeCategory = "all";

  function renderGrid() {
    const matches = filterCommonsApps(search.value, activeCategory);
    grid.replaceChildren();

    count.textContent = "Показано " + matches.length + " из " + MORA_COMMONS_APPS.length;

    if (!matches.length) {
      grid.appendChild(makeCommonsText("p", "commons-empty", "Ничего не найдено. Измените запрос или выберите другую категорию."));
      details.hidden = true;
      return;
    }

    for (const app of matches) {
      const category = MORA_COMMONS_CATEGORIES.find((item) => item.id === app.category);
      const card = document.createElement("article");
      card.className = "commons-card";

      const top = document.createElement("div");
      top.className = "commons-card-top";
      top.appendChild(makeCommonsText("span", "commons-card-glyph", app.glyph));

      const isFavorite = commonsFavorites.has(app.id);
      const favorite = makeCommonsText("button", "commons-favorite", isFavorite ? "★" : "☆");
      favorite.type = "button";
      favorite.dataset.commonsFavorite = app.id;
      favorite.setAttribute("aria-pressed", String(isFavorite));
      favorite.setAttribute(
        "aria-label",
        (isFavorite ? "Убрать из избранного: " : "Добавить в избранное: ") + app.name
      );
      top.appendChild(favorite);
      card.appendChild(top);

      card.appendChild(makeCommonsText("h3", "", app.name));
      card.appendChild(makeCommonsText("span", "commons-card-category", category ? category.title : ""));
      card.appendChild(makeCommonsText("p", "", app.subtitle));
      card.appendChild(makeCommonsText("p", "", app.description));

      const actions = document.createElement("div");
      actions.className = "commons-card-actions";
      const detailsButton = makeCommonsText("button", "", "Подробнее");
      detailsButton.type = "button";
      detailsButton.dataset.commonsDetails = app.id;
      actions.appendChild(detailsButton);
      card.appendChild(actions);
      grid.appendChild(card);
    }
  }

  filters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-commons-filter]");
    if (!button) return;
    activeCategory = button.dataset.commonsFilter;
    filters.querySelectorAll("[data-commons-filter]").forEach((item) => {
      item.setAttribute("aria-pressed", String(item === button));
    });
    renderGrid();
  });

  search.addEventListener("input", renderGrid);

  grid.addEventListener("click", (event) => {
    const favorite = event.target.closest("[data-commons-favorite]");
    if (favorite) {
      const appId = favorite.dataset.commonsFavorite;
      if (commonsFavorites.has(appId)) commonsFavorites.delete(appId);
      else commonsFavorites.add(appId);
      const saved = saveCommonsFavorites();
      renderGrid();
      if (saved) {
        showToast(commonsFavorites.has(appId) ? "Добавлено в избранное" : "Убрано из избранного");
      }
      return;
    }

    const detailsButton = event.target.closest("[data-commons-details]");
    if (detailsButton) {
      const app = MORA_COMMONS_APPS.find((item) => item.id === detailsButton.dataset.commonsDetails);
      if (app) renderCommonsDetails(details, app);
    }
  });

  details.addEventListener("click", (event) => {
    if (event.target.closest("[data-commons-close-detail]")) {
      details.hidden = true;
    }
  });

  renderGrid();
}

function panelMarkup(appId) {
  switch (appId) {
    case "cockos":
      return '<p class="window-kicker">АУДИОЦЕНТР · ДЕМО</p>' +
        '<h2 class="window-heading">Звук под контролем</h2>' +
        '<div class="control-row"><div class="control-copy"><strong>Системная громкость</strong><span>Общий уровень выхода</span></div><input type="range" min="0" max="100" value="72" data-range="volume"><span class="value-label" data-range-value="volume">72%</span></div>' +
        '<div class="control-row"><div class="control-copy"><strong>Микрофон</strong><span>Входной уровень</span></div><input type="range" min="0" max="100" value="58" data-range="mic"><span class="value-label" data-range-value="mic">58%</span></div>' +
        '<div class="control-row"><div class="control-copy"><strong>Запись</strong><span data-record-status>Готово к записи · 00:00</span></div><button class="action-button" data-action="record"><span class="record-dot"></span><span data-record-label>Начать запись</span></button></div>' +
        '<p class="window-copy">Показатели демонстрационные. Управление реальными аудиоустройствами появится через системный аудиосервис DuckOS.</p>';
    case "kavun":
      return '<p class="window-kicker">ГАЛЕРЕЯ · ДЕМОАЛЬБОМ</p><h2 class="window-heading">Сохранённые моменты</h2>' +
        '<div class="photo-grid">' +
        '<button class="photo-tile" data-photo="Закат над холмами">Закат над холмами</button><button class="photo-tile" data-photo="Лиловый горизонт">Лиловый горизонт</button><button class="photo-tile" data-photo="Тёплый берег">Тёплый берег</button>' +
        '<button class="photo-tile" data-photo="Тихий залив">Тихий залив</button><button class="photo-tile" data-photo="Старый город">Старый город</button><button class="photo-tile" data-photo="Вечерний свет">Вечерний свет</button></div>' +
        '<p class="window-copy" data-photo-status>Выберите плитку, чтобы отметить фотографию.</p>';
    case "kabon":
      return '<p class="window-kicker">ЛИЧНЫЙ БЮДЖЕТ · ДЕМО</p><h2 class="window-heading">Расходы за сегодня</h2>' +
        '<div class="expense-total"><strong>₴ 1 840</strong><span>из ₴ 2 500 · 73,6%</span></div>' +
        '<div class="expense-row"><span>Продукты</span><div class="expense-track"><i style="width:82%"></i></div><strong>₴ 740</strong></div>' +
        '<div class="expense-row"><span>Транспорт</span><div class="expense-track"><i style="width:44%"></i></div><strong>₴ 260</strong></div>' +
        '<div class="expense-row"><span>Кафе</span><div class="expense-track"><i style="width:68%"></i></div><strong>₴ 390</strong></div>' +
        '<div class="expense-row"><span>Покупки</span><div class="expense-track"><i style="width:53%"></i></div><strong>₴ 450</strong></div>' +
        '<p class="window-copy">Все суммы придуманы для демонстрации интерфейса. Банковские счета и платёжные сервисы не подключены.</p>';
    case "gloverty":
      return '<p class="window-kicker">АВТОМАТИЗАЦИЯ · ДЕМО</p><h2 class="window-heading">Сценарии дня</h2>' +
        '<div class="scene-list">' +
        '<div class="scene-row"><span class="scene-symbol">☀</span><div class="scene-copy"><strong>Доброе утро</strong><small>Свет, погода и календарь</small></div><button class="switch" role="switch" aria-checked="true" aria-label="Доброе утро"></button></div>' +
        '<div class="scene-row"><span class="scene-symbol">⌂</span><div class="scene-copy"><strong>Рабочий режим</strong><small>Фокус и уведомления</small></div><button class="switch" role="switch" aria-checked="false" aria-label="Рабочий режим"></button></div>' +
        '<div class="scene-row"><span class="scene-symbol">☾</span><div class="scene-copy"><strong>Тихий вечер</strong><small>Приглушённый свет и звук</small></div><button class="switch" role="switch" aria-checked="false" aria-label="Тихий вечер"></button></div>' +
        '</div><p class="window-copy" data-scene-status>Активен сценарий «Доброе утро». Переключатели меняют только демонстрационное состояние.</p>';
    case "po":
      return '<p class="window-kicker">ОРИЕНТИР · ДЕМО</p><h2 class="window-heading">Компас и направления</h2>' +
        '<div class="compass-layout"><div class="compass-rose"><span class="compass-north">N</span><span class="compass-needle">✦</span></div><div class="compass-details"><strong data-direction>Северо-восток</strong><span data-bearing>Азимут 045°</span><div class="compass-tabs"><button class="compass-tab active" data-direction-tab="Северо-восток" data-bearing-value="045">Северо-восток</button><button class="compass-tab" data-direction-tab="Юго-восток" data-bearing-value="135">Юго-восток</button><button class="compass-tab" data-direction-tab="Юго-запад" data-bearing-value="225">Юго-запад</button><button class="compass-tab" data-direction-tab="Северо-запад" data-bearing-value="315">Северо-запад</button></div></div></div>' +
        '<p class="window-copy">Направления иллюстративные. Геолокация и датчики компаса не используются.</p>';
    case "illidia":
      return '<p class="window-kicker">БИБЛИОТЕКА · ДЕМО</p><h2 class="window-heading">Продолжить приключение</h2>' +
        '<div class="game-list">' +
        '<div class="game-card"><div class="game-top"><strong>Echoes of Aster</strong><span>68%</span></div><div class="progress-track"><i style="width:68%"></i></div><div class="game-bottom"><span>Последняя игра: вчера</span><span>Глава 08</span></div></div>' +
        '<div class="game-card"><div class="game-top"><strong>Moonfall Keep</strong><span>34%</span></div><div class="progress-track"><i style="width:34%"></i></div><div class="game-bottom"><span>Сохранение найдено</span><span>Глава 03</span></div></div>' +
        '<div class="game-card"><div class="game-top"><strong>Wild Meridian</strong><span>12%</span></div><div class="progress-track"><i style="width:12%"></i></div><div class="game-bottom"><span>Новое приключение</span><span>Глава 01</span></div></div>' +
        '</div><div class="control-row"><div class="control-copy"><strong>Игровой режим</strong><span>Профиль производительности (демо)</span></div><button class="action-button" data-action="game-mode">Включить</button></div>';
    case "unify":
      return '<p class="window-kicker">ПОДКЛЮЧЕНИЯ · ДЕМО</p><h2 class="window-heading">Ваши устройства</h2>' +
        '<div class="device-list">' +
        '<div class="device-row"><span class="device-symbol">▣</span><div class="device-copy"><strong>Ноутбук Mora</strong><span>Основное устройство · Wi-Fi</span></div><span class="device-state">ONLINE</span></div>' +
        '<div class="device-row"><span class="device-symbol">♫</span><div class="device-copy"><strong>Беспроводные наушники</strong><span>Аудио · Bluetooth</span></div><button class="switch" role="switch" aria-checked="true" aria-label="Беспроводные наушники"></button></div>' +
        '<div class="device-row"><span class="device-symbol">⌘</span><div class="device-copy"><strong>Геймпад</strong><span>Игровой контроллер · Bluetooth</span></div><button class="switch" role="switch" aria-checked="false" aria-label="Геймпад"></button></div>' +
        '<div class="device-row"><span class="device-symbol">▤</span><div class="device-copy"><strong>Внешний дисплей</strong><span>Экран · HDMI</span></div><button class="switch" role="switch" aria-checked="true" aria-label="Внешний дисплей"></button></div>' +
        '</div><p class="window-copy" data-device-status>Подключённые устройства показаны условно. Сканирование оборудования не выполняется.</p>';
    case "mora-boost":
      return '<p class="window-kicker">MORA BOOST · OPLAGUE GAMING LAB</p>' +
        '<h2 class="window-heading">Игровая производительность под контролем</h2>' +
        '<div class="system-notice"><span class="notice-dot"></span><span>Здесь собраны реальные локальные измерения OPlague. Mora остаётся единым рабочим столом, но браузер не притворяется драйвером или аппаратным брокером.</span></div>' +
        '<div class="setting-block"><strong>Точное состояние оборудования</strong><span>Полные PCI/USB PnP ID, SUBSYS, REV, INF и версии драйверов; локальный SHA-256 отпечаток и атомарный снимок перед изменениями.</span></div>' +
        '<div class="setting-block"><strong>Обратимый игровой сеанс</strong><span>Нативный OPlague после подтверждения временно включает штатный план питания Windows и восстанавливает прежний, если он не менялся извне.</span></div>' +
        '<div class="setting-block"><strong>Телеметрия и стабильность</strong><span>NVIDIA nvidia-smi: температура, загрузка, VRAM, мощность и частоты; Windows WHEA/Display 4101; CSV frametime, средний FPS, 1%/0.1% low и p99.</span></div>' +
        '<div class="setting-block"><strong>Проверенные профили</strong><span>Локальный кэш только подтверждённых профилей по точной связке «игра + железо + версия драйвера». Деградация бенчмарка вызывает guarded restore плана питания.</span></div>' +
        '<div class="system-notice warning"><span class="notice-dot"></span><span>Прямой доступ Mora к PCI/GPU, установке драйверов, реестру, BIOS, IRQ/MSI, службам и сетевому стеку не включён. Нативный IPC DuckOS пока описан контрактом, но не реализован.</span></div>' +
        '<div class="approval-actions">' +
        '<a class="action-button" href="https://github.com/Ivan-VHS/OPlague" target="_blank" rel="noopener noreferrer">Открыть OPlague ↗</a>' +
        '<a class="subtle-button" href="https://github.com/Ivan-VHS/OPlague/blob/main/docs/GAMING_PERFORMANCE_WORKBENCH.md" target="_blank" rel="noopener noreferrer">Документация ↗</a>' +
        '</div>' +
        '<p class="window-copy">Сама браузерная панель не меняет настройки компьютера. Для снимка, телеметрии и игрового режима откройте нативное Windows-приложение OPlague.</p>';
    case "desktop":
      return '<p class="window-kicker">DUCK DESKTOP · НАТИВНЫЙ ИНСТРУМЕНТ</p>' +
        '<h2 class="window-heading">Рабочее пространство под контролем</h2>' +
        '<p class="window-copy">Mora остаётся графической оболочкой. Настоящая диагностика и управление пользовательской автозагрузкой выполняются отдельным приложением Duck Desktop на стороне DuckOS, а не браузерным JavaScript.</p>' +
        '<div class="setting-block"><strong>Нативное приложение</strong><span>Аудит файлов, пользовательской автозагрузки и процессов.</span></div>' +
        '<div class="setting-block"><strong>Команда запуска</strong><span>Откройте терминал установленной среды DuckOS и выполните: <code>duckos desktop gui</code>.</span></div>' +
        '<div class="setting-block"><strong>Безопасная организация</strong><span>Перенос выбранных файлов в Inbox без удаления и перезаписи; операции выполняются после подтверждения.</span></div>' +
        '<div class="setting-block"><strong>Автозагрузка</strong><span>Только текущий пользователь; отключение можно восстановить.</span></div>' +
        '<p class="window-copy">Браузерная Mora показывает только точку входа. Она не изображает системный монитор, оконный менеджер или привилегированный доступ.</p>';
    case "mora-commons":
      return commonsPanelMarkup();
    case "mora-ai":
      return '<p class="window-kicker">MORA INTENT ENGINE · ЛОКАЛЬНЫЙ РЕЖИМ</p>' +
        '<h2 class="window-heading">Сформулируйте задачу</h2>' +
        '<div class="system-notice"><span class="notice-dot"></span><span>Локальные сценарии доступны. Внешняя модель и NPU не подключены.</span></div>' +
        '<form class="intent-form" data-intent-form><label for="mora-intent-input">Что нужно сделать?</label>' +
        '<div class="intent-input-row"><input id="mora-intent-input" data-intent-input maxlength="320" placeholder="Например: включи фокус и экономию энергии" autocomplete="off">' +
        '<button class="action-button" type="submit">Подготовить план</button></div></form>' +
        '<div class="intent-status" data-intent-status>Агент распознаёт только ограниченный список безопасных локальных действий.</div>' +
        '<div class="intent-preview" data-intent-preview hidden><p class="window-kicker">ПЛАН НА ПРОВЕРКУ</p><ol data-intent-steps></ol>' +
        '<div class="approval-actions"><button class="action-button" data-action="approve-intent">Подтвердить план</button>' +
        '<button class="subtle-button" data-action="deny-intent">Отклонить</button></div></div>' +
        '<p class="window-copy">Подтверждение обязательно. Агент не исполняет shell-команды, не меняет системные файлы и не отправляет запросы в сеть.</p>';
    case "security":
      return '<p class="window-kicker">SENTINEL · МОДЕЛЬ ДОВЕРИЯ</p><h2 class="window-heading">Доступы и изоляция</h2>' +
        '<div class="security-summary"><strong>По умолчанию — запрет</strong><span>Каждое право должно быть запрошено отдельно.</span></div>' +
        capabilityRow("microphone", "Микрофон", "Для приложений, которым нужен аудиоввод") +
        capabilityRow("camera", "Камера", "Для фото, видео и конференций") +
        capabilityRow("location", "Геолокация", "Только при явном разрешении") +
        capabilityRow("files", "Личные файлы", "Доступ к выбранным папкам и документам") +
        capabilityRow("network", "Сеть", "Исходящие соединения приложений") +
        capabilityRow("clipboard", "Буфер обмена", "Чтение и запись скопированного содержимого") +
        '<div class="system-notice warning"><span class="notice-dot"></span><span>Это сохранённые предпочтения оболочки. Нативный capability broker и реальные песочницы ещё не подключены.</span></div>' +
        '<p class="window-copy">Профиль не выдаёт разрешения процессам браузера и не заменяет системную защиту.</p>';
    case "updates":
      return '<p class="window-kicker">RESTORE · ВОССТАНОВЛЕНИЕ</p><h2 class="window-heading">Обновления без сюрпризов</h2>' +
        '<div class="update-state"><span class="state-mark">↶</span><div><strong>Системный updater не подключён</strong><span>Атомарные A/B-образы и откат — целевая архитектура DuckOS.</span></div></div>' +
        '<div class="recovery-card"><strong>Точка восстановления Mora</strong><span data-recovery-status>' + recoveryStatus() + '</span>' +
        '<div class="approval-actions"><button class="action-button" data-action="save-recovery">Сохранить профиль</button>' +
        '<button class="subtle-button" data-action="restore-recovery">Восстановить</button></div></div>' +
        '<button class="wide-action" data-action="preview-update">Проверить план обновления</button>' +
        '<div class="intent-status" data-update-preview>Проверка только сформирует локальный план. Скачивания и установки не будет.</div>' +
        '<p class="window-copy">Сейчас сохраняются только настройки Mora в локальном хранилище браузера — не раздел ОС, приложения или пользовательские файлы.</p>';
    case "runtime":
      return '<p class="window-kicker">BRIDGE · WINDOWS COMPATIBILITY</p><h2 class="window-heading">Совместимость Windows-приложений</h2>' +
        '<p class="window-copy">Bridge проверяет выбранные EXE/DLL локально. В Mora доступна быстрая проверка заголовка; расширенный PE-анализ, список импортируемых DLL, профили приложений и диагностика доступны через инструменты DuckOS CLI.</p>' +
        '<label class="file-picker">Проверить EXE или DLL<input type="file" data-executable-file accept=".exe,.dll"></label>' +
        '<div class="inspection-report" data-runtime-report>Файл ещё не выбран.</div>' +
        '<div class="setting-block"><strong>Инструменты DuckOS</strong><span>После установки пакета duckos-build-tools в среде разработки:</span>' +
        '<div class="system-notice"><span class="notice-dot"></span><span>duckos inspect-pe ./game.exe — заголовки PE32/PE32+, секции и импортируемые DLL</span></div>' +
        '<div class="system-notice"><span class="notice-dot"></span><span>duckos prefix-create ./prefixes game --architecture x86_64 — отдельный профиль игры</span></div>' +
        '<div class="system-notice"><span class="notice-dot"></span><span>duckos compat-diagnose ./game.exe --prefix ./prefixes/game — поиск отсутствующих DLL</span></div>' +
        '<div class="system-notice"><span class="notice-dot"></span><span>duckos compat-plan ./game.exe --prefix ./prefixes/game — отчёт о блокерах запуска</span></div>' +
        '<div class="system-notice"><span class="notice-dot"></span><span>duckos bridge runtimes — поиск Wine, Proton, CrossOver, Bottles, Box64 и QEMU без запуска этих программ</span></div>' +
        '<div class="system-notice"><span class="notice-dot"></span><span>duckos bridge plan ./game.exe --purpose game --compat-data PATH — подготовка структуры команды Proton без её выполнения</span></div></div>' +
        '<div class="system-notice warning"><span class="notice-dot"></span><span>Реальный запуск EXE пока заблокирован: в DuckOS ещё нет NT process manager, Win32 API runtime и DirectX/Vulkan backend. Автозагрузка DLL, драйверов и обход античитов не выполняются.</span></div>' +
        '<p class="window-copy">Создание профиля пока формирует только изолированную структуру и manifest. Это фундамент совместимости, а не готовая замена Wine.</p>';
    case "workspace":
      return '<p class="window-kicker">CONTROL · WORKSPACE</p><h2 class="window-heading">Рабочая среда Mora</h2>' +
        '<div class="setting-block"><strong>Профиль ресурсов</strong><span>Локальная настройка оболочки, не планировщик ядра</span>' +
        '<div class="profile-options">' + profileButton("saver", "Экономия") + profileButton("balanced", "Баланс") + profileButton("performance", "Производительность") + '</div></div>' +
        '<div class="permission-row"><div class="permission-copy"><strong>Режим фокуса</strong><span>Приглушить второстепенные элементы оболочки</span></div><button class="permission-toggle" data-setting="focusMode" aria-pressed="' + String(preferences.focusMode) + '">' + (preferences.focusMode ? "Включено" : "Выключено") + '</button></div>' +
        '<div class="permission-row"><div class="permission-copy"><strong>Снижение движения</strong><span>Убрать декоративные переходы и перемещения</span></div><button class="permission-toggle" data-setting="reducedMotion" aria-pressed="' + String(preferences.appearance.reducedMotion) + '">' + (preferences.appearance.reducedMotion ? "Включено" : "Выключено") + '</button></div>' +
        '<div class="system-notice"><span class="notice-dot"></span><span>Адаптивная сетка и настройки доступности работают в оболочке. Аппаратные профили, VRR и NPU-планирование требуют native services.</span></div>' +
        '<p class="window-copy">Настройки хранятся локально в профиле браузера и могут быть сброшены очисткой данных сайта.</p>';
    case "provenance":
      return '<p class="window-kicker">PROOF · FILE ORIGIN</p><h2 class="window-heading">Проверка файла</h2>' +
        '<p class="window-copy">SHA-256 вычисляется локально в браузере. Это помогает сравнить контрольные суммы, но не подтверждает автора или подлинность содержимого.</p>' +
        '<label class="file-picker">Выбрать файл для проверки<input type="file" data-provenance-file></label>' +
        '<div class="inspection-report" data-provenance-report>Файл ещё не выбран.</div>' +
        '<div class="system-notice warning"><span class="notice-dot"></span><span>Проверка подписей и C2PA provenance manifest пока не реализована. Не считайте хеш криптографическим подтверждением происхождения.</span></div>';
    default:
      return '<h2 class="window-heading">Приложение не найдено</h2>';
  }
}

function updateClock() {
  const now = new Date();
  const time = new Intl.DateTimeFormat("ru-RU", { hour: "2-digit", minute: "2-digit" }).format(now);
  const date = new Intl.DateTimeFormat("ru-RU", { weekday: "long", day: "numeric", month: "long", year: "numeric" }).format(now);
  document.getElementById("hero-clock").textContent = time;
  document.getElementById("status-time").textContent = time;
  document.getElementById("hero-date").textContent = date.charAt(0).toLocaleUpperCase("ru-RU") + date.slice(1);
}

function showToast(message) {
  toastElement.textContent = message;
  toastElement.classList.add("visible");
  window.clearTimeout(toastTimeout);
  toastTimeout = window.setTimeout(() => toastElement.classList.remove("visible"), 2200);
}

function updateActiveApp() {
  const windows = Array.from(windowLayer.querySelectorAll(".app-window"));
  if (windows.length === 0) {
    activeAppLabel.textContent = "Рабочий стол";
  } else {
    windows.sort((a, b) => Number(b.style.zIndex) - Number(a.style.zIndex));
    const topWindow = windows[0];
    activeAppLabel.textContent = appDefinitions[topWindow.dataset.window].name;
  }
  document.querySelectorAll(".dock-item").forEach((item) => {
    item.classList.toggle("is-running", Boolean(windowLayer.querySelector('[data-window="' + item.getAttribute("data-app") + '"]')));
  });
}

function focusWindow(appWindow) {
  appWindow.style.zIndex = String(++nextZIndex);
  updateActiveApp();
}

function openApp(appId) {
  const definition = appDefinitions[appId];
  if (!definition) return;
  let appWindow = windowLayer.querySelector('[data-window="' + appId + '"]');
  if (appWindow) {
    focusWindow(appWindow);
    return;
  }

  appWindow = document.createElement("section");
  appWindow.className = "app-window";
  appWindow.dataset.window = appId;
  appWindow.setAttribute("role", "dialog");
  appWindow.setAttribute("aria-modal", "false");
  appWindow.setAttribute("aria-label", definition.name);
  appWindow.style.setProperty("--accent", definition.color);
  appWindow.style.zIndex = String(++nextZIndex);
  appWindow.innerHTML =
    '<header class="window-titlebar"><span class="window-app-icon">' + definition.glyph + '</span><span class="window-title">' + definition.name + '</span><button class="window-close" data-action="close" aria-label="Закрыть окно">×</button></header>' +
    '<div class="window-body">' + panelMarkup(appId) + '</div>';
  windowLayer.appendChild(appWindow);
  renderExtensionEntries(appWindow);
  if (appId === "mora-commons") initializeCommonsPanel(appWindow);

  const left = Math.max(16, Math.round((window.innerWidth - appWindow.offsetWidth) / 2));
  const top = Math.max(16, Math.round((window.innerHeight - appWindow.offsetHeight) / 2) - 14);
  appWindow.style.left = left + "px";
  appWindow.style.top = top + "px";
  appWindow.style.transform = "none";
  focusWindow(appWindow);
  appWindow.querySelector(".window-close").focus();
  showToast(definition.name + " открыто");
}

function closeWindow(appWindow) {
  if (!appWindow) return;
  appWindow.remove();
  updateActiveApp();
}

function closeTopWindow() {
  const windows = Array.from(windowLayer.querySelectorAll(".app-window"));
  if (!windows.length) return;
  windows.sort((a, b) => Number(b.style.zIndex) - Number(a.style.zIndex));
  closeWindow(windows[0]);
}

function startWindowDrag(appWindow, header, pointerEvent) {
  if (pointerEvent.target.closest("button")) return;
  const rect = appWindow.getBoundingClientRect();
  const offsetX = pointerEvent.clientX - rect.left;
  const offsetY = pointerEvent.clientY - rect.top;
  header.setPointerCapture(pointerEvent.pointerId);
  focusWindow(appWindow);

  function move(moveEvent) {
    if (moveEvent.pointerId !== pointerEvent.pointerId) return;
    const width = appWindow.offsetWidth;
    const height = appWindow.offsetHeight;
    const maxLeft = Math.max(8, window.innerWidth - width - 8);
    const maxTop = Math.max(56, window.innerHeight - height - 72);
    const left = Math.min(maxLeft, Math.max(8, moveEvent.clientX - offsetX));
    const top = Math.min(maxTop, Math.max(56, moveEvent.clientY - offsetY));
    appWindow.style.left = left + "px";
    appWindow.style.top = top + "px";
  }

  function stop(stopEvent) {
    if (stopEvent.pointerId !== pointerEvent.pointerId) return;
    header.removeEventListener("pointermove", move);
    header.removeEventListener("pointerup", stop);
    header.removeEventListener("pointercancel", stop);
  }

  header.addEventListener("pointermove", move);
  header.addEventListener("pointerup", stop);
  header.addEventListener("pointercancel", stop);
}

document.addEventListener("click", (event) => {
  const themeToggle = event.target.closest('[data-action="toggle-theme"]');
  if (themeToggle) {
    const nextTheme = { amber: "dark", dark: "light", light: "amber" };
    preferences.appearance.theme = nextTheme[preferences.appearance.theme] || "amber";
    persistPreferences();
    const themeNames = { amber: "Mora Amber", dark: "Тёмная тема", light: "Светлая тема" };
    showToast("Тема: " + themeNames[preferences.appearance.theme]);
    return;
  }

  const setupTheme = event.target.closest("[data-setup-theme]");
  if (setupTheme) {
    const theme = setupTheme.dataset.setupTheme;
    if (!["amber", "dark", "light"].includes(theme)) return;
    preferences.appearance.theme = theme;
    persistPreferences();
    applyPreferences();
    const owner = setupTheme.closest(".app-window");
    if (owner) owner.querySelectorAll("[data-setup-theme]").forEach((button) => {
      const active = button.dataset.setupTheme === theme;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    showToast("Тема Mora обновлена");
    return;
  }

  const setupComplete = event.target.closest('[data-action="setup-complete"]');
  if (setupComplete) {
    const status = setupComplete.closest(".app-window").querySelector("[data-setup-status]");
    try {
      localStorage.setItem("duckos.mora.setupup.v1", new Date().toISOString());
      if (status) status.textContent = "Настройка Mora завершена и сохранена в профиле браузера.";
      showToast("Первичная настройка Mora завершена");
    } catch {
      if (status) status.textContent = "Не удалось сохранить состояние настройки.";
    }
    return;
  }

  const extensionRemove = event.target.closest("[data-extension-remove]");
  if (extensionRemove) {
    const appId = extensionRemove.dataset.extensionApp;
    const index = Number(extensionRemove.dataset.extensionRemove);
    const entries = loadExtensionEntries(appId);
    if (!EXTENSION_APP_IDS.has(appId) || !Number.isInteger(index) || index < 0 || index >= entries.length) return;
    entries.splice(index, 1);
    const owner = extensionRemove.closest(".app-window");
    if (!saveExtensionEntries(appId, entries)) {
      const status = owner && owner.querySelector("[data-extension-status]");
      if (status) status.textContent = "Не удалось обновить локальный список.";
      return;
    }
    if (owner) {
      renderExtensionEntries(owner);
      const status = owner.querySelector("[data-extension-status]");
      if (status) status.textContent = "Запись удалена из локального списка.";
    }
    return;
  }

  const beatSave = event.target.closest('[data-action="save-beat-profile"]');
  if (beatSave) {
    const owner = beatSave.closest(".app-window");
    const bpm = Number(owner.querySelector('[data-beat-range="bpm"]').value);
    const swing = Number(owner.querySelector('[data-beat-range="swing"]').value);
    try {
      localStorage.setItem("duckos.mora.concrete-thump.v1", JSON.stringify({ bpm, swing, savedAt: new Date().toISOString() }));
      owner.querySelector("[data-beat-status]").textContent = "Профиль " + bpm + " BPM / " + swing + "% сохранён локально.";
      showToast("Ритмический профиль сохранён");
    } catch {
      owner.querySelector("[data-beat-status]").textContent = "Не удалось сохранить профиль браузера.";
    }
    return;
  }

  const shareReview = event.target.closest('[data-action="review-share"]');
  if (shareReview) {
    const owner = shareReview.closest(".app-window");
    const total = owner.querySelectorAll("[data-share-check]").length;
    const checked = owner.querySelectorAll("[data-share-check]:checked").length;
    owner.querySelector("[data-share-status]").textContent =
      checked + " из " + total + " пунктов отмечено. Проверьте получателя и содержимое передачи самостоятельно.";
    return;
  }

  const opener = event.target.closest("[data-app]");
  if (opener) {
    openApp(opener.dataset.app);
    return;
  }

  const closeButton = event.target.closest('[data-action="close"]');
  if (closeButton) {
    closeWindow(closeButton.closest(".app-window"));
    return;
  }

  const switchButton = event.target.closest('.switch[role="switch"]');
  if (switchButton) {
    const enabled = switchButton.getAttribute("aria-checked") !== "true";
    switchButton.setAttribute("aria-checked", String(enabled));
    const owner = switchButton.closest(".app-window");
    if (owner && owner.dataset.window === "gloverty") {
      const active = Array.from(owner.querySelectorAll('.switch[aria-checked="true"]')).length;
      const status = owner.querySelector("[data-scene-status]");
      status.textContent = active ? "Активных сценариев: " + active + ". Реальные устройства не затрагиваются." : "Все сценарии выключены.";
    }
    if (owner && owner.dataset.window === "unify") {
      const status = owner.querySelector("[data-device-status]");
      status.textContent = "Состояния демонстрационных подключений обновлены. Реальное подключение не выполняется.";
      const state = switchButton.getAttribute("aria-checked") === "true" ? "ПОДКЛЮЧЕНО" : "ОТКЛЮЧЕНО";
      showToast("Состояние изменено: " + state.toLowerCase());
    }
    return;
  }

  const recordButton = event.target.closest('[data-action="record"]');
  if (recordButton) {
    const recording = recordButton.classList.toggle("recording");
    recordButton.querySelector("[data-record-label]").textContent = recording ? "Остановить" : "Начать запись";
    recordButton.closest(".app-window").querySelector("[data-record-status]").textContent = recording ? "Идёт демонстрационная запись · 00:01" : "Запись остановлена · 00:01";
    showToast(recording ? "Демонстрационная запись началась" : "Демонстрационная запись остановлена");
    return;
  }

  const photo = event.target.closest("[data-photo]");
  if (photo) {
    photo.classList.toggle("selected");
    const status = photo.closest(".app-window").querySelector("[data-photo-status]");
    status.textContent = photo.classList.contains("selected") ? "Выбрано: " + photo.dataset.photo : "Выделение снято.";
    return;
  }

  const directionTab = event.target.closest("[data-direction-tab]");
  if (directionTab) {
    const panel = directionTab.closest(".app-window");
    panel.querySelectorAll(".compass-tab").forEach((tab) => tab.classList.toggle("active", tab === directionTab));
    panel.querySelector("[data-direction]").textContent = directionTab.dataset.directionTab;
    panel.querySelector("[data-bearing]").textContent = "Азимут " + directionTab.dataset.bearingValue + "°";
    return;
  }

  const gameMode = event.target.closest('[data-action="game-mode"]');
  if (gameMode) {
    const enabled = gameMode.dataset.enabled !== "true";
    gameMode.dataset.enabled = String(enabled);
    gameMode.textContent = enabled ? "Выключить" : "Включить";
    showToast(enabled ? "Игровой профиль включён (демо)" : "Игровой профиль выключен");
  }

  const gameButton = event.target.closest('[data-action="game-launch"]');
  if (gameButton) {
    showToast("Запуск игр пока представлен демонстрационной карточкой");
  }
});

document.addEventListener("input", (event) => {
  const beatRange = event.target.closest("[data-beat-range]");
  if (beatRange) {
    const output = beatRange.closest(".extension-range-row").querySelector('[data-beat-value="' + beatRange.dataset.beatRange + '"]');
    if (output) output.textContent = beatRange.dataset.beatRange === "bpm" ? beatRange.value + " BPM" : beatRange.value + "%";
    return;
  }
  const range = event.target.closest("[data-range]");
  if (!range) return;
  const valueLabel = range.closest(".control-row").querySelector('[data-range-value="' + range.dataset.range + '"]');
  if (valueLabel) valueLabel.textContent = range.value + "%";
});

windowLayer.addEventListener("pointerdown", (event) => {
  const appWindow = event.target.closest(".app-window");
  if (!appWindow) return;
  focusWindow(appWindow);
  const header = event.target.closest(".window-titlebar");
  if (header && event.button === 0) startWindowDrag(appWindow, header, event);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeTopWindow();
  }
});


document.addEventListener("submit", (event) => {
  const extensionForm = event.target.closest("[data-extension-form]");
  if (extensionForm) {
    event.preventDefault();
    const appId = extensionForm.dataset.extensionApp;
    const input = extensionForm.querySelector("[data-extension-input]");
    const value = input ? input.value.trim() : "";
    const status = extensionForm.closest(".app-window").querySelector("[data-extension-status]");
    if (!EXTENSION_APP_IDS.has(appId)) return;
    if (!value) {
      if (status) status.textContent = "Введите текст перед добавлением.";
      return;
    }
    const entries = loadExtensionEntries(appId);
    if (entries.length >= 100) {
      if (status) status.textContent = "Достигнут предел в 100 записей для этого списка.";
      return;
    }
    entries.push(value.slice(0, 160));
    if (!saveExtensionEntries(appId, entries)) {
      if (status) status.textContent = "Хранилище браузера недоступно или заполнено.";
      return;
    }
    input.value = "";
    renderExtensionEntries(extensionForm.closest(".app-window"));
    if (status) status.textContent = "Сохранено локально · " + entries.length + " записей.";
    return;
  }

  const form = event.target.closest("[data-intent-form]");
  if (!form) return;
  event.preventDefault();

  const appWindow = form.closest(".app-window");
  const input = form.querySelector("[data-intent-input]");
  pendingIntentPlan = buildIntentPlan(input.value);
  renderIntentPlan(appWindow, pendingIntentPlan);
});

document.addEventListener("click", (event) => {
  const approve = event.target.closest('[data-action="approve-intent"]');
  if (approve) {
    executeApprovedPlan();
    return;
  }

  const deny = event.target.closest('[data-action="deny-intent"]');
  if (deny) {
    pendingIntentPlan = null;
    renderIntentPlan(deny.closest(".app-window"), null);
    showToast("План отклонён");
    return;
  }

  const capability = event.target.closest("[data-capability]");
  if (capability) {
    const name = capability.dataset.capability;
    if (!(name in preferences.permissions)) return;
    preferences.permissions[name] = capability.getAttribute("aria-pressed") !== "true";
    persistPreferences();
    updateSecurityPanel();
    showToast("Предпочтение доступа сохранено");
    return;
  }

  const profile = event.target.closest("[data-power-profile]");
  if (profile) {
    const value = profile.dataset.powerProfile;
    if (!["saver", "balanced", "performance"].includes(value)) return;
    preferences.powerProfile = value;
    persistPreferences();
    updateWorkspacePanel();
    showToast("Профиль оболочки: " + value);
    return;
  }

  const setting = event.target.closest("[data-setting]");
  if (setting) {
    if (setting.dataset.setting === "focusMode") {
      preferences.focusMode = !preferences.focusMode;
    } else if (setting.dataset.setting === "reducedMotion") {
      preferences.appearance.reducedMotion = !preferences.appearance.reducedMotion;
    } else {
      return;
    }
    persistPreferences();
    updateWorkspacePanel();
    showToast("Настройки рабочего пространства сохранены");
    return;
  }

  const saveRecovery = event.target.closest('[data-action="save-recovery"]');
  if (saveRecovery) {
    const snapshot = createRecoverySnapshot(preferences);
    try {
      localStorage.setItem(RECOVERY_KEY, JSON.stringify(snapshot));
      setRecoveryStatus("Профиль Mora сохранён: " + new Date(snapshot.createdAt).toLocaleString("ru-RU"));
      showToast("Точка настроек Mora сохранена");
    } catch {
      setRecoveryStatus("Не удалось сохранить профиль: локальное хранилище недоступно.");
    }
    return;
  }

  const restoreRecovery = event.target.closest('[data-action="restore-recovery"]');
  if (restoreRecovery) {
    try {
      const raw = localStorage.getItem(RECOVERY_KEY);
      const snapshot = raw ? validateRecoverySnapshot(JSON.parse(raw)) : null;
      if (!snapshot) {
        setRecoveryStatus("Нет действительной точки восстановления настроек Mora.");
        return;
      }
      preferences = normalizePreferences(snapshot.preferences);
      persistPreferences();
      updateSecurityPanel();
      updateWorkspacePanel();
      setRecoveryStatus("Настройки Mora восстановлены из точки от " + new Date(snapshot.createdAt).toLocaleString("ru-RU"));
      showToast("Профиль Mora восстановлен");
    } catch {
      setRecoveryStatus("Восстановление невозможно: хранилище недоступно или данные повреждены.");
    }
    return;
  }

  const updatePreview = event.target.closest('[data-action="preview-update"]');
  if (updatePreview) {
    const output = updatePreview.closest(".app-window").querySelector("[data-update-preview]");
    output.textContent = "План: проверить подпись пакета → проверить свободное место → подготовить новый слот → выполнить smoke-test → оставить текущий слот для отката. Это архитектурный preview; updater и образы не подключены.";
  }
});

document.addEventListener("change", async (event) => {
  const archiveInput = event.target.closest("[data-archive-file]");
  if (archiveInput) {
    const report = archiveInput.closest(".app-window").querySelector("[data-archive-report]");
    const file = archiveInput.files && archiveInput.files[0];
    if (!file) return;
    const supported = /\.(zip|7z|rar|tar|gz|bz2|xz)$/i.test(file.name);
    if (!supported) {
      report.textContent = "Неподдерживаемое расширение архива.";
      return;
    }
    if (file.size > 100 * 1024 * 1024) {
      report.textContent = "Файл превышает локальный предел проверки 100 МБ.";
      return;
    }
    report.textContent = "Файл: " + file.name + "\nРазмер: " + file.size.toLocaleString("ru-RU") +
      " байт\nМетаданные прочитаны. Извлечение содержимого не выполнялось.";
    return;
  }

  const executableInput = event.target.closest("[data-executable-file]");
  if (executableInput) {
    const report = executableInput.closest(".app-window").querySelector("[data-runtime-report]");
    const file = executableInput.files && executableInput.files[0];
    if (!file) return;
    report.textContent = "Читаю заголовок файла локально…";
    try {
      const result = await inspectExecutable(file);
      let details = file.name + "\n" + file.size.toLocaleString("ru-RU") + " байт\n" +
        result.format + " · " + result.architecture + "\n" + result.detail;
      if (executableInput.closest('[data-window="exedotexe"]')) {
        details += "\nSHA-256\n" + await hashFile(file);
      }
      report.textContent = details;
    } catch (error) {
      report.textContent = error.message || "Не удалось прочитать файл.";
    }
    return;
  }

  const provenanceInput = event.target.closest("[data-provenance-file]");
  if (provenanceInput) {
    const report = provenanceInput.closest(".app-window").querySelector("[data-provenance-report]");
    const file = provenanceInput.files && provenanceInput.files[0];
    if (!file) return;
    report.textContent = "Вычисляю SHA-256 в локальном контексте…";
    try {
      const digest = await hashFile(file);
      report.textContent = file.name + "\n" + file.size.toLocaleString("ru-RU") + " байт\nSHA-256\n" + digest;
    } catch (error) {
      report.textContent = error.message || "Не удалось вычислить контрольную сумму.";
    }
  }
});

document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    openApp("mora-ai");
  }
});

applyPreferences();
updateClock();
window.setInterval(updateClock, 1000);
updateActiveApp();

if ("serviceWorker" in navigator &&
    (location.protocol === "https:" || location.hostname === "localhost" || location.hostname === "127.0.0.1")) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./service-worker.js").catch(() => {
      // The desktop remains usable when offline installation is unavailable.
    });
  });
}