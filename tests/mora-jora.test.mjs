import test from "node:test";
import assert from "node:assert/strict";

import {
  analyzeJora,
  analyzeJoraFormula,
  buildJoraGraph
} from "../mora/jora.js";

test("Russian and English aliases resolve to a canonical formula", () => {
  const result = analyzeJoraFormula("текстовый редактор + audio editor + переводчик");
  assert.equal(result.ok, true);
  assert.deepEqual(result.ids, ["text_editor", "audio_editor", "translator"]);
});

test("the canonical three-component composition proposes SlovoVolna", () => {
  const result = analyzeJora("текстовый редактор + аудиоредактор + переводчик");
  assert.equal(result.ok, true);
  assert.equal(result.identity.name, "Слововолна");
  assert.equal(result.identity.slug, "slovovolna");
  assert.equal(result.status, "browser_preview_only");
  assert.match(result.command, /duckos jora create/);
});

test("duplicate components and incompatible offline/cloud requirements are rejected", () => {
  assert.equal(analyzeJoraFormula("заметки + notes").ok, false);
  assert.match(
    analyzeJoraFormula("строго офлайн + облачный стриминг").error,
    /несовместим/
  );
});

test("graph expansion is bounded by the configured local neighborhood", () => {
  const formula = analyzeJoraFormula(
    "текстовый редактор + аудиоредактор + переводчик + глоссарий + субтитры + заметки + канбан"
  );
  assert.equal(formula.ok, true);
  const graph = buildJoraGraph(formula.components, 2);
  assert.equal(graph.nodes.length, formula.components.length + 1);
  assert.ok(graph.edges.length <= formula.components.length * 3);
  assert.equal(graph.growth, "O(N*M*K)");
});

test("the profile includes Reaper and explains optional helper toolchains", () => {
  const result = analyzeJora("аудиоредактор + переводчик", "desktop");
  assert.equal(result.languages[0].language, "Reaper");
  assert.ok(result.languages.some((row) => row.language === "Python"));
  assert.ok(result.languages.some((row) => row.language === "Rust or C"));
});
