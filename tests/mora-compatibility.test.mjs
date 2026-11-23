import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const catalog = JSON.parse(await readFile(new URL("../mora/compatibility-targets.v1.json", import.meta.url), "utf8"));
const canonical = JSON.parse(await readFile(new URL("../catalogs/compatibility-targets.v1.json", import.meta.url), "utf8"));
const schema = JSON.parse(await readFile(new URL("../schemas/compatibility-targets.v1.schema.json", import.meta.url), "utf8"));
const app = await readFile(new URL("../mora/app.js", import.meta.url), "utf8");
const bridge = await readFile(new URL("../mora/compatibility.js", import.meta.url), "utf8");
const worker = await readFile(new URL("../mora/service-worker.js", import.meta.url), "utf8");

test("the Mora-local compatibility data matches its versioned source catalog", () => {
  assert.deepEqual(catalog, canonical);
  assert.equal(catalog.schema, "duckos.compatibility-targets.v1");
  assert.equal(schema.properties.targets.minItems, 15);
  assert.equal(schema.properties.targets.maxItems, 15);
});

test("all fifteen reference operating systems are present exactly once", () => {
  const ids = catalog.targets.map(target => target.id);
  assert.equal(ids.length, 15);
  assert.equal(new Set(ids).size, 15);
  assert.deepEqual(new Set(ids), new Set([
    "macos", "freebsd", "reactos", "haiku", "openbsd", "netbsd",
    "dragonfly-bsd", "openindiana-illumos", "freedos", "kolibrios",
    "aros", "morphos", "qnx", "plan9-9front", "redox"
  ]));
});

test("all four execution models have a dedicated description", () => {
  assert.deepEqual(new Set(catalog.mechanisms.map(item => item.id)), new Set([
    "native-execution", "api-translation",
    "binary-translation", "emulation-virtualization"
  ]));
  for (const item of catalog.mechanisms) assert.ok(item.description.length > 20);
});

test("the current Bridge panel opens the integrated compatibility matrix", () => {
  assert.ok(app.includes('data-compatibility-reference'));
  assert.ok(app.includes('renderCompatibilityReference'));
  assert.ok(bridge.includes('renderCompatibilityReference'));
});

test("the browser does not claim that executable launch runtimes are already installed", () => {
  assert.equal(catalog.duckos_runtime.native_bridge, "not_implemented");
  assert.equal(catalog.duckos_runtime.pe_execution, "not_available");
  assert.equal(catalog.duckos_runtime.dos_execution, "not_available");
  assert.ok(bridge.includes("Нативный исполнитель не подключён"));
  assert.ok(!bridge.includes("child_process"));
  assert.ok(!bridge.includes("cmd.exe"));
});

test("the Mora service worker caches compatibility data inside its own scope", () => {
  assert.ok(worker.includes('"./compatibility.js"'));
  assert.ok(worker.includes('"./compatibility.css"'));
  assert.ok(worker.includes('"./compatibility-targets.v1.json"'));
  assert.ok(worker.includes("url.pathname.startsWith(SCOPE_PATH)"));
});
