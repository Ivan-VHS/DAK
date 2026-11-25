#!/usr/bin/env node
import { existsSync, readFileSync, realpathSync, statSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const STAGES = [
  "Genesis", "Foundation", "Evolution", "Ascension", "Vanguard",
  "Frontier", "Dominion", "Apex", "Zenith", "Singularity"
];

const REQUIRED_EVIDENCE = new Map([
  [1, ["scope"]],
  [2, ["architecture", "policy", "build", "ci"]],
  [3, ["source", "tests", "runtime"]],
  [4, ["integration", "contract_tests", "ci"]],
  [5, ["target_build", "resource_budget"]],
  [6, ["platform_coverage", "threat_model", "security_tests", "fuzz_or_fault_tests", "accessibility"]],
  [7, ["core_acceptance", "compatibility", "migration"]],
  [8, ["release_candidate", "provenance", "recovery"]],
  [9, ["support_policy", "operations", "release_regression", "deprecation"]],
  [10, ["reproducible_rebuild", "audit_chain", "independent_integration"]]
]);
const VERIFICATIONS = new Set([
  "documentation_only", "source_reviewed", "tests_passed", "ci_passed", "artifact_verified"
]);

function addEvidencePathError(root, path, add) {
  if (typeof path !== "string" || !path || isAbsolute(path) || path.includes("\\") ||
      path.split("/").some(part => part === ".." || part === "" || part === ".")) {
    add("unsafe evidence path: " + String(path));
    return;
  }
  const absolute = resolve(root, path);
  const rel = relative(root, absolute);
  if (rel === ".." || rel.startsWith(".." + sep)) {
    add("evidence path escapes repository: " + path);
    return;
  }
  try {
    if (!existsSync(absolute)) {
      add("evidence path does not exist: " + path);
      return;
    }
    const info = statSync(absolute);
    if (!info.isFile() && !info.isDirectory()) {
      add("evidence path is not a file or directory: " + path);
      return;
    }
    const realRel = relative(root, realpathSync(absolute));
    if (realRel === ".." || realRel.startsWith(".." + sep)) add("evidence path resolves outside repository: " + path);
  } catch (error) {
    add("cannot inspect evidence path " + path + ": " + error.message);
  }
}

export function validateProjectLadder(record, root = ROOT) {
  const errors = [];
  const add = message => errors.push(message);

  if (record?.schema !== "dak.project-maturity.v1" || record?.version !== 1) {
    add("unsupported project maturity schema or version");
  }
  if (typeof record?.project !== "string" || !record.project.trim()) add("project name is required");
  if (!/^Ivan-VHS\/[A-Za-z0-9._-]+$/.test(record?.repository ?? "")) add("repository must be an Ivan-VHS owner/name");
  if (process.env.GITHUB_REPOSITORY && record?.repository !== process.env.GITHUB_REPOSITORY) {
    add("manifest repository does not match GITHUB_REPOSITORY");
  }
  if (!Number.isInteger(record?.current_stage) || record.current_stage < 1 || record.current_stage > 10) {
    add("current_stage must be an integer from 1 through 10");
  }
  if (record?.current_name !== STAGES[(record?.current_stage ?? 0) - 1]) {
    add("current_name does not match current_stage");
  }
  if (!["provisional", "verified"].includes(record?.assessment)) add("assessment must be provisional or verified");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(record?.assessment_date ?? "")) add("assessment_date must use YYYY-MM-DD");
  if (typeof record?.assessment_basis !== "string" || record.assessment_basis.trim().length < 20) {
    add("assessment_basis must explain how the record was assessed");
  }
  if (record?.semver_independent !== true) add("semver_independent must remain true");

  const stages = record?.stages;
  if (!Array.isArray(stages) || stages.length !== 10) {
    add("exactly ten stage records are required");
  } else {
    let highestCumulativeStage = 0;
    let encounteredPending = false;

    for (let index = 0; index < STAGES.length; index += 1) {
      const stage = stages[index];
      const expectedNumber = index + 1;
      if (stage?.number !== expectedNumber || stage?.name !== STAGES[index]) {
        add("stage " + expectedNumber + " must be named " + STAGES[index] + " and remain in canonical order");
        continue;
      }
      if (!["met", "pending", "not_applicable"].includes(stage.status)) {
        add(STAGES[index] + ": invalid status");
        continue;
      }
      const evidence = Array.isArray(stage.evidence) ? stage.evidence : [];
      if (stage.status === "met") {
        if (encounteredPending) add(STAGES[index] + ": a completed stage cannot follow a pending stage");
        if (evidence.length === 0) add(STAGES[index] + ": met status requires evidence");
        const kinds = new Set();
        for (const item of evidence) {
          if (typeof item?.kind !== "string") add(STAGES[index] + ": evidence kind is required");
          else kinds.add(item.kind);
          if (typeof item?.claim !== "string" || item.claim.trim().length < 12) {
            add(STAGES[index] + ": evidence claim is too short");
          }
          if (!VERIFICATIONS.has(item?.verification)) {
            add(STAGES[index] + ": invalid verification type");
          }
          addEvidencePathError(root, item?.path, add);
        }
        for (const required of REQUIRED_EVIDENCE.get(expectedNumber) ?? []) {
          if (!kinds.has(required)) add(STAGES[index] + ": missing required evidence kind " + required);
        }
        if (!encounteredPending) highestCumulativeStage = expectedNumber;
      } else if (stage.status === "not_applicable") {
        if (encounteredPending) add(STAGES[index] + ": not_applicable cannot follow a pending stage");
        if (typeof stage.rationale !== "string" || stage.rationale.trim().length < 20) {
          add(STAGES[index] + ": not_applicable requires a written rationale");
        }
        if (!encounteredPending) highestCumulativeStage = expectedNumber;
        for (const item of evidence) addEvidencePathError(root, item?.path, add);
      } else {
        encounteredPending = true;
        if (stage.rationale && typeof stage.rationale !== "string") add(STAGES[index] + ": rationale must be text");
        for (const item of evidence) addEvidencePathError(root, item?.path, add);
      }
    }

    if (record?.current_stage !== highestCumulativeStage) {
      add("current_stage must equal the highest consecutive completed stage (" + highestCumulativeStage + ")");
    }
  }

  const expectedNext = record?.current_stage === 10 ? null : record?.current_stage + 1;
  if (record?.next_stage !== expectedNext) add("next_stage must be the next cumulative stage or null at Singularity");
  if (expectedNext === null) {
    if (!Array.isArray(record?.next_gate) || record.next_gate.length !== 0) add("Singularity must have an empty next_gate");
  } else if (!Array.isArray(record?.next_gate) || record.next_gate.length === 0 ||
             record.next_gate.some(item => typeof item !== "string" || item.trim().length < 12)) {
    add("next_gate must contain actionable, specific acceptance work");
  }

  if (record?.assessment === "verified") {
    const run = record?.verification_run;
    if (!run || !/^[0-9a-f]{40}$/i.test(run.commit ?? "") ||
        typeof run.workflow !== "string" || !run.workflow ||
        typeof run.environment !== "string" || !run.environment ||
        typeof run.run_url !== "string" || !run.run_url.startsWith("https://")) {
      add("verified assessment requires commit, workflow, environment and a CI run URL");
    }
    const allEvidence = (stages ?? []).flatMap(stage => stage?.evidence ?? []);
    if (!allEvidence.some(item => item?.verification === "tests_passed")) add("verified assessment requires test evidence");
    if (!allEvidence.some(item => item?.verification === "ci_passed")) add("verified assessment requires CI evidence");
    if ((record?.current_stage ?? 0) >= 5 &&
        !allEvidence.some(item => item?.verification === "artifact_verified")) {
      add("Vanguard or higher requires verified target artifacts");
    }
  }

  return errors;
}

export function validateRepository(root = ROOT) {
  const manifestPath = resolve(root, ".github/project-ladder.v1.json");
  const schemaPath = resolve(root, "schemas/project-ladder.v1.schema.json");
  const errors = [];
  try {
    const schema = JSON.parse(readFileSync(schemaPath, "utf8"));
    if (schema?.$id !== "https://raw.githubusercontent.com/Ivan-VHS/DAK/main/schemas/project-ladder.v1.schema.json") {
      errors.push("project ladder schema $id is not canonical");
    }
    if (schema?.properties?.schema?.const !== "dak.project-maturity.v1") {
      errors.push("project ladder schema does not declare the canonical contract");
    }
  } catch (error) {
    errors.push("cannot read project ladder schema: " + error.message);
  }
  try {
    const record = JSON.parse(readFileSync(manifestPath, "utf8"));
    errors.push(...validateProjectLadder(record, root));
  } catch (error) {
    errors.push("cannot read project ladder manifest: " + error.message);
  }
  return errors;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const errors = validateRepository();
  if (errors.length) {
    for (const error of errors) process.stderr.write("ERROR: " + error + "\n");
    process.exitCode = 1;
  } else {
    process.stdout.write("Project maturity ladder: valid (evidence paths and cumulative gates checked)\n");
  }
}
