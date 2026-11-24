import test from "node:test";
import assert from "node:assert/strict";
import { JORA_PARAMETER_REGISTRY, parseJoraFormula, buildJoraGraph, buildJoraPackage } from "../mora/jora-core.js";

test("Jora parses multilingual formulas into canonical IDs", () => {
  const components = parseJoraFormula("текстовый редактор + audio editor + переводчик");
  assert.deepEqual(components.map((item) => item.id), ["text_editor", "audio_editor", "translator"]);
  assert.equal(components[0].role, "primary");
});

test("Jora rejects unknown, duplicate, conflicting and oversized formulas", () => {
  for (const formula of ["text editor + missing item", "translator + переводчик", "offline mode + cloud translation", "x".repeat(2049)]) {
    assert.throws(() => parseJoraFormula(formula));
  }
});

test("the three-component graph includes all pairwise synergy edges", () => {
  const graph = buildJoraGraph(parseJoraFormula("text editor + audio editor + translator"));
  assert.equal(graph.topology, "dense-triad");
  assert.equal(graph.edges.filter((item) => item.kind === "domain_synergy").length, 3);
  assert.ok(graph.nodes.some((item) => item.id === "reaper:core"));
  assert.ok(graph.nodes.some((item) => item.id === "data:unified-project"));
});

test("large formulas switch to bounded cluster graph growth", () => {
  const seed = parseJoraFormula("text editor + audio editor + translator");
  const components = Array.from({ length: 21 }, (_, index) => ({ ...seed[index % 3], id: seed[index % 3].id + "_" + index }));
  const graph = buildJoraGraph(components);
  assert.equal(graph.topology, "clustered-hub");
  assert.ok(graph.edges.length <= components.length * 3 + Object.keys(graph.clusters).length);
});

test("Jora creates a Reaper-first source draft and connected demo segments", () => {
  assert.ok(JORA_PARAMETER_REGISTRY.length >= 9);
  const result = buildJoraPackage("текстовый редактор + аудиоредактор + переводчик");
  assert.equal(result.displayName, "Слововолна");
  assert.equal(result.languages[0].id, "reaper");
  assert.match(result.reaperSource, /make app_name/);
  assert.equal(result.demo.segments.length, 4);
  assert.ok(result.demo.segments.every((item) => item.audioRef && item.translatedText && item.sourceText));
  assert.equal(result.manifest.maturity.installed, false);
});
