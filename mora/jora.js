const COMPONENTS = Object.freeze({
  "text.editor": {
    name: "Text Editor",
    label: "Текстовый редактор",
  },
  "audio.editor": {
    name: "Audio Editor",
    label: "Аудиоредактор",
  },
  "translation.workspace": {
    name: "Translator",
    label: "Переводчик",
  }
});

const LOCALES = new Set(["en", "ru", "uk", "most"]);
const EXTRA_TARGETS = new Set(["java", "kotlin", "python", "typescript", "rust", "c"]);
const NAME_STYLES = new Set(["compact", "balanced", "descriptive", "formula"]);
const GRAPH_TOPOLOGIES = Object.freeze({
  auto: "Автоматический подбор",
  layered: "Многослойная композиция",
  pipeline: "Последовательный процесс",
  hub_spoke: "Общий координатор",
  plugin_mesh: "Сеть возможностей",
  event_driven: "Событийная архитектура",
  hybrid: "Гибридная архитектура"
});

function safeText(value, maximum, field) {
  if (typeof value !== "string") {
    throw new TypeError(field + " must be text");
  }
  const normalized = value.trim();
  if (normalized.length > maximum) {
    throw new RangeError(field + " exceeds " + maximum + " characters");
  }
  return normalized;
}

export function composeJoraRequest(options = {}) {
  const componentIds = options.components;
  const localeIds = options.locales;

  if (!Array.isArray(componentIds) || componentIds.length < 1 || componentIds.length > 24) {
    throw new TypeError("Select between 1 and 24 application components.");
  }
  const uniqueComponents = new Set();
  for (const id of componentIds) {
    if (typeof id !== "string" || !Object.hasOwn(COMPONENTS, id)) {
      throw new TypeError("Unknown Jora component: " + String(id));
    }
    if (uniqueComponents.has(id)) {
      throw new TypeError("Duplicate Jora component: " + id);
    }
    uniqueComponents.add(id);
  }

  if (!Array.isArray(localeIds) || localeIds.length < 1 || localeIds.length > 8) {
    throw new TypeError("Select at least one interface language.");
  }
  const uniqueLocales = new Set();
  for (const locale of localeIds) {
    if (!LOCALES.has(locale)) {
      throw new TypeError("Unsupported interface language: " + String(locale));
    }
    if (uniqueLocales.has(locale)) {
      throw new TypeError("Duplicate interface language: " + locale);
    }
    uniqueLocales.add(locale);
  }

  const preferredLocale = safeText(options.preferredLocale || localeIds[0], 16, "preferred locale");
  if (!uniqueLocales.has(preferredLocale)) {
    throw new TypeError("The primary language must be among selected interface languages.");
  }

  const requestedTargets = options.languageTargets || [];
  if (!Array.isArray(requestedTargets)) {
    throw new TypeError("Additional implementation targets must be a list.");
  }
  const uniqueTargets = new Set();
  for (const target of requestedTargets) {
    if (!EXTRA_TARGETS.has(target)) {
      throw new TypeError("Unsupported additional language target: " + String(target));
    }
    if (uniqueTargets.has(target)) {
      throw new TypeError("Duplicate additional language target: " + target);
    }
    uniqueTargets.add(target);
  }

  const requestedName = safeText(options.name || "Jora", 80, "application name");
  if (requestedName && requestedName !== "Jora") {
    throw new TypeError("Jora is the fixed application name for every composition.");
  }
  const nameStyle = options.nameStyle || "balanced";
  if (!NAME_STYLES.has(nameStyle)) {
    throw new TypeError("Unsupported Jora naming style: " + String(nameStyle));
  }

  const graphTopology = options.graphTopology || "auto";
  if (!Object.hasOwn(GRAPH_TOPOLOGIES, graphTopology)) {
    throw new TypeError("Unsupported Jora graph topology: " + String(graphTopology));
  }
  const graphVariants = options.graphVariants === undefined ? 4 : options.graphVariants;
  const graphVariation = options.graphVariation === undefined ? 50 : options.graphVariation;
  if (!Number.isInteger(graphVariants) || graphVariants < 1 || graphVariants > 6) {
    throw new RangeError("Jora graph variants must be from 1 to 6.");
  }
  if (!Number.isInteger(graphVariation) || graphVariation < 0 || graphVariation > 100) {
    throw new RangeError("Jora graph variation must be from 0 to 100.");
  }
  const graphSeed = safeText(options.graphSeed || "", 64, "graph seed");
  const description = safeText(options.description || "", 500, "application description");

  const formula = componentIds.map((id) => COMPONENTS[id].name).join(" + ");
  const domainOrder = ["Documents", "Audio", "Languages"];
  const domains = [...new Set(componentIds.map((id) => ({
    "text.editor": "Documents",
    "audio.editor": "Audio",
    "translation.workspace": "Languages"
  })[id]))].sort((left, right) => domainOrder.indexOf(left) - domainOrder.indexOf(right));
  const descriptors = domains;
  const joined = descriptors.join(" · ");
  const natural = descriptors.join(" & ");
  const nameSuggestions = [
    "Jora · " + joined,
    "Jora — " + natural + " Workspace",
    "Jora | Workspace for " + natural,
    "Jora — " + descriptors.join(" + ")
  ];

  const graph = {
    topology: graphTopology,
    seed: graphSeed,
    variants: graphVariants,
    variation: graphVariation
  };
  const request = {
    schema: "reaper.jora.request.v1",
    name: "Jora",
    description,
    name_style: nameStyle,
    components: [...componentIds],
    locales: [...localeIds],
    preferred_locale: preferredLocale,
    syntax_mode: "flow",
    language_targets: uniqueTargets.size ? ["reaper", ...uniqueTargets] : "auto",
    graph
  };

  return Object.freeze({
    name: "Jora",
    formula,
    request,
    nameStyle,
    nameSuggestions,
    graphPlan: {
      topology: graphTopology,
      topologyLabel: GRAPH_TOPOLOGIES[graphTopology],
      variants: graphVariants,
      variation: graphVariation,
      seed: graphSeed || "auto",
      availableTopologies: Object.entries(GRAPH_TOPOLOGIES).filter(([id]) => id !== "auto")
        .map(([id, label]) => ({ id, label }))
    },
    target: "Reaper .rpr scaffold",
    languageTargets: ["reaper", ...uniqueTargets],
    pendingTargets: [...uniqueTargets],
    generatedLocales: [...localeIds]
  });
}
