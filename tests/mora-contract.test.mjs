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
  assert.equal(registry.native_apps.length, 4);
});

test("four native project tools share the Mora desktop and fixed local launcher", () => {
  const nativeApps = [
    ["reaper", "Reaper Studio"],
    ["oplague", "OPlague"],
    ["ventusample", "VentuSample"],
    ["pytyliki", "Pytyliki"]
  ];

  for (const [id, name] of nativeApps) {
    assert.ok(html.includes('data-app="native-' + id + '"'), name + " must appear on the desktop");
    assert.ok(js.includes('"native-' + id + '"'), name + " must have a native window definition");
    assert.ok(js.includes('data-native-id'), name + " must expose the registered launch ID");
    assert.ok(appIds.includes(id) === false, "native project IDs stay separate from first-party web IDs");
  }

  assert.deepEqual(registry.native_apps.map((app) => app.id), nativeApps.map(([id]) => id));
  assert.equal(registry.integration.external_launch, "implemented_loopback_allowlist_launcher");
  assert.ok(js.includes('fetch("/api/apps"'));
  assert.ok(js.includes('"/api/launch/"'));
  assert.ok(js.includes("new Set([\"cockos\""));
  assert.ok(js.includes("../prototype/mora-home.html?app="));
  assert.ok(css.includes(".embedded-web-app"));
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
