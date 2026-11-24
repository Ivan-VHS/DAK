import { normalizeConcreteThumpProfile } from "./concrete-thump.js";

const activeSessions = new WeakMap();
const RENDER_BARS = 4;
const SAMPLE_RATE = 44100;
const AUDIO_TAIL_SECONDS = 0.65;

function createNoiseBuffer(context) {
  const length = context.sampleRate;
  const buffer = context.createBuffer(1, length, context.sampleRate);
  const data = buffer.getChannelData(0);
  let seed = 0x51f15e;

  for (let index = 0; index < length; index += 1) {
    seed ^= seed << 13;
    seed ^= seed >>> 17;
    seed ^= seed << 5;
    data[index] = (seed / 0x7fffffff) * 0.32;
  }

  return buffer;
}

function makeEnvelope(context, destination, when, peak, duration) {
  const gain = context.createGain();
  gain.gain.setValueAtTime(0.0001, when);
  gain.gain.exponentialRampToValueAtTime(Math.max(0.0002, peak), when + 0.004);
  gain.gain.exponentialRampToValueAtTime(0.0001, when + duration);
  gain.connect(destination);
  return gain;
}

function scheduleKick(context, destination, when) {
  const oscillator = context.createOscillator();
  const gain = makeEnvelope(context, destination, when, 0.9, 0.2);
  oscillator.type = "sine";
  oscillator.frequency.setValueAtTime(145, when);
  oscillator.frequency.exponentialRampToValueAtTime(42, when + 0.14);
  oscillator.connect(gain);
  oscillator.start(when);
  oscillator.stop(when + 0.22);
}

function scheduleBass(context, destination, when) {
  const oscillator = context.createOscillator();
  const gain = makeEnvelope(context, destination, when, 0.58, 0.32);
  oscillator.type = "sine";
  oscillator.frequency.setValueAtTime(48, when);
  oscillator.frequency.exponentialRampToValueAtTime(40, when + 0.2);
  oscillator.connect(gain);
  oscillator.start(when);
  oscillator.stop(when + 0.34);
}

function scheduleNoiseHit(context, destination, noiseBuffer, when, kind) {
  const source = context.createBufferSource();
  const filter = context.createBiquadFilter();
  const duration = kind === "hat" ? 0.055 : 0.18;
  const gain = makeEnvelope(context, destination, when, kind === "hat" ? 0.17 : 0.3, duration);

  source.buffer = noiseBuffer;
  filter.type = kind === "hat" ? "highpass" : "bandpass";
  filter.frequency.setValueAtTime(kind === "hat" ? 7600 : 2100, when);
  filter.Q.setValueAtTime(kind === "hat" ? 0.7 : 0.9, when);
  source.connect(filter);
  filter.connect(gain);
  source.start(when);
  source.stop(when + duration + 0.01);
}

function scheduleChoir(context, destination, sampleBuffer, when, step, stepDuration, treatment) {
  if (!sampleBuffer || sampleBuffer.duration <= 0) return;

  const source = context.createBufferSource();
  const envelope = context.createGain();
  const offset = sampleBuffer.duration >= 1.6
    ? (step / 16) * sampleBuffer.duration
    : 0;
  const available = sampleBuffer.duration - offset;
  let duration = stepDuration * 0.92;

  if (treatment === "long-choir-beds") duration = Math.max(stepDuration * 3.5, 0.6);
  if (treatment === "granular-fragments") duration = stepDuration * 0.38;
  duration = Math.min(duration, available);

  if (duration < 0.012) return;

  source.buffer = sampleBuffer;
  source.playbackRate.setValueAtTime(treatment === "granular-fragments" ? 1.06 : 1, when);
  envelope.gain.setValueAtTime(0.0001, when);
  envelope.gain.linearRampToValueAtTime(0.44, when + 0.012);
  envelope.gain.setValueAtTime(0.44, Math.max(when + 0.013, when + duration * 0.72));
  envelope.gain.linearRampToValueAtTime(0.0001, when + duration);
  source.connect(envelope);
  envelope.connect(destination);
  source.start(when, offset, duration);
}

function scheduleSequence(context, destination, profile, sampleBuffer, startAt) {
  const sixteenth = 60 / profile.bpm / 4;
  const swingDelay = sixteenth * (profile.swing - 50) / 50;
  const loopDuration = sixteenth * 16 * RENDER_BARS + AUDIO_TAIL_SECONDS;
  const noiseBuffer = createNoiseBuffer(context);

  for (let bar = 0; bar < RENDER_BARS; bar += 1) {
    for (let step = 0; step < 16; step += 1) {
      const when = startAt + (bar * 16 + step) * sixteenth +
        (step % 2 === 1 ? swingDelay : 0);
      const sequence = profile.sequence;

      if (sequence.kick[step]) scheduleKick(context, destination, when);
      if (sequence.snare[step]) scheduleNoiseHit(context, destination, noiseBuffer, when, "snare");
      if (sequence.hat[step]) scheduleNoiseHit(context, destination, noiseBuffer, when, "hat");
      if (sequence.bass[step]) scheduleBass(context, destination, when);
      if (sequence.choir[step]) {
        scheduleChoir(context, destination, sampleBuffer, when, step, sixteenth, profile.sampleTreatment);
      }
    }
  }

  return loopDuration;
}

async function decodeSample(file, context) {
  if (!file) return null;
  const bytes = await file.arrayBuffer();
  return context.decodeAudioData(bytes.slice(0));
}

export async function playConcreteThump({ owner, profile, sampleFile = null }) {
  if (!owner) throw new TypeError("Concrete Thump owner window is required.");
  stopConcreteThump(owner);

  const AudioContextType = globalThis.AudioContext || globalThis.webkitAudioContext;
  if (!AudioContextType) throw new Error("Web Audio is not supported by this browser.");

  const context = new AudioContextType();
  const session = { context, timer: null };
  activeSessions.set(owner, session);

  try {
    const normalized = normalizeConcreteThumpProfile(profile);
    const sampleBuffer = await decodeSample(sampleFile, context);
    await context.resume();
    const startAt = context.currentTime + 0.08;
    const duration = scheduleSequence(context, context.destination, normalized, sampleBuffer, startAt);
    session.timer = globalThis.setTimeout(() => stopConcreteThump(owner), duration * 1000 + 300);
    return { durationSeconds: duration, choirLoaded: Boolean(sampleBuffer) };
  } catch (error) {
    stopConcreteThump(owner);
    throw error;
  }
}

export function stopConcreteThump(owner) {
  const session = activeSessions.get(owner);
  if (!session) return;
  if (session.timer !== null) globalThis.clearTimeout(session.timer);
  activeSessions.delete(owner);
  try {
    session.context.close();
  } catch {
    // The context may already have closed after the loop ended.
  }
}

function encodeWav(audioBuffer) {
  const channels = Math.min(audioBuffer.numberOfChannels, 2);
  const frames = audioBuffer.length;
  const bytesPerSample = 2;
  const dataBytes = frames * channels * bytesPerSample;
  const buffer = new ArrayBuffer(44 + dataBytes);
  const view = new DataView(buffer);

  const writeString = (offset, value) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + dataBytes, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, channels, true);
  view.setUint32(24, audioBuffer.sampleRate, true);
  view.setUint32(28, audioBuffer.sampleRate * channels * bytesPerSample, true);
  view.setUint16(32, channels * bytesPerSample, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, dataBytes, true);

  let offset = 44;
  for (let frame = 0; frame < frames; frame += 1) {
    for (let channel = 0; channel < channels; channel += 1) {
      const sample = Math.max(-1, Math.min(1, audioBuffer.getChannelData(channel)[frame]));
      view.setInt16(offset, sample < 0 ? sample * 32768 : sample * 32767, true);
      offset += 2;
    }
  }

  return new Blob([buffer], { type: "audio/wav" });
}

export async function renderConcreteThumpWav({ profile, sampleFile = null }) {
  const normalized = normalizeConcreteThumpProfile(profile);
  let decodeContext = null;
  let sampleBuffer = null;

  if (sampleFile) {
    const AudioContextType = globalThis.AudioContext || globalThis.webkitAudioContext;
    if (!AudioContextType) throw new Error("Web Audio is not supported by this browser.");
    decodeContext = new AudioContextType();
    try {
      sampleBuffer = await decodeSample(sampleFile, decodeContext);
    } finally {
      await decodeContext.close();
    }
  }

  const OfflineContextType = globalThis.OfflineAudioContext || globalThis.webkitOfflineAudioContext;
  if (!OfflineContextType) throw new Error("Offline WAV rendering is not supported by this browser.");

  const sixteenth = 60 / normalized.bpm / 4;
  const duration = sixteenth * 16 * RENDER_BARS + AUDIO_TAIL_SECONDS;
  const length = Math.ceil(duration * SAMPLE_RATE);
  const offline = new OfflineContextType(2, length, SAMPLE_RATE);
  scheduleSequence(offline, offline.destination, normalized, sampleBuffer, 0.04);
  const rendered = await offline.startRendering();
  return encodeWav(rendered);
}
