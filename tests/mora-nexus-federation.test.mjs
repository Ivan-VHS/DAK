import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const root = new URL("../", import.meta.url);
const peers = JSON.parse(await readFile(new URL("federation/nexus-peers.v1.json", root), "utf8"));
const federation = JSON.parse(await readFile(new URL("federation/repositories.v1.json", root), "utf8"));

test("NEXUS peer registry follows the exact four-repository source federation", () => {
  assert.equal(peers.schema, "duckos.nexus-peer-registry.v1");
  assert.equal(peers.version, 1);
  assert.equal(peers.integration_host, "DuckOS");
  assert.equal(peers.source_of_revision, "federation/repositories.v1.json");
  assert.equal(peers.topology, "direct-versioned-peer-contracts");
  assert.deepEqual(
    peers.peers.map((peer) => peer.id).sort(),
    federation.repositories.map((repo) => repo.id).sort()
  );
  for (const peer of peers.peers) {
    const source = federation.repositories.find((repo) => repo.id === peer.id);
    assert.equal(peer.repository, source.repository);
    assert.equal(peer.path, source.path);
    assert.ok(peer.contracts.length > 0, peer.id + " must own at least one declared contract");
    assert.ok(peer.prohibited_effects.length > 0, peer.id + " must declare forbidden inferences");
  }
});

test("NEXUS contracts are source-backed and explicitly versioned", () => {
  const ids = new Set();
  for (const peer of peers.peers) {
    for (const contract of peer.contracts) {
      assert.ok(contract.id.endsWith(".v1"), contract.id);
      assert.ok(!ids.has(contract.id), "duplicate contract: " + contract.id);
      ids.add(contract.id);
      assert.ok(contract.source.startsWith(peer.path + "/docs/"), contract.id);
      assert.ok(contract.source.endsWith(".md"), contract.id);
      assert.ok(contract.maturity.length > 0, contract.id);
      assert.ok(contract.consumer_rules.length > 0, contract.id);
    }
  }
});

test("peer contracts cannot create implicit kernel, device or execution privileges", () => {
  assert.equal(peers.policy.peer_optional, true);
  assert.equal(peers.policy.central_runtime_required, false);
  assert.equal(peers.policy.automatic_discovery, false);
  assert.equal(peers.policy.automatic_execution, false);
  assert.equal(peers.policy.kernel_privilege_from_peer_contracts, false);
  assert.equal(peers.policy.device_access_default, "read-only");
  assert.equal(peers.policy.audio_processing_default, "offline");
  assert.ok(peers.policy.desktop_wire_transport.includes("kernel IPC and caller authentication remain pending"));
  assert.ok(peers.peers.every((peer) => peer.prohibited_effects.length > 0));
});
