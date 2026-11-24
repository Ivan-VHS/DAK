const COMPONENTS = [
  ["text_editor", "Текстовый редактор", ["текстовый редактор", "редактор текста", "text editor", "markdown editor"]],
  ["audio_editor", "Аудиоредактор", ["аудиоредактор", "редактор аудио", "audio editor", "sound editor"]],
  ["translator", "Переводчик", ["переводчик", "перевод", "translator", "translation", "локализация"]],
  ["subtitle_export", "Экспорт субтитров", ["субтитры", "экспорт субтитров", "subtitle export", "srt", "vtt"]],
  ["speech_to_text", "Распознавание речи", ["распознавание речи", "транскрибация", "speech to text", "stt"]],
  ["text_to_speech", "Синтез речи", ["синтез речи", "озвучка", "text to speech", "tts"]],
  ["glossary", "Глоссарий", ["глоссарий", "терминологический словарь", "glossary"]],
  ["notes", "Заметки", ["заметки", "блокнот", "notes", "notepad"]],
  ["task_board", "Доска задач", ["доска задач", "задачи", "канбан", "task board", "kanban"]],
  ["calendar", "Календарь", ["календарь", "calendar", "расписание"]],
  ["spreadsheet", "Таблицы", ["таблицы", "электронные таблицы", "spreadsheet"]],
  ["charts", "Визуализация данных", ["графики", "диаграммы", "визуализация данных", "charts"]],
  ["code_editor", "Редактор кода", ["редактор кода", "code editor", "ide"]],
  ["debugger", "Отладчик", ["отладчик", "debugger", "debug"]],
  ["build_pipeline", "Сборочный конвейер", ["сборка", "сборочный конвейер", "build pipeline", "сборщик"]],
  ["file_manager", "Файловый менеджер", ["файловый менеджер", "файлы", "file manager"]],
  ["search_index", "Поисковый индекс", ["поиск", "поисковый индекс", "search index"]],
  ["version_control", "Версионирование", ["контроль версий", "версионирование", "version control", "git"]],
  ["image_editor", "Редактор изображений", ["редактор изображений", "фоторедактор", "image editor"]],
  ["video_editor", "Видеоредактор", ["видеоредактор", "редактор видео", "video editor"]],
  ["presentation", "Генератор презентаций", ["презентации", "генератор презентаций", "presentation"]],
  ["cloud_sync", "Облачная синхронизация", ["облачная синхронизация", "cloud sync", "облако"]],
  ["cloud_streaming", "Только облачная обработка", ["только облако", "облачный стриминг", "cloud streaming"]],
  ["offline_mode", "Строго офлайн-режим", ["строго офлайн", "офлайн режим", "offline mode"]],
  ["automation_rules", "Правила автоматизации", ["автоматизация", "правила автоматизации", "automation rules"]]
].map(([id, name, aliases]) => ({ id, name, aliases }));

const BY_ID = new Map(COMPONENTS.map((item) => [item.id, item]));
const ALIASES = new Map();
for (const item of COMPONENTS) {
  for (const alias of [item.id, item.name, ...item.aliases]) {
    ALIASES.set(normalizeJoraAlias(alias), item.id);
  }
}

const STORAGE_KEY = "duckos.jora.store.v1";
const QUICK_ADD = ["subtitle_export", "glossary", "notes", "speech_to_text", "text_to_speech"];

function normalizeJoraAlias(value) {
  return String(value).toLocaleLowerCase("ru-RU").replaceAll("_", " ").trim().replace(/\s+/g, " ");
}

export function analyzeJoraFormula(source) {
  if (typeof source !== "string" || !source.trim()) {
    return { ok: false, error: "Введите формулу хотя бы из одного компонента." };
  }
  if (source.length > 16384) return { ok: false, error: "Формула слишком длинная (лимит 16 384 символа)." };
  const tokens = source.trim().split(/\s*(?:\+|;|,|\s+и\s+|\band\b)\s*/i).filter(Boolean);
  if (tokens.length > 256) return { ok: false, error: "Максимум 256 компонентов на одну генерацию." };
  const components = [];
  for (const rawToken of tokens) {
    let token = rawToken.trim();
    let role = "standard";
    const roleMatch = token.match(/^(основной|главный|primary|фоновый|вспомогательный|background|опциональный|optional)\s*:\s*/i);
    if (roleMatch) {
      role = /^(основной|главный|primary)$/i.test(roleMatch[1]) ? "primary" :
        /^(опциональный|optional)$/i.test(roleMatch[1]) ? "optional" : "background";
      token = token.slice(roleMatch[0].length).trim();
    }
    let weight = 1;
    const weightMatch = token.match(/\s*[xх×]\s*(\d+)\s*$/i);
    if (weightMatch) {
      weight = Number(weightMatch[1]);
      token = token.slice(0, weightMatch.index).trim();
      if (!Number.isInteger(weight) || weight < 1 || weight > 16) {
        return { ok: false, error: "Вес компонента должен быть от 1 до 16." };
      }
    }
    const id = ALIASES.get(normalizeJoraAlias(token));
    if (!id) {
      const suggestions = COMPONENTS.filter((item) =>
        item.aliases.some((alias) => normalizeJoraAlias(alias).includes(normalizeJoraAlias(token))) ||
        normalizeJoraAlias(item.name).includes(normalizeJoraAlias(token))
      ).slice(0, 4).map((item) => item.name);
      return { ok: false, error: "Неизвестный компонент: " + token +
        (suggestions.length ? ". Попробуйте: " + suggestions.join(", ") : "") + "." };
    }
    if (components.some((item) => item.id === id)) {
      return { ok: false, error: "Компонент «" + BY_ID.get(id).name + "» указан дважды." };
    }
    components.push({ id, name: BY_ID.get(id).name, role, weight });
  }
  const ids = new Set(components.map((item) => item.id));
  if (ids.has("offline_mode") && (ids.has("cloud_streaming") || ids.has("cloud_sync"))) {
    return { ok: false, error: "Строго офлайн-режим несовместим с компонентами, которым требуется сеть." };
  }
  const canonical = components.map((item) => item.id + ":" + item.role + ":x" + item.weight).join("|");
  return { ok: true, components, ids: [...ids], canonical, complexity: components.reduce((sum, item) => sum + item.weight, 0) };
}

const DOMAIN_BY_ID = {
  text_editor: "text", translator: "language", glossary: "language",
  audio_editor: "audio", speech_to_text: "language", text_to_speech: "audio",
  subtitle_export: "media", video_editor: "media", image_editor: "media",
  notes: "productivity", task_board: "productivity", calendar: "productivity",
  spreadsheet: "data", charts: "data", search_index: "data",
  code_editor: "development", debugger: "development", build_pipeline: "development",
  version_control: "development", file_manager: "system", cloud_sync: "network",
  cloud_streaming: "network", offline_mode: "quality", automation_rules: "productivity",
  presentation: "productivity"
};
const CONTRACTS_BY_ID = {
  text_editor: ["text.document", "text.segment"],
  audio_editor: ["audio.asset", "audio.segment", "timeline.marker"],
  translator: ["text.segment", "translation.segment", "glossary.term"],
  subtitle_export: ["text.segment", "translation.segment", "timeline.marker"],
  speech_to_text: ["audio.asset", "text.segment"],
  text_to_speech: ["text.segment", "audio.asset"],
  glossary: ["glossary.term", "text.document"],
  notes: ["note.item"], task_board: ["task.item", "note.item"],
  calendar: ["calendar.event", "task.item"], spreadsheet: ["data.table"],
  charts: ["data.table", "chart.figure"], code_editor: ["source.file"],
  debugger: ["source.file", "debug.report"], build_pipeline: ["source.file", "build.artifact"],
  file_manager: ["filesystem.entry"], search_index: ["search.result", "text.document"],
  version_control: ["source.file", "source.revision"], image_editor: ["image.asset"],
  video_editor: ["video.asset", "audio.asset", "timeline.marker"],
  presentation: ["text.document", "data.table", "presentation.file"],
  cloud_sync: ["project.snapshot"], cloud_streaming: ["remote.asset"],
  offline_mode: [], automation_rules: ["system.event", "automation.action"]
};
const SPECIAL_SYNERGIES = {
  "audio_editor|text_editor": ["text.segment", "timeline.marker"],
  "charts|spreadsheet": ["data.table", "chart.figure"],
  "code_editor|debugger": ["source.file", "debug.report"],
  "build_pipeline|code_editor": ["source.file", "build.artifact"],
  "calendar|task_board": ["task.item", "calendar.event"],
  "notes|task_board": ["note.item", "task.item"]
};

function synergyContracts(left, right) {
  const key = [left, right].sort().join("|");
  if (SPECIAL_SYNERGIES[key]) return SPECIAL_SYNERGIES[key];
  const leftContracts = CONTRACTS_BY_ID[left] || [];
  const rightContracts = new Set(CONTRACTS_BY_ID[right] || []);
  const shared = leftContracts.filter((contract) => rightContracts.has(contract));
  if (shared.length) return shared;
  return DOMAIN_BY_ID[left] && DOMAIN_BY_ID[left] === DOMAIN_BY_ID[right] ? ["domain.shared"] : [];
}

export function buildJoraGraph(components, maxNeighbors = 4) {
  const limit = Math.max(1, Math.min(16, Number.isInteger(maxNeighbors) ? maxNeighbors : 4));
  const nodes = [{ id: "reaper:core", name: "Reaper Core", kind: "coordinator" }];
  const edges = [];
  for (const item of components) {
    nodes.push({ id: item.id, name: item.name, kind: "component", domain: DOMAIN_BY_ID[item.id] || "other" });
    edges.push({ from: "reaper:core", to: item.id, type: "component_registration" });
  }
  const seen = new Set();
  const contractIndex = new Map();
  const domainIndex = new Map();
  const inserted = new Set();
  for (const right of components) {
    const candidates = new Set();
    for (const contract of CONTRACTS_BY_ID[right.id] || []) {
      for (const id of contractIndex.get(contract) || []) candidates.add(id);
    }
    for (const id of domainIndex.get(DOMAIN_BY_ID[right.id]) || []) candidates.add(id);
    const special = right.id === "audio_editor" ? "text_editor" : right.id === "text_editor" ? "audio_editor" : null;
    if (special && inserted.has(special)) candidates.add(special);
    const scored = [...candidates].map((id) => ({ id, contracts: synergyContracts(id, right.id) }))
      .filter((item) => item.contracts.length)
      .sort((a, b) => b.contracts.length - a.contracts.length || a.id.localeCompare(b.id));
    for (const candidate of scored.slice(0, limit)) {
      const pair = [candidate.id, right.id].sort();
      const key = pair.join("|");
      if (seen.has(key)) continue;
      seen.add(key);
      edges.push({ from: pair[0], to: pair[1], type: "typed_synergy", contracts: candidate.contracts });
    }
    for (const contract of CONTRACTS_BY_ID[right.id] || []) {
      const index = contractIndex.get(contract) || [];
      index.push(right.id);
      if (index.length > limit) index.shift();
      contractIndex.set(contract, index);
    }
    const domain = DOMAIN_BY_ID[right.id] || "other";
    const domainCandidates = domainIndex.get(domain) || [];
    domainCandidates.push(right.id);
    if (domainCandidates.length > limit) domainCandidates.shift();
    domainIndex.set(domain, domainCandidates);
    inserted.add(right.id);
  }
  return { nodes, edges, maxNeighbors: limit, growth: "O(N*M*K)", clusters: [...new Set(components.map((item) => DOMAIN_BY_ID[item.id] || "other"))] };
}

function generatedIdentity(ids) {
  const selected = new Set(ids);
  if (["text_editor", "audio_editor", "translator"].every((id) => selected.has(id)) && selected.size === 3) {
    return { name: "Слововолна", slug: "slovovolna" };
  }
  if (selected.has("audio_editor") && selected.has("translator")) return { name: "Voxling", slug: "voxling" };
  if (selected.has("text_editor") && selected.has("translator")) return { name: "Lexora", slug: "lexora" };
  if (selected.has("code_editor") && selected.has("debugger")) return { name: "Tracecraft", slug: "tracecraft" };
  const domains = [...new Set(ids.map((id) => id.split("_")[0]))].sort();
  const words = { text: "Lex", audio: "Vox", translator: "Ling", task: "Tempo", calendar: "Chrona", spreadsheet: "Datum", charts: "Vista", code: "Forge", image: "Pixel", video: "Frame", presentation: "Slide", notes: "Memo" };
  const name = (words[domains[0]] || "Nova") + (words[domains[1]] || "Flow");
  const slug = name.toLocaleLowerCase("en-US").replace(/[^a-z0-9]+/g, "-");
  return { name, slug };
}

function languagePlan(ids, profile) {
  const rows = [{ language: "Reaper", role: "core", availability: "required", reason: "Основной исходник и интеграционное ядро." }];
  if (ids.some((id) => ["translator", "glossary", "subtitle_export", "speech_to_text", "text_to_speech", "search_index"].includes(id))) {
    rows.push({ language: "Python", role: "specialized", availability: "native_cli_check", reason: "Текстовые и контентные адаптеры; генератор добавляет stdlib helper." });
  }
  if (ids.some((id) => ["audio_editor", "video_editor"].includes(id))) {
    rows.push({ language: "Rust or C", role: "specialized", availability: "native_cli_check", reason: "DSP/media boundary only when rustc or a C compiler is present." });
  }
  if (profile === "web") rows.push({ language: "JavaScript/TypeScript", role: "ui", availability: "profile_dependent", reason: "Mora browser UI uses JavaScript; TypeScript is optional." });
  return rows;
}

export function analyzeJora(source, profile = "desktop") {
  const parsed = analyzeJoraFormula(source);
  if (!parsed.ok) return parsed;
  const graph = buildJoraGraph(parsed.components);
  const identity = generatedIdentity(parsed.ids);
  const languages = languagePlan(parsed.ids, profile);
  return {
    ok: true, formula: parsed, graph, identity, languages, profile,
    command: "duckos jora create --formula " + JSON.stringify(source) + " --output ./" + identity.slug + ".jora",
    status: "browser_preview_only"
  };
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function readDrafts() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(value) ? value.filter((item) => item && typeof item.formula === "string" && typeof item.name === "string") : [];
  } catch {
    return [];
  }
}

function saveDrafts(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, 100)));
}

export function mountJoraPanel(root, options = {}) {
  if (!root) return;
  const notify = typeof options.notify === "function" ? options.notify : () => {};
  root.replaceChildren();
  root.classList.add("jora-root");

  const intro = element("div", "jora-intro");
  intro.append(
    element("p", "window-kicker", "JORA · FORMULA-DRIVEN APP FACTORY"),
    element("h2", "jora-heading", "Создайте приложение из компонентов"),
    element("p", "jora-copy", "Составьте формулу — Jora рассчитает архитектуру, граф связей и языковой профиль. Нативная команда DuckOS создаст исходный пакет.")
  );
  root.append(intro);

  const studio = element("section", "jora-studio");
  const form = element("form", "jora-form");
  const label = element("label", "jora-label", "Формула приложения");
  const formula = element("textarea", "jora-formula");
  formula.rows = 3;
  formula.maxLength = 16384;
  formula.value = "текстовый редактор + аудиоредактор + переводчик";
  formula.setAttribute("aria-label", "Формула приложения");
  const actions = element("div", "jora-actions");
  const generate = element("button", "action-button", "Построить архитектуру");
  generate.type = "submit";
  const profile = document.createElement("select");
  profile.className = "jora-profile";
  for (const [value, title] of [["desktop", "Desktop"], ["web", "Web"], ["cli", "CLI"], ["source_only", "Source only"]]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = title;
    profile.append(option);
  }
  actions.append(profile, generate);
  form.append(label, formula, actions);
  studio.append(form);

  const quick = element("div", "jora-quick-add");
  quick.append(element("span", "jora-muted", "Добавить компонент:"));
  for (const id of QUICK_ADD) {
    const item = BY_ID.get(id);
    const button = element("button", "jora-chip", "+ " + item.name);
    button.type = "button";
    button.dataset.joraAdd = id;
    quick.append(button);
  }
  studio.append(quick);
  root.append(studio);

  const status = element("p", "jora-status", "Формула готова к анализу.");
  status.setAttribute("aria-live", "polite");
  root.append(status);

  const result = element("section", "jora-results");
  result.hidden = true;
  root.append(result);

  const draftsSection = element("section", "jora-drafts");
  draftsSection.append(element("h3", "jora-section-title", "Локальные черновики"));
  const search = document.createElement("input");
  search.className = "jora-search";
  search.type = "search";
  search.placeholder = "Найти черновик по имени или формуле";
  search.setAttribute("aria-label", "Поиск локальных черновиков");
  const drafts = element("div", "jora-draft-list");
  draftsSection.append(search, drafts);
  root.append(draftsSection);

  let latest = null;

  function renderDrafts() {
    drafts.replaceChildren();
    const query = search.value.trim().toLocaleLowerCase("ru-RU");
    const rows = readDrafts().filter((item) => !query ||
      (item.name + " " + item.formula).toLocaleLowerCase("ru-RU").includes(query));
    if (!rows.length) {
      drafts.append(element("p", "jora-muted", "Черновиков пока нет. Сохраните формулу после анализа."));
      return;
    }
    for (const row of rows) {
      const card = element("div", "jora-draft");
      const copy = element("div", "jora-draft-copy");
      copy.append(element("strong", "", row.name), element("span", "", row.formula));
      const open = element("button", "subtle-button", "Открыть");
      open.type = "button";
      open.dataset.joraLoad = row.formula;
      card.append(copy, open);
      drafts.append(card);
    }
  }

  function renderAnalysis(analysis) {
    result.replaceChildren();
    if (!analysis.ok) {
      result.hidden = true;
      status.textContent = analysis.error;
      status.classList.add("is-error");
      return;
    }
    status.classList.remove("is-error");
    status.textContent = "Архитектурный план построен. Это предпросмотр; исходный пакет ещё не создавался.";
    result.hidden = false;

    const hero = element("div", "jora-result-hero");
    hero.append(
      element("p", "window-kicker", "ПРЕДЛАГАЕМОЕ ИМЯ"),
      element("h3", "jora-app-name", analysis.identity.name),
      element("p", "jora-copy", analysis.identity.slug + " · " + analysis.formula.components.length + " компонентов")
    );
    const formulaLine = element("div", "jora-formula-line");
    analysis.formula.components.forEach((item, index) => {
      if (index) formulaLine.append(element("span", "jora-plus", "+"));
      formulaLine.append(element("span", "jora-chip", item.name + (item.weight > 1 ? " ×" + item.weight : "")));
    });
    hero.append(formulaLine);
    result.append(hero);

    const columns = element("div", "jora-result-grid");
    const graphCard = element("section", "jora-card");
    graphCard.append(element("h4", "jora-section-title", "Граф интеграции"));
    const nodes = element("div", "jora-node-list");
    for (const node of analysis.graph.nodes) {
      nodes.append(element("span", "jora-node" + (node.kind === "coordinator" ? " is-core" : ""), node.name));
    }
    graphCard.append(nodes, element("p", "jora-muted", analysis.graph.edges.length + " рёбер · O(N×M) · максимум " + analysis.graph.maxNeighbors + " соседей на компонент"));
    const edges = element("ul", "jora-edge-list");
    for (const edge of analysis.graph.edges.filter((item) => item.type === "typed_synergy")) {
      const left = BY_ID.get(edge.from)?.name || edge.from;
      const right = BY_ID.get(edge.to)?.name || edge.to;
      edges.append(element("li", "", left + " ↔ " + right + " · " + (edge.contracts || []).join(", ")));
    }
    graphCard.append(edges);

    const stackCard = element("section", "jora-card");
    stackCard.append(element("h4", "jora-section-title", "Языковой профиль"));
    for (const item of analysis.languages) {
      const row = element("div", "jora-language");
      row.append(element("strong", "", item.language), element("span", "", item.reason));
      stackCard.append(row);
    }
    stackCard.append(element("p", "jora-muted", "Фактическая доступность компиляторов проверяется нативной командой DuckOS. Reaper native compiler не предполагается автоматически."));
    columns.append(graphCard, stackCard);
    result.append(columns);

    const cli = element("section", "jora-cli-card");
    cli.append(element("h4", "jora-section-title", "Создать пакет в DuckOS"));
    cli.append(element("p", "jora-copy", "Браузерная Mora не запускает процессы хоста. Выполните эту команду в нативном терминале DuckOS."));
    const command = element("code", "jora-command", analysis.command);
    cli.append(command);
    const copy = element("button", "action-button", "Скопировать команду");
    copy.type = "button";
    copy.dataset.joraCopy = analysis.command;
    cli.append(copy);
    const save = element("button", "subtle-button", "Сохранить черновик в Mora");
    save.type = "button";
    save.dataset.joraSave = "true";
    cli.append(save);
    result.append(cli);
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    latest = analyzeJora(formula.value, profile.value);
    renderAnalysis(latest);
  });

  quick.addEventListener("click", (event) => {
    const button = event.target.closest("[data-jora-add]");
    if (!button) return;
    const label = BY_ID.get(button.dataset.joraAdd)?.name;
    if (!label) return;
    formula.value = formula.value.trim() ? formula.value.trim() + " + " + label : label;
    latest = analyzeJora(formula.value, profile.value);
    renderAnalysis(latest);
  });

  result.addEventListener("click", async (event) => {
    const copy = event.target.closest("[data-jora-copy]");
    if (copy) {
      try {
        await navigator.clipboard.writeText(copy.dataset.joraCopy);
        notify("Команда DuckOS скопирована");
      } catch {
        status.textContent = "Буфер обмена недоступен; выделите команду и скопируйте её вручную.";
      }
      return;
    }
    if (event.target.closest("[data-jora-save]")) {
      if (!latest || !latest.ok) return;
      try {
        const items = readDrafts();
        const row = {
          formula: formula.value.trim(),
          name: latest.identity.name,
          slug: latest.identity.slug,
          saved_at: new Date().toISOString(),
          maturity: "local_formula_draft"
        };
        const remaining = items.filter((item) => item.formula !== row.formula);
        saveDrafts([row, ...remaining]);
        renderDrafts();
        status.textContent = "Черновик сохранён только в хранилище текущего профиля Mora.";
        notify("Черновик Jora сохранён в Mora");
      } catch {
        status.textContent = "Не удалось сохранить черновик в локальном хранилище.";
      }
    }
  });

  drafts.addEventListener("click", (event) => {
    const button = event.target.closest("[data-jora-load]");
    if (!button) return;
    formula.value = button.dataset.joraLoad;
    latest = analyzeJora(formula.value, profile.value);
    renderAnalysis(latest);
  });
  search.addEventListener("input", renderDrafts);
  renderDrafts();
}
