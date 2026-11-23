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
  "mora-ai": { name: "Mora AI", subtitle: "Намерения и планы", color: "#C19A6A", glyph: "✦" },
  security: { name: "Sentinel", subtitle: "Права и доверие", color: "#829078", glyph: "◇" },
  updates: { name: "Restore", subtitle: "Обновления и откат", color: "#A97866", glyph: "↶" },
  runtime: { name: "Bridge", subtitle: "PE и ELF инспектор", color: "#948F7D", glyph: "⇄" },
  workspace: { name: "Control", subtitle: "Среда и питание", color: "#A08B98", glyph: "⌘" },
  provenance: { name: "Proof", subtitle: "Файлы и SHA-256", color: "#8A8A76", glyph: "⌁" }
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
      return '<p class="window-kicker">BRIDGE · INSPECTION ONLY</p><h2 class="window-heading">Инспектор исполняемых файлов</h2>' +
        '<p class="window-copy">Выберите локальный EXE, DLL или ELF. Mora проверит заголовок и разрядность, не запуская файл и не отправляя его в сеть.</p>' +
        '<label class="file-picker">Выбрать файл<input type="file" data-executable-file accept=".exe,.dll,.so"></label>' +
        '<div class="inspection-report" data-runtime-report>Файл ещё не выбран.</div>' +
        '<div class="system-notice warning"><span class="notice-dot"></span><span>Запуск Windows-программ, DirectX/Vulkan translation и античитов через этот браузерный интерфейс невозможен. Native runtime пока не подключён.</span></div>';
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
  const executableInput = event.target.closest("[data-executable-file]");
  if (executableInput) {
    const report = executableInput.closest(".app-window").querySelector("[data-runtime-report]");
    const file = executableInput.files && executableInput.files[0];
    if (!file) return;
    report.textContent = "Читаю заголовок файла локально…";
    try {
      const result = await inspectExecutable(file);
      report.textContent = file.name + "\n" + file.size.toLocaleString("ru-RU") + " байт\n" +
        result.format + " · " + result.architecture + "\n" + result.detail;
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