// The pattern: every hit in the film, for Ableton's Perc Kitchen Kit.
// Writes src/score.json — the one timeline the picture (Film.tsx), the
// preview mix (score.mjs) and the Live set (als.py) all read.
//
// Beats from 0, 4 to a bar, 152 bpm; 76 beats = 30.000 s.

import { writeFileSync } from 'node:fs';

// Perc Kitchen Kit.adg, pad by pad (MIDI note → sample).
export const KIT = {
  pan: 36, // Perc Pan — the low boom, our kick
  pot1: 37, // Perc Pot 1 — low tom
  pot2: 38, // Perc Pot 2 — high tom
  strike: 39, // Perc Strike — the backbeat
  drip1: 40,
  drip2: 41,
  knifes: 42, // Perc Knifes — the hat
  drip3: 43,
  ice: 44, // FX Ice Cubes — rattle
  drip4: 45,
  spoons: 46, // Perc Spoons — shaker
  water: 47, // FX Water — the swoosh
  glass: 48, // Perc Glass Low — a cut
  kettle: 49, // Perc Kettle — a tick
  kling: 50, // Perc Kling — high bell
  klang: 51, // Perc Klang — section hit
};

export const SECTIONS = [
  [0, 'Open'],
  [8, 'The loop'],
  [12, 'Ports'],
  [20, 'Prompt'],
  [24, 'Palette'],
  [28, 'Compositor'],
  [44, 'One action model'],
  [52, 'Look'],
  [60, 'Close'],
  [64, 'nus'],
];

const notes = [];
const hit = (beat, name, vel = 100, dur = 0.25) => notes.push({ beat, note: KIT[name], name, vel, dur });

// ── Open (0–7): the lid lifts, the screen comes on at 4 ─────────────────────
hit(0, 'ice', 90);
hit(0, 'water', 70);
for (let s = 0; s < 16; s++) hit(4 + s / 4, 'knifes', Math.round(40 + s * 4)); // a hat build into the downbeat
hit(4, 'klang', 110);
hit(4, 'pan', 100);
hit(6, 'pot1', 80);
hit(7, 'pot2', 85);
hit(7.5, 'pot1', 90);

// ── Groove A: the white half ────────────────────────────────────────────────
function grooveA(bar, { fill = false } = {}) {
  hit(bar, 'pan', 120);
  hit(bar + 1.5, 'pan', 95);
  hit(bar + 2.5, 'pan', 105);
  hit(bar + 1, 'strike', 110);
  hit(bar + 3, 'strike', 115);
  for (let e = 0; e < 8; e++) hit(bar + e / 2, 'knifes', e % 2 ? 55 : 72);
  hit(bar + 3.75, 'knifes', 45);
  hit(bar + 3.5, 'spoons', 80);
  if (fill) {
    hit(bar + 3, 'pot2', 95);
    hit(bar + 3.25, 'pot1', 90);
    hit(bar + 3.5, 'pot2', 100);
    hit(bar + 3.75, 'pot1', 105);
  }
}
for (const bar of [8, 12, 16, 20]) grooveA(bar);
grooveA(24, { fill: true });

// The loop (8–11): a URL at the prompt.
hit(8, 'glass', 105);
hit(9, 'drip3', 100);
hit(10, 'drip4', 95);
hit(11.5, 'spoons', 95); // the shutter closes
// Ports (12–19): port → process → page, then the three words.
hit(12, 'glass', 110);
hit(13, 'drip1', 105);
hit(14, 'drip3', 105);
hit(15, 'drip4', 110);
hit(16, 'kettle', 90);
hit(17, 'kettle', 95);
hit(18, 'kling', 105);
hit(19.5, 'water', 90); // band wipe
// Prompt (20–23) and palette (24–27).
hit(20, 'glass', 105);
hit(20, 'drip3', 90);
hit(22, 'drip4', 95);
hit(24, 'glass', 105);
hit(23.875, 'knifes', 60); // Ctrl, Shift go down
hit(24.25, 'kettle', 105); // K
hit(25, 'glass', 100); // the palette
hit(25, 'drip3', 95);
hit(28, 'ice', 95); // cell resolve

// ── Groove B: the compositor, half time, on black ───────────────────────────
function grooveB(bar) {
  hit(bar, 'pan', 120);
  hit(bar + 2.75, 'pan', 90);
  hit(bar + 2, 'strike', 118);
  hit(bar + 1, 'ice', 70);
  hit(bar + 3, 'ice', 66);
  for (let s = 0; s < 16; s++) hit(bar + s / 4, 'knifes', s % 4 === 0 ? 70 : s % 2 ? 42 : 55);
}
for (const bar of [28, 32, 36, 40]) grooveB(bar);
hit(28, 'klang', 127);
hit(30, 'pot1', 100); // the layers part, one a beat
hit(31, 'pot2', 100);
hit(32, 'glass', 105);
hit(33, 'kling', 100);
hit(36, 'kettle', 95);
hit(38, 'kling', 100);
hit(42, 'water', 90); // they close back up
hit(43, 'water', 95); // band wipe

// ── One action model (44–51): commands land on the beat ────────────────────
grooveA(44);
grooveA(48, { fill: true });
hit(44, 'klang', 115);
hit(45, 'drip3', 90);
hit(46, 'drip1', 105);
hit(47, 'drip3', 105);
hit(48, 'drip4', 110);
hit(49, 'drip2', 110);

// ── Look (52–59) on the laptop, and the lid closing (60–63) ─────────────────
hit(52, 'klang', 115);
hit(52, 'ice', 85); // cell resolve
for (const bar of [52, 56]) {
  hit(bar, 'pan', 118);
  hit(bar + 2, 'strike', 105);
  for (let e = 0; e < 8; e++) hit(bar + e / 2, 'knifes', e % 2 ? 40 : 58);
}
hit(53, 'kettle', 90); // a theme a beat
hit(54, 'kettle', 95);
hit(55, 'kettle', 100);
hit(56, 'glass', 110); // paper
hit(60, 'water', 95);
hit(60, 'pan', 105);
hit(61.5, 'spoons', 85);
hit(62, 'ice', 80);
for (let s = 0; s < 8; s++) hit(62 + s / 4, 'knifes', 50 + s * 8);

// ── nus (64–75): the end card ───────────────────────────────────────────────
hit(64, 'pan', 127);
hit(64, 'klang', 120);
hit(66, 'kling', 85);
hit(68, 'glass', 80);

notes.sort((a, b) => a.beat - b.beat || a.note - b.note);

// cuelume, once: its "arrival" under the icon drawing in.
const cuelume = [{ beat: 64, cue: 'arrival', gain: 0.9 }];

writeFileSync(
  new URL('../src/score.json', import.meta.url),
  JSON.stringify({ bpm: 152, beats: 76, kit: 'Perc Kitchen Kit.adg', sections: SECTIONS.map(([beat, name]) => ({ beat, name })), notes, cuelume }, null, 1) + '\n',
);
console.log(`score.json · ${notes.length} hits · ${SECTIONS.length} sections · cuelume ×${cuelume.length}`);
