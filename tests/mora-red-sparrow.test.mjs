import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createLocalDocumentStore } from "../mora/local-store.js";

function memoryStorage() {
  const values = new Map();
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
    removeItem(key) { values.delete(key); }
  };
}

test("local document store saves, reads and removes records through its fallback", async () => {
  const store = createLocalDocumentStore({
    indexedDB: null,
    storage: memoryStorage(),
    now: () => "2026-11-24T00:00:00.000Z"
  });
  const saved = await store.put("red-sparrow.notes", { text: "赤雀 · local notes" });
  assert.deepEqual(saved, {
    ok: true,
    backend: "localStorage",
    updatedAt: "2026-11-24T00:00:00.000Z"
  });
  assert.deepEqual(await store.get("red-sparrow.notes"), { text: "赤雀 · local notes" });
  assert.equal(await store.remove("red-sparrow.notes"), true);
  assert.equal(await store.get("red-sparrow.notes"), null);
});

test("local document store rejects invalid identifiers and oversized payloads", async () => {
  const store = createLocalDocumentStore({ indexedDB: null, storage: memoryStorage() });
  await assert.rejects(() => store.put("../escape", { text: "no" }), TypeError);
  await assert.rejects(() => store.put("large", { text: "x".repeat(270 * 1024) }), RangeError);
});

test("Red Sparrow and locale are registered without changing DAK's shared theme", async () => {
  const [catalogText, appText, htmlText, policyText, coreText, themeText] = await Promise.all([
    readFile(new URL("../mora/apps.json", import.meta.url), "utf8"),
    readFile(new URL("../mora/app.js", import.meta.url), "utf8"),
    readFile(new URL("../mora/index.html", import.meta.url), "utf8"),
    readFile(new URL("../mora/system-policy.json", import.meta.url), "utf8"),
    readFile(new URL("../mora/core.js", import.meta.url), "utf8"),
    readFile(new URL("../mora/theme.json", import.meta.url), "utf8")
  ]);
  const catalog = JSON.parse(catalogText);
  const policy = JSON.parse(policyText);
  const theme = JSON.parse(themeText);
  assert.ok(catalog.built_in_apps.some((app) => app.id === "red-sparrow"));
  assert.match(appText, /case "red-sparrow"/);
  assert.match(htmlText, /data-app="red-sparrow"/);
  assert.match(appText, /简体中文（普通话）/);
  assert.match(appText, /new Intl\.DateTimeFormat\(locale/);
  assert.match(coreText, /"red-sparrow"/);
  assert.equal(policy.capabilities.language_profile.maturity, "partial");
  assert.equal(policy.capabilities.red_sparrow_workspace.maturity, "partial");
  assert.deepEqual(Object.keys(theme.palettes), ["dak"]);
  assert.equal(theme.palettes.dak.brand, "#FFD700");
});
