const DB_NAME = "dak.mora.local.v1";
const DB_VERSION = 1;
const STORE_NAME = "documents";
const FALLBACK_PREFIX = "dak.mora.localdoc.v1:";
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
  let databasePromise = null;

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

  function openDatabase() {
    if (!indexedDBApi) return Promise.resolve(null);
    if (databasePromise) return databasePromise;
    databasePromise = new Promise((resolve, reject) => {
      let request;
      try { request = indexedDBApi.open(DB_NAME, DB_VERSION); }
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
    return databasePromise;
  }

  function fallbackKey(id) { return FALLBACK_PREFIX + id; }
  function fallbackRead(id) {
    if (!storage) return null;
    try {
      const raw = storage.getItem(fallbackKey(id));
      if (!raw || raw.length > MAX_DOCUMENT_BYTES * 1.4) return null;
      const record = JSON.parse(raw);
      return record && record.id === id ? record : null;
    } catch { return null; }
  }

  async function get(id) {
    id = validateId(id);
    const db = await openDatabase();
    if (db) {
      try {
        const tx = db.transaction(STORE_NAME, "readonly");
        const record = await requestResult(tx.objectStore(STORE_NAME).get(id));
        if (record && Object.hasOwn(record, "data")) return record.data;
      } catch { /* Fall back to the bounded browser store. */ }
    }
    const record = fallbackRead(id);
    return record && Object.hasOwn(record, "data") ? record.data : null;
  }

  async function put(id, data) {
    id = validateId(id);
    const record = { id, data: JSON.parse(serialize(data)), updatedAt: now() };
    const db = await openDatabase();
    if (db) {
      try {
        const tx = db.transaction(STORE_NAME, "readwrite");
        const completed = transactionResult(tx);
        tx.objectStore(STORE_NAME).put(record);
        await completed;
        return { ok: true, backend: "indexeddb", updatedAt: record.updatedAt };
      } catch { /* Use fallback if IndexedDB is unavailable or quota-limited. */ }
    }
    if (!storage) throw new Error("No local document storage is available.");
    storage.setItem(fallbackKey(id), JSON.stringify(record));
    return { ok: true, backend: "localStorage", updatedAt: record.updatedAt };
  }

  async function remove(id) {
    id = validateId(id);
    let removed = false;
    const db = await openDatabase();
    if (db) {
      try {
        const tx = db.transaction(STORE_NAME, "readwrite");
        const completed = transactionResult(tx);
        tx.objectStore(STORE_NAME).delete(id);
        await completed;
        removed = true;
      } catch { /* Try the fallback store. */ }
    }
    if (storage) {
      try { storage.removeItem(fallbackKey(id)); removed = true; } catch { /* No write access. */ }
    }
    return removed;
  }

  return Object.freeze({ get, put, remove });
}

const defaultStore = createLocalDocumentStore();
export const readLocalDocument = (id) => defaultStore.get(id);
export const writeLocalDocument = (id, data) => defaultStore.put(id, data);
export const deleteLocalDocument = (id) => defaultStore.remove(id);
