export const PERSONAL_SUITE_APPS = [
  {
    id: "lumina-cycle", name: "LuminaCycle", subtitle: "Цикл и самочувствие", group: "health", privacy: "sensitive", color: "#B7839D", glyph: "◔",
    description: "Личный календарь цикла с отметками самочувствия и ориентировочными датами.",
    titleField: "startDate", detailFields: ["cycleLength", "periodLength", "energy", "note"],
    capabilities: ["cycle_date_log", "self_reported_energy_notes", "calendar_estimates"],
    boundaries: ["Не ставит диагнозы и не даёт медицинских рекомендаций.", "Календарные оценки приблизительны и не являются прогнозом фертильности."],
    fields: [
      { key: "startDate", label: "Первый день цикла", type: "date", required: true },
      { key: "cycleLength", label: "Обычная длина цикла, дней", type: "number", min: 15, max: 60, defaultValue: "28", required: true },
      { key: "periodLength", label: "Длительность менструации, дней", type: "number", min: 1, max: 12, defaultValue: "5" },
      { key: "energy", label: "Самочувствие", type: "select", options: [["low", "Низкая энергия"], ["steady", "Ровная энергия"], ["high", "Много энергии"], ["variable", "Переменчивая"]] },
      { key: "note", label: "Личная заметка", type: "textarea", maxLength: 300 }
    ]
  },
  {
    id: "nura-calm", name: "NuraCalm", subtitle: "Спокойствие и дыхание", group: "health", privacy: "private", color: "#8FA6A0", glyph: "☾",
    description: "Дневник состояния, дыхательная пауза без звука и журнал спокойных ритуалов.",
    titleField: "mood", detailFields: ["stress", "note"],
    capabilities: ["mood_journal", "stress_self_rating", "guided_breathing_timer"],
    boundaries: ["Не является медицинским или психотерапевтическим инструментом.", "Практику можно остановить в любой момент."],
    fields: [
      { key: "mood", label: "Настроение", type: "select", required: true, options: [["calm", "Спокойно"], ["good", "Хорошо"], ["tired", "Усталость"], ["tense", "Напряжение"], ["sad", "Грусть"], ["mixed", "Смешанные чувства"]] },
      { key: "stress", label: "Напряжение, от 1 до 5", type: "number", min: 1, max: 5, defaultValue: "3" },
      { key: "note", label: "Что важно отметить", type: "textarea", maxLength: 300 }
    ]
  },
  {
    id: "verba-rest", name: "VerbaRest", subtitle: "Отдых и паузы", group: "health", privacy: "private", color: "#93A58B", glyph: "⌁",
    description: "План мягких пауз, завершения рабочего дня и заметок о восстановлении.",
    titleField: "activity", detailFields: ["duration", "date", "note"],
    capabilities: ["rest_routine_log", "break_planning", "workday_boundary_notes"],
    boundaries: ["Напоминания не срабатывают, когда оболочка закрыта.", "Системное управление фокусом и уведомлениями не подключено."],
    fields: [
      { key: "activity", label: "Пауза или ритуал", type: "text", required: true, placeholder: "Прогулка, чай, отдых без экрана", maxLength: 80 },
      { key: "duration", label: "Длительность, минут", type: "number", min: 1, max: 600, defaultValue: "15" },
      { key: "date", label: "Дата", type: "date" },
      { key: "note", label: "Заметка", type: "textarea", maxLength: 240 }
    ]
  },
  {
    id: "sora-glow", name: "SoraGlow", subtitle: "Уход за кожей и волосами", group: "health", privacy: "private", color: "#C58F83", glyph: "✧",
    description: "Дневник средств, последовательности ухода и личных реакций.",
    titleField: "product", detailFields: ["routine", "reaction", "date"],
    capabilities: ["product_diary", "routine_notes", "personal_reaction_log"],
    boundaries: ["Не оценивает безопасность ингредиентов и не назначает лечение.", "Погодные данные и сезонные рекомендации не подключены."],
    fields: [
      { key: "product", label: "Средство", type: "text", required: true, placeholder: "Название средства", maxLength: 100 },
      { key: "routine", label: "Тип ухода", type: "select", options: [["skin-am", "Кожа · утро"], ["skin-pm", "Кожа · вечер"], ["hair", "Волосы"], ["other", "Другое"]] },
      { key: "reaction", label: "Личное наблюдение", type: "textarea", maxLength: 280 },
      { key: "date", label: "Дата", type: "date" }
    ]
  },
  {
    id: "kora-closet", name: "KoraCloset", subtitle: "Цифровой гардероб", group: "style", privacy: "private", color: "#BD9A78", glyph: "◇",
    description: "Каталог собственных вещей, сезонных категорий и заметок о готовых сочетаниях.",
    titleField: "item", detailFields: ["category", "color", "season"],
    capabilities: ["wardrobe_catalog", "seasonal_tags", "outfit_notes"],
    boundaries: ["Погода и автоматические рекомендации образов не подключены.", "Внешние магазины не отслеживаются."],
    fields: [
      { key: "item", label: "Вещь", type: "text", required: true, placeholder: "Например, льняная рубашка", maxLength: 100 },
      { key: "category", label: "Категория", type: "select", options: [["tops", "Верх"], ["bottoms", "Низ"], ["dress", "Платье"], ["outerwear", "Верхняя одежда"], ["shoes", "Обувь"], ["accessories", "Аксессуар"]] },
      { key: "color", label: "Цвет вещи", type: "text", maxLength: 40, placeholder: "Бежевый, графитовый…" },
      { key: "season", label: "Сезон", type: "select", options: [["all", "Круглый год"], ["spring", "Весна"], ["summer", "Лето"], ["autumn", "Осень"], ["winter", "Зима"]] }
    ]
  },
  {
    id: "mirra-fit", name: "MirraFit", subtitle: "Замеры и посадка", group: "style", privacy: "sensitive", color: "#A48D9C", glyph: "⌖",
    description: "Личный архив замеров и заметок о посадке одежды. Записи остаются в локальном профиле.",
    titleField: "measurement", detailFields: ["value", "unit", "date", "fit"],
    capabilities: ["measurement_history", "fit_notes", "dated_comparisons"],
    boundaries: ["Не оценивает тело и не делает медицинских выводов.", "Значения не передаются и не синхронизируются."],
    fields: [
      { key: "measurement", label: "Параметр или вещь", type: "text", required: true, placeholder: "Например, талия или размер жакета", maxLength: 80 },
      { key: "value", label: "Значение", type: "number", min: 0, max: 500, step: "0.1", required: true },
      { key: "unit", label: "Единица", type: "select", options: [["cm", "см"], ["kg", "кг"], ["size", "размер"], ["other", "другое"]] },
      { key: "date", label: "Дата замера", type: "date" },
      { key: "fit", label: "Посадка и комментарий", type: "textarea", maxLength: 240 }
    ]
  },
  {
    id: "talia-palette", name: "TaliaPalette", subtitle: "Цветовые палитры", group: "style", privacy: "private", color: "#A98BAE", glyph: "◉",
    description: "Коллекция цветов для одежды, макияжа и интерьера с сохранением HEX-кода.",
    titleField: "name", detailFields: ["hex", "usage"],
    capabilities: ["saved_color_swatches", "hex_palette_export", "usage_tags"],
    boundaries: ["Автоматический анализ при разном освещении не подключён.", "Классификация оттенка кожи не выполняется."],
    fields: [
      { key: "name", label: "Название оттенка", type: "text", required: true, placeholder: "Пыльная роза", maxLength: 60 },
      { key: "hex", label: "Цвет", type: "color", defaultValue: "#B7839D", required: true },
      { key: "usage", label: "Для чего", type: "select", options: [["clothes", "Одежда"], ["makeup", "Макияж"], ["interior", "Интерьер"], ["mixed", "Общая палитра"]] }
    ]
  },
  {
    id: "zara-loom", name: "ZaraLoom", subtitle: "Локальные мастера и бренды", group: "style", privacy: "private", color: "#B18C72", glyph: "✳",
    description: "Личная подборка локальных мастеров, брендов и апсайклинг-проектов, добавляемых вручную.",
    titleField: "maker", detailFields: ["craft", "material", "url"],
    capabilities: ["manual_maker_directory", "material_notes", "saved_reference_links"],
    boundaries: ["Каталог не является маркетплейсом и не проверяет продавцов или сертификаты.", "Ссылки добавляются пользователем и проверяются им самостоятельно."],
    fields: [
      { key: "maker", label: "Мастер или бренд", type: "text", required: true, placeholder: "Название", maxLength: 100 },
      { key: "craft", label: "Изделия", type: "text", maxLength: 100, placeholder: "Одежда, керамика, аксессуары" },
      { key: "material", label: "Материалы и состав", type: "text", maxLength: 120 },
      { key: "url", label: "Сайт или страница", type: "url", maxLength: 300, placeholder: "https://…" }
    ]
  },
  {
    id: "bela-notes", name: "BelaNotes", subtitle: "Заметки и идеи", group: "creative", privacy: "sensitive", color: "#9B9CB6", glyph: "✎",
    description: "Быстрый личный блокнот с тегами, поиском и локальным сохранением черновиков.",
    titleField: "title", detailFields: ["tags", "body"],
    capabilities: ["quick_notes", "tagged_search", "local_drafts"],
    boundaries: ["Заметки остаются в профиле браузера, пока пользователь не экспортирует их вручную.", "Облачная синхронизация и совместное редактирование не подключены."],
    fields: [
      { key: "title", label: "Заголовок", type: "text", required: true, placeholder: "Новая мысль", maxLength: 100 },
      { key: "body", label: "Текст", type: "textarea", required: true, maxLength: 1600 },
      { key: "tags", label: "Теги через запятую", type: "text", maxLength: 160 }
    ]
  },
  {
    id: "rina-craft", name: "RinaCraft", subtitle: "Творческие проекты", group: "creative", privacy: "private", color: "#B58D82", glyph: "✿",
    description: "План проектов по шитью, керамике, рисованию и другим ремёслам.",
    titleField: "project", detailFields: ["craft", "stage", "materials"],
    capabilities: ["craft_project_board", "materials_inventory_notes", "stage_tracking"],
    boundaries: ["Внешнее хранилище, платные схемы и маркетплейс не подключены."],
    fields: [
      { key: "project", label: "Проект", type: "text", required: true, placeholder: "Название проекта", maxLength: 100 },
      { key: "craft", label: "Направление", type: "select", options: [["sewing", "Шитьё"], ["ceramics", "Керамика"], ["painting", "Рисование"], ["knitting", "Вязание"], ["other", "Другое"]] },
      { key: "stage", label: "Текущий этап", type: "text", maxLength: 100, placeholder: "Эскиз, подготовка, сборка…" },
      { key: "materials", label: "Материалы и схема", type: "textarea", maxLength: 300 }
    ]
  },
  {
    id: "olea-kitchen", name: "OleaKitchen", subtitle: "Рецепты и меню", group: "creative", privacy: "private", color: "#A99B70", glyph: "❋",
    description: "Личная книга рецептов и список ингредиентов. Выбранный список можно добавить в MilaNest.",
    titleField: "recipe", detailFields: ["ingredients", "method"],
    capabilities: ["recipe_book", "ingredient_lists", "manual_meal_tags", "shopping_task_handoff"],
    boundaries: ["Не рассчитывает лечебное питание или медицинские диеты.", "Складские остатки и магазины не подключены."],
    fields: [
      { key: "recipe", label: "Блюдо", type: "text", required: true, placeholder: "Название рецепта", maxLength: 100 },
      { key: "ingredients", label: "Ингредиенты через запятую", type: "textarea", required: true, maxLength: 500 },
      { key: "method", label: "Приготовление", type: "textarea", maxLength: 900 },
      { key: "meal", label: "Приём пищи", type: "select", options: [["breakfast", "Завтрак"], ["lunch", "Обед"], ["dinner", "Ужин"], ["snack", "Перекус"]] }
    ]
  },
  {
    id: "veda-bloom", name: "VedaBloom", subtitle: "Цели, чтение и обучение", group: "creative", privacy: "private", color: "#92A68C", glyph: "✦",
    description: "Бережный трекер небольших целей и привычек без наказания за пропущенные дни.",
    titleField: "goal", detailFields: ["area", "targetDate", "note"],
    capabilities: ["goal_list", "reading_and_learning_log", "non_punitive_progress"],
    boundaries: ["Нет штрафов за пропущенные дни и публичного рейтинга.", "Прогресс отмечается пользователем."],
    fields: [
      { key: "goal", label: "Цель", type: "text", required: true, placeholder: "Прочитать книгу, освоить навык…", maxLength: 120 },
      { key: "area", label: "Направление", type: "select", options: [["reading", "Чтение"], ["learning", "Обучение"], ["creative", "Творчество"], ["personal", "Личное"]] },
      { key: "targetDate", label: "Желаемая дата", type: "date" },
      { key: "note", label: "Первый небольшой шаг", type: "textarea", maxLength: 220 }
    ]
  },
  {
    id: "mila-nest", name: "MilaNest", subtitle: "Домашние дела и списки", group: "home", privacy: "private", color: "#A7A88A", glyph: "⌂",
    description: "Домашняя доска задач и покупок с отметками выполнения и ручным распределением.",
    titleField: "task", detailFields: ["date", "owner"],
    capabilities: ["household_task_list", "due_date_tags", "manual_assignment", "shopping_handoff"],
    boundaries: ["Совместный домашний аккаунт и уведомления в фоне не подключены.", "Назначение — локальная подпись, а не отправка сообщения или приглашения."],
    fields: [
      { key: "task", label: "Задача", type: "text", required: true, placeholder: "Что нужно сделать?", maxLength: 140 },
      { key: "date", label: "Срок", type: "date" },
      { key: "owner", label: "Кому", type: "text", placeholder: "Имя или «все»", maxLength: 60 }
    ]
  },
  {
    id: "daria-ledger", name: "DariaLedger", subtitle: "Личный бюджет и накопления", group: "home", privacy: "sensitive", color: "#B69A72", glyph: "₴",
    description: "Локальный учёт доходов, расходов и накоплений. Без банковских подключений и платежей.",
    titleField: "label", detailFields: ["amount", "entryType", "date"],
    capabilities: ["personal_budget_entries", "savings_goals", "income_expense_totals"],
    boundaries: ["Нет подключения к банкам, отправки платежей или автоматических переводов.", "Финансовые данные хранятся локально без шифрования этим браузерным модулем."],
    fields: [
      { key: "label", label: "Операция или цель", type: "text", required: true, placeholder: "Продукты, поездка, накопления…", maxLength: 100 },
      { key: "amount", label: "Сумма, грн", type: "number", required: true, min: 0.01, max: 100000000, step: "0.01" },
      { key: "entryType", label: "Тип", type: "select", required: true, options: [["expense", "Расход"], ["income", "Доход"], ["saving", "Накопление"]] },
      { key: "date", label: "Дата", type: "date" }
    ]
  },
  {
    id: "elda-circle", name: "EldaCircle", subtitle: "Встречи и книжные клубы", group: "home", privacy: "sensitive", color: "#A68FA7", glyph: "○",
    description: "Личный планировщик встреч, книжных клубов и обмена рекомендациями.",
    titleField: "event", detailFields: ["date", "guests", "note"],
    capabilities: ["private_event_planner", "book_club_notes", "recommendation_exchange_list"],
    boundaries: ["Нет публичной социальной сети, сообщений, загрузки контактов и автоматических приглашений.", "Участники хранятся только как личные локальные записи."],
    fields: [
      { key: "event", label: "Встреча или клуб", type: "text", required: true, placeholder: "Книжный вечер", maxLength: 120 },
      { key: "date", label: "Дата и время", type: "datetime-local" },
      { key: "guests", label: "Участники", type: "text", placeholder: "Имена через запятую", maxLength: 220 },
      { key: "note", label: "Место и детали", type: "textarea", maxLength: 300 }
    ]
  }
];

const STORE_KEY = "mora.personal-suite.v1";
const MAX_RECORDS = 500;
const EXPORT_SCHEMA = "mora.personal-suite.export.v1";

export const personalAppDefinitions = Object.fromEntries(PERSONAL_SUITE_APPS.map((app) => [
  app.id,
  { name: app.name, subtitle: app.subtitle, color: app.color, glyph: app.glyph }
]));

function emptyRecords() {
  return Object.fromEntries(PERSONAL_SUITE_APPS.map((app) => [app.id, []]));
}

export function createDefaultPersonalSuiteState() {
  return { schema: "mora.personal-suite.state.v1", version: 1, profile: { displayName: "" }, records: emptyRecords(), updatedAt: null };
}

function normalizeRecord(value) {
  if (!value || typeof value !== "object" || Array.isArray(value) || !value.fields || typeof value.fields !== "object" || Array.isArray(value.fields)) return null;
  const fields = {};
  for (const [key, entry] of Object.entries(value.fields)) {
    if (!/^[a-zA-Z][a-zA-Z0-9_-]{0,40}$/.test(key)) continue;
    if (typeof entry === "string") fields[key] = entry.slice(0, 1600);
    else if (typeof entry === "number" && Number.isFinite(entry)) fields[key] = entry;
  }
  if (typeof value.id !== "string" || !value.id.trim()) return null;
  return { id: value.id.slice(0, 96), createdAt: typeof value.createdAt === "string" ? value.createdAt.slice(0, 40) : "", fields, done: value.done === true };
}

export function normalizePersonalSuiteState(value) {
  const state = createDefaultPersonalSuiteState();
  if (!value || typeof value !== "object" || Array.isArray(value) || value.version !== 1 || !value.records || typeof value.records !== "object") return state;
  state.profile.displayName = typeof value.profile?.displayName === "string" ? value.profile.displayName.slice(0, 48) : "";
  state.updatedAt = typeof value.updatedAt === "string" ? value.updatedAt.slice(0, 40) : null;
  for (const app of PERSONAL_SUITE_APPS) {
    if (Array.isArray(value.records[app.id])) state.records[app.id] = value.records[app.id].slice(0, MAX_RECORDS).map(normalizeRecord).filter(Boolean);
  }
  return state;
}

export function getPersonalSuiteSummary(value) {
  const state = normalizePersonalSuiteState(value);
  const counts = Object.fromEntries(PERSONAL_SUITE_APPS.map((app) => [app.id, state.records[app.id].length]));
  return { applicationCount: PERSONAL_SUITE_APPS.length, totalRecords: Object.values(counts).reduce((sum, count) => sum + count, 0), counts };
}

function escapeHTML(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[character]));
}

let cachedState;
const breathTimers = new Map();

function loadState() {
  if (cachedState) return cachedState;
  try {
    cachedState = normalizePersonalSuiteState(JSON.parse(localStorage.getItem(STORE_KEY) || "null"));
  } catch {
    cachedState = createDefaultPersonalSuiteState();
  }
  return cachedState;
}

function saveState() {
  const state = loadState();
  state.updatedAt = new Date().toISOString();
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(state));
    return true;
  } catch {
    return false;
  }
}

function totalRecords(state) {
  return Object.values(state.records).reduce((count, records) => count + records.length, 0);
}

function announceChange(appId) {
  const state = loadState();
  document.querySelectorAll("[data-suite-total]").forEach((element) => {
    element.textContent = String(totalRecords(state));
  });
  window.dispatchEvent(new CustomEvent("mora:personal-suite-updated", {
    detail: { appId, totalRecords: totalRecords(state) }
  }));
}

function setStatus(panel, message, error = false) {
  const status = panel?.querySelector("[data-suite-status]");
  if (!status) return;
  status.textContent = message;
  status.classList.toggle("is-error", error);
}

function renderField(field) {
  const name = escapeHTML(field.key);
  const label = escapeHTML(field.label);
  const required = field.required ? " required" : "";
  const placeholder = field.placeholder ? ' placeholder="' + escapeHTML(field.placeholder) + '"' : "";
  const maxLength = field.maxLength ? ' maxlength="' + field.maxLength + '"' : "";
  const value = field.defaultValue ? ' value="' + escapeHTML(field.defaultValue) + '"' : "";
  let control;
  if (field.type === "textarea") {
    control = '<textarea name="' + name + '"' + required + placeholder + maxLength + ' rows="3"></textarea>';
  } else if (field.type === "select") {
    const options = field.options.map(([optionValue, optionLabel]) =>
      '<option value="' + escapeHTML(optionValue) + '">' + escapeHTML(optionLabel) + '</option>'
    ).join("");
    control = '<select name="' + name + '"' + required + '><option value="">Выберите…</option>' + options + '</select>';
  } else {
    const min = field.min == null ? "" : ' min="' + field.min + '"';
    const max = field.max == null ? "" : ' max="' + field.max + '"';
    const step = field.step ? ' step="' + escapeHTML(field.step) + '"' : "";
    control = '<input type="' + escapeHTML(field.type) + '" name="' + name + '"' + required + placeholder + maxLength + min + max + step + value + '>';
  }
  return '<label class="suite-field"><span>' + label + '</span>' + control + '</label>';
}

function formatAmount(value) {
  const number = Number(value);
  return Number.isFinite(number) ? new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(number) + " ₴" : "—";
}

function renderSummary(app, records) {
  let summary = records.length ? "Записей в разделе: " + records.length + "." : "Записей пока нет. Добавьте первую, чтобы начать.";
  if (app.id === "lumina-cycle" && records.length) {
    const latest = [...records].filter((record) => /^\d{4}-\d{2}-\d{2}$/.test(record.fields.startDate || ""))
      .sort((a, b) => b.fields.startDate.localeCompare(a.fields.startDate))[0];
    if (latest) {
      const start = new Date(latest.fields.startDate + "T00:00:00");
      const next = new Date(start);
      next.setDate(next.getDate() + (Number(latest.fields.cycleLength) || 28));
      const day = Math.max(1, Math.floor((Date.now() - start.getTime()) / 86400000) + 1);
      summary = "Последняя отметка: " + latest.fields.startDate + ". День по календарю: " + day + ". Ориентир следующей даты: " + next.toLocaleDateString("ru-RU") + ".";
    }
    return '<div class="suite-summary"><strong>Календарный обзор</strong><span>' + escapeHTML(summary) + '</span><small>Расчёт приблизительный и не является медицинской оценкой или прогнозом.</small></div>';
  }
  if (app.id === "daria-ledger") {
    const totals = { expense: 0, income: 0, saving: 0 };
    records.forEach((record) => {
      if (record.fields.entryType in totals) totals[record.fields.entryType] += Number(record.fields.amount) || 0;
    });
    summary = "Доходы: " + formatAmount(totals.income) + " · расходы: " + formatAmount(totals.expense) + " · накопления: " + formatAmount(totals.saving) + ".";
  }
  if (app.id === "mila-nest") {
    const pending = records.filter((record) => !record.done).length;
    summary = "Всего задач: " + records.length + " · ещё предстоит: " + pending + ".";
  }
  if (app.id === "veda-bloom") {
    const completed = records.filter((record) => record.done).length;
    summary = "Целей: " + records.length + " · отмечено завершёнными: " + completed + ". Пропущенные дни не обнуляют прогресс.";
  }
  if (app.id === "bela-notes") summary = "Заметок: " + records.length + ". Поиск работает по заголовкам, тексту и тегам.";
  return '<div class="suite-summary"><strong>Обзор раздела</strong><span>' + escapeHTML(summary) + '</span></div>';
}

function renderQuickTools(app, state) {
  if (app.id === "nura-calm") return '<section class="suite-tool"><div><strong>Дыхательная пауза</strong><span data-breath-status>Вдох 4 · пауза 4 · выдох 6. 3 спокойных цикла.</span></div><button type="button" class="subtle-button" data-suite-action="breath">Начать</button><button type="button" class="subtle-button" data-suite-action="send-rest">Записать паузу в VerbaRest</button></section>';
  const links = {
    "lumina-cycle": ["nura-calm", "Открыть NuraCalm для спокойной паузы"],
    "kora-closet": ["talia-palette", "Подобрать цвета в TaliaPalette"],
    "talia-palette": ["kora-closet", "Вернуться в KoraCloset"],
    "bela-notes": ["rina-craft", "Превратить идею в проект RinaCraft"],
    "veda-bloom": ["bela-notes", "Записать мысль в BelaNotes"]
  };
  if (links[app.id]) return '<div class="suite-cross-link"><span>' + escapeHTML(links[app.id][1]) + '</span><button type="button" data-suite-open="' + links[app.id][0] + '">Открыть ↗</button></div>';
  if (app.id === "olea-kitchen") {
    const latest = state.records[app.id][0];
    const disabled = !latest || !latest.fields.ingredients;
    return '<div class="suite-cross-link"><span>Передать ингредиенты последнего рецепта в домашний список</span><button type="button" data-suite-action="send-shopping"' + (disabled ? " disabled" : "") + '>Добавить в MilaNest ↗</button></div>';
  }
  return "";
}

function renderRecords(app, records) {
  if (!records.length) return '<p class="suite-empty">Записей пока нет.</p>';
  let visible = records;
  if (app.id === "bela-notes") {
    const query = document.querySelector('[data-suite-search="bela-notes"]')?.value.trim().toLowerCase() || "";
    if (query) visible = visible.filter((record) => Object.values(record.fields).join(" ").toLowerCase().includes(query));
  }
  return visible.slice(0, 80).map((record) => {
    const fields = record.fields;
    const title = escapeHTML(fields[app.titleField] || app.name);
    const details = app.detailFields.filter((key) => fields[key] !== undefined && String(fields[key]).trim() !== "").map((key) => {
      const field = app.fields.find((item) => item.key === key);
      if (field?.options) return field.options.find(([value]) => value === String(fields[key]))?.[1] || String(fields[key]);
      if (key === "amount") return formatAmount(fields[key]);
      return fields[key];
    }).map(escapeHTML).join(" · ");
    const swatch = fields.hex && /^#[0-9a-f]{6}$/i.test(fields.hex)
      ? '<span class="suite-color-chip" style="--suite-swatch:' + fields.hex + '"></span>'
      : "";
    const doneButton = ["mila-nest", "veda-bloom"].includes(app.id)
      ? '<button type="button" class="suite-record-action" data-suite-action="toggle-done" data-record-id="' + escapeHTML(record.id) + '">' + (record.done ? "Вернуть" : "Готово") + '</button>'
      : "";
    return '<article class="suite-record' + (record.done ? " is-done" : "") + '"><div class="suite-record-copy">' + swatch +
      '<strong>' + title + '</strong><span>' + (details || "Без дополнительных заметок") + '</span></div>' +
      '<div class="suite-record-actions">' + doneButton +
      '<button type="button" class="suite-record-remove" aria-label="Удалить запись" data-suite-action="delete" data-record-id="' + escapeHTML(record.id) + '">×</button></div></article>';
  }).join("");
}

export function renderPersonalApp(appId) {
  const app = PERSONAL_SUITE_APPS.find((item) => item.id === appId);
  if (!app) return '<h2 class="window-heading">Приложение не найдено</h2>';
  const state = loadState();
  const records = state.records[appId];
  const profileName = state.profile.displayName || "Личный профиль";
  return '<div class="personal-suite-panel" data-suite-app="' + appId + '">' +
    '<div class="suite-topline"><span>MORA PERSONAL SUITE · ' + app.group.toUpperCase() + '</span><span><b data-suite-total>' + totalRecords(state) + '</b> общих записей</span></div>' +
    '<p class="suite-profile-label">Профиль: ' + escapeHTML(profileName) + '</p>' +
    '<p class="suite-description">' + escapeHTML(app.description) + '</p>' +
    renderSummary(app, records) +
    renderQuickTools(app, state) +
    '<form class="suite-form" data-suite-form="' + appId + '"><div class="suite-form-heading"><strong>Новая запись</strong><span>' + records.length + ' в разделе</span></div>' +
    '<div class="suite-form-grid">' + app.fields.map(renderField).join("") + '</div>' +
    '<button class="action-button" type="submit">Сохранить локально</button></form>' +
    '<p class="suite-status" data-suite-status role="status" aria-live="polite">Данные сохраняются только в профиле браузера.</p>' +
    '<section class="suite-record-section"><div class="suite-record-heading"><strong>Ваши записи</strong>' +
    (appId === "bela-notes" ? '<input type="search" class="suite-search" data-suite-search="bela-notes" placeholder="Найти заметку…">' : "") +
    '</div><div class="suite-record-list" data-suite-records="' + appId + '">' + renderRecords(app, records) + '</div></section>' +
    '<div class="suite-data-actions"><button type="button" class="subtle-button" data-suite-action="export">Экспорт раздела</button>' +
    '<label class="suite-import-button">Импорт JSON<input type="file" accept="application/json,.json" data-suite-import="' + appId + '"></label></div>' +
    '<p class="suite-privacy-note">' + (app.privacy === "sensitive"
      ? "Чувствительные данные. Хранятся локально в localStorage профиля браузера и не шифруются этим модулем. Не используйте общий профиль браузера."
      : "Локальное хранение в профиле Mora. Автоматическая синхронизация и отправка данных отсутствуют.") +
      '</p></div>';
}

function makeRecordId() {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : "record-" + Date.now() + "-" + Math.random().toString(36).slice(2, 10);
}

function fieldValue(field, rawValue) {
  const raw = String(rawValue == null ? "" : rawValue).trim();
  if (!raw) return "";
  if (field.type === "number") {
    const value = Number(raw);
    if (!Number.isFinite(value) || (field.min != null && value < field.min) || (field.max != null && value > field.max)) throw new Error("Проверьте поле «" + field.label + "».");
    return value;
  }
  if (field.type === "date" && !/^\d{4}-\d{2}-\d{2}$/.test(raw)) throw new Error("Укажите корректную дату.");
  if (field.type === "datetime-local" && Number.isNaN(Date.parse(raw))) throw new Error("Укажите корректные дату и время.");
  if (field.type === "url") {
    let url;
    try { url = new URL(raw); } catch { throw new Error("Укажите полный адрес сайта, начиная с https://."); }
    if (!["https:", "http:"].includes(url.protocol)) throw new Error("Разрешены только ссылки http и https.");
  }
  if (field.type === "color" && !/^#[0-9a-f]{6}$/i.test(raw)) throw new Error("Выберите цвет из палитры.");
  return raw.slice(0, field.maxLength || 1600);
}

function createRecord(appId, fields) {
  const state = loadState();
  state.records[appId].unshift({ id: makeRecordId(), createdAt: new Date().toISOString(), fields, done: false });
  state.records[appId] = state.records[appId].slice(0, MAX_RECORDS);
  const saved = saveState();
  announceChange(appId);
  return saved;
}

function refreshPanel(panel, appId, message) {
  panel.innerHTML = renderPersonalApp(appId);
  setStatus(panel, message);
}

function handleSubmit(event) {
  const form = event.target.closest("[data-suite-form]");
  if (!form) return;
  event.preventDefault();
  const appId = form.dataset.suiteForm;
  const app = PERSONAL_SUITE_APPS.find((item) => item.id === appId);
  const panel = form.closest("[data-suite-app]");
  if (!app || !panel) return;
  const data = new FormData(form);
  const fields = {};
  try {
    for (const field of app.fields) {
      const value = fieldValue(field, data.get(field.key));
      if (field.required && value === "") throw new Error("Заполните поле «" + field.label + "».");
      if (value !== "") fields[field.key] = value;
    }
  } catch (error) {
    setStatus(panel, error.message || "Не удалось проверить запись.", true);
    return;
  }
  if (!Object.keys(fields).length) {
    setStatus(panel, "Добавьте хотя бы одно значение.", true);
    return;
  }
  const saved = createRecord(appId, fields);
  refreshPanel(panel, appId, saved ? "Запись сохранена в профиле Mora." : "Не удалось записать данные в хранилище. Проверьте свободное место.");
}

function downloadSection(appId) {
  const state = loadState();
  const payload = { schema: EXPORT_SCHEMA, version: 1, appId, exportedAt: new Date().toISOString(), records: state.records[appId] };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = appId + "-mora-export.json";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function importSection(input) {
  const appId = input.dataset.suiteImport;
  const panel = input.closest("[data-suite-app]");
  const file = input.files && input.files[0];
  if (!file || !panel) return;
  if (file.size > 1024 * 1024) {
    setStatus(panel, "Файл больше 1 МиБ. Импорт остановлен.", true);
    input.value = "";
    return;
  }
  file.text().then((content) => {
    const payload = JSON.parse(content);
    if (!payload || payload.schema !== EXPORT_SCHEMA || payload.version !== 1 || payload.appId !== appId || !Array.isArray(payload.records)) throw new Error("Формат файла или идентификатор раздела не совпадает.");
    const normalized = normalizePersonalSuiteState({ version: 1, records: { [appId]: payload.records } });
    const state = loadState();
    const existing = new Set(state.records[appId].map((record) => record.id));
    const incoming = normalized.records[appId].filter((record) => !existing.has(record.id));
    state.records[appId] = incoming.concat(state.records[appId]).slice(0, MAX_RECORDS);
    const saved = saveState();
    announceChange(appId);
    refreshPanel(panel, appId, "Импортировано новых записей: " + incoming.length + (saved ? "." : ". Хранилище недоступно."));
  }).catch((error) => setStatus(panel, error.message || "Не удалось прочитать файл.", true)).finally(() => { input.value = ""; });
}

function handleQuickAction(button) {
  const appId = button.closest("[data-suite-app]")?.dataset.suiteApp;
  const panel = button.closest("[data-suite-app]");
  if (!appId || !panel) return false;
  if (button.dataset.suiteOpen) {
    window.dispatchEvent(new CustomEvent("mora:open-app", { detail: { appId: button.dataset.suiteOpen } }));
    return true;
  }
  if (button.dataset.suiteAction === "breath") {
    const existing = breathTimers.get(appId);
    if (existing) {
      clearInterval(existing);
      breathTimers.delete(appId);
      const status = panel.querySelector("[data-breath-status]");
      if (status) status.textContent = "Сессия остановлена. Можно вернуться позже.";
      button.textContent = "Начать снова";
      return true;
    }
    const phases = [{ name: "Вдох", seconds: 4 }, { name: "Пауза", seconds: 4 }, { name: "Выдох", seconds: 6 }];
    let elapsed = 0;
    const interval = setInterval(() => {
      if (!panel.isConnected) {
        clearInterval(interval);
        breathTimers.delete(appId);
        return;
      }
      elapsed += 1;
      if (elapsed >= 42) {
        clearInterval(interval);
        breathTimers.delete(appId);
        const status = panel.querySelector("[data-breath-status]");
        if (status) status.textContent = "Практика завершена. Можно остановиться здесь.";
        const toggle = panel.querySelector('[data-suite-action="breath"]');
        if (toggle) toggle.textContent = "Начать снова";
        return;
      }
      const position = elapsed % 14;
      const phase = position < 4 ? phases[0] : position < 8 ? phases[1] : phases[2];
      const offset = position < 4 ? position : position < 8 ? position - 4 : position - 8;
      const status = panel.querySelector("[data-breath-status]");
      if (status) status.textContent = phase.name + " · " + (phase.seconds - offset) + " сек. Осталось " + (42 - elapsed) + " сек.";
    }, 1000);
    breathTimers.set(appId, interval);
    const status = panel.querySelector("[data-breath-status]");
    if (status) status.textContent = "Вдох · 4 сек. Практика длится 42 секунды.";
    button.textContent = "Остановить";
    return true;
  }
  if (button.dataset.suiteAction === "send-rest") {
    createRecord("verba-rest", {
      activity: "Дыхательная пауза из NuraCalm",
      duration: 2,
      date: new Date().toISOString().slice(0, 10),
      note: "Добавлено вручную через Mora Personal Suite."
    });
    setStatus(panel, "Пауза добавлена в журнал VerbaRest.");
    return true;
  }
  if (button.dataset.suiteAction === "send-shopping") {
    const latest = loadState().records["olea-kitchen"][0];
    if (!latest || !latest.fields.ingredients) {
      setStatus(panel, "Сначала сохраните рецепт с ингредиентами.", true);
      return true;
    }
    createRecord("mila-nest", {
      task: "Купить для рецепта «" + String(latest.fields.recipe || "Без названия").slice(0, 80) + "»: " + String(latest.fields.ingredients).slice(0, 400),
      owner: "Домашний список"
    });
    refreshPanel(panel, appId, "Список ингредиентов добавлен в задачи MilaNest.");
    return true;
  }
  if (button.dataset.suiteAction === "export") {
    downloadSection(appId);
    setStatus(panel, "Подготовлен JSON-экспорт только этого раздела. Проверьте файл перед передачей.");
    return true;
  }
  if (button.dataset.suiteAction === "delete") {
    const recordId = button.dataset.recordId;
    if (!loadState().records[appId].some((record) => record.id === recordId) || !window.confirm("Удалить эту запись из локального профиля?")) return true;
    const state = loadState();
    state.records[appId] = state.records[appId].filter((record) => record.id !== recordId);
    saveState();
    announceChange(appId);
    refreshPanel(panel, appId, "Запись удалена.");
    return true;
  }
  if (button.dataset.suiteAction === "toggle-done") {
    const record = loadState().records[appId].find((item) => item.id === button.dataset.recordId);
    if (!record) return true;
    record.done = !record.done;
    saveState();
    announceChange(appId);
    refreshPanel(panel, appId, "Состояние записи обновлено.");
    return true;
  }
  return false;
}

export function installPersonalSuite() {
  if (window.__moraPersonalSuiteInstalled) return;
  window.__moraPersonalSuiteInstalled = true;
  document.addEventListener("submit", handleSubmit);
  document.addEventListener("click", (event) => {
    const button = event.target.closest?.("[data-suite-action], [data-suite-open]");
    if (button && handleQuickAction(button)) event.stopPropagation();
  });
  document.addEventListener("change", (event) => {
    const input = event.target.closest?.("[data-suite-import]");
    if (input) importSection(input);
  });
  document.addEventListener("input", (event) => {
    const search = event.target.closest?.('[data-suite-search="bela-notes"]');
    if (!search) return;
    const panel = search.closest("[data-suite-app]");
    if (panel) {
      const app = PERSONAL_SUITE_APPS.find((item) => item.id === "bela-notes");
      const records = loadState().records["bela-notes"];
      panel.querySelector('[data-suite-records="bela-notes"]').innerHTML = renderRecords(app, records);
    }
  });
}
