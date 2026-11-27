import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const root = new URL("../", import.meta.url);
const html = await readFile(new URL("mora/index.html", root), "utf8");
const app = await readFile(new URL("mora/app.js", root), "utf8");
const serviceWorker = await readFile(new URL("mora/service-worker.js", root), "utf8");
const registry = JSON.parse(await readFile(new URL("federation/mora-workbenches.v1.json", root), "utf8"));
const federation = JSON.parse(await readFile(new URL("federation/repositories.v1.json", root), "utf8"));
const release = JSON.parse(await readFile(new URL("federation/release-edition.v1.json", root), "utf8"));
const appRegistry = JSON.parse(await readFile(new URL("mora/apps.json", root), "utf8"));

const ids = ["reaper-workbench", "pytyliki-workbench", "oplague-workbench", "ventusample-workbench"];
const repoIds = ["pytyliki", "reaper", "oplague", "ventusample"];

test("Mora launcher exposes every pinned ecosystem workbench", () => {
  assert.equal(registry.schema, "dakos.mora-workbenches.v1");
  assert.equal(registry.policy.browser_launch, "panel-only");
  assert.equal(registry.policy.external_process_launch, false);
  assert.equal(registry.policy.auto_execute, false);
  assert.deepEqual(registry.workbenches.map((entry) => entry.id), ids);
  assert.equal(appRegistry.schema_version, "1.4.0");
  assert.deepEqual(appRegistry.ecosystem_workbenches.map((entry) => entry.id), ids);
  assert.ok(appRegistry.ecosystem_workbenches.every((entry) => entry.auto_execute === false));
  for (const entry of registry.workbenches) {
    assert.ok(html.includes('data-app="' + entry.id + '"'), entry.id + " has no desktop launcher");
    assert.ok(app.includes('"' + entry.id + '": { name:'), entry.id + " has no Mora app definition");
    assert.ok(app.includes('case "' + entry.id + '":'), entry.id + " has no panel route");
    assert.ok(app.includes(entry.documentation.replace("projects/", "../projects/")), entry.id + " has no local documentation route");
    assert.ok(entry.path.startsWith("projects/"));
    assert.ok(entry.license);
    assert.ok(entry.build && entry.test);
  }
});

test("federation pins exactly the four active user-space repositories", () => {
  assert.deepEqual(federation.repositories.map((entry) => entry.id), repoIds);
  assert.deepEqual(registry.workbenches.map((entry) => entry.project), ["reaper", "pytyliki", "oplague", "ventusample"]);
  assert.ok(federation.repositories.every((entry) => entry.auto_execute === false));
  assert.ok(federation.repositories.every((entry) => /^[0-9a-f]{40}$/.test(entry.pinned_commit)));
  assert.ok(federation.repositories.every((entry) => entry.path.startsWith("projects/")));
  for (const project of release.projects) {
    const pinned = federation.repositories.find((entry) => entry.id === project.id);
    assert.ok(pinned, project.id + " is missing from the federation contract");
    assert.equal(project.commit, pinned.pinned_commit, project.id + " release pin must match its gitlink contract");
  }
});

test("release metadata declares firmware and application boundaries honestly", () => {
  assert.equal(release.schema, "dakos.release-edition.v1");
  assert.equal(release.boot.kernel_stage, 1);
  assert.equal(release.boot.desktop_session_from_kernel, false);
  assert.equal(release.desktop.external_process_launch, false);
  assert.equal(release.projects.length, 4);
  assert.equal(release.release_policy.artificial_size_padding, false);
  assert.ok(serviceWorker.includes("mora-shell-v9-ecosystem"));
});
