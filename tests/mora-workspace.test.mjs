import test from "node:test";
import assert from "node:assert/strict";
import { VirtualWorkspace, MAX_WORKSPACE_FILE_BYTES, WORKSPACE_STORAGE_KEY } from "../mora/workspace.js";

function makeStorage() {
  const values = new Map();
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
    removeItem(key) { values.delete(key); }
  };
}

test("workspace starts with a navigable home tree and sample files", () => {
  const workspace = new VirtualWorkspace(makeStorage());
  assert.deepEqual(workspace.path("documents"), ["Home", "Documents"]);
  assert.equal(workspace.get("workspace-rpr").name, "workspace.rpr");
  assert.equal(workspace.list("home").filter((item) => item.type === "folder").length, 6);
});

test("folder and text file creation, rename and removal are persisted", () => {
  const storage = makeStorage();
  const workspace = new VirtualWorkspace(storage);
  const folder = workspace.createFolder("Notes", "documents");
  const file = workspace.createFile("draft.txt", "Hello DuckOS", folder.id);
  assert.equal(workspace.get(file.id).content, "Hello DuckOS");
  workspace.rename(file.id, "final.txt");
  assert.equal(workspace.get(file.id).name, "final.txt");
  assert.equal(workspace.remove(folder.id), 2);

  const restored = new VirtualWorkspace(storage);
  assert.equal(restored.get(folder.id), null);
});

test("sample system files are protected against edits", () => {
  const workspace = new VirtualWorkspace(makeStorage());
  assert.throws(() => workspace.rename("theme-json", "custom.json"), /read-only/);
  assert.throws(() => workspace.remove("theme-json"), /protected/);
});

test("search and sorting operate on current entries", () => {
  const workspace = new VirtualWorkspace(makeStorage());
  workspace.createFile("zeta.txt", "z", "documents");
  workspace.createFile("alpha.txt", "a", "documents");
  const names = workspace.list("documents", { sort: "name" }).map((item) => item.name);
  assert.deepEqual(names, ["alpha.txt", "system-report.duck", "workspace.rpr", "zeta.txt"]);
  assert.equal(workspace.search("workspace").length, 1);
});

test("file size limit is enforced in UTF-8 bytes", () => {
  const workspace = new VirtualWorkspace(makeStorage());
  assert.throws(
    () => workspace.createFile("too-large.txt", "x".repeat(MAX_WORKSPACE_FILE_BYTES + 1)),
    /2 MiB/
  );
  assert.equal(workspace.createFile("small.txt", "ok").size, 2);
});

test("invalid names cannot escape the virtual folder tree", () => {
  const workspace = new VirtualWorkspace(makeStorage());
  for (const name of ["../secrets", "folder/name", "C:\\\\boot.ini", "a:b"]) {
    assert.throws(() => workspace.createFolder(name), /name of up to 120 characters/);
  }
});

test("a malformed or cyclic stored tree is discarded", () => {
  const storage = makeStorage();
  storage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify([
    { id: "home", name: "Home", type: "folder", parentId: null },
    { id: "a", name: "A", type: "folder", parentId: "b" },
    { id: "b", name: "B", type: "folder", parentId: "a" }
  ]));
  const workspace = new VirtualWorkspace(storage);
  assert.equal(workspace.get("a"), null);
  assert.deepEqual(workspace.path("documents"), ["Home", "Documents"]);
});

test("memory-only mode is explicit when storage is unavailable", () => {
  const workspace = new VirtualWorkspace(null);
  const file = workspace.createFile("session.txt", "temporary");
  assert.equal(workspace.persistenceAvailable, false);
  assert.equal(workspace.get(file.id).content, "temporary");
});
