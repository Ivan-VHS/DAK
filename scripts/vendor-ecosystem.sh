#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY="$ROOT/federation/repositories.v1.json"
SOURCES="$ROOT/federation/vendor-sources.v1.json"
MODE="${1:---verify}"

fail() {
    echo "DuckOS monorepo vendor: $*" >&2
    exit 1
}

for tool in git jq; do
    command -v "$tool" >/dev/null 2>&1 || fail "required tool is missing: $tool"
done

[[ -f "$REGISTRY" && -f "$SOURCES" ]] || fail "source registry or vendor lock is missing"
git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not a Git worktree"

jq -e '
    .schema == "duckos.repository-federation.v1"
    and .checkout_strategy == "vendored-monorepo"
    and .projects_root == "projects"
    and (.repositories | length == 4)
' "$REGISTRY" >/dev/null || fail "repository registry is invalid"

jq -e '
    .schema == "duckos.vendor-sources.v1"
    and .strategy == "git-subtree-squash"
    and .projects_root == "projects"
    and (.sources | length == 4)
' "$SOURCES" >/dev/null || fail "vendor source lock is invalid"

jq -e --slurpfile registry "$REGISTRY" '
    all(.sources[];
        . as $source
        | any($registry[0].repositories[];
            .id == $source.id
            and .repository == $source.repository
            and .path == $source.path
            and .pinned_commit == $source.upstream_commit
            and .upstream_tree_sha == $source.upstream_tree_sha
            and .source_files == $source.file_count
            and .source_bytes == $source.content_bytes
            and .license == $source.license
        )
    )
' "$SOURCES" >/dev/null || fail "vendor lock and repository registry disagree"

verify_sources() {
    local id path expected_tree expected_files expected_bytes actual_line mode object_type actual_tree
    local actual_files actual_bytes

    if git -C "$ROOT" ls-tree --name-only HEAD -- .gitmodules | grep -q .; then
        fail ".gitmodules still exists; the monorepo must not depend on submodule initialization"
    fi

    while IFS=$'\t' read -r id path expected_tree expected_files expected_bytes; do
        actual_line="$(git -C "$ROOT" ls-tree HEAD -- "$path")"
        [[ -n "$actual_line" ]] || fail "$path is missing from the committed tree"
        read -r mode object_type actual_tree _ <<<"$actual_line"

        [[ "$mode" == "040000" && "$object_type" == "tree" ]] || fail "$path is not a normal tracked directory"
        [[ "$actual_tree" == "$expected_tree" ]] || fail "$path tree mismatch: expected $expected_tree, got $actual_tree"
        [[ -f "$ROOT/$path/LICENSE" ]] || fail "$path is missing its upstream LICENSE file"

        actual_files="$(git -C "$ROOT" ls-tree -r --name-only HEAD -- "$path" | wc -l | tr -d ' ')"
        actual_bytes="$(git -C "$ROOT" ls-tree -r -l HEAD -- "$path" | awk '{ total += $4 } END { printf "%.0f", total }')"
        [[ "$actual_files" == "$expected_files" ]] || fail "$path file count mismatch: expected $expected_files, got $actual_files"
        [[ "$actual_bytes" == "$expected_bytes" ]] || fail "$path byte count mismatch: expected $expected_bytes, got $actual_bytes"

        printf 'vendored %-12s tree=%s files=%s bytes=%s\n' "$id" "$actual_tree" "$actual_files" "$actual_bytes"
    done < <(jq -r '.sources[] | [.id, .path, .upstream_tree_sha, .file_count, .content_bytes] | @tsv' "$SOURCES")
}

if [[ "$MODE" == "--verify" ]]; then
    verify_sources
    echo "DuckOS vendored source validation: passed"
    exit 0
fi

[[ "$MODE" == "--import" ]] || fail "usage: $0 [--verify|--import]"

if [[ -n "$(git -C "$ROOT" status --porcelain --untracked-files=all)" ]]; then
    fail "working tree is not clean; refusing to overwrite local changes"
fi

removed_gitlinks=0
while IFS=$'\t' read -r id path; do
    line="$(git -C "$ROOT" ls-tree HEAD -- "$path")"
    [[ -n "$line" ]] || continue
    read -r mode object_type _ _ <<<"$line"

    if [[ "$mode" == "160000" && "$object_type" == "commit" ]]; then
        git -C "$ROOT" rm -f -- "$path"
        removed_gitlinks=1
    elif [[ "$mode" == "040000" && "$object_type" == "tree" ]]; then
        :
    else
        fail "$path has unexpected Git entry mode $mode"
    fi
done < <(jq -r '.sources[] | [.id, .path] | @tsv' "$SOURCES")

if [[ -f "$ROOT/.gitmodules" ]]; then
    git -C "$ROOT" rm -f -- .gitmodules
    removed_gitlinks=1
fi

if [[ "$removed_gitlinks" -eq 1 ]]; then
    git -C "$ROOT" commit -m "build(monorepo): replace ecosystem gitlinks with source directories"
fi

while IFS=$'\t' read -r id path url commit expected_tree; do
    line="$(git -C "$ROOT" ls-tree HEAD -- "$path")"
    if [[ -n "$line" ]]; then
        read -r mode object_type actual_tree _ <<<"$line"
        if [[ "$mode" == "040000" && "$object_type" == "tree" ]]; then
            [[ "$actual_tree" == "$expected_tree" ]] || fail "$path already exists with a different tree; refusing overwrite"
            continue
        fi
        fail "$path is occupied by an unexpected Git object"
    fi

    echo "Importing $id at $commit"
    git -C "$ROOT" subtree add --prefix="$path" "$url" "$commit" --squash
done < <(jq -r '.sources[] | [.id, .path, .upstream_url, .upstream_commit, .upstream_tree_sha] | @tsv' "$SOURCES")

verify_sources
echo "DuckOS monorepo import: complete"
