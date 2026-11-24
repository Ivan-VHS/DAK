import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  MORA_COMMONS_APPS,
  MORA_COMMONS_CATEGORIES,
  MORA_COMMONS_POLICY,
  filterCommonsApps
} from "../mora/commons-catalog.js";
import {
  BASE_APP_DEFINITIONS,
  BASE_APP_IDS,
  calculateExpression,
  renderBaseAppPanel
} from "../mora/base-apps.js";

const html = await readFile(new URL("../mora/index.html", import.meta.url), "utf8");
const js = await readFile(new URL("../mora/app.js", import.meta.url), "utf8");
const css = await readFile(new URL("../mora/styles.css", import.meta.url), "utf8");
const serviceWorker = await readFile(new URL("../mora/service-worker.js", import.meta.url), "utf8");
const registry = JSON.parse(await readFile(new URL("../mora/apps.json", import.meta.url), "utf8"));

test("Mora Commons keeps its original products and adds thirteen distinct core apps", () => {
  assert.equal(MORA_COMMONS_APPS.length, 28);
  assert.equal(new Set(MORA_COMMONS_APPS.map((app) => app.id)).size, 28);
  assert.deepEqual(
    MORA_COMMONS_APPS.slice(0, 13).map((app) => app.name),
    ["Deskline", "Nuvault", "Daymark", "Lexora", "Relay", "Wayline", "Sumora",
      "Pixora", "Nexcode", "Mnemo", "Calcora", "Paceforge", "Trailmark"]
  );
  assert.deepEqual(
    MORA_COMMONS_APPS.slice(13).map((app) => app.name),
    [
      "TorqueSpec", "Bore & Thread", "GarageBay Log", "Blade & Edge", "RigCheck",
      "IronCadence", "RoundTimer Pro", "RuckLedger", "Grip & Hang", "RecoveryLedger",
      "DeadReckon", "CampLoad", "WatchDesk", "MarginLine", "ColdStart"
    ]
  );
  assert.equal(MORA_COMMONS_CATEGORIES.length, 13);
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

test("all thirteen base products have a runnable Mora panel and registry definition", () => {
  assert.equal(BASE_APP_IDS.length, 13);
  assert.equal(new Set(BASE_APP_IDS).size, 13);
  const baseProducts = MORA_COMMONS_APPS.filter((app) => app.runtime === "local_browser");
  assert.equal(baseProducts.length, 13);
  assert.deepEqual(baseProducts.map((app) => app.id), BASE_APP_IDS);
  for (const app of baseProducts) {
    assert.ok(BASE_APP_DEFINITIONS[app.id], app.id + " needs a launcher definition");
    assert.ok(renderBaseAppPanel(app.id), app.id + " needs a working panel");
  }
});

test("Calcora parses arithmetic safely and rejects invalid or non-finite expressions", () => {
  assert.equal(calculateExpression("(12 + 8) * 3"), 60);
  assert.equal(calculateExpression("10 / 2 + 3"), 8);
  assert.equal(calculateExpression("7 % 4"), 3);
  assert.throws(() => calculateExpression("5 / 0"), /Деление на ноль/);
  assert.throws(() => calculateExpression("window.alert(1)"), /Недопустимый символ/);
  assert.throws(() => calculateExpression("(3 + 2"), /Не закрыта скобка/);
});

test("search and category filters return the expected catalogue entries", () => {
  assert.deepEqual(filterCommonsApps("", "workshop").map((app) => app.id), [
    "torquespec", "bore-thread", "garagebay-log", "blade-edge", "rigcheck"
  ]);
  assert.ok(filterCommonsApps("затяжки").some((app) => app.id === "torquespec"));
  assert.ok(filterCommonsApps("бокс", "training").some((app) => app.id === "roundtimer-pro"));
  assert.equal(filterCommonsApps("несуществующий запрос").length, 0);
  assert.equal(filterCommonsApps("", "all").length, 28);
});

test("equal access is a product rule rather than a user segment", () => {
  assert.equal(MORA_COMMONS_POLICY.audience, "everyone");
  assert.equal(MORA_COMMONS_POLICY.genderSegmentation, false);
  assert.equal(MORA_COMMONS_POLICY.maturity, "13_local_first_apps_15_specialist_specs");
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
  assert.ok(js.includes("data-commons-launch"));
  assert.ok(js.includes("initializeBaseAppPanel(appWindow)"));
  assert.ok(css.includes(".commons-grid"));
  assert.ok(css.includes("@media (max-width:760px)"));
  assert.ok(serviceWorker.includes("./commons-catalog.js"));
  assert.ok(serviceWorker.includes("./base-apps.js"));
  assert.ok(registry.built_in_apps.some((app) => app.id === "mora-commons"));
  for (const id of BASE_APP_IDS) assert.ok(registry.built_in_apps.some((app) => app.id === id), id + " must be in the Mora registry");
});
