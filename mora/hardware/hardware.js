(() => {
  "use strict";

  const modules = [
    {id:"device-atlas",name:"Device Atlas",icon:"▦",group:"device",role:"Инвентаризация устройств",description:"PCI, USB, ACPI, Plug-and-Play IDs, классы и назначенные драйверы.",color:["#7fd6e5","#287f9d"],mode:"READ ONLY"},
    {id:"driver-capture",name:"Driver Capture",icon:"⇩",group:"device",role:"Снимок Driver Store",description:"Экспорт установленных пакетов Windows и манифест SHA-256 без установки.",color:["#b8a4ff","#6045ad"],mode:"EXPORT ONLY"},
    {id:"driver-scout",name:"Driver Scout",icon:"⌕",group:"device",role:"Официальный поиск драйверов",description:"Поиск Windows Update и точечный переход к каталогу по точному Hardware ID.",color:["#8fc4ff","#3a65ac"],mode:"NETWORK READ"},
    {id:"driver-lab",name:"Driver Lab",icon:"⌘",group:"device",role:"Лаборатория пакетов",description:"Разбор INF, архитектуры, моделей, ID и подготовка доказательств для OPlague.",color:["#d5a0f4","#8052a8"],mode:"READ ONLY"},
    {id:"driver-graph",name:"Driver Graph",icon:"⌁",group:"device",role:"Граф совместимости",description:"Точное сопоставление Hardware ID устройства с данными пакета, без догадок по имени.",color:["#8ce0bd","#398b70"],mode:"READ ONLY"},
    {id:"driver-restore",name:"Driver Restore",icon:"↶",group:"device",role:"Резервирование и откат",description:"Просмотр манифеста копии и подготовка адресной команды восстановления.",color:["#f1c47f","#a66b32"],mode:"EXPLICIT APPLY"},
    {id:"firmware-atlas",name:"Firmware Atlas",icon:"◉",group:"firmware",role:"BIOS и UEFI",description:"Версия BIOS, производитель платы, дата прошивки и режим загрузки.",color:["#f5b59d","#a75f63"],mode:"READ ONLY"},
    {id:"uefi-guard",name:"UEFI Guard",icon:"⛨",group:"firmware",role:"Безопасность платформы",description:"Secure Boot, TPM и доступные сигналы целостности прошивки.",color:["#a4dbd1","#4b9289"],mode:"READ ONLY"},
    {id:"pcie-scope",name:"PCIe Scope",icon:"⟁",group:"firmware",role:"PCI Express",description:"PCIe-устройства, классы, активные драйверы и доступные link-параметры.",color:["#a8b1f5","#565fa5"],mode:"READ ONLY"},
    {id:"gpu-deck",name:"GPU Deck",icon:"▧",group:"performance",role:"Графический адаптер",description:"GPU, драйвер и телеметрия, которую действительно предоставляет платформа.",color:["#f1a5c8","#a44e83"],mode:"READ ONLY"},
    {id:"cpu-lab",name:"CPU Lab",icon:"◫",group:"performance",role:"Процессор и частоты",description:"Модель CPU, потоки, доступные частоты и governor.",color:["#f2c27e","#9b793c"],mode:"READ ONLY"},
    {id:"memory-lens",name:"Memory Lens",icon:"▤",group:"performance",role:"Оперативная память",description:"Объём RAM, доступная память и системное давление.",color:["#a5c8f4","#577fae"],mode:"READ ONLY"},
    {id:"storage-pulse",name:"Storage Pulse",icon:"▣",group:"performance",role:"Накопители и I/O",description:"Физические диски, интерфейсы, объём и доступные health-счётчики.",color:["#9ad7b2","#4b8c68"],mode:"READ ONLY"},
    {id:"thermal-core",name:"Thermal Core",icon:"♨",group:"performance",role:"Температуры и питание",description:"Температуры, доступные power counters и признаки троттлинга.",color:["#f29c87","#a84a50"],mode:"READ ONLY"},
    {id:"gameframe",name:"GameFrame",icon:"▷",group:"performance",role:"Игровая производительность",description:"Локальные игровые профили и измерение frame pacing без скрытых системных изменений.",color:["#9c9af5","#5850b2"],mode:"PROFILE ONLY"}
  ];

  const $ = (selector) => document.querySelector(selector);
  const byId = (id) => modules.find((item) => item.id === id);
  const state = { snapshot: null, offers: null, browserGpu: null, selected: "overview", benchmarkRunning: false };
  const toastNode = $("#toast");
  let toastTimer = 0;

  function showToast(message) {
    toastNode.textContent = message;
    toastNode.classList.add("visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toastNode.classList.remove("visible"), 2600);
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function kv(container, key, value) {
    const row = element("div", "hw-kv");
    row.append(element("span", "", key), element("span", "", value === null || value === undefined || value === "" ? "Неизвестно" : value));
    container.append(row);
  }

  function card(title, description) {
    const node = element("article", "hw-detail-card");
    node.append(element("h3", "", title));
    if (description) node.append(element("p", "", description));
    return node;
  }

  function table(headers, rows) {
    if (!rows.length) return element("div", "hw-empty", "В отчёте нет подходящих записей. Импортируй локальный отчёт агента; отсутствующие поля не будут домыслены.");
    const wrap = element("div", "hw-table-wrap");
    const node = element("table", "hw-table");
    const head = document.createElement("thead");
    const headRow = document.createElement("tr");
    headers.forEach((label) => headRow.append(element("th", "", label)));
    head.append(headRow);
    const body = document.createElement("tbody");
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      row.forEach((value) => tr.append(element("td", "", value)));
      body.append(tr);
    });
    node.append(head, body);
    wrap.append(node);
    return wrap;
  }

  function field(label, input, type) {
    const wrapper = element("label", "hw-field");
    wrapper.append(element("span", "", label));
    if (type === "textarea") input.classList.add("hw-field-control");
    wrapper.append(input);
    return wrapper;
  }

  function actionButton(label, callback, primary) {
    const button = element("button", "hw-action" + (primary ? " primary" : ""), label);
    button.type = "button";
    button.addEventListener("click", callback);
    return button;
  }

  function codeBlock(text) {
    return element("code", "hw-code", text);
  }

  async function copyText(value) {
    try {
      await navigator.clipboard.writeText(value);
      showToast("Команда скопирована. Проверь путь перед запуском.");
    } catch {
      showToast("Буфер обмена недоступен. Выдели и скопируй команду вручную.");
    }
  }

  function browserFacts() {
    const nav = navigator;
    let gpu = null;
    try {
      const canvas = document.createElement("canvas");
      const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");
      if (gl) {
        const extension = gl.getExtension("WEBGL_debug_renderer_info");
        gpu = {
          api: (typeof WebGL2RenderingContext !== "undefined" && gl instanceof WebGL2RenderingContext) ? "WebGL 2" : "WebGL",
          vendor: extension ? gl.getParameter(extension.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR),
          renderer: extension ? gl.getParameter(extension.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)
        };
        gl.getExtension("WEBGL_lose_context")?.loseContext();
      }
    } catch { /* Browser policy may hide GPU details. */ }
    state.browserGpu = gpu;
    return {
      collected_at: new Date().toISOString(),
      user_agent: nav.userAgent,
      platform_hint: nav.userAgentData?.platform || nav.platform || "Недоступно",
      architecture_hint: nav.userAgentData?.architecture || "Недоступно",
      logical_processors: Number.isFinite(nav.hardwareConcurrency) ? nav.hardwareConcurrency : null,
      device_memory_gib: Number.isFinite(nav.deviceMemory) ? nav.deviceMemory : null,
      browser_gpu: gpu,
      storage: null,
      performance_memory: null
    };
  }

  const localFacts = browserFacts();

  async function enrichBrowserFacts() {
    if (navigator.storage?.estimate) {
      try {
        const estimate = await navigator.storage.estimate();
        localFacts.storage = { quota_bytes: estimate.quota ?? null, usage_bytes: estimate.usage ?? null };
      } catch { /* Optional API. */ }
    }
    if (performance.memory) {
      localFacts.performance_memory = {
        used_bytes: performance.memory.usedJSHeapSize,
        total_bytes: performance.memory.totalJSHeapSize,
        limit_bytes: performance.memory.jsHeapSizeLimit
      };
    }
    renderMetrics();
  }

  function currentSnapshot() {
    return state.snapshot || {};
  }

  function firstCpu() {
    const value = currentSnapshot().cpu;
    if (Array.isArray(value)) return value[0] || {};
    return value && typeof value === "object" ? value : {};
  }

  function formatBytes(value) {
    if (!Number.isFinite(Number(value)) || Number(value) < 0) return "—";
    const units = ["Б", "КиБ", "МиБ", "ГиБ", "ТиБ"];
    let amount = Number(value);
    let unit = 0;
    while (amount >= 1024 && unit < units.length - 1) { amount /= 1024; unit += 1; }
    return amount.toFixed(unit > 1 ? 1 : 0) + " " + units[unit];
  }

  function renderMetrics() {
    const report = currentSnapshot();
    const cpu = firstCpu();
    const devices = Array.isArray(report.devices) ? report.devices : [];
    const gpu = Array.isArray(report.gpu) && report.gpu.length
      ? (report.gpu[0].name || report.gpu[0].Name || report.gpu[0].device_id || "Обнаружен")
      : (state.browserGpu?.renderer || "—");
    const memory = report.memory?.total_bytes
      ? formatBytes(report.memory.total_bytes)
      : localFacts.device_memory_gib ? "~" + localFacts.device_memory_gib + " ГиБ*" : "—";
    $("#metricCpu").textContent = cpu.logical_processors || localFacts.logical_processors || "—";
    $("#metricCpuSource").textContent = cpu.name || "логические потоки";
    $("#metricGpu").textContent = String(gpu).slice(0, 22);
    $("#metricGpuSource").textContent = report.gpu?.length ? "отчёт агента" : "WebGL / браузерная оценка";
    $("#metricMemory").textContent = memory;
    $("#metricMemorySource").textContent = report.memory?.total_bytes ? "физическая память" : "deviceMemory — оценка браузера";
    $("#metricDevices").textContent = report.devices ? devices.length : "—";
    $("#metricDevicesSource").textContent = report.devices ? "PnP / sysfs отчёт" : "нет отчёта агента";
    $("#agentStatus").textContent = state.snapshot
      ? "ЛОКАЛЬНЫЙ ОТЧЁТ ЗАГРУЖЕН · " + (report.platform || "UNKNOWN").toUpperCase()
      : "БРАУЗЕРНЫЙ РЕЖИМ · АГЕНТ НЕ ПОДКЛЮЧЁН";
    $("#evidenceState").textContent = state.snapshot ? "Данные агента импортированы" : "Ожидается локальный отчёт";
    $("#hostPlatform").textContent = report.platform || localFacts.platform_hint || "Браузер";
    $("#hostRelease").textContent = report.host?.os || "Веб-страница не имеет доступа к версии ОС";
    $("#firmwareVersion").textContent = report.firmware?.version || report.firmware?.bios_version || "Неизвестно";
    $("#firmwareVendor").textContent = report.firmware?.vendor || report.firmware?.bios_vendor || "BIOS/UEFI данные недоступны";
    $("#graphicsApi").textContent = state.browserGpu?.api || "WebGL недоступен";
    $("#graphicsRenderer").textContent = state.browserGpu?.renderer || "GPU скрыт политикой браузера";
  }

  function renderSideNavigation() {
    const groups = {
      device: $("#sideDevice"),
      firmware: $("#sideFirmware"),
      performance: $("#sidePerformance")
    };
    Object.values(groups).forEach((group) => group.replaceChildren());
    modules.forEach((app) => {
      const button = element("button", "hw-side-link");
      button.type = "button";
      button.dataset.app = app.id;
      button.append(element("span", "", app.icon), document.createTextNode(app.name));
      button.addEventListener("click", () => openModule(app.id));
      groups[app.group].append(button);
    });
  }

  function renderModuleGrid() {
    const query = $("#moduleSearch").value.trim().toLocaleLowerCase("ru");
    const grid = $("#moduleGrid");
    grid.replaceChildren();
    const visible = modules.filter((app) => (app.name + " " + app.role + " " + app.description).toLocaleLowerCase("ru").includes(query));
    visible.forEach((app) => {
      const item = element("article", "hw-app-card");
      item.style.setProperty("--accent-a", app.color[0]);
      item.style.setProperty("--accent-b", app.color[1]);
      const top = element("div", "hw-app-card-top");
      top.append(element("span", "hw-app-icon", app.icon));
      const title = element("div");
      title.append(element("h3", "", app.name), element("small", "", app.role));
      top.append(title);
      item.append(top, element("p", "", app.description));
      const button = element("button", "", "Открыть приложение");
      button.type = "button";
      button.addEventListener("click", () => openModule(app.id));
      item.append(button);
      grid.append(item);
    });
    if (!visible.length) grid.append(element("div", "hw-empty", "Ничего не найдено."));
  }

  function openModule(id) {
    if (id === "overview") {
      state.selected = "overview";
      $("#overviewPanel").hidden = false;
      $("#detailPanel").hidden = true;
    } else {
      const app = byId(id);
      if (!app) return;
      state.selected = id;
      $("#overviewPanel").hidden = true;
      $("#detailPanel").hidden = false;
      renderDetail(app);
    }
    document.querySelectorAll(".hw-side-link").forEach((button) => button.classList.toggle("active", button.dataset.app === id));
    window.location.hash = id === "overview" ? "" : id;
  }

  function detailLayout(app) {
    const content = $("#detailContent");
    content.replaceChildren();
    const header = element("div", "hw-detail-head");
    header.append(element("span", "hw-app-icon", app.icon));
    const title = element("div");
    title.append(element("h2", "", app.name), element("p", "", app.description));
    header.append(title);
    content.append(header);
    const meta = element("div", "hw-inline-actions");
    meta.append(element("span", "hw-badge", app.mode));
    meta.append(element("span", "hw-badge", "ИСТОЧНИКИ ПОКАЗАНЫ"));
    content.append(meta);
    const grid = element("div", "hw-detail-grid");
    content.append(grid);
    return grid;
  }

  function snapshotArray(key) {
    const value = currentSnapshot()[key];
    return Array.isArray(value) ? value : [];
  }

  function deviceRows(items) {
    return items.slice(0, 120).map((item) => [
      item.name || item.Name || item.device_name || "Без имени",
      item.bus || item.class || item.PNPClass || "—",
      Array.isArray(item.hardware_ids) ? item.hardware_ids.slice(0, 2).join(", ") : (item.device_id || item.DeviceID || "—"),
      item.status || item.Status || item.driver || "—"
    ]);
  }

  function renderDeviceAtlas(grid) {
    const box = card("Обнаруженные устройства", "Не более 120 строк показывается в таблице; полный исходный отчёт остаётся в локальном JSON.");
    box.append(table(["Устройство", "Шина / класс", "Идентификатор", "Статус / драйвер"], deviceRows(snapshotArray("devices"))));
    grid.append(box);
    const note = card("Источники", "Windows: Win32_PnPEntity / PnPSignedDriver. Linux: sysfs PCI/USB.");
    note.append(element("p", "", "Точное совпадение Hardware ID — это кандидат для дальнейшей проверки, а не автоматическое разрешение на установку."));
    grid.append(note);
  }

  function renderDriverCapture(grid) {
    const box = card("Экспорт Driver Store", "Работает на Windows. Команда копирует установленные сторонние пакеты в пустой каталог и формирует SHA-256-манифест.");
    const command = 'python agent/duckos_hardware_agent.py export-drivers --output "D:\\DuckOSDriverBackup"';
    box.append(codeBlock(command));
    const actions = element("div", "hw-inline-actions");
    actions.append(actionButton("Копировать команду", () => copyText(command), true));
    box.append(actions);
    box.append(element("p", "", "Запускай терминал от администратора только для этого действия. Убедись, что целевая папка пуста и находится на диске с достаточным свободным местом."));
    const manifest = card("Манифест резервной копии");
    manifest.append(element("p", "", "Экспортный манифест duckos-driver-capture.manifest.json содержит относительные пути, размеры и SHA-256. Он подтверждает целостность копии, но сам по себе не подтверждает совместимость или подпись."));
    grid.append(box, manifest);
  }

  function renderDriverScout(grid) {
    const search = card("Поиск по точному Hardware ID", "Укажи ID из Device Atlas. Поиск откроется только после нажатия — Mora не отправляет идентификаторы автоматически.");
    const input = document.createElement("input");
    input.type = "text";
    input.id = "hardwareIdQuery";
    input.placeholder = "PCI\\VEN_10DE&DEV_2684";
    search.append(field("Hardware ID", input));
    const actions = element("div", "hw-inline-actions");
    const open = actionButton("Открыть Microsoft Update Catalog", () => {
      const value = input.value.trim();
      if (!value) return showToast("Сначала введи точный Hardware ID.");
      window.open("https://www.catalog.update.microsoft.com/Search.aspx?q=" + encodeURIComponent(value), "_blank", "noopener,noreferrer");
    }, true);
    actions.append(open);
    search.append(actions);
    const scan = card("Автоматический поиск Windows Update", "Локальный агент может запросить только опубликованные Windows Update предложения типа Driver. Ничего не устанавливается на этапе поиска.");
    const command = "python agent/duckos_hardware_agent.py scan-driver-updates --output driver-offers.json";
    scan.append(codeBlock(command));
    scan.append(actionButton("Копировать команду поиска", () => copyText(command)));
    grid.append(search, scan);
    renderOffers(grid);
  }

  function renderOffers(grid) {
    if (!state.offers) return;
    const box = card("Предложения Windows Update", "Импортированный список предложений. Установка остаётся отдельной операцией в локальном терминале.");
    const items = state.offers.updates || [];
    box.append(element("p", "", "Найдено: " + items.length));
    const rows = items.slice(0, 100).map((item) => [
      item.title || "Без названия",
      item.driver_manufacturer || "—",
      item.driver_model || item.driver_class || "—",
      item.update_id || "—",
      item.reboot_required ? "Требуется" : "Не указано"
    ]);
    box.append(table(["Пакет", "Производитель", "Модель / класс", "Update ID", "Перезагрузка"], rows));
    const command = items.length ? "python agent/duckos_hardware_agent.py install-driver-update --update-id " + items[0].update_id + ' --backup-dir "D:\\DuckOSDriverBackup"' : "";
    if (command) {
      box.append(element("p", "", "Команда для первого предложения. Перед запуском проверь устройство, название, поставщика и GUID."));
      box.append(codeBlock(command));
      box.append(actionButton("Копировать команду установки", () => copyText(command), true));
    }
    grid.append(box);
  }

  function renderDriverLab(grid) {
    const box = card("Проверка INF", "Выбери INF-файл из пакета. В браузере анализируется только текстовая совместимость; подпись CAT, PE и publisher проверяются отдельным инспектором OPlague.");
    box.append(element("p", "", "Файл читается локально и не загружается в сеть."));
    box.append(actionButton("Выбрать INF-файл", () => $("#infFile").click(), true));
    const results = element("div", "hw-empty", "INF ещё не выбран.");
    results.id = "infResults";
    box.append(results);
    grid.append(box);
    const o = card("Глубокая проверка OPlague", "Используй существующие инспекторы для Authenticode, PE, INF target decorations и аудита доказательств.");
    const link = element("a", "hw-action", "Открыть OPlague ↗");
    link.href = "https://github.com/Ivan-VHS/OPlague";
    link.target = "_blank";
    link.rel = "noreferrer";
    o.append(link);
    grid.append(o);
  }

  function renderDriverGraph(grid) {
    const devices = snapshotArray("devices");
    const drivers = snapshotArray("drivers");
    const rows = [];
    devices.forEach((device) => {
      const ids = new Set([device.device_id, ...(Array.isArray(device.hardware_ids) ? device.hardware_ids : [])].filter(Boolean).map((value) => String(value).toUpperCase()));
      const matched = drivers.filter((driver) => {
        const candidateIds = [driver.device_id, ...(Array.isArray(driver.hardware_ids) ? driver.hardware_ids : [])].filter(Boolean);
        return candidateIds.some((value) => ids.has(String(value).toUpperCase()));
      });
      matched.forEach((driver) => rows.push([
        device.name || device.Name || device.device_id || "Устройство",
        driver.name || driver.device_name || driver.Name || driver.device_id || "Драйвер",
        "Совпадение ID · кандидат"
      ]));
    });
    const box = card("Точные совпадения", "Граф строится только на равенстве идентификаторов, полученных из отчёта. Названия устройств не участвуют в подборе.");
    box.append(table(["Устройство", "Кандидат драйвера", "Вердикт"], rows));
    grid.append(box);
    const note = card("Семантика графа");
    note.append(element("p", "", "Ребро означает найденное совпадение ID. Оно не подтверждает правильность версии, совместимость с текущей сборкой ОС, rank, подпись, происхождение или стабильность."));
    grid.append(note);
  }

  function renderDriverRestore(grid) {
    const box = card("Проверенный откат", "Сначала экспортируй Driver Store. Восстановление выполняй только для конкретного INF после проверки подписи, версии, архитектуры и Hardware ID.");
    const command = 'pnputil /add-driver "D:\\DuckOSDriverBackup\\<package>\\<driver>.inf" /install';
    box.append(codeBlock(command));
    box.append(actionButton("Копировать шаблон команды", () => copyText(command)));
    box.append(element("p", "", "Путь в команде — шаблон. Не запускай её с wildcard по всему каталогу: выбери один проверенный INF и проверь список затрагиваемых устройств."));
    const manifest = card("Результат экспорта");
    manifest.append(element("p", "", "Открой duckos-driver-capture.manifest.json в резервной папке и сравни SHA-256 перед использованием. Автоматическое массовое понижение версий отключено."));
    grid.append(box, manifest);
  }

  function renderFirmwareAtlas(grid) {
    const data = currentSnapshot().firmware || {};
    const box = card("Информация о прошивке", "Значения поступают из CIM/SMBIOS/DMI или EFI. Если платформа не раскрыла поле, оно остаётся неизвестным.");
    ["vendor","version","release_date","board_vendor","board_name","system_vendor","system_product","uefi_mode"].forEach((key) => kv(box, key, data[key]));
    grid.append(box);
    const note = card("Прошивка устройства");
    note.append(element("p", "", "Для EC, VBIOS и периферийных контроллеров нужны отдельные адаптеры конкретного производителя. Универсального безопасного интерфейса записи BIOS не существует."));
    grid.append(note);
  }

  function renderUefiGuard(grid) {
    const data = currentSnapshot().firmware || {};
    const box = card("Состояние платформенной защиты", "Неизвестное значение не интерпретируется как выключенная защита.");
    const secure = data.secure_boot === true ? "Включён" : data.secure_boot === false ? "Выключен" : "Неизвестно";
    const tpm = data.tpm_present === true ? "Обнаружен" : data.tpm_present === false ? "Не обнаружен" : "Неизвестно";
    kv(box, "Secure Boot", secure);
    kv(box, "TPM", tpm);
    kv(box, "Режим UEFI", data.uefi_mode === true ? "UEFI" : data.uefi_mode === false ? "Legacy / не обнаружен" : "Неизвестно");
    grid.append(box);
    const note = card("Firmware Guard");
    note.append(element("p", "", "Приложение не меняет Secure Boot keys, TPM state, boot order, BIOS variables или firmware. Для обновления прошивки необходимы точный board revision и официальный подписанный образ."));
    grid.append(note);
  }

  function renderPcieScope(grid) {
    const items = snapshotArray("devices").filter((item) => String(item.bus || "").toUpperCase() === "PCI");
    const rows = items.map((item) => [
      item.name || item.device_id || "PCI device",
      item.device_id || "—",
      item.class_code || item.class || "—",
      item.driver || item.driver_module || "—",
      item.link_speed || item.current_link_speed || "Не раскрыто",
      item.link_width || item.current_link_width || "Не раскрыто"
    ]);
    const box = card("PCI Express inventory", "Базовый агент читает ID и привязанный драйвер. Скорость и ширина линии появятся только при наличии соответствующего sysfs/CIM/vendor counter.");
    box.append(table(["Устройство", "BDF", "Класс", "Драйвер", "Link speed", "Link width"], rows));
    grid.append(box);
  }

  function renderGpuDeck(grid) {
    const items = snapshotArray("gpu");
    const box = card("Графические адаптеры", "Нативный отчёт имеет приоритет. WebGL ниже — только сведения о рендерере браузера.");
    const rows = items.map((gpu) => [
      gpu.name || gpu.Name || gpu.device_id || "GPU",
      gpu.driver || gpu.DriverVersion || "—",
      gpu.vendor_id || gpu.vendor || "—",
      gpu.device_code || gpu.device_id || gpu.PNPDeviceID || "—"
    ]);
    box.append(table(["Адаптер", "Драйвер", "Vendor", "Device"], rows));
    if (!items.length) box.append(element("p", "", state.browserGpu ? "WebGL: " + state.browserGpu.renderer + ". Это не полный список GPU и не версия системного драйвера." : "GPU-данные не предоставлены."));
    grid.append(box);
  }

  function renderCpuLab(grid) {
    const cpu = firstCpu();
    const box = card("Параметры процессора", "Частота показывается только при наличии аппаратного счётчика. Значение из браузера — количество логических потоков, а не физическая топология.");
    ["name","manufacturer","cores","logical_processors","max_clock_mhz","current_clock_mhz","governor"].forEach((key) => kv(box, key, cpu[key]));
    if (!cpu.name) kv(box, "Browser logical processors", localFacts.logical_processors);
    grid.append(box);
    const link = element("a", "hw-action", "Открыть Pytyliki ↗");
    link.href = "https://github.com/Ivan-VHS/Pytyliki";
    link.target = "_blank";
    link.rel = "noreferrer";
    box.append(element("p", "", "Для расширенных CPU-бенчмарков и source-labelled сенсорных снимков используй Pytyliki."), link);
  }

  function renderMemoryLens(grid) {
    const memory = currentSnapshot().memory || {};
    const box = card("Физическая память", "Оценка navigator.deviceMemory — грубая браузерная категория, а не точный объём установленной RAM.");
    kv(box, "Всего", formatBytes(memory.total_bytes) || "—");
    kv(box, "Доступно", formatBytes(memory.available_bytes));
    kv(box, "Swap total", formatBytes(memory.swap_total_bytes));
    kv(box, "Browser deviceMemory", localFacts.device_memory_gib ? "~" + localFacts.device_memory_gib + " ГиБ" : "Не раскрыто");
    if (localFacts.performance_memory) kv(box, "JS heap", formatBytes(localFacts.performance_memory.used_bytes) + " / " + formatBytes(localFacts.performance_memory.limit_bytes));
    grid.append(box);
  }

  function renderStoragePulse(grid) {
    const items = snapshotArray("storage");
    const box = card("Физические накопители", "SMART/NVMe health не выводится, если нативный адаптер не предоставил соответствующие атрибуты.");
    const rows = items.map((disk) => [
      disk.name || disk.Model || disk.device || "Disk",
      disk.InterfaceType || disk.interface || "—",
      formatBytes(disk.size_bytes || disk.Size),
      disk.Status || disk.health || "Не раскрыто"
    ]);
    box.append(table(["Накопитель", "Интерфейс", "Размер", "Статус"], rows));
    if (localFacts.storage) kv(box, "Browser storage quota", formatBytes(localFacts.storage.quota_bytes));
    grid.append(box);
  }

  function renderThermalCore(grid) {
    const sensors = snapshotArray("sensors");
    const box = card("Доступные сенсоры", "Источники и качество измерения показываются рядом с показаниями. Наличие датчика зависит от платформы, ядра и производителя.");
    const rows = sensors.map((sensor) => [
      sensor.name || sensor.label || "Sensor",
      sensor.value === undefined ? "—" : sensor.value,
      sensor.unit || "—",
      sensor.source || "—",
      sensor.quality || "unknown"
    ]);
    box.append(table(["Сенсор", "Значение", "Ед.", "Источник", "Качество"], rows));
    if (!sensors.length) box.append(element("p", "", "Температурные данные недоступны без нативного датчика. Не пытайся оценивать температуру по нагрузке CPU или GPU."));
    grid.append(box);
  }

  function percentile(values, p) {
    if (!values.length) return 0;
    const sorted = values.slice().sort((a, b) => a - b);
    return sorted[Math.min(sorted.length - 1, Math.ceil(p * sorted.length) - 1)];
  }

  function runPacingTest(container) {
    if (state.benchmarkRunning) return;
    state.benchmarkRunning = true;
    const result = element("div", "hw-empty", "Тест выполняется: не переключай вкладку…");
    container.append(result);
    const durations = [];
    let previous = 0;
    const start = performance.now();
    const durationMs = 5000;
    function frame(now) {
      if (!previous) previous = now;
      durations.push(now - previous);
      previous = now;
      if (now - start < durationMs) {
        requestAnimationFrame(frame);
        return;
      }
      state.benchmarkRunning = false;
      const samples = durations.slice(1).filter((value) => value > 0 && value < 1000);
      const average = samples.reduce((sum, value) => sum + value, 0) / Math.max(1, samples.length);
      const fps = 1000 / average;
      result.replaceChildren(
        element("strong", "", "Browser frame pacing probe завершён"),
        element("p", "", "Средняя частота: " + fps.toFixed(1) + " кадров/с"),
        element("p", "", "Frame time: median " + percentile(samples, 0.5).toFixed(2) + " ms · p95 " + percentile(samples, 0.95).toFixed(2) + " ms · p99 " + percentile(samples, 0.99).toFixed(2) + " ms"),
        element("p", "", "Это нагрузка requestAnimationFrame текущей вкладки, не FPS игры. Для игрового процесса нужны ETW/PresentMon или vendor API.")
      );
    }
    requestAnimationFrame(frame);
  }

  function renderGameFrame(grid) {
    const box = card("Browser frame pacing", "Пятиисекундный тест измеряет тайминги requestAnimationFrame в этой вкладке. Он полезен как sanity check интерфейса, но не подменяет игровой benchmark.");
    const run = actionButton("Запустить измерение 5 секунд", () => runPacingTest(box), true);
    box.append(run);
    const profiles = card("Локальный профиль игры", "Сохраняется только в localStorage этого браузера. Параметры ОС, драйвера, частоты и напряжения не изменяются.");
    const name = document.createElement("input");
    name.id = "gameProfileName";
    name.placeholder = "Название игры";
    name.maxLength = 80;
    const preset = document.createElement("select");
    preset.id = "gameProfilePreset";
    [["balanced","Сбалансированный"],["competitive","Низкая задержка"],["quality","Качество изображения"]].forEach(([value,label]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      preset.append(option);
    });
    profiles.append(field("Игра", name), field("Цель профиля", preset));
    profiles.append(actionButton("Сохранить локальный профиль", () => {
      const title = name.value.trim();
      if (!title) return showToast("Укажи название игры.");
      let saved = [];
      try { saved = JSON.parse(localStorage.getItem("mora-game-profiles") || "[]"); } catch { saved = []; }
      const entry = {name:title, preset:preset.value, updated_at:new Date().toISOString()};
      saved = saved.filter((item) => item.name.toLocaleLowerCase() !== title.toLocaleLowerCase());
      saved.unshift(entry);
      localStorage.setItem("mora-game-profiles", JSON.stringify(saved.slice(0, 40)));
      showToast("Профиль сохранён локально. Системные настройки не менялись.");
      renderSavedProfiles(profiles);
    }, true));
    renderSavedProfiles(profiles);
    grid.append(box, profiles);
  }

  function renderSavedProfiles(container) {
    const existing = container.querySelector(".hw-profile-list");
    if (existing) existing.remove();
    let saved = [];
    try { saved = JSON.parse(localStorage.getItem("mora-game-profiles") || "[]"); } catch { saved = []; }
    if (!Array.isArray(saved) || !saved.length) return;
    const list = element("div", "hw-profile-list");
    list.append(element("h3", "", "Сохранённые профили"));
    saved.forEach((item) => list.append(element("p", "", item.name + " · " + item.preset + " · " + new Date(item.updated_at).toLocaleDateString())));
    container.append(list);
  }

  function renderDetail(app) {
    const grid = detailLayout(app);
    switch (app.id) {
      case "device-atlas": renderDeviceAtlas(grid); break;
      case "driver-capture": renderDriverCapture(grid); break;
      case "driver-scout": renderDriverScout(grid); break;
      case "driver-lab": renderDriverLab(grid); break;
      case "driver-graph": renderDriverGraph(grid); break;
      case "driver-restore": renderDriverRestore(grid); break;
      case "firmware-atlas": renderFirmwareAtlas(grid); break;
      case "uefi-guard": renderUefiGuard(grid); break;
      case "pcie-scope": renderPcieScope(grid); break;
      case "gpu-deck": renderGpuDeck(grid); break;
      case "cpu-lab": renderCpuLab(grid); break;
      case "memory-lens": renderMemoryLens(grid); break;
      case "storage-pulse": renderStoragePulse(grid); break;
      case "thermal-core": renderThermalCore(grid); break;
      case "gameframe": renderGameFrame(grid); break;
      default: grid.append(element("div", "hw-empty", "Модуль не зарегистрирован."));
    }
  }

  async function readJsonFile(file, maximumBytes) {
    if (!file || file.size > maximumBytes) throw new Error("Файл превышает допустимый размер.");
    return JSON.parse(await file.text());
  }

  $("#snapshotFile").addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    try {
      const report = await readJsonFile(file, 20 * 1024 * 1024);
      if (!report || report.schema !== "duckos.hardware-snapshot.v1") throw new Error("Ожидается схема duckos.hardware-snapshot.v1.");
      if (report.devices !== undefined && (!Array.isArray(report.devices) || report.devices.length > 10000)) throw new Error("Некорректный список устройств.");
      if (report.drivers !== undefined && (!Array.isArray(report.drivers) || report.drivers.length > 10000)) throw new Error("Некорректный список драйверов.");
      if (report.sensors !== undefined && (!Array.isArray(report.sensors) || report.sensors.length > 2048)) throw new Error("Некорректный список сенсоров.");
      state.snapshot = report;
      renderMetrics();
      renderModuleGrid();
      showToast("Аппаратный отчёт импортирован в текущую сессию.");
      if (state.selected !== "overview") openModule(state.selected);
    } catch (error) {
      showToast(error.message || "Не удалось прочитать отчёт.");
    }
  });

  $("#offersFile").addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    try {
      const report = await readJsonFile(file, 10 * 1024 * 1024);
      if (report?.schema !== "duckos.windows-update-driver-offers.v1" || !Array.isArray(report.updates) || report.updates.length > 1000) {
        throw new Error("Ожидается корректный список Windows Update driver offers.");
      }
      state.offers = report;
      showToast("Список обновлений импортирован. Установка не запускалась.");
      openModule("driver-scout");
    } catch (error) {
      showToast(error.message || "Не удалось прочитать список обновлений.");
    }
  });

  $("#infFile").addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    try {
      if (file.size > 2 * 1024 * 1024) throw new Error("INF превышает лимит 2 МиБ.");
      const content = await file.text();
      const sections = [...content.matchAll(/^\s*\[([^\]]+)\]\s*$/gm)].map((match) => match[1]).filter((name) => /models/i.test(name));
      const ids = [...new Set(content.match(/(?:PCI|USB|ACPI|HID|ROOT|SCSI|BTH)\\[A-Z0-9_&\\.-]+/gi) || [])].slice(0, 256);
      const architectures = [...new Set(sections.map((name) => {
        const match = name.match(/NT(?:amd64|arm64|x86|arm|ia64)/i);
        return match ? match[0] : "generic / undecorated";
      }))];
      const result = $("#infResults");
      result.replaceChildren(
        element("strong", "", "INF прочитан как текст"),
        element("p", "", "Model sections: " + (sections.length ? sections.join(", ") : "не найдены")),
        element("p", "", "Архитектурные decorations: " + (architectures.length ? architectures.join(", ") : "не указаны")),
        element("p", "", "Hardware IDs: " + ids.length),
        element("p", "", ids.length ? ids.join("\n") : "ID не извлечены")
      );
      showToast("INF разобран. Подпись пакета ещё не проверена.");
    } catch (error) {
      showToast(error.message || "Не удалось прочитать INF.");
    }
  });

  $("#importSnapshot").addEventListener("click", () => $("#snapshotFile").click());
  $("#importOffers").addEventListener("click", () => $("#offersFile").click());
  $("#exportReport").addEventListener("click", () => {
    const report = {
      schema: "duckos.mora-hardware-session.v1",
      exported_at: new Date().toISOString(),
      browser_observations: localFacts,
      imported_hardware_snapshot: state.snapshot,
      imported_windows_update_offers: state.offers,
      game_profiles: (() => { try { return JSON.parse(localStorage.getItem("mora-game-profiles") || "[]"); } catch { return []; } })(),
      note: "Browser observations are not a native hardware inventory. No device identifiers are uploaded."
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], {type:"application/json"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "mora-hardware-session.json";
    link.click();
    URL.revokeObjectURL(url);
  });
  $("#moduleSearch").addEventListener("input", renderModuleGrid);
  $("#backOverview").addEventListener("click", () => openModule("overview"));

  renderSideNavigation();
  renderModuleGrid();
  renderMetrics();
  enrichBrowserFacts();
  const initial = window.location.hash.replace(/^#/, "");
  openModule(byId(initial) ? initial : "overview");
})();