export const DEEP_TIME_EPOCH_YEARS = "86452654432564423644";
const MAX_DIGITS = 120;

export function parseEpochYears(value) {
  const source = typeof value === "bigint" ? value.toString() : String(value ?? "");
  if (!/^(0|[1-9][0-9]*)$/.test(source) || source.length > MAX_DIGITS) {
    throw new RangeError("Epoch years must be a non-negative integer with at most 120 digits.");
  }
  return BigInt(source);
}

export function createChronoStamp({
  epochYears,
  cycle = 0,
  cycleOffsetTicks = "0",
  source = "simulation"
} = {}) {
  const years = parseEpochYears(epochYears);
  const offset = parseEpochYears(cycleOffsetTicks);
  if (!Number.isSafeInteger(cycle) || cycle < 0) {
    throw new RangeError("Cycle must be a non-negative safe integer.");
  }
  if (!["simulation", "civil"].includes(source)) {
    throw new TypeError("Unsupported chrono source.");
  }

  return Object.freeze({
    schema: "duckos.chrono.v1",
    epochYears: years.toString(),
    cycle,
    cycleOffsetTicks: offset.toString(),
    source
  });
}

export function compareChronoStamps(left, right) {
  const a = createChronoStamp(left);
  const b = createChronoStamp(right);
  const aYears = BigInt(a.epochYears);
  const bYears = BigInt(b.epochYears);
  if (aYears !== bYears) return aYears < bYears ? -1 : 1;
  if (a.cycle !== b.cycle) return a.cycle < b.cycle ? -1 : 1;
  const aOffset = BigInt(a.cycleOffsetTicks);
  const bOffset = BigInt(b.cycleOffsetTicks);
  return aOffset === bOffset ? 0 : aOffset < bOffset ? -1 : 1;
}

export function formatEpochYears(value, locale = "ru") {
  const years = parseEpochYears(value);
  const language = locale === "uk" || locale === "uk-UA" ? "uk" : "ru";
  const grouped = new Intl.NumberFormat(language === "uk" ? "uk-UA" : "ru-RU", {
    maximumFractionDigits: 0
  }).format(years);
  return language === "uk" ? grouped + " років" : grouped + " лет";
}
