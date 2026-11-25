const STORAGE_KEY = "duckos.mora.locale.v1";
const RTL_SCRIPTS = new Set(["Arab", "Hebr", "Thaa", "Nkoo", "Adlm", "Rohg", "Syrc"]);

async function loadCatalogs() {
  const response = await fetch(new URL("./i18n.v1.json", import.meta.url), { cache: "no-cache" });
  if (!response.ok) throw new Error("Mora locale catalog could not be loaded");
  const value = await response.json();
  if (value.schema !== "duck.mora-catalog/v1" || !value.locales?.en?.messages) {
    throw new Error("Mora locale catalog has an unsupported schema");
  }
  return value.locales;
}

const catalogs = await loadCatalogs();

function validTag(value) {
  if (typeof value !== "string" || !value.trim()) return null;
  try { return Intl.getCanonicalLocales(value)[0] ?? null; }
  catch { return null; }
}

function storedLocale() {
  try {
    const saved = validTag(localStorage.getItem(STORAGE_KEY));
    if (saved) return saved;
  } catch { /* Storage can be unavailable in restricted browser contexts. */ }
  for (const candidate of navigator.languages ?? []) {
    const tag = validTag(candidate);
    if (tag) return tag;
  }
  return "en";
}

export let currentLocale = storedLocale();

function catalogKey(tag) {
  const locale = new Intl.Locale(tag);
  const language = locale.language.toLowerCase();
  if (language === "zh" && locale.script === "Hans") return "zh-Hans";
  if (language === "zh" && locale.region && ["CN", "SG"].includes(locale.region)) return "zh-Hans";
  return Object.hasOwn(catalogs, language) ? language : "en";
}

export function getMoraDictionary() {
  const key = catalogKey(currentLocale);
  return catalogs[key]?.messages ?? catalogs.en.messages;
}

export function getMoraMessage(key, values = {}) {
  const messages = getMoraDictionary();
  let message = messages[key] ?? catalogs.en.messages[key] ?? key;
  for (const [name, value] of Object.entries(values)) {
    message = message.replaceAll("{" + name + "}", String(value));
  }
  return message;
}

export function getMoraDirection() {
  const locale = new Intl.Locale(currentLocale).maximize();
  return RTL_SCRIPTS.has(locale.script) ? "rtl" : "ltr";
}

export function formatMoraDate(value, options = {}) {
  return new Intl.DateTimeFormat(currentLocale, options).format(value);
}

export function formatMoraNumber(value, options = {}) {
  return new Intl.NumberFormat(currentLocale, options).format(value);
}

export function setMoraLocale(value) {
  const tag = validTag(value);
  if (!tag) return false;
  try { localStorage.setItem(STORAGE_KEY, tag); }
  catch { return false; }
  currentLocale = tag;
  document.documentElement.lang = tag;
  document.documentElement.dir = getMoraDirection();
  return true;
}
