const DEFAULT_ENDPOINT = "http://127.0.0.1:47682";
const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost"]);

function makeElement(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function validEndpoint(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" &&
      LOOPBACK_HOSTS.has(url.hostname) &&
      url.port !== "" &&
      !url.username &&
      !url.password &&
      !url.search &&
      !url.hash &&
      url.pathname === "/";
  } catch {
    return false;
  }
}

function readArguments(value) {
  const lines = value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length > 128 || lines.some((line) => line.length > 2048 || line.includes("\0"))) {
    throw new Error("Допускается до 128 аргументов, не более 2048 символов каждый.");
  }
  return lines;
}

function appendOption(select, value, label, disabled = false) {
  const option = makeElement("option", "", label);
  option.value = value;
  option.disabled = disabled;
  select.append(option);
}

export function mountRuntimeManager(appWindow) {
  const root = appWindow && appWindow.querySelector("[data-runtime-manager]");
  if (!root || root.dataset.mounted === "true") return;
  root.dataset.mounted = "true";

  let endpoint = DEFAULT_ENDPOINT;
  let token = "";
  let connected = false;
  let runtimes = [];
  let applications = [];
  let virtualMachines = [];
  let activeProcesses = [];

  const panel = makeElement("div", "runtime-manager");
  const intro = makeElement(
    "p",
    "runtime-intro",
    "Локальный host-agent создаёт настоящие процессы через API операционной системы. На Windows PE запускается напрямую; на POSIX для PE нужен Wine. Для DOS нужен DOSBox, для гостевой Windows — QEMU."
  );

  const pairing = makeElement("section", "runtime-card");
  pairing.append(
    makeElement("h3", "", "1. Сопряжение с host-agent"),
    makeElement("p", "runtime-help", "Запустите команду duckos runtime bridge, затем вставьте выведенный pairing token. Токен не сохраняется в настройках и действует только пока открыто это окно Mora.")
  );

  const endpointLabel = makeElement("label", "runtime-field");
  endpointLabel.append(makeElement("span", "", "Loopback endpoint"));
  const endpointInput = makeElement("input", "runtime-input");
  endpointInput.type = "url";
  endpointInput.value = DEFAULT_ENDPOINT;
  endpointInput.autocomplete = "url";
  endpointInput.spellcheck = false;
  endpointLabel.append(endpointInput);

  const tokenLabel = makeElement("label", "runtime-field");
  tokenLabel.append(makeElement("span", "", "Pairing token"));
  const tokenInput = makeElement("input", "runtime-input");
  tokenInput.type = "password";
  tokenInput.autocomplete = "off";
  tokenInput.spellcheck = false;
  tokenLabel.append(tokenInput);

  const connectRow = makeElement("div", "runtime-actions");
  const connectButton = makeElement("button", "runtime-button runtime-primary", "Подключить");
  connectButton.type = "button";
  const disconnectButton = makeElement("button", "runtime-button", "Отключить");
  disconnectButton.type = "button";
  disconnectButton.disabled = true;
  connectRow.append(connectButton, disconnectButton);

  const connectionStatus = makeElement("p", "runtime-status", "Агент не подключён.");
  connectionStatus.setAttribute("role", "status");
  connectionStatus.setAttribute("aria-live", "polite");
  pairing.append(endpointLabel, tokenLabel, connectRow, connectionStatus);

  const runtimeCard = makeElement("section", "runtime-card");
  runtimeCard.append(
    makeElement("h3", "", "2. Обнаруженные исполнительные среды"),
    makeElement("p", "runtime-help", "Список формируется на хосте по фактически найденным программам. DuckOS не скачивает Wine, DOSBox или QEMU без отдельной установки.")
  );
  const runtimeList = makeElement("div", "runtime-list");
  runtimeList.append(makeElement("p", "runtime-muted", "Подключите агент, чтобы проверить среды."));
  runtimeCard.append(runtimeList);

  const importCard = makeElement("section", "runtime-card");
  importCard.append(
    makeElement("h3", "", "3. Импорт приложения или игры"),
    makeElement("p", "runtime-help", "Можно импортировать один .exe/.com, ZIP-пакет игры или папку через ZIP. Каждый файл сохраняется в приватном каталоге и сверяется по SHA-256 перед запуском.")
  );

  const fileLabel = makeElement("label", "runtime-field");
  fileLabel.append(makeElement("span", "", "Файл или ZIP-пакет"));
  const fileInput = makeElement("input", "runtime-input runtime-file");
  fileInput.type = "file";
  fileInput.accept = ".exe,.com,.zip";
  fileLabel.append(fileInput);

  const nameLabel = makeElement("label", "runtime-field");
  nameLabel.append(makeElement("span", "", "Имя в библиотеке (необязательно)"));
  const nameInput = makeElement("input", "runtime-input");
  nameInput.type = "text";
  nameInput.maxLength = 120;
  nameInput.placeholder = "Например, My Game";
  nameLabel.append(nameInput);

  const entryLabel = makeElement("label", "runtime-field");
  entryLabel.append(makeElement("span", "", "Entry point внутри ZIP (если EXE несколько)"));
  const entryInput = makeElement("input", "runtime-input");
  entryInput.type = "text";
  entryInput.maxLength = 1024;
  entryInput.placeholder = "Game/game.exe";
  entryInput.spellcheck = false;
  entryLabel.append(entryInput);

  const importButton = makeElement("button", "runtime-button runtime-primary", "Импортировать в библиотеку");
  importButton.type = "button";
  importButton.disabled = true;
  const importStatus = makeElement("p", "runtime-status", "");
  importStatus.setAttribute("role", "status");
  importCard.append(fileLabel, nameLabel, entryLabel, importButton, importStatus);

  const launchCard = makeElement("section", "runtime-card");
  launchCard.append(
    makeElement("h3", "", "4. Запуск приложения"),
    makeElement("p", "runtime-help", "Запускаются только импортированные приложения с проверенным манифестом. Каждая сессия требует явного подтверждения.")
  );

  const appLabel = makeElement("label", "runtime-field");
  appLabel.append(makeElement("span", "", "Установленное приложение"));
  const appSelect = makeElement("select", "runtime-select");
  appendOption(appSelect, "", "Нет импортированных приложений");
  appSelect.disabled = true;
  appLabel.append(appSelect);

  const adapterLabel = makeElement("label", "runtime-field");
  adapterLabel.append(makeElement("span", "", "Runtime"));
  const adapterSelect = makeElement("select", "runtime-select");
  appendOption(adapterSelect, "auto", "Автоматический выбор");
  adapterSelect.disabled = true;
  adapterLabel.append(adapterSelect);

  const argsLabel = makeElement("label", "runtime-field");
  argsLabel.append(makeElement("span", "", "Аргументы приложения — один аргумент на строку"));
  const argsInput = makeElement("textarea", "runtime-input runtime-arguments");
  argsInput.rows = 3;
  argsInput.placeholder = "--windowed\n-nointro";
  argsLabel.append(argsInput);

  const consentBox = makeElement("div", "runtime-consent");
  const hostConsentLabel = makeElement("label", "runtime-check");
  const hostConsent = makeElement("input");
  hostConsent.type = "checkbox";
  hostConsentLabel.append(hostConsent, makeElement("span", "", "Разрешить запуск без host sandbox. Приложение получит права текущего пользователя Windows/Linux."));

  const networkConsentLabel = makeElement("label", "runtime-check");
  const networkConsent = makeElement("input");
  networkConsent.type = "checkbox";
  networkConsentLabel.append(networkConsent, makeElement("span", "", "Разрешить сеть, когда выбранный sandbox способен управлять сетевым namespace. Это не блокирует сеть для прямого Windows-запуска."));

  consentBox.append(hostConsentLabel, networkConsentLabel);
  const launchButton = makeElement("button", "runtime-button runtime-primary", "Запустить приложение");
  launchButton.type = "button";
  launchButton.disabled = true;
  const launchStatus = makeElement("p", "runtime-status", "");
  launchStatus.setAttribute("role", "status");
  launchCard.append(appLabel, adapterLabel, argsLabel, consentBox, launchButton, launchStatus);

  const vmCard = makeElement("section", "runtime-card");
  vmCard.append(
    makeElement("h3", "", "5. Виртуальные машины"),
    makeElement("p", "runtime-help", "Добавление образа выполняется локально через CLI. Mora может показать зарегистрированные машины и запустить гостевую Windows в QEMU; по умолчанию диск стартует в snapshot-режиме, сеть выключена, GPU passthrough не настроен.")
  );
  const vmSelect = makeElement("select", "runtime-select");
  appendOption(vmSelect, "", "Нет зарегистрированных VM");
  vmSelect.disabled = true;
  const vmNetworkLabel = makeElement("label", "runtime-check");
  const vmNetwork = makeElement("input");
  vmNetwork.type = "checkbox";
  vmNetworkLabel.append(vmNetwork, makeElement("span", "", "Разрешить гостевой системе user-mode NAT"));
  const vmLaunch = makeElement("button", "runtime-button", "Запустить гостевую машину");
  vmLaunch.type = "button";
  vmLaunch.disabled = true;
  const vmStatus = makeElement("p", "runtime-status", "");
  vmStatus.setAttribute("role", "status");
  vmCard.append(vmSelect, vmNetworkLabel, vmLaunch, vmStatus);

  const processCard = makeElement("section", "runtime-card");
  const processHeading = makeElement("div", "runtime-heading-row");
  processHeading.append(makeElement("h3", "", "6. Управление процессами"));
  const refreshButton = makeElement("button", "runtime-button runtime-small", "Обновить");
  refreshButton.type = "button";
  processHeading.append(refreshButton);
  const processList = makeElement("div", "runtime-processes");
  processList.append(makeElement("p", "runtime-muted", "Пока нет запущенных процессов."));
  processCard.append(processHeading, processList);

  const graphicsNotice = makeElement(
    "p",
    "runtime-notice",
    "Графика: Windows native использует драйверы хоста. Wine может использовать DXVK для Direct3D 9/10/11 → Vulkan после отдельной установки проверенного архива. Direct3D 12 требует vkd3d-proton и пока не включён. QEMU сейчас использует виртуальную VGA без GPU passthrough."
  );

  panel.append(intro, pairing, runtimeCard, importCard, launchCard, vmCard, processCard, graphicsNotice);
  root.replaceChildren(panel);

  function setConnected(value) {
    connected = value;
    connectButton.disabled = value;
    disconnectButton.disabled = !value;
    tokenInput.disabled = value;
    endpointInput.disabled = value;
    importButton.disabled = !value;
    appSelect.disabled = !value || applications.length === 0;
    adapterSelect.disabled = !value;
    vmSelect.disabled = !value || virtualMachines.length === 0;
    vmLaunch.disabled = !value || virtualMachines.length === 0;
    refreshButton.disabled = !value;
    updateLaunchButton();
  }

  function updateLaunchButton() {
    launchButton.disabled = !connected || !appSelect.value;
  }

  async function api(path, options = {}) {
    if (!connected && path !== "/v1/capabilities") {
      throw new Error("Сначала подключите локальный runtime-agent.");
    }
    const headers = new Headers(options.headers || {});
    headers.set("Authorization", "Bearer " + token);
    if (options.body && typeof options.body === "string") {
      headers.set("Content-Type", "application/json");
    }
    const response = await fetch(endpoint + path, {
      ...options,
      headers,
      mode: "cors",
      credentials: "omit",
      cache: "no-store",
      redirect: "error"
    });
    const body = await response.text();
    let payload = {};
    if (body) {
      try {
        payload = JSON.parse(body);
      } catch {
        throw new Error("Runtime-agent вернул некорректный ответ.");
      }
    }
    if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
    return payload;
  }

  function renderRuntimes() {
    runtimeList.replaceChildren();
    adapterSelect.replaceChildren();
    appendOption(adapterSelect, "auto", "Автоматический выбор");
    for (const runtime of runtimes) {
      const line = makeElement("div", "runtime-runtime-row");
      line.append(
        makeElement("strong", "", runtime.name + " · " + (runtime.available ? "Доступна" : "Не установлена")),
        makeElement("p", "", runtime.description || ""),
        makeElement("p", "runtime-muted", "Графика: " + (runtime.graphics || "не указана"))
      );
      runtimeList.append(line);
      appendOption(adapterSelect, runtime.id, runtime.name + (runtime.available ? "" : " (не установлена)"), !runtime.available);
    }
  }

  function renderApps() {
    appSelect.replaceChildren();
    if (!applications.length) {
      appendOption(appSelect, "", "Импортируйте приложение");
      appSelect.disabled = true;
    } else {
      appendOption(appSelect, "", "Выберите приложение");
      for (const app of applications) {
        const details = app.status === "invalid"
          ? " · пакет повреждён"
          : " · " + app.format + " · " + app.architecture + " · " + app.trust_state;
        appendOption(appSelect, app.id, app.name + details, app.status === "invalid");
      }
      appSelect.disabled = false;
    }
    updateLaunchButton();
  }

  function renderVms() {
    vmSelect.replaceChildren();
    if (!virtualMachines.length) {
      appendOption(vmSelect, "", "Сначала зарегистрируйте VM через CLI");
      vmSelect.disabled = true;
      vmLaunch.disabled = true;
      return;
    }
    appendOption(vmSelect, "", "Выберите гостевую систему");
    for (const vm of virtualMachines) {
      appendOption(vmSelect, vm.name, vm.name + " · " + vm.disk_format + " · " +
        vm.memory_mb + " MiB RAM · " + vm.cpus + " vCPU", vm.status === "invalid");
    }
    vmSelect.disabled = false;
    vmLaunch.disabled = false;
  }

  function renderProcesses() {
    processList.replaceChildren();
    if (!activeProcesses.length) {
      processList.append(makeElement("p", "runtime-muted", "Управляемых процессов нет."));
      return;
    }
    for (const process of activeProcesses) {
      const row = makeElement("div", "runtime-process-row");
      const copy = makeElement("div", "runtime-process-copy");
      copy.append(
        makeElement("strong", "", process.name + " · PID " + process.host_pid),
        makeElement("p", "", process.runtime_id + " · " + process.state +
          (process.exit_code === null || process.exit_code === undefined ? "" : " · exit " + process.exit_code))
      );
      const stop = makeElement("button", "runtime-button runtime-small", "Остановить");
      stop.type = "button";
      stop.disabled = process.state !== "running";
      stop.addEventListener("click", async () => {
        stop.disabled = true;
        try {
          await api("/v1/processes/" + process.process_id + "/terminate", {method:"POST"});
          await refreshAll();
        } catch (error) {
          connectionStatus.textContent = error.message;
          stop.disabled = false;
        }
      });
      row.append(copy, stop);
      processList.append(row);
    }
  }

  async function refreshAll() {
    const [appResponse, processResponse, vmResponse] = await Promise.all([
      api("/v1/apps"), api("/v1/processes"), api("/v1/vms")
    ]);
    applications = Array.isArray(appResponse.apps) ? appResponse.apps : [];
    activeProcesses = Array.isArray(processResponse.processes) ? processResponse.processes : [];
    virtualMachines = Array.isArray(vmResponse.vms) ? vmResponse.vms : [];
    renderApps();
    renderProcesses();
    renderVms();
  }

  connectButton.addEventListener("click", async () => {
    if (!validEndpoint(endpointInput.value)) {
      connectionStatus.textContent = "Разрешён только HTTP endpoint на localhost или 127.0.0.1 с явным портом.";
      return;
    }
    if (!tokenInput.value.trim()) {
      connectionStatus.textContent = "Введите pairing token, который напечатал duckos runtime bridge.";
      return;
    }
    endpoint = endpointInput.value.replace(/\/$/, "");
    token = tokenInput.value.trim();
    connectionStatus.textContent = "Подключаюсь к локальному агенту…";
    connectButton.disabled = true;
    try {
      const capabilities = await api("/v1/capabilities");
      if (capabilities.protocol !== "duckos.runtime.v1" || !capabilities.host) {
        throw new Error("Неизвестный протокол native runtime-agent.");
      }
      runtimes = Array.isArray(capabilities.runtimes) ? capabilities.runtimes : [];
      renderRuntimes();
      setConnected(true);
      await refreshAll();
      connectionStatus.textContent = "Подключено: " + capabilities.host.os + " · " +
        capabilities.host.architecture + ". Агент работает от имени текущего пользователя.";
    } catch (error) {
      token = "";
      setConnected(false);
      connectionStatus.textContent = error.message;
      tokenInput.value = "";
    }
  });

  disconnectButton.addEventListener("click", () => {
    token = "";
    endpoint = DEFAULT_ENDPOINT;
    runtimes = [];
    applications = [];
    virtualMachines = [];
    activeProcesses = [];
    tokenInput.value = "";
    renderApps();
    renderVms();
    renderProcesses();
    runtimeList.replaceChildren(makeElement("p", "runtime-muted", "Подключите агент, чтобы проверить среды."));
    adapterSelect.replaceChildren();
    appendOption(adapterSelect, "auto", "Автоматический выбор");
    setConnected(false);
    connectionStatus.textContent = "Сопряжение завершено. Токен очищен из памяти.";
  });

  appSelect.addEventListener("change", updateLaunchButton);
  refreshButton.addEventListener("click", async () => {
    refreshButton.disabled = true;
    try {
      await refreshAll();
      connectionStatus.textContent = "Состояние runtime-agent обновлено.";
    } catch (error) {
      connectionStatus.textContent = error.message;
    } finally {
      refreshButton.disabled = false;
    }
  });

  importButton.addEventListener("click", async () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) {
      importStatus.textContent = "Сначала выберите EXE, COM или ZIP.";
      return;
    }
    if (file.size > 8 * 1024 * 1024 * 1024) {
      importStatus.textContent = "Файл больше лимита импорта 8 GiB.";
      return;
    }
    importButton.disabled = true;
    importStatus.textContent = "Передаю файл в приватное хранилище DuckOS…";
    const headers = {
      "Content-Type": "application/octet-stream",
      "X-DuckOS-Filename": encodeURIComponent(file.name)
    };
    if (entryInput.value.trim()) headers["X-DuckOS-Entrypoint"] = entryInput.value.trim();
    if (nameInput.value.trim()) headers["X-DuckOS-Name"] = nameInput.value.trim();
    try {
      const result = await api("/v1/apps/import", {method:"POST", headers, body:file});
      importStatus.textContent = "Импортировано: " + result.app.name + " · " +
        result.app.format + " · SHA-256-проверка будет выполнена при запуске.";
      fileInput.value = "";
      entryInput.value = "";
      nameInput.value = "";
      await refreshAll();
      appSelect.value = result.app.id;
      updateLaunchButton();
    } catch (error) {
      importStatus.textContent = error.message;
    } finally {
      importButton.disabled = !connected;
    }
  });

  launchButton.addEventListener("click", async () => {
    if (!appSelect.value) return;
    let args;
    try {
      args = readArguments(argsInput.value);
    } catch (error) {
      launchStatus.textContent = error.message;
      return;
    }
    const app = applications.find((item) => item.id === appSelect.value);
    if (!app) return;
    if (!window.confirm("Запустить «" + app.name + "» через host runtime?\n\nПакет будет повторно проверен по SHA-256. Приложение сможет выполнять действия в пределах выбранной политики хоста.")) {
      return;
    }
    launchButton.disabled = true;
    launchStatus.textContent = "Запускаю " + app.name + "…";
    try {
      const result = await api("/v1/launch", {
        method:"POST",
        body:JSON.stringify({
          app_id:app.id,
          runtime_id:adapterSelect.value || "auto",
          arguments:args,
          approved:true,
          allow_unisolated:hostConsent.checked,
          allow_network:networkConsent.checked
        })
      });
      launchStatus.textContent = "Процесс запущен · PID " + result.process.host_pid +
        " · " + result.process.runtime_id + " · " + result.process.isolation +
        " · сеть: " + result.process.network_policy;
      await refreshAll();
    } catch (error) {
      launchStatus.textContent = error.message;
    } finally {
      updateLaunchButton();
    }
  });

  vmLaunch.addEventListener("click", async () => {
    if (!vmSelect.value) return;
    if (!hostConsent.checked) {
      vmStatus.textContent = "QEMU host process пока не изолирован. Подтвердите запуск без host sandbox выше.";
      return;
    }
    if (!window.confirm("Запустить гостевую машину «" + vmSelect.value + "» в QEMU?\n\nПо умолчанию изменения на виртуальном диске будут временными, сеть выключена, GPU passthrough не настроен.")) return;
    vmLaunch.disabled = true;
    vmStatus.textContent = "Запускаю QEMU…";
    try {
      const result = await api("/v1/vms/" + encodeURIComponent(vmSelect.value) + "/launch", {
        method:"POST",
        body:JSON.stringify({
          approved:true,
          allow_unisolated:true,
          allow_network:vmNetwork.checked,
          persistent:false
        })
      });
      vmStatus.textContent = "VM запущена · PID " + result.process.host_pid +
        " · " + result.process.disk_policy + " · сеть: " + result.process.network_policy;
      await refreshAll();
    } catch (error) {
      vmStatus.textContent = error.message;
    } finally {
      vmLaunch.disabled = !connected || virtualMachines.length === 0;
    }
  });

  setConnected(false);
  return { disconnect() { token = ""; connected = false; } };
}
