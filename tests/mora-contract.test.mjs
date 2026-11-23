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
  "mora-ai", "security", "updates", "runtime", "workspace", "provenance", "mora-boost"
];

test("desktop exposes all seven first-party apps and seven system tools", () => {
  for (const id of appIds) {
    const matches = html.match(new RegExp('data-app="' + id + '"', "g")) || [];
    assert.ok(matches.length >= 1, id + " is missing from the desktop");
    const appKey = ["mora-ai", "mora-boost"].includes(id) ? '"' + id + '":' : id + ":";
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

test("Mora design system exposes five accessible selectable palettes", () => {
  const paletteIds = ["solar", "amber", "arctic", "amethyst", "jade"];
  assert.equal(theme.schema, "mora.theme.v1");
  assert.equal(theme.version, 3);
  assert.equal(theme.defaultPalette, "solar");
  assert.deepEqual(Object.keys(theme.palettes), paletteIds);
  assert.equal(theme.palettes.solar.page, "#080A0D");
  assert.equal(theme.palettes.solar.text, "#F6F7F8");
  assert.equal(theme.palettes.solar.brand, "#F2C94C");
  assert.equal(theme.palettes.amber.page, "#101113");
  assert.equal(theme.palettes.amber.brand, "#E7B93E");
  assert.equal(theme.palettes.arctic.page, "#F7F7F4");
  assert.equal(theme.palettes.arctic.brand, "#8A6500");
  assert.equal(theme.palettes.amethyst.brand, "#FFD400");
  assert.equal(theme.palettes.jade.brand, "#D8AD33");

  function isNeutralOrYellow(hex) {
    const [red, green, blue] = hex.match(/[0-9a-f]{2}/gi).map((part) => parseInt(part, 16));
    const channels = [red, green, blue];
    const neutral = Math.max(...channels) - Math.min(...channels) <= 24;
    const yellow = red >= green && green >= blue && red - green <= 120 && green - blue >= 30;
    return neutral || yellow;
  }

  for (const palette of Object.values(theme.palettes)) {
    for (const value of Object.values(palette)) {
      if (typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value)) {
        assert.ok(isNeutralOrYellow(value), palette.label + " contains a color outside the black-white-yellow family");
      }
    }
  }
  assert.ok(!JSON.stringify(theme.palettes).includes("#006A93"));
  assert.ok(!JSON.stringify(theme.palettes).includes("#B49AF7"));
  assert.ok(!JSON.stringify(theme.palettes).includes("#7FC49A"));

  for (const palette of Object.values(theme.palettes)) {
    assert.ok(contrastRatio(palette.text, palette.page) >= 7, palette.label + " body text");
    assert.ok(contrastRatio(palette.secondary, palette.surface) >= 4.5, palette.label + " secondary text");
    assert.ok(contrastRatio(palette.muted, palette.surface) >= 4.5, palette.label + " muted text");
    assert.ok(contrastRatio(palette.onBrand, palette.brand) >= 4.5, palette.label + " primary control");
    assert.ok(contrastRatio(palette.brand, palette.page) >= 4.5, palette.label + " accent");
    assert.ok(contrastRatio(palette.onSecondaryAccent, palette.secondaryAccent) >= 4.5, palette.label + " secondary control");
    assert.ok(contrastRatio(palette.onDanger, palette.danger) >= 4.5, palette.label + " destructive control");
  }

  assert.equal(manifest.name, "Mora — DuckOS Desktop");
  assert.equal(manifest.theme_color, "#080A0D");
  assert.equal(manifest.background_color, "#080A0D");
  assert.ok(html.includes('data-theme="solar"'));
  assert.ok(html.includes('id="mora-folds"'));
  assert.ok(html.includes('id="mora-fold-pattern"'));
  for (const id of paletteIds) {
    assert.ok(css.includes(':root[data-theme="' + id + '"]'), id + " palette styles are missing");
    assert.ok(js.includes('id: "' + id + '"'), id + " selector preview is missing");
  }
  assert.ok(js.includes("paletteChoicesMarkup"));
  assert.ok(js.includes("updatePalettePanel"));
  assert.ok(js.includes("selectPalette"));
  assert.ok(css.includes(".palette-choice[aria-pressed=\"true\"]"));
  assert.ok(css.includes("Five selectable Mora palettes"));
  assert.ok(css.includes("--mora-wallpaper"));
  assert.ok(css.includes("var(--mora-brand)"));
  assert.ok(!css.includes("Mora Amber — final visual pass"));
  assert.ok(!css.includes("#D58B3D"));
  assert.ok(serviceWorker.includes("mora-shell-v5-palettes"));
  assert.ok(serviceWorker.includes("./core.js"));
  assert.ok(serviceWorker.includes("self.location.origin"));
});
