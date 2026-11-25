import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const theme = JSON.parse(read("../mora/theme.json"));
const css = read("../mora/styles.css");
const native = read("../mora/native/main.cpp");
const worker = read("../mora/service-worker.js");

test("Mora theme exposes the shared Imperial Noir and Industrial Glass palette", () => {
  const palette = theme.palettes.duck;
  assert.equal(theme.version, 3);
  assert.equal(palette.canvas, "#050505");
  assert.equal(palette.page, "#070707");
  assert.equal(palette.brand, "#FFD700");
  assert.equal(palette.muted, "#929292");
  assert.equal(palette.success, "#55C78A");
  assert.equal(palette.danger, "#ED6874");
  assert.equal(palette.info, "#74A9FF");
});

test("browser shell uses semantic glass and accessible interaction tokens", () => {
  assert.match(css, /--glass:\s*rgba\(15, 15, 15, \.72\)/);
  assert.match(css, /--mora-brand:\s*#FFD700/);
  assert.match(css, /button:focus-visible, a:focus-visible/);
  assert.match(css, /prefers-reduced-motion:reduce/);
});

test("native shell reads the same theme and keeps keyboard-focused controls visible", () => {
  assert.match(native, /DUCKOS_MORA_THEME_PATH/);
  assert.match(native, /QPushButton:focus/);
  assert.match(native, /QLineEdit:focus, QComboBox:focus/);
  assert.match(native, /QColor kBrand\("#FFD700"\)/);
});

test("service worker uses a new cache namespace for the updated shell", () => {
  assert.match(worker, /mora-shell-v10-imperial-glass/);
  assert.match(worker, /\.\/theme\.json/);
});
