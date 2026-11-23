import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../mora/index.html", import.meta.url), "utf8");
const css = await readFile(new URL("../mora/styles.css", import.meta.url), "utf8");
const js = await readFile(new URL("../mora/app.js", import.meta.url), "utf8");
const registry = JSON.parse(await readFile(new URL("../mora/apps.json", import.meta.url), "utf8"));
const policy = JSON.parse(await readFile(new URL("../mora/system-policy.json", import.meta.url), "utf8"));

const coreAppIds = ["cockos", "kavun", "kabon", "gloverty", "po", "illidia", "unify"];
const extensionAppIds = [
  "sestem", "setupup", "orriganize", "abriganza", "olaab", "concrete-thump",
  "seu-beu", "love-il", "poi", "poi-2", "po-2", "gamecharager", "exedotexe"
];
const systemAppIds = [
  "mora-ai", "security", "updates", "runtime", "workspace", "provenance", "mora-boost", "desktop", "mora-commons"
];
const appIds = [...coreAppIds, ...extensionAppIds, ...systemAppIds];

test("desktop exposes 20 first-party apps and nine system tools", () => {
  for (const id of appIds) {
    const matches = html.match(new RegExp('data-app="' + id + '"', "g")) || [];
    assert.ok(matches.length >= 1, id + " is missing from the desktop");
    const appKey = id.includes("-") ? '"' + id + '"' : id;
    assert.ok(js.includes(appKey + ": { name:"), id + " must have an app definition");
  }
  for (const id of coreAppIds) {
    const matches = html.match(new RegExp('data-app="' + id + '"', "g")) || [];
    assert.ok(matches.length >= 2, id + " must remain available from desktop and dock/widget");
  }
  assert.deepEqual(registry.built_in_apps.map((app) => app.id), appIds);
  assert.equal(registry.system_services.length, 13);
  assert.ok(html.includes('id="extension-app-grid"'));
  for (const id of extensionAppIds) {
    assert.ok(html.includes('data-app="' + id + '"'), id + " is missing from the extension grid");
    assert.ok(js.includes('case "' + id + '"'), id + " is missing an extension panel");
    assert.ok(registry.built_in_apps.some((app) => app.id === id), id + " is missing from the registry");
  }
  for (const name of ["Sestem", "SetupUP", "Orriganize", "Abriganza", "Olaab",
    "Concrete Thump", "Seu-Beu", "Love-IL", "Poi", "Poi-2", "Po-2", "GameCharager", "EXEdotEXE"]) {
    assert.ok(html.includes(name) || js.includes(name), name + " label is missing");
  }
});

test("required dashboard surfaces and launch affordances are present", () => {
  for (const id of ["hero-clock", "hero-date", "active-app", "app-grid", "system-app-grid", "window-layer", "toast"]) {
    assert.ok(html.includes('id="' + id + '"'), id + " is missing");
  }
  assert.ok(html.includes('aria-label="Панель приложений"'));
  assert.ok(html.includes('data-app="workspace"'));
  assert.ok(html.includes("status-control"));
  assert.ok(html.includes('data-app="desktop"'));
  assert.ok(js.includes('case "desktop":'));
  assert.equal(policy.capabilities.desktop_optimizer.maturity, "partial");
});

test("system panels expose approvals, permissions, recovery and local file inspection", () => {
  for (const marker of [
    "data-intent-form", "data-intent-preview", "approve-intent", "deny-intent",
    "data-capability", "save-recovery", "restore-recovery", "preview-update",
    "data-executable-file", "data-provenance-file", "data-power-profile",
    "data-setting", "data-extension-form", "data-archive-file", "data-beat-range",
    "Единая палитра DuckOS", "data-share-check"
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
  assert.ok(policy.capabilities.zero_trust_permissions.scope.includes("no kernel enforcement"));
});

test("the desktop remains self-contained and responsive", () => {
  assert.ok(!/<script[^>]+src=["']https?:/i.test(html));
  assert.ok(!/<link[^>]+href=["']https?:/i.test(html));
  assert.ok(css.includes("@media (max-width:760px)"));
  assert.ok(css.includes("backdrop-filter"));
  assert.ok(css.includes("prefers-reduced-motion"));
  assert.ok(css.includes(".reduce-motion"));
});


const theme = JSON.parse(await readFile(new URL("../mora/theme.json", import.meta.url), "utf8"));
const manifest = JSON.parse(await readFile(new URL("../mora/manifest.webmanifest", import.meta.url), "utf8"));
const serviceWorker = await readFile(new URL("../mora/service-worker.js", import.meta.url), "utf8");

function relativeLuminance(hex) {
  const channels = hex.match(/[0-9a-f]{2}/gi).map((part) => parseInt(part, 16) / 255);
  const linear = channels.map((value) =>
    value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
  );
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}

function contrastRatio(foreground, background) {
  const values = [relativeLuminance(foreground), relativeLuminance(background)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

test("Mora uses one accessible black, white and yellow DuckOS palette", () => {
  assert.equal(theme.schema, "mora.theme.v1");
  assert.equal(theme.defaultPalette, "duck");
  assert.deepEqual(Object.keys(theme.palettes), ["duck"]);
  const palette = theme.palettes.duck;
  assert.equal(palette.page, "#0E0F0D");
  assert.equal(palette.surface, "#191A17");
  assert.equal(palette.text, "#F5F4EF");
  assert.equal(palette.brand, "#D6BE65");
  assert.equal(palette.danger, "#D6BE65");
  assert.ok(contrastRatio(palette.text, palette.page) >= 7);
  assert.ok(contrastRatio(palette.onBrand, palette.brand) >= 4.5);
  assert.ok(contrastRatio(palette.onSecondaryAccent, palette.secondaryAccent) >= 4.5);
  assert.equal(manifest.name, "Mora — DuckOS Desktop");
  assert.equal(manifest.theme_color, "#D6BE65");
  assert.equal(manifest.background_color, "#0E0F0D");
  assert.ok(html.includes('name="theme-color" content="#D6BE65"'));
  assert.ok(html.includes('id="mora-folds"'));
  assert.ok(html.includes('id="mora-fold-pattern"'));
  assert.ok(html.includes('Единая палитра DuckOS'));
  assert.ok(html.includes('data-app="mora-commons"'));
  assert.ok(css.includes(':root[data-theme="duck"]'));
  assert.ok(!/data-theme="(amber|dark|light)"/.test(css));
  assert.ok(css.includes("#D6BE65"));
  assert.ok(css.includes(".commons-grid"));
  const allowedColors = new Set([
    "#0E0F0D", "#191A17", "#252721", "#3A3B35", "#3E3825",
    "#A6A69D", "#E7E5DC", "#F5F4EF", "#D6BE65", "#E6D48B", "#14140F"
  ].map((color) => color.toLowerCase()));
  const cssColors = [...css.matchAll(/#[0-9a-f]{6}/gi)].map((match) => match[0].toLowerCase());
  assert.ok(cssColors.every((color) => allowedColors.has(color)), "CSS uses only Duck palette colors");
  const inlineColors = [...html.matchAll(/#[0-9a-f]{6}/gi)].map((match) => match[0].toLowerCase());
  assert.ok(inlineColors.every((color) => allowedColors.has(color)), "HTML and SVG use only Duck palette colors");
  assert.ok(js.includes('document.documentElement.dataset.theme = "duck"'));
  assert.ok(!js.includes("nextTheme"));
  assert.ok(!js.includes("data-setup-theme"));
  assert.ok(!html.includes('data-action="toggle-theme"'));
  assert.ok(serviceWorker.includes("mora-shell-v8-soft-glass"));
  assert.ok(serviceWorker.includes("./commons-catalog.js"));
  assert.ok(serviceWorker.includes("./core.js"));
  assert.ok(serviceWorker.includes("self.location.origin"));
});


test("Mora central launcher uses Soft Glass, one Duck accent and gentle platform motion", () => {
  assert.ok(html.includes("29 ПРИЛОЖЕНИЙ И ИНСТРУМЕНТОВ"));
  assert.ok(css.includes("grid-template-columns:repeat(4,minmax(0,1fr))"));
  assert.ok(css.includes(".app-tile:active"));
  assert.ok(css.includes("@keyframes mora-window-in"));
  assert.ok(css.includes("prefers-reduced-motion"));
  assert.ok(css.includes(":root.reduce-motion"));
  assert.ok(css.includes("@supports not"));
  assert.ok(js.includes("MAX_OPEN_WINDOWS = 6"));
});

test("Mora blocks remote active content and limits browser-layer authority", () => {
  assert.ok(html.includes("Content-Security-Policy"));
  assert.ok(html.includes("script-src 'self'"));
  assert.ok(html.includes("connect-src 'self'"));
  assert.ok(html.includes("object-src 'none'"));
  assert.ok(html.includes('name="referrer" content="no-referrer"'));
  assert.equal(policy.capabilities.content_security_policy.maturity,"partial");
  assert.ok(policy.capabilities.content_security_policy.scope.includes("inline styles remain allowed"));
});
