import {
  NEWS_BOOKMARKS_KEY,
  NEWS_CACHE_KEY,
  NEWS_CATEGORIES,
  NEWS_MAX_BOOKMARKS,
  NEWS_PREFERENCES_KEY,
  buildNewsRequestUrl,
  parseNewsArticles
} from "./news-core.js";

const MIN_REQUEST_INTERVAL_MS = 5500;
const REQUEST_TIMEOUT_MS = 15000;
let lastRequestAt = 0;

function readStoredJson(key, fallback) {
  try {
    const value = JSON.parse(localStorage.getItem(key) || "null");
    return value && typeof value === "object" ? value : fallback;
  } catch {
    return fallback;
  }
}

function writeStoredJson(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

function safeText(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = value;
  return element;
}

function formatArticleDate(value) {
  if (!value) return "Время публикации не указано";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Время публикации не указано";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

function formatIssueDate(value = new Date()) {
  return new Intl.DateTimeFormat("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric"
  }).format(value);
}

function articleFromBookmark(value) {
  if (!value || typeof value !== "object" || typeof value.url !== "string") return null;
  const articles = parseNewsArticles({ articles: [value] });
  return articles[0] || null;
}

function newsMarkup() {
  const tabs = NEWS_CATEGORIES.map((item) =>
    '<button class="news-category" type="button" data-news-category="' + item.id +
    '" aria-pressed="' + String(item.id === "ukraine") + '">' + item.label + "</button>"
  ).join("");

  return '<section class="newspaper-app" aria-label="Газетная лента новостей">' +
    '<header class="newspaper-masthead">' +
      '<div class="newspaper-overline"><span>НЕЗАВИСИМАЯ ЛЕНТА СОБЫТИЙ</span><span>DUCK PRESS · № 001</span></div>' +
      '<div class="newspaper-brand"><span class="newspaper-emblem" aria-hidden="true">Д</span><div><p>DUCK OS PRESENTS</p><h2>ГАЗЕТА</h2><span>НОВОСТИ · ФАКТЫ · КОНТЕКСТ</span></div></div>' +
      '<div class="newspaper-edition"><strong>ВЫПУСК ДНЯ</strong><time data-news-issue-date>' + formatIssueDate() + '</time></div>' +
    '</header>' +
    '<div class="newspaper-paper-rule" aria-hidden="true"></div>' +
    '<div class="newspaper-toolbar">' +
      '<div class="newspaper-section-heading"><span>ГЛАВНАЯ ПОЛОСА</span><h3>Новости дня</h3></div>' +
      '<div class="newspaper-actions"><button class="newspaper-utility" type="button" data-news-view="latest" aria-pressed="true">Лента</button>' +
      '<button class="newspaper-utility" type="button" data-news-view="saved" aria-pressed="false">Закладки <span data-news-bookmark-count>0</span></button>' +
      '<button class="newspaper-refresh" type="button" data-news-refresh><span aria-hidden="true">↻</span> Обновить</button></div>' +
    '</div>' +
    '<nav class="newspaper-categories" aria-label="Разделы газеты">' + tabs + '</nav>' +
    '<form class="newspaper-search" data-news-search-form role="search">' +
      '<label for="newspaper-search-input">ПОИСК ПО ЗАГОЛОВКАМ</label>' +
      '<input id="newspaper-search-input" type="search" maxlength="100" autocomplete="off" placeholder="Тема, событие или ключевые слова" data-news-search-input>' +
      '<button type="submit">Найти</button>' +
    '</form>' +
    '<div class="newspaper-status" data-news-status role="status" aria-live="polite">Подключаем мировую ленту…</div>' +
    '<div class="newspaper-feed" data-news-feed aria-live="polite"></div>' +
    '<footer class="newspaper-footer"><span>ИСТОЧНИКИ: GDELT DOC 2.0 · МАТЕРИАЛЫ ОТКРЫТЫХ ИЗДАНИЙ</span>' +
      '<span>ОТКРОЙТЕ ОРИГИНАЛЬНУЮ ПУБЛИКАЦИЮ ДЛЯ ПОЛНОГО ТЕКСТА</span></footer>' +
    '<p class="newspaper-disclaimer">Агрегатор показывает заголовки, источник и время публикации. Редакционный отбор и проверка утверждений не выполняются; содержание и достоверность материалов принадлежат их издателям.</p>' +
  '</section>';
}

export function newsPanelMarkup() {
  return newsMarkup();
}

function renderEmpty(feed, title, description) {
  feed.replaceChildren();
  const empty = safeText("div", "newspaper-empty", "");
  empty.appendChild(safeText("strong", "", title));
  empty.appendChild(safeText("p", "", description));
  feed.appendChild(empty);
}

function renderNewsArticles(feed, articles, bookmarks, savedView, status) {
  feed.replaceChildren();
  if (!articles.length) {
    renderEmpty(
      feed,
      savedView ? "Пока нет сохранённых материалов" : "Подходящих публикаций не найдено",
      savedView ? "Сохраняйте статьи значком закладки — они останутся в этом профиле." :
        "Попробуйте другую рубрику или более короткий поисковый запрос."
    );
    return;
  }

  const fragment = document.createDocumentFragment();
  articles.forEach((article, index) => {
    const card = safeText("article", "newspaper-story" + (index === 0 && !savedView ? " newspaper-story-lead" : ""));
    card.dataset.articleId = article.id;
    if (article.image) {
      const image = document.createElement("img");
      image.className = "newspaper-story-image";
      image.alt = "";
      image.loading = "lazy";
      image.crossOrigin = "anonymous";
      image.referrerPolicy = "no-referrer";
      image.src = article.image;
      image.addEventListener("error", () => image.remove(), { once: true });
      card.appendChild(image);
    }

    const copy = safeText("div", "newspaper-story-copy", "");
    const meta = safeText("div", "newspaper-story-meta", "");
    meta.appendChild(safeText("span", "newspaper-source", article.domain));
    meta.appendChild(safeText("time", "newspaper-date", formatArticleDate(article.seenAt)));
    copy.appendChild(meta);

    const heading = document.createElement("h4");
    const link = safeText("a", "newspaper-story-link", article.title);
    link.href = article.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer nofollow";
    link.referrerPolicy = "no-referrer";
    heading.appendChild(link);
    copy.appendChild(heading);

    const facts = safeText("div", "newspaper-story-facts", "");
    const country = article.sourceCountry ? article.sourceCountry.toUpperCase() : "";
    const language = article.language ? article.language.toUpperCase() : "";
    facts.textContent = [country, language].filter(Boolean).join(" · ");
    copy.appendChild(facts);

    const controls = safeText("div", "newspaper-story-controls", "");
    const saved = bookmarks.has(article.id);
    const save = safeText("button", "newspaper-save", saved ? "★ Сохранено" : "☆ Сохранить");
    save.type = "button";
    save.dataset.newsBookmark = article.id;
    save.setAttribute("aria-pressed", String(saved));
    save.setAttribute("aria-label", (saved ? "Убрать из закладок: " : "Сохранить статью: ") + article.title);
    controls.appendChild(save);

    const source = safeText("a", "newspaper-open-source", "Читать в источнике ↗");
    source.href = article.url;
    source.target = "_blank";
    source.rel = "noopener noreferrer nofollow";
    source.referrerPolicy = "no-referrer";
    controls.appendChild(source);
    copy.appendChild(controls);
    card.appendChild(copy);
    fragment.appendChild(card);
  });
  feed.appendChild(fragment);
}

export function initializeNewsPanel(appWindow) {
  const root = appWindow.querySelector(".newspaper-app");
  if (!root || root.dataset.initialized === "true") return;
  root.dataset.initialized = "true";

  const feed = root.querySelector("[data-news-feed]");
  const status = root.querySelector("[data-news-status]");
  const searchInput = root.querySelector("[data-news-search-input]");
  const refreshButton = root.querySelector("[data-news-refresh]");
  const bookmarkCount = root.querySelector("[data-news-bookmark-count]");
  const categoryTabs = [...root.querySelectorAll("[data-news-category]")];
  const viewButtons = [...root.querySelectorAll("[data-news-view]")];

  const prefs = readStoredJson(NEWS_PREFERENCES_KEY, {});
  let activeCategory = NEWS_CATEGORIES.some((item) => item.id === prefs.category) ? prefs.category : "ukraine";
  let currentView = "latest";
  let currentSearch = "";
  let requestSequence = 0;
  const rawCache = readStoredJson(NEWS_CACHE_KEY, {});
  let cached = Object.fromEntries(Object.entries(rawCache)
    .filter(([key, value]) => /^(ukraine|dnipro|world|technology|business|science):/.test(key) && Array.isArray(value))
    .map(([key, value]) => [key, parseNewsArticles({ articles: value })]));
  let bookmarks = new Map();
  const storedBookmarks = readStoredJson(NEWS_BOOKMARKS_KEY, []);
  const bookmarkItems = Array.isArray(storedBookmarks)
    ? storedBookmarks.map(articleFromBookmark).filter(Boolean).slice(0, NEWS_MAX_BOOKMARKS)
    : [];
  bookmarkItems.forEach((article) => bookmarks.set(article.id, article));

  function persistBookmarks() {
    const saved = writeStoredJson(NEWS_BOOKMARKS_KEY, [...bookmarks.values()].slice(0, NEWS_MAX_BOOKMARKS));
    bookmarkCount.textContent = String(bookmarks.size);
    return saved;
  }

  function activeCacheKey() {
    return activeCategory + ":" + currentSearch.toLowerCase();
  }

  function syncControls() {
    categoryTabs.forEach((button) => {
      const active = button.dataset.newsCategory === activeCategory;
      button.setAttribute("aria-pressed", String(active));
    });
    viewButtons.forEach((button) => {
      const active = button.dataset.newsView === currentView;
      button.setAttribute("aria-pressed", String(active));
    });
    bookmarkCount.textContent = String(bookmarks.size);
    refreshButton.disabled = currentView === "saved";
    if (currentView === "saved") refreshButton.classList.remove("is-loading");
  }

  function render() {
    syncControls();
    if (currentView === "saved") {
      renderNewsArticles(feed, [...bookmarks.values()], bookmarks, true, status);
      status.textContent = bookmarks.size ? "Сохранено в этом профиле браузера · " + bookmarks.size + " материалов." :
        "Ваш персональный газетный архив пока пуст.";
      return;
    }
    const articles = Array.isArray(cached[activeCacheKey()]) ? cached[activeCacheKey()] : [];
    renderNewsArticles(feed, articles, bookmarks, false, status);
  }

  function setStatus(message, isError = false) {
    status.textContent = message;
    status.classList.toggle("is-error", isError);
  }

  async function loadNews() {
    if (currentView === "saved") return;
    const sequence = ++requestSequence;
    const key = activeCacheKey();
    const available = cached[key];
    if (Array.isArray(available) && available.length) {
      renderNewsArticles(feed, available, bookmarks, false, status);
      setStatus("Показаны сохранённые результаты · " + available.length + " публикаций.");
    } else {
      renderEmpty(feed, "Подбираем публикации", "Получаем свежие заголовки из выбранного раздела.");
      setStatus("Обращаемся к открытой новостной базе GDELT…");
    }

    const elapsed = Date.now() - lastRequestAt;
    if (lastRequestAt > 0 && elapsed < MIN_REQUEST_INTERVAL_MS) {
      const wait = Math.ceil((MIN_REQUEST_INTERVAL_MS - elapsed) / 1000);
      refreshButton.disabled = false;
      refreshButton.classList.remove("is-loading");
      setStatus("Источник ограничивает частоту запросов. Повторите обновление через " + wait + " сек.", true);
      return;
    }

    lastRequestAt = Date.now();
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    refreshButton.disabled = true;
    refreshButton.classList.add("is-loading");
    try {
      const response = await fetch(buildNewsRequestUrl(activeCategory, currentSearch), {
        method: "GET",
        headers: { Accept: "application/json" },
        cache: "no-store",
        credentials: "omit",
        referrerPolicy: "no-referrer",
        signal: controller.signal
      });
      if (!response.ok) throw new Error("Сервер новостей ответил с кодом " + response.status + ".");
      const payload = await response.json();
      if (sequence !== requestSequence) return;
      const articles = parseNewsArticles(payload);
      cached[key] = articles;
      const cacheKeys = Object.keys(cached);
      while (cacheKeys.length > 8) delete cached[cacheKeys.shift()];
      if (!writeStoredJson(NEWS_CACHE_KEY, cached)) {
        setStatus("Получено " + articles.length + " публикаций; кеширование недоступно.", true);
      } else {
        setStatus("Обновлено " + formatIssueDate(new Date()) + " · " + articles.length + " публикаций.");
      }
      renderNewsArticles(feed, articles, bookmarks, false, status);
    } catch (error) {
      if (sequence !== requestSequence) return;
      const fallback = Array.isArray(cached[key]) ? cached[key] : [];
      if (fallback.length) {
        renderNewsArticles(feed, fallback, bookmarks, false, status);
        setStatus("Не удалось обновить источник. Показана последняя сохранённая выдача.", true);
      } else {
        renderEmpty(feed, "Лента временно недоступна", "Проверьте соединение и повторите запрос. Закладки и уже сохранённые результаты останутся доступны.");
        setStatus(error.name === "AbortError" ? "Время ожидания источника истекло." : error.message || "Ошибка получения новостей.", true);
      }
    } finally {
      window.clearTimeout(timeout);
      if (sequence === requestSequence) {
        refreshButton.disabled = currentView === "saved";
        refreshButton.classList.remove("is-loading");
      }
    }
  }

  root.addEventListener("click", (event) => {
    const category = event.target.closest("[data-news-category]");
    if (category) {
      activeCategory = category.dataset.newsCategory;
      currentView = "latest";
      writeStoredJson(NEWS_PREFERENCES_KEY, { category: activeCategory });
      render();
      loadNews();
      return;
    }

    const view = event.target.closest("[data-news-view]");
    if (view) {
      requestSequence += 1;
      currentView = view.dataset.newsView === "saved" ? "saved" : "latest";
      render();
      if (currentView === "latest" && !(cached[activeCacheKey()] || []).length) loadNews();
      return;
    }

    const bookmark = event.target.closest("[data-news-bookmark]");
    if (bookmark) {
      const articleId = bookmark.dataset.newsBookmark;
      const source = [...(cached[activeCacheKey()] || []), ...bookmarks.values()]
        .find((item) => item.id === articleId);
      if (!source) return;
      if (bookmarks.has(articleId)) bookmarks.delete(articleId);
      else {
        if (bookmarks.size >= NEWS_MAX_BOOKMARKS) {
          setStatus("Достигнут предел в " + NEWS_MAX_BOOKMARKS + " закладок.", true);
          return;
        }
        bookmarks.set(articleId, source);
      }
      if (!persistBookmarks()) setStatus("Не удалось сохранить закладки: хранилище браузера недоступно.", true);
      render();
    }
  });

  root.querySelector("[data-news-search-form]").addEventListener("submit", (event) => {
    event.preventDefault();
    currentSearch = searchInput.value.trim().slice(0, 100);
    currentView = "latest";
    render();
    loadNews();
  });

  refreshButton.addEventListener("click", () => loadNews());
  root.querySelector("[data-news-issue-date]").textContent = formatIssueDate();
  render();
  loadNews();
}
