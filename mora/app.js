const appDefinitions = {
  cockos: { name: "Cockos", subtitle: "Звук и запись", color: "#78c9d1", glyph: "∿" },
  kavun: { name: "Kavun", subtitle: "Фотографии", color: "#f17b79", glyph: "◒" },
  kabon: { name: "Ka-bon", subtitle: "Финансы", color: "#e9bb72", glyph: "₴" },
  gloverty: { name: "Gloverty", subtitle: "Сценарии", color: "#e9a0cf", glyph: "ϟ" },
  po: { name: "Po", subtitle: "Компас", color: "#a8b6ee", glyph: "⌖" },
  illidia: { name: "Illidia", subtitle: "Игры", color: "#9dce9b", glyph: "⌘" },
  unify: { name: "Unify", subtitle: "Устройства", color: "#9bd8c5", glyph: "∞" },
  serein: { name: "Serein", subtitle: "Нативная консоль", color: "#a8b6ee", glyph: "⌘" }
};

const windowLayer = document.getElementById("window-layer");
const activeAppLabel = document.getElementById("active-app");
const toastElement = document.getElementById("toast");
let nextZIndex = 10;
let toastTimeout = null;

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
    case "serein":
      return '<p class="window-kicker">СИСТЕМНАЯ УТИЛИТА · NATIVE C++20</p><h2 class="window-heading">Serein Console</h2><p class="window-copy">Serein — нативный менеджер установленных приложений DuckOS. Он проверяет манифест Mora, ограничивает пути каталогом приложения и запускает процессы напрямую, без shell-интерпретации.</p><div class="serein-terminal"><div class="serein-terminal-head"><span class="terminal-dot"></span><span>ЛОКАЛЬНАЯ КОНСОЛЬ</span><span class="terminal-state">COMMANDS</span></div><div class="serein-command"><span>serein ›</span> apps</div><div class="serein-command"><span>serein ›</span> inspect ivan-vhs.reaper-studio</div><div class="serein-command"><span>serein ›</span> run ivan-vhs.reaper-studio</div><div class="serein-command"><span>serein ›</span> ps</div><div class="serein-command"><span>serein ›</span> stop 12345</div></div><div class="serein-note"><strong>Важно:</strong> эта панель — справка интерфейса. Браузерная версия Mora не может запускать процессы ОС. Откройте системный терминал и выполните <code>serein</code>, чтобы использовать настоящий менеджер.</div><p class="window-copy">Регистрация: <code>serein register integrations/mora/manifest.json --root ПУТЬ_К_ПРОЕКТУ</code>. Первый запуск и регистрация требуют подтверждения пользователя.</p>';
    case "unify":
      return '<p class="window-kicker">ПОДКЛЮЧЕНИЯ · ДЕМО</p><h2 class="window-heading">Ваши устройства</h2>' +
        '<div class="device-list">' +
        '<div class="device-row"><span class="device-symbol">▣</span><div class="device-copy"><strong>Ноутбук Mora</strong><span>Основное устройство · Wi-Fi</span></div><span class="device-state">ONLINE</span></div>' +
        '<div class="device-row"><span class="device-symbol">♫</span><div class="device-copy"><strong>Беспроводные наушники</strong><span>Аудио · Bluetooth</span></div><button class="switch" role="switch" aria-checked="true" aria-label="Беспроводные наушники"></button></div>' +
        '<div class="device-row"><span class="device-symbol">⌘</span><div class="device-copy"><strong>Геймпад</strong><span>Игровой контроллер · Bluetooth</span></div><button class="switch" role="switch" aria-checked="false" aria-label="Геймпад"></button></div>' +
        '<div class="device-row"><span class="device-symbol">▤</span><div class="device-copy"><strong>Внешний дисплей</strong><span>Экран · HDMI</span></div><button class="switch" role="switch" aria-checked="true" aria-label="Внешний дисплей"></button></div>' +
        '</div><p class="window-copy" data-device-status>Подключённые устройства показаны условно. Сканирование оборудования не выполняется.</p>';
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

updateClock();
window.setInterval(updateClock, 1000);
updateActiveApp();