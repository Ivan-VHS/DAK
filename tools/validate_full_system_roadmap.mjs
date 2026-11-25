#!/usr/bin/env node
import { readFileSync, existsSync } from "node:fs";
import { resolve, relative, sep } from "node:path";

const root = resolve(new URL("..", import.meta.url).pathname);
const file = resolve(root, ".architecture/full-system-roadmap.v1.json");
const expectedIds = [
  "memory-management",
  "interrupts-time-scheduler",
  "processes-ring3-dabi64",
  "filesystem-user-profiles",
  "acpi-pci-usb-drivers",
  "reaper-runtime-services",
  "native-duck-desktop",
  "device-platform-services",
  "jora-duckbridge-bav",
  "installer-secure-boot-updates-recovery",
];
const maturities = new Set([
  "native_partially_verified",
  "policy_only",
  "host_only",
  "planned",
]);

function validate(data) {
  const errors = [];
  if (!data || data.schema !== "ivan-vhs.duckos-full-system-roadmap.v1" || data.version !== 1) {
    return ["unsupported or missing roadmap schema/version"];
  }
  if (data.project !== "DuckOS") errors.push("project must be DuckOS");
  if (data.baseline?.architecture?.primary !== "x86_64") errors.push("primary architecture must remain x86_64");
  const vendors = data.baseline?.architecture?.primary_vendors ?? [];
  if (!vendors.includes("Intel") || !vendors.includes("AMD")) errors.push("primary target must include Intel and AMD");
  if (!(data.baseline?.architecture?.preserved_compatibility ?? []).includes("Elbrus")) {
    errors.push("Elbrus compatibility track must be preserved");
  }
  if (!Array.isArray(data.domains) || data.domains.length !== 10) {
    return [...errors, "exactly ten implementation domains are required"];
  }

  const byId = new Map();
  data.domains.forEach((domain, index) => {
    if (!domain || domain.id !== expectedIds[index]) errors.push(`domains[${index}] has an unexpected id/order`);
    if (byId.has(domain?.id)) errors.push(`duplicate domain id: ${domain.id}`);
    if (domain?.id) byId.set(domain.id, domain);
    if (!maturities.has(domain?.maturity)) errors.push(`${domain?.id ?? index}: unsupported maturity`);
    if (!domain?.title?.trim() || !domain?.current_boundary?.trim() || !domain?.next_gate?.trim()) {
      errors.push(`${domain?.id ?? index}: title, current boundary and next gate are required`);
    }
    if (!Array.isArray(domain?.depends_on) || !Array.isArray(domain?.acceptance) || domain.acceptance.length === 0) {
      errors.push(`${domain?.id ?? index}: dependencies and acceptance gates must be arrays`);
    }
    for (const field of ["current_evidence", "verification"]) {
      const items = domain?.[field];
      if (!Array.isArray(items)) {
        errors.push(`${domain?.id ?? index}: ${field} must be an array`);
        continue;
      }
      if (["native_partially_verified", "policy_only", "host_only"].includes(domain.maturity) && items.length === 0) {
        errors.push(`${domain.id}: ${field} is required for a non-planned maturity`);
      }
      for (const item of items) {
        if (typeof item !== "string" || !item.trim() || item.includes("\\\\") ||
            item.startsWith("/") || item.split("/").includes("..")) {
          errors.push(`${domain.id}: unsafe ${field} path: ${item}`);
          continue;
        }
        const target = resolve(root, item);
        const rel = relative(root, target);
        if (rel === ".." || rel.startsWith(`..${sep}`) || !existsSync(target)) {
          errors.push(`${domain.id}: missing or escaping ${field} path: ${item}`);
        }
      }
    }
    if (domain.maturity !== "native_partially_verified" && domain.current_boundary.toLowerCase().includes("native implementation verified")) {
      errors.push(`${domain.id}: non-native maturity cannot claim verified native implementation`);
    }
  });

  for (const domain of data.domains) {
    for (const dependency of domain.depends_on ?? []) {
      if (!byId.has(dependency)) errors.push(`${domain.id}: unknown dependency ${dependency}`);
      if (dependency === domain.id) errors.push(`${domain.id}: self-dependency is invalid`);
    }
  }

  const visiting = new Set();
  const visited = new Set();
  function visit(id) {
    if (visiting.has(id)) {
      errors.push(`dependency cycle detected at ${id}`);
      return;
    }
    if (visited.has(id) || !byId.has(id)) return;
    visiting.add(id);
    for (const dependency of byId.get(id).depends_on ?? []) visit(dependency);
    visiting.delete(id);
    visited.add(id);
  }
  for (const id of byId.keys()) visit(id);

  if (!Array.isArray(data.delivery_waves) || data.delivery_waves.length !== 5) {
    errors.push("five ordered delivery waves are required");
  }
  return errors;
}

function runSelfTests(data) {
  const duplicate = structuredClone(data);
  duplicate.domains[1].id = duplicate.domains[0].id;
  if (!validate(duplicate).some((item) => item.includes("duplicate domain id"))) throw new Error("duplicate id was not rejected");

  const unsafe = structuredClone(data);
  unsafe.domains[0].current_evidence[0] = "../outside";
  if (!validate(unsafe).some((item) => item.includes("unsafe current_evidence path"))) throw new Error("path traversal was not rejected");

  const cycle = structuredClone(data);
  cycle.domains[0].depends_on = [cycle.domains[1].id];
  if (!validate(cycle).some((item) => item.includes("dependency cycle"))) throw new Error("dependency cycle was not rejected");

  const unverified = structuredClone(data);
  unverified.domains[0].verification = [];
  if (!validate(unverified).some((item) => item.includes("verification is required"))) throw new Error("missing verification was not rejected");
}

try {
  const data = JSON.parse(readFileSync(file, "utf8"));
  const errors = validate(data);
  if (errors.length) {
    for (const error of errors) console.error(`ERROR: ${error}`);
    process.exitCode = 1;
  } else {
    console.log("DuckOS Full System roadmap: 10 domains, 5 delivery waves, dependency graph and evidence paths valid.");
  }
  if (process.argv.includes("--self-test")) {
    runSelfTests(data);
    console.log("DuckOS Full System roadmap validator negative-case tests: passed.");
  }
} catch (error) {
  console.error(`DuckOS Full System roadmap validation failed: ${error.message}`);
  process.exitCode = 1;
}
