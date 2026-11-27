import assert from "node:assert/strict";
import { chromium } from "playwright";

const baseUrl = process.argv[2] || "http://127.0.0.1:8765";
const projects = [
  { id: "reaper-workbench", name: "Reaper", readme: "../projects/reaper/README.md" },
  { id: "pytyliki-workbench", name: "Pytyliki", readme: "../projects/pytyliki/README.md" },
  { id: "oplague-workbench", name: "OPlague", readme: "../projects/oplague/README.md" },
  { id: "ventusample-workbench", name: "VentuSample", readme: "../projects/ventusample/README.md" }
];

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));

  const response = await page.goto(new URL("/mora/", baseUrl).href, { waitUntil: "networkidle" });
  assert.equal(response?.status(), 200, "Mora desktop HTML must load");
  assert.equal(await page.title(), "DAK Desktop — Ivan-VHS");

  for (const project of projects) {
    await page.locator('[data-app="' + project.id + '"]').click();
    const window = page.locator('.app-window[data-window="' + project.id + '"]');
    await window.waitFor({ state: "visible" });
    assert.equal((await window.locator(".window-heading").innerText()).trim(), project.name);
    const sourceLink = window.locator('a[href="' + project.readme + '"]');
    assert.equal(await sourceLink.count(), 1, project.name + " README link must be present");
    const sourceResponse = await page.request.get(new URL(project.readme, page.url()).href);
    assert.equal(sourceResponse.status(), 200, project.name + " README must be reachable from the ISO payload");
    assert.equal(await window.locator('a[href="../projects/' + project.id.replace("-workbench", "") + '/LICENSE"]').count(), 1);
    await window.locator('[data-action="close"]').click();
    await window.waitFor({ state: "hidden" });
  }

  await page.locator('.app-tile[data-app="workspace"]').click();
  await page.locator('.app-window[data-window="workspace"]').waitFor({ state: "visible" });
  assert.equal(pageErrors.length, 0, "Mora must not produce uncaught browser errors: " + pageErrors.join("; "));
  console.log("DAK desktop browser smoke test passed: desktop loaded, four native workbench panels opened, source links resolved, windows closed.");
} finally {
  await browser.close();
}
