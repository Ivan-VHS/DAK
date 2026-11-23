const STORAGE_KEY = "duckos.mora.blade-hub.v1";
const HUB_EPOCH = "86 452 654 432 564 423 644";

export const HUB_BLADES = Object.freeze([
  { id: "live", ru: "Live", ua: "Live", subtitleRu: "Профиль и доступ", subtitleUa: "Профіль і доступ" },
  { id: "games", ru: "Игры", ua: "Ігри", subtitleRu: "Игровая библиотека", subtitleUa: "Ігрова бібліотека" },
  { id: "media", ru: "Медиа", ua: "Медіа", subtitleRu: "Звук, фото и коллекции", subtitleUa: "Звук, фото й колекції" },
  { id: "system", ru: "Система", ua: "Система", subtitleRu: "Инструменты DuckOS", subtitleUa: "Інструменти DuckOS" }
]);

export const HUB_APPS = Object.freeze([
  ["mora-ai","live","Mora AI","Планы и локальные действия с предварительным подтверждением.","Плани й локальні дії з попереднім підтвердженням.","✦"],
  ["security","live","Sentinel","Параметры доверия и разрешений браузерного профиля.","Параметри довіри й дозволів профілю браузера.","◇"],
  ["workspace","live","Control","Параметры фокуса, движения и профиля среды.","Параметри фокуса, руху та профілю середовища.","⌘"],
  ["provenance","live","Proof","Локальная проверка файлов и SHA-256.","Локальна перевірка файлів і SHA-256.","⌁"],
  ["unify","live","Unify","Панель устройств и подключений.","Панель пристроїв і підключень.","∞"],
  ["sestem","live","Sestem","Сводка зрелости компонентов DuckOS.","Зведення зрілості компонентів DuckOS.","♟"],
  ["setupup","live","SetupUP","Первичная настройка локального рабочего пространства.","Початкове налаштування локального робочого простору.","✳"],

  ["illidia","games","Illidia","Игровая библиотека и демонстрационные сохранения.","Ігрова бібліотека та демонстраційні збереження.","⌘"],
  ["gamecharager","games","GameCharager","Каталог игр и локальных игровых заметок.","Каталог ігор і локальних ігрових нотаток.","▣"],
  ["mora-boost","games","Mora Boost","Переход к нативной игровой рабочей станции OPlague.","Перехід до нативної ігрової робочої станції OPlague.","⚡"],
  ["concrete-thump","games","Concrete Thump","Локальные профили темпа и swing.","Локальні профілі темпу та swing.","♫"],
  ["exedotexe","games","EXEdotEXE","Инспекция исполняемых форматов без запуска.","Інспекція виконуваних форматів без запуску.","E"],
  ["runtime","games","Bridge","Инспектор PE/ELF и диагностика совместимости.","Інспектор PE/ELF і діагностика сумісності.","⇄"],
  ["updates","games","Restore","Локальные снимки настроек и preview обновления.","Локальні знімки налаштувань і попередній перегляд оновлення.","↶"],

  ["cockos","media","Cockos","Аудиопанель с демонстрационными уровнями.","Аудіопанель із демонстраційними рівнями.","∿"],
  ["kavun","media","Kavun","Фотографии и демонстрационный альбом.","Фотографії та демонстраційний альбом.","◒"],
  ["kabon","media","Ka-bon","Локальный демонстрационный бюджет.","Локальний демонстраційний бюджет.","₴"],
  ["olaab","media","Olaab","Медиатека, названия подборок и теги.","Медіатека, назви добірок і теги.","◈"],
  ["seu-beu","media","Seu-Beu","Контрольный список перед обменом материалами.","Контрольний список перед обміном матеріалами.","◇"],
  ["love-il","media","Love-IL","Локальные личные записи.","Локальні особисті записи.","♡"],

  ["gloverty","system","Gloverty","Сценарии и демонстрационная автоматизация.","Сценарії та демонстраційна автоматизація.","ϟ"],
  ["po","system","Po","Компас и выбор направления без доступа к геолокации.","Компас і вибір напрямку без доступу до геолокації.","⌖"],
  ["orriganize","system","Orriganize","Локальный список задач и проектов.","Локальний список завдань і проєктів.","▦"],
  ["abriganza","system","Abriganza","Инспекция метаданных архивов без распаковки.","Інспекція метаданих архівів без розпакування.","▤"],
  ["poi","system","Poi","Быстрые локальные заметки.","Швидкі локальні нотатки.","⌖"],
  ["poi-2","system","Poi-2","Карточки личной базы знаний.","Картки особистої бази знань.","▧"],
  ["po-2","system","Po-2","Маршруты и точки пользовательских коллекций.","Маршрути й точки користувацьких колекцій.","➤"],
  ["desktop","system","Duck Desktop","Переход к нативному инструменту обслуживания рабочего стола.","Перехід до нативного інструмента обслуговування робочого столу.","▦"],
  ["mora-commons","system","Mora Commons","Единый каталог приложений и их возможностей.","Єдиний каталог застосунків та їхніх можливостей.","✣"]
].map(([id, blade, ru, descRu, descUa, glyph]) => Object.freeze({
  id, blade, ru, ua: ru, descRu, descUa, glyph
})));

export const HUB_VFS_NODES = Object.freeze([
  { id: "root", path: "/", ru: "Корень", ua: "Корінь", blade: "system", detailRu: "Корневой узел семантической навигации.", detailUa: "Кореневий вузол семантичної навігації." },
  { id: "core", path: "/ядро", ru: "Ядро", ua: "Ядро", blade: "system", detailRu: "Архитектурные контракты и системные компоненты.", detailUa: "Архітектурні контракти й системні компоненти." },
  { id: "apps", path: "/приложения", ru: "Приложения", ua: "Застосунки", blade: "live", detailRu: "Каталог встроенных панелей Mora.", detailUa: "Каталог вбудованих панелей Mora." },
  { id: "games", path: "/игры", ru: "Игры", ua: "Ігри", blade: "games", detailRu: "Игровая библиотека, совместимость и производительность.", detailUa: "Ігрова бібліотека, сумісність і продуктивність." },
  { id: "media", path: "/медиа", ru: "Медиа", ua: "Медіа", blade: "media", detailRu: "Аудио, фотографии и личные коллекции.", detailUa: "Аудіо, фотографії та особисті колекції." },
  { id: "system", path: "/система", ru: "Система", ua: "Система", blade: "system", detailRu: "Системные настройки и служебные инструменты.", detailUa: "Системні налаштування та службові інструменти." },
  { id: "integrations", path: "/интеграции", ru: "Интеграции", ua: "Інтеграції", blade: "live", detailRu: "Связи между встроенными приложениями и проектами.", detailUa: "Зв’язки між вбудованими застосунками та проєктами." },
  { id: "journal", path: "/журнал", ru: "Журнал", ua: "Журнал", blade: "system", detailRu: "Локальный журнал событий текущей сессии Hub.", detailUa: "Локальний журнал подій поточного сеансу Hub." }
]);

export const MORA_VECTORS = Object.freeze([
  ["functional-development","Разработка функционала","Розробка функціональності","mora-ai"],
  ["capability-design","Проектирование возможностей","Проєктування можливостей","mora-commons"],
  ["tooling","Инструментарий","Інструментарій","abriganza"],
  ["equipment","Оснащение","Оснащення","sestem"],
  ["enablement","Оснащённость","Оснащеність","setupup"],
  ["competencies","Компетенции","Компетенції","mora-ai"],
  ["integrations","Интеграции","Інтеграції","unify"],
  ["subsystems","Подсистемы","Підсистеми","sestem"],
  ["mechanisms","Механизмы","Механізми","gloverty"],
  ["tools","Инструменты","Інструменти","desktop"],
  ["components","Компоненты","Компоненти","mora-commons"],
  ["modules","Модули","Модулі","runtime"],
  ["implementation","Реализация","Реалізація","sestem"],
  ["automation","Автоматизация","Автоматизація","gloverty"],
  ["optimization","Оптимизация","Оптимізація","mora-boost"],
  ["compatibility","Совместимость","Сумісність","runtime"],
  ["performance","Производительность","Продуктивність","mora-boost"],
  ["scalability","Масштабируемость","Масштабованість","desktop"],
  ["universality","Универсальность","Універсальність","mora-commons"],
  ["extensibility","Расширяемость","Розширюваність","mora-commons"]
].map(([id, ru, ua, appId]) => Object.freeze({ id, ru, ua, appId })));

const DEFAULT_VIEWS = Object.freeze({
  "01": { blade: "live", cwd: "root", selectedApp: "mora-ai" },
  "02": { blade: "games", cwd: "games", selectedApp: "illidia" },
  "03": { blade: "system", cwd: "system", selectedApp: "gloverty" }
});
const LANGUAGE_IDS = new Set(["ru", "ua", "dual"]);
const WORKSPACE_IDS = new Set(["01", "02", "03"]);
const BLADE_IDS = new Set(HUB_BLADES.map((blade) => blade.id));
const VFS_IDS = new Set(HUB_VFS_NODES.map((node) => node.id));
const APP_IDS = new Set(HUB_APPS.map((app) => app.id));

export function localizePair(ru, ua, language = "ru") {
  if (!ua || ua === ru) return ru || ua || "";
  if (language === "ua") return ua;
  if (language === "dual") return ru + " / " + ua;
  return ru;
}

export function normalizeHubPreferences(value = {}) {
  const source = value && typeof value === "object" ? value : {};
  const workspace = WORKSPACE_IDS.has(source.workspace) ? source.workspace : "01";
  const views = {};
  for (const id of WORKSPACE_IDS) {
    const saved = source.views && typeof source.views === "object" ? source.views[id] : null;
    const fallback = DEFAULT_VIEWS[id];
    const blade = saved && BLADE_IDS.has(saved.blade) ? saved.blade : fallback.blade;
    const selectedCandidate = saved && APP_IDS.has(saved.selectedApp) ? saved.selectedApp : fallback.selectedApp;
    const selectedApp = HUB_APPS.find((app) => app.id === selectedCandidate && app.blade === blade)?.id ||
      HUB_APPS.find((app) => app.blade === blade)?.id || fallback.selectedApp;
    views[id] = {
      blade,
      cwd: saved && VFS_IDS.has(saved.cwd) ? saved.cwd : fallback.cwd,
      selectedApp
    };
  }
  return {
    language: LANGUAGE_IDS.has(source.language) ? source.language : "ru",
    workspace,
    profile: source.profile === "guest" ? "guest" : "owner",
    views
  };
}

export function validateHubRegistry(expectedApps = HUB_APPS, installedIds = []) {
  const counts = new Map();
  for (const id of installedIds) counts.set(id, (counts.get(id) || 0) + 1);
  const expectedIds = new Set(expectedApps.map((app) => app.id));
  const missing = [...expectedIds].filter((id) => !counts.has(id));
  const duplicates = [...counts].filter(([, count]) => count > 1).map(([id]) => id);
  const unexpected = [...counts.keys()].filter((id) => !expectedIds.has(id));
  return {
    expected: expectedIds.size,
    available: [...expectedIds].filter((id) => counts.has(id)).length,
    missing,
    duplicates,
    unexpected,
    ok: missing.length === 0 && duplicates.length === 0 && unexpected.length === 0
  };
}

export function resolveVfsNode(value) {
  const query = String(value || "").trim().toLocaleLowerCase();
  return HUB_VFS_NODES.find((node) =>
    node.id === query ||
    node.path.toLocaleLowerCase() === query ||
    node.ru.toLocaleLowerCase() === query ||
    node.ua.toLocaleLowerCase() === query ||
    ("/" + node.ua).toLocaleLowerCase() === query ||
    ("/" + node.ru).toLocaleLowerCase() === query
  ) || null;
}

const UI_COPY = {
  ru: {
    eyebrow: "РАБОЧАЯ СРЕДА · DUCKOS", title: "Blade Hub", unofficial: "НЕОФИЦИАЛЬНАЯ НАВИГАЦИЯ В СТИЛЕ 360",
    close: "Закрыть", workspace: "Рабочие пространства", profile: "Локальный профиль",
    owner: "Основной", guest: "Гость", vfs: "Семантический VFS",
    vfsNote: "Это навигационная модель Mora, а не прямой доступ к дискам или нативной файловой системе.",
    centerKicker: "КАТАЛОГ MORA", search: "Поиск приложения", searchPlaceholder: "Название или назначение…",
    noResults: "Ничего не найдено. Измените запрос.", open: "Открыть в Mora", registered: "В реестре Mora",
    missing: "Нет в реестре", vectors: "20 системных векторов",
    vectorNote: "Единый реестр направлений. Метка «Контур» не означает, что нативная реализация уже готова.",
    inspector: "Инспектор прав и целостности", registry: "Реестр приложения",
    registryOk: "Встроенная панель найдена", signature: "Подпись пакета",
    signatureUnknown: "Не проверяется браузерной оболочкой", license: "Лицензии и DRM",
    licenseUnknown: "Проверка не подключена", execution: "Способ запуска",
    executionInfo: "Панель Mora · без запуска нативного процесса", profileScope: "Профиль",
    profileInfo: "Локальный режим интерфейса; не является учётной записью консоли.",
    audit: "Проверить реестр", auditReady: "Аудит сверяет встроенный каталог и карточки рабочего стола.",
    auditPass: "Реестр приложений согласован.", auditFail: "Найдены расхождения в реестре.",
    auditCsp: "Политика same-origin CSP присутствует.", auditNoCsp: "Не удалось подтвердить ожидаемую CSP-политику.",
    log: "Журнал сеанса", command: "Локальная строка команд",
    commandPlaceholder: "помощь · язык ua · путь /игры · blade media", run: "Выполнить",
    footer: "DuckOS / Mora · интерфейсный концепт, не продукт Microsoft.",
    vectorScope: "АРХИТЕКТУРНЫЙ КОНТУР", vectorOpen: "Открыть связанное приложение",
    commandHelp: "Команды: язык ru|ua|dual · путь <путь или алиас> · blade live|games|media|system · ws 01|02|03 · audit · помощь",
    commandUnknown: "Команда не распознана. Введите «помощь».",
    commandPathMiss: "Семантический узел не найден.",
    commandWorkspace: "Рабочее пространство переключено.", commandBlade: "Раздел переключён.",
    commandLanguage: "Язык интерфейса изменён.", commandAudit: "Проверка реестра завершена.",
    status: "ЛОКАЛЬНАЯ ОБОЛОЧКА", profileChanged: "Профиль изменён."
  },
  ua: {
    eyebrow: "РОБОЧЕ СЕРЕДОВИЩЕ · DUCKOS", title: "Blade Hub", unofficial: "НЕОФІЦІЙНА НАВІГАЦІЯ У СТИЛІ 360",
    close: "Закрити", workspace: "Робочі простори", profile: "Локальний профіль",
    owner: "Основний", guest: "Гість", vfs: "Семантичний VFS",
    vfsNote: "Це навігаційна модель Mora, а не прямий доступ до дисків або нативної файлової системи.",
    centerKicker: "КАТАЛОГ MORA", search: "Пошук застосунку", searchPlaceholder: "Назва або призначення…",
    noResults: "Нічого не знайдено. Змініть запит.", open: "Відкрити в Mora", registered: "У реєстрі Mora",
    missing: "Немає в реєстрі", vectors: "20 системних векторів",
    vectorNote: "Єдиний реєстр напрямів. Позначка «Контур» не означає, що нативну реалізацію вже завершено.",
    inspector: "Інспектор прав і цілісності", registry: "Реєстр застосунку",
    registryOk: "Вбудовану панель знайдено", signature: "Підпис пакета",
    signatureUnknown: "Не перевіряється браузерною оболонкою", license: "Ліцензії та DRM",
    licenseUnknown: "Перевірку не підключено", execution: "Спосіб запуску",
    executionInfo: "Панель Mora · без запуску нативного процесу", profileScope: "Профіль",
    profileInfo: "Локальний режим інтерфейсу; не є обліковим записом консолі.",
    audit: "Перевірити реєстр", auditReady: "Аудит звіряє вбудований каталог із картками робочого столу.",
    auditPass: "Реєстр застосунків узгоджено.", auditFail: "У реєстрі знайдено розбіжності.",
    auditCsp: "Політика same-origin CSP наявна.", auditNoCsp: "Не вдалося підтвердити очікувану CSP-політику.",
    log: "Журнал сеансу", command: "Локальний рядок команд",
    commandPlaceholder: "допомога · мова ua · шлях /ігри · blade media", run: "Виконати",
    footer: "DuckOS / Mora · інтерфейсний концепт, не продукт Microsoft.",
    vectorScope: "АРХІТЕКТУРНИЙ КОНТУР", vectorOpen: "Відкрити пов’язаний застосунок",
    commandHelp: "Команди: мова ru|ua|dual · шлях <шлях або аліас> · blade live|games|media|system · ws 01|02|03 · audit · допомога",
    commandUnknown: "Команду не розпізнано. Введіть «допомога».",
    commandPathMiss: "Семантичний вузол не знайдено.",
    commandWorkspace: "Робочий простір перемкнено.", commandBlade: "Розділ перемкнено.",
    commandLanguage: "Мову інтерфейсу змінено.", commandAudit: "Перевірку реєстру завершено.",
    status: "ЛОКАЛЬНА ОБОЛОНКА", profileChanged: "Профіль змінено."
  }
};

function createNode(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}

function makeButton(label, className, dataKey, dataValue) {
  const button = createNode("button", className, label);
  button.type = "button";
  if (dataKey) button.dataset[dataKey] = dataValue;
  return button;
}

function createRootMarkup(root) {
  root.innerHTML = [
    '<div class="xbox-hub-backdrop" data-hub-dismiss></div>',
    '<section class="xbox-hub-dialog" role="dialog" aria-modal="true" aria-labelledby="xbox-hub-title" tabindex="-1">',
    '<header class="xbox-hub-header"><div class="xbox-hub-brand"><span class="xbox-hub-mark" aria-hidden="true">◈</span>',
    '<div><p data-hub-copy="eyebrow"></p><h2 id="xbox-hub-title" data-hub-copy="title"></h2><span class="xbox-hub-unofficial" data-hub-copy="unofficial"></span></div></div>',
    '<div class="xbox-hub-controls"><div class="xbox-hub-control-group" role="group" aria-label="Workspaces" data-hub-workspaces></div>',
    '<div class="xbox-hub-control-group xbox-hub-languages" role="group" aria-label="Language" data-hub-languages></div>',
    '<label class="xbox-hub-profile"><span data-hub-copy="profile"></span><select data-hub-profile-select><option value="owner"></option><option value="guest"></option></select></label>',
    '<button type="button" class="xbox-hub-close" data-hub-close aria-label="Close hub">×</button></div></header>',
    '<nav class="xbox-hub-blades" aria-label="Hub sections" data-hub-blades></nav>',
    '<div class="xbox-hub-stage">',
    '<aside class="xbox-hub-panel xbox-hub-vfs-panel"><div class="xbox-hub-panel-head"><span data-hub-copy="vfs"></span><span class="xbox-hub-micro" data-hub-path>/</span></div>',
    '<div class="xbox-hub-vfs-list" data-hub-vfs></div><p class="xbox-hub-footnote" data-hub-copy="vfsNote"></p></aside>',
    '<section class="xbox-hub-panel xbox-hub-main-panel"><div class="xbox-hub-main-head"><div><span class="xbox-hub-kicker" data-hub-copy="centerKicker"></span>',
    '<h3 data-hub-center-title></h3><span class="xbox-hub-result-count" data-hub-result-count></span></div>',
    '<label class="xbox-hub-search"><span aria-hidden="true">⌕</span><input type="search" data-hub-search aria-label="Search Mora apps"></label></div>',
    '<div class="xbox-hub-app-grid" data-hub-apps></div>',
    '<section class="xbox-hub-vector-section"><div class="xbox-hub-vector-head"><div><h3 data-hub-copy="vectors"></h3><p data-hub-copy="vectorNote"></p></div><span class="xbox-hub-vector-count">20</span></div>',
    '<div class="xbox-hub-vector-grid" data-hub-vectors></div></section></section>',
    '<aside class="xbox-hub-panel xbox-hub-inspector-panel"><div class="xbox-hub-panel-head"><span data-hub-copy="inspector"></span><span class="xbox-hub-micro" data-hub-profile-tag></span></div>',
    '<div class="xbox-hub-inspector" data-hub-inspector></div><div class="xbox-hub-audit"><button type="button" class="xbox-hub-audit-button" data-hub-audit></button>',
    '<p data-hub-audit-result role="status"></p></div><div class="xbox-hub-log-area"><div class="xbox-hub-panel-head"><span data-hub-copy="log"></span><span class="xbox-hub-micro">SESSION</span></div>',
    '<ol class="xbox-hub-log" data-hub-log aria-live="polite"></ol></div>',
    '<form class="xbox-hub-command" data-hub-command-form><label data-hub-copy="command" for="xbox-hub-command-input"></label>',
    '<div><input id="xbox-hub-command-input" data-hub-command-input autocomplete="off" spellcheck="false"><button type="submit" data-hub-copy="run"></button></div></form></aside>',
    '</div><footer class="xbox-hub-footer"><span data-hub-copy="footer"></span><span data-hub-gamepad-status>Клавиатура · мышь · геймпад</span></footer>',
    '</section>'
  ].join("");
}

export function initializeXboxHub() {
  const root = document.getElementById("xbox-hub-root");
  const openButton = document.getElementById("xbox-hub-toggle");
  if (!root || !openButton || root.dataset.initialized === "true") return;
  root.dataset.initialized = "true";
  createRootMarkup(root);

  let preferences;
  try {
    preferences = normalizeHubPreferences(JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"));
  } catch {
    preferences = normalizeHubPreferences();
  }

  const state = {
    ...preferences,
    open: false,
    cwd: preferences.views[preferences.workspace].cwd,
    blade: preferences.views[preferences.workspace].blade,
    selectedApp: preferences.views[preferences.workspace].selectedApp,
    selectedVector: null,
    logs: [],
    audit: null
  };

  const $ = (selector) => root.querySelector(selector);
  const copy = (key) => UI_COPY[state.language === "ua" ? "ua" : "ru"][key];
  let returnFocus = null;
  let gamepadFrame = 0;
  let previousGamepadButtons = new Set();
  let lastGamepadAction = 0;

  function addLog(level, message) {
    state.logs.unshift({
      level,
      message,
      time: new Date().toLocaleTimeString(state.language === "ua" ? "uk-UA" : "ru-RU", {
        hour: "2-digit", minute: "2-digit", second: "2-digit"
      })
    });
    state.logs.length = Math.min(state.logs.length, 8);
    renderLog();
  }

  function saveState() {
    state.views[state.workspace] = {
      blade: state.blade,
      cwd: state.cwd,
      selectedApp: state.selectedApp
    };
    const saved = normalizeHubPreferences({
      language: state.language, workspace: state.workspace,
      profile: state.profile, views: state.views
    });
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
    } catch {
      addLog("warn", state.language === "ua"
        ? "Параметри не збережено: сховище браузера недоступне."
        : "Настройки не сохранены: хранилище браузера недоступно.");
    }
  }

  function textFor(ru, ua) {
    return localizePair(ru, ua, state.language);
  }

  function findDesktopTile(appId) {
    return [...document.querySelectorAll(".app-tile[data-app]")].find((tile) => tile.dataset.app === appId) || null;
  }

  function readDesktopTile(appId) {
    const tile = findDesktopTile(appId);
    if (!tile) return null;
    return {
      tile,
      name: tile.querySelector(".app-name")?.textContent.trim() || appId,
      subtitle: tile.querySelector(".app-subtitle")?.textContent.trim() || "",
      glyph: tile.querySelector(".system-glyph")?.textContent.trim() ||
        tile.querySelector(".app-icon")?.textContent.trim() || ""
    };
  }

  function renderCopy() {
    root.querySelectorAll("[data-hub-copy]").forEach((node) => {
      node.textContent = copy(node.dataset.hubCopy);
    });
    $("[data-hub-search]").placeholder = copy("searchPlaceholder");
    $("[data-hub-search]").setAttribute("aria-label", copy("search"));
    $("[data-hub-command-input]").placeholder = copy("commandPlaceholder");
    $("[data-hub-profile-select] option[value='owner']").textContent = copy("owner");
    $("[data-hub-profile-select] option[value='guest']").textContent = copy("guest");
    $("[data-hub-profile-select]").value = state.profile;
    $("[data-hub-audit]").textContent = copy("audit");
    $("[data-hub-audit-result]").textContent = copy("auditReady");
    $("[data-hub-close]").setAttribute("aria-label", copy("close"));
    $("[data-hub-workspaces]").setAttribute("aria-label", copy("workspace"));
    $("[data-hub-languages]").setAttribute("aria-label", state.language === "ua" ? "Мова" : "Язык");
    root.setAttribute("lang", state.language === "ua" ? "uk" : state.language === "dual" ? "ru-UA" : "ru");
  }

  function renderWorkspaces() {
    const group = $("[data-hub-workspaces]");
    group.replaceChildren();
    for (const id of ["01", "02", "03"]) {
      const button = makeButton(id, "xbox-hub-segment", "hubWorkspace", id);
      button.classList.toggle("is-active", state.workspace === id);
      button.setAttribute("aria-pressed", String(state.workspace === id));
      button.title = copy("workspace") + " " + id;
      group.append(button);
    }
  }

  function renderLanguages() {
    const group = $("[data-hub-languages]");
    group.replaceChildren();
    for (const [id, label] of [["ru", "RU"], ["ua", "UA"], ["dual", "RU/UA"]]) {
      const button = makeButton(label, "xbox-hub-segment", "hubLanguage", id);
      button.classList.toggle("is-active", state.language === id);
      button.setAttribute("aria-pressed", String(state.language === id));
      group.append(button);
    }
  }

  function renderBlades() {
    const nav = $("[data-hub-blades]");
    nav.replaceChildren();
    for (const blade of HUB_BLADES) {
      const button = makeButton("", "xbox-hub-blade", "hubBlade", blade.id);
      button.append(
        createNode("strong", "", textFor(blade.ru, blade.ua)),
        createNode("span", "", textFor(blade.subtitleRu, blade.subtitleUa))
      );
      button.classList.toggle("is-active", state.blade === blade.id);
      button.setAttribute("aria-current", state.blade === blade.id ? "page" : "false");
      nav.append(button);
    }
    const current = HUB_BLADES.find((blade) => blade.id === state.blade);
    $("[data-hub-center-title]").textContent = current ? textFor(current.ru, current.ua) : "Mora";
  }

  function renderVfs() {
    const list = $("[data-hub-vfs]");
    list.replaceChildren();
    const current = HUB_VFS_NODES.find((node) => node.id === state.cwd) || HUB_VFS_NODES[0];
    const currentName = textFor(current.ru, current.ua);
    $("[data-hub-path]").textContent = current.id === "root" ? "/" : "/" + currentName;
    for (const node of HUB_VFS_NODES) {
      const button = makeButton("", "xbox-hub-vfs-item", "hubVfs", node.id);
      button.append(
        createNode("span", "xbox-hub-vfs-name", textFor(node.ru, node.ua)),
        createNode("span", "xbox-hub-micro", node.path)
      );
      button.classList.toggle("is-active", state.cwd === node.id);
      button.setAttribute("aria-current", state.cwd === node.id ? "location" : "false");
      list.append(button);
    }
  }

  function renderApps() {
    const grid = $("[data-hub-apps]");
    const query = $("[data-hub-search]").value.trim().toLocaleLowerCase();
    const currentApps = HUB_APPS.filter((app) => app.blade === state.blade);
    const apps = currentApps.filter((app) => {
      if (!query) return true;
      const tile = readDesktopTile(app.id);
      return [app.ru, app.ua, app.descRu, app.descUa, tile?.name, tile?.subtitle, app.id]
        .join(" ").toLocaleLowerCase().includes(query);
    });
    grid.replaceChildren();
    $("[data-hub-result-count]").textContent = apps.length + " / " + currentApps.length;
    if (!apps.length) {
      grid.append(createNode("p", "xbox-hub-empty", copy("noResults")));
      return;
    }

    for (const app of apps) {
      const tile = readDesktopTile(app.id);
      const card = createNode("article", "xbox-hub-app-card");
      card.classList.toggle("is-selected", state.selectedApp === app.id);
      const select = makeButton("", "xbox-hub-app-select", "hubSelectApp", app.id);
      select.setAttribute("aria-pressed", String(state.selectedApp === app.id));
      select.append(
        createNode("span", "xbox-hub-app-glyph", tile?.glyph || app.glyph),
        createNode("span", "xbox-hub-app-copy", ""),
        createNode("span", "xbox-hub-app-state", tile ? copy("registered") : copy("missing"))
      );
      const appCopy = select.querySelector(".xbox-hub-app-copy");
      appCopy.append(
        createNode("strong", "", tile?.name || app.ru),
        createNode("small", "", textFor(app.descRu, app.descUa))
      );
      const launch = makeButton(copy("open"), "xbox-hub-launch", "hubLaunch", app.id);
      launch.disabled = !tile;
      launch.setAttribute("aria-label", copy("open") + ": " + (tile?.name || app.id));
      card.append(select, launch);
      grid.append(card);
    }
  }

  function renderVectors() {
    const grid = $("[data-hub-vectors]");
    grid.replaceChildren();
    for (const [index, vector] of MORA_VECTORS.entries()) {
      const button = makeButton("", "xbox-hub-vector", "hubVector", vector.id);
      button.classList.toggle("is-active", state.selectedVector === vector.id);
      button.setAttribute("aria-pressed", String(state.selectedVector === vector.id));
      button.append(
        createNode("span", "xbox-hub-vector-name", String(index + 1).padStart(2, "0") + " · " + textFor(vector.ru, vector.ua)),
        createNode("span", "xbox-hub-vector-tag", copy("vectorScope"))
      );
      grid.append(button);
    }
  }

  function renderInspector() {
    const panel = $("[data-hub-inspector]");
    panel.replaceChildren();
    const app = HUB_APPS.find((item) => item.id === state.selectedApp) || HUB_APPS[0];
    const tile = readDesktopTile(app.id);
    const heading = createNode("div", "xbox-hub-inspector-title");
    heading.append(
      createNode("span", "xbox-hub-inspector-glyph", tile?.glyph || app.glyph),
      createNode("div", "", "")
    );
    heading.lastChild.append(
      createNode("strong", "", tile?.name || app.ru),
      createNode("small", "", app.id)
    );
    panel.append(heading);

    const rows = [
      [copy("registry"), tile ? copy("registryOk") : copy("missing")],
      [copy("signature"), copy("signatureUnknown")],
      [copy("license"), copy("licenseUnknown")],
      [copy("execution"), copy("executionInfo")],
      [copy("profileScope"), (state.profile === "guest" ? copy("guest") : copy("owner")) + " · " + copy("profileInfo")]
    ];
    for (const [label, value] of rows) {
      const row = createNode("div", "xbox-hub-inspector-row");
      row.append(createNode("span", "", label), createNode("strong", "", value));
      panel.append(row);
    }

    if (state.selectedVector) {
      const vector = MORA_VECTORS.find((item) => item.id === state.selectedVector);
      if (vector) {
        const note = createNode("div", "xbox-hub-vector-detail");
        note.append(
          createNode("span", "xbox-hub-kicker", copy("vectorScope")),
          createNode("strong", "", textFor(vector.ru, vector.ua)),
          makeButton(copy("vectorOpen"), "xbox-hub-vector-open", "hubVectorOpen", vector.appId)
        );
        panel.append(note);
      }
    }
    $("[data-hub-profile-tag]").textContent = state.profile === "guest" ? copy("guest") : copy("owner");
  }

  function renderLog() {
    const list = $("[data-hub-log]");
    if (!list) return;
    list.replaceChildren();
    for (const entry of state.logs) {
      const item = createNode("li", "xbox-hub-log-entry");
      item.dataset.level = entry.level;
      item.append(createNode("time", "", entry.time), createNode("span", "", entry.message));
      list.append(item);
    }
  }

  function renderAll() {
    renderCopy();
    renderWorkspaces();
    renderLanguages();
    renderBlades();
    renderVfs();
    renderApps();
    renderVectors();
    renderInspector();
    renderLog();
  }

  function saveCurrentView() {
    state.views[state.workspace] = { blade: state.blade, cwd: state.cwd, selectedApp: state.selectedApp };
    saveState();
  }

  function selectWorkspace(id) {
    if (!WORKSPACE_IDS.has(id) || id === state.workspace) return;
    saveCurrentView();
    state.workspace = id;
    const view = state.views[id] || DEFAULT_VIEWS[id];
    state.blade = view.blade;
    state.cwd = view.cwd;
    state.selectedApp = view.selectedApp;
    state.selectedVector = null;
    saveState();
    renderAll();
    addLog("ok", "WS " + id + " · " + copy("commandWorkspace"));
  }

  function selectBlade(id) {
    if (!BLADE_IDS.has(id) || id === state.blade) return;
    state.blade = id;
    const firstApp = HUB_APPS.find((app) => app.blade === id);
    if (firstApp) state.selectedApp = firstApp.id;
    const node = HUB_VFS_NODES.find((item) => item.blade === id);
    if (node) state.cwd = node.id;
    state.selectedVector = null;
    saveCurrentView();
    renderAll();
    const blade = HUB_BLADES.find((item) => item.id === id);
    addLog("ok", copy("commandBlade") + " " + textFor(blade.ru, blade.ua));
  }

  function setLanguage(language) {
    if (!LANGUAGE_IDS.has(language)) return;
    state.language = language;
    saveCurrentView();
    renderAll();
    addLog("ok", copy("commandLanguage"));
  }

  function runAudit() {
    const installedIds = [...document.querySelectorAll(".app-tile[data-app]")].map((tile) => tile.dataset.app);
    const report = validateHubRegistry(HUB_APPS, installedIds);
    const csp = document.querySelector('meta[http-equiv="Content-Security-Policy"]')?.content || "";
    const cspOk = csp.includes("script-src 'self'") && csp.includes("connect-src 'self'") && csp.includes("object-src 'none'");
    state.audit = { ...report, cspOk };
    const output = $("[data-hub-audit-result]");
    output.textContent = [
      report.available + "/" + report.expected + " · " + (report.ok ? copy("auditPass") : copy("auditFail")),
      report.missing.length ? "Missing: " + report.missing.join(", ") : "",
      report.duplicates.length ? "Duplicate: " + report.duplicates.join(", ") : "",
      report.unexpected.length ? "Unexpected: " + report.unexpected.join(", ") : "",
      cspOk ? copy("auditCsp") : copy("auditNoCsp"),
      copy("signature") + ": " + copy("signatureUnknown")
    ].filter(Boolean).join(" ");
    output.dataset.state = report.ok && cspOk ? "ok" : "warn";
    addLog(report.ok && cspOk ? "ok" : "warn", report.available + "/" + report.expected + " · " + copy("commandAudit"));
  }

  function selectVfs(id) {
    const node = HUB_VFS_NODES.find((item) => item.id === id);
    if (!node) return;
    state.cwd = node.id;
    state.blade = node.blade;
    const firstApp = HUB_APPS.find((app) => app.blade === node.blade);
    if (firstApp) state.selectedApp = firstApp.id;
    state.selectedVector = null;
    saveCurrentView();
    renderAll();
    addLog("ok", node.path + " · " + textFor(node.ru, node.ua));
  }

  function selectVector(id) {
    const vector = MORA_VECTORS.find((item) => item.id === id);
    if (!vector) return;
    state.selectedVector = vector.id;
    state.selectedApp = vector.appId;
    renderVectors();
    renderInspector();
    addLog("info", textFor(vector.ru, vector.ua));
  }

  function closeHub() {
    if (!state.open) return;
    state.open = false;
    root.hidden = true;
    document.body.classList.remove("xbox-hub-open");
    openButton.setAttribute("aria-expanded", "false");
    stopGamepad();
    if (returnFocus?.isConnected) returnFocus.focus();
  }

  function launchApp(id) {
    const tile = findDesktopTile(id);
    if (!tile) {
      addLog("warn", id + " · " + copy("missing"));
      return;
    }
    closeHub();
    tile.click();
  }

  function moveFocus(step) {
    const items = [...root.querySelectorAll("button:not(:disabled), input:not(:disabled), select:not(:disabled)")];
    if (!items.length) return;
    const current = items.indexOf(document.activeElement);
    const next = current < 0 ? 0 : (current + step + items.length) % items.length;
    items[next].focus();
  }

  function switchBladeBy(step) {
    const index = HUB_BLADES.findIndex((blade) => blade.id === state.blade);
    const next = (index + step + HUB_BLADES.length) % HUB_BLADES.length;
    selectBlade(HUB_BLADES[next].id);
    root.querySelector('[data-hub-blade="' + HUB_BLADES[next].id + '"]')?.focus();
  }

  function focusAppGridBy(event) {
    const buttons = [...$("[data-hub-apps]").querySelectorAll("[data-hub-select-app]")];
    if (!buttons.length) return false;
    const current = buttons.indexOf(document.activeElement);
    if (current < 0) return false;
    const columns = Math.max(1, getComputedStyle($("[data-hub-apps]")).gridTemplateColumns.split(" ").length);
    let next = current;
    if (event.key === "ArrowLeft") next = current - 1;
    if (event.key === "ArrowRight") next = current + 1;
    if (event.key === "ArrowUp") next = current - columns;
    if (event.key === "ArrowDown") next = current + columns;
    if (next < 0 || next >= buttons.length) return false;
    buttons[next].focus();
    return true;
  }

  function openHub() {
    if (state.open) return;
    returnFocus = document.activeElement;
    state.open = true;
    root.hidden = false;
    document.body.classList.add("xbox-hub-open");
    openButton.setAttribute("aria-expanded", "true");
    renderAll();
    runAudit();
    $("[data-hub-close]").focus();
    startGamepad();
  }

  function startGamepad() {
    if (typeof navigator.getGamepads !== "function" || typeof requestAnimationFrame !== "function") return;
    const poll = () => {
      if (!state.open) return;
      const pressed = new Set();
      let action = "";
      for (const pad of navigator.getGamepads()) {
        if (!pad || !pad.connected) continue;
        for (let index = 0; index < pad.buttons.length; index += 1) {
          if (pad.buttons[index]?.pressed) pressed.add(pad.index + ":" + index);
        }
        const justPressed = (index) => pressed.has(pad.index + ":" + index) && !previousGamepadButtons.has(pad.index + ":" + index);
        if (justPressed(14)) action = "left";
        else if (justPressed(15)) action = "right";
        else if (justPressed(12)) action = "up";
        else if (justPressed(13)) action = "down";
        else if (justPressed(0)) action = "accept";
      }
      previousGamepadButtons = pressed;
      const now = typeof performance !== "undefined" ? performance.now() : Date.now();
      if (action && now - lastGamepadAction > 180) {
        lastGamepadAction = now;
        if (action === "left") switchBladeBy(-1);
        else if (action === "right") switchBladeBy(1);
        else if (action === "up") moveFocus(-1);
        else if (action === "down") moveFocus(1);
        else if (action === "accept") document.activeElement?.click?.();
      }
      gamepadFrame = requestAnimationFrame(poll);
    };
    gamepadFrame = requestAnimationFrame(poll);
  }

  function stopGamepad() {
    if (gamepadFrame && typeof cancelAnimationFrame === "function") cancelAnimationFrame(gamepadFrame);
    gamepadFrame = 0;
    previousGamepadButtons = new Set();
  }

  function runCommand(raw) {
    const trimmed = raw.trim();
    if (!trimmed) return;
    const parts = trimmed.split(/\s+/);
    const command = parts.shift().toLocaleLowerCase();
    const argument = parts.join(" ");
    if (["help", "помощь", "допомога"].includes(command)) {
      addLog("info", copy("commandHelp"));
    } else if (["язык", "мова", "lang"].includes(command)) {
      const language = argument.toLocaleLowerCase();
      setLanguage(["ru", "ua", "dual", "ru/ua"].includes(language) ? (language === "ru/ua" ? "dual" : language) : "ru");
    } else if (["путь", "шлях", "path"].includes(command)) {
      const node = resolveVfsNode(argument);
      if (node) selectVfs(node.id);
      else addLog("warn", copy("commandPathMiss"));
    } else if (["blade", "блейд", "раздел", "розділ"].includes(command)) {
      if (BLADE_IDS.has(argument.toLocaleLowerCase())) selectBlade(argument.toLocaleLowerCase());
      else addLog("warn", copy("commandUnknown"));
    } else if (["ws", "workspace", "пространство", "простір"].includes(command)) {
      if (WORKSPACE_IDS.has(argument)) selectWorkspace(argument);
      else addLog("warn", copy("commandUnknown"));
    } else if (["audit", "аудит"].includes(command)) {
      runAudit();
    } else {
      addLog("warn", copy("commandUnknown"));
    }
  }

  root.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    if (event.target.closest("[data-hub-dismiss], [data-hub-close]")) { closeHub(); return; }
    const workspace = event.target.closest("[data-hub-workspace]");
    if (workspace) { selectWorkspace(workspace.dataset.hubWorkspace); return; }
    const language = event.target.closest("[data-hub-language]");
    if (language) { setLanguage(language.dataset.hubLanguage); return; }
    const blade = event.target.closest("[data-hub-blade]");
    if (blade) { selectBlade(blade.dataset.hubBlade); return; }
    const vfs = event.target.closest("[data-hub-vfs]");
    if (vfs) { selectVfs(vfs.dataset.hubVfs); return; }
    const appSelect = event.target.closest("[data-hub-select-app]");
    if (appSelect) { state.selectedApp = appSelect.dataset.hubSelectApp; state.selectedVector = null; saveCurrentView(); renderApps(); renderInspector(); return; }
    const vector = event.target.closest("[data-hub-vector]");
    if (vector) { selectVector(vector.dataset.hubVector); return; }
    const vectorOpen = event.target.closest("[data-hub-vector-open]");
    if (vectorOpen) { launchApp(vectorOpen.dataset.hubVectorOpen); return; }
    const launch = event.target.closest("[data-hub-launch]");
    if (launch) { launchApp(launch.dataset.hubLaunch); return; }
    if (event.target.closest("[data-hub-audit]")) runAudit();
  });

  root.addEventListener("input", (event) => {
    if (event.target.matches("[data-hub-search]")) renderApps();
  });

  root.addEventListener("change", (event) => {
    if (event.target.matches("[data-hub-profile-select]")) {
      state.profile = event.target.value === "guest" ? "guest" : "owner";
      saveState();
      renderInspector();
      addLog("info", copy("profileChanged"));
    }
  });

  $("[data-hub-command-form]").addEventListener("submit", (event) => {
    event.preventDefault();
    const input = $("[data-hub-command-input]");
    const command = input.value;
    input.value = "";
    runCommand(command);
  });

  document.addEventListener("keydown", (event) => {
    if (!state.open) return;
    if (event.key === "Escape") { event.preventDefault(); closeHub(); return; }
    if (event.altKey && event.key === "ArrowLeft") { event.preventDefault(); switchBladeBy(-1); return; }
    if (event.altKey && event.key === "ArrowRight") { event.preventDefault(); switchBladeBy(1); return; }
    if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key) &&
        event.target instanceof Element && event.target.closest(".xbox-hub-app-grid")) {
      if (focusAppGridBy(event)) event.preventDefault();
      return;
    }
    if (event.key === "Tab") {
      const focusable = [...root.querySelectorAll("button:not(:disabled), input:not(:disabled), select:not(:disabled)")];
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });

  openButton.addEventListener("click", openHub);
  openButton.setAttribute("aria-controls", "xbox-hub-root");
  openButton.setAttribute("aria-expanded", "false");

  if (typeof window !== "undefined") {
    window.addEventListener("gamepadconnected", () => {
      $("[data-hub-gamepad-status]").textContent = state.language === "ua"
        ? "Геймпад підключено · D-pad / A" : "Геймпад подключён · D-pad / A";
    });
    window.addEventListener("gamepaddisconnected", () => {
      $("[data-hub-gamepad-status]").textContent = "Клавиатура · мышь · геймпад";
    });
  }

  renderAll();
  addLog("ok", "Mora Blade Hub · " + HUB_APPS.length + " apps · " + HUB_EPOCH);
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeXboxHub, { once: true });
  } else {
    initializeXboxHub();
  }
}
