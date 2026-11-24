import test from "node:test";
import assert from "node:assert/strict";
import {
  CONCRETE_THUMP_LIMITS,
  CONCRETE_THUMP_STORAGE_KEY,
  LEGACY_CONCRETE_THUMP_STORAGE_KEY,
  buildConcreteThumpPrompt,
  createDefaultConcreteThumpProfile,
  createReaperGridSource,
  loadConcreteThumpProfile,
  normalizeConcreteThumpProfile,
  saveConcreteThumpProfile,
  validateAudioSampleFile
} from "../mora/concrete-thump.js";

class MemoryStorage {
  constructor() {
    this.values = new Map();
  }
  getItem(key) {
    return this.values.has(key) ? this.values.get(key) : null;
  }
  setItem(key, value) {
    this.values.set(key, String(value));
  }
}

test("the default ritual profile targets heavyweight East Slavic trap at 160 BPM", () => {
  const profile = createDefaultConcreteThumpProfile();
  assert.equal(profile.bpm, 160);
  assert.equal(profile.swing, 60);
  assert.equal(profile.vocalTradition, "layered");
  assert.ok(profile.chantSources.includes("znamenny"));
  assert.ok(profile.chantSources.includes("kolyadky"));
  assert.ok(profile.chantSources.includes("kupala"));
});

test("profile normalization rejects unknown tags and out-of-range rhythm values", () => {
  const profile = normalizeConcreteThumpProfile({
    bpm: 999,
    swing: 4,
    vocalTradition: "root",
    chantSources: ["znamenny", "unknown", "znamenny"],
    sampleTreatment: "execute"
  });
  assert.equal(profile.bpm, 160);
  assert.equal(profile.swing, 60);
  assert.equal(profile.vocalTradition, "layered");
  assert.deepEqual(profile.chantSources, ["znamenny"]);
  assert.equal(profile.sampleTreatment, "chopped-call-response");
});

test("legacy BPM and swing settings migrate without losing their values", () => {
  const storage = new MemoryStorage();
  storage.setItem(LEGACY_CONCRETE_THUMP_STORAGE_KEY, JSON.stringify({ bpm: 150, swing: 57 }));
  const profile = loadConcreteThumpProfile(storage);
  assert.equal(profile.bpm, 150);
  assert.equal(profile.swing, 57);
});

test("profile storage writes only normalized versioned data", () => {
  const storage = new MemoryStorage();
  assert.equal(saveConcreteThumpProfile({ bpm: 166, swing: 62 }, storage), true);
  const saved = JSON.parse(storage.getItem(CONCRETE_THUMP_STORAGE_KEY));
  assert.equal(saved.schema, "duckos.concrete-thump-profile.v2");
  assert.equal(saved.bpm, 166);
  assert.equal(saved.swing, 62);
  assert.equal("shell" in saved, false);
});

test("audio sample import enforces type, count, per-file and aggregate bounds", () => {
  assert.equal(validateAudioSampleFile({ name: "choir.wav", type: "audio/wav", size: 1024 }).ok, true);
  assert.equal(validateAudioSampleFile({ name: "notes.txt", type: "text/plain", size: 1024 }).ok, false);
  assert.equal(validateAudioSampleFile({ name: "large.wav", type: "audio/wav", size: CONCRETE_THUMP_LIMITS.maxSampleBytes + 1 }).ok, false);
  assert.equal(validateAudioSampleFile({ name: "ninth.ogg", type: "audio/ogg", size: 1024 }, { sampleCount: 8 }).ok, false);
  assert.equal(validateAudioSampleFile({ name: "overflow.wav", type: "audio/wav", size: 1024 }, { totalBytes: CONCRETE_THUMP_LIMITS.maxTotalSampleBytes }).ok, false);
});

test("the generated production prompt remains within the 500-character brief limit", () => {
  const prompt = buildConcreteThumpPrompt(createDefaultConcreteThumpProfile());
  assert.ok(prompt.length <= 500);
  assert.match(prompt, /160 BPM/);
  assert.match(prompt, /Orthodox/);
  assert.match(prompt, /East Slavic/);
  assert.match(prompt, /Kolyadky/);
  assert.match(prompt, /MPC swing/);
});

test("Reaper timing helper uses validated numeric profile values and no host audio calls", () => {
  const source = createReaperGridSource({ bpm: 160, swing: 60 });
  assert.match(source, /make bpm := 160/);
  assert.match(source, /make swing_percent := 60/);
  assert.match(source, /range\(0, 8\) :: map\(offbeat_time\)/);
  assert.match(source, /offbeat_ms=/);
  assert.doesNotMatch(source, /import |open\(|exec\(|audio device/i);
  assert.doesNotMatch(createReaperGridSource({ bpm: "160\nexec()", swing: 60 }), /exec\(\)/);
});
