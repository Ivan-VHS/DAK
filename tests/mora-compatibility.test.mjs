import test from "node:test";
import assert from "node:assert/strict";
import {
  COMPATIBILITY_ENTRIES,
  buildCompatibilityCommand
} from "../mora/compatibility.js";

test("the compatibility catalogue includes runtimes, launchers, graphics layers and macOS tools", () => {
  const names = new Set(COMPATIBILITY_ENTRIES.map((entry) => entry.name));
  for (const name of [
    "Wine", "Proton", "DOSBox / Staging", "Winetricks", "DXVK",
    "vkd3d-proton", "CrossOver", "Bottles", "Lutris", "Heroic",
    "PortProton", "PlayOnLinux", "Whisky", "Kegworks",
    "Game Porting Toolkit", "ReactOS"
  ]) {
    assert.ok(names.has(name), name + " must be documented");
  }
});

test("command builder only emits bounded DuckOS compatibility commands", () => {
  assert.equal(buildCompatibilityCommand("status"), "duckos compatibility status");
  assert.equal(buildCompatibilityCommand("prefixes"), "duckos compatibility prefixes");
  assert.equal(
    buildCompatibilityCommand("create-prefix", { prefix: "games", architecture: "win64" }),
    "duckos compatibility create-prefix --name 'games' --arch win64"
  );
  assert.equal(
    buildCompatibilityCommand("install-component", { prefix: "games", component: "dxvk" }),
    "duckos compatibility install-component --prefix 'games' --component 'dxvk'"
  );
});

test("launch paths are shell-quoted and engine-specific prefix arguments are required", () => {
  assert.equal(
    buildCompatibilityCommand("launch", {
      engine: "wine", prefix: "games", executable: "/home/user/My Game's setup.exe"
    }),
    "duckos compatibility launch --engine wine --prefix 'games' -- '/home/user/My Game'\\''s setup.exe'"
  );
  assert.throws(() => buildCompatibilityCommand("launch", {
    engine: "wine", prefix: "../outside", executable: "/tmp/game.exe"
  }), /Имя префикса/);
  assert.throws(() => buildCompatibilityCommand("launch", {
    engine: "proton", executable: "/tmp/game.exe"
  }), /Steam compatdata path/);
  assert.throws(() => buildCompatibilityCommand("install-component", {
    prefix: "games", component: "arbitrary"
  }), /разрешённом списке/);
});

test("Proton and DOSBox command lines are distinct from Wine prefix commands", () => {
  assert.match(buildCompatibilityCommand("launch", {
    engine: "proton", compatData: "/home/user/Steam/steamapps/compatdata/123", executable: "/games/title.exe"
  }), /--compat-data/);
  assert.match(buildCompatibilityCommand("launch", {
    engine: "dosbox", executable: "/games/OLDGAME.EXE"
  }), /--engine dosbox/);
});
