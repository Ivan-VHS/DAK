import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../mora/index.html", import.meta.url), "utf8");
const css = await readFile(new URL("../mora/styles.css", import.meta.url), "utf8");
const amberCss = await readFile(new URL("../mora/amber.css", import.meta.url), "utf8");
const serviceWorker = await readFile(new URL("../mora/service-worker.js", import.meta.url), "utf8");
const theme = JSON.parse(await readFile(new URL("../mora/theme.json", import.meta.url), "utf8"));
const js = await readFile(new URL("../mora/app.js", import.meta.url), "utf8");
const registry = JSON.parse(await readFile(new URL("../mora/apps.json", import.meta.url), "utf8"));
const policy = JSON.parse(await readFile(new URL("../mora/system-policy.json", import.meta.url), "utf8"));

const appIds = [
  "cockos", "kavun", "kabon", "gloverty", "po", "illidia", "unify",
  "mora-ai", "security", "updates", "runtime", "workspace", "provenance", "newsroom", "horizon"
];

test("desktop exposes all seven first-party apps and six system tools", () => {
  for (const id of appIds) {
    const matches = html.match(new RegExp('data-app="' + id + '"', "g")) || [];
    assert.ok(matches.length >= 1, id + " is missing from the desktop");
    const appKey = id === "mora-ai" ? '"mora-ai":' : id + ":";
    assert.ok(js.includes(appKey), id + " must have a panel definition");
  }
  for (const id of appIds.slice(0, 7)) {
    const matches = html.match(new RegExp('data-app="' + id + '"', "g")) || [];
    assert.ok(matches.length >= 2, id + " must remain available from desktop and dock/widget");
  }
  assert.deepEqual(registry.built_in_apps.map((app) => app.id), appIds);
  assert.equal(registry.system_services.length, 9);
});

test("required dashboard surfaces and launch affordances are present", () => {
  for (const id of ["hero-clock", "hero-date", "active-app", "app-grid", "system-app-grid", "window-layer", "toast"]) {
    assert.ok(html.includes('id="' + id + '"'), id + " is missing");
  }
  assert.ok(html.includes('aria-label="Панель приложений"'));
  assert.ok(html.includes('data-app="workspace"'));
  assert.ok(html.includes("status-control"));
});

test("system panels expose approvals, permissions, recovery and local file inspection", () => {
  for (const marker of [
    "data-intent-form", "data-intent-preview", "approve-intent", "deny-intent",
    "data-capability", "save-recovery", "restore-recovery", "preview-update",
    "data-executable-file", "data-provenance-file", "data-power-profile",
    "data-setting", "NEWS_API", "data-news-status", "refresh-news", "horizonFeatures", "os-run"
  ]) {
    assert.ok(js.includes(marker), "missing system control: " + marker);
  }
  assert.ok(js.includes('event.key.toLowerCase() === "k"'));
  assert.ok(js.includes("Ctrl+K") === false);
});

test("shell policy keeps prototype and native-service maturity separate", () => {
  assert.equal(policy.desktop, "Mora");
  assert.equal(policy.product, "DuckOS");
  assert.equal(policy.capabilities.local_ai_and_npu.maturity, "planned");
  assert.equal(policy.capabilities.immutable_updates.maturity, "planned");
  assert.equal(policy.capabilities.compatibility.maturity, "partial");
  assert.equal(policy.capabilities.newsroom.maturity, "implemented");
  assert.equal(policy.capabilities.windows_runtime.maturity, "partial");
  assert.equal(policy.capabilities.reaper_native_contracts.maturity, "partial");
  assert.equal(policy.capabilities.build_manifest_tools.maturity, "implemented");
  assert.ok(policy.capabilities.zero_trust_permissions.scope.includes("no kernel enforcement"));
});

test("the desktop remains self-contained and responsive", () => {
  assert.ok(!/<script[^>]+src=["']https?:/i.test(html));
  assert.ok(!/<link[^>]+href=["']https?:/i.test(html));
  assert.ok(css.includes("@media (max-width:760px)"));
  assert.ok(css.includes("backdrop-filter"));
  assert.ok(css.includes("prefers-reduced-motion"));
  assert.ok(css.includes(".reduce-motion"));
  assert.ok(html.includes('href="amber.css"'));
  assert.ok(amberCss.includes("#d58b3d"));
  assert.ok(amberCss.includes('data-theme="light"'));
  assert.ok(amberCss.includes("wallpaper.svg"));
  assert.equal(theme.name, "Mora Amber");
  assert.equal(theme.palettes.dark.brand, "#D58B3D");
  assert.equal(theme.palettes.light.brand, "#8A4F1C");
  assert.ok(serviceWorker.includes("mora-shell-v3"));
  assert.ok(serviceWorker.includes("./wallpaper.svg"));
  assert.ok(js.includes('data-action="toggle-theme"'));
  assert.ok(js.includes("NEWS_API"));
});
