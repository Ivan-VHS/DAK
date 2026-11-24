import test from "node:test";
import assert from "node:assert/strict";
import {
  APP_IDS,
  buildIntentPlan,
  createDefaultPreferences,
  createRecoverySnapshot,
  inspectExecutable,
  loadPreferences,
  normalizePreferences,
  savePreferences,
  validateRecoverySnapshot
} from "../mora/core.js";

class MemoryStorage {
  constructor() {
    this.values = new Map();
  }
  getItem(key) {
    return this.values.has(key) ? this.values.get(key) : null;
  }
  setItem(key, value) {
    this.values.set(key, String(value));
  }
}

test("the shell registry exposes 20 user apps and seven system tools", () => {
  assert.equal(APP_IDS.length, 28);
  for (const id of ["sestem", "setupup", "orriganize", "abriganza", "olaab", "concrete-thump", "seu-beu", "love-il", "poi", "poi-2", "po-2", "gamecharager", "exedotexe"]) {
    assert.ok(APP_IDS.includes(id), id + " must be registered");
  }
  assert.ok(APP_IDS.includes("jora"));
  assert.ok(APP_IDS.includes("mora-ai"));
  assert.ok(APP_IDS.includes("security"));
  assert.ok(APP_IDS.includes("runtime"));
});

test("intent plans only describe whitelisted local actions", () => {
  const plan = buildIntentPlan("включи режим фокуса и экономию энергии");
  assert.equal(plan.ok, true);
  assert.deepEqual(plan.actions.map((item) => item.setting), ["focusMode", "powerProfile"]);
  assert.equal(buildIntentPlan("удали все системные файлы").ok, false);
  assert.equal(buildIntentPlan("x".repeat(321)).ok, false);
});

test("opening an app is restricted to the built-in application list", () => {
  const plan = buildIntentPlan("открой безопасность");
  assert.equal(plan.ok, true);
  assert.equal(plan.actions[0].type, "open-app");
  assert.equal(plan.actions[0].appId, "security");
  assert.equal(buildIntentPlan("запусти powershell").ok, false);
});

test("Mora Boost can be opened through the bounded intent allowlist", () => {
  const plan = buildIntentPlan("открой Mora Boost");
  assert.equal(plan.ok, true);
  assert.deepEqual(plan.actions.map((action) => action.appId), ["mora-boost"]);
});

test("preferences are validated and saved without trusting arbitrary values", () => {
  const storage = new MemoryStorage();
  const settings = createDefaultPreferences();
  settings.powerProfile = "performance";
  settings.permissions.camera = true;
  settings.permissions.shell = true;
  assert.equal(savePreferences(settings, storage), true);

  const loaded = loadPreferences(storage);
  assert.equal(loaded.powerProfile, "performance");
  assert.equal(loaded.permissions.camera, true);
  assert.equal("shell" in loaded.permissions, false);

  const normalized = normalizePreferences({ powerProfile: "root", focusMode: "yes" });
  assert.equal(normalized.powerProfile, "balanced");
  assert.equal(normalized.focusMode, false);
});

test("recovery snapshots preserve only normalized shell preferences", () => {
  const snapshot = createRecoverySnapshot({
    focusMode: true,
    powerProfile: "saver",
    permissions: { microphone: true, unknown: true }
  }, "2026-11-23T12:00:00.000Z");

  const restored = validateRecoverySnapshot(snapshot);
  assert.equal(restored.preferences.focusMode, true);
  assert.equal(restored.preferences.powerProfile, "saver");
  assert.equal("unknown" in restored.preferences.permissions, false);
  assert.equal(validateRecoverySnapshot({ schemaVersion: 7 }), null);
});

test("PE inspection recognises a 64-bit image without attempting to launch it", async () => {
  const bytes = new Uint8Array(128);
  bytes[0] = 0x4d;
  bytes[1] = 0x5a;
  new DataView(bytes.buffer).setUint32(0x3c, 64, true);
  bytes[64] = 0x50;
  bytes[65] = 0x45;
  new DataView(bytes.buffer).setUint16(68, 0x8664, true);

  const result = await inspectExecutable(new Blob([bytes]));
  assert.equal(result.valid, true);
  assert.equal(result.format, "Windows PE");
  assert.equal(result.architecture, "x86-64 · 64-bit");
  assert.match(result.detail, /запуск не выполнялся/);
});


test("legacy appearance settings migrate to the fixed DuckOS palette", () => {
  const defaults = createDefaultPreferences();
  assert.equal(defaults.appearance.theme, "duck");
  for (const theme of ["amber", "dark", "light", "system", "custom", null]) {
    assert.equal(normalizePreferences({ appearance: { theme } }).appearance.theme, "duck");
  }
});
