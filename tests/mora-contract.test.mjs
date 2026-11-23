import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../mora/index.html", import.meta.url), "utf8");
const css = await readFile(new URL("../mora/styles.css", import.meta.url), "utf8");
const js = await readFile(new URL("../mora/app.js", import.meta.url), "utf8");
const registry = JSON.parse(await readFile(new URL("../mora/apps.json", import.meta.url), "utf8"));
const policy = JSON.parse(await readFile(new URL("../mora/system-policy.json", import.meta.url), "utf8"));

const appIds = [
  "cockos", "kavun", "kabon", "gloverty", "po", "illidia", "unify",
  "mora-ai", "security", "updates", "runtime", "workspace", "provenance"
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
  assert.equal(registry.system_services.length, 8);
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
    "data-setting"
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

test("Mora design system exposes Amber, Dark and Light themes", () => {
  assert.equal(theme.schema, "mora.theme.v1");
  assert.equal(theme.defaultPalette, "amber");
  assert.equal(theme.palettes.amber.page, "#211913");
  assert.equal(theme.palettes.amber.surface, "#33261D");
  assert.equal(theme.palettes.amber.text, "#FFF3E2");
  assert.equal(theme.palettes.amber.brand, "#D58B3D");
  assert.equal(theme.palettes.amber.secondaryAccent, "#526347");
  assert.equal(theme.palettes.amber.danger, "#B64A40");
  assert.ok(contrastRatio(theme.palettes.amber.text, theme.palettes.amber.page) >= 7);
  assert.ok(contrastRatio(theme.palettes.amber.onBrand, theme.palettes.amber.brand) >= 4.5);
  assert.ok(contrastRatio(theme.palettes.amber.onSecondaryAccent, theme.palettes.amber.secondaryAccent) >= 4.5);
  assert.equal(theme.palettes.dark.brand, "#A78BFA");
  assert.equal(theme.palettes.light.brand, "#5B43B5");
  assert.equal(manifest.name, "Mora — DuckOS Desktop");
  assert.equal(manifest.theme_color, "#211913");
  assert.equal(manifest.background_color, "#211913");
  assert.ok(html.includes('id="mora-folds"'));
  assert.ok(html.includes('id="mora-fold-pattern"'));
  assert.ok(css.includes(':root[data-theme="amber"]'));
  assert.ok(css.includes("repeating-linear-gradient(90deg"));
  assert.ok(css.includes("Mora Amber — final visual pass"));
  assert.ok(css.includes(".app-grid::before"));
  assert.ok(css.includes(".dock-wrap::before"));
  assert.ok(css.includes("#526347"));
  assert.ok(js.includes('const nextTheme = { amber: "dark", dark: "light", light: "amber" }'));
  assert.ok(serviceWorker.includes("mora-shell-v3-amber"));
  assert.ok(serviceWorker.includes("./core.js"));
  assert.ok(serviceWorker.includes("self.location.origin"));
});
