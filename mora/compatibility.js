const PREFIX_PATTERN = /^[a-zA-Z0-9][a-zA-Z0-9._-]{0,47}$/;
const COMPONENTS = new Set([
  "corefonts", "d3dcompiler_47", "dotnet48", "dxvk",
  "vcrun2019", "vcrun2022", "vkd3d"
]);

export const COMPATIBILITY_ENTRIES = Object.freeze([
  { name: "Wine", group: "Запуск", state: "cli", detail: "Win32 API runtime; управляемые префиксы и нативный запуск через CLI DuckOS." },
  { name: "Proton", group: "Запуск", state: "cli", detail: "Запуск через обнаруженный Steam Proton и указанный compatdata-каталог." },
  { name: "DOSBox / Staging", group: "Запуск", state: "cli", detail: "Эмуляция DOS-программ с ограничением имён файлов для прямого запуска." },
  { name: "Winetricks", group: "Компоненты", state: "cli", detail: "Установка ограниченного набора Winetricks-компонентов в выбранный Wine-префикс." },
  { name: "DXVK", group: "Графика", state: "component", detail: "Установка Direct3D 8–11 → Vulkan через Winetricks; нужен совместимый Vulkan-драйвер." },
  { name: "vkd3d-proton", group: "Графика", state: "component", detail: "Компонент Direct3D 12 → Vulkan; совместимость зависит от версии Proton и игры." },
  { name: "CrossOver", group: "Менеджеры", state: "detect", detail: "Коммерческая сборка Wine: обнаруживается, но не заменяет основной backend DuckOS." },
  { name: "Bottles", group: "Менеджеры", state: "detect", detail: "Внешний менеджер префиксов; его графический интерфейс не встраивается в Mora." },
  { name: "Lutris", group: "Менеджеры", state: "detect", detail: "Внешний игровой launcher; каталоги и сценарии Lutris не исполняются из Mora." },
  { name: "Heroic", group: "Менеджеры", state: "detect", detail: "Внешний launcher; поддержка магазина зависит от установленного Heroic." },
  { name: "PortProton", group: "Менеджеры", state: "detect", detail: "Внешняя обёртка Wine/Proton; обнаруживается отдельно от CLI backend." },
  { name: "PlayOnLinux", group: "Менеджеры", state: "detect", detail: "Внешний классический менеджер Wine-префиксов." },
  { name: "Whisky", group: "macOS", state: "mac", detail: "macOS-инструмент; не является Linux-компонентом DuckOS." },
  { name: "Kegworks", group: "macOS", state: "mac", detail: "macOS wrapper builder; не переносится в Linux-сборку." },
  { name: "Game Porting Toolkit", group: "macOS", state: "mac", detail: "Apple/Metal стек; DirectX → Metal здесь не используется." },
  { name: "ReactOS", group: "Отдельная ОС", state: "vm", detail: "Самостоятельная ОС NT-направления; не является Wine-движком или DLL-пакетом." }
]);

function shellQuote(value) {
  return "'" + String(value).replace(/'/g, "'\\''") + "'";
}

function requiredText(value, label, maxLength = 4096) {
  const text = String(value ?? "").trim();
  if (!text || text.length > maxLength || /[\u0000-\u001f\u007f]/.test(text)) {
    throw new TypeError(label + " заполнено некорректно.");
  }
  return text;
}

function validPrefix(value) {
  const name = requiredText(value, "Имя префикса", 48);
  if (!PREFIX_PATTERN.test(name) || name === "." || name === "..") {
    throw new TypeError("Имя префикса: латинские буквы, цифры, точка, дефис или подчёркивание; 1–48 символов.");
  }
  return name;
}

export function buildCompatibilityCommand(action, values = {}) {
  if (action === "status") return "duckos compatibility status";
  if (action === "prefixes") return "duckos compatibility prefixes";

  if (action === "create-prefix") {
    const name = validPrefix(values.prefix);
    const architecture = values.architecture === "win32" ? "win32" : "win64";
    return "duckos compatibility create-prefix --name " + shellQuote(name) +
      " --arch " + architecture;
  }

  if (action === "install-component") {
    const name = validPrefix(values.prefix);
    const component = requiredText(values.component, "Компонент", 32);
    if (!COMPONENTS.has(component)) throw new TypeError("Этот компонент отсутствует в разрешённом списке.");
    return "duckos compatibility install-component --prefix " + shellQuote(name) +
      " --component " + shellQuote(component);
  }

  if (action === "launch") {
    const engine = values.engine || "wine";
    if (!["wine", "proton", "dosbox"].includes(engine)) {
      throw new TypeError("Выберите Wine, Proton или DOSBox.");
    }
    const executable = requiredText(values.executable, "Путь к EXE");
    let command = "duckos compatibility launch --engine " + engine;
    if (engine === "wine") {
      command += " --prefix " + shellQuote(validPrefix(values.prefix));
    } else if (engine === "proton") {
      command += " --compat-data " + shellQuote(requiredText(values.compatData, "Steam compatdata path"));
    }
    return command + " -- " + shellQuote(executable);
  }

  throw new TypeError("Неизвестная операция центра совместимости.");
}

function statusLabel(state) {
  return ({
    cli: "CLI backend",
    component: "Компонент",
    detect: "Обнаружение",
    mac: "Только macOS",
    vm: "Отдельная ОС"
  })[state] || "Справка";
}

export function compatibilityPanelMarkup() {
  const groups = [...new Set(COMPATIBILITY_ENTRIES.map((entry) => entry.group))];
  const catalog = groups.map((group) => {
    const items = COMPATIBILITY_ENTRIES.filter((entry) => entry.group === group);
    return '<section class="compat-group"><h3>' + group + '</h3><div class="compat-entry-list">' +
      items.map((entry) =>
        '<article class="compat-entry"><div class="compat-entry-top"><strong>' +
        entry.name + '</strong><span class="compat-state compat-state-' + entry.state + '">' +
        statusLabel(entry.state) + '</span></div><p>' + entry.detail + '</p></article>'
      ).join("") + '</div></section>';
  }).join("");

  return '<p class="window-kicker">DUCKOS · WINDOWS COMPATIBILITY</p>' +
    '<h2 class="window-heading">Центр совместимости</h2>' +
    '<div class="system-notice warning"><span class="notice-dot"></span><span>Окно Mora не получает доступ к процессам хоста. Команды ниже копируются в терминал; backend CLI выполняет реальные проверки и запуск.</span></div>' +
    '<section class="compat-actions"><h3>Состояние системы</h3><p>Проверить установленные движки, графические средства и системные пути.</p>' +
    '<div class="compat-button-row"><button class="action-button" data-compat-action="status">Скопировать проверку</button>' +
    '<button class="subtle-button" data-compat-action="prefixes">Список префиксов</button></div></section>' +
    '<section class="compat-actions"><h3>Новый Wine-префикс</h3><div class="compat-form-grid">' +
    '<label>Имя <input data-compat-prefix value="games" maxlength="48" autocomplete="off"></label>' +
    '<label>Архитектура <select data-compat-arch><option value="win64">64-bit</option><option value="win32">32-bit</option></select></label></div>' +
    '<button class="action-button" data-compat-action="create-prefix">Скопировать создание префикса</button></section>' +
    '<section class="compat-actions"><h3>Запуск программы</h3><div class="compat-form-grid">' +
    '<label>Движок <select data-compat-engine><option value="wine">Wine</option><option value="proton">Proton</option><option value="dosbox">DOSBox</option></select></label>' +
    '<label data-compat-prefix-wrap>Wine-префикс <input data-compat-prefix-launch value="games" maxlength="48"></label>' +
    '<label class="compat-wide" data-compat-compatdata-wrap hidden>Путь Proton compatdata <input data-compat-compatdata placeholder="/путь/к/steamapps/compatdata/APPID"></label>' +
    '<label class="compat-wide">Полный путь к EXE <input data-compat-executable placeholder="/home/user/Games/setup.exe"></label>' +
    '</div><button class="action-button" data-compat-action="launch">Скопировать команду запуска</button></section>' +
    '<section class="compat-actions"><h3>Графика и зависимости</h3><div class="compat-form-grid">' +
    '<label>Wine-префикс <input data-compat-prefix-component value="games" maxlength="48"></label>' +
    '<label>Компонент <select data-compat-component><option value="dxvk">DXVK</option><option value="vkd3d">vkd3d</option><option value="vcrun2022">Visual C++ 2022</option><option value="vcrun2019">Visual C++ 2019</option><option value="corefonts">Core Fonts</option><option value="d3dcompiler_47">D3DCompiler 47</option><option value="dotnet48">.NET 4.8</option></select></label>' +
    '</div><button class="action-button" data-compat-action="install-component">Скопировать установку компонента</button></section>' +
    '<div class="compat-command-preview"><label for="compat-command-output">Команда для терминала</label><textarea id="compat-command-output" data-compat-command-output rows="2" readonly>Выберите действие выше.</textarea><p data-compat-status role="status">Ничего не выполняется, пока вы не запустите скопированную команду в терминале.</p><button class="subtle-button" data-compat-copy disabled>Копировать команду</button></div>' +
    '<div class="compat-catalog"><h3>Экосистема интеграций</h3>' + catalog + '</div>' +
    '<p class="window-copy">Wine-программы получают права текущего пользователя и не изолированы автоматически. Не запускайте неизвестные EXE. Обход античита, загрузка Windows-драйверов и эмуляция ядра Windows не поддерживаются.</p>';
}
