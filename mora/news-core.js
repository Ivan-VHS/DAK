export const NEWS_CATEGORIES = Object.freeze([
  { id: "ukraine", label: "Украина", query: "(Ukraine OR Kyiv OR Kharkiv OR Odesa OR Zaporizhzhia OR Dnipro)" },
  { id: "dnipro", label: "Днепр", query: '(Dnipro OR Dnipropetrovsk OR "Dnipro city")' },
  { id: "world", label: "Мир", query: '("world news" OR diplomacy OR "international relations")' },
  { id: "technology", label: "Технологии", query: '("artificial intelligence" OR cybersecurity OR technology)' },
  { id: "business", label: "Экономика", query: '("global economy" OR markets OR business)' },
  { id: "science", label: "Наука", query: '(science OR "space exploration" OR research)' }
]);

export const NEWS_CACHE_KEY = "duckos.mora.news.cache.v1";
export const NEWS_BOOKMARKS_KEY = "duckos.mora.news.bookmarks.v1";
export const NEWS_PREFERENCES_KEY = "duckos.mora.news.preferences.v1";
export const NEWS_MAX_ARTICLES = 30;
export const NEWS_MAX_BOOKMARKS = 100;

export function parseGdeltDate(value) {
  if (typeof value !== "string") return null;
  const match = value.match(/^(\\d{4})(\\d{2})(\\d{2})T(\\d{2})(\\d{2})(\\d{2})Z?$/);
  if (!match) {
    const parsed = Date.parse(value);
    return Number.isFinite(parsed) ? new Date(parsed).toISOString() : null;
  }
  const [, year, month, day, hour, minute, second] = match;
  const date = new Date(Date.UTC(+year, +month - 1, +day, +hour, +minute, +second));
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

export function normalizeNewsArticle(item) {
  if (!item || typeof item !== "object") return null;
  const title = typeof item.title === "string" ? item.title.trim().slice(0, 500) : "";
  const rawUrl = typeof item.url === "string" ? item.url.trim() : "";
  if (!title || !rawUrl) return null;

  let articleUrl;
  try {
    articleUrl = new URL(rawUrl);
  } catch {
    return null;
  }
  if (articleUrl.protocol !== "https:" || !articleUrl.hostname || articleUrl.username || articleUrl.password) return null;

  let image = null;
  if (typeof item.socialimage === "string" && item.socialimage.trim()) {
    try {
      const candidate = new URL(item.socialimage.trim());
      if (candidate.protocol === "https:") image = candidate.href;
    } catch {
      image = null;
    }
  }

  const domain = typeof item.domain === "string" && item.domain.trim()
    ? item.domain.trim().toLowerCase().slice(0, 180)
    : articleUrl.hostname.toLowerCase();
  return {
    id: articleUrl.href,
    url: articleUrl.href,
    title,
    domain,
    language: typeof item.language === "string" ? item.language.slice(0, 48) : "",
    sourceCountry: typeof item.sourcecountry === "string" ? item.sourcecountry.slice(0, 64) : "",
    seenAt: parseGdeltDate(item.seendate),
    image
  };
}

export function parseNewsArticles(payload) {
  if (!payload || typeof payload !== "object" || !Array.isArray(payload.articles)) return [];
  const unique = new Map();
  for (const raw of payload.articles) {
    const article = normalizeNewsArticle(raw);
    if (article && !unique.has(article.id)) unique.set(article.id, article);
    if (unique.size >= NEWS_MAX_ARTICLES) break;
  }
  return [...unique.values()].sort((a, b) => {
    const left = a.seenAt ? Date.parse(a.seenAt) : 0;
    const right = b.seenAt ? Date.parse(b.seenAt) : 0;
    return right - left;
  });
}

export function buildNewsRequestUrl(categoryId, searchText = "") {
  const category = NEWS_CATEGORIES.find((item) => item.id === categoryId);
  if (!category) throw new TypeError("Unknown news category");
  const cleanSearch = String(searchText)
    .replace(/[\\u0000-\\u001f\\u007f]/g, " ")
    .replace(/[()"]/g, " ")
    .replace(/\\s+/g, " ")
    .trim()
    .slice(0, 100);
  const query = category.query + (cleanSearch ? ' "' + cleanSearch + '"' : "");
  const params = new URLSearchParams({
    query,
    mode: "artlist",
    format: "json",
    maxrecords: String(NEWS_MAX_ARTICLES),
    timespan: "24h",
    sort: "datedesc"
  });
  return "https://api.gdeltproject.org/api/v2/doc/doc?" + params.toString();
}
