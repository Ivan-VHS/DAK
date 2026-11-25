import test from "node:test";
import assert from "node:assert/strict";
import { createLocalDocumentStore } from "../mora/local-store.js";

class MemoryStorage {
  constructor() {
    this.values = new Map();
  }

  getItem(key) {
    return this.values.has(key) ? this.values.get(key) : null;
  }

  setItem(key, value) {
    this.values.set(key, String(value));
  }

  removeItem(key) {
    this.values.delete(key);
  }
}

test("recovery documents migrate to the DAK identifier without losing their data", async () => {
  const storage = new MemoryStorage();
  const previousRecord = {
    id: "duckos.mora.recovery.v1",
    data: { focusMode: true, powerProfile: "performance" },
    updatedAt: "2026-11-25T12:00:00.000Z"
  };
  storage.setItem(
    "duckos.mora.localdoc.v1:duckos.mora.recovery.v1",
    JSON.stringify(previousRecord)
  );

  const store = createLocalDocumentStore({ indexedDB: null, storage });
  const value = await store.get("dak.mora.recovery.v1");

  assert.deepEqual(value, previousRecord.data);
  const migrated = JSON.parse(storage.getItem("dak.mora.localdoc.v1:dak.mora.recovery.v1"));
  assert.equal(migrated.id, "dak.mora.recovery.v1");
  assert.deepEqual(migrated.data, previousRecord.data);
  assert.equal(await store.remove("dak.mora.recovery.v1"), true);
  assert.equal(storage.getItem("duckos.mora.localdoc.v1:duckos.mora.recovery.v1"), null);
});

test("new local documents are written only under DAK storage keys", async () => {
  const storage = new MemoryStorage();
  const store = createLocalDocumentStore({
    indexedDB: null,
    storage,
    now: () => "2026-11-25T12:00:00.000Z"
  });

  const result = await store.put("mora.notes.v1", { title: "DAK notes" });
  assert.equal(result.ok, true);
  assert.ok(storage.getItem("dak.mora.localdoc.v1:mora.notes.v1"));
  assert.equal(storage.getItem("duckos.mora.localdoc.v1:mora.notes.v1"), null);
});
