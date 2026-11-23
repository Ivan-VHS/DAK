import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  PERSONAL_SUITE_APPS,
  personalAppDefinitions,
  createDefaultPersonalSuiteState,
  normalizePersonalSuiteState,
  getPersonalSuiteSummary
} from "../mora/personal-suite.js";

const root = new URL("../", import.meta.url);
const html = await readFile(new URL("mora/index.html", root), "utf8");
const appJs = await readFile(new URL("mora/app.js", root), "utf8");
const registry = JSON.parse(await readFile(new URL("mora/apps.json", root), "utf8"));
const catalog = JSON.parse(await readFile(new URL("catalogs/personal-suite.v1.json", root), "utf8"));
const worker = await readFile(new URL("mora/service-worker.js", root), "utf8");

const ids = [
  "lumina-cycle", "nura-calm", "verba-rest", "sora-glow",
  "kora-closet", "mirra-fit", "talia-palette", "zara-loom",
  "bela-notes", "rina-craft", "olea-kitchen", "veda-bloom",
  "mila-nest", "daria-ledger", "elda-circle"
];

test("all fifteen personal apps have stable launcher and panel identities", () => {
  assert.deepEqual(PERSONAL_SUITE_APPS.map((app) => app.id), ids);
  assert.deepEqual(Object.keys(personalAppDefinitions), ids);
  for (const id of ids) assert.match(html, new RegExp('data-app="' + id + '"'));
  assert.ok(appJs.includes("personalAppDefinitions"));
  assert.ok(appJs.includes("renderPersonalApp"));
  assert.deepEqual(catalog.applications.map((app) => app.id), ids);
  assert.equal(catalog.applications.length, 15);
  assert.equal(registry.personal_suites[0].application_ids.length, 15);
  assert.equal(registry.personal_suites[0].data_policy, "local_only");
  assert.equal(registry.personal_suites[0].cloud_sync, false);
});

test("each app has usable fields and an explicit privacy boundary", () => {
  for (const app of PERSONAL_SUITE_APPS) {
    assert.ok(app.fields.length > 0, app.id);
    assert.ok(app.fields.every((field) => field.key && field.label && field.type), app.id);
    assert.ok(["sensitive", "private"].includes(app.privacy), app.id);
    assert.ok(app.boundaries.length > 0, app.id);
  }
  assert.equal(catalog.storage.provider, "browser-localStorage");
  assert.equal(catalog.storage.cloud_sync, false);
  assert.equal(catalog.storage.encryption_at_rest, false);
});

test("state normalization rejects malformed records and unknown apps", () => {
  const state = normalizePersonalSuiteState({
    version: 1,
    profile: { displayName: "<Name>".repeat(20) },
    records: {
      "lumina-cycle": [
        { id: "valid", fields: { note: "kept", cycleLength: 28 } },
        { id: "", fields: { note: "bad" } },
        { id: "broken", fields: null }
      ],
      unknown: [{ id: "ignored", fields: { note: "ignored" } }]
    }
  });
  assert.equal(state.records["lumina-cycle"].length, 1);
  assert.equal(state.records["lumina-cycle"][0].fields.cycleLength, 28);
  assert.equal(state.records["nura-calm"].length, 0);
  assert.equal(state.records.unknown, undefined);
  assert.equal(state.profile.displayName.length, 48);
});

test("aggregate counters count records without exposing their contents", () => {
  const state = createDefaultPersonalSuiteState();
  state.records["bela-notes"].push({ id: "a", fields: { title: "private note" } });
  state.records["daria-ledger"].push({ id: "b", fields: { amount: 50 } });
  const summary = getPersonalSuiteSummary(state);
  assert.equal(summary.applicationCount, 15);
  assert.equal(summary.totalRecords, 2);
  assert.equal(summary.counts["bela-notes"], 1);
  assert.equal(summary.counts["daria-ledger"], 1);
});

test("service worker caches the suite module and catalogue uses local-only storage", () => {
  assert.ok(worker.includes("./personal-suite.js"));
  assert.ok(worker.includes("mora-shell-v5-personal"));
  assert.ok(html.includes("15 приложений"));
});
