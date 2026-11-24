import test from "node:test";
import assert from "node:assert/strict";
import { composeJoraRequest } from "../mora/jora.js";

test("Jora composes selected features into a deterministic product formula", () => {
  const result = composeJoraRequest({
    components: ["text.editor", "audio.editor", "translation.workspace"],
    locales: ["en", "ru", "uk", "most"],
    preferredLocale: "ru"
  });
  assert.equal(result.name, "Jora");
  assert.equal(result.formula, "Text Editor + Audio Editor + Translator");
  assert.deepEqual(result.request.components,
    ["text.editor", "audio.editor", "translation.workspace"]);
  assert.deepEqual(result.generatedLocales, ["en", "ru", "uk", "most"]);
  assert.equal(result.request.schema, "reaper.jora.request.v1");
  assert.equal(result.request.name, "Jora");
  assert.equal(result.request.language_targets, "auto");
  assert.equal(result.request.name_style, "balanced");
  assert.deepEqual(result.request.graph, { topology: "auto", objective: "balanced", seed: "", variants: 4, variation: 50 });
  assert.equal(result.nameSuggestions.length, 4);
  assert.ok(result.nameSuggestions.every((label) => label.startsWith("Jora")));
});

test("Jora can mark additional compiler targets as pending adapters", () => {
  const result = composeJoraRequest({
    components: ["text.editor", "translation.workspace"],
    locales: ["ru", "uk"],
    preferredLocale: "ru",
    languageTargets: ["java", "typescript"]
  });
  assert.deepEqual(result.languageTargets, ["reaper", "java", "typescript"]);
  assert.deepEqual(result.pendingTargets, ["java", "typescript"]);
  assert.deepEqual(result.request.language_targets, ["reaper", "java", "typescript"]);
});

test("Jora keeps its canonical name while allowing a locale subset", () => {
  const result = composeJoraRequest({
    name: "Jora",
    components: ["text.editor"],
    locales: ["uk"],
    preferredLocale: "uk"
  });
  assert.equal(result.name, "Jora");
  assert.equal(result.formula, "Text Editor");
  assert.deepEqual(result.request.locales, ["uk"]);
});

test("Jora allows graph topology, variant count and variation to be selected", () => {
  const result = composeJoraRequest({
    components: ["text.editor", "translation.workspace"],
    locales: ["ru"],
    preferredLocale: "ru",
    graphTopology: "event_driven",
    graphVariants: 2,
    graphVariation: 80,
    graphObjective: "modularity",
    graphSeed: "user-seed-42",
    nameStyle: "descriptive"
  });
  assert.equal(result.request.name, "Jora");
  assert.equal(result.request.name_style, "descriptive");
  assert.deepEqual(result.request.graph, {
    topology: "event_driven", objective: "modularity", seed: "user-seed-42", variants: 2, variation: 80
  });
  assert.equal(result.graphPlan.topologyLabel, "Событийная архитектура");
  assert.equal(result.graphPlan.objectiveLabel, "Модульность");
  assert.equal(result.graphPlan.variants, 2);
  assert.equal(result.graphPlan.seed, "user-seed-42");
});

test("Jora rejects unsupported graph and naming options", () => {
  const base = { components: ["text.editor"], locales: ["en"] };
  assert.throws(() => composeJoraRequest({ ...base, graphTopology: "random" }), /Unsupported Jora graph topology/);
  assert.throws(() => composeJoraRequest({ ...base, graphObjective: "random" }), /Unsupported Jora graph objective/);
  assert.throws(() => composeJoraRequest({ ...base, graphVariants: 7 }), /from 1 to 6/);
  assert.throws(() => composeJoraRequest({ ...base, graphVariation: 101 }), /from 0 to 100/);
  assert.throws(() => composeJoraRequest({ ...base, nameStyle: "invented" }), /Unsupported Jora naming style/);
  assert.throws(() => composeJoraRequest({ ...base, graphSeed: "x".repeat(65) }), /exceeds 64/);
});

test("Jora refuses separately branded application names", () => {
  assert.throws(() => composeJoraRequest({
    name: "OtherProduct",
    components: ["text.editor"],
    locales: ["en"]
  }), /fixed application name/);
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
