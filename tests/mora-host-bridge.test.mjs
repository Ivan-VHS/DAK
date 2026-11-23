import test from "node:test";
import assert from "node:assert/strict";
import {
  createNativeHostBridge,
  normalizeHostEndpoint
} from "../mora/host-bridge.js";

const token = "a".repeat(43);

function response(payload, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    async json() { return payload; }
  };
}

test("native host URL is restricted to loopback HTTP endpoints", () => {
  assert.equal(normalizeHostEndpoint(), "http://127.0.0.1:8765");
  assert.equal(normalizeHostEndpoint("http://localhost:8765"), "http://localhost:8765");
  assert.throws(() => normalizeHostEndpoint("https://127.0.0.1:8765"), /loopback/);
  assert.throws(() => normalizeHostEndpoint("http://example.com:8765"), /loopback/);
  assert.throws(() => normalizeHostEndpoint("http://127.0.0.1:8765/path"), /loopback/);
});

test("bridge authenticates health and JSON-RPC requests without shell payloads", async () => {
  const calls = [];
  const store = new Map();
  const fetcher = async (url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/health")) {
      return response({ service: "duckos-native-host", status: "ready" });
    }
    return response({
      jsonrpc: "2.0",
      id: 1,
      result: { host: "Linux", display_backend: "x11", native_x11_compositor_installed: true }
    });
  };
  const bridge = createNativeHostBridge({
    fetcher,
    storage: {
      getItem: key => store.get(key) || null,
      setItem: (key, value) => store.set(key, value),
      removeItem: key => store.delete(key)
    }
  });
  const host = await bridge.connect(token);
  assert.equal(host.host, "Linux");
  assert.equal(bridge.isConnected(), true);
  assert.equal(store.size, 1);
  assert.equal(calls[0].options.credentials, "omit");
  assert.equal(calls[1].options.headers.Authorization, "Bearer " + token);
  const request = JSON.parse(calls[1].options.body);
  assert.deepEqual(request, { id: 1, method: "host.status", params: {} });
  assert.equal("command" in request, false);
  bridge.disconnect();
  assert.equal(bridge.isConnected(), false);
  assert.equal(store.size, 0);
});

test("bridge rejects malformed tokens and non-loopback endpoints before a request", () => {
  assert.throws(() => createNativeHostBridge({ endpoint: "http://duckos.example" }), /loopback/);
  const bridge = createNativeHostBridge({ fetcher: async () => { throw new Error("must not run"); } });
  assert.rejects(() => bridge.connect("too-short"), /формат/);
});
