const BUTTON_ACTIONS = Object.freeze({
  0: "select",
  1: "back",
  2: "details",
  3: "search"
});

const DIRECTION_BUTTONS = Object.freeze({
  12: "up",
  13: "down",
  14: "left",
  15: "right"
});

export function mapGamepadButton(index) {
  return BUTTON_ACTIONS[index] ?? DIRECTION_BUTTONS[index] ?? null;
}

export function isEditableTarget(target) {
  if (!target) return false;
  const element = typeof target.closest === "function"
    ? target.closest("input,textarea,select,[contenteditable='true'],[role='textbox']")
    : null;
  return Boolean(element);
}

function centre(rect) {
  return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
}

export function findDirectionalTarget(elements, activeElement, direction, rectOf = (element) => element.getBoundingClientRect()) {
  if (!["up", "down", "left", "right"].includes(direction)) return null;
  const candidates = Array.from(elements ?? []).filter((element) =>
    element && element !== activeElement && !element.disabled && !element.hidden &&
    element.getAttribute?.("aria-hidden") !== "true"
  );
  if (!candidates.length) return null;

  const activeRect = activeElement ? rectOf(activeElement) : null;
  if (!activeRect) {
    return candidates.sort((a, b) => {
      const first = rectOf(a);
      const second = rectOf(b);
      return first.top - second.top || first.left - second.left;
    })[0];
  }

  const origin = centre(activeRect);
  const ranked = [];
  for (const candidate of candidates) {
    const point = centre(rectOf(candidate));
    const dx = point.x - origin.x;
    const dy = point.y - origin.y;
    const primary = direction === "left" ? -dx
      : direction === "right" ? dx
      : direction === "up" ? -dy : dy;
    if (primary <= 1) continue;
    const secondary = direction === "left" || direction === "right" ? Math.abs(dy) : Math.abs(dx);
    ranked.push({ candidate, score: primary + secondary * 1.8 + Math.hypot(dx, dy) * 0.08 });
  }
  ranked.sort((a, b) => a.score - b.score);
  return ranked[0]?.candidate ?? null;
}

export function createGamepadInput({
  windowRef = globalThis.window,
  onAction = () => {},
  onDirection = () => {},
  onConnection = () => {},
  requestFrame = globalThis.requestAnimationFrame?.bind(globalThis),
  cancelFrame = globalThis.cancelAnimationFrame?.bind(globalThis)
} = {}) {
  let frameId = null;
  let started = false;
  const previousButtons = new Map();
  const axisDirections = new Map();

  function tick() {
    if (!started) return;
    const pads = windowRef?.navigator?.getGamepads?.() ?? [];
    for (const pad of pads) {
      if (!pad || !pad.connected) continue;
      const previous = previousButtons.get(pad.index) ?? [];
      const current = pad.buttons ?? [];
      current.forEach((button, index) => {
        const pressed = Boolean(button?.pressed || (button?.value ?? 0) > 0.7);
        if (pressed && !previous[index]) {
          const mapped = mapGamepadButton(index);
          if (mapped && DIRECTION_BUTTONS[index]) onDirection(mapped, pad);
          else if (mapped) onAction(mapped, pad);
        }
        previous[index] = pressed;
      });
      previousButtons.set(pad.index, previous);

      const axes = pad.axes ?? [];
      const x = Number(axes[0]) || 0;
      const y = Number(axes[1]) || 0;
      const axisDirection = Math.abs(x) > Math.abs(y)
        ? (x > 0.58 ? "right" : x < -0.58 ? "left" : null)
        : (y > 0.58 ? "down" : y < -0.58 ? "up" : null);
      const lastDirection = axisDirections.get(pad.index) ?? null;
      if (axisDirection && !lastDirection) onDirection(axisDirection, pad);
      axisDirections.set(pad.index, axisDirection);
    }
    frameId = requestFrame?.(tick) ?? null;
  }

  function connected(event) {
    previousButtons.delete(event.gamepad.index);
    axisDirections.delete(event.gamepad.index);
    onConnection(true, event.gamepad);
  }

  function disconnected(event) {
    previousButtons.delete(event.gamepad.index);
    axisDirections.delete(event.gamepad.index);
    onConnection(false, event.gamepad);
  }

  return {
    start() {
      if (started) return;
      if (!windowRef?.navigator?.getGamepads || !requestFrame) return;
      started = true;
      windowRef.addEventListener?.("gamepadconnected", connected);
      windowRef.addEventListener?.("gamepaddisconnected", disconnected);
      frameId = requestFrame(tick);
    },
    stop() {
      if (!started) return;
      started = false;
      windowRef?.removeEventListener?.("gamepadconnected", connected);
      windowRef?.removeEventListener?.("gamepaddisconnected", disconnected);
      if (frameId !== null) cancelFrame?.(frameId);
      frameId = null;
      previousButtons.clear();
      axisDirections.clear();
    },
    get running() {
      return started;
    }
  };
}
