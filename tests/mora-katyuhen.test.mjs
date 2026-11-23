import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const readJson = async (path) => JSON.parse(await readFile(new URL(path, import.meta.url), "utf8"));
const readText = async (path) => readFile(new URL(path, import.meta.url), "utf8");

test("Katyuhen registry has one stable identity and five registered projects", async () => {
  const registry = await readJson("../ecosystem/katyuhen.v1.json");
  assert.equal(registry.schema, "katyuhen.ecosystem.v1");
  assert.equal(registry.version, 1);
  assert.equal(registry.name, "Katyuhen");
  assert.deepEqual(registry.workspace, {
    host_project: "duckos",
    desktop: "mora",
    hub_panel: "katyuhen",
    theme_contract: "mora.theme.v1"
  });

  const ids = registry.projects.map((project) => project.id);
  assert.equal(ids.length, 5);
  assert.equal(new Set(ids).size, ids.length);
  assert.deepEqual(new Set(ids), new Set(["duckos", "reaper", "oplague", "pytyliki", "ventusample"]));

  for (const project of registry.projects) {
    assert.match(project.repository_url, /^https:\/\/github\.com\/Ivan-VHS\//);
    assert.match(project.manifest_url, /^https:\/\/raw\.githubusercontent\.com\/Ivan-VHS\//);
    assert.ok(project.description.length > 10);
    assert.ok(project.scope.length > 10);
  }
});

test("every integration edge points to registered projects and carries evidence", async () => {
  const registry = await readJson("../ecosystem/katyuhen.v1.json");
  const ids = new Set(registry.projects.map((project) => project.id));
  const edgeIds = registry.integrations.map((edge) => edge.id);
  assert.equal(new Set(edgeIds).size, edgeIds.length);

  for (const edge of registry.integrations) {
    assert.ok(ids.has(edge.source), edge.id + " has an unknown source");
    assert.ok(ids.has(edge.target), edge.id + " has an unknown target");
    assert.ok(edge.contract.length > 0);
    assert.ok(edge.description.length > 10);
    assert.match(edge.evidence_url, /^https:\/\/github\.com\/Ivan-VHS\//);
    assert.ok(["implemented", "partial", "specified", "planned"].includes(edge.status));
  }
});

test("Mora exposes the Katyuhen hub as a registered system tool", async () => {
  const html = await readText("../mora/index.html");
  const app = await readText("../mora/app.js");
  const manifest = await readJson("../mora/apps.json");
  assert.match(html, /data-app="katyuhen"/);
  assert.match(app, /katyuhen:/);
  assert.match(app, /case "katyuhen":/);
  assert.ok(manifest.built_in_apps.some((item) => item.id === "katyuhen"));
});

test("DuckOS project declaration keeps external process and driver mutation disabled", async () => {
  const manifest = await readJson("../integrations/katyuhen/manifest.json");
  assert.equal(manifest.schema, "katyuhen.project.v1");
  assert.equal(manifest.id, "duckos");
  assert.equal(manifest.security.driver_mutation_policy, "not_supported");
  assert.equal(manifest.security.process_execution_policy, "not_supported");
  assert.ok(manifest.limits.some((line) => line.includes("does not launch external processes")));
});
