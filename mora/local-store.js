const DB_NAME = "dak.mora.local.v1";
const LEGACY_DB_NAME = "duckos.mora.local.v1";
const DB_VERSION = 1;
const STORE_NAME = "documents";
const FALLBACK_PREFIX = "dak.mora.localdoc.v1:";
const LEGACY_FALLBACK_PREFIX = "duckos.mora.localdoc.v1:";
const LEGACY_ID_ALIASES = new Map([
  ["dak.mora.recovery.v1", "duckos.mora.recovery.v1"]
]);
const MAX_DOCUMENT_BYTES = 256 * 1024;
const ID_PATTERN = /^[a-zA-Z0-9:._-]{1,96}$/;

function defaultStorage() {
  try { return globalThis.localStorage || null; } catch { return null; }
}

function requestResult(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error("IndexedDB request failed."));
  });
}

function transactionResult(transaction) {
  return new Promise((resolve, reject) => {
    transaction.oncomplete = () => resolve();
    transaction.onabort = () => reject(transaction.error || new Error("IndexedDB transaction aborted."));
    transaction.onerror = () => reject(transaction.error || new Error("IndexedDB transaction failed."));
  });
}

export function createLocalDocumentStore(options = {}) {
  const indexedDBApi = Object.hasOwn(options, "indexedDB") ? options.indexedDB : globalThis.indexedDB;
  const storage = Object.hasOwn(options, "storage") ? options.storage : defaultStorage();
  const now = typeof options.now === "function" ? options.now : () => new Date().toISOString();
  const databasePromises = new Map();

  function validateId(id) {
    if (typeof id !== "string" || !ID_PATTERN.test(id)) throw new TypeError("Invalid local document id.");
    return id;
  }

  function serialize(value) {
    const json = JSON.stringify(value);
    if (typeof json !== "string" || new TextEncoder().encode(json).byteLength > MAX_DOCUMENT_BYTES) {
      throw new RangeError("Local document exceeds the 256 KiB limit.");
    }
    return json;
  }

  function openDatabase(name = DB_NAME) {
    if (!indexedDBApi) return Promise.resolve(null);
    if (databasePromises.has(name)) return databasePromises.get(name);

    const pending = new Promise((resolve, reject) => {
      let request;
      try { request = indexedDBApi.open(name, DB_VERSION); }
      catch (error) { reject(error); return; }
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: "id" });
          store.createIndex("updatedAt", "updatedAt", { unique: false });
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("Unable to open local database."));
      request.onblocked = () => reject(new Error("Local database upgrade is blocked."));
    }).catch(() => null);

    databasePromises.set(name, pending);
    return pending;
  }

  async function legacyDatabaseExists() {
    if (!indexedDBApi) return false;
    if (typeof indexedDBApi.databases !== "function") return true;
    try {
      const databases = await indexedDBApi.databases();
      return databases.some((database) => database.name === LEGACY_DB_NAME);
    } catch {
      return true;
    }
  }

  async function readDatabase(name, id) {
    const db = await openDatabase(name);
    if (!db) return null;
    try {
      const tx = db.transaction(STORE_NAME, "readonly");
      return await requestResult(tx.objectStore(STORE_NAME).get(id));
    } catch {
      return null;
    }
  }

  async function writeDatabase(name, record) {
    const db = await openDatabase(name);
    if (!db) return false;
    try {
      const tx = db.transaction(STORE_NAME, "readwrite");
      const completed = transactionResult(tx);
      tx.objectStore(STORE_NAME).put(record);
      await completed;
      return true;
    } catch {
      return false;
    }
  }

  async function deleteDatabaseRecord(name, id) {
    const db = await openDatabase(name);
    if (!db) return false;
    try {
      const tx = db.transaction(STORE_NAME, "readwrite");
      const completed = transactionResult(tx);
      tx.objectStore(STORE_NAME).delete(id);
      await completed;
      return true;
    } catch {
      return false;
    }
  }

  function fallbackKey(id, prefix = FALLBACK_PREFIX) { return prefix + id; }

  function fallbackRead(id, prefix = FALLBACK_PREFIX) {
    if (!storage) return null;
    try {
      const raw = storage.getItem(fallbackKey(id, prefix));
      if (!raw || raw.length > MAX_DOCUMENT_BYTES * 1.4) return null;
      const record = JSON.parse(raw);
      return record && record.id === id ? record : null;
    } catch {
      return null;
    }
  }

  function migrateFallbackRecord(record, id) {
    if (!storage || !record) return;
    const migrated = { ...record, id };
    try { storage.setItem(fallbackKey(id), JSON.stringify(migrated)); } catch { /* Keep the legacy copy intact. */ }
  }

  async function get(id) {
    id = validateId(id);
    const legacyId = LEGACY_ID_ALIASES.get(id) || id;

    let record = await readDatabase(DB_NAME, id);
    if (record && Object.hasOwn(record, "data")) return record.data;

    if (await legacyDatabaseExists()) {
      record = await readDatabase(LEGACY_DB_NAME, legacyId);
      if (record && Object.hasOwn(record, "data")) {
        await writeDatabase(DB_NAME, { ...record, id });
        return record.data;
      }
    }

    record = fallbackRead(id);
    if (record && Object.hasOwn(record, "data")) return record.data;

    record = fallbackRead(legacyId, LEGACY_FALLBACK_PREFIX);
    if (record && Object.hasOwn(record, "data")) {
      migrateFallbackRecord(record, id);
      return record.data;
    }

    return null;
  }

  async function put(id, data) {
    id = validateId(id);
    const record = { id, data: JSON.parse(serialize(data)), updatedAt: now() };
    if (await writeDatabase(DB_NAME, record)) {
      return { ok: true, backend: "indexeddb", updatedAt: record.updatedAt };
    }
    if (!storage) throw new Error("No local document storage is available.");
    storage.setItem(fallbackKey(id), JSON.stringify(record));
    return { ok: true, backend: "localStorage", updatedAt: record.updatedAt };
  }

  async function remove(id) {
    id = validateId(id);
    const legacyId = LEGACY_ID_ALIASES.get(id) || id;
    let removed = await deleteDatabaseRecord(DB_NAME, id);
    if (await legacyDatabaseExists()) {
      removed = (await deleteDatabaseRecord(LEGACY_DB_NAME, legacyId)) || removed;
    }
    if (storage) {
      try {
        storage.removeItem(fallbackKey(id));
        storage.removeItem(fallbackKey(legacyId, LEGACY_FALLBACK_PREFIX));
        removed = true;
      } catch { /* No write access. */ }
    }
    return removed;
  }

  return Object.freeze({ get, put, remove });
}

const defaultStore = createLocalDocumentStore();
export const readLocalDocument = (id) => defaultStore.get(id);
export const writeLocalDocument = (id, data) => defaultStore.put(id, data);
export const deleteLocalDocument = (id) => defaultStore.remove(id);
