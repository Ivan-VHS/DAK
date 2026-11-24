export const NEWS_CACHE_KEY = "duckos.mora.gazette.cache.v1";
export const NEWS_BOOKMARKS_KEY = "duckos.mora.gazette.bookmarks.v1";
export const NEWS_CACHE_TTL_MS = 15 * 60 * 1000;
export const MAX_NEWS_ITEMS = 60;
export const MAX_BOOKMARKS = 200;
export const RSS_CONVERTER_ENDPOINT = "https://api.rss2json.com/v1/api.json";

export const NEWS_SOURCES = Object.freeze([
  { id: "pravda", name: "Українська правда", category: "ukraine", feed: "https://www.pravda.com.ua/rss/", home: "https://www.pravda.com.ua/" },
  { id: "suspilne", name: "Суспільне Новини", category: "ukraine", feed: "https://suspilne.media/rss/ukrnet.rss", home: "https://suspilne.media/" },
  { id: "bbc-ukraine", name: "BBC News Україна", category: "ukraine", feed: "https://feeds.bbci.co.uk/ukrainian/rss.xml", home: "https://www.bbc.com/ukrainian" },
  { id: "kyiv-independent", name: "The Kyiv Independent", category: "ukraine", feed: "https://kyivindependent.com/news-archive/rss/", home: "https://kyivindependent.com/" },
  { id: "bbc-world", name: "BBC World", category: "world", feed: "https://feeds.bbci.co.uk/news/world/rss.xml", home: "https://www.bbc.com/news/world" },
  { id: "bbc-technology", name: "BBC Technology", category: "technology", feed: "https://feeds.bbci.co.uk/news/technology/rss.xml", home: "https://www.bbc.com/news/technology" }
]);

const REQUEST_TIMEOUT_MS = 10_000;
const CONCURRENCY = 3;

export function safeArticleUrl(value) {
  try {
    const url = new URL(String(value ?? ""));
    if (!["http:", "https:"].includes(url.protocol) || url.username || url.password) return null;
    return url.href;
  } catch {
    return null;
  }
}

export function plainText(value, maxLength = 420) {
  const source = String(value ?? "");
  let output = source;
  if (typeof DOMParser === "function") {
    try {
      const parsed = new DOMParser().parseFromString(source, "text/html");
      parsed.querySelectorAll("script,style,noscript,iframe,object").forEach((node) => node.remove());
      output = parsed.body?.textContent || "";
    } catch {
      output = source;
    }
  } else {
    output = source
      .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ")
      .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " ")
      .replace(/<[^>]*>/g, " ")
      .replace(/&nbsp;|&#160;/gi, " ")
      .replace(/&amp;/gi, "&")
      .replace(/&lt;/gi, "<")
      .replace(/&gt;/gi, ">")
      .replace(/&quot;/gi, '"')
      .replace(/&#39;|&apos;/gi, "'");
    output = output.replace(/&#(\d+);/g, (_match, code) => {
      const point = Number(code);
      return Number.isInteger(point) && point >= 0 && point <= 0x10ffff ? String.fromCodePoint(point) : " ";
    });
    output = output.replace(/&#x([0-9a-f]+);/gi, (_match, code) => {
      const point = Number.parseInt(code, 16);
      return Number.isInteger(point) && point >= 0 && point <= 0x10ffff ? String.fromCodePoint(point) : " ";
    });
  }
  const limit = Number.isInteger(maxLength) ? Math.max(0, Math.min(maxLength, 4000)) : 420;
  return output.replace(/\u00a0/g, " ").replace(/\s+/g, " ").trim().slice(0, limit);
}

export function normalizeNewsItem(item, source, now = Date.now()) {
  if (!item || typeof item !== "object" || !source ||
      !NEWS_SOURCES.some((known) => known.id === source.id)) return null;
  const url = safeArticleUrl(item.link || item.url || item.guid);
  const title = plainText(item.title, 180);
  if (!url || !title) return null;
  const parsedDate = new Date(item.pubDate || item.published || item.isoDate || item.publishedAt || now);
  const publishedAt = Number.isFinite(parsedDate.getTime()) ? parsedDate.getTime() : now;
  const description = plainText(item.description || item.summary || "", 280);
  return { id: url, url, title, description, sourceId: source.id, sourceName: source.name, category: source.category, publishedAt };
}

function normalizeCachedItem(item) {
  const source = NEWS_SOURCES.find((candidate) => candidate.id === item?.sourceId);
  if (!source) return null;
  return normalizeNewsItem({
    title: item.title, link: item.url, description: item.description, publishedAt: item.publishedAt
  }, source);
}

export function normalizeBookmarkRecords(value, fallbackItems = []) {
  if (!Array.isArray(value)) return [];
  const fallbackByUrl = new Map(
    fallbackItems.filter((item) => safeArticleUrl(item?.url) === item.url).map((item) => [item.url, item])
  );
  const byUrl = new Map();
  for (const entry of value.slice(-MAX_BOOKMARKS)) {
    const item = typeof entry === "string"
      ? fallbackByUrl.get(entry) || null
      : normalizeCachedItem(entry);
    if (item) byUrl.set(item.url, item);
  }
  return [...byUrl.values()].slice(-MAX_BOOKMARKS);
}

function readCache() {
  try {
    const stored = JSON.parse(globalThis.localStorage?.getItem(NEWS_CACHE_KEY) || "null");
    if (!stored || !Array.isArray(stored.items)) return null;
    const items = stored.items.map(normalizeCachedItem).filter(Boolean).slice(0, MAX_NEWS_ITEMS);
    const fetchedAt = Number(stored.fetchedAt);
    return {
      items,
      fetchedAt: Number.isFinite(fetchedAt) && fetchedAt > 0 ? fetchedAt : 0,
      sources: Array.isArray(stored.sources) ? stored.sources.slice(0, NEWS_SOURCES.length) : []
    };
  } catch {
    return null;
  }
}

function writeCache(items, fetchedAt, sources) {
  try {
    globalThis.localStorage?.setItem(NEWS_CACHE_KEY, JSON.stringify({
      schema: "duckos.mora.gazette-cache.v1", fetchedAt, sources, items: items.slice(0, MAX_NEWS_ITEMS)
    }));
    return true;
  } catch {
    return false;
  }
}

function readBookmarks(fallbackItems = []) {
  try {
    const value = JSON.parse(globalThis.localStorage?.getItem(NEWS_BOOKMARKS_KEY) || "[]");
    return new Map(normalizeBookmarkRecords(value, fallbackItems).map((item) => [item.url, item]));
  } catch {
    return new Map();
  }
}

function writeBookmarks(bookmarks) {
  try {
    if (!globalThis.localStorage) return false;
    globalThis.localStorage.setItem(
      NEWS_BOOKMARKS_KEY,
      JSON.stringify([...bookmarks.values()].slice(0, MAX_BOOKMARKS))
    );
    return true;
  } catch {
    return false;
  }
}

async function fetchSource(source) {
  const endpoint = new URL(RSS_CONVERTER_ENDPOINT);
  endpoint.searchParams.set("rss_url", source.feed);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(endpoint.href, {
      method: "GET", headers: { Accept: "application/json" }, signal: controller.signal, cache: "no-store"
    });
    if (!response.ok) throw new Error("HTTP " + response.status);
    const payload = await response.json();
    if (payload?.status !== "ok" || !Array.isArray(payload.items)) {
      throw new Error(plainText(payload?.message || "Источник вернул некорректный ответ", 140));
    }
    const items = payload.items.map((item) => normalizeNewsItem(item, source)).filter(Boolean).slice(0, 20);
    return { ok: true, source, items };
  } finally {
    clearTimeout(timeout);
  }
}

async function mapWithLimit(values, limit, mapper) {
  const output = new Array(values.length);
  let cursor = 0;
  const workers = Array.from({ length: Math.min(limit, values.length) }, async () => {
    while (cursor < values.length) {
      const index = cursor++;
      output[index] = await mapper(values[index], index);
    }
  });
  await Promise.all(workers);
  return output;
}

function uniqueSorted(items) {
  const byUrl = new Map();
  for (const item of items) if (!byUrl.has(item.url)) byUrl.set(item.url, item);
  return [...byUrl.values()].sort((a, b) => b.publishedAt - a.publishedAt).slice(0, MAX_NEWS_ITEMS);
}

function createText(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = text;
  return node;
}

export function newsPanelMarkup() {
  const sources = NEWS_SOURCES.map((source) =>
    '<a href="' + source.home + '" target="_blank" rel="noopener noreferrer">' + source.name + '</a>'
  ).join("");
  return '<main class="gazette" data-gazette>' +
    '<div class="gazette-paper">' +
      '<header class="gazette-masthead">' +
        '<div class="gazette-topline"><span>DUCKOS PRESS · НЕЗАВИСИМАЯ ЛЕНТА</span><time data-gazette-date></time><span>ЦИФРОВОЙ ВЫПУСК</span></div>' +
        '<div class="gazette-masthead-main"><span class="gazette-emblem" aria-hidden="true">G</span>' +
          '<div class="gazette-title-wrap"><p class="gazette-overline">СОБЫТИЯ · КОНТЕКСТ · ТЕХНОЛОГИИ</p><h1>Газета <span>Gazette</span></h1></div>' +
          '<div class="gazette-edition"><strong>№ 001</strong><span>MORA EDITION</span></div>' +
        '</div><div class="gazette-masthead-rule"><span></span><b>СВЕЖИЙ ВЫПУСК</b><span></span></div>' +
      '</header>' +
      '<section class="gazette-toolbar" aria-label="Управление новостной лентой">' +
        '<label class="gazette-search"><span aria-hidden="true">⌕</span><input type="search" data-news-search placeholder="Найти публикацию…" aria-label="Поиск по заголовкам и описаниям"></label>' +
        '<div class="gazette-filters" data-news-filters aria-label="Рубрики">' +
          '<button type="button" data-news-category="all" aria-pressed="true">Все новости</button>' +
          '<button type="button" data-news-category="ukraine" aria-pressed="false">Украина</button>' +
          '<button type="button" data-news-category="world" aria-pressed="false">Мир</button>' +
          '<button type="button" data-news-category="technology" aria-pressed="false">Технологии</button>' +
          '<button type="button" data-news-category="saved" aria-pressed="false">Закладки <span data-news-saved-count>0</span></button>' +
        '</div><button class="gazette-refresh" type="button" data-news-refresh><span aria-hidden="true">↻</span> Обновить</button>' +
      '</section>' +
      '<div class="gazette-feed-meta"><p data-news-status role="status" aria-live="polite">Подключение к новостным источникам…</p><p data-news-updated>Обновлено: —</p></div>' +
      '<section class="gazette-feature" data-news-feature aria-label="Главная публикация"></section>' +
      '<div class="gazette-section-heading"><span>ПОСЛЕДНИЕ ПУБЛИКАЦИИ</span><span data-news-count>0 материалов</span></div>' +
      '<section class="gazette-grid" data-news-list aria-label="Список публикаций"></section>' +
      '<p class="gazette-empty" data-news-empty hidden>По этому запросу публикаций нет. Попробуйте другую рубрику или обновите ленту.</p>' +
      '<footer class="gazette-footer"><div class="gazette-footer-heading"><span>ИСТОЧНИКИ ВЫПУСКА</span><span>ПЕРВОИСТОЧНИКИ</span></div>' +
        '<nav class="gazette-sources" aria-label="Новостные источники">' + sources + '</nav>' +
        '<p>Заголовки и короткие описания поступают из открытых RSS-лент. Полные материалы открываются на сайтах редакций. Для преобразования RSS используется внешний сервис rss2json.com; закладки и ограниченный кэш заголовков остаются в этом профиле браузера.</p>' +
        '<div class="gazette-colophon"><span>GAZETTE · MORA DESKTOP</span><span>ЧИТАЙТЕ ПЕРВОИСТОЧНИК</span><span>DUCKOS</span></div>' +
      '</footer>' +
    '</div></main>';
}

function articleCard(item, { featured = false, bookmarked = false } = {}) {
  const card = createText("article", featured ? "gazette-lead" : "gazette-story", "");
  card.dataset.articleId = item.id;
  const top = createText("div", "gazette-story-top", "");
  top.append(
    createText("span", "gazette-category-label", ({ ukraine: "УКРАИНА", world: "МИР", technology: "ТЕХНОЛОГИИ" })[item.category] || "НОВОСТИ"),
    createText("span", "gazette-story-source", item.sourceName)
  );
  const bookmark = createText("button", "gazette-bookmark", bookmarked ? "★" : "☆");
  bookmark.type = "button";
  bookmark.dataset.newsBookmark = item.id;
  bookmark.setAttribute("aria-pressed", String(bookmarked));
  bookmark.setAttribute("aria-label", (bookmarked ? "Убрать из закладок: " : "Добавить в закладки: ") + item.title);
  top.appendChild(bookmark);

  const title = document.createElement(featured ? "h2" : "h3");
  const titleLink = createText("a", "gazette-story-title", item.title);
  titleLink.href = item.url;
  titleLink.target = "_blank";
  titleLink.rel = "noopener noreferrer";
  title.appendChild(titleLink);

  const description = createText("p", "gazette-story-description",
    item.description || "Откройте публикацию на сайте редакции, чтобы прочитать полный материал.");
  const footer = createText("div", "gazette-story-footer", "");
  const dateText = new Date(item.publishedAt).toLocaleString("ru-RU", {
    day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
  });
  footer.append(createText("time", "gazette-story-date", dateText), createText("span", "gazette-story-dot", "·"));
  const sourceLink = createText("a", "gazette-read-link", "Читать у источника ↗");
  sourceLink.href = item.url;
  sourceLink.target = "_blank";
  sourceLink.rel = "noopener noreferrer";
  footer.appendChild(sourceLink);
  card.append(top, title, description, footer);
  if (featured) card.appendChild(createText("div", "gazette-print-mark", "ГЛАВНАЯ ПОЛОСА"));
  return card;
}

export function initializeNewsPanel(appWindow, { showToast } = {}) {
  const root = appWindow.querySelector("[data-gazette]");
  if (!root) return;
  const search = root.querySelector("[data-news-search]");
  const filters = root.querySelector("[data-news-filters]");
  const refreshButton = root.querySelector("[data-news-refresh]");
  const feature = root.querySelector("[data-news-feature]");
  const list = root.querySelector("[data-news-list]");
  const empty = root.querySelector("[data-news-empty]");
  const status = root.querySelector("[data-news-status]");
  const updated = root.querySelector("[data-news-updated]");
  const count = root.querySelector("[data-news-count]");
  const savedCount = root.querySelector("[data-news-saved-count]");
  const date = root.querySelector("[data-gazette-date]");

  let cache = readCache();
  let articles = cache?.items || [];
  let bookmarks = readBookmarks(articles);
  let activeCategory = "all";
  let isLoading = false;
  let lastUpdated = cache?.fetchedAt || 0;

  if (date) date.textContent = new Date().toLocaleDateString("ru-RU", {
    weekday: "long", day: "numeric", month: "long", year: "numeric"
  }).toLocaleUpperCase("ru-RU");

  function render() {
    const query = search.value.trim().toLocaleLowerCase("ru-RU");
    const candidates = activeCategory === "saved" ? [...bookmarks.values()] : articles;
    const matches = candidates.filter((item) => {
      const categoryMatch = activeCategory === "all" ||
        activeCategory === "saved" || item.category === activeCategory;
      const searchMatch = !query ||
        (item.title + " " + item.description + " " + item.sourceName).toLocaleLowerCase("ru-RU").includes(query);
      return categoryMatch && searchMatch;
    });
    feature.replaceChildren();
    list.replaceChildren();
    if (matches.length) {
      feature.appendChild(articleCard(matches[0], { featured: true, bookmarked: bookmarks.has(matches[0].url) }));
      matches.slice(1).forEach((item) => list.appendChild(articleCard(item, { bookmarked: bookmarks.has(item.url) })));
      empty.hidden = true;
    } else {
      empty.hidden = false;
    }
    count.textContent = matches.length + (matches.length === 1 ? " материал" : " материалов");
    savedCount.textContent = String(bookmarks.size);
    updated.textContent = lastUpdated ? "Обновлено: " + new Date(lastUpdated).toLocaleString("ru-RU") : "Обновлено: —";
    filters.querySelectorAll("[data-news-category]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.newsCategory === activeCategory));
    });
  }

  async function refresh({ force = false, notify = false } = {}) {
    if (isLoading) return;
    const freshCache = cache && cache.fetchedAt && Date.now() - cache.fetchedAt < NEWS_CACHE_TTL_MS;
    if (!force && freshCache) {
      status.textContent = "Показан свежий локальный кэш. Следующее сетевое обновление — по кнопке.";
      render();
      return;
    }
    isLoading = true;
    refreshButton.disabled = true;
    refreshButton.textContent = "↻ Загружаем…";
    status.textContent = "Проверяем " + NEWS_SOURCES.length + " RSS-источников…";
    const results = await mapWithLimit(NEWS_SOURCES, CONCURRENCY, async (source) => {
      try {
        return await fetchSource(source);
      } catch (error) {
        return {
          ok: false, source,
          error: error?.name === "AbortError" ? "Тайм-аут" : plainText(error?.message || "Недоступен", 120)
        };
      }
    });
    const successful = results.filter((result) => result.ok);
    const failedIds = new Set(results.filter((result) => !result.ok).map((result) => result.source.id));
    const sourceResults = results.map((result) => ({
      id: result.source.id, name: result.source.name, ok: result.ok,
      count: result.ok ? result.items.length : 0, error: result.ok ? "" : result.error
    }));

    if (successful.length) {
      const freshItems = successful.flatMap((result) => result.items);
      const fallbackItems = (cache?.items || articles).filter((item) => failedIds.has(item.sourceId));
      articles = uniqueSorted([...freshItems, ...fallbackItems]);
      lastUpdated = Date.now();
      cache = { items: articles, sources: sourceResults, fetchedAt: lastUpdated };
      writeCache(articles, lastUpdated, sourceResults);
      status.textContent = "Подключено источников: " + successful.length + " из " + NEWS_SOURCES.length +
        (failedIds.size ? ". Для части редакций сохранены последние доступные заголовки." : ".");
    } else if (articles.length) {
      status.textContent = "Источники сейчас недоступны. Показаны последние сохранённые заголовки.";
    } else {
      status.textContent = "Не удалось получить новости. Проверьте соединение или откройте сайты редакций ниже.";
    }

    render();
    isLoading = false;
    refreshButton.disabled = false;
    refreshButton.textContent = "↻ Обновить";
    if (notify && showToast) {
      showToast(successful.length
        ? "Лента обновлена · источников: " + successful.length + "/" + NEWS_SOURCES.length
        : "Новостные источники пока недоступны");
    }
  }

  filters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-news-category]");
    if (!button) return;
    activeCategory = button.dataset.newsCategory;
    render();
  });
  search.addEventListener("input", render);
  refreshButton.addEventListener("click", () => refresh({ force: true, notify: true }));
  root.addEventListener("click", (event) => {
    const bookmark = event.target.closest("[data-news-bookmark]");
    if (!bookmark) return;
    const url = safeArticleUrl(bookmark.dataset.newsBookmark);
    if (!url) return;
    const wasBookmarked = bookmarks.has(url);
    const previousBookmark = bookmarks.get(url);
    if (wasBookmarked) bookmarks.delete(url);
    else {
      if (bookmarks.size >= MAX_BOOKMARKS) {
        status.textContent = "Достигнут предел в " + MAX_BOOKMARKS + " закладок. Удалите старые, чтобы добавить новые.";
        return;
      }
      const article = articles.find((item) => item.url === url);
      if (!article) return;
      bookmarks.set(url, article);
    }
    if (!writeBookmarks(bookmarks)) {
      if (wasBookmarked) bookmarks.set(url, previousBookmark);
      else bookmarks.delete(url);
      status.textContent = "Не удалось сохранить закладку в этом профиле браузера.";
      render();
      return;
    }
    render();
    if (showToast) showToast(bookmarks.has(url) ? "Публикация добавлена в закладки" : "Закладка удалена");
  });

  render();
  if (cache?.fetchedAt && Date.now() - cache.fetchedAt < NEWS_CACHE_TTL_MS) {
    status.textContent = "Показан свежий локальный кэш.";
  } else {
    void refresh();
  }
}
