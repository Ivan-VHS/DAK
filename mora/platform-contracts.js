const STORAGE_SCHEMA = "duckos.storage-envelope.v1";
const BRANCH_SCHEMA = "duckos.state-branch.v1";
const UPDATE_SCHEMA = "duckos.atomic-update-plan.v1";

function stableJson(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return "[" + value.map(stableJson).join(",") + "]";
  const keys = Object.keys(value).sort();
  return "{" + keys.map((key) => JSON.stringify(key) + ":" + stableJson(value[key])).join(",") + "}";
}

function crc32(value) {
  const bytes = new TextEncoder().encode(value);
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
    }
  }
  return ((crc ^ 0xffffffff) >>> 0).toString(16).padStart(8, "0");
}

function cloneJson(value, maxBytes = 1024 * 1024) {
  const serialized = stableJson(value);
  const size = new TextEncoder().encode(serialized).byteLength;
  if (size > maxBytes) throw new RangeError("The stored state exceeds the configured size limit.");
  return { value: JSON.parse(serialized), serialized, size };
}

export function createStorageEnvelope(payload, {
  generation = 1,
  previousDigest = null
} = {}) {
  if (!Number.isSafeInteger(generation) || generation < 1) {
    throw new RangeError("Storage generation must be a positive safe integer.");
  }
  if (previousDigest !== null && !/^[0-9a-f]{8}$/i.test(previousDigest)) {
    throw new TypeError("Previous digest must be a CRC32 value.");
  }
  const copy = cloneJson(payload);
  return {
    schema: STORAGE_SCHEMA,
    version: 1,
    generation,
    encoding: "utf-8",
    byteLength: copy.size,
    integrity: {
      algorithm: "CRC32",
      digest: crc32(copy.serialized),
      purpose: "accidental-corruption-detection"
    },
    previousDigest,
    payload: copy.value
  };
}

export function validateStorageEnvelope(value) {
  if (!value || typeof value !== "object" || value.schema !== STORAGE_SCHEMA ||
      value.version !== 1 || !Number.isSafeInteger(value.generation) || value.generation < 1 ||
      value.encoding !== "utf-8" || !Number.isSafeInteger(value.byteLength) ||
      !value.integrity || value.integrity.algorithm !== "CRC32" ||
      typeof value.integrity.digest !== "string" || !value.payload) {
    return null;
  }

  try {
    const copy = cloneJson(value.payload);
    if (copy.size !== value.byteLength || crc32(copy.serialized) !== value.integrity.digest) return null;
    return {
      schema: STORAGE_SCHEMA,
      version: 1,
      generation: value.generation,
      encoding: "utf-8",
      byteLength: copy.size,
      integrity: { algorithm: "CRC32", digest: value.integrity.digest, purpose: "accidental-corruption-detection" },
      previousDigest: value.previousDigest ?? null,
      payload: copy.value
    };
  } catch {
    return null;
  }
}

export function createStateBranch({
  id,
  parentId = null,
  revision = 1,
  state,
  createdAt = new Date().toISOString()
} = {}) {
  if (typeof id !== "string" || !/^[a-z0-9._-]{1,80}$/i.test(id)) {
    throw new TypeError("Branch id is invalid.");
  }
  if (parentId !== null && (typeof parentId !== "string" || !/^[a-z0-9._-]{1,80}$/i.test(parentId))) {
    throw new TypeError("Parent branch id is invalid.");
  }
  if (!Number.isSafeInteger(revision) || revision < 1 || typeof createdAt !== "string") {
    throw new TypeError("Branch metadata is invalid.");
  }
  const copy = cloneJson(state);
  return {
    schema: BRANCH_SCHEMA,
    id,
    parentId,
    revision,
    createdAt,
    state: copy.value,
    integrity: { algorithm: "CRC32", digest: crc32(copy.serialized) }
  };
}

export function validateStateBranch(value) {
  if (!value || typeof value !== "object" || value.schema !== BRANCH_SCHEMA ||
      typeof value.id !== "string" || !/^[a-z0-9._-]{1,80}$/i.test(value.id) ||
      (value.parentId !== null && typeof value.parentId !== "string") ||
      !Number.isSafeInteger(value.revision) || value.revision < 1 ||
      typeof value.createdAt !== "string" || !value.integrity ||
      value.integrity.algorithm !== "CRC32" || typeof value.integrity.digest !== "string") {
    return null;
  }
  try {
    const copy = cloneJson(value.state);
    if (crc32(copy.serialized) !== value.integrity.digest) return null;
    return createStateBranch({
      id: value.id,
      parentId: value.parentId,
      revision: value.revision,
      state: copy.value,
      createdAt: value.createdAt
    });
  } catch {
    return null;
  }
}

export function createAtomicUpdatePlan({
  activeSlot = "A",
  signatureVerified = false,
  compatible = false,
  availableBytes = 0,
  requiredBytes = 0
} = {}) {
  if (!["A", "B"].includes(activeSlot)) throw new TypeError("Active update slot must be A or B.");
  if (!Number.isSafeInteger(availableBytes) || availableBytes < 0 ||
      !Number.isSafeInteger(requiredBytes) || requiredBytes < 0) {
    throw new RangeError("Update capacity values must be non-negative safe integers.");
  }

  const checks = {
    signatureVerified: signatureVerified === true,
    compatible: compatible === true,
    capacityAvailable: availableBytes >= requiredBytes
  };
  const ready = Object.values(checks).every(Boolean);
  return {
    schema: UPDATE_SCHEMA,
    currentSlot: activeSlot,
    targetSlot: activeSlot === "A" ? "B" : "A",
    checks,
    ready,
    steps: [
      "verify-signed-metadata-and-payload",
      "stage-inactive-slot",
      "verify-capacity-and-compatibility",
      "run-health-checks",
      "switch-boot-entry-atomically",
      "retain-previous-slot-until-accepted-boot"
    ],
    execution: "plan-only",
    note: ready
      ? "All declared preconditions pass; a native updater and boot controller are still required."
      : "Do not switch boot entries while any precondition is missing."
  };
}

export function createDiagnosticRecord({
  code,
  component,
  detail,
  recoveryAction,
  severity = "error",
  locale = "ru"
} = {}) {
  const safe = (value, max) => String(value ?? "").replace(/[\u0000-\u001f]/g, " ").trim().slice(0, max);
  const normalizedCode = safe(code, 64);
  if (!/^[A-Z0-9._-]+$/.test(normalizedCode)) throw new TypeError("Diagnostic code is invalid.");
  if (!["info", "warning", "error", "critical"].includes(severity)) throw new TypeError("Diagnostic severity is invalid.");
  return Object.freeze({
    schema: "duckos.diagnostic.v1",
    code: normalizedCode,
    component: safe(component, 80) || "unknown",
    severity,
    locale: locale === "uk" ? "uk" : "ru",
    detail: safe(detail, 1000),
    recoveryAction: safe(recoveryAction, 500),
    timestamp: new Date().toISOString()
  });
}
