import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
const root = new URL("../", import.meta.url);
const html = await readFile(new URL("mora/belle/index.html", root), "utf8");
const js = await readFile(new URL("mora/belle/app.js", root), "utf8");
const css = await readFile(new URL("mora/belle/styles.css", root), "utf8");
const catalog = JSON.parse(await readFile(new URL("catalogs/mora-belle-applications.v1.json", root), "utf8"));
const theme = JSON.parse(await readFile(new URL("mora/belle/theme.json", root), "utf8"));
test("Mora Belle exposes fifteen unique modules with a matching working panel",()=>{
 assert.equal(catalog.applications.length,15);
 assert.equal(new Set(catalog.applications.map(x=>x.id)).size,15);
 for(const item of catalog.applications){assert.ok(js.includes('id:"'+item.id+'"'),item.id);assert.ok(js.includes('case "'+item.id+'"'),item.id);}
});
test("filters, search, dialog and keyboard focus are present",()=>{
 for(const category of ["style","wellbeing","home","growth"])assert.ok(html.includes('data-filter="'+category+'"'));
 assert.ok(html.includes('id="module-grid"'));assert.ok(html.includes('id="module-search"'));assert.ok(html.includes("<dialog"));
 assert.ok(css.includes("button:focus-visible"));assert.ok(css.includes("@media(prefers-reduced-motion:reduce)"));
});
test("cycle and wellbeing notes never enter persistent storage or export",()=>{
 assert.ok(js.includes('const persistentFields = ["wardrobe","beauty","shopping","checkups","chores","places","circles","career","projects"]'));
 assert.ok(js.includes("session.cycle"));assert.ok(js.includes("session.reset"));
 assert.ok(js.includes("Object.fromEntries(storedFields.map"));
 assert.ok(!js.includes('storedFields = ["cycle"'));
});
test("the browser suite makes no remote requests",()=>{
 assert.ok(!/<script[^>]+src=["']https?:/i.test(html));assert.ok(!/<link[^>]+href=["']https?:/i.test(html));
 assert.ok(!/fetch\s*\(/.test(js));assert.ok(html.includes("Личные записи остаются в этом браузере"));
});
test("Belle tokens reserve ornament for decoration and support reduced motion",()=>{
 assert.equal(theme.schema,"mora.belle.theme.v1");assert.equal(theme.ornament.decorativeOnly,true);
 assert.equal(theme.ornament.minimumInteractiveTargetPx,44);assert.equal(theme.motion.reducedMotionRespected,true);
 assert.ok(css.includes("repeating-conic-gradient"));assert.ok(css.includes("@media(max-width:620px)"));
});
