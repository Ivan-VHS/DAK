(() => {
  "use strict";

  const API = "http://127.0.0.1:8765";
  const READ_KEY = "duckos.news.read.v1";
  const SAVED_KEY = "duckos.news.saved.v1";
  const CATEGORIES = ["Все", "Украина", "Мир", "Политика", "Экономика", "Технологии", "Наука", "Спорт", "Культура", "Другое"];

  const elements = {
    date: document.getElementById("dateLine"),
    live: document.getElementById("liveText"),
    liveWrap: document.querySelector(".live-indicator"),
    tabs: document.getElementById("tabs"),
    search: document.getElementById("searchInput"),
    unread: document.getElementById("unreadButton"),
    saved: document.getElementById("savedButton"),
    refresh: document.getElementById("refreshButton"),
    sources: document.getElementById("sourceList"),
    updated: document.getElementById("updatedAt"),
    banner: document.getElementById("statusBanner"),
    feed: document.getElementById("feed"),
    count: document.getElementById("countLine"),
    dialog: document.getElementById("articleDialog"),
    close: document.getElementById("closeArticle"),
    articleCategory: document.getElementById("articleCategory"),
    articleTitle: document.getElementById("articleTitle"),
    articleMeta: document.getElementById("articleMeta"),
    articleSummary: document.getElementById("articleSummary"),
    articleLink: document.getElementById("originalLink")
  };

  const state = {
    category: "Все",
    query: "",
    items: [],
    sources: [],
    updatedAt: null,
    read: loadSet(READ_KEY),
    saved: loadSet(SAVED_KEY),
    unreadOnly: false,
    savedOnly: false,
    loading: false,
    online: false,
    refreshSeconds: 300,
    activeArticle: null
  };

  function loadSet(key) {
    try {
      const value = JSON.parse(localStorage.getItem(key) || "[]");
      return new Set(Array.isArray(value) ? value.filter(item => typeof item === "string") : []);
    } catch {
      return new Set();
    }
  }

  function saveSet(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(Array.from(value)));
    } catch {
      // Reading the newspaper remains available when browser storage is disabled.
    }
  }

  function formatDate(value, options) {
    if (!value) return "дата не указана";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "дата не указана";
    return new Intl.DateTimeFormat("ru-RU", options || {
      day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit"
    }).format(date);
  }

  function setConnection(online, label) {
    state.online = online;
    elements.live.textContent = label;
    elements.liveWrap.classList.toggle("online", online);
  }

  function showBanner(title, message, command) {
    elements.banner.replaceChildren();
    const strong = document.createElement("strong");
    strong.textContent = title;
    const paragraph = document.createElement("span");
    paragraph.textContent = message;
    elements.banner.append(strong, paragraph);
    if (command) {
      const code = document.createElement("code");
      code.textContent = command;
      elements.banner.append(document.createElement("br"), code);
    }
    elements.banner.hidden = false;
  }

  function hideBanner() {
    elements.banner.hidden = true;
    elements.banner.replaceChildren();
  }

  async function request(path, options) {
    const response = await fetch(API + path, {
      mode: "cors",
      credentials: "omit",
      cache: "no-store",
      referrerPolicy: "no-referrer",
      ...options
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
    return payload;
  }

  function renderTabs() {
    elements.tabs.replaceChildren();
    CATEGORIES.forEach(category => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "tab";
      button.setAttribute("role", "tab");
      button.setAttribute("aria-selected", String(state.category === category));
      button.textContent = category;
      button.addEventListener("click", () => {
        state.category = category;
        renderTabs();
        loadNews();
      });
      elements.tabs.append(button);
    });
  }

  function renderSources() {
    elements.sources.replaceChildren();
    if (!state.sources.length) {
      const empty = document.createElement("span");
      empty.className = "source-chip muted";
      empty.textContent = "Источники ещё не проверены";
      elements.sources.append(empty);
      return;
    }

    state.sources.forEach(source => {
      const chip = document.createElement("span");
      chip.className = "source-chip " + (source.status === "ok" ? "ok" : "error");
      chip.title = source.error || (source.article_count + " материалов в источнике");
      chip.textContent = source.name;
      elements.sources.append(chip);
    });
  }

  function makeStory(item, index) {
    const article = document.createElement("article");
    article.className = "story" + (index === 0 ? " lead" : "");
    article.dataset.id = item.id;

    if (state.read.has(item.id)) {
      const stamp = document.createElement("span");
      stamp.className = "read-stamp";
      stamp.textContent = "ПРОЧИТАНО";
      article.append(stamp);
    }

    const open = document.createElement("button");
    open.type = "button";
    open.className = "story-open";
    open.setAttribute("aria-label", "Открыть материал: " + item.title);

    const content = document.createElement("div");
    const kicker = document.createElement("div");
    kicker.className = "kicker";
    kicker.textContent = item.category || "Новости";

    const title = document.createElement("h2");
    title.textContent = item.title;

    const deck = document.createElement("p");
    deck.className = "deck";
    deck.textContent = item.summary || "Краткий анонс не предоставлен. Откройте оригинальную публикацию.";

    const meta = document.createElement("div");
    meta.className = "byline";
    const author = item.author ? item.author + " · " : "";
    meta.textContent = author + formatDate(item.published_at);

    content.append(kicker, title, deck, meta);

    const photo = document.createElement("div");
    photo.className = "photo";
    photo.setAttribute("aria-label", "Декоративная газетная полутоновая иллюстрация");

    if (index === 0) {
      open.append(content, photo);
    } else {
      open.append(photo, content);
    }
    open.addEventListener("click", () => openArticle(item));
    article.append(open);

    const footer = document.createElement("div");
    footer.className = "story-footer";
    const source = document.createElement("span");
    source.className = "story-source";
    source.textContent = item.source || "Источник не указан";
    const favorite = document.createElement("button");
    favorite.type = "button";
    favorite.className = "favorite-button";
    favorite.textContent = state.saved.has(item.id) ? "★ В избранном" : "☆ Сохранить";
    favorite.setAttribute("aria-pressed", String(state.saved.has(item.id)));
    favorite.setAttribute("aria-label", state.saved.has(item.id) ? "Убрать из сохранённого" : "Сохранить материал");
    favorite.addEventListener("click", () => toggleSaved(item.id));
    footer.append(source, favorite);
    article.append(footer);

    return article;
  }

  function visibleItems() {
    return state.items.filter(item => {
      if (state.unreadOnly && state.read.has(item.id)) return false;
      if (state.savedOnly && !state.saved.has(item.id)) return false;
      return true;
    });
  }

  function renderFeed() {
    const items = visibleItems();
    elements.feed.replaceChildren();
    elements.feed.setAttribute("aria-busy", String(state.loading));

    if (!items.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      const icon = document.createElement("span");
      icon.className = "empty-icon";
      icon.textContent = state.savedOnly ? "★" : "📰";
      const title = document.createElement("strong");
      const note = document.createElement("small");
      if (state.loading) {
        title.textContent = "Получаем свежие материалы";
        note.textContent = "Служба опрашивает подключённые источники.";
      } else if (state.savedOnly) {
        title.textContent = "Сохранённых материалов пока нет";
        note.textContent = "Нажмите «☆ Сохранить» у интересной публикации.";
      } else if (state.unreadOnly) {
        title.textContent = "Непрочитанных материалов нет";
        note.textContent = "Вы просмотрели все материалы в этом разделе.";
      } else if (state.online) {
        title.textContent = "В этом разделе пока пусто";
        note.textContent = "Выберите другую рубрику или обновите ленту.";
      } else {
        title.textContent = "Лента пока не подключена";
        note.textContent = "Запустите локальную службу новостей DuckOS.";
      }
      empty.append(icon, title, note);
      elements.feed.append(empty);
    } else {
      items.forEach((item, index) => elements.feed.append(makeStory(item, index)));
    }

    const readCount = state.items.filter(item => state.read.has(item.id)).length;
    elements.count.textContent =
      "Источников: " + state.sources.length +
      " · Материалов: " + state.items.length +
      " · Прочитано: " + readCount +
      " · Показано: " + items.length;
  }

  function renderUpdatedAt() {
    elements.updated.textContent = state.updatedAt
      ? "Последняя синхронизация: " + formatDate(state.updatedAt)
      : "Обновление ещё не выполнено";
  }

  async function loadNews() {
    const params = new URLSearchParams({
      category: state.category,
      q: state.query,
      limit: "100"
    });
    state.loading = true;
    renderFeed();

    try {
      const payload = await request("/api/news?" + params.toString());
      state.items = Array.isArray(payload.items) ? payload.items : [];
      state.sources = Array.isArray(payload.sources) ? payload.sources : [];
      state.updatedAt = payload.updated_at || null;
      state.refreshSeconds = Math.max(60, Math.min(3600, Number(payload.refresh_seconds) || 300));
      setConnection(true, state.sources.some(source => source.status === "ok") ? "Источники активны" : "Кэш доступен");
      hideBanner();
    } catch (error) {
      setConnection(false, "Нет соединения");
      showBanner(
        "Служба новостей не отвечает",
        "Интерфейс работает, но для получения актуальных публикаций нужно запустить локальный backend.",
        "PYTHONPATH=native/services python -m duckos_services news serve"
      );
      state.sources = [];
      state.items = [];
    } finally {
      state.loading = false;
      renderSources();
      renderUpdatedAt();
      renderFeed();
    }
  }

  async function refreshNews() {
    if (state.loading && !state.online) return;
    state.refresh.disabled = true;
    state.refresh.classList.add("loading");
    try {
      await request("/api/news/refresh", { method: "POST" });
      await loadNews();
    } catch (error) {
      setConnection(false, "Нет соединения");
      showBanner(
        "Не удалось обновить ленту",
        error.message || "Локальная служба недоступна.",
        "PYTHONPATH=native/services python -m duckos_services news serve"
      );
    } finally {
      state.refresh.disabled = false;
      state.refresh.classList.remove("loading");
    }
  }

  function toggleSaved(identifier) {
    if (state.saved.has(identifier)) state.saved.delete(identifier);
    else state.saved.add(identifier);
    saveSet(SAVED_KEY, state.saved);
    renderFeed();
  }

  function openArticle(item) {
    state.activeArticle = item;
    state.read.add(item.id);
    saveSet(READ_KEY, state.read);

    elements.articleCategory.textContent = item.category || "Новости";
    elements.articleTitle.textContent = item.title;
    elements.articleMeta.textContent =
      (item.source || "Источник не указан") + " · " +
      (item.author ? item.author + " · " : "") +
      formatDate(item.published_at);
    elements.articleSummary.textContent = item.summary || "Издатель не предоставил краткое описание.";
    elements.articleLink.href = item.url;
    elements.articleLink.textContent = "Читать оригинал у издателя ↗";

    if (typeof elements.dialog.showModal === "function" && !elements.dialog.open) {
      elements.dialog.showModal();
    }
    renderFeed();
  }

  function closeArticle() {
    if (elements.dialog.open) elements.dialog.close();
  }

  function setFilterButton(button, enabled) {
    button.setAttribute("aria-pressed", String(enabled));
  }

  elements.close.addEventListener("click", closeArticle);
  elements.dialog.addEventListener("click", event => {
    if (event.target === elements.dialog) closeArticle();
  });

  elements.unread.addEventListener("click", () => {
    state.unreadOnly = !state.unreadOnly;
    setFilterButton(elements.unread, state.unreadOnly);
    renderFeed();
  });

  elements.saved.addEventListener("click", () => {
    state.savedOnly = !state.savedOnly;
    setFilterButton(elements.saved, state.savedOnly);
    renderFeed();
  });

  elements.refresh.addEventListener("click", refreshNews);

  let searchTimer;
  elements.search.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => {
      state.query = elements.search.value.trim();
      loadNews();
    }, 260);
  });

  document.addEventListener("keydown", event => {
    if (event.key === "/" && !event.ctrlKey && !event.metaKey &&
        !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
      event.preventDefault();
      elements.search.focus();
    }
  });

  elements.date.textContent = new Intl.DateTimeFormat("ru-RU", {
    weekday: "long", day: "numeric", month: "long", year: "numeric"
  }).format(new Date());

  renderTabs();
  renderSources();
  loadNews();

  // The backend refreshes publishers on its own schedule; this timer only refreshes the view.
  window.setInterval(loadNews, 60 * 1000);
})();
