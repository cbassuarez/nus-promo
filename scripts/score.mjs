// The preview mix: src/score.json played through Ableton's Perc Kitchen Kit
// — its own samples at its own pad settings (Drum Sampler volume, velocity
// → volume, hold and decay) — plus cuelume, once. Writes public/score.wav.
//
// The rack's Saturator (no drive) and Reverb (sends at −70 dB) are all but
// transparent as shipped, so this is close to what Live plays. The real
// thing is the Live set in ableton/: bounce it to ableton/bounce.wav and
// `npm run mux` uses that instead.

import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { RECIPES, render } from './cuelume.mjs';

const RATE = 48000;
const sheet = JSON.parse(readFileSync(new URL('../src/score.json', import.meta.url)));
const BEAT = 60 / sheet.bpm;
const LENGTH = sheet.beats * BEAT + 2;
const N = Math.ceil(LENGTH * RATE);
const at = (beat) => Math.round(beat * BEAT * RATE);

export const LIVE = '/Applications/Ableton Live 12 Intro.app/Contents/App-Resources/Core Library';

// The kit, from the .adg: note → sample, Drum Sampler volume (dB), hold and decay (s).
const PADS = {
  36: ['Misc Percussion/Perc Pan.wav', -13.8, 0.3, 4.37],
  37: ['Misc Percussion/Perc Pot 1.wav', -12.09, 0.3, 4.77],
  38: ['Misc Percussion/Perc Pot 2.wav', -13.8, 0.3, 5.68],
  39: ['Misc Percussion/Perc Strike.wav', -13.8, 0.3, 3.36],
  40: ['FX Hit/FX Drip 1.wav', -6.95, 0.6, 0.05],
  41: ['FX Hit/FX Drip 2.wav', -8.7, 0.6, 0.05],
  42: ['Misc Percussion/Perc Knifes.wav', -12.8, 0.3, 1.83],
  43: ['FX Hit/FX Drip 3.wav', -4.77, 0.6, 0.05],
  44: ['FX Hit/FX Ice Cubes.aif', -12.8, 0.3, 3.52],
  45: ['FX Hit/FX Drip 4.wav', -4.77, 0.6, 0.05],
  46: ['Misc Percussion/Perc Spoons.wav', -12.8, 0.3, 2.82],
  47: ['FX Hit/FX Water.wav', -8.7, 0.6, 0.05],
  48: ['Misc Percussion/Perc Glass Low.aif', -10.93, 0.3, 1.29],
  49: ['Misc Percussion/Perc Kettle.wav', -12.8, 0.3, 2.59],
  50: ['Misc Percussion/Perc Kling.wav', -12.8, 0.3, 1.67],
  51: ['Misc Percussion/Perc Klang.wav', -12.8, 0.3, 3.23],
};
const VEL_TO_VOL = 0.35;

function decode(file) {
  const raw = execFileSync('ffmpeg', ['-v', 'error', '-i', `${LIVE}/Samples/One Shots/Drums/${file}`, '-ac', '2', '-ar', String(RATE), '-f', 'f32le', '-'], { maxBuffer: 1 << 28 });
  const f = new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4);
  return [f.filter((_, i) => i % 2 === 0), f.filter((_, i) => i % 2 === 1)];
}

const L = new Float32Array(N);
const R = new Float32Array(N);
const samples = {};

for (const { beat, note, vel } of sheet.notes) {
  const [file, db, hold, decay] = PADS[note];
  const [sl, sr] = (samples[note] ??= decode(file));
  const gain = Math.pow(10, db / 20) * (1 - VEL_TO_VOL * (1 - vel / 127));
  const s0 = at(beat);
  const holdN = hold * RATE;
  for (let i = 0; i < sl.length && s0 + i < N; i++) {
    // Drum Sampler's envelope: hold, then an exponential decay to −60 dB.
    const env = i < holdN ? 1 : Math.pow(0.001, (i - holdN) / (decay * RATE));
    if (env < 1e-4) break;
    L[s0 + i] += sl[i] * gain * env;
    R[s0 + i] += sr[i] * gain * env;
  }
}

// cuelume, once.
mkdirSync(new URL('../ableton/nus-object Project/Samples/Imported/', import.meta.url), { recursive: true });
for (const { beat, cue, gain } of sheet.cuelume) {
  const c = render(RECIPES[cue], RATE);
  const s0 = at(beat);
  for (let i = 0; i < c.length && s0 + i < N; i++) {
    L[s0 + i] += c[i] * gain * 0.5;
    R[s0 + i] += c[i] * gain * 0.5;
  }
  writeWav(new URL(`../ableton/nus-object Project/Samples/Imported/cuelume-${cue}.wav`, import.meta.url), c, c);
}

// The master: drive into a soft knee, then a ceiling that keeps the true
// peak under −1 dBFS.
let peak = 0;
for (let i = 0; i < N; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
const g = Math.pow(10, -1 / 20) / peak;
const DRIVE = Number(process.env.DRIVE ?? 3.2);
const CEILING = Number(process.env.CEILING ?? 0.58);
const knee = (x) => (Math.abs(x) < 0.7 ? x : Math.sign(x) * (0.7 + Math.tanh((Math.abs(x) - 0.7) / 0.3) * 0.3));
for (let i = 0; i < N; i++) {
  L[i] = knee(L[i] * g * DRIVE) * CEILING;
  R[i] = knee(R[i] * g * DRIVE) * CEILING;
}
writeWav(new URL('../public/score.wav', import.meta.url), L, R);
console.log(`score.wav · Perc Kitchen Kit · ${sheet.notes.length} hits · cuelume ×${sheet.cuelume.length} · ${(sheet.beats * BEAT).toFixed(3)} s`);

function writeWav(url, l, r) {
  const n = l.length;
  const data = Buffer.alloc(n * 4);
  for (let i = 0; i < n; i++) {
    data.writeInt16LE(Math.round(Math.max(-1, Math.min(1, l[i])) * 32767), i * 4);
    data.writeInt16LE(Math.round(Math.max(-1, Math.min(1, r[i])) * 32767), i * 4 + 2);
  }
  const h = Buffer.alloc(44);
  h.write('RIFF', 0); h.writeUInt32LE(36 + data.length, 4); h.write('WAVE', 8);
  h.write('fmt ', 12); h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(2, 22);
  h.writeUInt32LE(RATE, 24); h.writeUInt32LE(RATE * 4, 28); h.writeUInt16LE(4, 32); h.writeUInt16LE(16, 34);
  h.write('data', 36); h.writeUInt32LE(data.length, 40);
  writeFileSync(url, Buffer.concat([h, data]));
}
