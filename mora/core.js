export const PREFERENCES_KEY = "duckos.mora.preferences.v1";
export const RECOVERY_KEY = "duckos.mora.recovery.v1";

export const APP_IDS = Object.freeze([
  "cockos", "kavun", "kabon", "gloverty", "po", "illidia", "unify",
  "mora-ai", "security", "updates", "runtime", "workspace", "provenance"
]);

const CAPABILITIES = ["microphone", "camera", "location", "files", "network", "clipboard"];
const POWER_PROFILES = ["saver", "balanced", "performance"];

export function createDefaultPreferences() {
  return {
    version: 1,
    appearance: {
      reducedMotion: false,
      density: "comfortable",
      theme: "amber"
    },
    focusMode: false,
    powerProfile: "balanced",
    permissions: Object.fromEntries(CAPABILITIES.map((name) => [name, false]))
  };
}

export function normalizePreferences(value) {
  const defaults = createDefaultPreferences();
  const source = value && typeof value === "object" ? value : {};
  const appearance = source.appearance && typeof source.appearance === "object"
    ? source.appearance
    : {};
  const permissions = source.permissions && typeof source.permissions === "object"
    ? source.permissions
    : {};

  return {
    version: 1,
    appearance: {
      reducedMotion: appearance.reducedMotion === true,
      density: appearance.density === "compact" ? "compact" : defaults.appearance.density,
      theme: ["amber", "dark", "light"].includes(appearance.theme) ? appearance.theme : defaults.appearance.theme
    },
    focusMode: source.focusMode === true,
    powerProfile: POWER_PROFILES.includes(source.powerProfile)
      ? source.powerProfile
      : defaults.powerProfile,
    permissions: Object.fromEntries(
      CAPABILITIES.map((name) => [name, permissions[name] === true])
    )
  };
}

function getStorage(storage) {
  if (storage) return storage;
  try {
    return globalThis.localStorage;
  } catch {
    return null;
  }
}

export function loadPreferences(storage) {
  const target = getStorage(storage);
  if (!target) return createDefaultPreferences();

  try {
    const saved = target.getItem(PREFERENCES_KEY);
    return saved ? normalizePreferences(JSON.parse(saved)) : createDefaultPreferences();
  } catch {
    return createDefaultPreferences();
  }
}

export function savePreferences(value, storage) {
  const target = getStorage(storage);
  if (!target) return false;

  try {
    target.setItem(PREFERENCES_KEY, JSON.stringify(normalizePreferences(value)));
    return true;
  } catch {
    return false;
  }
}

const APP_ALIASES = [
  { id: "cockos", pattern: /cockos/i },
  { id: "kavun", pattern: /kavun/i },
  { id: "kabon", pattern: /ka.?bon|кабон/i },
  { id: "gloverty", pattern: /gloverty/i },
  { id: "po", pattern: /(?:^|\s)po(?:$|\s)/i },
  { id: "illidia", pattern: /illidia/i },
  { id: "unify", pattern: /unify/i },
  { id: "mora-ai", pattern: /mora\s*ai|помощник|агент/i },
  { id: "security", pattern: /sentinel|безопасност/i },
  { id: "updates", pattern: /restore|обновлен|восстановлен/i },
  { id: "runtime", pattern: /bridge|совместим|runtime|\.exe/i },
  { id: "workspace", pattern: /control|настройк|системн/i },
  { id: "provenance", pattern: /proof|подлин|происхожд|провер.*файл/i }
];

export function buildIntentPlan(rawInput) {
  const input = String(rawInput ?? "").trim();
  if (!input) {
    return { ok: false, message: "Напишите, что нужно сделать." };
  }
  if (input.length > 320) {
    return { ok: false, message: "Запрос слишком длинный. Ограничьте его 320 символами." };
  }

  const text = input.toLocaleLowerCase("ru-RU");
  const actions = [];

  if (/(включи|активируй|запусти).{0,24}(фокус|не беспокоить)|режим фокуса/u.test(text)) {
    actions.push({
      type: "set",
      setting: "focusMode",
      value: true,
      label: "Включить режим фокуса"
    });
  } else if (/(выключи|отключи).{0,24}(фокус|не беспокоить)/u.test(text)) {
    actions.push({
      type: "set",
      setting: "focusMode",
      value: false,
      label: "Выключить режим фокуса"
    });
  }

  if (/(эконом|энергосбереж|меньше энергии|бережн.*питани)/u.test(text)) {
    actions.push({
      type: "set",
      setting: "powerProfile",
      value: "saver",
      label: "Выбрать профиль экономии энергии"
    });
  } else if (/(сбалансирован.*режим|обычн.*профиль)/u.test(text)) {
    actions.push({
      type: "set",
      setting: "powerProfile",
      value: "balanced",
      label: "Выбрать сбалансированный профиль"
    });
  } else if (/(максимальн.*производительност|профиль производительност)/u.test(text)) {
    actions.push({
      type: "set",
      setting: "powerProfile",
      value: "performance",
      label: "Выбрать профиль производительности"
    });
  }

  if (/(уменьш|сниз|отключ|без).{0,24}анимац/u.test(text)) {
    actions.push({
      type: "set",
      setting: "reducedMotion",
      value: true,
      label: "Снизить движение интерфейса"
    });
  } else if (/(обычн|включ).{0,24}анимац/u.test(text)) {
    actions.push({
      type: "set",
      setting: "reducedMotion",
      value: false,
      label: "Вернуть обычную анимацию"
    });
  }

  const openMatch = text.match(/(?:открой|запусти|перейди в)\s+(.+)/u);
  if (openMatch) {
    const destination = APP_ALIASES.find((entry) => entry.pattern.test(openMatch[1]));
    if (destination) {
      actions.push({
        type: "open-app",
        appId: destination.id,
        label: "Открыть " + destination.id
      });
    }
  }

  if (actions.length === 0) {
    return {
      ok: false,
      message: "Для этого запроса нет безопасного локального сценария. Команды оболочки, запуск процессов и изменение системных файлов агент не выполняет."
    };
  }

  return {
    ok: true,
    summary: "План содержит " + actions.length + " действие(й). Ничего не изменится до вашего подтверждения.",
    actions
  };
}

export async function inspectExecutable(file) {
  if (!file || typeof file.slice !== "function") {
    throw new TypeError("Ожидался локальный файл.");
  }
  if (file.size < 4) {
    return { valid: false, format: "Неизвестный", architecture: "Не определена", detail: "Файл слишком мал для проверки заголовка." };
  }

  const bytes = new Uint8Array(await file.slice(0, Math.min(file.size, 1024 * 1024)).arrayBuffer());

  if (bytes[0] === 0x4d && bytes[1] === 0x5a) {
    if (bytes.length < 64) {
      return { valid: false, format: "DOS/PE", architecture: "Не определена", detail: "Заголовок MZ найден, но DOS-заголовок неполный." };
    }

    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const peOffset = view.getUint32(0x3c, true);
    if (peOffset + 6 > bytes.length ||
        bytes[peOffset] !== 0x50 || bytes[peOffset + 1] !== 0x45 ||
        bytes[peOffset + 2] !== 0 || bytes[peOffset + 3] !== 0) {
      return { valid: false, format: "DOS/PE", architecture: "Не определена", detail: "MZ найден, но корректная сигнатура PE не обнаружена в проверенной области." };
    }

    const machine = view.getUint16(peOffset + 4, true);
    const architectures = {
      0x014c: "x86 · 32-bit",
      0x8664: "x86-64 · 64-bit",
      0xaa64: "ARM64",
      0x01c4: "ARM · 32-bit"
    };

    return {
      valid: true,
      format: "Windows PE",
      architecture: architectures[machine] || "Неизвестная архитектура (0x" + machine.toString(16) + ")",
      detail: "Заголовок PE распознан. Это только проверка формата и архитектуры; запуск не выполнялся."
    };
  }

  if (bytes[0] === 0x7f && bytes[1] === 0x45 && bytes[2] === 0x4c && bytes[3] === 0x46) {
    return {
      valid: true,
      format: "ELF",
      architecture: bytes[4] === 2 ? "64-bit ELF" : bytes[4] === 1 ? "32-bit ELF" : "Неизвестный класс ELF",
      detail: "Заголовок ELF распознан. Это только проверка формата; запуск не выполнялся."
    };
  }

  return {
    valid: false,
    format: "Неизвестный",
    architecture: "Не определена",
    detail: "Сигнатура PE или ELF не найдена."
  };
}

export async function hashFile(file) {
  if (!file || typeof file.arrayBuffer !== "function") {
    throw new TypeError("Ожидался локальный файл.");
  }
  if (file.size > 100 * 1024 * 1024) {
    throw new RangeError("Для локальной проверки поддерживаются файлы до 100 МБ.");
  }
  const cryptoApi = globalThis.crypto;
  if (!cryptoApi || !cryptoApi.subtle) {
    throw new Error("Web Crypto недоступен в этом контексте. Откройте оболочку в защищённом контексте браузера.");
  }

  const digest = await cryptoApi.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function createRecoverySnapshot(preferences, createdAt = new Date().toISOString()) {
  return {
    schemaVersion: 1,
    createdAt,
    preferences: normalizePreferences(preferences)
  };
}

export function validateRecoverySnapshot(value) {
  if (!value || typeof value !== "object" || value.schemaVersion !== 1 ||
      typeof value.createdAt !== "string" || !value.preferences ||
      typeof value.preferences !== "object") {
    return null;
  }
  return createRecoverySnapshot(value.preferences, value.createdAt);
}
