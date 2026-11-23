import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { mountRuntimeManager } from "../mora/runtime-manager.js";

const app = await readFile(new URL("../mora/app.js", import.meta.url), "utf8");
const html = await readFile(new URL("../mora/index.html", import.meta.url), "utf8");
const worker = await readFile(new URL("../mora/service-worker.js", import.meta.url), "utf8");
const moduleSource = await readFile(new URL("../mora/runtime-manager.js", import.meta.url), "utf8");

test("the existing Bridge system app mounts the host process manager", () => {
  assert.ok(app.includes('import { mountRuntimeManager } from "./runtime-manager.js"'));
  assert.ok(app.includes('data-runtime-manager'));
  assert.ok(app.includes('mountRuntimeManager(appWindow)'));
});

test("Mora ships the manager styles and offline module in its own cache scope", () => {
  assert.ok(html.includes('href="runtime-manager.css"'));
  assert.ok(worker.includes('"./runtime-manager.css"'));
  assert.ok(worker.includes('"./runtime-manager.js"'));
  assert.ok(worker.includes("mora-shell-v3-runtime"));
});

test("the browser bridge uses an authenticated loopback endpoint and does not persist pairing tokens", () => {
  assert.ok(moduleSource.includes('http://127.0.0.1:47682'));
  assert.ok(moduleSource.includes('Authorization'));
  assert.ok(moduleSource.includes('duckos.runtime.v1'));
  assert.ok(moduleSource.includes('credentials: "omit"'));
  assert.ok(!moduleSource.includes("localStorage"));
  assert.ok(!moduleSource.includes("sessionStorage"));
  assert.ok(!moduleSource.includes("child_process"));
  assert.equal(typeof mountRuntimeManager, "function");
});

test("launch and import controls require an explicit host approval choice", () => {
  assert.ok(moduleSource.includes("approved:true"));
  assert.ok(moduleSource.includes("allow_unisolated:hostConsent.checked"));
  assert.ok(moduleSource.includes("window.confirm"));
  assert.ok(moduleSource.includes("X-DuckOS-Filename"));
  assert.ok(moduleSource.includes("X-DuckOS-Entrypoint"));
});
