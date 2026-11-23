import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const catalog = JSON.parse(await readFile(new URL("../catalogs/hardware-performance-suite.v1.json", import.meta.url), "utf8"));
const html = await readFile(new URL("../mora/hardware/index.html", import.meta.url), "utf8");
const js = await readFile(new URL("../mora/hardware/hardware.js", import.meta.url), "utf8");
const serviceWorker = await readFile(new URL("../mora/service-worker.js", import.meta.url), "utf8");
const shell = await readFile(new URL("../mora/index.html", import.meta.url), "utf8");
const app = await readFile(new URL("../mora/app.js", import.meta.url), "utf8");

test("Hardware Studio has exactly fifteen uniquely identified modules", () => {
  const modules = catalog.applications;
  assert.equal(modules.length, 15);
  assert.equal(new Set(modules.map((module) => module.id)).size, 15);
  for (const module of modules) {
    assert.ok(js.includes('id:"' + module.id + '"'), module.id + " is missing from the UI registry");
    assert.ok(module.entrypoint.startsWith("mora/hardware/index.html#"), module.id);
  }
});

test("Hardware Studio is reachable from the current Mora shell", () => {
  assert.ok(shell.includes('data-app="hardware-studio"'));
  assert.ok(app.includes('entryPoint: "./hardware/index.html"'));
  assert.ok(html.includes('href="../index.html"'));
  assert.ok(html.includes('href="../styles.css"'));
});

test("the Mora service worker precaches the hardware workspace", () => {
  for (const asset of [
    "./hardware/index.html",
    "./hardware/hardware.css",
    "./hardware/hardware.js"
  ]) {
    assert.ok(serviceWorker.includes(asset), asset + " is not precached");
  }
});

test("the browser UI does not present its frame probe as a game benchmark", () => {
  assert.ok(js.includes("не FPS игры"));
  assert.ok(js.includes("requestAnimationFrame"));
  assert.ok(js.includes("ETW/PresentMon"));
});

test("the driver installer requires explicit approval and never flashes firmware", async () => {
  const agent = await readFile(new URL("../agent/duckos_hardware_agent.py", import.meta.url), "utf8");
  assert.ok(agent.includes("INSTALL "));
  assert.ok(agent.includes("export_windows_driver_store"));
  assert.ok(agent.includes("Checkpoint-Computer"));
  assert.ok(agent.includes("EulaAccepted"));
  assert.ok(!agent.includes("AcceptEula"));
  assert.ok(!agent.toLowerCase().includes("flash firmware"));
});
