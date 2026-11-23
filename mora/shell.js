const WORKSPACES = [
  { id: "home", label: "Дом", hint: "Главное пространство" },
  { id: "studio", label: "Студия", hint: "Работа и инструменты" },
  { id: "play", label: "Игры", hint: "Игровые приложения" },
  { id: "system", label: "Система", hint: "Настройки и обслуживание" }
];

const DIRECTIONS = [
  { id: 1, group: "arch", title: "Разработать Функционал Единовременно", maturity: "partial", detail: "Оболочка Mora, CLI и Reaper-контракты связаны. Нативный compositor и системный session manager ещё не реализованы." },
  { id: 2, group: "arch", title: "Спроектировать Возможности Одновременно", maturity: "partial", detail: "Архитектура разделяет UI, Reaper-политику и привилегированные host-интерфейсы." },
  { id: 3, group: "arch", title: "Реализовать Инструментарий Комплексно", maturity: "partial", detail: "Существуют CLI, проверки, инспекторы совместимости и desktop-контракты. Нативный набор системных инструментов неполон." },
  { id: 4, group: "arch", title: "Создать Оснащение Целиком", maturity: "planned", detail: "Физические драйверы, аудиостек, compositor и аппаратное управление требуют native backend." },
  { id: 5, group: "arch", title: "Внедрить Оснащённость Полностью", maturity: "planned", detail: "Поставка системных служб и загрузочного образа остаётся отдельным этапом bring-up." },
  { id: 6, group: "arch", title: "Интегрировать Компетенции Разом", maturity: "partial", detail: "Reaper содержит проверяемые контракты boot, IPC, capabilities, drivers, storage и UI policy." },
  { id: 7, group: "arch", title: "Модернизировать Интеграции Сразу", maturity: "partial", detail: "Mora соединена с локальными контрактами и CLI. Аутентифицированный привилегированный host broker ещё не подключён." },
  { id: 8, group: "auto", title: "Оптимизировать Подсистемы Моментально", maturity: "specified", detail: "Есть правила бюджетов кадров, телеметрии и обратного давления. Реальные измерения нужны от native providers." },
  { id: 9, group: "auto", title: "Автоматизировать Механизмы Параллельно", maturity: "planned", detail: "Reaper описывает выбор worker и supervisor policy, но не исполняет preemptive scheduler или параллельный runtime ОС." },
  { id: 10, group: "auto", title: "Усовершенствовать Инструменты Совокупно", maturity: "partial", detail: "CLI и диагностические инструменты работают в пользовательском окружении; системные операции остаются ограниченными." },
  { id: 11, group: "auto", title: "Переработать Компоненты Системно", maturity: "partial", detail: "Модули разделены по границам kernel policy, services, storage, security, UI и compatibility." },
  { id: 12, group: "auto", title: "Масштабировать Модули Массово", maturity: "specified", detail: "Контракты ограничивают очереди, историю телеметрии и размеры сессии. Распределённый runtime ещё не внедрён." },
  { id: 13, group: "auto", title: "Адаптировать Реализация Пакетно", maturity: "planned", detail: "Нужны проверенные платформенные адаптеры и общий ABI для Linux, Windows и будущих архитектур." },
  { id: 14, group: "auto", title: "Унифицировать Автоматизация Централизованно", maturity: "partial", detail: "Единые правила тем, сессий, уведомлений и разрешённых команд находятся в Reaper." },
  { id: 15, group: "scale", title: "Синхронизировать Оптимизация Комплексно", maturity: "partial", detail: "Есть детерминированный LWW-регистр и журнал последовательности. Полноценное постоянное хранилище и синхронизация ещё не готовы." },
  { id: 16, group: "scale", title: "Имплементировать Совместимость Автоматически", maturity: "partial", detail: "PE/ELF inspection и запуск через внешние Wine-compatible runtimes есть в DuckBridge/Illidia. Нативный Win32 runtime отсутствует." },
  { id: 17, group: "scale", title: "Расширить Производительность Синхронно", maturity: "specified", detail: "Есть классификаторы frame budget и telemetry. NPU/GPU/температура не считываются этой браузерной оболочкой." },
  { id: 18, group: "scale", title: "Ускорить Масштабируемость Последовательно", maturity: "specified", detail: "Есть лимиты окон, уведомлений и контрактов. Нагрузочные результаты должны подтверждаться измерениями." },
  { id: 19, group: "scale", title: "Комплексно усовершенствовать Универсальность Безостановочно", maturity: "specified", detail: "Контракты отделяют общие состояния оболочки от платформенных адаптеров; parity между платформами ещё не достигнута." },
  { id: 20, group: "scale", title: "Рефакторить Расширяемость Одномоментно", maturity: "partial", detail: "Модули UI policy, window management, notifications и desktop command authorization разделены и покрываются Reaper tests." }
];

const GROUPS = [
  { id: "all", label: "Все · 20" },
  { id: "arch", label: "Ядро · 7" },
  { id: "auto", label: "Автоматизация · 7" },
  { id: "scale", label: "Совместимость · 6" }
];

const MATURITY = {
  specified: "Спецификация",
  planned: "Запланировано",
  partial: "Частично"
};

const PALETTE_NAMES = { amber: "Mora Amber", dark: "Тёмная", light: "Светлая" };
const SESSION_KEY = "mora.desktop-session.v1";

function readWorkspace() {
  try {
    const saved = window.localStorage.getItem(SESSION_KEY);
    return WORKSPACES.some((workspace) => workspace.id === saved) ? saved : "home";
  } catch {
    return "home";
  }
}

function saveWorkspace(workspaceId) {
  try {
    window.localStorage.setItem(SESSION_KEY, workspaceId);
  } catch {
    // The desktop remains usable when browser storage is unavailable.
  }
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function createWorkspaceSwitcher(onSelect) {
  const nav = element("nav", "workspace-switcher");
  nav.setAttribute("aria-label", "Виртуальные рабочие пространства");

  for (const workspace of WORKSPACES) {
    const button = element("button", "workspace-tab", workspace.label);
    button.type = "button";
    button.dataset.workspace = workspace.id;
    button.title = workspace.hint;
    button.addEventListener("click", () => onSelect(workspace.id));
    nav.appendChild(button);
  }

  return nav;
}

function createCommandPalette() {
  const overlay = element("div", "command-overlay");
  overlay.hidden = true;
  overlay.innerHTML = [
    '<section class="command-palette" role="dialog" aria-modal="true" aria-label="Командная палитра">',
    '  <div class="command-palette-heading"><span>DUCKOS · MORA SHELL</span><kbd>ESC</kbd></div>',
    '  <label class="command-input-wrap">',
    '    <span aria-hidden="true">⌕</span>',
    '    <input class="command-input" type="text" autocomplete="off" spellcheck="false" placeholder="Открыть приложение или ввести команду…">',
    '  </label>',
    '  <div class="command-hint">Команды: /help · /status · /workspace play · /theme dark · /focus on</div>',
    '  <div class="command-results" role="listbox" aria-label="Результаты"></div>',
    '</section>'
  ].join("");
  return overlay;
}

function commandTokens(value) {
  return value.trim().toLowerCase().split(/\s+/).filter(Boolean);
}

function getWorkspaceWindow(windowLayer, appId) {
  return windowLayer.querySelector('[data-window="' + CSS.escape(appId) + '"]');
}

function buildMatrix(container) {
  if (container.querySelector(".shell-directions")) return;

  const section = element("section", "shell-directions");
  const heading = element("div", "shell-directions-heading");
  const copy = element("div");
  copy.append(
    element("p", "window-kicker", "DUCKOS · REAPER SYSTEM MATRIX"),
    element("h3", "", "20 системных направлений"),
    element("p", "shell-directions-note", "Статусы отражают текущую зрелость контрактов и кода, а не условные проценты готовности.")
  );
  heading.appendChild(copy);
  section.appendChild(heading);

  const tools = element("div", "shell-matrix-tools");
  const search = element("input", "shell-matrix-search");
  search.type = "search";
  search.placeholder = "Поиск по направлениям…";
  search.setAttribute("aria-label", "Поиск по системным направлениям");
  tools.appendChild(search);

  const filters = element("div", "shell-matrix-filters");
  let selectedGroup = "all";
  for (const group of GROUPS) {
    const button = element("button", "shell-matrix-filter" + (group.id === selectedGroup ? " active" : ""), group.label);
    button.type = "button";
    button.addEventListener("click", () => {
      selectedGroup = group.id;
      filters.querySelectorAll("button").forEach((item) => item.classList.toggle("active", item.dataset.group === selectedGroup));
      render();
    });
    button.dataset.group = group.id;
    filters.appendChild(button);
  }
  tools.appendChild(filters);
  section.appendChild(tools);

  const list = element("div", "shell-matrix-list");
  const inspector = element("div", "shell-matrix-inspector");
  const inspectorTitle = element("strong", "", "Выберите направление");
  const inspectorText = element("p", "", "Здесь появится описание текущей реализации и оставшихся системных границ.");
  inspector.append(inspectorTitle, inspectorText);

  let selectedId = 1;

  function selectTask(task) {
    selectedId = task.id;
    inspector.replaceChildren();
    inspectorTitle.textContent = "№" + String(task.id).padStart(2, "0") + " · " + task.title;
    const badge = element("span", "maturity-pill maturity-" + task.maturity, MATURITY[task.maturity]);
    inspector.append(inspectorTitle, badge, element("p", "", task.detail));
    list.querySelectorAll(".shell-matrix-item").forEach((item) => item.classList.toggle("selected", Number(item.dataset.id) === selectedId));
  }

  function render() {
    const query = search.value.trim().toLocaleLowerCase("ru-RU");
    const tasks = DIRECTIONS.filter((task) => {
      const inGroup = selectedGroup === "all" || task.group === selectedGroup;
      const matches = !query || task.title.toLocaleLowerCase("ru-RU").includes(query) || String(task.id) === query;
      return inGroup && matches;
    });

    list.replaceChildren();
    for (const task of tasks) {
      const button = element("button", "shell-matrix-item" + (task.id === selectedId ? " selected" : ""));
      button.type = "button";
      button.dataset.id = String(task.id);
      const top = element("span", "shell-matrix-top");
      top.append(
        element("span", "shell-matrix-number", "№" + String(task.id).padStart(2, "0")),
        element("span", "maturity-pill maturity-" + task.maturity, MATURITY[task.maturity])
      );
      button.append(top, element("strong", "", task.title));
      button.addEventListener("click", () => selectTask(task));
      list.appendChild(button);
    }
    if (!tasks.length) {
      list.appendChild(element("p", "shell-matrix-empty", "Совпадений не найдено."));
    }
    const selected = tasks.find((task) => task.id === selectedId);
    if (selected) selectTask(selected);
    else if (tasks.length) selectTask(tasks[0]);
  }

  search.addEventListener("input", render);
  section.append(list, inspector);
  container.appendChild(section);
  render();
}

export function initDesktopShell({
  appDefinitions,
  openApp,
  closeTopWindow,
  showToast,
  updateActiveApp,
  preferences,
  persistPreferences
}) {
  const desktop = document.getElementById("desktop");
  const statusbar = desktop?.querySelector(".statusbar");
  const systemStatus = desktop?.querySelector(".system-status");
  const windowLayer = document.getElementById("window-layer");
  if (!desktop || !statusbar || !systemStatus || !windowLayer) return;

  let activeWorkspace = readWorkspace();
  const palette = createCommandPalette();
  desktop.appendChild(palette);

  const workspaceSwitcher = createWorkspaceSwitcher(switchWorkspace);
  statusbar.insertBefore(workspaceSwitcher, systemStatus);

  const commandButton = element("button", "status-control shell-command-button", "⌕");
  commandButton.type = "button";
  commandButton.setAttribute("aria-label", "Открыть командную палитру");
  commandButton.title = "Команды и запуск приложений · Ctrl+K";
  systemStatus.insertBefore(commandButton, systemStatus.firstChild);

  const paletteInput = palette.querySelector(".command-input");
  const paletteResults = palette.querySelector(".command-results");

  function updateSwitcher() {
    workspaceSwitcher.querySelectorAll("[data-workspace]").forEach((button) => {
      const active = button.dataset.workspace === activeWorkspace;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
  }

  function updateWindows() {
    windowLayer.querySelectorAll(".app-window").forEach((appWindow) => {
      if (!appWindow.dataset.workspace) appWindow.dataset.workspace = activeWorkspace;
      const visible = appWindow.dataset.workspace === activeWorkspace && appWindow.dataset.minimized !== "true";
      appWindow.hidden = !visible;
    });
    updateActiveApp();
    updateSwitcher();
  }

  function switchWorkspace(workspaceId) {
    if (!WORKSPACES.some((workspace) => workspace.id === workspaceId)) return;
    activeWorkspace = workspaceId;
    saveWorkspace(workspaceId);
    updateWindows();
    showToast("Пространство: " + WORKSPACES.find((workspace) => workspace.id === workspaceId).label);
  }

  function decorateWindow(appWindow) {
    if (appWindow.dataset.shellDecorated === "true") return;
    appWindow.dataset.shellDecorated = "true";
    appWindow.dataset.workspace = appWindow.dataset.workspace || activeWorkspace;

    const titlebar = appWindow.querySelector(".window-titlebar");
    const closeButton = titlebar?.querySelector(".window-close");
    if (titlebar && closeButton) {
      const controls = element("div", "window-controls");
      const minimize = element("button", "window-tool", "—");
      minimize.type = "button";
      minimize.dataset.windowAction = "minimize";
      minimize.setAttribute("aria-label", "Свернуть окно");
      const maximize = element("button", "window-tool", "□");
      maximize.type = "button";
      maximize.dataset.windowAction = "maximize";
      maximize.setAttribute("aria-label", "Развернуть или восстановить окно");
      controls.append(minimize, maximize);
      titlebar.insertBefore(controls, closeButton);
    }

    if (appWindow.dataset.window === "workspace") {
      const body = appWindow.querySelector(".window-body");
      if (body) buildMatrix(body);
    }
  }

  function openPalette() {
    palette.hidden = false;
    paletteInput.value = "";
    renderResults();
    window.requestAnimationFrame(() => paletteInput.focus());
  }

  function closePalette() {
    palette.hidden = true;
    commandButton.focus();
  }

  function appMatches(query) {
    const normalized = query.trim().toLocaleLowerCase("ru-RU");
    return Object.entries(appDefinitions).filter(([id, definition]) => {
      return !normalized || id.includes(normalized) || definition.name.toLocaleLowerCase("ru-RU").includes(normalized) || definition.subtitle.toLocaleLowerCase("ru-RU").includes(normalized);
    });
  }

  function renderResults() {
    paletteResults.replaceChildren();
    const value = paletteInput.value.trim();
    if (value.startsWith("/")) {
      const commands = [
        ["/help", "Список встроенных команд"],
        ["/status", "Состояние оболочки и активное пространство"],
        ["/apps", "Каталог приложений"],
        ["/open illidia", "Открыть Illidia"],
        ["/open workspace", "Открыть панель системных задач"],
        ["/close", "Закрыть верхнее окно"],
        ["/workspace home", "Перейти на рабочий стол"],
        ["/workspace studio", "Перейти в студию"],
        ["/workspace play", "Перейти к играм"],
        ["/workspace system", "Перейти к системным инструментам"],
        ["/theme amber", "Включить Mora Amber"],
        ["/theme dark", "Включить тёмную тему"],
        ["/theme light", "Включить светлую тему"],
        ["/focus on", "Включить режим фокуса"],
        ["/focus off", "Выключить режим фокуса"]
      ].filter(([command, description]) => command.includes(value.toLowerCase()) || description.toLocaleLowerCase("ru-RU").includes(value.slice(1).toLocaleLowerCase("ru-RU")));
      for (const [command, description] of commands) {
        const button = element("button", "command-result");
        button.type = "button";
        button.append(element("strong", "", command), element("span", "", description));
        button.addEventListener("click", () => runCommand(commandTokens(command)));
        paletteResults.appendChild(button);
      }
      return;
    }

    const matches = appMatches(value);
    for (const [id, definition] of matches) {
      const button = element("button", "command-result");
      button.type = "button";
      button.append(element("strong", "", definition.name), element("span", "", definition.subtitle + " · " + id));
      button.addEventListener("click", () => {
        closePalette();
        openApp(id);
      });
      paletteResults.appendChild(button);
    }
    if (!matches.length) paletteResults.appendChild(element("p", "command-empty", "Приложение не найдено."));
  }

  function runCommand(tokens) {
    if (!tokens.length) return;
    const [command, value] = tokens;
    if (command === "/help" && tokens.length === 1) {
      showToast("Команды: /status, /apps, /open <id>, /close, /workspace <id>, /theme <name>, /focus on|off");
    } else if (command === "/status" && tokens.length === 1) {
      showToast("Mora browser shell · пространство: " + activeWorkspace + " · окон: " + windowLayer.querySelectorAll(".app-window").length);
    } else if (command === "/apps" && tokens.length === 1) {
      showToast("Приложений и системных инструментов: " + Object.keys(appDefinitions).length);
    } else if (command === "/close" && tokens.length === 1) {
      closeTopWindow();
    } else if (command === "/open" && tokens.length === 2) {
      const found = Object.entries(appDefinitions).find(([id, item]) => id === value || item.name.toLocaleLowerCase("ru-RU") === value);
      if (found) {
        closePalette();
        openApp(found[0]);
        return;
      }
      showToast("Неизвестное приложение: " + value);
    } else if (command === "/workspace" && tokens.length === 2) {
      if (!WORKSPACES.some((workspace) => workspace.id === value)) {
        showToast("Неизвестное рабочее пространство: " + value);
        return;
      }
      switchWorkspace(value);
    } else if (command === "/theme" && tokens.length === 2 && PALETTE_NAMES[value]) {
      preferences.appearance.theme = value;
      persistPreferences();
      showToast("Тема: " + PALETTE_NAMES[value]);
    } else if (command === "/focus" && tokens.length === 2 && (value === "on" || value === "off")) {
      preferences.focusMode = value === "on";
      persistPreferences();
      showToast(preferences.focusMode ? "Режим фокуса включён" : "Режим фокуса выключен");
    } else {
      showToast("Команда отклонена. Введите /help");
      return;
    }
    closePalette();
  }

  commandButton.addEventListener("click", openPalette);
  palette.addEventListener("click", (event) => {
    if (event.target === palette) closePalette();
  });
  paletteInput.addEventListener("input", renderResults);
  paletteInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      const value = paletteInput.value.trim();
      if (value.startsWith("/")) runCommand(commandTokens(value));
      else {
        const matches = appMatches(value);
        if (matches.length === 1) {
          closePalette();
          openApp(matches[0][0]);
        }
      }
    }
  });

  document.addEventListener("click", (event) => {
    const action = event.target.closest("[data-window-action]");
    if (!action) return;
    const appWindow = action.closest(".app-window");
    if (!appWindow) return;
    event.preventDefault();
    event.stopPropagation();

    if (action.dataset.windowAction === "minimize") {
      appWindow.dataset.minimized = "true";
      appWindow.hidden = true;
      updateActiveApp();
      return;
    }

    if (action.dataset.windowAction === "maximize") {
      const maximized = appWindow.classList.toggle("is-maximized");
      if (maximized) {
        appWindow.dataset.restoreLeft = appWindow.style.left;
        appWindow.dataset.restoreTop = appWindow.style.top;
        appWindow.dataset.restoreWidth = appWindow.style.width;
        appWindow.dataset.restoreMaxHeight = appWindow.style.maxHeight;
        appWindow.style.left = "12px";
        appWindow.style.top = "64px";
        appWindow.style.width = "calc(100% - 24px)";
        appWindow.style.maxHeight = "calc(100vh - 112px)";
        action.setAttribute("aria-label", "Восстановить размер окна");
      } else {
        appWindow.style.left = appWindow.dataset.restoreLeft || "";
        appWindow.style.top = appWindow.dataset.restoreTop || "";
        appWindow.style.width = appWindow.dataset.restoreWidth || "";
        appWindow.style.maxHeight = appWindow.dataset.restoreMaxHeight || "";
        action.setAttribute("aria-label", "Развернуть окно");
      }
    }
  });

  document.addEventListener("click", (event) => {
    const appButton = event.target.closest(".dock-item[data-app]");
    if (!appButton) return;
    const appWindow = getWorkspaceWindow(windowLayer, appButton.dataset.app);
    if (!appWindow) return;
    if (appWindow.dataset.minimized === "true") {
      appWindow.dataset.minimized = "false";
      appWindow.hidden = false;
    }
  });

  window.addEventListener("mora:window-focus", (event) => {
    const appWindow = getWorkspaceWindow(windowLayer, event.detail?.appId);
    if (!appWindow) return;
    if (appWindow.dataset.workspace !== activeWorkspace) {
      switchWorkspace(appWindow.dataset.workspace);
    }
    appWindow.dataset.minimized = "false";
    appWindow.hidden = false;
  });

  document.addEventListener("keydown", (event) => {
    const modifier = event.ctrlKey || event.metaKey;
    if (modifier && event.key.toLowerCase() === "k") {
      event.preventDefault();
      openPalette();
      return;
    }

    if (palette.hidden && modifier && /^[1-4]$/.test(event.key)) {
      event.preventDefault();
      switchWorkspace(WORKSPACES[Number(event.key) - 1].id);
      return;
    }

    if (!palette.hidden && event.key === "Escape") {
      event.preventDefault();
      event.stopImmediatePropagation();
      closePalette();
    }
  }, true);

  const observer = new MutationObserver((records) => {
    for (const record of records) {
      for (const node of record.addedNodes) {
        if (node.nodeType !== Node.ELEMENT_NODE) continue;
        if (node.matches?.(".app-window")) decorateWindow(node);
        node.querySelectorAll?.(".app-window").forEach(decorateWindow);
      }
    }
    updateWindows();
  });
  observer.observe(windowLayer, { childList: true });
  windowLayer.querySelectorAll(".app-window").forEach(decorateWindow);
  updateWindows();

  const hostNotice = element("span", "shell-status-note", "Ctrl+K · команды оболочки");
  systemStatus.appendChild(hostNotice);
}
