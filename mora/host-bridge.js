const DEFAULT_ENDPOINT = "http://127.0.0.1:8765";
const TOKEN_KEY = "duckos.native-host-token";
const ALLOWED_HOSTS = new Set(["127.0.0.1", "localhost", "[::1]"]);

function browserSessionStorage() {
  try {
    return globalThis.sessionStorage;
  } catch {
    return null;
  }
}

export function normalizeHostEndpoint(value = DEFAULT_ENDPOINT) {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new TypeError("Адрес Native Host должен быть корректным URL.");
  }
  if (url.protocol !== "http:" || !ALLOWED_HOSTS.has(url.hostname) ||
      url.username || url.password || url.pathname !== "/" || url.search || url.hash) {
    throw new TypeError("Native Host разрешено подключать только по HTTP loopback адресу.");
  }
  return url.origin;
}

export function createNativeHostBridge({
  endpoint = DEFAULT_ENDPOINT,
  fetcher = globalThis.fetch,
  storage = browserSessionStorage()
} = {}) {
  const baseUrl = normalizeHostEndpoint(endpoint);
  if (typeof fetcher !== "function") {
    throw new TypeError("Fetch API недоступен.");
  }

  let token = "";
  let sequence = 0;

  function readToken() {
    try {
      return storage?.getItem(TOKEN_KEY) || "";
    } catch {
      return "";
    }
  }

  function writeToken(value) {
    try {
      storage?.setItem(TOKEN_KEY, value);
    } catch {
      // An in-memory connection is still possible when session storage is disabled.
    }
  }

  function clearToken() {
    try {
      storage?.removeItem(TOKEN_KEY);
    } catch {
      // Nothing else is needed when storage is unavailable.
    }
  }

  async function readJson(response) {
    let payload;
    try {
      payload = await response.json();
    } catch {
      throw new Error("Native Host вернул некорректный JSON.");
    }
    if (!response.ok) {
      throw new Error(payload.error || "Native Host: HTTP " + response.status);
    }
    return payload;
  }

  async function request(method, params = {}) {
    if (!token) {
      throw new Error("Сначала подключите Native Host.");
    }
    const response = await fetcher(baseUrl + "/v1/rpc", {
      method: "POST",
      mode: "cors",
      credentials: "omit",
      cache: "no-store",
      redirect: "error",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
      },
      body: JSON.stringify({
        id: ++sequence,
        method,
        params
      })
    });
    const payload = await readJson(response);
    if (payload.error) {
      throw new Error(payload.error.message || "Native Host отклонил запрос.");
    }
    if (!Object.prototype.hasOwnProperty.call(payload, "result")) {
      throw new Error("Native Host не вернул поле result.");
    }
    return payload.result;
  }

  async function connect(candidate = readToken()) {
    if (typeof candidate !== "string" || !/^[A-Za-z0-9_-]{32,128}$/.test(candidate)) {
      throw new TypeError("Токен Native Host имеет неверный формат.");
    }
    const health = await readJson(await fetcher(baseUrl + "/health", {
      method: "GET",
      mode: "cors",
      credentials: "omit",
      cache: "no-store",
      redirect: "error",
      headers: { "Accept": "application/json" }
    }));
    if (health.service !== "duckos-native-host" || health.status !== "ready") {
      throw new Error("Локальная служба DuckOS не подтвердила готовность.");
    }
    token = candidate;
    const host = await request("host.status");
    writeToken(candidate);
    return host;
  }

  function disconnect() {
    token = "";
    clearToken();
  }

  return {
    endpoint: baseUrl,
    connect,
    disconnect,
    request,
    isConnected: () => Boolean(token),
    hasSavedToken: () => Boolean(readToken())
  };
}

export function initNativeHostBridge({
  button = document.getElementById("native-host-connect"),
  status = document.getElementById("native-host-state"),
  dialog = document.getElementById("native-host-dialog"),
  output = document.getElementById("native-host-output"),
  commandSelect = document.getElementById("native-host-command")
} = {}) {
  const bridge = createNativeHostBridge();
  const setStatus = (message, state) => {
    if (status) {
      status.textContent = message;
      status.dataset.state = state;
    }
    if (button) {
      button.textContent = bridge.isConnected() ? "Native Host" : "Подключить Host";
      button.setAttribute("aria-pressed", String(bridge.isConnected()));
    }
  };
  const showResult = (value) => {
    if (output) {
      output.textContent = JSON.stringify(value, null, 2);
    }
  };

  if (!button) {
    return bridge;
  }

  button.addEventListener("click", async () => {
    if (bridge.isConnected()) {
      if (dialog && typeof dialog.showModal === "function") {
        dialog.showModal();
      } else {
        setStatus("Служба подключена", "connected");
      }
      return;
    }

    const savedToken = bridge.hasSavedToken();
    const token = savedToken ? null : window.prompt("Введите одноразово выданный токен DuckOS Native Host:");
    if (!savedToken && !token) {
      setStatus("Подключение отменено", "offline");
      return;
    }
    button.disabled = true;
    setStatus("Подключение…", "connecting");
    try {
      const host = await bridge.connect(token ? token.trim() : undefined);
      const backend = host.display_backend || "display не определён";
      const label = host.native_x11_compositor_installed
        ? "X11 compositor установлен"
        : "X11 compositor не найден";
      setStatus("Host: " + host.host + " · " + backend, "connected");
      showResult({ host, compositor: label });
      if (dialog && typeof dialog.showModal === "function") {
        dialog.showModal();
      }
    } catch (error) {
      bridge.disconnect();
      setStatus(error.message || "Не удалось подключить Native Host", "error");
    } finally {
      button.disabled = false;
    }
  });

  if (dialog) {
    dialog.addEventListener("click", async (event) => {
      const actionButton = event.target.closest("[data-native-host-action]");
      if (!actionButton) {
        return;
      }
      const action = actionButton.dataset.nativeHostAction;
      actionButton.disabled = true;
      try {
        let result;
        if (action === "status") {
          result = await bridge.request("host.status");
        } else if (action === "drivers") {
          result = await bridge.request("driver.inventory");
        } else if (action === "sessions") {
          result = await bridge.request("session.list");
        } else if (action === "reaper") {
          result = await bridge.request("reaper.status");
        } else if (action === "terminal") {
          const commandId = commandSelect?.value;
          const allowed = ["system", "date", "uptime", "memory", "storage", "processes", "network", "home"];
          if (!allowed.includes(commandId)) {
            throw new Error("Выберите разрешённую диагностическую команду.");
          }
          result = await bridge.request("terminal.run", { command_id: commandId });
        } else if (action === "disconnect") {
          bridge.disconnect();
          setStatus("Native Host отключён", "offline");
          dialog.close();
          return;
        } else {
          throw new Error("Неизвестное действие Native Host.");
        }
        showResult(result);
      } catch (error) {
        showResult({ error: error.message || "Ошибка Native Host" });
      } finally {
        actionButton.disabled = false;
      }
    });
  }

  setStatus("Native Host: offline", "offline");
  return bridge;
}
