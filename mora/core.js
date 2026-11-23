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
      theme: "dark"
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
      theme: appearance.theme === "light" ? "light" : "dark"
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
  if (!file || typeof file.slice !== "function") throw new TypeError("Ожидался локальный файл.");
  const extension = typeof file.name === "string" && file.name.includes(".")
    ? file.name.split(".").pop().toLowerCase() : "";

  if (extension === "com" && file.size > 0 && file.size <= 0xff00) {
    return {valid:true,format:"DOS COM candidate",architecture:"x86 · 16-bit DOS",
      detail:"COM не имеет обязательной сигнатуры. Формат предполагается по расширению; запуск не выполнялся."};
  }
  if (file.size < 4) {
    return {valid:false,format:"Неизвестный",architecture:"Не определена",
      detail:"Файл слишком мал для проверки известных заголовков."};
  }

  const prefix = new Uint8Array(await file.slice(0,Math.min(file.size,64)).arrayBuffer());
  if (prefix[0] === 0x4d && prefix[1] === 0x5a) {
    if (prefix.length < 64) {
      return {valid:false,format:"DOS/PE",architecture:"Не определена",
        detail:"Заголовок MZ найден, но DOS-заголовок неполный."};
    }
    const dosView = new DataView(prefix.buffer,prefix.byteOffset,prefix.byteLength);
    const peOffset = dosView.getUint32(0x3c,true);
    if (peOffset >= 64 && peOffset <= file.size - 6) {
      const header = new Uint8Array(await file.slice(peOffset,Math.min(file.size,peOffset+256)).arrayBuffer());
      const signature = String.fromCharCode(...header.slice(0,4));
      if (signature === "PE\u0000\u0000" && header.length >= 24) {
        const view = new DataView(header.buffer,header.byteOffset,header.byteLength);
        const machine = view.getUint16(4,true);
        const optionalHeaderSize = view.getUint16(20,true);
        const optionalMagic = optionalHeaderSize >= 2 && header.length >= 26 ? view.getUint16(24,true) : 0;
        const architectures = {
          0x014c:"x86 · 32-bit",0x8664:"x86-64 · 64-bit",0xaa64:"ARM64",
          0x01c0:"ARM · 32-bit",0x01c4:"ARMv7 · 32-bit",0xa641:"ARM64EC",
          0x5032:"RISC-V 32",0x5064:"RISC-V 64"
        };
        let detail = "Заголовок PE распознан. Это только проверка формата и архитектуры; запуск не выполнялся.";
        if (optionalHeaderSize >= 70 && header.length >= 24 + 70) {
          const subsystem = view.getUint16(24+68,true);
          const names = {2:"GUI",3:"Console",10:"EFI application"};
          detail += " Подсистема: " + (names[subsystem] || "код " + subsystem) + ".";
        }
        return {valid:true,format:"Windows PE",
          architecture:(architectures[machine] || "Неизвестная архитектура (0x"+machine.toString(16)+")")+
            (optionalMagic===0x20b?" · PE32+":optionalMagic===0x10b?" · PE32":""),
          detail};
      }
      const legacy = signature.slice(0,2);
      if (["NE","LE","LX"].includes(legacy)) {
        return {valid:true,format:"Legacy "+legacy,architecture:"x86 · legacy",
          detail:"Обнаружен старый формат NE/LE/LX. Нужен подходящий DOS extender или гостевая среда; запуск не выполнялся."};
      }
    }
    return {valid:true,format:"DOS MZ candidate",architecture:"x86 · 16-bit DOS",
      detail:"Найден MZ-заголовок без подтверждённой PE-сигнатуры. Это может быть DOS-программа или нестандартный файл; запуск не выполнялся."};
  }

  if (prefix[0]===0x7f && prefix[1]===0x45 && prefix[2]===0x4c && prefix[3]===0x46) {
    const bytes = new Uint8Array(await file.slice(0,Math.min(file.size,20)).arrayBuffer());
    const littleEndian = bytes[5] !== 2;
    const machine = bytes.length >= 20 ? new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength).getUint16(18,littleEndian) : 0;
    const architectures = {3:"x86 · 32-bit",40:"ARM · 32-bit",62:"x86-64 · 64-bit",183:"ARM64",243:"RISC-V"};
    return {valid:true,format:"ELF",
      architecture:(bytes[4]===2?"64-bit · ":bytes[4]===1?"32-bit · ":"")+(architectures[machine]||"архитектура не определена"),
      detail:"Заголовок ELF распознан. Это не Windows PE; запуск не выполнялся."};
  }

  const magic = Array.from(prefix.slice(0,4),byte=>byte.toString(16).padStart(2,"0")).join("");
  const machO = {
    feedface:"Mach-O · 32-bit big-endian",feedfacf:"Mach-O · 64-bit big-endian",
    cefaedfe:"Mach-O · 32-bit little-endian",cffaedfe:"Mach-O · 64-bit little-endian",
    cafebabe:"Mach-O fat binary",bebafeca:"Mach-O fat binary"
  };
  if (machO[magic]) return {valid:true,format:"Mach-O",architecture:machO[magic],
    detail:"Распознан формат исполняемого файла Apple. Для запуска нужна совместимая macOS-среда; запуск не выполнялся."};

  return {valid:false,format:"Неизвестный",architecture:"Не определена",
    detail:"Сигнатуры PE, DOS MZ/COM, ELF или Mach-O не найдены."};
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
