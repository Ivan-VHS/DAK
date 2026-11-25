import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";
import { createMoraDemoServer } from "../scripts/mora-demo-server.mjs";

const root = new URL("../", import.meta.url);
const read = file => readFile(new URL(file, root), "utf8");

const [html, css, js] = await Promise.all([
  read("mora/demo.html"),
  read("mora/demo.css"),
  read("mora/demo.js")
]);

test("desktop demo references its local styles and script", () => {
  assert.match(html, /href="demo\.css"/);
  assert.match(html, /src="demo\.js"/);
  assert.doesNotMatch(html, /https?:\/\//i);
  assert.doesNotMatch(css, /@import\s+url\(/i);
});

test("desktop demo JavaScript parses without browser globals at load time", () => {
  assert.doesNotThrow(() => new vm.Script(js, { filename: "mora/demo.js" }));
});

test("desktop demo exposes all 34 catalogue entries", () => {
  const tick = String.fromCharCode(96);
  const catalogueStart = js.indexOf("const apps=");
  const contentStart = catalogueStart >= 0 ? js.indexOf(tick, catalogueStart) + 1 : -1;
  const catalogueEnd = contentStart > 0 ? js.indexOf(tick + ".split", contentStart) : -1;
  const recordsStart = js.indexOf("const records = [");
  const recordsEnd = recordsStart >= 0 ? js.indexOf("].map", recordsStart) : -1;
  const ids = contentStart > 0 && catalogueEnd > contentStart
    ? js.slice(contentStart, catalogueEnd).split("\n").filter(Boolean).map(line => line.split("|")[0])
    : [...js.slice(recordsStart, recordsEnd).matchAll(/\["([^"]+)","[^"]+","[^"]+","[^"]+"\]/g)].map(match => match[1]);
  assert.equal(ids.length, 34);
  for (const id of ["cockos", "orriganize", "reaper", "pytyliki", "oplague", "ventusample"]) {
    assert.ok(ids.includes(id), "missing catalogue entry: " + id);
  }
});

test("desktop demo contains the expected window, launcher and tray controls", () => {
  for (const id of ["launcherPanel", "launcherGrid", "launcherSearch", "appWindow", "windowContent", "quickPanel", "notificationPanel", "searchPanel", "dockApps"]) {
    assert.match(html, new RegExp('id="' + id + '"'));
  }
  assert.match(css, /prefers-reduced-motion/);
  assert.match(css, /@media\s*\(max-width:\s*640px\)/);
  assert.match(js, /function minimizeWindow\(\)/);
  assert.match(js, /windowMin.*minimizeWindow/s);
});

test("local server serves the demo and rejects paths outside the allow-list", async t => {
  const server = createMoraDemoServer();
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  t.after(() => new Promise(resolve => server.close(resolve)));

  const address = server.address();
  const origin = "http://127.0.0.1:" + address.port;
  const [page, stylesheet, missing, method] = await Promise.all([
    fetch(origin + "/"),
    fetch(origin + "/mora/demo.css"),
    fetch(origin + "/package.json"),
    fetch(origin + "/", { method: "POST" })
  ]);

  assert.equal(page.status, 200);
  assert.equal(page.url, origin + "/mora/demo.html");
  assert.match(page.headers.get("content-type"), /text\/html/);
  assert.match(page.headers.get("content-security-policy"), /connect-src 'none'/);
  assert.equal(stylesheet.status, 200);
  assert.match(stylesheet.headers.get("content-type"), /text\/css/);
  assert.equal(missing.status, 404);
  assert.equal(method.status, 405);
});