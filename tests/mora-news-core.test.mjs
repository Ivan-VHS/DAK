import test from "node:test";
import assert from "node:assert/strict";

import {
  NEWS_CATEGORIES,
  NEWS_MAX_ARTICLES,
  buildNewsRequestUrl,
  normalizeNewsArticle,
  parseGdeltDate,
  parseNewsArticles
} from "../mora/news-core.js";

test("news categories produce bounded GDELT JSON article-list requests", () => {
  assert.equal(NEWS_CATEGORIES.length, 6);
  const url = new URL(buildNewsRequestUrl("ukraine"));
  assert.equal(url.origin, "https://api.gdeltproject.org");
  assert.equal(url.pathname, "/api/v2/doc/doc");
  assert.equal(url.searchParams.get("mode"), "artlist");
  assert.equal(url.searchParams.get("format"), "json");
  assert.equal(url.searchParams.get("timespan"), "24h");
  assert.equal(url.searchParams.get("sort"), "datedesc");
  assert.equal(url.searchParams.get("maxrecords"), String(NEWS_MAX_ARTICLES));
  assert.match(url.searchParams.get("query"), /Ukraine/);
  assert.throws(() => buildNewsRequestUrl("unknown"), TypeError);
});

test("user search text is bounded and cannot add raw GDELT query operators", () => {
  const url = new URL(buildNewsRequestUrl("dnipro", 'Dnipro\n) OR domain:example.com "breaking"'));
  const query = url.searchParams.get("query");
  assert.ok(query.length < 300);
  assert.ok(!query.includes("\n"));
  assert.ok(!query.includes("domain:example.com"));
  assert.match(query, /Dnipro/);
  assert.match(query, /Dnipropetrovsk/);
});

test("GDELT timestamps are parsed as UTC and invalid dates are rejected", () => {
  assert.equal(parseGdeltDate("20261124T013045Z"), "2026-11-24T01:30:45.000Z");
  assert.equal(parseGdeltDate("not-a-date"), null);
  assert.equal(parseGdeltDate(null), null);
});

test("article normalization accepts HTTPS publisher URLs and rejects unsafe schemes", () => {
  const article = normalizeNewsArticle({
    title: "  A headline  ",
    url: "https://example.org/story",
    domain: "example.org",
    language: "English",
    sourcecountry: "ukraine",
    seendate: "20261124T010000Z",
    socialimage: "javascript:alert(1)"
  });
  assert.equal(article.title, "A headline");
  assert.equal(article.domain, "example.org");
  assert.equal(article.sourceCountry, "ukraine");
  assert.equal(article.image, null);
  assert.equal(article.seenAt, "2026-11-24T01:00:00.000Z");
  assert.equal(normalizeNewsArticle({ title: "bad", url: "javascript:alert(1)" }), null);
  assert.equal(normalizeNewsArticle({ title: "bad", url: "http://example.org/story" }), null);
  assert.equal(normalizeNewsArticle({ title: "", url: "https://example.org/story" }), null);
});

test("article lists deduplicate publisher URLs, sort by publication time and enforce limits", () => {
  const items = [
    { title: "Earlier", url: "https://example.org/1", seendate: "20261124T010000Z" },
    { title: "Latest", url: "https://example.org/2", seendate: "20261124T020000Z" },
    { title: "Duplicate", url: "https://example.org/2", seendate: "20261124T020000Z" },
    { title: "Unsafe", url: "javascript:alert(1)" }
  ];
  const parsed = parseNewsArticles({ articles: items });
  assert.deepEqual(parsed.map((item) => item.title), ["Latest", "Earlier"]);
  const oversized = Array.from({ length: NEWS_MAX_ARTICLES + 10 }, (_, index) => ({
    title: "Story " + index,
    url: "https://example.org/" + index,
    seendate: "20261124T020000Z"
  }));
  assert.equal(parseNewsArticles({ articles: oversized }).length, NEWS_MAX_ARTICLES);
  assert.deepEqual(parseNewsArticles({ articles: "invalid" }), []);
});

test("saved articles keep their local metadata when reopened from browser storage", () => {
  const [saved] = parseNewsArticles({
    articles: [{
      title: "Saved headline",
      url: "https://example.org/saved",
      domain: "example.org",
      seenAt: "2026-11-24T02:15:00.000Z",
      sourceCountry: "ukraine",
      image: "https://images.example.org/front.jpg"
    }]
  });
  assert.equal(saved.seenAt, "2026-11-24T02:15:00.000Z");
  assert.equal(saved.sourceCountry, "ukraine");
  assert.equal(saved.image, "https://images.example.org/front.jpg");
});
