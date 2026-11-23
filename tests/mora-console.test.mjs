import test from "node:test";
import assert from "node:assert/strict";
import {
  createGamepadInput,
  findDirectionalTarget,
  isEditableTarget,
  mapGamepadButton
} from "../mora/console-navigation.js";

function item(name, left, top, width = 100, height = 50) {
  return {
    name,
    disabled: false,
    hidden: false,
    getAttribute() { return null; },
    getBoundingClientRect() { return { left, top, width, height }; }
  };
}

test("standard Xbox-style face buttons map to stable console actions", () => {
  assert.equal(mapGamepadButton(0), "select");
  assert.equal(mapGamepadButton(1), "back");
  assert.equal(mapGamepadButton(2), "details");
  assert.equal(mapGamepadButton(3), "search");
  assert.equal(mapGamepadButton(12), "up");
  assert.equal(mapGamepadButton(13), "down");
  assert.equal(mapGamepadButton(14), "left");
  assert.equal(mapGamepadButton(15), "right");
  assert.equal(mapGamepadButton(9), null);
});

test("directional focus chooses the nearest candidate in the requested half-plane", () => {
  const current = item("current", 100, 100);
  const right = item("right", 240, 110);
  const diagonal = item("diagonal", 190, 190);
  const left = item("left", 0, 100);
  const all = [current, right, diagonal, left];
  assert.equal(findDirectionalTarget(all, current, "right"), right);
  assert.equal(findDirectionalTarget(all, current, "down"), diagonal);
  assert.equal(findDirectionalTarget(all, current, "left"), left);
  assert.equal(findDirectionalTarget(all, current, "up"), null);
});

test("initial directional focus starts at the first visible element", () => {
  const later = item("later", 200, 40);
  const first = item("first", 20, 20);
  assert.equal(findDirectionalTarget([later, first], null, "right"), first);
});

test("text-entry controls are excluded from global controller shortcuts", () => {
  const input = { closest(selector) { return selector.includes("input") ? this : null; } };
  const button = { closest() { return null; } };
  assert.equal(isEditableTarget(input), true);
  assert.equal(isEditableTarget(button), false);
});

test("gamepad polling emits edge-triggered button actions and directional moves", () => {
  let poll;
  let pad;
  const events = [];
  const listeners = new Map();
  const win = {
    navigator: { getGamepads: () => [pad] },
    addEventListener(name, callback) { listeners.set(name, callback); },
    removeEventListener(name) { listeners.delete(name); }
  };
  const controller = createGamepadInput({
    windowRef: win,
    requestFrame(callback) { poll = callback; return 7; },
    cancelFrame() {},
    onAction(action) { events.push(["action", action]); },
    onDirection(direction) { events.push(["direction", direction]); }
  });
  pad = {
    index: 0,
    connected: true,
    buttons: Array.from({ length: 16 }, () => ({ pressed: false, value: 0 })),
    axes: [0, 0]
  };
  controller.start();
  assert.equal(controller.running, true);
  pad.buttons[0] = { pressed: true, value: 1 };
  pad.buttons[14] = { pressed: true, value: 1 };
  poll();
  poll();
  pad.buttons[0] = { pressed: false, value: 0 };
  pad.buttons[14] = { pressed: false, value: 0 };
  pad.axes = [0.9, 0];
  poll();
  poll();
  assert.deepEqual(events, [
    ["action", "select"],
    ["direction", "left"],
    ["direction", "right"]
  ]);
  controller.stop();
  assert.equal(controller.running, false);
});
