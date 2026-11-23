import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("Mora exposes every entry from the fifteen-app system utility catalogue", async () => {
  const catalogue = JSON.parse(await readFile(
    new URL("../catalogs/system-applications.v1.json", import.meta.url), "utf8"
  ));
  const appSource = await readFile(new URL("../mora/app.js", import.meta.url), "utf8");
  const index = await readFile(new URL("../mora/index.html", import.meta.url), "utf8");
  const apps = JSON.parse(await readFile(new URL("../mora/apps.json", import.meta.url), "utf8"));

  assert.equal(catalogue.applications.length, 15);
  assert.match(appSource, /case "system-apps"/);
  assert.match(index, /data-app="system-apps"/);
  assert.ok(apps.built_in_apps.some((app) => app.id === "system-apps"));

  for (const application of catalogue.applications) {
    assert.ok(
      appSource.includes('id: "' + application.id + '"'),
      "Mora is missing " + application.id
    );
  }
});
