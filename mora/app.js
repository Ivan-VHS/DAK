import { MORA_COMMONS_APPS, MORA_COMMONS_CATEGORIES, filterCommonsApps } from "./commons-catalog.js";
import { VirtualWorkspace, MAX_WORKSPACE_FILE_BYTES } from "./workspace.js";
import { applyTranslations, detectLocale, formatItemCount, LOCALE_STORAGE_KEY, translateText } from "./i18n.js";
import { createGamepadInput, findDirectionalTarget, isEditableTarget } from "./console-navigation.js";

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

const DUCK_ACCENT = "#FFD400";

const appDefinitions = {
  cockos: { name: "Cockos", subtitle: "Звук и запись", color: DUCK_ACCENT, glyph: "∿" },
  kavun: { name: "Kavun", subtitle: "Фотографии", color: DUCK_ACCENT, glyph: "◒" },
  kabon: { name: "Ka-bon", subtitle: "Финансы", color: DUCK_ACCENT, glyph: "₴" },
  gloverty: { name: "Gloverty", subtitle: "Сценарии", color: DUCK_ACCENT, glyph: "ϟ" },
  po: { name: "Po", subtitle: "Компас", color: DUCK_ACCENT, glyph: "⌖" },
  illidia: { name: "Illidia", subtitle: "Игры", color: DUCK_ACCENT, glyph: "⌘" },
  unify: { name: "Unify", subtitle: "Устройства", color: DUCK_ACCENT, glyph: "∞" },
  sestem: { name: "Sestem", subtitle: "Статус системы", color: DUCK_ACCENT, glyph: "♟" },
  setupup: { name: "SetupUP", subtitle: "Первичная настройка", color: DUCK_ACCENT, glyph: "✳" },
  orriganize: { name: "Orriganize", subtitle: "Задачи и проекты", color: DUCK_ACCENT, glyph: "▦" },
  abriganza: { name: "Abriganza", subtitle: "Архивы и файлы", color: DUCK_ACCENT, glyph: "▤" },
  olaab: { name: "Olaab", subtitle: "Медиатека", color: DUCK_ACCENT, glyph: "◈" },
  "concrete-thump": { name: "Concrete Thump", subtitle: "Ритм и темп", color: DUCK_ACCENT, glyph: "♫" },
  "seu-beu": { name: "Seu-Beu", subtitle: "Проверка обмена", color: DUCK_ACCENT, glyph: "◇" },
  "love-il": { name: "Love-IL", subtitle: "Личный дневник", color: DUCK_ACCENT, glyph: "♡" },
  poi: { name: "Poi", subtitle: "Быстрые заметки", color: DUCK_ACCENT, glyph: "⌖" },
  "poi-2": { name: "Poi-2", subtitle: "База знаний", color: DUCK_ACCENT, glyph: "▧" },
  "po-2": { name: "Po-2", subtitle: "Маршруты и точки", color: DUCK_ACCENT, glyph: "➤" },
  gamecharager: { name: "GameCharager", subtitle: "Игровая библиотека", color: DUCK_ACCENT, glyph: "▣" },
  exedotexe: { name: "EXEdotEXE", subtitle: "EXE-инспектор", color: DUCK_ACCENT, glyph: "E" },
  "mora-ai": { name: "Mora AI", subtitle: "Намерения и планы", color: DUCK_ACCENT, glyph: "✦" },
  security: { name: "Sentinel", subtitle: "Права и доверие", color: DUCK_ACCENT, glyph: "◇" },
  updates: { name: "Restore", subtitle: "Обновления и откат", color: DUCK_ACCENT, glyph: "↶" },
  runtime: { name: "Bridge", subtitle: "Windows compatibility", color: DUCK_ACCENT, glyph: "⇄" },
  workspace: { name: "Control", subtitle: "Среда и питание", color: DUCK_ACCENT, glyph: "⌘" },
  provenance: { name: "Proof", subtitle: "Файлы и SHA-256", color: DUCK_ACCENT, glyph: "⌁" },
  "mora-boost": { name: "Mora Boost", subtitle: "Игровая производительность", color: DUCK_ACCENT, glyph: "⚡" },
  desktop: { name: "Duck Desktop", subtitle: "Оптимизация рабочего пространства", color: DUCK_ACCENT, glyph: "▦" },
  "mora-commons": { name: "Mora Commons", subtitle: "Единый центр приложений", color: DUCK_ACCENT, glyph: "✣" },
  files: { name: "Duck Files", subtitle: "Файлы и папки", color: DUCK_ACCENT, glyph: "▤" },
  terminal: { name: "Terminal", subtitle: "Локальная командная строка", color: DUCK_ACCENT, glyph: "›_" },
  settings: { name: "Settings", subtitle: "Настройки оболочки", color: DUCK_ACCENT, glyph: "⚙" },
  rights: { name: "Rights Center", subtitle: "Лицензии и происхождение", color: DUCK_ACCENT, glyph: "©" }
};

const windowLayer = document.getElementById("window-layer");
const activeAppLabel = document.getElementById("active-app");
const toastElement = document.getElementById("toast");
let nextZIndex = 10;
let toastTimeout = null;
const virtualWorkspace = new VirtualWorkspace();
let currentDirectoryId = "home";
let activeWorkspace = 1;
let currentLocale = "ru";
let consoleMode = false;
let consoleAudioEnabled = true;
let consoleAudioContext = null;
let contextTargetFile = null;
let contextOwnerPanel = null;
const quickState = { wifi: true, bluetooth: true, focus: false, airplane: false };
const notifications = [
  { id: "welcome", title: "Mora запущена", body: "Рабочая оболочка готова. Файловые и системные действия ограничены браузерным профилем.", app: "files", read: false },
  { id: "security", title: "Sentinel активен", body: "Профиль разрешений действует как настройка интерфейса и не заменяет нативный брокер доступа.", app: "security", read: false }
];

try {
  const savedLocale = localStorage.getItem(LOCALE_STORAGE_KEY);
  currentLocale = detectLocale(savedLocale);
  consoleMode = localStorage.getItem("duckos.mora.console-mode.v1") === "true";
  consoleAudioEnabled = localStorage.getItem("duckos.mora.console-audio.v1") !== "false";
  const savedWorkspace = Number(localStorage.getItem("duckos.mora.active-workspace.v1"));
  if ([1, 2, 3].includes(savedWorkspace)) activeWorkspace = savedWorkspace;
} catch {
  currentLocale = detectLocale(null);
}
try {
  const savedReads = JSON.parse(localStorage.getItem("duckos.mora.notifications.v1") || "[]");
  if (Array.isArray(savedReads)) notifications.forEach((item) => { item.read = savedReads.includes(item.id); });
} catch {
  // Fresh session starts with the two local onboarding notices.
}

let preferences = loadPreferences();
let pendingIntentPlan = null;

function applyPreferences() {
  document.documentElement.classList.toggle("reduce-motion", preferences.appearance.reducedMotion);
  document.documentElement.dataset.theme = "duck";
  document.body.classList.toggle("focus-mode", preferences.focusMode);
  document.documentElement.dataset.powerProfile = preferences.powerProfile;
  document.querySelector(".desktop")?.setAttribute("data-workspace", String(activeWorkspace));
  document.querySelectorAll("[data-workspace-select]").forEach((button) => {
    const selected = Number(button.dataset.workspaceSelect) === activeWorkspace;
    button.classList.toggle("is-active", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
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
      return '<p class="window-kicker">SETUPUP · МАСТЕР MORA</p><h2 class="window-heading">Настройте рабочее пространство</h2>' +
        '<p class="window-copy">Отметьте завершение локальной настройки. Установка ОС, разметка диска и настройка загрузчика здесь не выполняются.</p>' +
        '<div class="setting-block"><strong>Цветовая схема</strong><span>Единая палитра DuckOS: чёрный, белый и жёлтый.</span></div><div class="approval-actions"><button class="action-button" data-action="setup-complete">Завершить настройку</button></div>' +
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


function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}

function formatBytes(value) {
  if (!value) return "0 B";
  if (value < 1024) return value + " B";
  if (value < 1024 * 1024) return (value / 1024).toFixed(1) + " KB";
  return (value / (1024 * 1024)).toFixed(2) + " MB";
}

function filesPanelMarkup() {
  return '<p class="window-kicker">DUCK FILES · LOCAL WORKSPACE</p>' +
    '<h2 class="window-heading">Файлы и папки</h2>' +
    '<div class="files-toolbar">' +
      '<button type="button" data-files-action="back" aria-label="Назад" disabled>←</button>' +
      '<button type="button" data-files-action="forward" aria-label="Вперёд" disabled>→</button>' +
      '<button type="button" data-files-action="up" aria-label="Вверх">↑</button>' +
      '<input type="search" data-files-search placeholder="Поиск файлов и папок" aria-label="Поиск файлов и папок">' +
      '<button type="button" data-files-action="new-folder">+ Новая папка</button>' +
      '<button type="button" data-files-action="new-file">Новый файл</button>' +
      '<button type="button" data-files-action="upload">Загрузить</button>' +
      '<input type="file" data-files-upload accept=".txt,.md,.json,.rpr,.duck,.csv,.log,.xml,.html,.css,.js" multiple hidden>' +
      '<select data-files-sort aria-label="Сортировка"><option value="name">Имя</option><option value="date">Дата</option><option value="size">Размер</option><option value="type">Тип</option></select>' +
      '<span class="files-count" data-files-count></span>' +
      '<button type="button" data-files-action="view" data-files-view="list" aria-label="Сменить вид">▦</button>' +
    '</div>' +
    '<div class="files-layout" data-files-root>' +
      '<nav class="files-sidebar" aria-label="Папки">' +
        '<button type="button" data-files-folder="home" class="active">⌂ Home</button>' +
        '<button type="button" data-files-folder="desktop">▣ Desktop</button>' +
        '<button type="button" data-files-folder="documents">▤ Documents</button>' +
        '<button type="button" data-files-folder="downloads">↓ Downloads</button>' +
        '<button type="button" data-files-folder="pictures">▧ Pictures</button>' +
        '<button type="button" data-files-folder="applications">◇ Applications</button>' +
        '<button type="button" data-files-folder="system">⚙ System</button>' +
      '</nav>' +
      '<div class="files-main">' +
        '<nav class="files-breadcrumb" data-files-breadcrumb aria-label="Путь"></nav>' +
        '<ul class="files-list" data-files-list aria-label="Содержимое папки"></ul>' +
      '</div>' +
    '</div>' +
    '<section class="files-preview" data-files-preview aria-live="polite">' +
      '<h3 data-files-preview-title>Предпросмотр</h3><p data-files-preview-meta>Выберите файл для просмотра.</p>' +
      '<pre data-files-preview-content data-user-content></pre>' +
      '<button type="button" data-files-action="download" hidden>Скачать файл</button>' +
    '</section>' +
    '<p class="files-status" data-files-status role="status">Готово · локальное виртуальное пространство</p>' +
    '<p class="files-footnote" data-files-footnote>Виртуальное пространство Duck Files хранится в профиле браузера. Оно не является доступом к диску или настоящей файловой системе DuckOS. Текстовые файлы ограничены 2 MiB.</p>';
}

function filesAncestorChain(folderId) {
  const chain = [];
  let item = virtualWorkspace.get(folderId);
  while (item) {
    chain.unshift(item);
    item = item.parentId ? virtualWorkspace.get(item.parentId) : null;
  }
  return chain;
}

function navigateFiles(panel, folderId, remember = true) {
  const target = virtualWorkspace.get(folderId);
  if (!target || target.type !== "folder") return;
  const state = panel._filesState;
  if (remember && state.currentFolder !== folderId) {
    state.back.push(state.currentFolder);
    state.forward = [];
  }
  state.currentFolder = folderId;
  currentDirectoryId = folderId;
  state.selectedId = null;
  const search = panel.querySelector("[data-files-search]");
  if (search) search.value = "";
  renderFileManager(panel);
}

function renderFileManager(panel) {
  const state = panel._filesState;
  if (!state) return;
  const folder = virtualWorkspace.get(state.currentFolder);
  if (!folder || folder.type !== "folder") {
    state.currentFolder = "home";
    currentDirectoryId = "home";
  }
  const search = panel.querySelector("[data-files-search]");
  const query = search ? search.value.trim() : "";
  let items = query ? virtualWorkspace.search(query) : virtualWorkspace.list(state.currentFolder);
  const sort = panel.querySelector("[data-files-sort]")?.value || state.sort || "name";
  state.sort = sort;
  const compare = {
    name: (a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }),
    date: (a, b) => b.updatedAt.localeCompare(a.updatedAt),
    size: (a, b) => b.size - a.size,
    type: (a, b) => a.type.localeCompare(b.type) || a.name.localeCompare(b.name)
  }[sort] || ((a, b) => a.name.localeCompare(b.name));
  items = items.slice().sort((a, b) => a.type !== b.type ? (a.type === "folder" ? -1 : 1) : compare(a, b));
  const count = panel.querySelector("[data-files-count]");
  if (count) count.textContent = formatItemCount(items.length, currentLocale);
  const footnote = panel.querySelector("[data-files-footnote]");
  if (footnote && !virtualWorkspace.persistenceAvailable) {
    footnote.textContent = "Временная сессия: браузерное хранилище недоступно или переполнено. Изменения исчезнут после закрытия страницы.";
    footnote.classList.add("is-ephemeral");
  } else if (footnote) {
    footnote.textContent = "Виртуальное пространство Duck Files хранится в профиле браузера. Это не доступ к диску или настоящей файловой системе DuckOS. Текстовые файлы ограничены 2 MiB.";
    footnote.classList.remove("is-ephemeral");
  }

  const list = panel.querySelector("[data-files-list]");
  list.classList.toggle("grid-view", state.view === "grid");
  list.innerHTML = "";
  if (!items.length) {
    const empty = document.createElement("li");
    empty.className = "notification-empty";
    empty.textContent = query ? "Ничего не найдено." : "Нет элементов в этой папке.";
    list.append(empty);
  } else {
    items.forEach((item, index) => {
      const row = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "files-item" + (state.selectedId === item.id ? " selected" : "");
      button.dataset.fileOpen = item.id;
      button.dataset.fileId = item.id;
      button.style.animationDelay = Math.min(index * 18, 160) + "ms";
      const icon = document.createElement("span");
      icon.className = "files-item-icon";
      icon.textContent = item.type === "folder" ? "▣" : (item.name.endsWith(".json") ? "{}" : "▤");
      const name = document.createElement("span");
      name.className = "files-item-name";
      name.textContent = item.name;
      const meta = document.createElement("span");
      meta.className = "files-item-meta";
      meta.textContent = item.type === "folder" ? "Папка" : formatBytes(item.size);
      button.append(icon, name, meta);
      row.append(button);
      list.append(row);
    });
  }

  const breadcrumbs = panel.querySelector("[data-files-breadcrumb]");
  breadcrumbs.innerHTML = "";
  const chain = filesAncestorChain(state.currentFolder);
  chain.forEach((item, index) => {
    if (index) {
      const separator = document.createElement("span");
      separator.textContent = "›";
      separator.setAttribute("aria-hidden", "true");
      breadcrumbs.append(separator);
    }
    const crumb = document.createElement("button");
    crumb.type = "button";
    crumb.textContent = item.name;
    crumb.dataset.filesFolder = item.id;
    crumb.classList.toggle("active", index === chain.length - 1);
    breadcrumbs.append(crumb);
  });

  panel.querySelectorAll("[data-files-folder]").forEach((button) => {
    button.classList.toggle("active", button.dataset.filesFolder === state.currentFolder);
  });
  panel.querySelector('[data-files-action="back"]').disabled = state.back.length === 0;
  panel.querySelector('[data-files-action="forward"]').disabled = state.forward.length === 0;
  const selected = state.selectedId ? virtualWorkspace.get(state.selectedId) : null;
  const title = panel.querySelector("[data-files-preview-title]");
  const meta = panel.querySelector("[data-files-preview-meta]");
  const content = panel.querySelector("[data-files-preview-content]");
  const download = panel.querySelector('[data-files-action="download"]');
  if (!selected) {
    title.textContent = "Предпросмотр";
    meta.textContent = "Выберите файл для просмотра.";
    content.textContent = "";
    download.hidden = true;
  } else {
    title.textContent = selected.name;
    meta.textContent = selected.type === "folder" ? "Папка · " + virtualWorkspace.path(selected.id).join(" / ") :
      formatBytes(selected.size) + " · " + selected.mime + (selected.readonly ? " · образец только для чтения" : "");
    content.textContent = selected.type === "file" ? (selected.content.slice(0, 1800) || "Этот файл пуст.") : "Папка содержит " +
      virtualWorkspace.list(selected.id).length + " элементов.";
    download.hidden = selected.type !== "file";
  }
}

function initializeFileManager(appWindow) {
  const panel = appWindow.querySelector("[data-files-root]");
  if (!panel) return;
  panel._filesState = { currentFolder: "home", back: [], forward: [], selectedId: null, sort: "name", view: "list" };
  panel.querySelector("[data-files-search]").addEventListener("input", () => renderFileManager(panel));
  panel.querySelector("[data-files-sort]").addEventListener("change", () => renderFileManager(panel));
  renderFileManager(panel);
}

function setFilesStatus(panel, message) {
  const status = panel.querySelector("[data-files-status]");
  if (!status) return;
  status.textContent = virtualWorkspace.persistenceAvailable
    ? message
    : message + " (только в памяти этой страницы; сохранение недоступно)";
}

function downloadWorkspaceFile(item) {
  if (!item || item.type !== "file") return;
  const blob = new Blob([item.content], { type: item.mime || "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = item.name;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function handleFilesAction(button) {
  const panel = button.closest(".app-window");
  const root = panel?.querySelector("[data-files-root]");
  if (!panel || !root?._filesState) return;
  const state = root._filesState;
  const action = button.dataset.filesAction;
  if (action === "back" && state.back.length) {
    state.forward.push(state.currentFolder);
    state.currentFolder = state.back.pop();
    state.selectedId = null;
    renderFileManager(root);
    return;
  }
  if (action === "forward" && state.forward.length) {
    state.back.push(state.currentFolder);
    state.currentFolder = state.forward.pop();
    state.selectedId = null;
    renderFileManager(root);
    return;
  }
  if (action === "up") {
    const current = virtualWorkspace.get(state.currentFolder);
    if (current?.parentId) navigateFiles(root, current.parentId);
    return;
  }
  if (action === "new-folder") {
    const name = window.prompt("Имя новой папки");
    if (name === null) return;
    try {
      virtualWorkspace.createFolder(name, state.currentFolder);
      renderFileManager(root);
      setFilesStatus(panel, "Папка создана.");
    } catch (error) { setFilesStatus(panel, error.message); }
    return;
  }
  if (action === "new-file") {
    const name = window.prompt("Имя текстового файла", "Новая заметка.txt");
    if (name === null) return;
    try {
      const item = virtualWorkspace.createFile(name, "", state.currentFolder);
      state.selectedId = item.id;
      renderFileManager(root);
      setFilesStatus(panel, "Файл добавлен в виртуальное пространство.");
    } catch (error) { setFilesStatus(panel, error.message); }
    return;
  }
  if (action === "upload") {
    panel.querySelector("[data-files-upload]").click();
    return;
  }
  if (action === "view") {
    state.view = state.view === "list" ? "grid" : "list";
    button.setAttribute("aria-label", state.view === "grid" ? "Показать список" : "Показать сетку");
    renderFileManager(root);
    return;
  }
  if (action === "download") {
    const item = state.selectedId ? virtualWorkspace.get(state.selectedId) : null;
    if (item?.type === "file") downloadWorkspaceFile(item);
  }
}

function runTerminalCommand(root, rawCommand) {
  const output = root.querySelector("[data-terminal-output]");
  const command = String(rawCommand || "").trim();
  if (!command) return;
  const [verb, ...parts] = command.split(/\s+/);
  const argument = parts.join(" ").trim();
  const lines = ["mora:" + virtualWorkspace.path(currentDirectoryId).join("/") + "$ " + command];
  const folderItems = () => virtualWorkspace.list(currentDirectoryId);
  const current = () => virtualWorkspace.get(currentDirectoryId);
  const findChild = (name) => folderItems().find((item) => item.name.toLocaleLowerCase() === name.toLocaleLowerCase());

  try {
    switch (verb.toLowerCase()) {
      case "help":
        lines.push("help  ls  pwd  cd DIR  cat FILE  mkdir DIR  touch FILE  rm ITEM  date  whoami  neofetch  clear");
        lines.push("Only the local Duck Files workspace is available. No host shell commands are executed.");
        break;
      case "clear":
        output.textContent = "";
        return;
      case "pwd":
        lines.push("/" + virtualWorkspace.path(currentDirectoryId).join("/"));
        break;
      case "ls":
        lines.push(...folderItems().map((item) => (item.type === "folder" ? "[DIR] " : "      ") + item.name));
        if (!folderItems().length) lines.push("(empty)");
        break;
      case "cd": {
        if (!argument || argument === "/") { currentDirectoryId = "home"; break; }
        if (argument === "..") {
          currentDirectoryId = current()?.parentId || "home";
          break;
        }
        const target = findChild(argument);
        if (!target || target.type !== "folder") throw new Error("Directory not found: " + argument);
        currentDirectoryId = target.id;
        break;
      }
      case "cat": {
        if (!argument) throw new Error("Usage: cat FILE");
        const target = findChild(argument);
        if (!target || target.type !== "file") throw new Error("File not found: " + argument);
        lines.push(target.content || "(empty file)");
        break;
      }
      case "mkdir":
        if (!argument) throw new Error("Usage: mkdir DIR");
        virtualWorkspace.createFolder(argument, currentDirectoryId);
        lines.push("Directory created.");
        break;
      case "touch":
        if (!argument) throw new Error("Usage: touch FILE");
        virtualWorkspace.createFile(argument, "", currentDirectoryId);
        lines.push("File created.");
        break;
      case "rm": {
        if (!argument) throw new Error("Usage: rm ITEM");
        const target = findChild(argument);
        if (!target) throw new Error("Item not found: " + argument);
        virtualWorkspace.remove(target.id);
        lines.push("Removed from virtual workspace.");
        break;
      }
      case "date":
        lines.push(new Date().toLocaleString(currentLocale === "uk" ? "uk-UA" : currentLocale === "en" ? "en-US" : "ru-RU"));
        break;
      case "whoami":
        lines.push("mora-local-user (browser profile)");
        break;
      case "neofetch":
        lines.push("   DUCKOS / MORA");
        lines.push("   Workspace: browser-local");
        lines.push("   Locale: " + currentLocale.toUpperCase());
        lines.push("   Native shell: not connected");
        break;
      default:
        lines.push("Command not found. Type help. Native shell execution is disabled.");
    }
  } catch (error) {
    lines.push("error: " + error.message);
  }
  output.textContent += (output.textContent ? "\n" : "") + lines.join("\n");
  output.scrollTop = output.scrollHeight;
  const prompt = root.querySelector("[data-terminal-prompt]");
  if (prompt) prompt.textContent = "mora:" + virtualWorkspace.path(currentDirectoryId).join("/") + "$";
}

function settingsPanelMarkup() {
  return '<p class="window-kicker">MORA · SHELL SETTINGS</p><h2 class="window-heading">Настройки оболочки</h2>' +
    '<div class="settings-grid">' +
      '<label class="settings-control"><div><strong>Язык интерфейса</strong><small>RU · UK · EN · выбор сохраняется локально</small></div>' +
        '<select data-locale-select><option value="ru"' + (currentLocale === "ru" ? " selected" : "") + '>Русский</option>' +
        '<option value="uk"' + (currentLocale === "uk" ? " selected" : "") + '>Українська</option>' +
        '<option value="en"' + (currentLocale === "en" ? " selected" : "") + '>English</option></select></label>' +
      '<div class="settings-control"><div><strong>Движение интерфейса</strong><small>Учитывает системное предпочтение уменьшения движения</small></div>' +
        '<button class="permission-toggle" data-setting="reducedMotion" aria-pressed="' + String(preferences.appearance.reducedMotion) + '">' +
        (preferences.appearance.reducedMotion ? "Включено" : "Выключено") + '</button></div>' +
      '<div class="settings-control"><div><strong>Режим фокуса</strong><small>Приглушить второстепенные виджеты</small></div>' +
        '<button class="permission-toggle" data-setting="focusMode" aria-pressed="' + String(preferences.focusMode) + '">' +
        (preferences.focusMode ? "Включено" : "Выключено") + '</button></div>' +
      '<div class="settings-control"><div><strong>Аудиосигналы TV</strong><small>Короткие сигналы фокуса и выбора</small></div><button class="permission-toggle" data-console-audio-toggle aria-pressed="' + String(consoleAudioEnabled) + '">' + (consoleAudioEnabled ? "Включено" : "Выключено") + '</button></div>' +
      '<div class="settings-control"><div><strong>Режим ТВ</strong><small>Крупные карточки и управление D-pad / A / B / X / Y</small></div><button class="permission-toggle" data-console-mode-toggle aria-pressed="' + String(consoleMode) + '">' + (consoleMode ? "TV · ВКЛ" : "TV · ВЫКЛ") + '</button></div>' +
      '<div class="settings-control"><div><strong>Акцент DuckOS</strong><small>Единая палитра не переключается</small></div><strong>#FFD400</strong></div>' +
    '</div>' +
    '<div class="system-notice"><span class="notice-dot"></span><span>Только локальные настройки оболочки. Системные службы и оборудование браузеру не управляются.</span></div>';
}

function initializeTerminal(appWindow) {
  const root = appWindow.querySelector("[data-terminal-root]");
  const form = root?.querySelector("[data-terminal-form]");
  if (!root || !form) return;
  const prompt = root.querySelector("[data-terminal-prompt]");
  if (prompt) prompt.textContent = "mora:" + virtualWorkspace.path(currentDirectoryId).join("/") + "$";
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const input = form.querySelector("[data-terminal-command]");
    runTerminalCommand(root, input.value);
    input.value = "";
  });
}

function persistNotifications() {
  try {
    localStorage.setItem("duckos.mora.notifications.v1", JSON.stringify(notifications.filter((item) => item.read).map((item) => item.id)));
  } catch {
    showToast("Не удалось сохранить состояние уведомлений.");
  }
}

function renderNotifications() {
  const list = document.querySelector("[data-notification-list]");
  if (!list) return;
  list.innerHTML = "";
  if (!notifications.length) {
    const empty = document.createElement("p");
    empty.className = "notification-empty";
    empty.textContent = "Новых уведомлений нет.";
    list.append(empty);
  } else {
    notifications.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "notification-card" + (item.read ? "" : " unread");
      button.dataset.notificationOpen = item.id;
      const title = document.createElement("strong");
      title.textContent = item.title;
      const body = document.createElement("span");
      body.textContent = item.body;
      const time = document.createElement("time");
      time.textContent = item.read ? "Прочитано" : "Новое";
      button.append(title, body, time);
      list.append(button);
    });
  }
  applyTranslations(document.getElementById("notification-panel"), currentLocale);
}

function toggleFlyout(name, force) {
  const panelIds = {
    start: "start-menu",
    quick: "quick-panel",
    notifications: "notification-panel",
    clock: "clock-panel"
  };
  const target = document.getElementById(panelIds[name]);
  if (!target) return;
  const shouldOpen = force ?? target.hidden;
  document.querySelectorAll(".desktop-flyout").forEach((panel) => { panel.hidden = panel !== target || !shouldOpen; });
  document.querySelectorAll("[data-panel-toggle]").forEach((button) => {
    const active = button.dataset.panelToggle === name && shouldOpen;
    button.setAttribute("aria-expanded", String(active));
  });
  if (shouldOpen && name === "notifications") renderNotifications();
  if (shouldOpen && name === "clock") updateClock();
  if (shouldOpen && name === "start") {
    const search = target.querySelector("[data-start-search]");
    if (search) window.setTimeout(() => search.focus(), 40);
  }
}

function saveActiveWorkspace() {
  try { localStorage.setItem("duckos.mora.active-workspace.v1", String(activeWorkspace)); } catch {}
}

function switchWorkspace(number) {
  if (![1, 2, 3].includes(number) || number === activeWorkspace) return;
  activeWorkspace = number;
  saveActiveWorkspace();
  const desktop = document.querySelector(".desktop");
  desktop.dataset.workspace = String(number);
  desktop.classList.remove("workspace-changing");
  void desktop.offsetWidth;
  desktop.classList.add("workspace-changing");
  document.querySelectorAll("[data-workspace-select]").forEach((button) => {
    const active = Number(button.dataset.workspaceSelect) === number;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  windowLayer.querySelectorAll(".app-window").forEach((appWindow) => {
    appWindow.hidden = Number(appWindow.dataset.workspace || 1) !== activeWorkspace;
  });
  updateActiveApp();
}

function updateDemoMetrics() {
  const values = {
    cpu: 18 + Math.round(Math.random() * 34),
    memory: 42 + Math.round(Math.random() * 19),
    disk: 56 + Math.round(Math.random() * 12)
  };
  Object.entries(values).forEach(([key, value]) => {
    const row = document.querySelector('[data-metric="' + key + '"]');
    if (!row) return;
    row.querySelector("strong").textContent = value + "%";
    row.querySelector("b").style.width = value + "%";
  });
}

function renderDesktopContextMenu(x, y, items) {
  const menu = document.getElementById("desktop-context-menu");
  menu.innerHTML = items.map((item) => '<button type="button" role="menuitem" data-context-action="' +
    escapeHtml(item.action) + '"' + (item.disabled ? " disabled" : "") + '>' + escapeHtml(item.label) + '</button>').join("");
  menu.hidden = false;
  const left = Math.max(8, Math.min(x, window.innerWidth - menu.offsetWidth - 8));
  const top = Math.max(8, Math.min(y, window.innerHeight - menu.offsetHeight - 8));
  menu.style.left = left + "px";
  menu.style.top = top + "px";
}

function handleContextAction(action) {
  const menu = document.getElementById("desktop-context-menu");
  menu.hidden = true;
  if (action === "files") { openApp("files"); return; }
  if (action === "terminal") { openApp("terminal"); return; }
  if (action === "settings") { openApp("settings"); return; }
  if (!contextTargetFile) {
    if (action === "new-folder") {
      const name = window.prompt("Имя новой папки");
      if (name === null) return;
      try {
        virtualWorkspace.createFolder(name, "home");
        showToast("Папка создана.");
      } catch (error) { showToast(error.message); }
    }
    return;
  }
  const item = virtualWorkspace.get(contextTargetFile);
  const owner = contextOwnerPanel;
  if (!item) return;
  if (action === "open") {
    if (item.type === "folder" && owner) navigateFiles(owner, item.id);
    else if (item.type === "file" && owner) {
      owner._filesState.selectedId = item.id;
      renderFileManager(owner);
    }
  } else if (action === "properties") {
    if (item.type === "file" && owner) {
      owner._filesState.selectedId = item.id;
      renderFileManager(owner);
    } else if (owner) {
      setFilesStatus(owner.closest(".app-window"), item.name + " · папка · " + virtualWorkspace.list(item.id).length + " элементов");
    }
  } else if (action === "rename") {
    const name = window.prompt("Новое имя", item.name);
    if (name === null) return;
    try {
      virtualWorkspace.rename(item.id, name);
      if (owner) renderFileManager(owner);
      showToast("Изменения сохранены локально.");
    } catch (error) { showToast(error.message); }
  } else if (action === "delete") {
    if (!window.confirm("Удалить «" + item.name + "» из виртуального пространства?")) return;
    try {
      virtualWorkspace.remove(item.id);
      if (owner) {
        if (owner._filesState.selectedId === item.id) owner._filesState.selectedId = null;
        renderFileManager(owner);
      }
      showToast("Удалено из локального пространства.");
    } catch (error) { showToast(error.message); }
  } else if (action === "download") {
    downloadWorkspaceFile(item);
  }
  contextTargetFile = null;
  contextOwnerPanel = null;
}

function rightsPanelMarkup() {
  return '<p class="window-kicker">DUCKOS · CONTENT RIGHTS</p>' +
    '<h2 class="window-heading">Rights Center</h2>' +
    '<p class="window-copy">Единое место для лицензий, сохранений, авторства и проверки целостности. Подлинность подтверждается только нативным модулем DuckOS с доверенным ключом издателя.</p>' +
    '<div class="rights-status-grid">' +
      '<article class="rights-status-card"><strong>Доверенные издатели</strong><span class="rights-status status-unconfigured">НЕ НАСТРОЕНО</span><small>Ключи издателей не встроены и не выдумываются.</small></article>' +
      '<article class="rights-status-card"><strong>Нативная проверка</strong><span class="rights-status status-unverified">CLI / OPENSSL</span><small>Ed25519 + SHA-256 · проверка пакета до доверенного запуска.</small></article>' +
      '<article class="rights-status-card"><strong>Офлайн-доступ</strong><span class="rights-status status-policy">SIGNED TOKEN</span><small>Кэшированный токен действует только до offline_valid_until.</small></article>' +
      '<article class="rights-status-card"><strong>Журнал прав</strong><span class="rights-status status-policy">HASH CHAIN</span><small>Локальная цепочка событий; не неизменяемое хранилище.</small></article>' +
    '</div>' +
    '<section class="rights-section"><h3>Проверить метаданные</h3><p>Выберите токен лицензии или манифест контента. Браузер покажет только поля документа — статус всегда останется «НЕ ПРОВЕРЕНО».</p>' +
      '<div class="rights-import-row"><label class="file-picker">Entitlement JSON<input type="file" data-rights-document="entitlement" accept=".json,application/json"></label>' +
      '<label class="file-picker">Content manifest JSON<input type="file" data-rights-document="content" accept=".json,application/json"></label></div>' +
      '<div class="rights-document-preview" data-rights-preview aria-live="polite"><strong>Документ не выбран</strong><span>Источник, издатель, владелец профиля/устройства, срок действия и права появятся здесь после чтения метаданных.</span></div>' +
      '<p class="rights-warning">Просмотр JSON не проверяет подпись. Не используйте этот экран как доказательство покупки или разрешение на запуск.</p>' +
    '</section>' +
    '<section class="rights-section"><h3>Разделение прав</h3>' +
      '<div class="rights-rule"><strong>Профиль</strong><span>Лицензия следует за владельцем аккаунта после повторной авторизации у издателя.</span></div>' +
      '<div class="rights-rule"><strong>Домашнее устройство</strong><span>Подписанный home_device token может давать локальный офлайн-доступ всем профилям зарегистрированного устройства.</span></div>' +
      '<div class="rights-rule"><strong>Сохранения и пользовательские ассеты</strong><span>Сейвы отделены от игрового пакета; авторство тем, аватаров и модов хранится отдельно и помечается как self-declared, пока не подтверждено издателем.</span></div>' +
      '<div class="rights-rule"><strong>Перенос</strong><span>Экспорт сохраняет исходные подписанные манифесты и токены, но не переносит и не расширяет права. На новом устройстве лицензия перепроверяется.</span></div>' +
      '<div class="rights-rule"><strong>Захват экрана и клипы</strong><span>Политика capture может быть прочитана, но блокировка записи требует нативного compositor/capture broker.</span></div>' +
    '</section>' +
    '<section class="rights-section"><h3>Нативные команды проверки</h3>' +
      '<pre class="rights-cli">duckos rights verify-entitlement license.json --trusted-key studio=/path/studio.pub --profile-id PROFILE --device-id DEVICE --offline --action launch\n' +
      'duckos rights verify-content manifest.json ./package --trusted-key studio=/path/studio.pub\n' +
      'duckos rights build-transfer records.json rights-transfer.json\n' +
      'duckos rights validate-transfer rights-transfer.json\n' +
      'duckos rights audit-log</pre>' +
      '<p class="rights-warning">До подключения доверенного launcher и compositor результат проверки не является системным запретом обходного запуска или записи сторонним приложением.</p>' +
    '</section>';
}

function initializeRightsPanel(appWindow) {
  const preview = appWindow.querySelector("[data-rights-preview]");
  if (!preview) return;
  appWindow.querySelector(".window-body").addEventListener("change", async (event) => {
    const input = event.target.closest("[data-rights-document]");
    if (!input) return;
    const file = input.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      preview.textContent = "Документ превышает лимит 2 MiB.";
      return;
    }
    preview.replaceChildren();
    try {
      const documentData = JSON.parse(await file.text());
      if (!documentData || typeof documentData !== "object" || Array.isArray(documentData)) {
        throw new Error("Корневой элемент должен быть JSON-объектом.");
      }
      const content = documentData.content && typeof documentData.content === "object" ? documentData.content : {};
      const license = documentData.license && typeof documentData.license === "object" ? documentData.license : {};
      const publisher = documentData.publisher ?? documentData.issuer ?? {};
      const attribution = documentData.attribution ?? {};
      const values = [
        ["Файл", file.name],
        ["Тип документа", documentData.schema ?? "неизвестный"],
        ["Контент", content.title ?? content.id ?? "не указан"],
        ["Тип контента", content.kind ?? "не указан"],
        ["Издатель / подписант", publisher.id ?? "не указан"],
        ["Профиль", license.profile_id ?? "не привязан"],
        ["Домашнее устройство", license.home_device_id ?? "не привязано"],
        ["Область лицензии", license.scope ?? "не указана"],
        ["Права", Array.isArray(license.rights) ? license.rights.join(", ") : "не указаны"],
        ["Срок", license.expires_at ?? "не указан"],
        ["Создатель", typeof attribution.creator === "string" ? attribution.creator : (attribution.creator?.display_name ?? "не указан")],
        ["Источник", attribution.source?.reference ?? attribution.source?.description ?? "не указан"]
      ];
      const heading = document.createElement("strong");
      heading.textContent = input.dataset.rightsDocument === "entitlement" ? "Entitlement metadata" : "Content manifest metadata";
      const state = document.createElement("span");
      state.className = "rights-status status-unverified";
      state.textContent = "НЕ ПРОВЕРЕНО · просмотр метаданных";
      const list = document.createElement("dl");
      list.className = "rights-meta-list";
      values.forEach(([label, value]) => {
        const row = document.createElement("div");
        const term = document.createElement("dt");
        const detail = document.createElement("dd");
        term.textContent = label;
        detail.textContent = String(value);
        row.append(term, detail);
        list.append(row);
      });
      preview.append(heading, state, list);
    } catch (error) {
      preview.textContent = "Не удалось прочитать JSON: " + (error.message || "неизвестная ошибка");
    }
  });
}

function consoleFocusableElements() {
  return Array.from(document.querySelectorAll(
    'button:not([disabled]),a[href],input:not([type="hidden"]):not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex="0"]'
  )).filter((element) => {
    if (element.closest("[hidden],.app-window[hidden]")) return false;
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  });
}

function moveConsoleFocus(direction) {
  const elements = consoleFocusableElements();
  const current = elements.includes(document.activeElement) ? document.activeElement : null;
  const next = findDirectionalTarget(elements, current, direction);
  if (!next) return;
  next.focus({ preventScroll: true });
  next.scrollIntoView?.({
    block: "nearest",
    inline: "nearest",
    behavior: document.documentElement.classList.contains("reduce-motion") ? "auto" : "smooth"
  });
  playConsoleCue("move");
}

function playConsoleCue(kind = "move") {
  if (!consoleMode || !consoleAudioEnabled) return;
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return;
  try {
    consoleAudioContext ??= new AudioContextClass();
    if (consoleAudioContext.state === "suspended") consoleAudioContext.resume().catch(() => {});
    const oscillator = consoleAudioContext.createOscillator();
    const gain = consoleAudioContext.createGain();
    const frequency = kind === "select" ? 760 : kind === "back" ? 360 : kind === "details" ? 620 : 520;
    const now = consoleAudioContext.currentTime;
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(frequency, now);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.028, now + 0.006);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.055);
    oscillator.connect(gain);
    gain.connect(consoleAudioContext.destination);
    oscillator.start(now);
    oscillator.stop(now + 0.06);
  } catch {
    // Audio feedback is optional; unsupported browsers keep silent navigation.
  }
}

function handleConsoleAction(action) {
  const active = document.activeElement;
  if (action === "select") {
    const target = active?.closest?.("button,a,[role='button']");
    if (target) {
      target.click();
      playConsoleCue("select");
    }
    return;
  }
  if (action === "back") {
    const menu = document.getElementById("desktop-context-menu");
    if (menu && !menu.hidden) { menu.hidden = true; playConsoleCue("back"); return; }
    const flyout = document.querySelector(".desktop-flyout:not([hidden])");
    if (flyout) {
      toggleFlyout("start", false); toggleFlyout("quick", false);
      toggleFlyout("clock", false); toggleFlyout("notifications", false);
      playConsoleCue("back");
      return;
    }
    const filesWindow = windowLayer.querySelector('[data-window="files"]:not([hidden])');
    const files = filesWindow?.querySelector("[data-files-root]");
    if (files?._filesState) {
      const state = files._filesState;
      if (state.back.length) {
        handleFilesAction(filesWindow.querySelector('[data-files-action="back"]'));
        playConsoleCue("back");
        return;
      }
      if (state.currentFolder !== "home") {
        handleFilesAction(filesWindow.querySelector('[data-files-action="up"]'));
        playConsoleCue("back");
        return;
      }
    }
    closeTopWindow();
    playConsoleCue("back");
    return;
  }
  if (action === "details") {
    const file = active?.closest?.("[data-file-id]");
    if (file) {
      file.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, clientX: 30, clientY: 80 }));
      playConsoleCue("details");
      return;
    }
    const game = active?.closest?.("[data-demo-game]");
    if (game) {
      openApp("rights");
      playConsoleCue("details");
      return;
    }
    const app = active?.closest?.("[data-app]");
    if (app) {
      openApp(app.dataset.app === "illidia" ? "rights" : app.dataset.app);
      playConsoleCue("details");
    }
    return;
  }
  if (action === "search") {
    const filesSearch = windowLayer.querySelector('[data-window="files"]:not([hidden]) [data-files-search]');
    if (filesSearch) {
      filesSearch.focus();
    } else {
      toggleFlyout("start", true);
      document.querySelector("[data-start-search]")?.focus();
    }
    playConsoleCue("select");
  }
}

function setConsoleMode(enabled) {
  consoleMode = Boolean(enabled);
  document.documentElement.classList.toggle("console-mode", consoleMode);
  try { localStorage.setItem("duckos.mora.console-mode.v1", String(consoleMode)); } catch {}
  document.querySelectorAll("[data-console-mode-toggle]").forEach((button) => {
    button.setAttribute("aria-pressed", String(consoleMode));
    button.textContent = consoleMode ? "TV · ВКЛ" : "TV · ВЫКЛ";
  });
  if (consoleMode) gamepadInput.start();
  else gamepadInput.stop();
  showToast(consoleMode ? "Режим ТВ включён · D-pad / A / B / X / Y" : "Обычный режим Mora");
}

const gamepadInput = createGamepadInput({
  onAction: handleConsoleAction,
  onDirection: moveConsoleFocus,
  onConnection: (connected) => {
    if (connected) showToast("Геймпад обнаружен · можно управлять DuckOS");
  }
});

function panelMarkup(appId) {
  switch (appId) {
    case "rights":
      return rightsPanelMarkup();
    case "files":
      return filesPanelMarkup();
    case "terminal":
      return '<p class="window-kicker">MORA TERMINAL · VIRTUAL MODE</p><h2 class="window-heading">Терминал</h2>' +
        '<div class="terminal-panel" data-terminal-root><p class="window-copy">Доступ к настоящему терминалу не подключён. Команды выполняются только в виртуальном пространстве Mora.</p>' +
        '<div class="terminal-window"><pre data-terminal-output data-user-content>DuckOS Mora local workspace\\nType help to see available commands.</pre></div>' +
        '<form class="terminal-form" data-terminal-form><label data-terminal-prompt>mora:/Home$</label><input data-terminal-command autocomplete="off" spellcheck="false" aria-label="Команда" placeholder="help"></form></div>';
    case "settings":
      return settingsPanelMarkup();
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

function localeTag() {
  return currentLocale === "uk" ? "uk-UA" : currentLocale === "en" ? "en-US" : "ru-RU";
}

function updateClock() {
  const now = new Date();
  const locale = localeTag();
  const time = new Intl.DateTimeFormat(locale, { hour: "2-digit", minute: "2-digit" }).format(now);
  const date = new Intl.DateTimeFormat(locale, { weekday: "long", day: "numeric", month: "long", year: "numeric" }).format(now);
  document.getElementById("hero-clock").textContent = time;
  document.getElementById("status-time").textContent = time;
  document.getElementById("hero-date").textContent = date.charAt(0).toLocaleUpperCase(locale) + date.slice(1);
  const panelTime = document.querySelector("[data-panel-clock-time]");
  const panelDate = document.querySelector("[data-panel-clock-date]");
  if (panelTime) panelTime.textContent = time;
  if (panelDate) panelDate.textContent = date.charAt(0).toLocaleUpperCase(locale) + date.slice(1);
}

function showToast(message) {
  toastElement.textContent = translateText(message, currentLocale);
  toastElement.classList.add("visible");
  window.clearTimeout(toastTimeout);
  toastTimeout = window.setTimeout(() => toastElement.classList.remove("visible"), 2200);
}

function updateActiveApp() {
  const windows = Array.from(windowLayer.querySelectorAll(".app-window"))
    .filter((item) => !item.hidden && Number(item.dataset.workspace || 1) === activeWorkspace);
  if (windows.length === 0) {
    activeAppLabel.textContent = translateText("Рабочий стол", currentLocale);
  } else {
    windows.sort((a, b) => Number(b.style.zIndex) - Number(a.style.zIndex));
    const topWindow = windows[0];
    activeAppLabel.textContent = translateText(appDefinitions[topWindow.dataset.window].name, currentLocale);
  }
  document.querySelectorAll(".dock-item").forEach((item) => {
    const appWindow = windowLayer.querySelector('[data-window="' + item.getAttribute("data-app") + '"]');
    item.classList.toggle("is-running", Boolean(appWindow));
    item.classList.toggle("is-active", Boolean(appWindow && !appWindow.hidden && Number(appWindow.dataset.workspace || 1) === activeWorkspace));
  });
}

function focusWindow(appWindow) {
  appWindow.hidden = false;
  appWindow.classList.remove("is-minimizing", "is-closing");
  appWindow.style.zIndex = String(++nextZIndex);
  updateActiveApp();
}

function openApp(appId) {
  const definition = appDefinitions[appId];
  if (!definition) return;
  let appWindow = windowLayer.querySelector('[data-window="' + appId + '"]');
  if (appWindow) {
    appWindow.dataset.workspace = String(activeWorkspace);
    focusWindow(appWindow);
    return;
  }

  const displayName = translateText(definition.name, currentLocale);
  appWindow = document.createElement("section");
  appWindow.className = "app-window";
  appWindow.dataset.window = appId;
  appWindow.dataset.workspace = String(activeWorkspace);
  appWindow.setAttribute("role", "dialog");
  appWindow.setAttribute("aria-modal", "false");
  appWindow.setAttribute("aria-label", displayName);
  appWindow.style.setProperty("--accent", definition.color);
  appWindow.style.zIndex = String(++nextZIndex);
  appWindow.innerHTML =
    '<header class="window-titlebar"><span class="window-app-icon">' + definition.glyph + '</span><span class="window-title">' + escapeHtml(displayName) + '</span>' +
      '<div class="window-titlebar-actions">' +
        '<button type="button" data-window-action="minimize" aria-label="Свернуть" title="Свернуть">−</button>' +
        '<button type="button" data-window-action="maximize" aria-label="Развернуть" title="Развернуть">□</button>' +
        '<button type="button" class="window-close" data-action="close" aria-label="Закрыть">×</button>' +
      '</div></header>' +
    '<div class="window-body">' + panelMarkup(appId) + '</div>';
  windowLayer.appendChild(appWindow);
  renderExtensionEntries(appWindow);
  if (appId === "mora-commons") initializeCommonsPanel(appWindow);
  if (appId === "rights") initializeRightsPanel(appWindow);
  if (appId === "files") initializeFileManager(appWindow);
  if (appId === "terminal") initializeTerminal(appWindow);
  applyTranslations(appWindow, currentLocale);

  const layerTop = windowLayer.getBoundingClientRect().top;
  const left = Math.max(8, Math.round((window.innerWidth - appWindow.offsetWidth) / 2));
  const top = Math.max(8, Math.round((window.innerHeight - appWindow.offsetHeight) / 2) - 14 - layerTop);
  appWindow.style.left = left + "px";
  appWindow.style.top = top + "px";
  appWindow.style.transform = "none";
  focusWindow(appWindow);
  appWindow.querySelector(".window-close").focus();
  showToast(displayName + " открыто");
}

function minimizeWindow(appWindow) {
  if (!appWindow || appWindow.hidden) return;
  appWindow.classList.add("is-minimizing");
  window.setTimeout(() => {
    appWindow.hidden = true;
    appWindow.classList.remove("is-minimizing");
    updateActiveApp();
  }, 190);
}

function maximizeWindow(appWindow) {
  if (!appWindow) return;
  const maximized = appWindow.classList.toggle("is-maximized");
  const button = appWindow.querySelector('[data-window-action="maximize"]');
  if (button) {
    button.textContent = maximized ? "❐" : "□";
    button.setAttribute("aria-label", maximized ? "Восстановить" : "Развернуть");
    button.title = button.getAttribute("aria-label");
  }
}

function closeWindow(appWindow) {
  if (!appWindow) return;
  appWindow.classList.add("is-closing");
  window.setTimeout(() => {
    appWindow.remove();
    updateActiveApp();
  }, 170);
}

function closeTopWindow() {
  const windows = Array.from(windowLayer.querySelectorAll(".app-window"))
    .filter((item) => !item.hidden && Number(item.dataset.workspace || 1) === activeWorkspace);
  if (!windows.length) return;
  windows.sort((a, b) => Number(b.style.zIndex) - Number(a.style.zIndex));
  closeWindow(windows[0]);
}

function startWindowDrag(appWindow, header, pointerEvent) {
  if (pointerEvent.target.closest("button") || appWindow.classList.contains("is-maximized")) return;
  const rect = appWindow.getBoundingClientRect();
  const layerRect = windowLayer.getBoundingClientRect();
  const offsetX = pointerEvent.clientX - rect.left;
  const offsetY = pointerEvent.clientY - rect.top;
  header.setPointerCapture(pointerEvent.pointerId);
  focusWindow(appWindow);

  function move(moveEvent) {
    if (moveEvent.pointerId !== pointerEvent.pointerId) return;
    const width = appWindow.offsetWidth;
    const height = appWindow.offsetHeight;
    const maxLeft = Math.max(8, window.innerWidth - width - 8);
    const maxTop = Math.max(8, window.innerHeight - height - 72 - layerRect.top);
    const left = Math.min(maxLeft, Math.max(8, moveEvent.clientX - offsetX - layerRect.left));
    const top = Math.min(maxTop, Math.max(8, moveEvent.clientY - offsetY - layerRect.top));
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
  const consoleAudioToggle = event.target.closest("[data-console-audio-toggle]");
  if (consoleAudioToggle) {
    consoleAudioEnabled = !consoleAudioEnabled;
    try { localStorage.setItem("duckos.mora.console-audio.v1", String(consoleAudioEnabled)); } catch {}
    consoleAudioToggle.setAttribute("aria-pressed", String(consoleAudioEnabled));
    consoleAudioToggle.textContent = consoleAudioEnabled ? "Включено" : "Выключено";
    showToast(consoleAudioEnabled ? "Аудиосигналы включены." : "Аудиосигналы выключены.");
    return;
  }
  const panelToggle = event.target.closest("[data-panel-toggle]");
  if (panelToggle) {
    toggleFlyout(panelToggle.dataset.panelToggle);
    return;
  }
  const panelClose = event.target.closest("[data-panel-close]");
  if (panelClose) {
    toggleFlyout("start", false);
    toggleFlyout("quick", false);
    toggleFlyout("notifications", false);
    return;
  }
  if (!event.target.closest(".desktop-flyout")) {
    toggleFlyout("start", false);
    toggleFlyout("quick", false);
    toggleFlyout("notifications", false);
  }

  const contextAction = event.target.closest("[data-context-action]");
  if (contextAction) {
    handleContextAction(contextAction.dataset.contextAction);
    return;
  }

  const workspaceButton = event.target.closest("[data-workspace-select]");
  if (workspaceButton) {
    switchWorkspace(Number(workspaceButton.dataset.workspaceSelect));
    return;
  }

  const windowAction = event.target.closest("[data-window-action]");
  if (windowAction) {
    const owner = windowAction.closest(".app-window");
    if (windowAction.dataset.windowAction === "minimize") minimizeWindow(owner);
    else if (windowAction.dataset.windowAction === "maximize") maximizeWindow(owner);
    return;
  }

  const filesFolder = event.target.closest("[data-files-folder]");
  if (filesFolder) {
    const owner = filesFolder.closest(".app-window");
    const root = owner?.querySelector("[data-files-root]");
    if (root?._filesState) navigateFiles(root, filesFolder.dataset.filesFolder);
    return;
  }

  const filesAction = event.target.closest("[data-files-action]");
  if (filesAction) {
    handleFilesAction(filesAction);
    return;
  }

  const fileOpen = event.target.closest("[data-file-open]");
  if (fileOpen) {
    const owner = fileOpen.closest(".app-window");
    const root = owner?.querySelector("[data-files-root]");
    const item = virtualWorkspace.get(fileOpen.dataset.fileOpen);
    if (root?._filesState && item) {
      if (item.type === "folder") navigateFiles(root, item.id);
      else {
        root._filesState.selectedId = item.id;
        renderFileManager(root);
        setFilesStatus(owner, "Выбран файл: " + item.name);
      }
    }
    return;
  }

  const quickToggle = event.target.closest("[data-quick-id]");
  if (quickToggle) {
    const id = quickToggle.dataset.quickId;
    const enabled = quickToggle.getAttribute("aria-pressed") !== "true";
    quickState[id] = enabled;
    quickToggle.setAttribute("aria-pressed", String(enabled));
    quickToggle.classList.toggle("is-on", enabled);
    if (id === "focus") {
      preferences.focusMode = enabled;
      persistPreferences();
      updateWorkspacePanel();
    }
    showToast(id === "focus" ? "Режим фокуса оболочки обновлён." :
      "Изменён локальный индикатор " + id + ". Нативное устройство не переключалось.");
    return;
  }

  const notificationAction = event.target.closest("[data-notification-action]");
  if (notificationAction) {
    if (notificationAction.dataset.notificationAction === "read") {
      notifications.forEach((item) => { item.read = true; });
    } else if (notificationAction.dataset.notificationAction === "clear") {
      notifications.splice(0, notifications.length);
    }
    persistNotifications();
    renderNotifications();
    return;
  }

  const notificationOpen = event.target.closest("[data-notification-open]");
  if (notificationOpen) {
    const item = notifications.find((entry) => entry.id === notificationOpen.dataset.notificationOpen);
    if (item) {
      item.read = true;
      persistNotifications();
      renderNotifications();
      toggleFlyout("notifications", false);
      openApp(item.app);
    }
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

  const dockItem = event.target.closest(".dock-item");
  if (dockItem) {
    const dockWindow = windowLayer.querySelector('[data-window="' + dockItem.dataset.app + '"]');
    if (dockWindow && !dockWindow.hidden && Number(dockWindow.dataset.workspace || 1) === activeWorkspace) {
      minimizeWindow(dockWindow);
      return;
    }
  }

  const opener = event.target.closest("[data-app]");
  if (opener) {
    toggleFlyout("start", false);
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
  const startSearch = event.target.closest("[data-start-search]");
  if (startSearch) {
    const query = startSearch.value.trim().toLocaleLowerCase();
    document.querySelectorAll(".start-app").forEach((item) => {
      const haystack = item.textContent.toLocaleLowerCase();
      item.hidden = Boolean(query) && !haystack.includes(query);
    });
    return;
  }
  const quickRange = event.target.closest("[data-quick-range]");
  if (quickRange) {
    const output = document.querySelector('[data-quick-value="' + quickRange.dataset.quickRange + '"]');
    if (output) output.textContent = quickRange.value + "%";
    return;
  }
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

windowLayer.addEventListener("dblclick", (event) => {
  const header = event.target.closest(".window-titlebar");
  const appWindow = event.target.closest(".app-window");
  if (!header || !appWindow || event.target.closest("button")) return;
  maximizeWindow(appWindow);
});

document.addEventListener("keydown", (event) => {
  if (consoleMode && !isEditableTarget(event.target)) {
    const key = event.key.toLowerCase();
    if (["arrowup", "arrowdown", "arrowleft", "arrowright"].includes(key)) {
      event.preventDefault();
      moveConsoleFocus(key.slice(5));
      return;
    }
    if (["a", "b", "x", "y"].includes(key)) {
      event.preventDefault();
      handleConsoleAction(({ a: "select", b: "back", x: "details", y: "search" })[key]);
      return;
    }
  }
  if (event.altKey && !event.ctrlKey && !event.metaKey && ["1", "2", "3"].includes(event.key)) {
    event.preventDefault();
    switchWorkspace(Number(event.key));
    return;
  }
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "f") {
    event.preventDefault();
    openApp("files");
    window.setTimeout(() => windowLayer.querySelector('[data-window="files"] [data-files-search]')?.focus(), 80);
    return;
  }
  if (event.key === "Escape") {
    const menu = document.getElementById("desktop-context-menu");
    if (menu && !menu.hidden) { menu.hidden = true; return; }
    const openFlyout = document.querySelector(".desktop-flyout:not([hidden])");
    if (openFlyout) {
      toggleFlyout("start", false);
      toggleFlyout("quick", false);
      toggleFlyout("notifications", false);
      return;
    }
    closeTopWindow();
  }
});
document.addEventListener("contextmenu", (event) => {
  const fileItem = event.target.closest("[data-file-id]");
  if (fileItem) {
    event.preventDefault();
    contextTargetFile = fileItem.dataset.fileId;
    contextOwnerPanel = fileItem.closest("[data-files-root]");
    const item = virtualWorkspace.get(contextTargetFile);
    const actions = [{ action: "open", label: item?.type === "folder" ? "Открыть папку" : "Предпросмотр" },
      { action: "properties", label: "Свойства" },
      { action: "rename", label: "Переименовать", disabled: item?.readonly },
      { action: "delete", label: "Удалить", disabled: item?.readonly },
      { action: "download", label: "Скачать", disabled: item?.type !== "file" }];
    renderDesktopContextMenu(event.clientX, event.clientY, actions);
    return;
  }
  if (event.target.closest(".desktop") && !event.target.closest(".app-window,.desktop-flyout,.desktop-context-menu,button,input,textarea,select")) {
    event.preventDefault();
    contextTargetFile = null;
    contextOwnerPanel = null;
    renderDesktopContextMenu(event.clientX, event.clientY, [
      { action: "files", label: "Открыть Duck Files" },
      { action: "terminal", label: "Открыть Terminal" },
      { action: "settings", label: "Настройки" },
      { action: "new-folder", label: "Создать папку в Home" }
    ]);
  }
});

document.addEventListener("click", (event) => {
  const menu = document.getElementById("desktop-context-menu");
  if (menu && !menu.hidden && !event.target.closest(".desktop-context-menu")) menu.hidden = true;
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
    const settingsWindow = windowLayer.querySelector('[data-window="settings"]');
    if (settingsWindow) {
      settingsWindow.querySelector(".window-body").innerHTML = settingsPanelMarkup();
      applyTranslations(settingsWindow, currentLocale);
    }
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
  const localeSelect = event.target.closest("[data-locale-select]");
  if (localeSelect) {
    const nextLocale = localeSelect.value;
    if (!["ru", "uk", "en"].includes(nextLocale)) return;
    currentLocale = nextLocale;
    try { localStorage.setItem(LOCALE_STORAGE_KEY, currentLocale); } catch {}
    applyTranslations(document, currentLocale);
    updateClock();
    renderNotifications();
    document.querySelectorAll('[data-window="settings"]').forEach((appWindow) => {
      const select = appWindow.querySelector("[data-locale-select]");
      if (select) select.value = currentLocale;
    });
    showToast("Язык интерфейса изменён.");
    return;
  }

  const workspaceUpload = event.target.closest("[data-files-upload]");
  if (workspaceUpload) {
    const owner = workspaceUpload.closest(".app-window");
    const root = owner?.querySelector("[data-files-root]");
    const files = Array.from(workspaceUpload.files || []);
    if (!root?._filesState || !files.length) return;
    for (const file of files) {
      const extension = file.name.split(".").pop().toLowerCase();
      const allowed = ["txt", "md", "json", "rpr", "duck", "csv", "log", "xml", "html", "css", "js"];
      if (!allowed.includes(extension) || file.size > MAX_WORKSPACE_FILE_BYTES) {
        setFilesStatus(owner, "Не добавлен " + file.name + ": поддерживаются текстовые файлы до 2 MiB.");
        continue;
      }
      try {
        const content = await file.text();
        const item = virtualWorkspace.createFile(file.name, content, root._filesState.currentFolder, file.type || "text/plain");
        root._filesState.selectedId = item.id;
        setFilesStatus(owner, "Файл добавлен в виртуальное пространство.");
      } catch (error) {
        setFilesStatus(owner, error.message);
      }
    }
    workspaceUpload.value = "";
    renderFileManager(root);
    return;
  }

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
switchWorkspace(activeWorkspace);
setConsoleMode(consoleMode);
updateClock();
window.setInterval(updateClock, 1000);
updateDemoMetrics();
window.setInterval(updateDemoMetrics, 2200);
renderNotifications();
updateActiveApp();

applyTranslations(document, currentLocale);
if (typeof MutationObserver !== "undefined") {
  const translationObserver = new MutationObserver((records) => {
    for (const record of records) {
      record.addedNodes.forEach((node) => {
        if (node.nodeType === 1) applyTranslations(node, currentLocale);
        else if (node.nodeType === 3 && node.parentElement) {
          const next = translateText(node.nodeValue, currentLocale);
          if (next !== node.nodeValue) node.nodeValue = next;
        }
      });
    }
  });
  translationObserver.observe(document.body, { childList: true, subtree: true, characterData: true });
}

if ("serviceWorker" in navigator &&
    (location.protocol === "https:" || location.hostname === "localhost" || location.hostname === "127.0.0.1")) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./service-worker.js").catch(() => {
      // The desktop remains usable when offline installation is unavailable.
    });
  });
}