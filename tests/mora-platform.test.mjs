import test from "node:test";
import assert from "node:assert/strict";
import {
  createAtomicUpdatePlan,
  createDiagnosticRecord,
  createStateBranch,
  createStorageEnvelope,
  validateStateBranch,
  validateStorageEnvelope
} from "../mora/platform-contracts.js";
import { getLocale, setLocale, translate } from "../mora/i18n.js";
import {
  compareChronoStamps,
  createChronoStamp,
  DEEP_TIME_EPOCH_YEARS,
  formatEpochYears,
  parseEpochYears
} from "../mora/chrono.js";

test("Russian and Ukrainian locale changes are persistent at the UI contract layer", () => {
  assert.equal(getLocale(), "ru");
  setLocale("uk");
  assert.equal(getLocale(), "uk");
  assert.equal(translate("Приложения"), "Застосунки");
  assert.equal(
    translate("План содержит 2 действие(й). Ничего не изменится до вашего подтверждения."),
    "План містить 2 дію(ї). Нічого не зміниться без вашого підтвердження."
  );
  assert.equal(
    translate("86 452 654 432 564 423 644 лет · отдельная BigInt-шкала, не системные часы"),
    "86 452 654 432 564 423 644 років · окрема шкала BigInt, а не системний годинник"
  );
  assert.equal(
    translate("Создана ветка mora-2 · ревизия 2 · родитель mora-1"),
    "Створено гілку mora-2 · ревізія 2 · батьківська mora-1"
  );
  const updatePreview = [
    "A/B-план · текущий слот A · целевой слот B",
    "Подпись пакета: не проверено",
    "Совместимость: не проверено",
    "Свободное место: не проверено",
    "Этапы: verify-signed-metadata-and-payload → verify-compatibility-and-capacity → stage-inactive-slot",
    "Не переключайте записи загрузки, пока все условия не подтверждены.",
    " · режим: plan-only."
  ].join("\n");
  const localizedPreview = translate(updatePreview);
  assert.match(localizedPreview, /поточний слот A · цільовий слот B/);
  assert.match(localizedPreview, /Підпис пакета: не перевірено/);
  assert.match(localizedPreview, /Етапи: перевірити підписані метадані та пакет/);
  assert.match(localizedPreview, /Не перемикайте записи завантаження/);
  setLocale("ru");
  assert.equal(translate("Приложения"), "Приложения");
});

test("the deep-time epoch keeps the full integer without Number conversion", () => {
  const epoch = parseEpochYears(DEEP_TIME_EPOCH_YEARS);
  assert.equal(epoch.toString(), "86452654432564423644");
  assert.equal(formatEpochYears(epoch, "ru").replace(/\s/g, ""), "86452654432564423644лет");
  assert.throws(() => parseEpochYears("86452654432564423644.5"), RangeError);
  assert.throws(() => parseEpochYears("-1"), RangeError);
});

test("chrono stamps compare arbitrary-size epochs and reject unsafe cycle data", () => {
  const early = createChronoStamp({ epochYears: "999999999999999999999999" });
  const late = createChronoStamp({ epochYears: "1000000000000000000000000" });
  assert.equal(compareChronoStamps(early, late), -1);
  assert.equal(compareChronoStamps(late, late), 0);
  assert.throws(() => createChronoStamp({ epochYears: "1", cycle: Number.MAX_SAFE_INTEGER + 1 }), RangeError);
});

test("versioned storage envelope detects accidental payload corruption", () => {
  const envelope = createStorageEnvelope({ preferences: { language: "uk", reducedMotion: true } });
  assert.equal(validateStorageEnvelope(envelope).payload.preferences.language, "uk");
  const damaged = structuredClone(envelope);
  damaged.payload.preferences.language = "ru";
  assert.equal(validateStorageEnvelope(damaged), null);
});

test("state branches keep parent lineage and validate their payload", () => {
  const branch = createStateBranch({
    id: "mora-branch-2",
    parentId: "mora-branch-1",
    state: { focusMode: true, permissions: { camera: false } }
  });
  assert.equal(validateStateBranch(branch).parentId, "mora-branch-1");
  const damaged = structuredClone(branch);
  damaged.state.focusMode = false;
  assert.equal(validateStateBranch(damaged), null);
});

test("A/B update plans never claim execution and require all preconditions", () => {
  const blocked = createAtomicUpdatePlan({ activeSlot: "A" });
  assert.equal(blocked.ready, false);
  assert.equal(blocked.checks.capacityAvailable, false);
  assert.equal(blocked.targetSlot, "B");
  assert.equal(blocked.execution, "plan-only");
  const ready = createAtomicUpdatePlan({
    activeSlot: "B",
    signatureVerified: true,
    compatible: true,
    availableBytes: 500,
    requiredBytes: 400
  });
  assert.equal(ready.ready, true);
  assert.equal(ready.checks.capacityAvailable, true);
  assert.equal(ready.targetSlot, "A");
  assert.equal(ready.execution, "plan-only");
});

test("diagnostic records are bounded and use an explicit language", () => {
  const diagnostic = createDiagnosticRecord({
    code: "MORA.STORAGE.DAMAGED",
    component: "Restore",
    detail: "x".repeat(2000),
    recoveryAction: "Create a new local snapshot",
    locale: "uk"
  });
  assert.equal(diagnostic.locale, "uk");
  assert.equal(diagnostic.detail.length, 1000);
  assert.throws(() => createDiagnosticRecord({ code: "bad code" }), TypeError);
});
