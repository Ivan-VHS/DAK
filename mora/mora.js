const projects = [
  {
    id: "pytyliki",
    nativeId: "pytyliki",
    name: "Pytyliki",
    category: "system",
    role: "Processor diagnostics",
    description: "CPU-профили, измерения, мониторинг и локальные отчёты.",
    icon: "▣",
    colors: ["#5ed9ef", "#1769b5"],
    repo: "https://github.com/Ivan-VHS/Pytyliki",
    image: "https://raw.githubusercontent.com/Ivan-VHS/Pytyliki/main/assets/screenshots/pytyliki-workstation.png"
  },
  {
    id: "reaper",
    nativeId: "reaper",
    name: "Reaper Studio",
    category: "developer",
    role: "Language & Studio IDE",
    description: "Язык Reaper, редактор, запуск, отладчик, LSP и DAP.",
    icon: "R",
    colors: ["#c0a7ff", "#5d3bc0"],
    repo: "https://github.com/Ivan-VHS/Reaper",
    image: "https://raw.githubusercontent.com/Ivan-VHS/Reaper/main/assets/screenshots/reaper-studio.png"
  },
  {
    id: "oplague",
    nativeId: "oplague",
    name: "OPlague",
    category: "system",
    role: "Hardware workbench",
    description: "Инвентаризация устройств и безопасная инспекция пакетов.",
    icon: "O",
    colors: ["#ff9eaa", "#a91f49"],
    repo: "https://github.com/Ivan-VHS/OPlague",
    image: "https://raw.githubusercontent.com/Ivan-VHS/OPlague/main/assets/screenshots/oplague-workbench.png"
  },
  {
    id: "ventu",
    nativeId: "ventusample",
    name: "VentuSample",
    category: "creative",
    role: "Sample workstation",
    description: "Создание лупов, сэмплов и офлайн-обработка аудио.",
    icon: "V",
    colors: ["#e6a3ff", "#7043b6"],
    repo: "https://github.com/Ivan-VHS/VentuSample",
    image: "https://raw.githubusercontent.com/Ivan-VHS/VentuSample/main/assets/screenshots/ventusample-studio.png"
  },
  {
    id: "duckos",
    name: "DuckOS",
    category: "system",
    role: "Operating system",
    description: "Системная платформа и домашний экран Mora.",
    icon: "🦆",
    colors: ["#ffd36d", "#bb781e"],
    repo: "https://github.com/Ivan-VHS/DuckOS",
    image: ""
  }
];

const builtins = [
  {
    id: "cockos",
    name: "Cockos",
    category: "creative",
    role: "Звук и запись",
    description: "Микшер по приложениям, входные устройства, запись и локальное сведение.",
    icon: "♫",
    colors: ["#ff83ad", "#bd3e74"]
  },
  {
    id: "kavun",
    name: "Kavun",
    category: "creative",
    role: "Фото и галерея",
    description: "Альбомы, подборки-срезы, просмотр и неразрушающая обработка изображений.",
    icon: "◉",
    colors: ["#75e4a9", "#219d6b"]
  },
  {
    id: "kabon",
    name: "Ka-bon",
    category: "system",
    role: "Финансы",
    description: "Расходы, чеки, категории, лимиты, подписки и локальные отчёты.",
    icon: "₴",
    colors: ["#ffd45c", "#c28a1d"]
  },
  {
    id: "gloverty",
    name: "Gloverty",
    category: "system",
    role: "Автоматизация",
    description: "Сценарии, условия, разрешённые действия и ручной запуск правил.",
    icon: "ϟ",
    colors: ["#ad98ff", "#5c43bd"]
  },
  {
    id: "po",
    name: "Po",
    category: "developer",
    role: "Браузер",
    description: "Вкладки, навигация, команды, режим чтения и рабочие ссылки.",
    icon: "⌕",
    colors: ["#82bfff", "#275fba"]
  },
  {
    id: "illidia",
    name: "Illidia",
    category: "creative",
    role: "Игры",
    description: "Игровая библиотека, коллекции, прогресс, достижения и клипы.",
    icon: "⌘",
    colors: ["#6ce4e0", "#168c9c"]
  },
  {
    id: "unify",
    name: "Unify",
    category: "system",
    role: "Устройства",
    description: "Устройства, локальный буфер и ручная передача выбранных данных.",
    icon: "⌁",
    colors: ["#d8dcff", "#7788cc"]
  }
];

const $ = selector => document.querySelector(selector);
const apps = $("#apps");
const projectGrid = $("#projectGrid");
const dialog = $("#appDialog");
const search = $("#search");
const nativeApps = new Map();
let filter = "all";
let nativeBridgeAvailable = false;
let currentDialogApp = null;

const allApps = () => projects.concat(builtins);

function createLink(label, href) {
  const link = document.createElement("a");
  link.href = href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = label;
  return link;
}

function nativeState(app) {
  return app.nativeId ? nativeApps.get(app.nativeId) : null;
}

function card(app) {
  const element = document.createElement("article");
  element.className = "app-card";
  element.style.setProperty("--a", app.colors[0]);
  element.style.setProperty("--b", app.colors[1]);

  const top = document.createElement("div");
  top.className = "app-top";

  const icon = document.createElement("span");
  icon.className = "app-icon";
  icon.textContent = app.icon;

  const titleGroup = document.createElement("span");
  const heading = document.createElement("h3");
  heading.textContent = app.name;
  const kind = document.createElement("small");
  kind.className = "kind";

  if (app.nativeId) {
    const state = nativeState(app);
    kind.textContent = state?.available
      ? "Нативное приложение · готово"
      : nativeBridgeAvailable
        ? "Нативное приложение · сборка недоступна"
        : "Нативное приложение · узел не подключён";
  } else if (app.repo) {
    kind.textContent = "Системная оболочка";
  } else {
    kind.textContent = "Веб-приложение Mora";
  }

  titleGroup.append(heading, kind);
  top.append(icon, titleGroup);

  const description = document.createElement("p");
  description.textContent = app.description;

  const button = document.createElement("button");
  button.className = "open-app";
  button.type = "button";
  button.dataset.id = app.id;
  button.textContent = app.nativeId
    ? "Открыть нативное приложение"
    : app.repo
      ? "Открыть пространство"
      : "Открыть веб-приложение";

  element.append(top, description, button);
  return element;
}

function render() {
  const query = search.value.trim().toLocaleLowerCase("ru");
  const visible = allApps().filter(app => {
    const categoryMatches = filter === "all" || app.category === filter;
    const text = [app.name, app.role, app.description].join(" ").toLocaleLowerCase("ru");
    return categoryMatches && text.includes(query);
  });

  apps.replaceChildren(...visible.map(card));

  if (!visible.length) {
    const message = document.createElement("p");
    message.className = "empty-results";
    message.textContent = "Ничего не найдено";
    apps.append(message);
  }

  projectGrid.replaceChildren(...projects.map(projectCard));
}

function showDialog(app) {
  currentDialogApp = app;
  $("#dialogTitle").textContent = app.name;
  $("#dialogContent").replaceChildren();

  if (app.image) {
    const image = document.createElement("img");
    image.className = "dialog-image";
    image.src = app.image;
    image.alt = app.name + " desktop capture";
    image.onerror = () => image.remove();
    $("#dialogContent").append(image);
  }

  const description = document.createElement("p");
  description.className = "dialog-copy";
  description.textContent = app.description;
  $("#dialogContent").append(description);

  const actions = document.createElement("div");
  actions.className = "dialog-actions";

  if (app.nativeId) {
    const state = nativeState(app);
    const status = document.createElement("p");
    status.className = "native-status-copy";
    status.textContent = state?.status_message || (
      nativeBridgeAvailable
        ? "Нативная сборка или репозиторий пока не обнаружены."
        : "Для проверки сборки и запуска откройте Mora через локальный узел: python mora_host.py."
    );
    $("#dialogContent").append(status);

    const launch = document.createElement("button");
    launch.type = "button";
    launch.className = "primary native-launch";
    launch.textContent = state?.running ? "Уже запущено" : "Запустить нативное приложение";
    launch.disabled = !state?.available || state?.running;
    launch.addEventListener("click", () => launchNative(app, status, launch));
    actions.append(launch);
  } else if (!app.repo) {
    const frame = document.createElement("iframe");
    frame.className = "app-frame";
    frame.title = app.name + " — веб-приложение Mora";
    frame.allow = "microphone; camera; display-capture; clipboard-read; clipboard-write";
    frame.referrerPolicy = "same-origin";
    frame.src = "../prototype/mora-home.html?app=" + encodeURIComponent(app.id)
      + "&embed=1&theme=" + encodeURIComponent(document.documentElement.dataset.theme || "dark");
    frame.addEventListener("load", () => {
      frame.contentWindow?.postMessage({
        type: "mora:theme",
        theme: document.documentElement.dataset.theme || "dark"
      }, location.origin);
    });
    $("#dialogContent").append(frame);
  } else {
    const note = document.createElement("p");
    note.className = "dialog-copy";
    note.textContent = "Mora — домашний экран и системная оболочка DuckOS. Семь веб-модулей и нативные проекты открываются из общей рабочей области.";
    $("#dialogContent").append(note);
  }

  if (app.repo) {
    actions.append(
      createLink("Открыть репозиторий ↗", app.repo),
      createLink("Релизы и сборки ↗", app.repo + "/releases")
    );
  }

  if (actions.childElementCount) {
    $("#dialogContent").append(actions);
  }

  dialog.showModal();
}

function openApp(id) {
  const app = allApps().find(item => item.id === id);
  if (app) showDialog(app);
}

async function launchNative(app, statusElement, buttonElement) {
  if (!nativeBridgeAvailable) {
    statusElement.textContent = "Локальный узел Mora не подключён. Запустите python mora_host.py и откройте рабочий стол на 127.0.0.1:43860.";
    return;
  }

  const state = nativeState(app);
  if (!state?.available) {
    statusElement.textContent = state?.status_message || "Нативная сборка пока недоступна.";
    return;
  }

  buttonElement.disabled = true;
  buttonElement.textContent = "Запуск…";

  try {
    const response = await fetch("/api/launch/" + encodeURIComponent(app.nativeId), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}"
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(result.error || "Не удалось запустить приложение.");
    }

    statusElement.textContent = result.message || "Приложение запускается в отдельном окне.";
    await refreshNativeApps();
    buttonElement.textContent = "Запустить ещё раз";
    buttonElement.disabled = false;
  } catch (error) {
    statusElement.textContent = error.message;
    buttonElement.textContent = "Повторить запуск";
    buttonElement.disabled = false;
  }
}

function projectCard(app) {
  const element = document.createElement("article");
  element.className = "project-card";

  const image = document.createElement("img");
  image.className = "project-image";
  image.alt = app.name + " desktop capture";
  image.loading = "lazy";
  if (app.image) {
    image.src = app.image;
  } else {
    image.hidden = true;
  }
  image.onerror = () => {
    image.hidden = true;
  };

  const info = document.createElement("div");
  const title = document.createElement("h3");
  title.textContent = app.name;

  const description = document.createElement("p");
  description.textContent = app.description;

  const actions = document.createElement("div");
  actions.className = "actions";

  if (app.nativeId) {
    const state = nativeState(app);
    const launch = document.createElement("button");
    launch.type = "button";
    launch.className = "project-launch";
    launch.textContent = state?.available ? "Запустить" : "Недоступно";
    launch.disabled = !state?.available;
    launch.addEventListener("click", () => openApp(app.id));
    actions.append(launch);
  }

  const repository = createLink("Репозиторий ↗", app.repo);
  const details = document.createElement("button");
  details.type = "button";
  details.className = "project-details";
  details.textContent = "Подробнее";
  details.addEventListener("click", () => openApp(app.id));

  actions.append(repository, details);
  info.append(title, description, actions);
  element.append(image, info);
  return element;
}

apps.addEventListener("click", event => {
  const button = event.target.closest("[data-id]");
  if (button) openApp(button.dataset.id);
});

search.addEventListener("input", render);

document.querySelectorAll(".nav").forEach(button => {
  button.addEventListener("click", () => {
    filter = button.dataset.filter;
    document.querySelectorAll(".nav").forEach(item => item.classList.toggle("active", item === button));
    document.querySelectorAll(".chip").forEach(item => item.classList.toggle("selected", item.dataset.filter === filter));
    render();
  });
});

document.querySelectorAll(".chip").forEach(button => {
  button.addEventListener("click", () => {
    filter = button.dataset.filter;
    document.querySelectorAll(".chip").forEach(item => item.classList.toggle("selected", item === button));
    document.querySelectorAll(".nav").forEach(item => item.classList.toggle("active", item.dataset.filter === filter));
    render();
  });
});

$("#closeDialog").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", event => {
  if (event.target === dialog) dialog.close();
});
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && dialog.open) dialog.close();
});
window.addEventListener("message", event => {
  if (event.origin === location.origin && event.source && event.data?.type === "mora:close-app") {
    dialog.close();
  }
});

$("#projectsJump").addEventListener("click", () => {
  $("#projects").scrollIntoView({ behavior: "smooth" });
});

async function refreshNativeApps() {
  try {
    const response = await fetch("/api/apps", { cache: "no-store" });
    if (!response.ok) {
      throw new Error("Local host is unavailable");
    }

    const payload = await response.json();
    nativeBridgeAvailable = true;
    nativeApps.clear();
    for (const app of payload.apps || []) {
      nativeApps.set(app.id, app);
    }

    const ready = Array.from(nativeApps.values()).filter(app => app.available).length;
    const status = $("#bridgeStatus");
    if (status) {
      status.textContent = "NATIVE TOOLS " + ready + "/" + nativeApps.size;
    }
    const dot = $("#bridgeDot");
    if (dot) dot.classList.add("online");

    applyTheme(payload.theme);
    render();
  } catch {
    nativeBridgeAvailable = false;
    const status = $("#bridgeStatus");
    if (status) status.textContent = "NATIVE LAUNCHER OFFLINE";
    const dot = $("#bridgeDot");
    if (dot) dot.classList.remove("online");
    render();
  }
}

function applyTheme(theme) {
  if (theme !== "dark" && theme !== "light") return;
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("mora-theme", theme);
}

async function toggleTheme() {
  const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
  applyTheme(next);
  const frame = document.querySelector(".app-frame");
  frame?.contentWindow?.postMessage({ type: "mora:theme", theme: next }, location.origin);

  try {
    const response = await fetch("/api/theme", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme: next })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error || "Theme host unavailable");
    }
  } catch {
    // Browser-only mode retains its local theme preference.
  }
}

$("#theme").addEventListener("click", toggleTheme);

function tick() {
  const now = new Date();
  const time = new Intl.DateTimeFormat("ru-RU", {
    hour: "2-digit",
    minute: "2-digit"
  }).format(now);

  $("#clock").textContent = time;
  $("#heroClock").textContent = time;
  $("#date").textContent = new Intl.DateTimeFormat("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long"
  }).format(now);
}

const savedTheme = localStorage.getItem("mora-theme");
if (savedTheme === "light" || savedTheme === "dark") {
  applyTheme(savedTheme);
} else {
  const systemTheme = matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  applyTheme(systemTheme);
}

tick();
setInterval(tick, 10000);
render();
refreshNativeApps();

window.addEventListener("focus", refreshNativeApps);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) refreshNativeApps();
});

if ("serviceWorker" in navigator && location.protocol !== "file:") {
  addEventListener("load", () => {
    navigator.serviceWorker.register("service-worker.js").catch(() => {});
  });
}
