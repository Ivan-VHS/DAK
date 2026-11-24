import test from "node:test";
import assert from "node:assert/strict";
import {
  NEWS_SOURCES, normalizeNewsItem, plainText, safeArticleUrl,
  newsPanelMarkup, NEWS_CACHE_TTL_MS, MAX_NEWS_ITEMS
} from "../mora/news-feed.js";

test("Gazette has a bounded set of real publisher RSS sources", () => {
  assert.equal(NEWS_SOURCES.length, 6);
  assert.equal(new Set(NEWS_SOURCES.map((source) => source.id)).size, NEWS_SOURCES.length);
  assert.ok(NEWS_SOURCES.some((source) => source.category === "ukraine"));
  assert.ok(NEWS_SOURCES.some((source) => source.category === "world"));
  assert.ok(NEWS_SOURCES.some((source) => source.category === "technology"));
  assert.ok(NEWS_SOURCES.every((source) => safeArticleUrl(source.feed) && safeArticleUrl(source.home)));
  assert.equal(NEWS_CACHE_TTL_MS, 15 * 60 * 1000);
  assert.equal(MAX_NEWS_ITEMS, 60);
});

test("publisher URLs accept only credential-free HTTP and HTTPS links", () => {
  assert.equal(safeArticleUrl("https://example.com/story"), "https://example.com/story");
  assert.equal(safeArticleUrl("http://example.com/story"), "http://example.com/story");
  assert.equal(safeArticleUrl("javascript:alert(1)"), null);
  assert.equal(safeArticleUrl("data:text/html,hello"), null);
  assert.equal(safeArticleUrl("https://user:secret@example.com/story"), null);
  assert.equal(safeArticleUrl("not a URL"), null);
});

test("RSS markup is reduced to bounded plain text before it reaches the interface", () => {
  assert.equal(plainText("<p>News <strong>and</strong> context</p>"), "News and context");
  assert.equal(plainText("A &amp; B&nbsp;C"), "A & B C");
  assert.equal(plainText("<script>alert(1)</script><b>Safe</b>"), "Safe");
  assert.equal(plainText("Headline", 4), "Head");
});

test("news item normalization rejects unsafe links and untrusted markup is only text", () => {
  const source = NEWS_SOURCES.find((item) => item.id === "pravda");
  const valid = normalizeNewsItem({
    title: "<b>Важлива</b> новина", link: "https://example.com/news/1",
    description: "<p>Короткий <em>опис</em> матеріалу.</p>", pubDate: "2026-11-24T00:00:00Z"
  }, source);
  assert.ok(valid);
  assert.equal(valid.title, "Важлива новина");
  assert.equal(valid.description, "Короткий опис матеріалу.");
  assert.equal(valid.category, "ukraine");
  assert.equal(valid.url, "https://example.com/news/1");
  assert.equal(normalizeNewsItem({ title: "Unsafe", link: "javascript:alert(1)" }, source), null);
  assert.equal(normalizeNewsItem({ title: "<b></b>", link: "https://example.com" }, source), null);
});

test("Gazette exposes topic filters, search, refresh and publisher attribution", () => {
  const markup = newsPanelMarkup();
  for (const marker of [
    'data-gazette', 'data-news-search', 'data-news-refresh', 'data-news-list',
    'data-news-feature', 'data-news-category="ukraine"', 'data-news-category="world"',
    'data-news-category="technology"', "rss2json.com", "Українська правда",
    "Суспільне Новини", "BBC World"
  ]) {
    assert.ok(markup.includes(marker), "Missing Gazette UI contract: " + marker);
  }
});
