import test from "node:test";
import assert from "node:assert/strict";
import { composeJoraRequest } from "../mora/jora.js";

test("Jora composes selected features into a deterministic product formula", () => {
  const result = composeJoraRequest({
    components: ["text.editor", "audio.editor", "translation.workspace"],
    locales: ["en", "ru", "uk", "most"],
    preferredLocale: "ru"
  });
  assert.equal(result.name, "LexiTone 3D");
  assert.equal(result.formula, "Text Editor + Audio Editor + Translator");
  assert.deepEqual(result.request.components,
    ["text.editor", "audio.editor", "translation.workspace"]);
  assert.deepEqual(result.generatedLocales, ["en", "ru", "uk", "most"]);
  assert.equal(result.request.schema, "reaper.jora.request.v1");
  assert.equal(result.request.name, "LexiTone 3D");
  assert.equal(result.request.language_targets, "auto");
});

test("Jora allows a custom product name and a subset of locales", () => {
  const result = composeJoraRequest({
    name: "My Workspace",
    components: ["text.editor"],
    locales: ["uk"],
    preferredLocale: "uk"
  });
  assert.equal(result.name, "My Workspace");
  assert.equal(result.formula, "Text Editor");
  assert.deepEqual(result.request.locales, ["uk"]);
});

test("Jora rejects an empty feature selection and unknown components", () => {
  assert.throws(() => composeJoraRequest({ components: [], locales: ["en"] }));
  assert.throws(() => composeJoraRequest({
    components: ["text.editor", "unknown.pack"], locales: ["en"]
  }), /Unknown Jora component/);
});

test("Jora rejects duplicate components, locales and invalid primary locale", () => {
  assert.throws(() => composeJoraRequest({
    components: ["text.editor", "text.editor"], locales: ["en"]
  }), /Duplicate Jora component/);
  assert.throws(() => composeJoraRequest({
    components: ["text.editor"], locales: ["en", "en"]
  }), /Duplicate interface language/);
  assert.throws(() => composeJoraRequest({
    components: ["text.editor"], locales: ["en"], preferredLocale: "ru"
  }), /primary language/);
});

test("Jora bounds metadata before exporting a request", () => {
  assert.throws(() => composeJoraRequest({
    name: "x".repeat(81), components: ["text.editor"], locales: ["en"]
  }), /exceeds 80/);
});
