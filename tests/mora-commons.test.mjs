import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  MORA_COMMONS_APPS,
  MORA_COMMONS_CATEGORIES,
  MORA_COMMONS_POLICY,
  filterCommonsApps
} from "../mora/commons-catalog.js";

const html = await readFile(new URL("../mora/index.html", import.meta.url), "utf8");
const js = await readFile(new URL("../mora/app.js", import.meta.url), "utf8");
const css = await readFile(new URL("../mora/styles.css", import.meta.url), "utf8");
const serviceWorker = await readFile(new URL("../mora/service-worker.js", import.meta.url), "utf8");
const registry = JSON.parse(await readFile(new URL("../mora/apps.json", import.meta.url), "utf8"));

test("Mora Commons exposes all fifteen products exactly once", () => {
  assert.equal(MORA_COMMONS_APPS.length, 15);
  assert.equal(new Set(MORA_COMMONS_APPS.map((app) => app.id)).size, 15);
  assert.deepEqual(
    MORA_COMMONS_APPS.map((app) => app.name),
    [
      "TorqueSpec", "Bore & Thread", "GarageBay Log", "Blade & Edge", "RigCheck",
      "IronCadence", "RoundTimer Pro", "RuckLedger", "Grip & Hang", "RecoveryLedger",
      "DeadReckon", "CampLoad", "WatchDesk", "MarginLine", "ColdStart"
    ]
  );
});

test("all catalogue entries belong to a task category and have useful specifications", () => {
  const categoryIds = new Set(MORA_COMMONS_CATEGORIES.map((category) => category.id));
  for (const app of MORA_COMMONS_APPS) {
    assert.ok(categoryIds.has(app.category), app.id + " has an unknown category");
    assert.ok(app.description.length > 20, app.id + " needs a useful description");
    assert.ok(app.capabilities.length >= 3, app.id + " needs an initial capability list");
    assert.ok(app.keywords.length >= 3, app.id + " needs search keywords");
  }
});

test("search and category filters return the expected catalogue entries", () => {
  assert.deepEqual(filterCommonsApps("", "workshop").map((app) => app.id), [
    "torquespec", "bore-thread", "garagebay-log", "blade-edge", "rigcheck"
  ]);
  assert.ok(filterCommonsApps("затяжки").some((app) => app.id === "torquespec"));
  assert.ok(filterCommonsApps("бокс", "training").some((app) => app.id === "roundtimer-pro"));
  assert.equal(filterCommonsApps("несуществующий запрос").length, 0);
  assert.equal(filterCommonsApps("", "all").length, 15);
});

test("equal access is a product rule rather than a user segment", () => {
  assert.equal(MORA_COMMONS_POLICY.audience, "everyone");
  assert.equal(MORA_COMMONS_POLICY.genderSegmentation, false);
  assert.equal(MORA_COMMONS_POLICY.maturity, "catalog_implemented_products_specified");
  assert.ok(MORA_COMMONS_POLICY.principles.some((rule) => rule.includes("Equal access")));
  assert.ok(MORA_COMMONS_POLICY.principles.some((rule) => rule.includes("No gender-based")));
  assert.ok(MORA_COMMONS_CATEGORIES.every((category) => !/men|women|мужчин|женщин/i.test(category.title)));
});

test("Mora shell includes an accessible and offline-cached Commons entry point", () => {
  assert.ok(html.includes('data-app="mora-commons"'));
  assert.ok(js.includes('case "mora-commons"'));
  assert.ok(js.includes("data-commons-search"));
  assert.ok(js.includes("data-commons-filters"));
  assert.ok(js.includes("data-commons-favorite"));
  assert.ok(css.includes(".commons-grid"));
  assert.ok(css.includes("@media (max-width:760px)"));
  assert.ok(serviceWorker.includes("./commons-catalog.js"));
  assert.ok(registry.built_in_apps.some((app) => app.id === "mora-commons"));
});
