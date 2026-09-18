// cuelume's cues through nus's synth — a line-for-line port of
// spikes/composite/src/sound.rs (cuelume's recipes, Daniel Belyi, MIT):
// tone and filtered-noise layers, exponential envelopes, glide, a
// feedback-delay shimmer and the same soft output stage.

// ── Recipes (sound.rs) ────────────────────────────────────────────────────
const tone = (wave, freq, offset, attack, decay, peak, detune = 0) => ({ kind: 'tone', wave, freq, offset, attack, decay, peak, detune });
const glide = (wave, freq, to, time, offset, attack, decay, peak) => ({ kind: 'tone', wave, freq, glideTo: to, glideTime: time, offset, attack, decay, peak, detune: 0 });
const noise = (filter, freq, q, offset, attack, decay, peak) => ({ kind: 'noise', filter, freq, q, offset, attack, decay, peak });
const sh = (delay, feedback, wet, lowpass) => ({ delay, feedback, wet, lowpass });

export const RECIPES = {
  chime: { master: 0.5, layers: [tone('sine', 1046.5, 0, 0.006, 0.22, 0.09), tone('sine', 1568, 0.09, 0.006, 0.26, 0.08)], shimmer: sh(0.12, 0.25, 0.18, 4000) },
  sparkle: { master: 0.5, layers: [tone('sine', 1760, 0, 0.003, 0.09, 0.045), tone('sine', 2217, 0.045, 0.003, 0.09, 0.04), tone('sine', 2637, 0.09, 0.003, 0.1, 0.038), tone('sine', 3520, 0.135, 0.003, 0.12, 0.032)], shimmer: sh(0.07, 0.35, 0.22, 6000) },
  droplet: { master: 0.55, layers: [glide('sine', 1200, 550, 0.14, 0, 0.004, 0.2, 0.075)], shimmer: sh(0.09, 0.2, 0.15, 3000) },
  bloom: { master: 0.5, layers: [tone('sine', 528, 0, 0.06, 0.32, 0.06), tone('sine', 528, 0, 0.06, 0.34, 0.05, 12)], shimmer: sh(0.15, 0.2, 0.12, 2500) },
  whisper: { master: 0.48, layers: [noise('lowpass', 1600, 0.7, 0, 0.025, 0.13, 0.04), glide('sine', 880, 660, 0.14, 0.01, 0.012, 0.14, 0.025)], shimmer: null },
  tick: { master: 0.4, layers: [noise('bandpass', 5400, 1.8, 0, 0.001, 0.018, 0.14), tone('sine', 2600, 0, 0.001, 0.012, 0.018)], shimmer: null },
  press: { master: 0.4, layers: [noise('bandpass', 1700, 1.4, 0, 0.001, 0.02, 0.13)], shimmer: null },
  release: { master: 0.4, layers: [noise('bandpass', 4600, 1.8, 0, 0.001, 0.016, 0.12), tone('sine', 3200, 0.006, 0.001, 0.05, 0.02)], shimmer: null },
  toggle: { master: 0.4, layers: [noise('bandpass', 2200, 1.6, 0, 0.001, 0.016, 0.12), noise('bandpass', 3800, 1.6, 0.024, 0.001, 0.02, 0.1)], shimmer: null },
  success: { master: 0.5, layers: [tone('sine', 880, 0, 0.004, 0.09, 0.06), tone('sine', 1108.73, 0.06, 0.004, 0.1, 0.06), tone('sine', 1318.51, 0.12, 0.004, 0.18, 0.07)], shimmer: sh(0.1, 0.22, 0.16, 4500) },
  error: { master: 0.42, layers: [noise('bandpass', 850, 1.1, 0, 0.001, 0.035, 0.13), tone('triangle', 440, 0.025, 0.004, 0.09, 0.045), tone('triangle', 349.23, 0.1, 0.004, 0.14, 0.04)], shimmer: null },
  page: { master: 0.38, layers: [noise('lowpass', 1800, 0.7, 0, 0.006, 0.08, 0.11), noise('bandpass', 4200, 1.2, 0.04, 0.004, 0.065, 0.08), tone('sine', 2400, 0.075, 0.002, 0.045, 0.02)], shimmer: null },
  loading: { master: 0.42, layers: [noise('lowpass', 1400, 0.6, 0, 0.035, 0.14, 0.035), glide('sine', 420, 630, 0.18, 0, 0.025, 0.18, 0.05)], shimmer: sh(0.11, 0.18, 0.12, 2800) },
  ready: { master: 0.48, layers: [noise('bandpass', 3600, 1.8, 0, 0.001, 0.02, 0.11), glide('triangle', 330, 660, 0.12, 0.012, 0.004, 0.16, 0.055), tone('sine', 990, 0.13, 0.004, 0.22, 0.06)], shimmer: sh(0.1, 0.16, 0.1, 4200) },
  pulse: { master: 0.42, layers: [noise('bandpass', 2600, 2.4, 0, 0.001, 0.022, 0.08), glide('triangle', 620, 1240, 0.07, 0, 0.002, 0.085, 0.055)], shimmer: null },
  scan: { master: 0.4, layers: [tone('sine', 740, 0, 0.002, 0.055, 0.05), tone('sine', 1110, 0.045, 0.002, 0.055, 0.045), tone('sine', 1665, 0.09, 0.002, 0.07, 0.04)], shimmer: sh(0.065, 0.16, 0.1, 4200) },
  arrival: { master: 0.44, layers: [noise('lowpass', 900, 0.8, 0, 0.05, 0.24, 0.035), glide('sine', 220, 440, 0.32, 0, 0.04, 0.34, 0.055), tone('sine', 659.25, 0.12, 0.045, 0.32, 0.04), tone('sine', 987.77, 0.19, 0.045, 0.34, 0.032)], shimmer: sh(0.16, 0.28, 0.18, 3200) },
};

// ── Synthesis (sound.rs) ──────────────────────────────────────────────────
const OUTPUT_GAIN = 4.0;
const FLOOR = 0.0001;
const TAU = Math.PI * 2;

function biquad(filter, freq, q, rate) {
  const w0 = (TAU * Math.min(freq, rate * 0.45)) / rate;
  const sin = Math.sin(w0), cos = Math.cos(w0);
  const alpha = sin / (2 * Math.max(q, 0.01));
  let b0, b1, b2, a0, a1, a2;
  if (filter === 'lowpass') [b0, b1, b2, a0, a1, a2] = [(1 - cos) / 2, 1 - cos, (1 - cos) / 2, 1 + alpha, -2 * cos, 1 - alpha];
  else [b0, b1, b2, a0, a1, a2] = [alpha, 0, -alpha, 1 + alpha, -2 * cos, 1 - alpha];
  const c = { b0: b0 / a0, b1: b1 / a0, b2: b2 / a0, a1: a1 / a0, a2: a2 / a0 };
  let x1 = 0, x2 = 0, y1 = 0, y2 = 0;
  return (x) => {
    const y = c.b0 * x + c.b1 * x1 + c.b2 * x2 - c.a1 * y1 - c.a2 * y2;
    x2 = x1; x1 = x; y2 = y1; y1 = y;
    return y;
  };
}

function envelope(t, attack, decay, peak) {
  if (t < 0) return 0;
  if (t < attack) return FLOOR * Math.pow(peak / FLOOR, t / Math.max(attack, 1e-4));
  if (t < attack + decay) return peak * Math.pow(FLOOR / peak, (t - attack) / Math.max(decay, 1e-4));
  return 0;
}

function wave(w, phase) {
  const p = ((phase % 1) + 1) % 1;
  if (w === 'sine') return Math.sin(p * TAU);
  if (w === 'triangle') return 4 * Math.abs(p - 0.5) - 1;
  if (w === 'square') return p < 0.5 ? 1 : -1;
  return 2 * p - 1;
}

export function render(r, rate) {
  const end = Math.max(...r.layers.map((l) => l.offset + l.attack + l.decay + 0.05));
  const s = r.shimmer;
  const tail = s && s.feedback > 0 ? s.delay * (1 + Math.ceil(Math.log(FLOOR) / Math.log(s.feedback))) : 0;
  const n = Math.floor((end + tail + 0.05) * rate);
  const dry = new Float32Array(n);
  let seed = 0x9e3779b9 >>> 0;
  const rnd = () => {
    seed ^= seed << 13; seed >>>= 0;
    seed ^= seed >>> 17;
    seed ^= seed << 5; seed >>>= 0;
    return (seed / 0xffffffff) * 2 - 1;
  };
  for (const l of r.layers) {
    const start = Math.floor(l.offset * rate);
    const len = Math.floor((l.attack + l.decay + 0.05) * rate);
    if (l.kind === 'tone') {
      const f0 = l.freq * Math.pow(2, l.detune / 1200);
      const gt = Math.max(l.glideTime ?? l.attack + l.decay, 1e-4);
      let phase = 0;
      for (let i = 0; i < len && start + i < n; i++) {
        const t = i / rate;
        const f = l.glideTo ? f0 * Math.pow(l.glideTo / f0, Math.min(t / gt, 1)) : f0;
        phase += f / rate;
        dry[start + i] += wave(l.wave, phase) * envelope(t, l.attack, l.decay, l.peak);
      }
    } else {
      const bq = biquad(l.filter, l.freq, l.q, rate);
      for (let i = 0; i < len && start + i < n; i++) {
        dry[start + i] += bq(rnd()) * envelope(i / rate, l.attack, l.decay, l.peak);
      }
    }
  }
  for (let i = 0; i < n; i++) dry[i] *= r.master;
  const out = Float32Array.from(dry);
  if (s) {
    const d = Math.max(Math.floor(s.delay * rate), 1);
    const line = new Float32Array(n + d);
    const lp = biquad('lowpass', s.lowpass, 0.7, rate);
    for (let i = 0; i < n; i++) {
      const filtered = lp(i >= d ? line[i - d] : 0);
      line[i] = dry[i] + filtered * s.feedback;
      out[i] += filtered * s.wet;
    }
  }
  for (let i = 0; i < n; i++) {
    const x = out[i] * OUTPUT_GAIN;
    out[i] = Math.abs(x) < 0.4 ? x : Math.sign(x) * (0.4 + Math.tanh(Math.abs(x) - 0.4) * 0.6);
  }
  return out;
}
