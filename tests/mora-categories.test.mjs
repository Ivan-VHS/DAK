import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { validateMoraCategoryRegistry } from "../mora/category-shell.js";

const root = new URL("../", import.meta.url);
const categories = JSON.parse(await readFile(new URL("mora/categories.v1.json", root), "utf8"));
const manifest = JSON.parse(await readFile(new URL("mora/apps.json", root), "utf8"));
const index = await readFile(new URL("mora/index.html", root), "utf8");
const app = await readFile(new URL("mora/app.js", root), "utf8");
const shell = await readFile(new URL("mora/category-shell.js", root), "utf8");
const worker = await readFile(new URL("mora/service-worker.js", root), "utf8");

test("Mora defines seven stable architectural categories", () => {
  assert.equal(categories.schema, "duckos.mora.categories.v1");
  assert.equal(categories.category_count, 7);
  assert.deepEqual(categories.categories.map((item)=>item.id), [
    "system-core","security-contracts","development-federation","mora-shell",
    "media-processing","network-communication","utilities"
  ]);
  assert.equal(manifest.schema_version, "1.5.0");
  assert.equal(manifest.category_registry, "mora/categories.v1.json");
  assert.equal(manifest.application_manifest_schema, "schemas/mora-application-manifest.v1.schema.json");
});

test("all 34 installed Mora applications have one canonical category and preserved domain", () => {
  const { apps, categories: categoryMap } = validateMoraCategoryRegistry(categories,manifest);
  assert.equal(apps.length,34);
  assert.equal(new Set(apps.map((item)=>item.id)).size,34);
  assert.ok(apps.every((item)=>item.domain && item.category && item.panel));
  assert.ok(apps.every((item)=>item.execution_surface==="mora-panel"));
  assert.ok(apps.every((item)=>Array.isArray(item.required_capabilities)));
  assert.equal(categoryMap.size,7);
});

test("privileged categories fail closed until a native broker is connected", () => {
  for (const id of ["system-core","security-contracts"]) {
    const category = categories.categories.find((item)=>item.id===id);
    assert.equal(category.access,"privileged");
    assert.equal(category.native_launch_policy,"required-capability-and-native-broker");
    assert.ok(category.required_capabilities.length>0);
    assert.ok(category.application_ids.every((id)=>{
      const app=manifest.built_in_apps.find((item)=>item.id===id);
      return app && app.native_process_launch==="denied-until-native-capability-broker";
    }));
  }
  assert.equal(categories.policy.privileged_native_launch,"deny_without_all_required_capabilities_and_native_broker");
  assert.equal(categories.policy.browser_panel_is_not_native_process,true);
});

test("Mora loads categories from local manifests and builds a filterable launcher", () => {
  assert.ok(index.includes('id="mora-category-browser"'));
  assert.ok(index.includes('id="mora-category-filters"'));
  assert.ok(index.includes('id="mora-category-groups"'));
  assert.ok(app.includes('initializeMoraCategories();'));
  assert.ok(shell.includes('fetcher(categoryPath)'));
  assert.ok(shell.includes('fetcher(manifestPath)'));
  assert.ok(shell.includes('data-category-filter'));
  assert.ok(worker.includes('"./category-shell.js"'));
  assert.ok(worker.includes('"./categories.v1.json"'));
  assert.ok(worker.includes("mora-shell-v10-categories"));
});
