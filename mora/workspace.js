const STORAGE_KEY = "duckos.mora.workspace.v1";
const MAX_FILE_BYTES = 2 * 1024 * 1024;
const INVALID_NAME = /[\\\\/:*?"<>|]/;

function makeId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return "item-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
}

function byteLength(value) {
  return new TextEncoder().encode(String(value)).length;
}

function cleanName(value) {
  const name = String(value ?? "").trim();
  if (!name || name.length > 120 || INVALID_NAME.test(name) || name === "." || name === "..") {
    throw new Error("Use a name of up to 120 characters without \\ / : * ? \" < > |.");
  }
  return name;
}

function defaultStorage() {
  try { return globalThis.localStorage ?? null; } catch { return null; }
}

function seedItems() {
  const now = new Date().toISOString();
  const folder = (id, name) => ({ id, name, type: "folder", parentId: "home", size: 0, updatedAt: now, readonly: true });
  const file = (id, name, parentId, content, mime = "text/plain") => ({
    id, name, type: "file", parentId, content, mime,
    size: byteLength(content), updatedAt: now, readonly: true
  });

  return [
    { id: "home", name: "Home", type: "folder", parentId: null, size: 0, updatedAt: now, readonly: true },
    folder("desktop", "Desktop"),
    folder("documents", "Documents"),
    folder("downloads", "Downloads"),
    folder("pictures", "Pictures"),
    folder("applications", "Applications"),
    folder("system", "System"),
    file("system-report", "system-report.duck", "documents",
      "DuckOS Mora workspace report\n\nShell: Mora browser workspace\nStorage: local virtual workspace\nNative filesystem: not connected\n", "text/plain"),
    file("workspace-rpr", "workspace.rpr", "documents",
      "# Reaper workspace example\nlet workspace = \"DuckOS Mora\";\nprint(workspace);\n", "text/plain"),
    file("welcome-note", "welcome.txt", "desktop",
      "Welcome to DuckOS.\nThis file belongs to the local Mora workspace.\n", "text/plain"),
    file("app-catalog", "applications.json", "applications",
      JSON.stringify({ schema: "duckos.apps.v1", source: "Mora browser catalogue", nativeLaunch: false }, null, 2), "application/json"),
    file("theme-json", "theme.json", "system",
      JSON.stringify({ palette: "duck", accent: "#FFD400", nativeKernelState: "not exposed by browser shell" }, null, 2), "application/json")
  ];
}

function validateItems(value) {
  if (!Array.isArray(value) || value.length > 5000) return null;
  const ids = new Set();
  const items = [];
  for (const raw of value) {
    if (!raw || typeof raw.id !== "string" || ids.has(raw.id) ||
        typeof raw.name !== "string" || !["folder", "file"].includes(raw.type)) return null;
    ids.add(raw.id);
    items.push({
      id: raw.id,
      name: raw.name.slice(0, 120),
      type: raw.type,
      parentId: typeof raw.parentId === "string" ? raw.parentId : null,
      content: raw.type === "file" && typeof raw.content === "string" ? raw.content : "",
      mime: typeof raw.mime === "string" ? raw.mime.slice(0, 120) : "text/plain",
      size: Number.isFinite(raw.size) && raw.size >= 0 ? raw.size : 0,
      updatedAt: typeof raw.updatedAt === "string" ? raw.updatedAt : new Date(0).toISOString(),
      readonly: raw.readonly === true
    });
  }
  if (!ids.has("home")) return null;
  const byId = new Map(items.map((item) => [item.id, item]));
  for (const item of items) {
    if (item.id !== "home" && (!item.parentId || byId.get(item.parentId)?.type !== "folder")) return null;
  }
  if (byId.get("home")?.parentId !== null || byId.get("home")?.type !== "folder") return null;
  for (const item of items) {
    if (item.id === "home") continue;
    const visited = new Set([item.id]);
    let parentId = item.parentId;
    while (parentId) {
      if (visited.has(parentId)) return null;
      visited.add(parentId);
      parentId = byId.get(parentId)?.parentId ?? null;
    }
    if (!visited.has("home")) return null;
    if (item.type === "file" && byteLength(item.content) > MAX_FILE_BYTES) return null;
  }
  return items;
}

export class VirtualWorkspace {
  constructor(storage = defaultStorage()) {
    this.storage = storage;
    this.items = this.load();
  }

  load() {
    if (this.storage) {
      try {
        const parsed = JSON.parse(this.storage.getItem(STORAGE_KEY) || "null");
        const checked = validateItems(parsed);
        if (checked) return checked;
      } catch {
        // Start from the checked-in sample workspace if local storage is unavailable.
      }
    }
    return seedItems();
  }

  save() {
    if (!this.storage) return false;
    try {
      this.storage.setItem(STORAGE_KEY, JSON.stringify(this.items));
      return true;
    } catch {
      return false;
    }
  }

  get(id) {
    const item = this.items.find((entry) => entry.id === id);
    return item ? { ...item } : null;
  }

  list(parentId = "home", { query = "", sort = "name", direction = "asc" } = {}) {
    const parent = this.items.find((item) => item.id === parentId);
    if (!parent || parent.type !== "folder") return [];
    const needle = String(query).trim().toLocaleLowerCase();
    const items = this.items.filter((item) => item.parentId === parentId &&
      (!needle || item.name.toLocaleLowerCase().includes(needle)));
    const multiplier = direction === "desc" ? -1 : 1;
    const compare = {
      name: (a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }),
      date: (a, b) => a.updatedAt.localeCompare(b.updatedAt),
      size: (a, b) => a.size - b.size,
      type: (a, b) => a.type.localeCompare(b.type) || a.name.localeCompare(b.name)
    }[sort] || ((a, b) => a.name.localeCompare(b.name));
    return items.sort((a, b) => {
      if (a.type !== b.type) return a.type === "folder" ? -1 : 1;
      return multiplier * compare(a, b);
    }).map((item) => ({ ...item }));
  }

  search(query) {
    const needle = String(query ?? "").trim().toLocaleLowerCase();
    if (!needle) return [];
    return this.items.filter((item) => item.id !== "home" &&
      item.name.toLocaleLowerCase().includes(needle)).map((item) => ({ ...item }));
  }

  path(id) {
    const parts = [];
    let current = this.items.find((item) => item.id === id);
    while (current) {
      parts.unshift(current.name);
      current = current.parentId ? this.items.find((item) => item.id === current.parentId) : null;
    }
    return parts;
  }

  createFolder(name, parentId = "home") {
    const parent = this.items.find((item) => item.id === parentId);
    if (!parent || parent.type !== "folder") throw new Error("The destination folder does not exist.");
    const normalized = cleanName(name);
    if (this.items.some((item) => item.parentId === parentId && item.name.toLocaleLowerCase() === normalized.toLocaleLowerCase())) {
      throw new Error("An item with that name already exists.");
    }
    const item = {
      id: makeId(), name: normalized, type: "folder", parentId,
      size: 0, updatedAt: new Date().toISOString(), readonly: false
    };
    this.items.push(item);
    this.save();
    return { ...item };
  }

  createFile(name, content, parentId = "home", mime = "text/plain") {
    const parent = this.items.find((item) => item.id === parentId);
    if (!parent || parent.type !== "folder") throw new Error("The destination folder does not exist.");
    const normalized = cleanName(name);
    if (this.items.some((item) => item.parentId === parentId && item.name.toLocaleLowerCase() === normalized.toLocaleLowerCase())) {
      throw new Error("An item with that name already exists.");
    }
    const value = String(content ?? "");
    const size = byteLength(value);
    if (size > MAX_FILE_BYTES) throw new Error("Files are limited to 2 MiB in the browser workspace.");
    const item = {
      id: makeId(), name: normalized, type: "file", parentId, content: value,
      mime: String(mime || "text/plain").slice(0, 120), size,
      updatedAt: new Date().toISOString(), readonly: false
    };
    this.items.push(item);
    this.save();
    return { ...item };
  }

  rename(id, name) {
    const item = this.items.find((entry) => entry.id === id);
    if (!item || item.id === "home") throw new Error("This item cannot be renamed.");
    if (item.readonly) throw new Error("Sample system items are read-only.");
    const normalized = cleanName(name);
    if (this.items.some((entry) => entry.id !== id && entry.parentId === item.parentId &&
      entry.name.toLocaleLowerCase() === normalized.toLocaleLowerCase())) {
      throw new Error("An item with that name already exists.");
    }
    item.name = normalized;
    item.updatedAt = new Date().toISOString();
    this.save();
    return { ...item };
  }

  remove(id) {
    const item = this.items.find((entry) => entry.id === id);
    if (!item || item.id === "home" || item.readonly) throw new Error("This item is protected.");
    const removed = new Set([id]);
    let changed = true;
    while (changed) {
      changed = false;
      for (const entry of this.items) {
        if (entry.parentId && removed.has(entry.parentId) && !removed.has(entry.id)) {
          removed.add(entry.id);
          changed = true;
        }
      }
    }
    this.items = this.items.filter((entry) => !removed.has(entry.id));
    this.save();
    return removed.size;
  }
}

export const WORKSPACE_STORAGE_KEY = STORAGE_KEY;
export const MAX_WORKSPACE_FILE_BYTES = MAX_FILE_BYTES;
