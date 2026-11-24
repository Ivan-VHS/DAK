export const JORA_PARAMETER_REGISTRY = Object.freeze([
  { id: "text_editor", name: "Текстовый редактор", aliases: ["текст", "редактор текста", "text editor"], domain: "text", description: "Документы, сегменты и структурированный текст.", variants: ["plain text", "markdown", "субтитры", "многоязычный текст"] },
  { id: "audio_editor", name: "Аудиоредактор", aliases: ["аудио", "звук", "audio editor", "sound editor"], domain: "media", description: "Дорожки, маркеры, таймкоды и аудиосегменты.", variants: ["подкасты", "дубляж", "аудиоанализ"] },
  { id: "translator", name: "Переводчик", aliases: ["перевод", "локализация", "translator", "translation"], domain: "language", description: "Перевод сегментов, глоссарии и память переводов.", variants: ["глоссарий", "память переводов", "дубляжный перевод"] },
  { id: "subtitles", name: "Субтитры", aliases: ["captions", "srt", "vtt"], domain: "language", description: "Тайминг и экспорт субтитров.", variants: ["SRT", "WebVTT", "ASS/SSA"] },
  { id: "notes", name: "Заметки", aliases: ["notes", "memo"], domain: "productivity", description: "Быстрые записи, теги и ссылки.", variants: ["быстрые заметки", "дневник"] },
  { id: "task_board", name: "Доска задач", aliases: ["задачи", "канбан", "kanban", "todo"], domain: "productivity", description: "Задачи, статусы и приоритеты.", variants: ["канбан", "список задач"] },
  { id: "calendar", name: "Календарь", aliases: ["calendar", "schedule"], domain: "productivity", description: "События и временные планы.", variants: ["планировщик"] },
  { id: "offline_mode", name: "Офлайн-режим", aliases: ["офлайн", "без интернета", "offline"], domain: "runtime", conflicts: ["cloud_translation"], description: "Локальная работа без сети.", variants: ["локальное хранилище"] },
  { id: "cloud_translation", name: "Облачный перевод", aliases: ["cloud translation", "online translation"], domain: "language", conflicts: ["offline_mode"], description: "Удалённые переводческие адаптеры.", variants: ["API перевода"] }
]);

const MAX_FORMULA_LENGTH = 2048;
const MAX_COMPONENTS = 64;
const normalizeKey = (value) => String(value).toLocaleLowerCase("ru-RU")
  .replace(/ё/gu, "е").replace(/[^\\p{L}\\p{N}]+/gu, " ").trim();

const aliases = new Map();
for (const item of JORA_PARAMETER_REGISTRY) {
  for (const alias of [item.id, item.name, ...item.aliases]) aliases.set(normalizeKey(alias), item);
}

export function parseJoraFormula(formula) {
  if (typeof formula !== "string" || !formula.trim()) throw new Error("Введите хотя бы один параметр формулы.");
  if (formula.length > MAX_FORMULA_LENGTH) throw new Error("Формула превышает лимит 2 048 символов.");
  const normalized = formula.replace(/\\s+(?:и|and)\\s+/giu, "+");
  const tokens = normalized.split(/[+,;&]/u).map((item) => item.trim().replace(/^\\[|\\]$/gu, ""));
  if (tokens.length > MAX_COMPONENTS) throw new Error("Превышен предел в 64 компонента.");
  const seen = new Set();
  const components = tokens.map((token, index) => {
    let value = token;
    let role = index === 0 ? "primary" : "standard";
    const prefix = value.match(/^(основной|главный|primary|optional|фоновый)\\s*:\\s*(.+)$/iu);
    if (prefix) {
      role = ["основной", "главный", "primary"].includes(prefix[1].toLocaleLowerCase("ru-RU")) ? "primary" : "optional";
      value = prefix[2].trim();
    }
    const match = aliases.get(normalizeKey(value));
    if (!match) throw new Error("Неизвестный параметр: " + value);
    if (seen.has(match.id)) throw new Error("Параметр уже добавлен: " + match.name);
    seen.add(match.id);
    return { id: match.id, name: match.name, domain: match.domain, role, description: match.description };
  });
  for (const component of components) {
    const definition = JORA_PARAMETER_REGISTRY.find((item) => item.id === component.id);
    const conflicts = (definition.conflicts || []).filter((id) => seen.has(id));
    if (conflicts.length) throw new Error(component.name + " конфликтует с " + conflicts.join(", "));
  }
  return components;
}

const edge = (source, target, kind, layer = "functional") => ({ source, target, kind, layer });

export function buildJoraGraph(components) {
  if (!Array.isArray(components) || !components.length) throw new Error("Нельзя построить пустой граф.");
  const nodes = [
    { id: "reaper:core", kind: "coordinator", layer: "language", name: "Reaper core" },
    { id: "data:unified-project", kind: "data-hub", layer: "data", name: "Unified project model" },
    ...components.map((item) => ({ id: "component:" + item.id, kind: "component", layer: "functional", name: item.name, domain: item.domain }))
  ];
  const edges = [];
  const clusters = {};
  if (components.length <= 12) {
    for (const item of components) {
      edges.push(edge("component:" + item.id, "reaper:core", "register_component"));
      edges.push(edge("component:" + item.id, "data:unified-project", "bind_project_data", "data"));
    }
    for (let i = 0; i < components.length; i += 1) {
      for (let j = i + 1; j < components.length; j += 1) {
        if (components[i].domain === components[j].domain || components.length === 3) {
          edges.push(edge("component:" + components[i].id, "component:" + components[j].id, "domain_synergy"));
        }
      }
    }
  } else {
    for (const item of components) (clusters[item.domain] ||= []).push(item.id);
    for (const [domain, members] of Object.entries(clusters).sort(([a], [b]) => a.localeCompare(b))) {
      const gateway = "cluster:" + domain;
      nodes.push({ id: gateway, kind: "cluster-gateway", layer: "functional", name: domain + " gateway", memberCount: members.length });
      edges.push(edge(gateway, "reaper:core", "cluster_route"));
      for (const member of members) {
        edges.push(edge("component:" + member, gateway, "cluster_membership"));
        edges.push(edge("component:" + member, "data:unified-project", "bind_project_data", "data"));
      }
      for (let i = 0; i < members.length - 1; i += 1) {
        edges.push(edge("component:" + members[i], "component:" + members[i + 1], "local_domain_synergy"));
      }
    }
  }
  return {
    schema: "jora.formula-graph.v1",
    topology: components.length === 3 ? "dense-triad" : (components.length > 12 ? "clustered-hub" : "hub-and-spoke"),
    componentCount: components.length, nodes, edges, clusters,
    growthPolicy: { maxComponents: MAX_COMPONENTS, densePairwiseOnlyForBaseTriad: true, largeFormulaStrategy: "domain clusters, gateways and bounded local adjacency", edgeComplexity: "O(N) for N > 12" }
  };
}

const slugify = (value) => value.toLocaleLowerCase("en-US").replace(/[^a-z0-9]+/gu, "-").replace(/^-|-$/gu, "").slice(0, 56) || "jora-app";

function deriveIdentity(components) {
  const ids = new Set(components.map((item) => item.id));
  if (["text_editor", "audio_editor", "translator"].every((id) => ids.has(id))) {
    return { name: "Слововолна", slug: "slovovolna", alternatives: ["WordWave", "Голосослов"] };
  }
  const roots = components.slice(0, 3).map((item) => item.id.split("_")[0]);
  const labels = { text: "Text", audio: "Sound", translator: "Lingua", notes: "Note", task: "Task", calendar: "Time", subtitles: "Caption", offline: "Local", cloud: "Cloud" };
  const name = roots.map((root) => labels[root] || root[0].toUpperCase() + root.slice(1)).join("") + (components.length > 1 ? " Studio" : "");
  return { name: name.slice(0, 40), slug: slugify(roots.join("-")), alternatives: [name + " Studio", "Jora " + name] };
}

function selectJoraLanguages(components) {
  const ids = new Set(components.map((item) => item.id));
  const selected = [{ id: "reaper", name: "Reaper", status: "core", reason: "Основной язык приложения, композиции и координации модулей." }];
  if (["text_editor", "translator", "subtitles"].some((id) => ids.has(id))) {
    selected.push({ id: "python", name: "Python", status: "runtime-available", reason: "Текстовые и переводческие адаптеры на reference runtime DuckOS." });
  }
  if (ids.has("audio_editor")) {
    selected.push({ id: "rust", name: "Rust", status: "toolchain-check-required", reason: "Кандидат для DSP; наличие rustc проверяет CLI перед сборкой." });
  }
  return selected;
}

function createDemo(components) {
  const ids = new Set(components.map((item) => item.id));
  const ru = ["Добро пожаловать в проект.", "Текст, звук и смысл связаны в одном рабочем пространстве.", "Изменения сегмента отмечают связанные данные для проверки.", "Экспорт сохраняет структуру и временные связи."];
  const en = ["Welcome to the project.", "Text, sound and meaning share one workspace.", "Segment edits mark related data for review.", "Export preserves structure and timing links."];
  const segments = ru.map((text, index) => {
    const unit = { id: "seg_" + String(index + 1).padStart(3, "0"), status: "demo" };
    if (ids.has("text_editor")) unit.sourceText = text;
    if (ids.has("translator")) { unit.translatedText = en[index]; unit.translationStatus = "demo_not_reviewed"; }
    if (ids.has("audio_editor")) {
      unit.startMs = index * 2500; unit.endMs = (index + 1) * 2500;
      unit.audioRef = "audio.placeholder.segment_" + unit.id;
      unit.audioAssetStatus = "metadata_placeholder_no_audio_file";
    }
    return unit;
  });
  return { schema: "jora.demo-project.v1", name: "Утренний подкаст о языках и звуке", generatedContent: true, segments,
    glossary: ids.has("translator") ? [{ source: "timeline", target: "таймлайн" }, { source: "segment", target: "сегмент" }, { source: "workflow", target: "рабочий процесс" }] : [],
    assets: { audio: ids.has("audio_editor") ? "placeholder-metadata-only" : "not-requested", images: "not-generated" } };
}

function reaperSource(name, formula) {
  return "# Generated by Jora for DuckOS. Review before execution.\n" +
    "make app_name := " + JSON.stringify(name) + "\n" +
    "make formula := " + JSON.stringify(formula) + "\n" +
    'emit "Jora source package: " ++ app_name\n' +
    'emit "Formula: " ++ formula\n';
}

export function buildJoraPackage(formula, options = {}) {
  const components = parseJoraFormula(formula);
  const identity = deriveIdentity(components);
  const displayName = options.name || identity.name;
  const slug = options.name ? slugify(options.name) : identity.slug;
  if (!displayName.trim() || displayName.length > 64) throw new Error("Название должно содержать 1–64 символа.");
  const canonicalFormula = components.map((item) => item.name).join(" + ");
  const graph = buildJoraGraph(components);
  const languages = selectJoraLanguages(components);
  const demo = createDemo(components);
  const source = reaperSource(displayName, canonicalFormula);
  const manifest = {
    schema: "jora.app-draft.v1",
    app: { id: slug, displayName, alternativeNames: identity.alternatives, tagline: "Приложение, собранное из совместимых возможностей." },
    formula: { source: formula, canonical: canonicalFormula, components },
    runtime: { coreLanguage: "reaper", selectedLanguages: languages, targetProfile: "duckos-user-space-source-package" },
    graph: { topology: graph.topology, nodeCount: graph.nodes.length, edgeCount: graph.edges.length },
    content: { generated: true, audioPayloadIncluded: false },
    maturity: { sourceDraft: true, compiled: false, tested: false, published: false, installed: false }
  };
  return { displayName, slug, tagline: manifest.app.tagline, components, canonicalFormula, graph, languages, demo, manifest, reaperSource: source };
}
