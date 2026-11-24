export const COMPONENTS = Object.freeze({
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
    description: "Перевод, терминология и параллельные тексты.",
    domain: "language",
  },
  "subtitle.editor": { name: "Subtitle Editor", label: "Редактор субтитров", description: "Тайминг, проверка и экспорт SRT/WebVTT/ASS.", domain: "language" },
  "notes.workspace": { name: "Notes Workspace", label: "Заметки и связи", description: "Связанные заметки, теги, ссылки и аннотации.", domain: "productivity" },
  "task.board": { name: "Task Board", label: "Доска задач", description: "Задачи, статусы, приоритеты и очереди проекта.", domain: "productivity" },
  "calendar.scheduler": { name: "Calendar Scheduler", label: "Календарь и расписание", description: "События, дедлайны, расписания и напоминания.", domain: "productivity" },
  "speech.synthesis": { name: "Speech Synthesis", label: "Синтез речи", description: "Озвучка текста, голосовые профили и речевые ресурсы.", domain: "audio" },
  "speech.recognition": { name: "Speech Recognition", label: "Распознавание речи", description: "Транскрибация, распознавание и разделение спикеров.", domain: "audio" },
  "code.editor": { name: "Code Editor", label: "Редактор кода", description: "Исходники, диагностика, структура и поиск по проекту.", domain: "development" },
  "spreadsheet.editor": { name: "Spreadsheet Editor", label: "Таблицы", description: "Табличные данные, формулы, сортировка и преобразования.", domain: "data" },
  "image.editor": { name: "Image Editor", label: "Редактор изображений", description: "Изображения, слои, маски и экспорт графики.", domain: "visual" },
  "video.editor": { name: "Video Editor", label: "Видеоредактор", description: "Видеоклипы, монтажные последовательности и рендер.", domain: "video" },
  "presentation.editor": { name: "Presentation Editor", label: "Презентации", description: "Слайды, заметки докладчика, макеты и экспорт.", domain: "documents" },
  "file.manager": { name: "File Manager", label: "Файловый менеджер", description: "Файлы, метаданные, избранные каталоги и навигация.", domain: "system" },
  "api.client": { name: "API Client", label: "API-клиент", description: "HTTP API, запросы, схемы ответов и коллекции.", domain: "network" },
  "automation.engine": { name: "Automation Engine", label: "Автоматизация", description: "Триггеры, правила, события и автоматические действия.", domain: "automation" },
  "data.visualizer": { name: "Data Visualizer", label: "Визуализация данных", description: "Графики, агрегаты, панели и интерактивные данные.", domain: "analytics" },
  "database.manager": { name: "Database Manager", label: "Менеджер баз данных", description: "Схемы, запросы, миграции и просмотр записей.", domain: "data" },
  "archive.manager": { name: "Archive Manager", label: "Архиватор", description: "Просмотр, распаковка, упаковка и проверка архивов.", domain: "system" },
  "knowledge.graph": { name: "Knowledge Graph", label: "Граф знаний", description: "Сущности, отношения, обратные ссылки и семантический поиск.", domain: "knowledge" },
});

const LOCALES = new Set(["en", "ru", "uk", "most"]);
const EXTRA_TARGETS = new Set(["java", "kotlin", "python", "typescript", "rust", "c"]);
const NAME_STYLES = new Set(["compact", "balanced", "descriptive", "formula"]);
const GRAPH_OBJECTIVES = Object.freeze({
  balanced: "Сбалансированность",
  low_latency: "Минимальная задержка",
  modularity: "Модульность",
  extensibility: "Расширяемость",
  minimal_complexity: "Минимальная сложность"
});
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
  const graphObjective = options.graphObjective || "balanced";
  if (!Object.hasOwn(GRAPH_OBJECTIVES, graphObjective)) {
    throw new TypeError("Unsupported Jora graph objective: " + String(graphObjective));
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
  const namingTerms = {
    "text.editor": { short: "Docs", domain: "Documents", action: "Writing", formula: "Text" },
    "audio.editor": { short: "Audio", domain: "Media", action: "Audio Editing", formula: "Audio" },
    "translation.workspace": { short: "Translate", domain: "Languages", action: "Translation", formula: "Translation" },
    "subtitle.editor": { short: "Captions", domain: "Languages", action: "Subtitle Editing", formula: "Subtitles" },
    "notes.workspace": { short: "Notes", domain: "Productivity", action: "Note Taking", formula: "Notes" },
    "task.board": { short: "Tasks", domain: "Productivity", action: "Task Management", formula: "Tasks" },
    "calendar.scheduler": { short: "Calendar", domain: "Productivity", action: "Scheduling", formula: "Calendar" },
    "speech.synthesis": { short: "Voice", domain: "Audio", action: "Speech Synthesis", formula: "Voice" },
    "speech.recognition": { short: "Speech", domain: "Audio", action: "Speech Recognition", formula: "Transcription" },
    "code.editor": { short: "Code", domain: "Development", action: "Code Editing", formula: "Code" },
    "spreadsheet.editor": { short: "Sheets", domain: "Data", action: "Spreadsheet Editing", formula: "Sheets" },
    "image.editor": { short: "Images", domain: "Visual", action: "Image Editing", formula: "Images" },
    "video.editor": { short: "Video", domain: "Media", action: "Video Editing", formula: "Video" },
    "presentation.editor": { short: "Slides", domain: "Documents", action: "Presentation Design", formula: "Slides" },
    "file.manager": { short: "Files", domain: "System", action: "File Management", formula: "Files" },
    "api.client": { short: "API", domain: "Development", action: "API Integration", formula: "API" },
    "automation.engine": { short: "Flow", domain: "Automation", action: "Workflow Automation", formula: "Automation" },
    "data.visualizer": { short: "Charts", domain: "Analytics", action: "Data Visualization", formula: "Charts" },
    "database.manager": { short: "Database", domain: "Data", action: "Database Management", formula: "Database" },
    "archive.manager": { short: "Archive", domain: "System", action: "Archive Management", formula: "Archive" },
    "knowledge.graph": { short: "Knowledge", domain: "Knowledge", action: "Knowledge Mapping", formula: "Knowledge" }
  };
  const unique = (values) => [...new Set(values)];
  const joinNatural = (values) => values.length <= 1
    ? (values[0] || "Workspace")
    : values.length === 2
      ? values[0] + " & " + values[1]
      : values.slice(0, -1).join(", ") + " & " + values[values.length - 1];
  const shortTerms = unique(componentIds.map((id) => namingTerms[id].short));
  const descriptors = unique(componentIds.map((id) => namingTerms[id].domain));
  const actionTerms = unique(componentIds.map((id) => namingTerms[id].action));
  const formulaTerms = unique(componentIds.map((id) => namingTerms[id].formula));
  const naturalDomains = joinNatural(descriptors);
  const naturalActions = joinNatural(actionTerms).toLowerCase();
  const nameSuggestions = [
    "Jora · " + shortTerms.join(" / "),
    "Jora — " + naturalDomains + " Workspace",
    "Jora | Workspace for " + naturalActions,
    "Jora — " + formulaTerms.join(" + ")
  ];

  const graph = {
    topology: graphTopology,
    objective: graphObjective,
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
      objective: graphObjective,
      objectiveLabel: GRAPH_OBJECTIVES[graphObjective],
      selectionPolicy: "max_compatibility_then_capability_reuse_then_minimal_planned_nodes",
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
