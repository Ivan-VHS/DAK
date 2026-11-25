import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFile } from "node:fs/promises";

const root = new URL("../", import.meta.url);
const federation = JSON.parse(await readFile(new URL("federation/repositories.v1.json", root), "utf8"));
const vendor = JSON.parse(await readFile(new URL("federation/vendor-sources.v1.json", root), "utf8"));

function git(...args) {
  return execFileSync("git", args, { cwd: root, encoding: "utf8" }).trim();
}

test("DuckOS is a self-contained monorepo with no submodule checkout requirement", () => {
  assert.equal(federation.checkout_strategy, "vendored-monorepo");
  assert.equal(vendor.strategy, "git-fetch-read-tree");
  assert.equal(vendor.sources.length, 4);
  assert.throws(() => git("cat-file", "-e", "HEAD:.gitmodules"));
});

test("every upstream project is a normal directory at its exact source tree", () => {
  assert.deepEqual(
    [...vendor.sources.map((source) => source.id)].sort(),
    [...federation.repositories.map((source) => source.id)].sort()
  );

  for (const source of vendor.sources) {
    const manifest = federation.repositories.find((item) => item.id === source.id);
    assert.equal(source.repository, manifest.repository);
    assert.equal(source.path, manifest.path);
    assert.equal(source.upstream_commit, manifest.pinned_commit);
    assert.equal(source.upstream_tree_sha, manifest.upstream_tree_sha);
    assert.equal(source.license, manifest.license);
    assert.equal(source.commit_signature_verified, true);

    const entry = git("ls-tree", "HEAD", "--", source.path).split(/\s+/);
    assert.equal(entry[0], "040000", source.id + " must be a normal directory");
    assert.equal(entry[1], "tree", source.id);
    assert.equal(entry[2], source.upstream_tree_sha, source.id + " source tree must be exact");

    const files = git("ls-tree", "-r", "--name-only", "HEAD", "--", source.path)
      .split("\n")
      .filter(Boolean);
    assert.equal(files.length, source.file_count, source.id + " file count");
    assert.ok(files.includes(source.path + "/LICENSE"), source.id + " license is preserved");
  }
});

test("the source import remains declarative and does not auto-execute upstream programs", () => {
  assert.ok(federation.repositories.every((source) => source.auto_build === false));
  assert.ok(federation.repositories.every((source) => source.auto_execute === false));
  assert.equal(vendor.total_source_files, vendor.sources.reduce((n, source) => n + source.file_count, 0));
  assert.equal(vendor.total_source_bytes, vendor.sources.reduce((n, source) => n + source.content_bytes, 0));
});
