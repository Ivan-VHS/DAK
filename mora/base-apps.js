export const BASE_APP_DEFINITIONS = {
  deskline: { name: "Deskline", subtitle: "Пульт рабочего пространства", glyph: "⌘", category: "system" },
  nuvault: { name: "Nuvault", subtitle: "Локальный каталог файлов", glyph: "▤", category: "files" },
  daymark: { name: "Daymark", subtitle: "Задачи и приоритеты", glyph: "✓", category: "productivity" },
  lexora: { name: "Lexora", subtitle: "Текстовый редактор", glyph: "¶", category: "documents" },
  relay: { name: "Relay", subtitle: "Локальная адресная книга", glyph: "↗", category: "communication" },
  wayline: { name: "Wayline", subtitle: "Закладки и чтение", glyph: "⌖", category: "internet" },
  sumora: { name: "Sumora", subtitle: "Личный учёт доходов и расходов", glyph: "₴", category: "finance" },
  pixora: { name: "Pixora", subtitle: "Галерея выбранных изображений", glyph: "▧", category: "multimedia" },
  nexcode: { name: "Nexcode", subtitle: "Инструменты разработчика", glyph: "⌘", category: "development" },
  mnemo: { name: "Mnemo", subtitle: "Карточки для обучения", glyph: "◇", category: "education" },
  calcora: { name: "Calcora", subtitle: "Инженерный калькулятор", glyph: "∑", category: "utilities" },
  paceforge: { name: "Paceforge", subtitle: "Дневник активности", glyph: "↗", category: "health" },
  trailmark: { name: "Trailmark", subtitle: "Планировщик маршрутов", glyph: "➤", category: "travel" }
};

export const BASE_APP_IDS = Object.freeze(Object.keys(BASE_APP_DEFINITIONS));
const STORAGE_PREFIX = "duckos.mora.base-app.";
const MAX_RECORDS = 200;
const MAX_TEXT = 500;

function storageKey(appId) {
  return STORAGE_PREFIX + appId + ".v1";
}

function readRecords(appId) {
  try {
    const parsed = JSON.parse(localStorage.getItem(storageKey(appId)) || "[]");
    return Array.isArray(parsed)
      ? parsed.filter((item) => item && typeof item === "object").slice(0, MAX_RECORDS)
      : [];
  } catch {
    return [];
  }
}

function writeRecords(appId, records) {
  try {
    localStorage.setItem(storageKey(appId), JSON.stringify(records.slice(0, MAX_RECORDS)));
    return true;
  } catch {
    return false;
  }
}

function makeElement(documentRef, tag, className, text) {
  const element = documentRef.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function addRemoveButton(documentRef, item, appId, index) {
  const button = makeElement(documentRef, "button", "extension-entry-remove", "Удалить");
  button.type = "button";
  button.dataset.baseAction = "remove";
  button.dataset.baseApp = appId;
  button.dataset.baseIndex = String(index);
  button.setAttribute("aria-label", "Удалить запись");
  item.appendChild(button);
}

function renderRecords(root, appId) {
  const list = root.querySelector("[data-base-list]");
  if (!list) return;
  const documentRef = root.ownerDocument;
  const records = readRecords(appId);
  list.replaceChildren();

  if (records.length === 0) {
    list.appendChild(makeElement(documentRef, "li", "extension-empty", "Пока нет записей. Данные хранятся локально в профиле Mora."));
  }

  if (appId === "sumora") {
    const income = records.filter((item) => item.kind === "income").reduce((sum, item) => sum + item.amount, 0);
    const expenses = records.filter((item) => item.kind === "expense").reduce((sum, item) => sum + item.amount, 0);
    const summary = root.querySelector("[data-sumora-summary]");
    if (summary) summary.textContent = "Доходы: " + income.toFixed(2) + " ₴ · Расходы: " + expenses.toFixed(2) + " ₴ · Остаток: " + (income - expenses).toFixed(2) + " ₴";
  }

  if (appId === "paceforge") {
    const minutes = records.reduce((sum, item) => sum + item.minutes, 0);
    const summary = root.querySelector("[data-paceforge-summary]");
    if (summary) summary.textContent = "Занесено активности: " + minutes + " мин · " + records.length + " записей";
  }

  records.forEach((record, index) => {
    const item = makeElement(documentRef, "li", "extension-entry");
    if (appId === "daymark") {
      const toggle = makeElement(documentRef, "button", "base-task-toggle", record.done ? "✓" : "○");
      toggle.type = "button";
      toggle.dataset.baseAction = "toggle";
      toggle.dataset.baseApp = appId;
      toggle.dataset.baseIndex = String(index);
      toggle.setAttribute("aria-label", record.done ? "Вернуть задачу в работу" : "Отметить задачу выполненной");
      const value = makeElement(documentRef, "span", "extension-entry-text", record.text);
      if (record.done) value.classList.add("base-entry-done");
      item.append(toggle, value);
    } else if (appId === "wayline") {
      const link = makeElement(documentRef, "a", "extension-entry-text", record.label || record.url);
      let safeUrl = null;
      try {
        const parsed = new URL(record.url);
        if (["http:", "https:"].includes(parsed.protocol)) safeUrl = parsed.href;
      } catch {}
      if (!safeUrl) {
        item.appendChild(makeElement(documentRef, "span", "extension-entry-text", "Недопустимая или повреждённая ссылка"));
      } else {
        link.href = safeUrl;
        item.appendChild(link);
      }
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    } else if (appId === "mnemo") {
      const copy = makeElement(documentRef, "div", "base-card-copy");
      copy.appendChild(makeElement(documentRef, "strong", "", record.question));
      const answer = makeElement(documentRef, "p", "", record.answer);
      answer.hidden = true;
      answer.dataset.baseAnswer = "true";
      copy.appendChild(answer);
      const reveal = makeElement(documentRef, "button", "extension-entry-remove", "Ответ");
      reveal.type = "button";
      reveal.dataset.baseAction = "flip";
      reveal.dataset.baseIndex = String(index);
      reveal.dataset.baseApp = appId;
      item.append(copy, reveal);
    } else {
      let label = record.text || record.name || record.stop || record.activity || record.label || record.name || "Запись";
      if (appId === "relay") label = record.name + (record.detail ? " · " + record.detail : "");
      if (appId === "sumora") label = record.label + " · " + (record.kind === "income" ? "+" : "−") + record.amount.toFixed(2) + " ₴";
      if (appId === "paceforge") label = record.activity + " · " + record.minutes + " мин";
      if (appId === "trailmark") label = record.stop + (record.note ? " · " + record.note : "");
      if (appId === "nuvault" || appId === "pixora") {
        label = record.name + " · " + record.size.toLocaleString("ru-RU") + " байт";
      }
      item.appendChild(makeElement(documentRef, "span", "extension-entry-text", label));
    }
    addRemoveButton(documentRef, item, appId, index);
    list.appendChild(item);
  });
}

function setStatus(root, message) {
  const status = root.querySelector("[data-base-status]");
  if (status) status.textContent = message;
}

function panelShell(appId, kicker, title, description, body) {
  return '<div data-base-app="' + appId + '">' +
    '<p class="window-kicker">' + kicker + '</p><h2 class="window-heading">' + title + '</h2>' +
    '<p class="window-copy">' + description + '</p>' + body +
    '<p class="extension-status" data-base-status>Данные хранятся локально в текущем профиле браузера.</p></div>';
}

function recordList(appId) {
  return '<ul class="extension-entry-list" data-base-list="' + appId + '" aria-live="polite"></ul>';
}

export function renderBaseAppPanel(appId) {
  switch (appId) {
    case "deskline":
      return panelShell(appId, "DESKLINE · SYSTEM WORKSPACE", "Быстрый доступ к DuckOS",
        "Единая стартовая панель для повседневных инструментов Mora. Индикаторы показывают состояние браузерной оболочки, а не аппаратных служб ядра.",
        '<div class="extension-status-grid"><div class="extension-status-card"><strong>Рабочий стол Mora</strong><span>Активная браузерная оболочка</span></div><div class="extension-status-card"><strong>Хранилище приложений</strong><span>Локальные модули базового набора</span></div><div class="extension-status-card"><strong>Доступ к ОС</strong><span>Привилегированные API не подключены</span></div><div class="extension-status-card"><strong>Режим работы</strong><span>Офлайн-функции доступны без аккаунта</span></div></div><div class="approval-actions"><button class="action-button" data-app="workspace">Control</button><button class="subtle-button" data-app="security">Sentinel</button><button class="subtle-button" data-app="mora-commons">Открыть каталог</button></div>');
    case "nuvault":
      return panelShell(appId, "NUVAULT · FILE INDEX", "Локальный список файлов",
        "Выберите файлы, чтобы добавить их метаданные в личный список. Содержимое не загружается и не копируется в хранилище приложения.",
        '<label class="file-picker">Добавить файлы<input type="file" data-base-files="nuvault" multiple></label>' + recordList(appId));
    case "daymark":
      return panelShell(appId, "DAYMARK · DAILY PLANNER", "План на сегодня",
        "Добавляйте задачи, отмечайте завершённые пункты и удаляйте устаревшие. Список остаётся в этом браузерном профиле.",
        '<form class="extension-form" data-base-form="daymark"><label for="daymark-task">Новая задача</label><div class="intent-input-row"><input id="daymark-task" data-base-field="task" maxlength="160" required placeholder="Что нужно сделать?"><button class="action-button" type="submit">Добавить</button></div></form>' + recordList(appId));
    case "lexora":
      return panelShell(appId, "LEXORA · DOCUMENT STUDIO", "Текстовый документ",
        "Редактируйте текст, сохраняйте черновик локально или экспортируйте его в TXT. Автоматическая синхронизация и облачное хранилище не подключены.",
        '<textarea class="base-app-textarea" data-lexora-editor rows="10" maxlength="50000" placeholder="Начните писать…"></textarea><div class="approval-actions"><button class="action-button" data-base-action="save-document">Сохранить</button><button class="subtle-button" data-base-action="export-document">Экспорт TXT</button></div><p class="extension-status" data-lexora-count>0 слов · 0 символов</p>');
    case "relay":
      return panelShell(appId, "RELAY · CONTACT DESK", "Контакты и способы связи",
        "Собирайте имена и заметки о способе связи. Relay хранит личную адресную книгу локально и ничего не отправляет адресатам.",
        '<form class="extension-form" data-base-form="relay"><label>Новый контакт</label><div class="base-app-form-grid"><input data-base-field="name" required maxlength="80" placeholder="Имя"><input data-base-field="detail" maxlength="120" placeholder="Телефон, email или заметка"></div><button class="action-button" type="submit">Сохранить контакт</button></form>' + recordList(appId));
    case "wayline":
      return panelShell(appId, "WAYLINE · WEB LIBRARY", "Избранные страницы",
        "Сохраняйте HTTPS- и HTTP-адреса, добавляйте понятные подписи и открывайте сайты во внешней вкладке браузера.",
        '<form class="extension-form" data-base-form="wayline"><label>Новая закладка</label><div class="base-app-form-grid"><input data-base-field="label" maxlength="100" placeholder="Название страницы"><input data-base-field="url" type="url" required maxlength="2048" placeholder="https://example.com"></div><button class="action-button" type="submit">Добавить закладку</button></form>' + recordList(appId));
    case "sumora":
      return panelShell(appId, "SUMORA · PERSONAL LEDGER", "Доходы и расходы",
        "Ведите простой локальный журнал поступлений и затрат. Суммы вводятся вручную; банковские счета, платежи и финансовые рекомендации не подключены.",
        '<form class="extension-form" data-base-form="sumora"><label>Новая операция</label><div class="base-app-form-grid"><input data-base-field="label" required maxlength="100" placeholder="Описание"><input data-base-field="amount" type="number" min="0.01" max="100000000" step="0.01" required placeholder="Сумма ₴"><select data-base-field="kind"><option value="expense">Расход</option><option value="income">Доход</option></select></div><button class="action-button" type="submit">Добавить операцию</button></form><div class="setting-block" data-sumora-summary>Доходы: 0.00 ₴ · Расходы: 0.00 ₴ · Остаток: 0.00 ₴</div>' + recordList(appId));
    case "pixora":
      return panelShell(appId, "PIXORA · IMAGE DESK", "Выбранные изображения",
        "Просматривайте изображения, выбранные вручную. Файлы остаются на исходном носителе; в журнале сохраняются только имена и метаданные.",
        '<label class="file-picker">Выбрать изображения<input type="file" data-base-images="pixora" accept="image/*" multiple></label><div class="base-image-preview" data-base-image-preview aria-live="polite"></div>' + recordList(appId));
    case "nexcode":
      return panelShell(appId, "NEXCODE · DEVELOPER TOOLS", "Форматирование JSON",
        "Вставьте JSON, чтобы проверить синтаксис и привести структуру к читаемому виду. Код не исполняется и не отправляется в сеть.",
        '<textarea class="base-app-textarea base-code-textarea" data-nexcode-editor rows="10" spellcheck="false" placeholder="{ &quot;hello&quot;: &quot;DuckOS&quot; }"></textarea><div class="approval-actions"><button class="action-button" data-base-action="format-json">Проверить и форматировать</button></div><p class="extension-status" data-nexcode-status>Ожидает JSON.</p>');
    case "mnemo":
      return panelShell(appId, "MNEMO · STUDY CARDS", "Карточки обучения",
        "Создавайте пары «вопрос — ответ» и проверяйте себя, открывая ответ после попытки вспомнить материал.",
        '<form class="extension-form" data-base-form="mnemo"><label>Новая карточка</label><div class="base-app-form-grid"><input data-base-field="question" required maxlength="180" placeholder="Вопрос или термин"><input data-base-field="answer" required maxlength="400" placeholder="Ответ или объяснение"></div><button class="action-button" type="submit">Создать карточку</button></form>' + recordList(appId));
    case "calcora":
      return panelShell(appId, "CALCORA · SAFE CALCULATOR", "Калькулятор выражений",
        "Поддерживаются числа, скобки, десятичные дроби и операции +, −, ×, ÷, %. Выражение разбирается безопасным парсером, без исполнения JavaScript.",
        '<form class="extension-form" data-base-form="calcora"><label for="calcora-expression">Выражение</label><div class="intent-input-row"><input id="calcora-expression" data-base-expression maxlength="120" required placeholder="(12 + 8) * 3"><button class="action-button" type="submit">Вычислить</button></div></form><div class="inspection-report" data-calcora-result>Результат появится здесь.</div>');
    case "paceforge":
      return panelShell(appId, "PACEFORGE · ACTIVITY LOG", "Журнал активности",
        "Записывайте движение, тренировки и их длительность. Это дневник личной активности, а не медицинская оценка или рекомендация по нагрузке.",
        '<form class="extension-form" data-base-form="paceforge"><label>Новая запись</label><div class="base-app-form-grid"><input data-base-field="activity" required maxlength="100" placeholder="Вид активности"><input data-base-field="minutes" type="number" min="1" max="1440" step="1" required placeholder="Минуты"></div><button class="action-button" type="submit">Добавить запись</button></form><div class="setting-block" data-paceforge-summary>Занесено активности: 0 мин · 0 записей</div>' + recordList(appId));
    case "trailmark":
      return panelShell(appId, "TRAILMARK · ROUTE PLANNER", "План поездки",
        "Составляйте последовательность остановок и личные заметки к ним. GPS, онлайн-карты, прогноз времени и навигация не подключены.",
        '<form class="extension-form" data-base-form="trailmark"><label>Добавить остановку</label><div class="base-app-form-grid"><input data-base-field="stop" required maxlength="120" placeholder="Название места"><input data-base-field="note" maxlength="180" placeholder="Заметка или ориентир"></div><button class="action-button" type="submit">Добавить точку</button></form>' + recordList(appId));
    default:
      return null;
  }
}

function renderFilePreview(root, files) {
  const preview = root.querySelector("[data-base-image-preview]");
  if (!preview) return;
  preview.replaceChildren();
  const documentRef = root.ownerDocument;
  for (const file of files.slice(0, 8)) {
    const figure = makeElement(documentRef, "figure", "base-image-figure");
    const image = makeElement(documentRef, "img", "", "");
    image.alt = file.name;
    const url = URL.createObjectURL(file);
    image.src = url;
    image.addEventListener("load", () => URL.revokeObjectURL(url), { once: true });
    image.addEventListener("error", () => URL.revokeObjectURL(url), { once: true });
    figure.append(image, makeElement(documentRef, "figcaption", "", file.name));
    preview.appendChild(figure);
  }
}

function makeRecordId() {
  return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
}

function addRecord(root, appId, record) {
  const records = readRecords(appId);
  if (records.length >= MAX_RECORDS) {
    setStatus(root, "Достигнут лимит в 200 записей.");
    return;
  }
  records.unshift({ id: makeRecordId(), ...record, createdAt: new Date().toISOString() });
  if (!writeRecords(appId, records)) {
    setStatus(root, "Не удалось сохранить данные: локальное хранилище недоступно или заполнено.");
    return;
  }
  renderRecords(root, appId);
  setStatus(root, "Сохранено локально.");
}

function submitBaseForm(root, form) {
  const appId = form.dataset.baseForm;
  const value = (name) => {
    const field = form.querySelector('[data-base-field="' + name + '"]');
    return field ? field.value.trim() : "";
  };
  if (appId === "daymark") {
    const text = value("task");
    if (text) addRecord(root, appId, { text: text.slice(0, MAX_TEXT), done: false });
  } else if (appId === "relay") {
    const name = value("name");
    if (name) addRecord(root, appId, { name: name.slice(0, 80), detail: value("detail").slice(0, 120) });
  } else if (appId === "wayline") {
    const rawUrl = value("url");
    try {
      const parsed = new URL(rawUrl);
      if (!["http:", "https:"].includes(parsed.protocol)) throw new Error("Недопустимый протокол");
      addRecord(root, appId, { label: value("label").slice(0, 100) || parsed.hostname, url: parsed.href });
    } catch {
      setStatus(root, "Введите корректную ссылку с http:// или https://.");
      return;
    }
  } else if (appId === "sumora") {
    const amount = Number(value("amount"));
    const kind = value("kind");
    if (!Number.isFinite(amount) || amount <= 0 || amount > 100000000 || !["income", "expense"].includes(kind)) {
      setStatus(root, "Проверьте сумму и тип операции.");
      return;
    }
    addRecord(root, appId, { label: value("label").slice(0, 100), amount, kind });
  } else if (appId === "mnemo") {
    const question = value("question");
    const answer = value("answer");
    if (question && answer) addRecord(root, appId, { question: question.slice(0, 180), answer: answer.slice(0, 400) });
  } else if (appId === "paceforge") {
    const minutes = Number(value("minutes"));
    if (!Number.isInteger(minutes) || minutes < 1 || minutes > 1440) {
      setStatus(root, "Укажите длительность от 1 до 1440 минут.");
      return;
    }
    const activity = value("activity");
    if (activity) addRecord(root, appId, { activity: activity.slice(0, 100), minutes });
  } else if (appId === "trailmark") {
    const stop = value("stop");
    if (stop) addRecord(root, appId, { stop: stop.slice(0, 120), note: value("note").slice(0, 180) });
  }
  form.reset();
}

export function calculateExpression(source) {
  const input = String(source).replace(/\s+/g, "");
  if (!input || input.length > 120) throw new Error("Введите выражение длиной до 120 символов.");
  const tokens = [];
  const pattern = /(?:\d+(?:\.\d*)?|\.\d+)|[()+*\/%-]/y;
  let offset = 0;
  while (offset < input.length) {
    pattern.lastIndex = offset;
    const match = pattern.exec(input);
    if (!match) throw new Error("Недопустимый символ или формат числа.");
    tokens.push(match[0]);
    offset = pattern.lastIndex;
  }
  let cursor = 0;
  function primary() {
    const token = tokens[cursor++];
    if (token === "+" || token === "-") {
      const value = primary();
      return token === "-" ? -value : value;
    }
    if (token === "(") {
      const value = expression();
      if (tokens[cursor++] !== ")") throw new Error("Не закрыта скобка.");
      return value;
    }
    if (token === undefined || !/^\d|^\./.test(token)) throw new Error("Ожидалось число.");
    const value = Number(token);
    if (!Number.isFinite(value)) throw new Error("Число вне допустимого диапазона.");
    return value;
  }
  function term() {
    let value = primary();
    while (["*", "/", "%"].includes(tokens[cursor])) {
      const operator = tokens[cursor++];
      const right = primary();
      if ((operator === "/" || operator === "%") && right === 0) throw new Error("Деление на ноль запрещено.");
      value = operator === "*" ? value * right : operator === "/" ? value / right : value % right;
    }
    return value;
  }
  function expression() {
    let value = term();
    while (tokens[cursor] === "+" || tokens[cursor] === "-") {
      const operator = tokens[cursor++];
      const right = term();
      value = operator === "+" ? value + right : value - right;
    }
    return value;
  }
  const result = expression();
  if (cursor !== tokens.length) throw new Error("Проверьте порядок операций и скобки.");
  if (!Number.isFinite(result)) throw new Error("Результат вне допустимого диапазона.");
  return Number(result.toPrecision(12));
}

function saveLexora(root, exportFile) {
  const editor = root.querySelector("[data-lexora-editor]");
  const text = editor ? editor.value : "";
  try {
    localStorage.setItem(STORAGE_PREFIX + "lexora.document.v1", text);
    const count = root.querySelector("[data-lexora-count]");
    if (count) count.textContent = text.trim().split(/\s+/).filter(Boolean).length + " слов · " + text.length + " символов";
    setStatus(root, "Документ сохранён в текущем профиле браузера.");
  } catch {
    setStatus(root, "Не удалось сохранить документ: локальное хранилище недоступно или заполнено.");
    return;
  }
  if (exportFile) {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = root.ownerDocument.createElement("a");
    link.href = url;
    link.download = "lexora-document.txt";
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

export function initializeBaseAppPanel(appWindow) {
  const appId = appWindow.dataset.window;
  const root = appWindow.querySelector("[data-base-app]");
  if (!root || !BASE_APP_DEFINITIONS[appId]) return;

  if (appId === "lexora") {
    const editor = root.querySelector("[data-lexora-editor]");
    try {
      editor.value = localStorage.getItem(STORAGE_PREFIX + "lexora.document.v1") || "";
    } catch {
      setStatus(root, "Хранилище браузера недоступно; документ работает только в памяти.");
    }
    const count = root.querySelector("[data-lexora-count]");
    if (count) count.textContent = editor.value.trim().split(/\s+/).filter(Boolean).length + " слов · " + editor.value.length + " символов";
    editor.addEventListener("input", () => {
      if (count) count.textContent = editor.value.trim().split(/\s+/).filter(Boolean).length + " слов · " + editor.value.length + " символов";
    });
  }

  if (appId === "nexcode") {
    const editor = root.querySelector("[data-nexcode-editor]");
    try {
      editor.value = localStorage.getItem(STORAGE_PREFIX + "nexcode.source.v1") || "";
    } catch {
      setStatus(root, "Хранилище браузера недоступно.");
    }
  }

  renderRecords(root, appId);

  root.addEventListener("submit", (event) => {
    const form = event.target.closest("[data-base-form]");
    if (!form) return;
    event.preventDefault();
    if (form.dataset.baseForm === "calcora") {
      const input = root.querySelector("[data-base-expression]");
      const output = root.querySelector("[data-calcora-result]");
      try {
        output.textContent = calculateExpression(input.value);
        setStatus(root, "Вычисление выполнено локально.");
      } catch (error) {
        output.textContent = error.message;
        setStatus(root, "Проверьте выражение.");
      }
      return;
    }
    submitBaseForm(root, form);
  });

  root.addEventListener("click", (event) => {
    const action = event.target.closest("[data-base-action]");
    if (!action) return;
    const actionName = action.dataset.baseAction;
    if (actionName === "remove" || actionName === "toggle" || actionName === "flip") {
      const targetApp = action.dataset.baseApp || appId;
      const index = Number(action.dataset.baseIndex);
      const records = readRecords(targetApp);
      if (!Number.isInteger(index) || index < 0 || index >= records.length) return;
      if (actionName === "remove") records.splice(index, 1);
      if (actionName === "toggle" && targetApp === "daymark") records[index].done = !records[index].done;
      if (actionName === "flip" && targetApp === "mnemo") {
        const answer = action.closest(".extension-entry")?.querySelector("[data-base-answer]");
        if (answer) answer.hidden = !answer.hidden;
        action.textContent = answer && !answer.hidden ? "Скрыть" : "Ответ";
        return;
      }
      if (!writeRecords(targetApp, records)) {
        setStatus(root, "Не удалось обновить локальные данные.");
        return;
      }
      renderRecords(root, targetApp);
      setStatus(root, actionName === "remove" ? "Запись удалена." : "Состояние обновлено.");
      return;
    }
    if (actionName === "save-document") {
      saveLexora(root, false);
      return;
    }
    if (actionName === "export-document") {
      saveLexora(root, true);
      return;
    }
    if (actionName === "format-json") {
      const editor = root.querySelector("[data-nexcode-editor]");
      const status = root.querySelector("[data-nexcode-status]");
      try {
        const parsed = JSON.parse(editor.value);
        editor.value = JSON.stringify(parsed, null, 2);
        localStorage.setItem(STORAGE_PREFIX + "nexcode.source.v1", editor.value);
        status.textContent = "Корректный JSON · отформатировано и сохранено локально.";
        setStatus(root, "Синтаксис проверен. Код не исполнялся.");
      } catch (error) {
        status.textContent = "Ошибка JSON: " + error.message;
      }
    }
  });

  root.addEventListener("change", (event) => {
    const fileInput = event.target.closest("[data-base-files], [data-base-images]");
    if (!fileInput) return;
    const files = Array.from(fileInput.files || []);
    if (!files.length) return;
    const isImages = fileInput.hasAttribute("data-base-images");
    const appTarget = isImages ? "pixora" : "nuvault";
    const allowed = files.slice(0, isImages ? 30 : 100).filter((file) => {
      if (file.size > 50 * 1024 * 1024) return false;
      return !isImages || file.type.startsWith("image/");
    });
    if (isImages) renderFilePreview(root, allowed);
    const records = readRecords(appTarget);
    for (const file of allowed) {
      if (records.length >= MAX_RECORDS) break;
      records.unshift({
        id: makeRecordId(),
        name: file.name.slice(0, 240),
        size: file.size,
        type: file.type || "unknown",
        lastModified: file.lastModified
      });
    }
    if (!writeRecords(appTarget, records)) {
      setStatus(root, "Не удалось сохранить список файлов.");
      return;
    }
    renderRecords(root, appTarget);
    setStatus(root, "Добавлено файлов: " + allowed.length + ". Содержимое не копировалось.");
  });
}
