const projects = [
  {id:"pytyliki",name:"Pytyliki",category:"system",role:"Processor diagnostics",description:"CPU-профили, измерения, мониторинг и локальные отчёты.",icon:"▣",colors:["#5ed9ef","#1769b5"],repo:"https://github.com/Ivan-VHS/Pytyliki",image:"https://raw.githubusercontent.com/Ivan-VHS/Pytyliki/main/assets/screenshots/pytyliki-workstation.png"},
  {id:"reaper",name:"Reaper",category:"developer",role:"Language & Studio IDE",description:"Язык Reaper, редактор, запуск, отладчик, LSP и DAP.",icon:"R",colors:["#c0a7ff","#5d3bc0"],repo:"https://github.com/Ivan-VHS/Reaper",image:"https://raw.githubusercontent.com/Ivan-VHS/Reaper/main/assets/screenshots/reaper-studio.png"},
  {id:"oplague",name:"OPlague",category:"system",role:"Hardware workbench",description:"Инвентаризация устройств и безопасная инспекция пакетов.",icon:"O",colors:["#ff9eaa","#a91f49"],repo:"https://github.com/Ivan-VHS/OPlague",image:"https://raw.githubusercontent.com/Ivan-VHS/OPlague/main/assets/screenshots/oplague-workbench.png"},
  {id:"ventu",name:"VentuSample",category:"creative",role:"Sample workstation",description:"Создание лупов, сэмплов и офлайн-обработка аудио.",icon:"V",colors:["#e6a3ff","#7043b6"],repo:"https://github.com/Ivan-VHS/VentuSample",image:"https://raw.githubusercontent.com/Ivan-VHS/VentuSample/main/assets/screenshots/ventusample-studio.png"},
  {id:"duckos",name:"DuckOS",category:"system",role:"Operating system",description:"Системная платформа и домашний экран Mora.",icon:"🦆",colors:["#ffd36d","#bb781e"],repo:"https://github.com/Ivan-VHS/DuckOS"},
  {id:"cockos",name:"Cockos",category:"creative",role:"Звук и запись",description:"Микшер по приложениям, запись и входные устройства.",icon:"♫",colors:["#ff83ad","#bd3e74"]},
  {id:"kavun",name:"Kavun",category:"creative",role:"Фото и галерея",description:"Альбомы и быстрый просмотр изображений.",icon:"◉",colors:["#75e4a9","#219d6b"]},
  {id:"kabon",name:"Ka-bon",category:"system",role:"Финансы",description:"Расходы, категории, лимиты и локальные отчёты.",icon:"₴",colors:["#ffd45c","#c28a1d"]},
  {id:"gloverty",name:"Gloverty",category:"system",role:"Автоматизация",description:"Сценарии, условия и действия для повседневных задач.",icon:"ϟ",colors:["#ad98ff","#5c43bd"]},
  {id:"po",name:"Po",category:"developer",role:"Браузер",description:"Поиск, вкладки, команды и рабочие ссылки.",icon:"⌕",colors:["#82bfff","#275fba"]},
  {id:"illidia",name:"Illidia",category:"creative",role:"Игры",description:"Игровая библиотека, ярлыки и коллекции.",icon:"⌘",colors:["#6ce4e0","#168c9c"]},
  {id:"unify",name:"Unify",category:"system",role:"Устройства",description:"Статусы устройств и передача файлов между инструментами.",icon:"⌁",colors:["#d8dcff","#7788cc"]}
];

const hardwareApps = [
  {id:"device-atlas",name:"Device Atlas",category:"system",role:"Инвентаризация железа",description:"PCI, USB, ACPI, Hardware IDs и активные драйверы.",icon:"▦",colors:["#7fd6e5","#287f9d"],href:"hardware/index.html#device-atlas"},
  {id:"driver-capture",name:"Driver Capture",category:"system",role:"Резервная копия драйверов",description:"Экспорт Windows Driver Store и SHA-256-манифест.",icon:"⇩",colors:["#b8a4ff","#6045ad"],href:"hardware/index.html#driver-capture"},
  {id:"driver-scout",name:"Driver Scout",category:"system",role:"Поиск драйверов",description:"Windows Update и точный поиск пакетов по Hardware ID.",icon:"⌕",colors:["#8fc4ff","#3a65ac"],href:"hardware/index.html#driver-scout"},
  {id:"driver-lab",name:"Driver Lab",category:"system",role:"Проверка INF и пакетов",description:"Архитектура, модели, Hardware IDs и данные подписи.",icon:"⌘",colors:["#d5a0f4","#8052a8"],href:"hardware/index.html#driver-lab"},
  {id:"driver-graph",name:"Driver Graph",category:"system",role:"Граф соответствий",description:"Точные связи между устройствами и пакетами драйверов.",icon:"⌁",colors:["#8ce0bd","#398b70"],href:"hardware/index.html#driver-graph"},
  {id:"driver-restore",name:"Driver Restore",category:"system",role:"Восстановление",description:"Резервирование, проверка манифеста и адресный откат.",icon:"↶",colors:["#f1c47f","#a66b32"],href:"hardware/index.html#driver-restore"},
  {id:"firmware-atlas",name:"Firmware Atlas",category:"system",role:"BIOS и UEFI",description:"Инвентаризация прошивки и системной платы.",icon:"◉",colors:["#f5b59d","#a75f63"],href:"hardware/index.html#firmware-atlas"},
  {id:"uefi-guard",name:"UEFI Guard",category:"system",role:"Защита платформы",description:"Secure Boot, TPM и сигналы целостности.",icon:"⛨",colors:["#a4dbd1","#4b9289"],href:"hardware/index.html#uefi-guard"},
  {id:"pcie-scope",name:"PCIe Scope",category:"system",role:"PCI Express",description:"Шины, классы PCIe, привязанные драйверы и link-данные.",icon:"⟁",colors:["#a8b1f5","#565fa5"],href:"hardware/index.html#pcie-scope"},
  {id:"gpu-deck",name:"GPU Deck",category:"system",role:"Видеокарты",description:"Графические адаптеры и доступная GPU-телеметрия.",icon:"▧",colors:["#f1a5c8","#a44e83"],href:"hardware/index.html#gpu-deck"},
  {id:"cpu-lab",name:"CPU Lab",category:"system",role:"Процессор",description:"Топология CPU, потоки, частоты и governor.",icon:"◫",colors:["#f2c27e","#9b793c"],href:"hardware/index.html#cpu-lab"},
  {id:"memory-lens",name:"Memory Lens",category:"system",role:"Оперативная память",description:"RAM, доступная память, commit и paging pressure.",icon:"▤",colors:["#a5c8f4","#577fae"],href:"hardware/index.html#memory-lens"},
  {id:"storage-pulse",name:"Storage Pulse",category:"system",role:"Накопители",description:"NVMe/SATA, объём, интерфейсы и доступное состояние.",icon:"▣",colors:["#9ad7b2","#4b8c68"],href:"hardware/index.html#storage-pulse"},
  {id:"thermal-core",name:"Thermal Core",category:"system",role:"Температуры и питание",description:"Температуры, датчики питания и признаки троттлинга.",icon:"♨",colors:["#f29c87","#a84a50"],href:"hardware/index.html#thermal-core"},
  {id:"gameframe",name:"GameFrame",category:"system",role:"Игровая производительность",description:"Игровые профили, frame pacing и повторяемые замеры.",icon:"▷",colors:["#9c9af5","#5850b2"],href:"hardware/index.html#gameframe"}
];

const $ = (selector) => document.querySelector(selector);
const apps = $("#apps");
const projectGrid = $("#projectGrid");
const dialog = $("#appDialog");
const search = $("#search");
let filter = "all";

function card(app) {
  const node = document.createElement("article");
  node.className = "app-card";
  node.style.setProperty("--a", app.colors[0]);
  node.style.setProperty("--b", app.colors[1]);

  const top = document.createElement("div");
  top.className = "app-top";
  const icon = document.createElement("span");
  icon.className = "app-icon";
  icon.textContent = app.icon;
  const heading = document.createElement("span");
  const title = document.createElement("h3");
  title.textContent = app.name;
  const role = document.createElement("small");
  role.className = "kind";
  role.textContent = app.role;
  heading.append(title, role);
  top.append(icon, heading);

  const description = document.createElement("p");
  description.textContent = app.description;
  const button = document.createElement("button");
  button.className = "open-app";
  button.dataset.id = app.id;
  button.type = "button";
  button.textContent = app.href ? "Открыть инструмент" : app.repo ? "Открыть пространство" : "Открыть модуль";
  node.append(top, description, button);
  return node;
}

function render() {
  const query = search.value.trim().toLocaleLowerCase("ru");
  const visible = projects.concat(hardwareApps).filter((app) =>
    (filter === "all" || app.category === filter) &&
    [app.name, app.role, app.description].join(" ").toLocaleLowerCase("ru").includes(query)
  );
  apps.replaceChildren(...visible.map(card));
  if (!visible.length) {
    const empty = document.createElement("p");
    empty.textContent = "Ничего не найдено";
    apps.append(empty);
  }
}

function openApp(id) {
  const app = projects.concat(hardwareApps).find((item) => item.id === id);
  if (!app) return;
  if (app.href) {
    window.location.assign(app.href);
    return;
  }

  $("#dialogTitle").textContent = app.name;
  const content = $("#dialogContent");
  content.replaceChildren();

  if (app.image) {
    const image = document.createElement("img");
    image.className = "dialog-image";
    image.src = app.image;
    image.alt = app.name + " desktop capture";
    image.onerror = () => image.remove();
    content.append(image);
  }

  const description = document.createElement("p");
  description.className = "dialog-copy";
  description.textContent = app.description;
  content.append(description);

  const actions = document.createElement("div");
  actions.className = "dialog-actions";
  if (app.repo) {
    const repository = document.createElement("a");
    repository.href = app.repo;
    repository.target = "_blank";
    repository.rel = "noreferrer";
    repository.textContent = "Открыть репозиторий ↗";
    const releases = document.createElement("a");
    releases.href = app.repo + "/releases";
    releases.target = "_blank";
    releases.rel = "noreferrer";
    releases.textContent = "Релизы и сборки ↗";
    actions.append(repository, releases);
  } else {
    const note = document.createElement("span");
    note.className = "dialog-copy";
    note.textContent = "Модуль зарегистрирован в Mora. Для полной работы нужны соответствующие системные службы и разрешения DuckOS.";
    actions.append(note);
  }
  content.append(actions);
  dialog.showModal();
}

apps.addEventListener("click", (event) => {
  const button = event.target.closest("[data-id]");
  if (button) openApp(button.dataset.id);
});
search.addEventListener("input", render);

document.querySelectorAll(".nav").forEach((button) => {
  button.addEventListener("click", () => {
    filter = button.dataset.filter;
    document.querySelectorAll(".nav").forEach((item) => item.classList.toggle("active", item === button));
    document.querySelectorAll(".chip").forEach((item) => item.classList.toggle("selected", item.dataset.filter === filter));
    render();
  });
});
document.querySelectorAll(".chip").forEach((button) => {
  button.addEventListener("click", () => {
    filter = button.dataset.filter;
    document.querySelectorAll(".chip").forEach((item) => item.classList.toggle("selected", item === button));
    document.querySelectorAll(".nav").forEach((item) => item.classList.toggle("active", item.dataset.filter === filter));
    render();
  });
});

function projectCard(app) {
  const node = document.createElement("article");
  node.className = "project-card";

  const image = document.createElement("img");
  image.className = "project-image";
  image.alt = app.name + " desktop capture";
  image.loading = "lazy";
  if (app.image) image.src = app.image;
  image.onerror = () => image.removeAttribute("src");

  const info = document.createElement("div");
  const title = document.createElement("h3");
  title.textContent = app.name;
  const description = document.createElement("p");
  description.textContent = app.description;
  const actions = document.createElement("div");
  actions.className = "actions";

  const repository = document.createElement("a");
  repository.href = app.repo;
  repository.target = "_blank";
  repository.rel = "noreferrer";
  repository.textContent = "Репозиторий ↗";

  const details = document.createElement("a");
  details.href = "#";
  details.textContent = "Подробнее";
  details.addEventListener("click", (event) => {
    event.preventDefault();
    openApp(app.id);
  });

  actions.append(repository, details);
  info.append(title, description, actions);
  node.append(image, info);
  return node;
}

projectGrid.replaceChildren(...projects.filter((app) => app.repo).map(projectCard));

$("#theme").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("mora-theme", next);
});
$("#closeDialog").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && dialog.open) dialog.close();
});
$("#projectsJump").addEventListener("click", () => $("#projects").scrollIntoView({behavior:"smooth"}));

function tick() {
  const now = new Date();
  $("#clock").textContent = new Intl.DateTimeFormat("ru-RU", {hour:"2-digit",minute:"2-digit"}).format(now);
  $("#heroClock").textContent = $("#clock").textContent;
  $("#date").textContent = new Intl.DateTimeFormat("ru-RU", {weekday:"long",day:"numeric",month:"long"}).format(now);
}

const savedTheme = localStorage.getItem("mora-theme");
if (savedTheme === "light" || savedTheme === "dark") document.documentElement.dataset.theme = savedTheme;
else if (matchMedia("(prefers-color-scheme: light)").matches) document.documentElement.dataset.theme = "light";

tick();
setInterval(tick, 10000);
render();
if ("serviceWorker" in navigator && location.protocol !== "file:") {
  addEventListener("load", () => navigator.serviceWorker.register("service-worker.js").catch(() => {}));
}
