import test from "node:test";
import assert from "node:assert/strict";
import {
  detectLocale,
  formatItemCount,
  translateText
} from "../mora/i18n.js";

test("saved locale takes precedence over browser preference", () => {
  assert.equal(detectLocale("en", "uk-UA"), "en");
  assert.equal(detectLocale(null, "uk-UA"), "uk");
  assert.equal(detectLocale(null, "en-US"), "en");
  assert.equal(detectLocale(null, "fr-FR"), "ru");
});

test("the same interface phrase can switch RU -> EN -> UK -> RU", () => {
  const russian = "Рабочий стол";
  const english = translateText(russian, "en");
  const ukrainian = translateText(english, "uk");
  const restored = translateText(ukrainian, "ru");
  assert.equal(english, "Desktop");
  assert.equal(ukrainian, "Робочий стіл");
  assert.equal(restored, russian);
});

test("item counts use locale-specific plural forms", () => {
  assert.equal(formatItemCount(1, "ru"), "1 элемент");
  assert.equal(formatItemCount(2, "ru"), "2 элемента");
  assert.equal(formatItemCount(5, "ru"), "5 элементов");
  assert.equal(formatItemCount(1, "uk"), "1 елемент");
  assert.equal(formatItemCount(3, "uk"), "3 елементи");
  assert.equal(formatItemCount(7, "uk"), "7 елементів");
  assert.equal(formatItemCount(1, "en"), "1 item");
  assert.equal(formatItemCount(2, "en"), "2 items");
});

test("unknown labels remain unchanged instead of being guessed", () => {
  assert.equal(translateText("Custom user file name.rpr", "en"), "Custom user file name.rpr");
  assert.equal(translateText("Custom user file name.rpr", "ru"), "Custom user file name.rpr");
});

test("text translation is a pure function and never mutates its input", () => {
  const label = "Настройки";
  assert.equal(translateText(label, "en"), "Settings");
  assert.equal(label, "Настройки");
});
