import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const catalog = JSON.parse(await readFile(new URL("../catalogs/nexus-system-services.v1.json", import.meta.url), "utf8"));
const schema = JSON.parse(await readFile(new URL("../schemas/nexus-system-services.v1.schema.json", import.meta.url), "utf8"));

test("NEXUS registry preserves DAKOS and Reaper identities", () => {
  assert.equal(catalog.schema, "dakos.nexus-system-services.v1");
  assert.equal(catalog.identity.operating_system, "DAKOS");
  assert.equal(catalog.identity.systems_language, "Reaper");
  assert.equal(catalog.identity.repository_identity_policy, "immutable");
});

test("NEXUS registry contains the eight canonical component roles", () => {
  assert.deepEqual(new Set(catalog.components.map((item) => item.name)), new Set(["KernelCore", "NexusShell", "AudioSubsys", "SecurityModule", "NetworkStack", "GraphicsEngine", "BuildToolchain", "AILayer"]));
  assert.equal(new Set(catalog.components.map((item) => item.id)).size, 8);
});

test("six system services have explicit prerequisites and valid dependencies", () => {
  assert.deepEqual(new Set(catalog.services.map((item) => item.name)), new Set(["KERNEL_SENTINEL", "MEMORY_FORGE", "VECTOR_GATEWAY", "PIXEL_PIPELINE", "DATA_ORCHESTRATOR", "BUILD_VANGUARD"]));
  assert.equal(new Set(catalog.services.map((item) => item.id)).size, 6);
  const componentIds = new Set(catalog.components.map((item) => item.id));
  for (const service of catalog.services) {
    assert.equal(service.runtime_state, "not_implemented", service.name);
    assert.equal(service.maturity, "specified", service.name);
    assert.ok(service.prerequisites.length >= 2, service.name);
    assert.ok(service.safety_boundary.length >= 25, service.name);
    for (const dependency of service.component_dependencies) assert.ok(componentIds.has(dependency), service.name + " has unknown dependency " + dependency);
  }
});

test("schema closes the v1 contract and fixes catalog cardinality", () => {
  assert.equal(schema.$schema, "https://json-schema.org/draft/2020-12/schema");
  assert.equal(schema.additionalProperties, false);
  assert.equal(schema.properties.components.minItems, 8);
  assert.equal(schema.properties.components.maxItems, 8);
  assert.equal(schema.properties.services.minItems, 6);
  assert.equal(schema.properties.services.maxItems, 6);
});
