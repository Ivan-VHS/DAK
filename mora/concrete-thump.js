export const CONCRETE_THUMP_STORAGE_KEY = "duckos.mora.concrete-thump.v2";
export const LEGACY_CONCRETE_THUMP_STORAGE_KEY = "duckos.mora.concrete-thump.v1";

export const CONCRETE_THUMP_LIMITS = Object.freeze({
  maxSamples: 8,
  maxSampleBytes: 25 * 1024 * 1024,
  maxTotalSampleBytes: 80 * 1024 * 1024
});

export const SEQUENCE_TRACKS = Object.freeze(["kick", "snare", "hat", "bass", "choir"]);

const DEFAULT_SEQUENCE = Object.freeze({
  kick:  [true, false, false, false, false, false, true, false, true, false, false, false, false, true, false, false],
  snare: [false, false, false, false, true, false, false, false, false, false, false, false, true, false, false, false],
  hat:   [true, false, true, false, true, false, true, false, true, false, true, false, true, false, true, false],
  bass:  [true, false, false, false, false, false, false, true, true, false, false, false, false, false, true, false],
  choir: [true, false, false, false, false, false, false, false, true, false, false, false, false, false, false, false]
});

export const CHANT_SOURCE_LABELS = Object.freeze({
  "znamenny": "Знаменный распев",
  "byzantine-slavic": "Византийско-славянский церковный распев",
  "kolyadky": "Колядки",
  "vesnyanky": "Веснянки",
  "kupala": "Купальские песни",
  "harvest": "Жатвенные и обжинковые песни",
  "wedding": "Свадебные песни",
  "funeral": "Похоронные и причитальные песни"
});

const ALLOWED_TRADITIONS = new Set([
  "orthodox-liturgical",
  "east-slavic-folk",
  "layered"
]);

const ALLOWED_TREATMENTS = new Set([
  "chopped-call-response",
  "long-choir-beds",
  "granular-fragments"
]);

const ALLOWED_RIGHTS = new Set([
  "unspecified",
  "user-owned",
  "public-domain",
  "licensed",
  "permission-granted"
]);

const AUDIO_EXTENSIONS = /\.(wav|wave|mp3|flac|ogg|oga|m4a|aac|aif|aiff|opus|webm)$/i;
const SOURCE_IDS = Object.keys(CHANT_SOURCE_LABELS);

export function createDefaultConcreteThumpProfile() {
  return {
    schema: "duckos.concrete-thump-profile.v2",
    bpm: 160,
    swing: 60,
    vocalTradition: "layered",
    chantSources: [
      "znamenny",
      "byzantine-slavic",
      "kolyadky",
      "vesnyanky",
      "kupala",
      "harvest",
      "wedding",
      "funeral"
    ],
    sampleTreatment: "chopped-call-response",
    samples: [],
    sequence: Object.fromEntries(SEQUENCE_TRACKS.map((track) => [track, [...DEFAULT_SEQUENCE[track]]]))
  };
}

function normalizeSampleMetadata(value) {
  if (!value || typeof value !== "object") return null;
  const name = typeof value.name === "string" ? value.name.trim().slice(0, 160) : "";
  if (!name) return null;

  const type = typeof value.type === "string" ? value.type.slice(0, 80) : "";
  const size = Number.isSafeInteger(value.size) && value.size >= 0 ? value.size : 0;
  const credit = typeof value.credit === "string" ? value.credit.trim().slice(0, 200) : "";
  const rights = ALLOWED_RIGHTS.has(value.rights) ? value.rights : "unspecified";

  return { name, type, size, credit, rights };
}

export function normalizeConcreteThumpProfile(value) {
  const defaults = createDefaultConcreteThumpProfile();
  const source = value && typeof value === "object" ? value : {};
  const bpm = Number.isInteger(source.bpm) && source.bpm >= 40 && source.bpm <= 240
    ? source.bpm
    : defaults.bpm;
  const swing = Number.isInteger(source.swing) && source.swing >= 50 && source.swing <= 75
    ? source.swing
    : defaults.swing;
  const chantSources = Array.isArray(source.chantSources)
    ? [...new Set(source.chantSources.filter((id) => SOURCE_IDS.includes(id)))].slice(0, SOURCE_IDS.length)
    : defaults.chantSources;

  const samples = Array.isArray(source.samples)
    ? source.samples.map(normalizeSampleMetadata).filter(Boolean).slice(0, CONCRETE_THUMP_LIMITS.maxSamples)
    : [];
  const sequenceSource = source.sequence && typeof source.sequence === "object" ? source.sequence : {};
  const sequence = Object.fromEntries(SEQUENCE_TRACKS.map((track) => {
    const savedSteps = sequenceSource[track];
    const fallback = DEFAULT_SEQUENCE[track];
    const steps = Array.isArray(savedSteps) && savedSteps.length === 16
      ? savedSteps.map((step) => step === true)
      : [...fallback];
    return [track, steps];
  }));

  return {
    schema: defaults.schema,
    bpm,
    swing,
    vocalTradition: ALLOWED_TRADITIONS.has(source.vocalTradition)
      ? source.vocalTradition
      : defaults.vocalTradition,
    chantSources,
    sampleTreatment: ALLOWED_TREATMENTS.has(source.sampleTreatment)
      ? source.sampleTreatment
      : defaults.sampleTreatment,
    samples,
    sequence
  };
}

function storageOrNull(storage) {
  if (storage) return storage;
  try {
    return globalThis.localStorage || null;
  } catch {
    return null;
  }
}

export function loadConcreteThumpProfile(storage) {
  const target = storageOrNull(storage);
  if (!target) return createDefaultConcreteThumpProfile();

  try {
    const current = target.getItem(CONCRETE_THUMP_STORAGE_KEY);
    if (current) return normalizeConcreteThumpProfile(JSON.parse(current));

    const legacy = target.getItem(LEGACY_CONCRETE_THUMP_STORAGE_KEY);
    if (legacy) return normalizeConcreteThumpProfile(JSON.parse(legacy));
  } catch {
    return createDefaultConcreteThumpProfile();
  }

  return createDefaultConcreteThumpProfile();
}

export function saveConcreteThumpProfile(value, storage) {
  const target = storageOrNull(storage);
  if (!target) return false;

  try {
    target.setItem(
      CONCRETE_THUMP_STORAGE_KEY,
      JSON.stringify(normalizeConcreteThumpProfile(value))
    );
    return true;
  } catch {
    return false;
  }
}

export function validateAudioSampleFile(file, { sampleCount = 0, totalBytes = 0 } = {}) {
  if (!file || typeof file.name !== "string" || !file.name.trim()) {
    return { ok: false, reason: "Выберите аудиофайл." };
  }

  if (sampleCount >= CONCRETE_THUMP_LIMITS.maxSamples) {
    return { ok: false, reason: "Можно добавить не более восьми сэмплов." };
  }

  const hasAudioMime = typeof file.type === "string" && /^audio\//i.test(file.type);
  if (!hasAudioMime && !AUDIO_EXTENSIONS.test(file.name)) {
    return { ok: false, reason: "Поддерживаются WAV, MP3, FLAC, OGG, M4A, AAC, AIFF, OPUS и WebM." };
  }

  if (!Number.isSafeInteger(file.size) || file.size <= 0) {
    return { ok: false, reason: "Файл пустой или имеет некорректный размер." };
  }

  if (file.size > CONCRETE_THUMP_LIMITS.maxSampleBytes) {
    return { ok: false, reason: "Размер одного сэмпла не должен превышать 25 МиБ." };
  }

  if (totalBytes + file.size > CONCRETE_THUMP_LIMITS.maxTotalSampleBytes) {
    return { ok: false, reason: "Общий размер импортированных сэмплов не должен превышать 80 МиБ." };
  }

  return { ok: true, reason: "" };
}

export function buildConcreteThumpPrompt(value) {
  const profile = normalizeConcreteThumpProfile(value);
  const promptNames = {
    "znamenny": "znamenny",
    "byzantine-slavic": "Byzantine-Slavic",
    "kolyadky": "Kolyadky",
    "vesnyanky": "Vesnyanky",
    "kupala": "Kupala",
    "harvest": "harvest",
    "wedding": "wedding",
    "funeral": "funeral"
  };
  const sourceNames = profile.chantSources.map((id) => promptNames[id]).filter(Boolean).join(", ");
  const identity = {
    "orthodox-liturgical": "Orthodox choir and sacred chant.",
    "east-slavic-folk": "East Slavic ritual folk choir and seasonal songs.",
    layered: "Orthodox choir and chant; East Slavic ritual songs."
  }[profile.vocalTradition];
  const treatment = {
    "chopped-call-response": "Chopped choir call-response, hypnotic loops.",
    "long-choir-beds": "Long choir beds, solemn refrains, selective chops.",
    "granular-fragments": "Granular chant fragments, evolving vocal loops."
  }[profile.sampleTreatment];
  const sourceLine = sourceNames ? "Sources: " + sourceNames + "." : "";
  const prompt = [
    "Heavyweight Modern Trap, " + profile.bpm + " BPM.",
    identity,
    sourceLine,
    "Sacred liturgy and folk ritual stay distinct; archaic polyphony, minor modes, solemn refrains.",
    treatment,
    "Thunderous 808s, hard kicks, sharp snares, rapid hi-hats, triplet bursts, " +
      profile.swing + "% MPC swing, aggressive double-time bounce, stutter edits, negative-space drops."
  ].filter(Boolean).join(" ").replace(/\\s+/g, " ").trim();

  return prompt.length <= 500 ? prompt : prompt.slice(0, 497).trimEnd() + "...";
}

export function createReaperGridSource(value) {
  const profile = normalizeConcreteThumpProfile(value);
  return [
    "# Generated by DuckOS Concrete Thump.",
    "# Calculates swung sixteenth-note offbeat markers; it does not process or play audio.",
    "make bpm := " + profile.bpm,
    "make swing_percent := " + profile.swing,
    "make sixteenth_ms := 60000 / bpm / 4",
    "make swing_delay_ms := sixteenth_ms * (swing_percent - 50) / 50",
    "",
    "craft offbeat_time(index) {",
    "    yield ((index * 2 + 1) * sixteenth_ms) + swing_delay_ms",
    "}",
    "",
    "make offbeat_markers := range(0, 8) :: map(offbeat_time)",
    'emit "BPM=" ++ text(bpm) ++ " swing=" ++ text(swing_percent)',
    "each marker in offbeat_markers {",
    '    emit "offbeat_ms=" ++ text(marker)',
    "}",
    ""
  ].join("\n");
}
