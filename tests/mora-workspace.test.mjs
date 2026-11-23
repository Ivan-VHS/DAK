import test from "node:test";
import assert from "node:assert/strict";
import { VirtualWorkspace, MAX_WORKSPACE_FILE_BYTES } from "../mora/workspace.js";

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
