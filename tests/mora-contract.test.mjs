import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../mora/index.html", import.meta.url), "utf8");
const css = await readFile(new URL("../mora/styles.css", import.meta.url), "utf8");
const js = await readFile(new URL("../mora/app.js", import.meta.url), "utf8");
const registry = JSON.parse(await readFile(new URL("../mora/apps.json", import.meta.url), "utf8"));

const appIds = ["cockos", "kavun", "kabon", "gloverty", "po", "illidia", "unify"];

test("desktop contains every built-in app exactly once", () => {
  for (const id of appIds) {
    const matches = html.match(new RegExp('data-app="' + id + '"', "g")) || [];
    assert.ok(matches.length >= 2, id + " must appear in the desktop and dock/widget launcher");
    assert.ok(js.includes(id + ":"), id + " must have a panel definition");
  }
  assert.deepEqual(registry.built_in_apps.map((app) => app.id), appIds);
});

test("required dashboard surfaces are present", () => {
  for (const id of ["hero-clock", "hero-date", "active-app", "app-grid", "window-layer", "toast"]) {
    assert.ok(html.includes('id="' + id + '"'), id + " is missing");
  }
  assert.ok(html.includes('data-app="kabon"') && html.includes('data-app="unify"'));
  assert.ok(html.includes('aria-label="Панель приложений"'));
});

test("application panels expose their requested live controls", () => {
  for (const marker of ["data-range", 'data-action="record"', "data-photo", "data-direction-tab", 'role="switch"', "expense-track", "progress-track"]) {
    assert.ok(js.includes(marker), "missing panel control: " + marker);
  }
  assert.ok(js.includes('event.key === "Escape"'));
  assert.ok(js.includes("pointermove"));
});

test("the desktop remains self-contained and responsive", () => {
  assert.ok(!/<script[^>]+src=["']https?:/i.test(html));
  assert.ok(!/<link[^>]+href=["']https?:/i.test(html));
  assert.ok(css.includes("@media (max-width:760px)"));
  assert.ok(css.includes("backdrop-filter"));
  assert.ok(css.includes("prefers-reduced-motion"));
});

test("demo data is explicitly declared", () => {
  assert.equal(registry.shell.data_policy, "fictional_demo_data");
  assert.equal(registry.integration.external_launch, "specified_not_enabled");
});